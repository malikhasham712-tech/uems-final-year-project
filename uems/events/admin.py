from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.contrib.auth.models import User

from openpyxl import Workbook

from .models import (
    Category,
    Event,
    EventRegistration,
    Announcement,
    Feedback,
    EventProposal,
    EventReport,
    Notification,
    EventStatus,
    ProposalStatus,
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

    # -------------------------------------------------
    # SAVE MODEL
    # -------------------------------------------------
    def save_model(self, request, obj, form, change):

        old_obj = None
        is_new = obj.pk is None

        if not is_new:
            old_obj = Event.objects.get(pk=obj.pk)

        super().save_model(request, obj, form, change)

        # ORGANIZER ASSIGNED
        if obj.organizer:

            if is_new:
                Notification.objects.create(
                    user=obj.organizer,
                    event=obj,
                    notification_type='event_assigned',
                    message=f"You are assigned as Organizer for '{obj.name}'."
                )

            elif old_obj and old_obj.organizer != obj.organizer:
                Notification.objects.create(
                    user=obj.organizer,
                    event=obj,
                    notification_type='event_assigned',
                    message=f"You are assigned as Organizer for '{obj.name}'."
                )

        # EVENT ANNOUNCED
        if (
            old_obj
            and old_obj.status != EventStatus.ANNOUNCED
            and obj.status == EventStatus.ANNOUNCED
        ):

            users = User.objects.filter(is_active=True)

            for user in users:
                Notification.objects.create(
                    user=user,
                    event=obj,
                    notification_type='event_announced',
                    message=f"Event Announced: {obj.name}"
                )

            if obj.organizer:
                Notification.objects.create(
                    user=obj.organizer,
                    event=obj,
                    notification_type='event_announced',
                    message=f"Your event '{obj.name}' is now announced."
                )

    # -------------------------------------------------
    # PROPOSAL BUTTON
    # -------------------------------------------------
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

        return format_html(
            '<span style="color:#999;">No Proposal</span>'
        )

    proposal_btn.short_description = "Proposal"

    # -------------------------------------------------
    # REGISTRATION BUTTON
    # -------------------------------------------------
    def registration_btn(self, obj):

        url = reverse(
            'events:event_registrations',
            args=[obj.id]
        )

        return format_html(
            '<a class="button" href="{}">Registrations</a>',
            url
        )

    registration_btn.short_description = "Registrations"

    # -------------------------------------------------
    # ATTENDANCE BUTTON
    # -------------------------------------------------
    def attendance_btn(self, obj):

        url = reverse(
            'events:view_attendance',
            args=[obj.id]
        )

        return format_html(
            '<a class="button" style="background:#333;color:white;padding:4px 8px;border-radius:4px;" href="{}">Attendance</a>',
            url
        )

    attendance_btn.short_description = "Attendance"

    # -------------------------------------------------
    # FEEDBACK BUTTON
    # -------------------------------------------------
    def feedback_btn(self, obj):

        url = reverse(
            'events:view_feedbacks',
            args=[obj.id]
        )

        return format_html(
            '<a class="button" href="{}">Feedback</a>',
            url
        )

    feedback_btn.short_description = "Feedback"


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
        'submitted_at',
    )

    list_filter = ('status',)
    search_fields = ('event__name', 'organizer__username')

    actions = ['approve_proposals', 'reject_proposals']

    def has_module_permission(self, request):
        return False

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [
                field.name
                for field in obj._meta.fields
                if field.name != "status"
            ]
        return []

    @admin.action(description="Approve selected proposals")
    def approve_proposals(self, request, queryset):

        for proposal in queryset:

            proposal.status = ProposalStatus.ACCEPTED
            proposal.save()

            if proposal.organizer:
                Notification.objects.create(
                    user=proposal.organizer,
                    event=proposal.event,
                    notification_type='general',
                    message=f"Your proposal for '{proposal.event.name}' has been approved."
                )

    @admin.action(description="Reject selected proposals")
    def reject_proposals(self, request, queryset):

        for proposal in queryset:

            proposal.status = ProposalStatus.REJECTED
            proposal.save()

            if proposal.organizer:
                Notification.objects.create(
                    user=proposal.organizer,
                    event=proposal.event,
                    notification_type='general',
                    message=f"Your proposal for '{proposal.event.name}' has been rejected."
                )


# =====================================================
# EVENT REPORT ADMIN
# =====================================================
@admin.register(EventReport)
class EventReportAdmin(admin.ModelAdmin):

    list_display = ("name", "event", "created_at")
    exclude = ("event", "created_at")
    change_list_template = "admin/event_report_landing.html"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["title"] = "Feedback Reports"
        return super().changelist_view(request, extra_context=extra_context)

    def feedback_list_view(self, request):

        events = Event.objects.filter(
            status=EventStatus.COMPLETED
        ).order_by("-date")

        rows = []

        for event in events:

            feedback_count = Feedback.objects.filter(event=event).count()

            report, _ = EventReport.objects.get_or_create(
                event=event,
                defaults={"name": f"{event.name} Report"}
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

    def change_view(self, request, object_id, form_url='', extra_context=None):

        report = get_object_or_404(EventReport, pk=object_id)
        event = report.event
        feedbacks = Feedback.objects.filter(event=event)

        stats = {
            "excellent": feedbacks.filter(experience="excellent").count(),
            "good": feedbacks.filter(experience="good").count(),
            "average": feedbacks.filter(experience="average").count(),
            "poor": feedbacks.filter(experience="poor").count(),
        }

        extra_context = extra_context or {}
        extra_context.update({
            "event": event,
            "report": report,
            "feedbacks": feedbacks,
            "stats": stats,
            "has_feedback": feedbacks.exists(),
        })

        return TemplateResponse(request, "admin/event_report_change.html", extra_context)

    def export_feedback_excel(self, request, object_id):

        report = get_object_or_404(EventReport, pk=object_id)
        event = report.event
        feedbacks = Feedback.objects.filter(event=event)

        wb = Workbook()
        ws = wb.active
        ws.title = "Feedback Report"

        ws.append(["Student", "Experience", "Remarks"])

        for fb in feedbacks:
            ws.append([
                fb.student.username if fb.student else "Unknown",
                fb.get_experience_display(),
                fb.message
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        name = (report.name or "report").replace(" ", "_")
        response['Content-Disposition'] = f'attachment; filename="{name}.xlsx"'

        wb.save(response)
        return response

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                'feedback/',
                self.admin_site.admin_view(self.feedback_list_view),
                name="eventreport_feedback_list"
            ),
            path(
                '<int:object_id>/export/',
                self.admin_site.admin_view(self.export_feedback_excel),
                name="eventreport_export"
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