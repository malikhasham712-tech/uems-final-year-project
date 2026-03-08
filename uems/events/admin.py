from django.contrib import admin
from .models import Category, Event, EventProposal


# =========================
# Category Admin
# =========================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    ordering = ('id',)  # Sort by ID ascending
    search_fields = ('name',)


# =========================
# Event Admin
# =========================
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('row_number', 'name', 'category', 'organizer', 'status', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('name', 'organizer__username')
    ordering = ('created_at',)  # Order by creation time ascending

    def row_number(self, obj):
        """
        Returns a sequential row number for display in admin (1,2,3...)
        """
        qs = Event.objects.all().order_by('created_at')  # Ascending
        for index, e in enumerate(qs, start=1):
            if e.pk == obj.pk:
                return index
        return '-'

    row_number.short_description = 'ID'


# =========================
# Event Proposal Admin
# =========================
@admin.register(EventProposal)
class EventProposalAdmin(admin.ModelAdmin):
    list_display = ('event_name', 'organizer', 'proposed_venue', 'status', 'submitted_at')
    list_filter = ('status',)
    search_fields = ('event_name', 'organizer__username')

    def save_model(self, request, obj, form, change):
        """
        When Admin approves a proposal, automatically create an Event.
        Prevent duplicate Events if already created.
        """
        old_status = None
        if obj.pk:
            old_status = EventProposal.objects.get(pk=obj.pk).status

        super().save_model(request, obj, form, change)

        # Only create Event if proposal status changed to Approved
        if obj.status == "Approved" and old_status != "Approved":
            category = Category.objects.first()  # Assign first category as default
            if category:
                # Check if Event already exists for this proposal
                event_exists = Event.objects.filter(
                    name=obj.event_name,
                    organizer=obj.organizer
                ).exists()

                if not event_exists:
                    Event.objects.create(
                        name=obj.event_name,
                        organizer=obj.organizer,
                        description=obj.description,
                        status="approved",
                        category=category
                    )