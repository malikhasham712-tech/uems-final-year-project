from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib import messages

from .models import Event, EventProposal, EventRegistration
from .forms import ProposalForm, EventRegistrationForm


# ----------------------
# ROLE HELPER
# ----------------------
def get_role(user):
    if user.is_superuser:
        return "admin"
    if hasattr(user, "profile"):
        return user.profile.role
    return None


# ----------------------
# DASHBOARD
# ----------------------
@login_required
def dashboard(request):

    role = get_role(request.user)

    if role == "organizer":

        events = Event.objects.filter(
            organizer=request.user
        ).prefetch_related("proposals", "registrations")

        return render(request, "accounts/dashboard.html", {
            "role": "organizer",
            "events": events
        })

    if role == "student":

        return render(request, "accounts/dashboard.html", {
            "role": "student"
        })

    return redirect("/admin/")


# ----------------------
# AVAILABLE EVENTS (STUDENT)
# ----------------------
@login_required
def available_events(request):

    events = Event.objects.filter(status__iexact="announced")

    return render(request, "events/available_events.html", {
        "events": events,
        "role": "student"
    })


# ----------------------
# REGISTER EVENT (STUDENT)
# ----------------------
@login_required
def register_event(request, event_id):

    role = get_role(request.user)

    if role != "student":
        messages.error(request, "Only students allowed.")
        return redirect("events:available_events")

    event = get_object_or_404(Event, id=event_id, status__iexact="announced")

    if EventRegistration.objects.filter(event=event, student=request.user).exists():
        messages.info(request, "Already registered.")
        return redirect("events:my_events")

    if request.method == "POST":
        form = EventRegistrationForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.event = event
            obj.student = request.user
            obj.save()

            messages.success(request, "Registered successfully!")
            return redirect("events:my_events")

    return render(request, "events/register_event.html", {
        "form": EventRegistrationForm(),
        "event": event,
        "role": "student"
    })


# ----------------------
# MY EVENTS
# ----------------------
@login_required
def my_events(request):

    role = get_role(request.user)

    if role == "student":

        regs = EventRegistration.objects.filter(student=request.user)
        events = [r.event for r in regs]

        return render(request, "events/my_events.html", {
            "events": events,
            "role": "student"
        })

    if role == "organizer":

        events = Event.objects.filter(organizer=request.user).annotate(
            total_registrations=Count("registrations")
        )

        return render(request, "events/my_events.html", {
            "events": events,
            "role": "organizer"
        })

    return redirect("/admin/")


# ----------------------
# VIEW EVENT
# ----------------------
@login_required
def view_event(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    role = "organizer" if request.user == event.organizer else "student"

    return render(request, "events/view_event.html", {
        "event": event,
        "role": role
    })


# ----------------------
# VIEW PROPOSALS
# ----------------------
@login_required
def view_proposals(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    if not (request.user.is_superuser or request.user == event.organizer):
        return redirect("events:my_events")

    return render(request, "events/view_proposals.html", {
        "event": event,
        "proposals": EventProposal.objects.filter(event=event),
        "form": ProposalForm(),
        "role": "organizer"
    })


# ----------------------
# SUBMIT PROPOSAL
# ----------------------
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
        "event": event,
        "role": "organizer"
    })


# ----------------------
# APPROVE PROPOSAL
# ----------------------
@login_required
def approve_proposal(request, proposal_id):

    if not request.user.is_superuser:
        return redirect("events:my_events")

    proposal = get_object_or_404(EventProposal, id=proposal_id)
    proposal.status = "Approved"
    proposal.save()

    event = proposal.event
    event.status = "Announced"
    event.save()

    return redirect("events:view_proposals", event_id=event.id)


# ----------------------
# REJECT PROPOSAL
# ----------------------
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

    regs = EventRegistration.objects.filter(event=event).select_related("student")

    return render(request, "events/event_registrations.html", {
        "event": event,
        "registrations": regs,
        "total": regs.count(),
        "role": "organizer"
    })