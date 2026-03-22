from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Category, Event, EventProposal, EventRegistration


# Hide EventProposal
class EventProposalAdmin(admin.ModelAdmin):
    list_display = ('event', 'organizer', 'proposed_venue', 'status', 'submitted_at')

    def get_model_perms(self, request):
        return {}


# Hide EventRegistration
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
        'registered_at'
    )

    def get_model_perms(self, request):
        return {}


# Category
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)


# Event
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
            '<a href="{}" style="background-color:#2196F3;color:white;padding:5px 10px;border-radius:5px;text-decoration:none;">View Proposals</a>',
            url
        )

    def view_registrations(self, obj):
        url = reverse("admin:events_eventregistration_changelist") + f"?event__id__exact={obj.id}"
        return format_html(
            '<a href="{}" style="background-color:#4CAF50;color:white;padding:5px 10px;border-radius:5px;text-decoration:none;">View Registrations</a>',
            url
        )


# Register
admin.site.register(Category, CategoryAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(EventProposal, EventProposalAdmin)
admin.site.register(EventRegistration, EventRegistrationAdmin)