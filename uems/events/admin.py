from django.contrib import admin
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe

from .models import (
    Category,
    Event,
    EventProposal,
    EventRegistration,
    Announcement,
    Notification,
    Feedback
)

from .notification_router import send_notification


# ----------------------
# CATEGORY
# ----------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


# ----------------------
# EVENT
# ----------------------
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

        # ----------------------
        # NORMALIZE STATUS SAFELY
        # ----------------------
        obj.status = (obj.status or "").lower()

        old_status = None
        is_new = obj.pk is None

        if not is_new:
            old_status = Event.objects.get(pk=obj.pk).status
            old_status = (old_status or "").lower()

        super().save_model(request, obj, form, change)

        # ----------------------
        # 1. ORGANIZER ASSIGNED
        # ----------------------
        if is_new and obj.organizer:
            send_notification(
                user=obj.organizer,
                event=obj,
                ntype="event_assigned",
                message=f"🎉 You are assigned as Organizer of '{obj.name}'"
            )

        # ----------------------
        # 2. EVENT ANNOUNCED
        # ----------------------
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

        # ----------------------
        # 3. EVENT COMPLETED
        # ----------------------
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

    # ----------------------
    # BUTTONS
    # ----------------------
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


# ----------------------
# EVENT PROPOSAL
# ----------------------
@admin.register(EventProposal)
class EventProposalAdmin(admin.ModelAdmin):

    list_display = ('event', 'organizer', 'proposed_venue', 'status', 'submitted_at')

    def get_model_perms(self, request):
        return {}  # hidden from sidebar

    actions = ['approve_proposals', 'reject_proposals']

    def approve_proposals(self, request, queryset):
        for proposal in queryset:

            proposal.status = "accepted"
            proposal.save()

            event = proposal.event
            event.status = "accepted"
            event.save()

            if event.organizer:
                send_notification(
                    user=event.organizer,
                    event=event,
                    ntype="event_assigned",
                    message=f"🎉 Proposal Accepted for '{event.name}'"
                )

    def reject_proposals(self, request, queryset):
        for proposal in queryset:

            proposal.status = "rejected"
            proposal.save()

            if proposal.event.organizer:
                send_notification(
                    user=proposal.event.organizer,
                    event=proposal.event,
                    ntype="general",
                    message=f"❌ Proposal Rejected for '{proposal.event.name}'"
                )


# ----------------------
# REGISTRATION
# ----------------------
@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('student', 'event', 'created_at')

    def get_model_perms(self, request):
        return {}


# ----------------------
# ANNOUNCEMENT
# ----------------------
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):

    list_display = ('event', 'created_by', 'created_at')
    fields = ('event', 'message')

    def save_model(self, request, obj, form, change):

        obj.created_by = request.user
        super().save_model(request, obj, form, change)

        event = obj.event

        user_ids = list(event.registrations.values_list("student", flat=True))

        if event.organizer:
            user_ids.append(event.organizer.id)

        users = User.objects.filter(id__in=set(user_ids))

        for user in users:
            send_notification(
                user=user,
                event=event,
                ntype="announcement",
                message=f"📢 New Announcement: {event.name}"
            )

    def get_model_perms(self, request):
        return {}


# ----------------------
# FEEDBACK
# ----------------------
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('student', 'event', 'rating', 'created_at')

    def get_model_perms(self, request):
        return {}