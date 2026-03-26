from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Event, EventProposal, EventRegistration
from .forms import ProposalForm, EventRegistrationForm

# ----------------------
# ORGANIZER VIEWS
# ----------------------
@login_required
def my_events(request):
    events = Event.objects.filter(organizer=request.user)
    submitted_events = EventProposal.objects.filter(
        organizer=request.user
    ).values_list('event_id', flat=True)

    return render(request, 'events/my_events.html', {
        'events': events,
        'submitted_events': list(submitted_events)
    })


@login_required
def submit_proposal(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        form = ProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.event = event
            proposal.organizer = request.user
            proposal.save()
            return redirect('my_proposals')
    else:
        form = ProposalForm()

    return render(request, 'events/submit_proposal.html', {'form': form, 'event': event})


@login_required
def my_proposals(request):
    proposals = EventProposal.objects.filter(organizer=request.user)
    return render(request, 'events/my_proposals.html', {'proposals': proposals})


@login_required
def view_proposals(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    proposals = EventProposal.objects.filter(event=event, organizer=request.user)
    return render(request, 'events/view_proposals.html', {'event': event, 'proposals': proposals})


@login_required
def view_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    proposals = EventProposal.objects.filter(event=event)
    return render(request, 'events/view_event.html', {'event': event, 'proposals': proposals})


# ----------------------
# STUDENT VIEWS
# ----------------------
@login_required
def student_events(request):
    events = Event.objects.filter(status='announced')
    registered_events = EventRegistration.objects.filter(student=request.user).values_list('event_id', flat=True)
    return render(request, 'events/student_events.html', {
        'events': events,
        'registered_events': list(registered_events)
    })


@login_required
def register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if EventRegistration.objects.filter(event=event, student=request.user).exists():
        return redirect('student_events')

    if request.method == 'POST':
        form = EventRegistrationForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.event = event
            registration.student = request.user
            registration.save()
            return redirect('student_events')
    else:
        form = EventRegistrationForm(initial={
            'student_name': request.user.get_full_name() or request.user.username,
            'email': request.user.email
        })

    return render(request, 'events/register_event.html', {'form': form, 'event': event})


# ----------------------
# ORGANIZER → VIEW REGISTRATIONS
# ----------------------
@login_required
def event_registrations(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # 🔐 Only organizer or admin allowed
    if request.user != event.organizer and not request.user.is_superuser:
        return redirect('my_events')

    registrations = EventRegistration.objects.filter(event=event)

    return render(request, 'events/event_registrations.html', {
        'event': event,
        'registrations': registrations
    })