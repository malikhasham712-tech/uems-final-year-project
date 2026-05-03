from django.contrib import admin
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.urls import path
from django.template.response import TemplateResponse

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
        'organizer'
    )
    list_filter = ('status', 'category')
    search_fields = ('name',)


# =====================================================
# EVENT REPORT ADMIN (CLEAN + STABLE)
# =====================================================
@admin.register(EventReport)
class EventReportAdmin(admin.ModelAdmin):

    list_display = ("name", "event", "created_at")
    readonly_fields = ("created_at",)

    change_list_template = "admin/event_report_landing.html"

    # -------------------------------------------------
    # SAVE (MANUAL SYSTEM ONLY)
    # -------------------------------------------------
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    # -------------------------------------------------
    # LIST PAGE TITLE
    # -------------------------------------------------
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["title"] = "Feedback Reports"
        return super().changelist_view(request, extra_context=extra_context)

    # -------------------------------------------------
    # FEEDBACK LIST PAGE (OPTIONAL DASHBOARD ENTRY)
    # -------------------------------------------------
    def feedback_list_view(self, request):

        events = Event.objects.filter(
            status="completed",
            feedbacks__isnull=False
        ).distinct()

        rows = []

        for event in events:
            report = EventReport.objects.filter(event=event).first()

            rows.append({
                "event": event,
                "report": report,
                "feedback_count": Feedback.objects.filter(event=event).count()
            })

        return TemplateResponse(request, "admin/event_report_list.html", {
            "rows": rows
        })

    # -------------------------------------------------
    # DETAIL VIEW (DASHBOARD VIEW - SAFE)
    # -------------------------------------------------
    def change_view(self, request, object_id, form_url='', extra_context=None):

        report = get_object_or_404(EventReport, pk=object_id)
        event = report.event

        # SAFE HANDLING (NO EVENT BREAK)
        if event:
            feedbacks = Feedback.objects.filter(event=event)

            stats = {
                "excellent": feedbacks.filter(experience="excellent").count(),
                "good": feedbacks.filter(experience="good").count(),
                "average": feedbacks.filter(experience="average").count(),
                "poor": feedbacks.filter(experience="poor").count(),
            }
        else:
            feedbacks = Feedback.objects.none()
            stats = {
                "excellent": 0,
                "good": 0,
                "average": 0,
                "poor": 0,
            }

        extra_context = extra_context or {}
        extra_context.update({
            "event": event,
            "report": report,
            "feedbacks": feedbacks,
            "stats": stats,
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

        report = get_object_or_404(EventReport, pk=object_id)
        event = report.event

        feedbacks = Feedback.objects.filter(event=event) if event else Feedback.objects.none()

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

        safe_name = (report.name or "report").replace(" ", "_")
        response['Content-Disposition'] = f'attachment; filename="{safe_name}_feedback.xlsx"'

        wb.save(response)
        return response

    # -------------------------------------------------
    # URLS
    # -------------------------------------------------
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
admin.site.register(EventProposal, HiddenAdmin)
admin.site.register(Announcement, HiddenAdmin)