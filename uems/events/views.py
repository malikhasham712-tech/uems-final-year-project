from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib import messages
from django.http import JsonResponse

from .models import Event, EventProposal, EventRegistration
from .forms import ProposalForm, EventRegistrationForm


# ----------------------
# DASHBOARD
# ----------------------
@login_required
def dashboard(request):

    user = request.user

    # ORGANIZER DASHBOARD
    if user.is_superuser or (hasattr(user, "profile") and user.profile.role == "organizer"):

        events = Event.objects.filter(organizer=user).prefetch_related('proposals')

        context = {
            "role": "organizer",
            "events": events
        }

        return render(request, "accounts/dashboard.html", context)

    # STUDENT DASHBOARD
    else:
        context = {
            "role": "student",
        }

        return render(request, "accounts/dashboard.html", context)
# ----------------------
# MY EVENTS
# ----------------------
@login_required
def my_events(request):

    user = request.user

    # Student → only registered events
    if hasattr(user, "profile") and user.profile.role == "student":

        regs = EventRegistration.objects.filter(student=user)
        events = [r.event for r in regs]

        return render(request, "events/my_events.html", {
            "events": events,
            "role": "student"
        })

    # Organizer/Admin → assigned events
    else:

        events = Event.objects.filter(organizer=user).annotate(
            total_registrations=Count('registrations')
        )

        return render(request, "events/my_events.html", {
            "events": events,
            "role": "organizer"
        })


# ----------------------
# AVAILABLE EVENTS (STUDENT ONLY)
# ----------------------
@login_required
def available_events(request):

    events = Event.objects.filter(status="announced")

    return render(request, "events/available_events.html", {
        "events": events,
        "role": "student"
    })


# ----------------------
# REGISTER EVENT
# ----------------------
@login_required
def register_event(request, event_id):

    if hasattr(request.user, "profile") and request.user.profile.role != "student":
        messages.error(request, "Only students allowed.")
        return redirect("events:my_events")

    event = get_object_or_404(Event, id=event_id, status="announced")

    if EventRegistration.objects.filter(event=event, student=request.user).exists():
        messages.info(request, "Already registered.")
        return redirect("events:available_events")

    if request.method == "POST":
        form = EventRegistrationForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.event = event
            obj.student = request.user
            obj.save()
            messages.success(request, "Registered successfully!")

            # ✅ Important: redirect to MY EVENTS
            return redirect("events:my_events")

    return render(request, "events/register_event.html", {
        "form": EventRegistrationForm(),
        "event": event,
        "role": "student"
    })


# ----------------------
# VIEW EVENT
# ----------------------
@login_required
def view_event(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    return render(request, "events/view_event.html", {
        "event": event
    })


# ----------------------
# PROPOSALS
# ----------------------
@login_required
def view_proposals(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    if not (request.user.is_superuser or request.user == event.organizer):
        return redirect("events:my_events")

    return render(request, "events/view_proposals.html", {
        "event": event,
        "proposals": EventProposal.objects.filter(event=event),
        "form": ProposalForm()
    })


@login_required
def submit_proposal(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    if not (request.user.is_superuser or request.user == event.organizer):
        return redirect("events:my_events")

    if request.method == "POST":
        form = ProposalForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.event = event
            obj.organizer = request.user
            obj.status = "Pending"
            obj.save()

            return redirect("events:view_proposals", event_id=event.id)

    return render(request, "events/submit_proposal.html", {
        "form": ProposalForm(),
        "event": event
    })


# ----------------------
# APPROVE / REJECT
# ----------------------
@login_required
def approve_proposal(request, proposal_id):

    if not request.user.is_superuser:
        return redirect("events:my_events")

    proposal = get_object_or_404(EventProposal, id=proposal_id)
    proposal.status = "Approved"
    proposal.save()

    return redirect("events:view_proposals", event_id=proposal.event.id)


@login_required
def reject_proposal(request, proposal_id):

    if not request.user.is_superuser:
        return redirect("events:my_events")

    proposal = get_object_or_404(EventProposal, id=proposal_id)
    proposal.status = "Rejected"
    proposal.save()

    return redirect("events:view_proposals", event_id=proposal.event.id)


# ----------------------
# REGISTRATIONS
# ----------------------
@login_required
def event_registrations(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    if not (request.user.is_superuser or request.user == event.organizer):
        return redirect("events:my_events")

    regs = EventRegistration.objects.filter(event=event)

    return render(request, "events/event_registrations.html", {
        "event": event,
        "registrations": regs,
        "total": regs.count()
    })