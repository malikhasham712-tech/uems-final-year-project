from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

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
# EVENT (CORE LOGIC HERE 🔥)
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
    search_fields = ('name', 'venue')
    list_editable = ('status', 'venue', 'date', 'organizer')

    def save_model(self, request, obj, form, change):

        old_obj = None
        if obj.pk:
            old_obj = Event.objects.get(pk=obj.pk)

        super().save_model(request, obj, form, change)

        # =========================
        # 🔥 ORGANIZER ASSIGNED
        # =========================
        if old_obj and old_obj.organizer != obj.organizer and obj.organizer:
            Notification.objects.create(
                user=obj.organizer,
                event=obj,
                message=f"🎉 You are now Organizer of '{obj.name}'"
            )

        # =========================
        # 🔥 EVENT ANNOUNCED
        # =========================
        if old_obj and old_obj.status != "Announced" and obj.status == "Announced":

            # Students
            student_ids = obj.registrations.values_list("student", flat=True).distinct()

            for sid in student_ids:
                Notification.objects.create(
                    user_id=sid,
                    event=obj,
                    message=f"📢 New Event Announced: {obj.name} is now open for registration."
                )

            # Organizer
            if obj.organizer:
                Notification.objects.create(
                    user=obj.organizer,
                    event=obj,
                    message=f"📌 Your event '{obj.name}' has been officially Announced."
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
    list_display = ('event', 'organizer', 'proposed_venue', 'status', 'submitted_at')
    list_filter = ('status',)
    search_fields = ('event__name', 'organizer__username')


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
# ANNOUNCEMENT (HIDDEN)
# ----------------------
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('event', 'created_by', 'created_at')

    def get_model_perms(self, request):
        return {}


# ----------------------
# NOTIFICATION (HIDDEN)
# ----------------------
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'is_read', 'created_at')

    def get_model_perms(self, request):
        return {}


# ----------------------
# FEEDBACK (HIDDEN)
# ----------------------
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('student', 'event', 'rating', 'created_at')

    def get_model_perms(self, request):
        return {}