from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Event, EventProposal
from .forms import EventProposalForm


# =========================
# My Assigned Events
# =========================
@login_required
def my_events(request):

    events = Event.objects.filter(organizer=request.user)

    context = {
        'events': events
    }

    return render(request, 'events/my_events.html', context)


# =========================
# Submit Proposal
# =========================
@login_required
def submit_proposal(request):

    if request.method == 'POST':
        form = EventProposalForm(request.POST)

        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.organizer = request.user
            proposal.save()

            return redirect('my_proposals')

    else:
        form = EventProposalForm()

    return render(request, 'events/submit_proposal.html', {'form': form})


# =========================
# My Proposals (Student View)
# =========================
@login_required
def my_proposals(request):

    proposals = EventProposal.objects.filter(
        organizer=request.user
    ).order_by('-submitted_at')

    return render(request, 'events/my_proposals.html', {'proposals': proposals})


# =========================
# Faculty Panel (Sir Ubaid)
# =========================
@login_required
def faculty_proposals(request):

    proposals = EventProposal.objects.filter(status='Pending')

    return render(request, 'events/faculty_proposals.html', {'proposals': proposals})


# =========================
# Approve Proposal
# =========================
@login_required
def approve_proposal(request, proposal_id):

    proposal = get_object_or_404(EventProposal, id=proposal_id)

    proposal.status = 'Approved'
    proposal.save()

    return redirect('faculty_proposals')


# =========================
# Reject Proposal
# =========================
@login_required
def reject_proposal(request, proposal_id):

    proposal = get_object_or_404(EventProposal, id=proposal_id)

    proposal.status = 'Rejected'
    proposal.save()

    return redirect('faculty_proposals')