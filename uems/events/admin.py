from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.urls import path, reverse
from django.template.response import TemplateResponse
from django.utils.html import format_html

from openpyxl import Workbook

from .models import (
    Category,
    Event,
    EventRegistration,
    Announcement,
    Feedback,
    EventProposal,
    EventReport
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
        'feedback_btn',
    )

    list_filter = ('status', 'category')

    search_fields = ('name',)

    # -------------------------------------------------
    # PROPOSALS BUTTON
    # -------------------------------------------------
    def proposal_btn(self, obj):

        url = reverse(
            'events:view_proposals',
            args=[obj.id]
        )

        return format_html(
            '<a class="button" href="{}">Proposals</a>',
            url
        )

    proposal_btn.short_description = "Proposals"

    # -------------------------------------------------
    # REGISTRATIONS BUTTON
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

    change_list_template = "admin/event_report_landing.html"

    # -------------------------------------------------
    # SAVE
    # -------------------------------------------------
    def save_model(self, request, obj, form, change):

        super().save_model(
            request,
            obj,
            form,
            change
        )

    # -------------------------------------------------
    # CHANGE LIST TITLE
    # -------------------------------------------------
    def changelist_view(self, request, extra_context=None):

        extra_context = extra_context or {}

        extra_context["title"] = "Feedback Reports"

        return super().changelist_view(
            request,
            extra_context=extra_context
        )

    # -------------------------------------------------
    # FEEDBACK LIST PAGE
    # -------------------------------------------------
    def feedback_list_view(self, request):

        events = Event.objects.filter(
            status="completed"
        ).order_by("-date")

        rows = []

        for event in events:

            feedback_count = Feedback.objects.filter(
                event=event
            ).count()

            # AUTO CREATE REPORT
            report, created = EventReport.objects.get_or_create(
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
            {
                "rows": rows
            }
        )

    # -------------------------------------------------
    # DETAIL VIEW
    # -------------------------------------------------
    def change_view(
        self,
        request,
        object_id,
        form_url='',
        extra_context=None
    ):

        report = get_object_or_404(
            EventReport,
            pk=object_id
        )

        event = report.event

        feedbacks = Feedback.objects.filter(
            event=event
        )

        stats = {

            "excellent": feedbacks.filter(
                experience="excellent"
            ).count(),

            "good": feedbacks.filter(
                experience="good"
            ).count(),

            "average": feedbacks.filter(
                experience="average"
            ).count(),

            "poor": feedbacks.filter(
                experience="poor"
            ).count(),
        }

        has_feedback = feedbacks.exists()

        extra_context = extra_context or {}

        extra_context.update({

            "event": event,

            "report": report,

            "feedbacks": feedbacks,

            "stats": stats,

            "has_feedback": has_feedback,
        })

        return TemplateResponse(
            request,
            "admin/event_report_change.html",
            extra_context
        )

    # -------------------------------------------------
    # EXPORT EXCEL
    # -------------------------------------------------
    def export_feedback_excel(self, request, object_id):

        report = get_object_or_404(
            EventReport,
            pk=object_id
        )

        event = report.event

        feedbacks = Feedback.objects.filter(
            event=event
        ) if event else Feedback.objects.none()

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

        safe_name = (
            report.name or "report"
        ).replace(" ", "_")

        response[
            'Content-Disposition'
        ] = f'attachment; filename="{safe_name}_feedback.xlsx"'

        wb.save(response)

        return response

    # -------------------------------------------------
    # CUSTOM URLS
    # -------------------------------------------------
    def get_urls(self):

        urls = super().get_urls()

        custom_urls = [

            path(
                'feedback/',
                self.admin_site.admin_view(
                    self.feedback_list_view
                ),
                name="eventreport_feedback_list"
            ),

            path(
                '<int:object_id>/export/',
                self.admin_site.admin_view(
                    self.export_feedback_excel
                ),
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
admin.site.register(EventProposal, HiddenAdmin)
admin.site.register(Announcement, HiddenAdmin)