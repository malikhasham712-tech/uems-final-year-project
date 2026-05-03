from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

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
# EVENT REPORT ADMIN (SAFE DASHBOARD VERSION)
# =====================================================
@admin.register(EventReport)
class EventReportAdmin(admin.ModelAdmin):

    list_display = ("name", "event", "created_at")
    readonly_fields = ("name", "event", "created_at")

    # -------------------------------------
    # LIST PAGE
    # -------------------------------------
    def changelist_view(self, request, extra_context=None):

        events = Event.objects.filter(
            status='completed',
            feedbacks__isnull=False
        ).distinct()

        data = []

        for event in events:
            report = self.get_or_create_report(event)

            data.append({
                "event": event,
                "report": report,
                "url": reverse(
                    "admin:events_eventreport_change",
                    args=[report.id]
                )
            })

        extra_context = extra_context or {}
        extra_context["data"] = data

        return super().changelist_view(request, extra_context=extra_context)

    # -------------------------------------
    # DETAIL PAGE
    # -------------------------------------
    def change_view(self, request, object_id, form_url='', extra_context=None):

        report = EventReport.objects.get(id=object_id)
        event = report.event

        feedbacks = Feedback.objects.filter(event=event)

        stats = {
            "excellent": [],
            "good": [],
            "average": [],
            "poor": []
        }

        for fb in feedbacks:
            level = fb.experience
            if level in stats:
                stats[level].append(
                    fb.student.username if fb.student else "Unknown"
                )

        extra_context = extra_context or {}
        extra_context.update({
            "event": event,
            "feedbacks": feedbacks,
            "stats": stats,
            "report": report
        })

        return super().change_view(
            request,
            object_id,
            form_url,
            extra_context=extra_context
        )

    # -------------------------------------
    # AUTO CREATE REPORT
    # -------------------------------------
    def get_or_create_report(self, event):
        report, _ = EventReport.objects.get_or_create(
            event=event,
            defaults={"name": f"{event.name} Report"}
        )
        return report


# =====================================================
# HIDDEN MODELS (NOT SHOWN IN ADMIN SIDEBAR)
# =====================================================
class HiddenAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return False


admin.site.register(EventRegistration, HiddenAdmin)
admin.site.register(Feedback, HiddenAdmin)
admin.site.register(EventProposal, HiddenAdmin)
admin.site.register(Announcement, HiddenAdmin)