from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.db.models import Count

from openpyxl import Workbook

from .models import (
    Category,
    Event,
    EventRegistration,
    Attendance,
    Announcement,
    Feedback,
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
        {}
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

    return TemplateResponse(
        request,
        "admin/attendance_report_list.html",
        {"rows": rows}
    )


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
    )

    list_filter = ('status', 'category')
    search_fields = ('name',)

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
                '<a class="button" href="{}">Proposal</a>',
                url
            )

        return "No Proposal"

    def registration_btn(self, obj):

        url = reverse(
            'events:event_registrations',
            args=[obj.id]
        )

        return format_html(
            '<a class="button" href="{}">Registrations</a>',
            url
        )

    def attendance_btn(self, obj):

        url = reverse(
            'events:view_attendance',
            args=[obj.id]
        )

        return format_html(
            '<a class="button" href="{}">Attendance</a>',
            url
        )

    def feedback_btn(self, obj):

        url = reverse(
            'events:view_feedbacks',
            args=[obj.id]
        )

        return format_html(
            '<a class="button" href="{}">Feedback</a>',
            url
        )


# =====================================================
# EVENT PROPOSAL ADMIN
# =====================================================
@admin.register(EventProposal)
class EventProposalAdmin(admin.ModelAdmin):

    list_display = (
        'event',
        'organizer',
        'proposed_venue',
        'status',
        'submitted_at'
    )

    list_filter = ('status',)

    search_fields = (
        'event__name',
        'organizer__username'
    )

    def has_module_permission(self, request):
        return False

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

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
        queryset.update(status=ProposalStatus.ACCEPTED)

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

        return TemplateResponse(
            request,
            "admin/event_report_list.html",
            {"rows": rows}
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

        extra_context = extra_context or {}
        extra_context.update({
            "event": event,
            "report": report,
            "feedbacks": feedbacks,
            "stats": stats,
            "has_feedback": feedbacks.exists(),
            **percentages,
            "total_feedback": total,
        })

        return TemplateResponse(
            request,
            "admin/event_report_change.html",
            extra_context
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

        return TemplateResponse(
            request,
            "admin/attendance_report_change.html",
            {
                "event": event,
                "data": data,
                "total_students": total_students,
                "present": present_count,
                "absent": absent_count,
                "percentage": round(percentage, 2),
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