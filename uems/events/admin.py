from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Category, Event, EventProposal, EventRegistration, Announcement, Notification, Feedback


# ----------------------
# CATEGORY
# ----------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


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
        'view_proposals',
        'view_registrations',
        'view_announcements'
    )

    def view_proposals(self, obj):
        url = reverse("admin:events_eventproposal_changelist") + f"?event__id__exact={obj.id}"
        return format_html('<a class="btn btn-primary btn-sm" href="{}">Proposals</a>', url)

    def view_registrations(self, obj):
        url = reverse("admin:events_eventregistration_changelist") + f"?event__id__exact={obj.id}"
        return format_html('<a class="btn btn-success btn-sm" href="{}">Registrations</a>', url)

    def view_announcements(self, obj):
        url = reverse("admin:events_announcement_changelist") + f"?event__id__exact={obj.id}"
        return format_html('<a class="btn btn-warning btn-sm" href="{}">Announcements</a>', url)


# ----------------------
# PROPOSAL
# ----------------------
@admin.register(EventProposal)
class EventProposalAdmin(admin.ModelAdmin):
    list_display = ('event', 'organizer', 'proposed_venue', 'status', 'submitted_at')


# ----------------------
# REGISTRATION
# ----------------------
@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'event', 'student_name', 'registration_no',
        'semester', 'department', 'email', 'contact_no', 'created_at'
    )


# ----------------------
# HIDE FROM SIDEBAR (CLEAN ADMIN)
# ----------------------
@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('event', 'created_by', 'created_at')

    def get_model_perms(self, request):
        return {}


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'announcement', 'is_read', 'created_at')

    def get_model_perms(self, request):
        return {}


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('student', 'event', 'rating', 'created_at')

    def get_model_perms(self, request):
        return {}