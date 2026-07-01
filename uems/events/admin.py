from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.db.models import Count
from django.core.paginator import Paginator
from django.contrib.admin.views.main import PAGE_VAR

from openpyxl import Workbook

from .models import (
    Category,
    Event,
    EventRegistration,
    Attendance,
    Announcement,
    Feedback,
    EventMessage,
    EventProposal,
    EventReport,
    Notification,
    EventStatus,
    ProposalStatus,
)


# =====================================================
# MODULE LANDING PAGE
# =====================================================
def event_report_module(request):
    return TemplateResponse(
        request,
        "admin/event_report_module.html",
        {
            **admin.site.each_context(request),
            "title": "Event Reports",
        }
    )


# =====================================================
# ATTENDANCE LIST (ALL EVENTS PAGE)
# =====================================================
def attendance_event_list(request):

    events = Event.objects.filter(
        status__in=[EventStatus.ANNOUNCED, EventStatus.COMPLETED]
    ).order_by("-date")

    rows = []

    for event in events:

        total = EventRegistration.objects.filter(event=event).count()

        # Count actual attendance records, not EventRegistration status
        present = Attendance.objects.filter(event=event).count()

        rows.append({
            "event": event,
            "total_registrations": total,
            "total_attendance": present,
        })

    rows_page = Paginator(
        rows,
        10
    ).get_page(request.GET.get("page"))

    return TemplateResponse(
        request,
        "admin/attendance_report_list.html",
        {
            **admin.site.each_context(request),
            "rows": rows_page.object_list,
            "page_obj": rows_page,
            "title": "Attendance Report",
        }
    )


def apply_accepted_proposal_to_event(proposal):
    event = proposal.event
    event.venue = proposal.proposed_venue

    if proposal.proposed_date:
        event.date = proposal.proposed_date

    event.save(update_fields=["venue", "date"])


# =====================================================
# CATEGORY
# =====================================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


