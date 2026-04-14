from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.contrib.auth.models import User

from .models import (
    Category,
    Event,
    EventProposal,
    EventRegistration,
    Announcement,
    Notification,
    Feedback
)


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
        'view_announcements'
    )

    list_filter = ('status', 'category')
    search_fields = ('name',)

    exclude = ('venue', 'description')

    def save_model(self, request, obj, form, change):
        old_status = None
        is_new = obj.pk is None

        if not is_new:
            old_status = Event.objects.get(pk=obj.pk).status

        super().save_model(request, obj, form, change)

        # Organizer assigned
        if is_new and obj.organizer:
            Notification.objects.create(
                user=obj.organizer,
                event=obj,
                message=f"🎉 You are assigned as Organizer of '{obj.name}'"
            )

        # Event Announced
        if old_status != "Announced" and obj.status == "Announced":

            users = User.objects.filter(is_active=True).only("id")

            for user in users:
                Notification.objects.create(
                    user=user,
                    event=obj,
                    message=f"📢 Event Announced: {obj.name}"
                )

            if obj.organizer:
                Notification.objects.create(
                    user=obj.organizer,
                    event=obj,
                    message=f"📌 Your event '{obj.name}' is now Announced"
                )

    def view_proposals(self, obj):
        url = reverse("admin:events_eventproposal_changelist") + f"?event__id__exact={obj.id}"
        return format_html('<a class="button" href="{}">Proposals</a>', url)

    def view_registrations(self, obj):
        url = reverse("admin:events_eventregistration_changelist") + f"?event__id__exact={obj.id}"
        return format_html('<a class="button" href="{}">Registrations</a>', url)

    def view_announcements(self, obj):
        url = reverse("admin:events_announcement_changelist") + f"?event__id__exact={obj.id}"
        return format_html('<a class="button" href="{}">Announcements</a>', url)


# ----------------------
# PROPOSAL
# ----------------------
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

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [f.name for f in obj._meta.fields if f.name != "status"]
        return []

    actions = ['approve_proposals', 'reject_proposals']

    @admin.action(description="Approve selected proposals")
    def approve_proposals(self, request, queryset):

        for proposal in queryset:
            proposal.status = "Accepted"
            proposal.save()

            event = proposal.event
            event.status = "Accepted"
            event.save()

            if event.organizer:
                Notification.objects.create(
                    user=event.organizer,
                    event=event,
                    message=f"🎉 Your proposal for '{event.name}' is Accepted"
                )

    @admin.action(description="Reject selected proposals")
    def reject_proposals(self, request, queryset):

        for proposal in queryset:
            proposal.status = "Rejected"
            proposal.save()

            Notification.objects.create(
                user=proposal.organizer,
                event=proposal.event,
                message=f"❌ Proposal Rejected for '{proposal.event.name}'"
            )


# ----------------------
# REGISTRATION
# ----------------------
@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'event', 'student_name', 'registration_no',
        'semester', 'department', 'email', 'contact_no', 'created_at'
    )
    search_fields = ('student_name', 'registration_no', 'event__name')


# ----------------------
# ANNOUNCEMENT
# ----------------------
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('event', 'created_by', 'created_at')

    def get_model_perms(self, request):
        return {}


# ----------------------
# NOTIFICATION
# ----------------------
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'is_read', 'created_at')

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