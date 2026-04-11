from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Category, Event, EventProposal, EventRegistration


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
        'view_registrations'
    )

    def view_proposals(self, obj):
        url = reverse("admin:events_eventproposal_changelist") + f"?event__id__exact={obj.id}"
        return format_html(
            '<a style="color:#fff;background:#2196F3;padding:5px 10px;border-radius:6px;text-decoration:none;" href="{}">Proposals</a>',
            url
        )

    def view_registrations(self, obj):
        url = reverse("admin:events_eventregistration_changelist") + f"?event__id__exact={obj.id}"
        return format_html(
            '<a style="color:#fff;background:#4CAF50;padding:5px 10px;border-radius:6px;text-decoration:none;" href="{}">Registrations</a>',
            url
        )


# ----------------------
# PROPOSAL (HIDDEN FROM ADMIN MENU)
# ----------------------
@admin.register(EventProposal)
class EventProposalAdmin(admin.ModelAdmin):
    list_display = ('event', 'organizer', 'proposed_venue', 'status', 'submitted_at')

    def get_model_perms(self, request):
        return {}


# ----------------------
# REGISTRATION (FIXED FIELD ISSUE)
# ----------------------
@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'event',
        'student_name',
        'registration_no',
        'semester',
        'department',
        'email',
        'contact_no',
        'created_at'
    )

    def get_model_perms(self, request):
        return {}