# =====================================================
# EVENT ADMIN
# =====================================================
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_per_page = 10
    change_list_template = "admin/events_event_change_list.html"

    list_display = (
        'name',
        'category',
        'venue',
        'date',
        'status',
        'organizer',
        'proposal_btn',
        'registration_btn',
        'attendance_btn',
        'feedback_btn',
        'messages_btn',
    )

    # list_filter = ('status', 'category')
    search_fields = ('name',)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "organizer":
            kwargs["queryset"] = User.objects.filter(
                profile__role="faculty",
                is_active=True,
            ).order_by("username")

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)

        if not hasattr(response, "context_data") or "cl" not in response.context_data:
            return response

        cl = response.context_data["cl"]

        def page_url(page_index):
            params = request.GET.copy()
            params[PAGE_VAR] = page_index
            return f"?{params.urlencode()}"

        page_items = [
            {
                "label": page_number,
                "url": page_url(page_number),
                "current": page_number == cl.page_num,
            }
            for page_number in range(1, cl.paginator.num_pages + 1)
        ]

        response.context_data["event_pagination"] = {
            "count": cl.result_count,
            "start": cl.result_count and ((cl.page_num - 1) * cl.list_per_page) + 1,
            "end": min(cl.page_num * cl.list_per_page, cl.result_count),
            "has_previous": cl.page_num > 1,
            "previous_url": page_url(cl.page_num - 1),
            "has_next": cl.page_num < cl.paginator.num_pages,
            "next_url": page_url(cl.page_num + 1),
            "page_items": page_items,
        }

        return response

    def save_model(self, request, obj, form, change):

        old_obj = None
        is_new = obj.pk is None

        if not is_new:
            old_obj = Event.objects.get(pk=obj.pk)

        super().save_model(request, obj, form, change)

        if obj.organizer and (
            is_new or (
                old_obj and old_obj.organizer != obj.organizer
            )
        ):

            if hasattr(obj.organizer, "profile") and not obj.organizer.profile.is_organizer:
                obj.organizer.profile.is_organizer = True
                obj.organizer.profile.save(update_fields=["is_organizer"])

            Notification.objects.create(
                user=obj.organizer,
                event=obj,
                notification_type='event_assigned',
                message=f"You are assigned as Organizer for '{obj.name}'."
            )

        if (
            old_obj and
            old_obj.status != EventStatus.ANNOUNCED and
            obj.status == EventStatus.ANNOUNCED
        ):

            users = User.objects.filter(is_active=True)

            for user in users:

                Notification.objects.create(
                    user=user,
                    event=obj,
                    notification_type='event_announced',
                    message=f"Event Announced: {obj.name}"
                )

    @admin.display(description="Proposals")
    def proposal_btn(self, obj):

        proposal = EventProposal.objects.filter(
            event=obj
        ).order_by("-id").first()

        if proposal:
            url = reverse(
                'admin:events_eventproposal_change',
                args=[proposal.id]
            )

            return format_html(
                '<a class="button" href="{}">View</a>',
                url
            )

        return "No Proposal"

    @admin.display(description="Registrations")
    def registration_btn(self, obj):

        url = reverse(
            'admin:events_event_registrations',
            args=[obj.id]
        )

        return format_html(
            '<a class="button" href="{}">View</a>',
            url
        )

    @admin.display(description="Attendance")
    def attendance_btn(self, obj):

        url = reverse(
            'admin:events_event_attendance',
            args=[obj.id]
        )

        return format_html(
            '<a class="button" href="{}">View</a>',
            url
        )

    @admin.display(description="Feedback")
    def feedback_btn(self, obj):

        url = reverse(
            'admin:events_event_feedback',
            args=[obj.id]
        )

        return format_html(
            '<a class="button" href="{}">View</a>',
            url
        )

    @admin.display(description="Messages")
    def messages_btn(self, obj):

        if not obj.organizer_id:
            return "-"

        url = reverse(
            'events:event_message_thread',
            args=[obj.id, obj.organizer_id]
        )

        return format_html(
            '<a class="button" href="{}">Message Organizer</a>',
            url
        )

    def registrations_view(self, request, event_id):

        event = get_object_or_404(Event, pk=event_id)

        registrations = EventRegistration.objects.filter(
            event=event
        ).select_related("student").order_by("-created_at")
        registrations_page = Paginator(
            registrations,
            10
        ).get_page(request.GET.get("page"))

        context = {
            **self.admin_site.each_context(request),
            "title": f"Registrations for {event.name}",
            "subtitle": str(event),
            "original": event,
            "opts": self.model._meta,
            "event": event,
            "registrations": registrations_page.object_list,
            "page_obj": registrations_page,
            "total": registrations.count(),
        }

        return TemplateResponse(
            request,
            "admin/event_registrations.html",
            context
        )

    def attendance_view(self, request, event_id):

        event = get_object_or_404(Event, pk=event_id)

        registrations = EventRegistration.objects.filter(
            event=event
        ).select_related("student").order_by("-created_at")

        attendance_map = {
            attendance.student_id: attendance.marked_at
            for attendance in Attendance.objects.filter(event=event)
        }

        rows = []

        for registration in registrations:
            rows.append({
                "name": registration.student.username,
                "reg_no": registration.registration_no,
                "department": registration.department,
                "email": registration.student.email,
                "status": (
                    "present"
                    if registration.student_id in attendance_map
                    else "absent"
                ),
                "marked_at": attendance_map.get(registration.student_id),
            })

        present = sum(1 for row in rows if row["status"] == "present")
        total = len(rows)
        absent = total - present
        percentage = round((present / total) * 100, 2) if total else 0
        rows_page = Paginator(
            rows,
            10
        ).get_page(request.GET.get("page"))

        context = {
            **self.admin_site.each_context(request),
            "title": f"Attendance for {event.name}",
            "subtitle": str(event),
            "original": event,
            "opts": self.model._meta,
            "event": event,
            "rows": rows_page.object_list,
            "page_obj": rows_page,
            "total": total,
            "present": present,
            "absent": absent,
            "percentage": percentage,
        }

        return TemplateResponse(
            request,
            "admin/event_attendance.html",
            context
        )

    def feedback_view(self, request, event_id):

        event = get_object_or_404(Event, pk=event_id)

        feedbacks = Feedback.objects.filter(
            event=event
        ).select_related("student")
        feedback_page = Paginator(
            feedbacks.order_by("-created_at"),
            10
        ).get_page(request.GET.get("page"))

        ratings = [
            feedback.rating
            for feedback in feedbacks
            if feedback.rating is not None
        ]

        context = {
            **self.admin_site.each_context(request),
            "title": f"Feedback for {event.name}",
            "subtitle": str(event),
            "original": event,
            "opts": self.model._meta,
            "event": event,
            "feedbacks": feedback_page.object_list,
            "page_obj": feedback_page,
            "total": feedbacks.count(),
            "average_rating": (
                round(sum(ratings) / len(ratings), 2)
                if ratings
                else None
            ),
        }

        return TemplateResponse(
            request,
            "admin/event_feedback.html",
            context
        )

    def get_urls(self):

        urls = super().get_urls()

        custom_urls = [
            path(
                '<int:event_id>/registrations/',
                self.admin_site.admin_view(
                    self.registrations_view
                ),
                name="events_event_registrations"
            ),
            path(
                '<int:event_id>/attendance/',
                self.admin_site.admin_view(
                    self.attendance_view
                ),
                name="events_event_attendance"
            ),
            path(
                '<int:event_id>/feedback/',
                self.admin_site.admin_view(
                    self.feedback_view
                ),
                name="events_event_feedback"
            ),
        ]

        return custom_urls + urls


