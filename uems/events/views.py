from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Event, EventProposal
from .forms import ProposalForm


# My Events

@login_required
def my_events(request):
    events = Event.objects.filter(organizer=request.user)

    # events jahan proposal already submit ho chuka
    submitted_events = EventProposal.objects.filter(
        organizer=request.user
    ).values_list('event_id', flat=True)

    return render(request, 'events/my_events.html', {
        'events': events,
        'submitted_events': list(submitted_events)
    })

# Submit Proposal for specific event
@login_required
def submit_proposal(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        form = ProposalForm(request.POST)

        if form.is_valid():
            proposal = form.save(commit=False)

            proposal.event = event
            proposal.organizer = request.user   # correct field from your model

            proposal.save()

            return redirect('my_proposals')

    else:
        form = ProposalForm()

    return render(request, 'events/submit_proposal.html', {
        'form': form,
        'event': event
    })


# My Proposals
@login_required
def my_proposals(request):

    proposals = EventProposal.objects.filter(organizer=request.user)

    return render(request, 'events/my_proposals.html', {
        'proposals': proposals
    })

# ----------------------

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

# View specific event + proposals
# ----------------------
@login_required
def view_event(request, event_id):
    """
    Show details of a single event and all its proposals.
    """
    event = get_object_or_404(Event, id=event_id)
    proposals = EventProposal.objects.filter(event=event)

    context = {
        'event': event,
        'proposals': proposals,
    }
    return render(request, 'events/view_event.html', context)