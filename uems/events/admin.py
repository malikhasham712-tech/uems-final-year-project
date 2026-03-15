from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Category, Event, EventProposal


# -----------------------------
# Hide EventProposal from sidebar
# -----------------------------
class EventProposalAdmin(admin.ModelAdmin):
    list_display = ('event', 'organizer', 'proposed_venue', 'status', 'submitted_at')

    def get_model_perms(self, request):
        return {}  # hides it from admin sidebar


# -----------------------------
# Category Admin
# -----------------------------
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('name',)


# -----------------------------
# Event Admin
# -----------------------------
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'venue', 'date', 'status', 'view_proposals')
    ordering = ('-date',)

    def view_proposals(self, obj):
        url = (
            reverse("admin:events_eventproposal_changelist")
            + f"?event__id__exact={obj.id}"
        )
        return format_html('<a class="button" href="{}">View Proposals</a>', url)

    view_proposals.short_description = "Proposals"


# -----------------------------
# Register Models
# -----------------------------
admin.site.register(Category, CategoryAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(EventProposal, EventProposalAdmin)