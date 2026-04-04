from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib import messages
from .models import Event, EventProposal, EventRegistration
from .forms import ProposalForm, EventRegistrationForm

# ----------------------
# ORGANIZER / ADMIN VIEWS
# ----------------------
@login_required
def my_events(request):
    """Show events depending on user role (Organizer/Admin)"""
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
    """Organizer submits proposal for assigned event"""
    event = get_object_or_404(Event, id=event_id)

    if not request.user.is_superuser and request.user != event.organizer:
        messages.error(request, "Access denied.")
        return redirect('my_events')

    if request.method == 'POST':
        form = ProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.event = event
            proposal.organizer = request.user
            proposal.status = 'pending'
            proposal.save()
            messages.success(request, "Proposal submitted successfully!")
            return redirect('view_proposals', event_id=event.id)
    else:
        form = ProposalForm()

    return render(request, 'events/submit_proposal.html', {'form': form, 'event': event})


@login_required
def view_proposals(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not (request.user.is_superuser or request.user == event.organizer):
        messages.error(request, "Access denied.")
        return redirect('my_events')

    proposals = EventProposal.objects.filter(event=event).order_by('-submitted_at')

    form = ProposalForm() if request.method != 'POST' else ProposalForm(request.POST)
    if request.method == 'POST' and form.is_valid() and request.user == event.organizer:
        proposal = form.save(commit=False)
        proposal.event = event
        proposal.organizer = request.user
        proposal.status = 'pending'
        proposal.save()
        messages.success(request, "Proposal submitted successfully!")
        return redirect('view_proposals', event_id=event.id)

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
        return redirect('my_events')

    proposal.status = 'approved'
    proposal.save()
    messages.success(request, f"Proposal '{proposal.name}' approved!")
    return redirect('view_proposals', event_id=proposal.event.id)


@login_required
def reject_proposal(request, proposal_id):
    proposal = get_object_or_404(EventProposal, id=proposal_id)
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('my_events')

    proposal.status = 'rejected'
    proposal.save()
    messages.success(request, f"Proposal '{proposal.name}' rejected!")
    return redirect('view_proposals', event_id=proposal.event.id)


@login_required
def view_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    proposals = EventProposal.objects.filter(event=event)
    return render(request, 'events/view_event.html', {'event': event, 'proposals': proposals})


@login_required
def event_registrations(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not request.user.is_superuser and request.user != event.organizer:
        messages.error(request, "Access denied.")
        return redirect('my_events')

    registrations = EventRegistration.objects.filter(event=event)
    return render(request, 'events/event_registrations.html', {
        'event': event,
        'registrations': registrations,
        'total': registrations.count()
    })


@login_required
def my_proposals(request):
    proposals = EventProposal.objects.filter(organizer=request.user)
    return render(request, 'events/my_proposals.html', {'proposals': proposals})


# ----------------------
# STUDENT VIEWS
# ----------------------
@login_required
def student_events(request):
    events = Event.objects.filter(status='announced')
    registered_events = EventRegistration.objects.filter(student=request.user).values_list('event_id', flat=True)
    return render(request, 'events/student_events.html', {
        'events': events,
        'registered_events': list(registered_events),
        'can_register': True
    })


@login_required
def register_event(request, event_id):
    if hasattr(request.user, 'profile') and request.user.profile.role != 'student':
        messages.error(request, "You are not allowed to register for events.")
        return redirect('my_events')

    event = get_object_or_404(Event, id=event_id, status='announced')

    if EventRegistration.objects.filter(event=event, student=request.user).exists():
        messages.info(request, "You are already registered for this event!")
        return redirect('student_events')

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

    return render(request, 'events/register_event.html', {'form': form, 'event': event})

@login_required
def dashboard(request):
    # Organizer / Admin data
    if request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'organizer'):
        user_events = Event.objects.filter(
            organizer=request.user
        ) if not request.user.is_superuser else Event.objects.all()
        total_events = user_events.count()
        total_registrations = EventRegistration.objects.filter(event__in=user_events).count()
        context = {
            'user_events': user_events,
            'total_events': total_events,
            'total_registrations': total_registrations,
        }

    # Student data
    elif hasattr(request.user, 'profile') and request.user.profile.role == 'student':
        student_events = Event.objects.filter(status='announced')
        registered_events = EventRegistration.objects.filter(
            student=request.user
        ).values_list('event_id', flat=True)
        context = {
            'student_events': student_events,
            'registered_events': list(registered_events),
        }

    else:
        messages.error(request, "Access denied.")
        return redirect('dashboard')

    return render(request, 'events/dashboard.html', context)