from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Event, EventProposal, EventRegistration
from .forms import ProposalForm


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

    return render(request, 'events/submit_proposal.html', {
        'form': form,
        'event': event
    })


@login_required
def my_proposals(request):
    proposals = EventProposal.objects.filter(organizer=request.user)

    return render(request, 'events/my_proposals.html', {
        'proposals': proposals
    })


@login_required
def view_proposals(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    proposals = EventProposal.objects.filter(
        event=event,
        organizer=request.user
    )

    return render(request, 'events/view_proposals.html', {
        'event': event,
        'proposals': proposals
    })


@login_required
def view_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    proposals = EventProposal.objects.filter(event=event)

    return render(request, 'events/view_event.html', {
        'event': event,
        'proposals': proposals,
    })


# ----------------------
# STUDENT VIEWS (NEW)
# ----------------------

@login_required
def student_events(request):
    # Only announced events
    events = Event.objects.filter(status='announced')

    # already registered events
    registered_events = EventRegistration.objects.filter(
        student=request.user
    ).values_list('event_id', flat=True)

    return render(request, 'events/student_events.html', {
        'events': events,
        'registered_events': list(registered_events)
    })


@login_required
def register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # prevent duplicate registration
    if EventRegistration.objects.filter(event=event, student=request.user).exists():
        return redirect('student_events')

    if request.method == 'POST':
        EventRegistration.objects.create(
            event=event,
            student=request.user,
            student_name=request.POST.get('student_name'),
            registration_no=request.POST.get('registration_no'),
            semester=request.POST.get('semester'),
            department=request.POST.get('department'),
            email=request.POST.get('email'),
            contact_no=request.POST.get('contact_no'),
        )
        return redirect('student_events')

    return render(request, 'events/register_event.html', {
        'event': event
    })


# ----------------------
# ORGANIZER → VIEW REGISTRATIONS
# ----------------------

@login_required
def event_registrations(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    registrations = EventRegistration.objects.filter(event=event)

    return render(request, 'events/event_registrations.html', {
        'event': event,
        'registrations': registrations
    })