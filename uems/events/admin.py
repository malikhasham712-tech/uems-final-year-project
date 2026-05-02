from django.contrib import admin
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from django.shortcuts import render, get_object_or_404

from .models import (
    Category,
    Event,
    EventRegistration,
    Announcement,
    Feedback,
    EventProposal
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
        'venue',
        'date',
        'status',
        'organizer',
        'feedback_report_button'
    )

    def feedback_report_button(self, obj):

        url = reverse("admin:events_feedback_dashboard")

        return mark_safe(
            f'<a class="button" style="background:#0d6efd;color:white;padding:4px 10px;border-radius:4px;" href="{url}">Feedback Report</a>'
        )

    feedback_report_button.short_description = "Report"


# =====================================================
# CUSTOM ADMIN REPORT SYSTEM (SAFE)
# =====================================================
class FeedbackReportAdminView:

    def get_urls(self):
        return [
            path(
                'feedback-report/',
                self.dashboard,
                name='events_feedback_dashboard'
            ),
            path(
                'feedback-report/<int:event_id>/',
                self.event_report,
                name='events_event_feedback_report'
            ),
        ]

    # ---------------------------
    # DASHBOARD (ALL EVENTS)
    # ---------------------------
    def dashboard(self, request):

        events = Event.objects.all().order_by('-date')

        data = []

        for event in events:
            count = Feedback.objects.filter(event=event).count()

            data.append({
                "event": event,
                "count": count
            })

        return render(request, "admin/feedback_dashboard.html", {
            "data": data
        })

    # ---------------------------
    # SINGLE EVENT REPORT
    # ---------------------------
    def event_report(self, request, event_id):

        event = get_object_or_404(Event, id=event_id)
        feedbacks = Feedback.objects.filter(event=event)

        stats = {
            "excellent": [],
            "good": [],
            "average": [],
            "poor": []
        }

        for fb in feedbacks:
            if fb.experience in stats:
                stats[fb.experience].append(
                    fb.student.username if fb.student else "Unknown"
                )

        return render(request, "admin/event_feedback_report.html", {
            "event": event,
            "feedbacks": feedbacks,
            "stats": stats
        })


# =====================================================
# ATTACH CUSTOM URLS SAFELY (NO MONKEY PATCH)
# =====================================================
from django.contrib import admin as django_admin

_feedback_view = FeedbackReportAdminView()

def custom_admin_urls(get_urls):
    def wrapper():
        return _feedback_view.get_urls() + get_urls()
    return wrapper

django_admin.site.get_urls = custom_admin_urls(django_admin.site.get_urls)


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