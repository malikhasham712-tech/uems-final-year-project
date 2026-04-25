from django.contrib import admin
from django.urls import reverse, path
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.http import HttpResponse
import openpyxl

from .models import (
    Category,
    Event,
    EventProposal,
    EventRegistration,
    Announcement,
    Notification,
    Feedback,
    EventReport
)

from .notification_router import send_notification


# =====================================================
# CATEGORY
# =====================================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


# =====================================================
# EVENT REPORT (FINAL SAFE VERSION + RANKING)
# =====================================================
@admin.register(EventReport)
class EventReportAdmin(admin.ModelAdmin):

    list_display = ('name', 'event', 'created_at')
    fields = ('name', 'event')

    change_form_template = "admin/event_report_change.html"

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    # -------------------------
    # CUSTOM EXPORT URL
    # -------------------------
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'export/<int:report_id>/',
                self.admin_site.admin_view(self.export_excel),
                name='events_eventreport_export'
            ),
        ]
        return custom_urls + urls

    # -------------------------
    # CHANGE VIEW (SAFE DATA + RANKING)
    # -------------------------
    def change_view(self, request, object_id, form_url='', extra_context=None):

        report = EventReport.objects.filter(pk=object_id).first()

        data = {
            "excellent": [],
            "good": [],
            "average": [],
            "poor": []
        }

        feedbacks = []
        ranking = []

        if report and report.event:
            feedbacks = Feedback.objects.filter(event=report.event)

            for fb in feedbacks:
                key = (fb.experience or "").lower().strip()
                if key in data:
                    data[key].append(fb.student.username)

            score_map = {
                "excellent": 4,
                "good": 3,
                "average": 2,
                "poor": 1
            }

            student_scores = {}

            for fb in feedbacks:
                username = fb.student.username
                score = score_map.get((fb.experience or "").lower(), 3)

                if username not in student_scores:
                    student_scores[username] = 0

                student_scores[username] += score

            ranking = sorted(student_scores.items(), key=lambda x: x[1], reverse=True)

        extra_context = extra_context or {}
        extra_context.update({
            "report": report,
            "data": data,
            "feedbacks": feedbacks,
            "ranking": ranking[:10],
            "show_save": False,
            "show_save_and_continue": False,
            "show_save_and_add_another": False,
        })

        return super().change_view(request, object_id, form_url, extra_context)

    # -------------------------
    # EXPORT EXCEL
    # -------------------------
    def export_excel(self, request, report_id):

        report = EventReport.objects.filter(id=report_id).first()

        if not report or not report.event:
            return HttpResponse("Invalid Report", status=400)

        feedbacks = Feedback.objects.filter(event=report.event)

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Report"

        ws.append(["Student", "Experience", "Message"])

        for fb in feedbacks:
            ws.append([
                fb.student.username,
                (fb.experience or "").lower(),
                fb.message
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        filename = report.name.replace(" ", "_")
        response['Content-Disposition'] = f'attachment; filename={filename}.xlsx'

        wb.save(response)
        return response


# =====================================================
# EVENT ADMIN (CLEAN + SAFE)
# =====================================================
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'venue',
        'date',
        'status',
        'organizer',
        'view_proposals',
        'view_registrations',
        'view_announcements',
        'view_feedback'
    )

    list_filter = ('status', 'category')
    search_fields = ('name',)
    exclude = ('venue', 'description')

    def save_model(self, request, obj, form, change):

        obj.status = (obj.status or "").lower()

        old_status = None
        is_new = obj.pk is None

        if not is_new:
            old_status = Event.objects.get(pk=obj.pk).status
            old_status = (old_status or "").lower()

        super().save_model(request, obj, form, change)

        if is_new and obj.organizer:
            send_notification(
                user=obj.organizer,
                event=obj,
                ntype="event_assigned",
                message=f"🎉 You are assigned as Organizer of '{obj.name}'"
            )

        if old_status != "announced" and obj.status == "announced":

            students = User.objects.filter(is_staff=False, is_active=True)

            for user in students:
                send_notification(
                    user=user,
                    event=obj,
                    ntype="event_announced",
                    message=f"📢 Event Announced: {obj.name}"
                )

            if obj.organizer:
                send_notification(
                    user=obj.organizer,
                    event=obj,
                    ntype="event_announced",
                    message=f"📢 Event Announced: {obj.name}"
                )

        if old_status != "completed" and obj.status == "completed":

            user_ids = list(obj.registrations.values_list("student", flat=True))

            if obj.organizer:
                user_ids.append(obj.organizer.id)

            users = User.objects.filter(id__in=set(user_ids))

            for user in users:
                send_notification(
                    user=user,
                    event=obj,
                    ntype="event_completed",
                    message=f"🎉 Event Completed: {obj.name}"
                )

    def view_proposals(self, obj):
        proposal = obj.proposals.first()
        if proposal:
            url = reverse("admin:events_eventproposal_change", args=[proposal.id])
            return mark_safe(f'<a class="button" href="{url}">View</a>')
        return "No Proposal"

    def view_registrations(self, obj):
        url = reverse("admin:events_eventregistration_changelist") + f"?event__id__exact={obj.id}"
        return mark_safe(f'<a class="button" href="{url}">View</a>')

    def view_announcements(self, obj):
        url = reverse("admin:events_announcement_changelist") + f"?event__id__exact={obj.id}"
        return mark_safe(f'<a class="button" href="{url}">View</a>')

    def view_feedback(self, obj):
        url = reverse("admin:events_feedback_changelist") + f"?event__id__exact={obj.id}"
        return mark_safe(
            f'<a class="button" style="background:#198754;color:white;padding:4px 10px;border-radius:4px;" href="{url}">View</a>'
        )


# =====================================================
# REGISTRATION (READ ONLY ADMIN)
# =====================================================
@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):

    list_display = ('event', 'student', 'created_at')

    readonly_fields = ('event', 'student', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# =====================================================
# FEEDBACK (READ ONLY ADMIN)
# =====================================================
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):

    list_display = ('event', 'student', 'experience', 'message')

    readonly_fields = ('event', 'student', 'experience', 'message')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# =====================================================
# HIDDEN MODELS (SYSTEM ONLY)
# =====================================================
@admin.register(EventProposal)
class EventProposalAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return False


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        return False