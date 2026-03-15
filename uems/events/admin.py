from django.contrib import admin
from .models import Category, Event, EventProposal

# ------------------------------
# Category Admin
# ------------------------------
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    ordering = ('name',)


# ------------------------------
# Event Admin
# ------------------------------
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'venue', 'date', 'status')  # Matches models
    ordering = ('-date',)
    list_filter = ('status', 'category')  # Optional: filter events by status/category
    search_fields = ('name', 'venue')     # Optional: search in admin


# ------------------------------
# EventProposal Admin
# ------------------------------
@admin.action(description='Approve selected proposals and update event venue')
def approve_and_update_venue(modeladmin, request, queryset):
    """
    Custom admin action to approve proposals and automatically
    update the related Event's venue.
    """
    for proposal in queryset:
        # Update proposal status
        proposal.status = 'Approved'
        proposal.save()
        
        # Automatically update Event venue
        proposal.event.venue = proposal.proposed_venue
        proposal.event.save()


class EventProposalAdmin(admin.ModelAdmin):
    list_display = ('event', 'organizer', 'proposed_venue', 'status', 'submitted_at')
    ordering = ('status',)
    actions = [approve_and_update_venue]
    list_filter = ('status',)
    search_fields = ('event__name', 'organizer__username', 'proposed_venue')


# ------------------------------
# Register models
# ------------------------------
admin.site.register(Category, CategoryAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(EventProposal, EventProposalAdmin)