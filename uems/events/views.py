from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib import messages
from .models import Event, EventProposal, EventRegistration
from .forms import ProposalForm, EventRegistrationForm

# ----------------------
# ORGANIZER VIEWS
# ----------------------
@login_required
def my_events(request):
    """Dashboard: show events depending on user role"""
    if request.user.is_superuser:
        events = Event.objects.annotate(total_registrations=Count('registrations'))
    elif hasattr(request.user, 'profile') and request.user.profile.role == 'organizer':
        events = Event.objects.filter(organizer=request.user).annotate(total_registrations=Count('registrations'))
    else:
        messages.error(request, "Access denied.")
        return redirect('student_events')

    return render(request, 'events/my_events.html', {'events': events})

@login_required
def submit_proposal(request, event_id):
    """
    Organizer: submit a proposal for a specific event.
    """
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        form = ProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.event = event
            proposal.organizer = request.user
            proposal.save()
            messages.success(request, "Proposal submitted successfully!")
            return redirect('my_proposals')
    else:
        form = ProposalForm()

    return render(request, 'events/submit_proposal.html', {
        'form': form,
        'event': event
    })


@login_required
def my_proposals(request):
    """
    Organizer: list all proposals submitted by the logged-in organizer.
    """
    proposals = EventProposal.objects.filter(organizer=request.user)
    return render(request, 'events/my_proposals.html', {'proposals': proposals})


from django.core.exceptions import PermissionDenied

@login_required
def view_proposals(request, event_id):
    if not (request.user.is_superuser or request.user.profile.role == 'organizer'):
        raise PermissionDenied()

    event = get_object_or_404(Event, id=event_id)
    proposals = EventProposal.objects.filter(event=event).order_by('-submitted_at')

    return render(request, 'events/view_proposals.html', {
        'event': event,
        'proposals': proposals
    })



@login_required
def view_event(request, event_id):
    """
    Organizer/Admin: view event details including proposals.
    """
    event = get_object_or_404(Event, id=event_id)
    proposals = EventProposal.objects.filter(event=event)
    return render(request, 'events/view_event.html', {
        'event': event,
        'proposals': proposals
    })


# ----------------------
# STUDENT VIEWS
# ----------------------
@login_required
def student_events(request):
    """
    Student dashboard (New students only):
    Shows only announced events. Registration allowed.
    Proposals and registrations view NOT shown.
    """
    # Only announced events
    events = Event.objects.filter(status='announced')

    # Already registered events
    registered_events = EventRegistration.objects.filter(
        student=request.user
    ).values_list('event_id', flat=True)

    return render(request, 'events/student_events.html', {
        'events': events,
        'registered_events': list(registered_events),
        # new students can always register if event is announced
        'can_register': True,
    })

@login_required
def register_event(request, event_id):
    print("REGISTER EVENT VIEW HIT")
    """
    ONLY new students can open and submit registration form.
    Old organizers/admins are blocked.
    """

    # ❌ Block Admin & Organizers (Old Users)
    if request.user.is_superuser or (
        hasattr(request.user, 'profile') and 
        request.user.profile.role in ['organizer', 'admin']
    ):
        messages.error(request, "You are not allowed to register for events.")
        return redirect('my_events')

    # ✅ Get event
    event = get_object_or_404(Event, id=event_id, status='announced')

    # ❌ Prevent duplicate registration
    if EventRegistration.objects.filter(event=event, student=request.user).exists():
        messages.info(request, "You are already registered for this event!")
        return redirect('student_events')

    # ✅ FORM LOGIC
    if request.method == 'POST':
        form = EventRegistrationForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.event = event
            registration.student = request.user
            registration.save()

            messages.success(request, "Successfully registered!")
            return redirect('student_events')
    else:
        form = EventRegistrationForm(initial={
            'student_name': request.user.get_full_name() or request.user.username,
            'email': request.user.email
        })

    return render(request, 'events/register_event.html', {
        'form': form,
        'event': event
    })


# ----------------------
# ORGANIZER/ADMIN → VIEW REGISTRATIONS
# ----------------------
@login_required
def view_proposals(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Only admin or organizer of the event
    if not (request.user.is_superuser or request.user == event.organizer):
        messages.error(request, "Access denied.")
        return redirect('my_events')

    proposals = EventProposal.objects.filter(event=event)

    return render(request, 'events/view_proposals.html', {
        'event': event,
        'proposals': proposals
    })

@login_required
def event_registrations(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Admin sees all; organizer sees only their event
    if not (request.user.is_superuser or request.user == event.organizer):
        messages.error(request, "Access denied.")
        return redirect('my_events')

    registrations = EventRegistration.objects.filter(event=event)

    return render(request, 'events/event_registrations.html', {
        'event': event,
        'registrations': registrations,
        'total': registrations.count()
    })