# =====================================================
# EVENT PROPOSAL ADMIN
# =====================================================
@admin.register(EventProposal)
class EventProposalAdmin(admin.ModelAdmin):

    list_display = (
        'event',
        'organizer',
        'proposed_venue',
        'proposed_date',
        'status',
        'submitted_at'
    )

    list_filter = ('status',)
    actions = ('approve_proposals', 'reject_proposals')

    search_fields = (
        'event__name',
        'organizer__username'
    )

    def has_module_permission(self, request):
        return False

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.status == ProposalStatus.ACCEPTED:
            apply_accepted_proposal_to_event(obj)

    def get_readonly_fields(self, request, obj=None):

        if obj:
            return [
                f.name
                for f in obj._meta.fields
                if f.name != "status"
            ]

        return []

    @admin.action(description="Approve selected proposals")
    def approve_proposals(self, request, queryset):
        for proposal in queryset.select_related("event"):
            proposal.status = ProposalStatus.ACCEPTED
            proposal.save(update_fields=["status"])
            apply_accepted_proposal_to_event(proposal)

    @admin.action(description="Reject selected proposals")
    def reject_proposals(self, request, queryset):
        queryset.update(status=ProposalStatus.REJECTED)


# =====================================================
# EVENT REPORT ADMIN
# =====================================================
@admin.register(EventReport)
class EventReportAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "event",
        "created_at"
    )

    exclude = (
        "event",
        "created_at"
    )

    def changelist_view(self, request, extra_context=None):

        extra_context = extra_context or {}
        extra_context["title"] = "Event Reports"

        return super().changelist_view(
            request,
            extra_context
        )

    # =================================================
    # FEEDBACK LIST
    # =================================================
    def feedback_list_view(self, request):

        events = Event.objects.filter(
            status__in=[
                EventStatus.ANNOUNCED,
                EventStatus.COMPLETED
            ]
        ).order_by("-date")

        rows = []

        for event in events:

            feedback_count = Feedback.objects.filter(
                event=event
            ).count()

            report, _ = EventReport.objects.get_or_create(
                event=event,
                defaults={
                    "name": f"{event.name} Report"
                }
            )

            rows.append({
                "event": event,
                "report": report,
                "feedback_count": feedback_count,
            })

        rows_page = Paginator(
            rows,
            10
        ).get_page(request.GET.get("page"))

        return TemplateResponse(
            request,
            "admin/event_report_list.html",
            {
                **self.admin_site.each_context(request),
                "rows": rows_page.object_list,
                "page_obj": rows_page,
                "title": "Feedback Report",
            }
        )

    # =================================================
    # CHANGE VIEW
    # =================================================
    def change_view(self, request, object_id, form_url='', extra_context=None):

        report = get_object_or_404(EventReport, pk=object_id)
        event = report.event

        feedbacks = Feedback.objects.filter(event=event)

        total = feedbacks.count()

        def safe_count(value):
            return feedbacks.filter(experience__iexact=value.strip()).count()

        excellent = safe_count("excellent")
        good = safe_count("good")
        average = safe_count("average")
        poor = safe_count("poor")

        def pct(value):
            return round((value / total) * 100, 1) if total else 0

        stats = {
            "excellent": excellent,
            "good": good,
            "average": average,
            "poor": poor,
        }

        percentages = {
            "excellent_percent": pct(excellent),
            "good_percent": pct(good),
            "average_percent": pct(average),
            "poor_percent": pct(poor),
        }
        feedback_page = Paginator(
            feedbacks.select_related("student").order_by("-created_at"),
            10
        ).get_page(request.GET.get("page"))

        extra_context = extra_context or {}
        extra_context.update({
            "event": event,
            "report": report,
            "feedbacks": feedback_page.object_list,
            "page_obj": feedback_page,
            "stats": stats,
            "has_feedback": feedbacks.exists(),
            **percentages,
            "total_feedback": total,
        })

        return TemplateResponse(
            request,
            "admin/event_report_change.html",
            {
                **self.admin_site.each_context(request),
                **extra_context,
                "title": "Feedback Report",
            }
        )

    # =================================================
    # EXPORT FEEDBACK EXCEL
    # =================================================
    def export_feedback_excel(self, request, object_id):

        report = get_object_or_404(
            EventReport,
            pk=object_id
        )

        feedbacks = Feedback.objects.filter(
            event=report.event
        )

        wb = Workbook()

        ws = wb.active
        ws.title = "Feedback Report"

        ws.append([
            "Student",
            "Experience",
            "Remarks"
        ])

        for fb in feedbacks:

            ws.append([
                fb.student.username if fb.student else "Unknown",
                fb.get_experience_display(),
                fb.message
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        filename = (
            report.name or "report"
        ).replace(" ", "_")

        response[
            'Content-Disposition'
        ] = f'attachment; filename="{filename}.xlsx"'

        wb.save(response)

        return response

    # =================================================
    # ATTENDANCE DETAIL
    # =================================================
    def attendance_report_detail(self, request, event_id):

        event = get_object_or_404(
            Event,
            pk=event_id
        )

        # Get all registrations and attendance records
        registrations = EventRegistration.objects.filter(
            event=event
        ).select_related("student")

        attendance_qs = Attendance.objects.filter(event=event)
        
        # Create attendance map for quick lookup
        attendance_map = {
            a.student_id: a for a in attendance_qs
        }

        # Build data with correct status
        data = []
        present_count = 0
        
        for reg in registrations:
            att = attendance_map.get(reg.student_id)
            is_present = att is not None
            
            if is_present:
                present_count += 1
                
            data.append({
                "name": reg.student.username,
                "reg_no": reg.student_id,
                "status": "present" if is_present else "absent",
                "marked_at": att.marked_at if att else None
            })

        total_students = len(data)
        absent_count = total_students - present_count
        percentage = (
            (present_count / total_students) * 100
        ) if total_students else 0
        attendance_page = Paginator(
            data,
            10
        ).get_page(request.GET.get("page"))

        return TemplateResponse(
            request,
            "admin/attendance_report_change.html",
            {
                **self.admin_site.each_context(request),
                "event": event,
                "data": attendance_page.object_list,
                "page_obj": attendance_page,
                "total_students": total_students,
                "present": present_count,
                "absent": absent_count,
                "percentage": round(percentage, 2),
                "title": "Attendance Report",
            }
        )

    # =================================================
    # URLS
    # =================================================
    def get_urls(self):

        urls = super().get_urls()

        custom_urls = [

            path(
                '',
                self.admin_site.admin_view(
                    event_report_module
                ),
                name="event_report_module"
            ),

            path(
                'feedback/',
                self.admin_site.admin_view(
                    self.feedback_list_view
                ),
                name="eventreport_feedback_list"
            ),

            path(
                'attendance/',
                self.admin_site.admin_view(
                    attendance_event_list
                ),
                name="attendance_report_list"
            ),

            path(
                'export/<int:object_id>/',
                self.admin_site.admin_view(
                    self.export_feedback_excel
                ),
                name="eventreport_export"
            ),

            path(
                'attendance/<int:event_id>/',
                self.admin_site.admin_view(
                    self.attendance_report_detail
                ),
                name="attendance_report_detail"
            ),
        ]

        return custom_urls + urls


# =====================================================
# HIDDEN MODELS
# =====================================================
class HiddenAdmin(admin.ModelAdmin):

    def has_module_permission(self, request):
        return False


admin.site.register(EventRegistration, HiddenAdmin)
admin.site.register(Feedback, HiddenAdmin)
admin.site.register(Announcement, HiddenAdmin)
admin.site.register(Notification, HiddenAdmin)


# =====================================================
# ADMIN SIDEBAR ORDER
# =====================================================
EVENTS_ADMIN_MODEL_ORDER = {
    "Event": 0,
    "Category": 1,
    "Messages": 2,
    "EventReport": 3,
}

EVENTS_ADMIN_MODEL_NAMES = {
    "EventReport": "Reports",
}


def apply_admin_sidebar_ordering():
    site = admin.site

    if not hasattr(site, "_uems_original_get_app_list"):
        site._uems_original_get_app_list = site.get_app_list

    def get_app_list(request, app_label=None):
        app_list = site._uems_original_get_app_list(request, app_label)

        for app in app_list:
            if app["app_label"] == "events":
                unread_messages = EventMessage.objects.filter(
                    recipient=request.user,
                    is_read=False,
                ).count()

                for model in app["models"]:
                    model["name"] = EVENTS_ADMIN_MODEL_NAMES.get(
                        model["object_name"],
                        model["name"],
                    )

                app["models"].append({
                    "name": "Messages",
                    "object_name": "Messages",
                    "perms": {"view": True},
                    "admin_url": reverse("events:message_inbox"),
                    "add_url": None,
                    "view_only": True,
                    "badge_count": unread_messages,
                })

                app["models"].sort(
                    key=lambda model: (
                        EVENTS_ADMIN_MODEL_ORDER.get(
                            model["object_name"],
                            len(EVENTS_ADMIN_MODEL_ORDER),
                        ),
                        model["name"],
                    )
                )

        return app_list

    site.get_app_list = get_app_list


apply_admin_sidebar_ordering()
