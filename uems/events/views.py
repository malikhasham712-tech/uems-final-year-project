from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib import messages
from django.http import JsonResponse
from .models import Event, EventProposal, EventRegistration
from .forms import ProposalForm, EventRegistrationForm

# ----------------------
# ORGANIZER / ADMIN VIEWS
# ----------------------

@login_required
def my_events(request):
    """Handle BOTH Organizer & Student correctly"""

    # STUDENT
    if hasattr(request.user, 'profile') and request.user.profile.role == 'student':
        registrations = EventRegistration.objects.filter(student=request.user).select_related('event')
        events = [reg.event for reg in registrations]

        return render(request, 'events/my_events.html', {
            'events': events,
            'role': 'student'
        })

    # ORGANIZER / ADMIN
    elif request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'organizer'):
        events = Event.objects.filter(organizer=request.user).annotate(
            total_registrations=Count('registrations')
        )

        return render(request, 'events/my_events.html', {
            'events': events,
            'role': 'organizer'
        })

    messages.error(request, "Access denied.")
    return redirect('events:dashboard')


@login_required
def submit_proposal(request, event_id):
    """Submit proposal for an event."""
    event = get_object_or_404(Event, id=event_id)
    if not request.user.is_superuser and request.user != event.organizer:
        messages.error(request, "Access denied.")
        return redirect('events:dashboard')

    if request.method == 'POST':
        form = ProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.event = event
            proposal.organizer = request.user
            proposal.status = 'pending'
            proposal.save()
            messages.success(request, "Proposal submitted successfully!")
            return redirect('events:view_proposals', event_id=event.id)
    else:
        form = ProposalForm()

    return render(request, 'events/submit_proposal.html', {'form': form, 'event': event})


@login_required
def view_proposals(request, event_id):
    """View all proposals for an event."""
    event = get_object_or_404(Event, id=event_id)
    if not (request.user.is_superuser or request.user == event.organizer):
        messages.error(request, "Access denied.")
        return redirect('events:dashboard')

    proposals = EventProposal.objects.filter(event=event).order_by('-submitted_at')
    form = ProposalForm() if request.method != 'POST' else ProposalForm(request.POST)

    if request.method == 'POST' and form.is_valid() and request.user == event.organizer:
        proposal = form.save(commit=False)
        proposal.event = event
        proposal.organizer = request.user
        proposal.status = 'pending'
        proposal.save()
        messages.success(request, "Proposal submitted successfully!")
        return redirect('events:view_proposals', event_id=event.id)

    return render(request, 'events/view_proposals.html', {
        'event': event,
        'proposals': proposals,
        'form': form
    })


@login_required
def approve_proposal(request, proposal_id):
    proposal = get_object_or_404(EventProposal, id=proposal_id)
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('events:dashboard')

    proposal.status = 'approved'
    proposal.save()
    messages.success(request, f"Proposal '{proposal.name}' approved!")
    return redirect('events:view_proposals', event_id=proposal.event.id)


@login_required
def reject_proposal(request, proposal_id):
    proposal = get_object_or_404(EventProposal, id=proposal_id)
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('events:dashboard')

    proposal.status = 'rejected'
    proposal.save()
    messages.success(request, f"Proposal '{proposal.name}' rejected!")
    return redirect('events:view_proposals', event_id=proposal.event.id)


@login_required
def view_event(request, event_id):
    """Display a single event's details (supports JSON/AJAX)."""
    event = get_object_or_404(Event, id=event_id)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = {
            'id': event.id,
            'name': event.name or "Untitled Event",
            'organizer': event.organizer.get_full_name() if event.organizer else "N/A",
            'venue': event.venue or "TBD",
            'date': event.date.strftime('%d %b %Y') if event.date else "TBD",
            'status': event.status or "unknown",
            'description': event.description or "N/A",
        }
        return JsonResponse(data)

    return render(request, 'events/view_event.html', {'event': event})


@login_required
def event_registrations(request, event_id):
    """List all registrations for a specific event."""
    event = get_object_or_404(Event, id=event_id)
    if not request.user.is_superuser and request.user != event.organizer:
        messages.error(request, "Access denied.")
        return redirect('events:dashboard')

    registrations = EventRegistration.objects.filter(event=event)
    return render(request, 'events/event_registrations.html', {
        'event': event,
        'registrations': registrations,
        'total': registrations.count()
    })


# ----------------------
# STUDENT EVENTS VIEWS
# ----------------------
@login_required
def available_events(request):
    """Show all announced events for students."""
    events = Event.objects.filter(status='announced')
    return render(request, 'events/available_events.html', {'events': events})


@login_required
def register_event(request, event_id):
    """Register a student for an event."""
    if hasattr(request.user, 'profile') and request.user.profile.role != 'student':
        messages.error(request, "You are not allowed to register for events.")
        return redirect('events:dashboard')

    event = get_object_or_404(Event, id=event_id, status='announced')

    if EventRegistration.objects.filter(event=event, student=request.user).exists():
        messages.info(request, "You are already registered for this event!")
        return redirect('events:available_events')

    if request.method == 'POST':
        form = EventRegistrationForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.event = event
            registration.student = request.user
            registration.save()
            messages.success(request, "Successfully registered!")
            return redirect('events:available_events')
    else:
        form = EventRegistrationForm(initial={
            'student_name': request.user.get_full_name() or request.user.username,
            'email': request.user.email
        })

    return render(request, 'events/register_event.html', {'form': form, 'event': event})


# ----------------------
# DASHBOARD (UNIFIED)
# ----------------------

@login_required
def dashboard(request):
    """Unified dashboard for both students and organizers."""
    user = request.user

    if hasattr(user, 'profile') and user.profile.role == 'organizer':
        # ORGANIZER DASHBOARD
        user_events = Event.objects.filter(organizer=user)
        total_events = user_events.count()
        total_registrations = EventRegistration.objects.filter(event__in=user_events).count()
        context = {
            'user_events': user_events,
            'total_events': total_events,
            'total_registrations': total_registrations,
            'role': 'organizer'
        }
    else:
        # STUDENT DASHBOARD
        registrations = EventRegistration.objects.filter(student=user).select_related('event')
        my_events = [reg.event for reg in registrations]
        announced_events = Event.objects.filter(status='announced')
        context = {
            'my_events': my_events,
            'announced_events': announced_events,
            'role': 'student'
        }

    return render(request, 'accounts/dashboard.html', context)