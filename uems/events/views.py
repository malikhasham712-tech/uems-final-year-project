from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib import messages

from .models import (
    Event,
    EventProposal,
    EventRegistration,
    Announcement,
    Notification,
    Feedback
)

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
        return redirect("events:available_events")

    return redirect("/admin/")


# ----------------------
# AVAILABLE EVENTS
# ----------------------
@login_required
def available_events(request):
    events = Event.objects.filter(status__iexact="announced")

    return render(request, "events/available_events.html", {
        "events": events,
        "role": "student"
    })


# ----------------------
# REGISTER EVENT
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

            # 🔔 OPTIONAL: student registration notification
            Notification.objects.create(
                user=request.user,
                announcement=None
            )

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
        events = Event.objects.filter(
            organizer=request.user
        ).annotate(total_registrations=Count("registrations"))

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
        "form": ProposalForm(),
        "role": "organizer"
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
            obj.requirements = request.POST.get("requirements")
            obj.save()

            return redirect("events:view_proposals", event_id=event.id)

    return render(request, "events/submit_proposal.html", {
        "form": ProposalForm(),
        "event": event,
        "role": "organizer"
    })


# ----------------------
# APPROVE / REJECT + NOTIFICATIONS (IMPORTANT FIX)
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

    # 🔔 NOTIFICATION → ORGANIZER
    if event.organizer:
        Notification.objects.create(
            user=event.organizer,
            announcement=None
        )

    # 🔔 NOTIFICATION → STUDENTS
    students = EventRegistration.objects.filter(event=event).values_list("student", flat=True)

    for uid in set(students):
        Notification.objects.create(
            user_id=uid,
            announcement=None
        )

    return redirect("events:view_proposals", event_id=event.id)


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


# ----------------------
# ANNOUNCEMENTS
# ----------------------
@login_required
def send_announcement(request):
    if not request.user.is_superuser:
        return redirect("events:dashboard")

    events = Event.objects.filter(status="Announced")

    if request.method == "POST":
        event_id = request.POST.get("event_id")
        message_text = request.POST.get("message")

        event = get_object_or_404(Event, id=event_id)

        announcement = Announcement.objects.create(
            event=event,
            message=message_text,
            created_by=request.user
        )

        # 🔔 ORGANIZER + STUDENTS NOTIFICATION
        user_ids = list(event.registrations.values_list("student", flat=True))

        if event.organizer:
            user_ids.append(event.organizer.id)

        for uid in set(user_ids):
            Notification.objects.create(
                user_id=uid,
                announcement=announcement
            )

        messages.success(request, "Announcement sent successfully!")
        return redirect("events:send_announcement")

    return render(request, "events/send_announcement.html", {
        "events": events
    })


# ----------------------
# EVENT ANNOUNCEMENTS
# ----------------------
@login_required
def event_announcements(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if not (request.user.is_superuser or request.user == event.organizer):
        return redirect("events:my_events")

    announcements = Announcement.objects.filter(event=event)

    return render(request, "events/event_announcements.html", {
        "event": event,
        "announcements": announcements
    })


# ----------------------
# NOTIFICATIONS PAGE
# ----------------------
@login_required
def notifications(request):
    notifs = request.user.notifications.all().order_by("-created_at")
    notifs.filter(is_read=False).update(is_read=True)

    return render(request, "events/notifications.html", {
        "notifications": notifs
    })


# ----------------------
# FEEDBACK
# ----------------------
@login_required
def submit_feedback(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    registration = EventRegistration.objects.filter(
        event=event,
        student=request.user
    ).first()

    if not registration:
        messages.error(request, "Not allowed")
        return redirect("events:my_events")

    if registration.status != "attended" and event.status != "Completed":
        messages.error(request, "You can only give feedback after attending event.")
        return redirect("events:my_events")

    if request.method == "POST":
        Feedback.objects.create(
            student=request.user,
            event=event,
            message=request.POST.get("message"),
            rating=request.POST.get("rating") or None
        )

        messages.success(request, "Feedback submitted!")
        return redirect("events:my_events")

    return render(request, "events/feedback.html", {
        "event": event
    })


# ALIASES
@login_required
def event_feedback(request, event_id):
    return submit_feedback(request, event_id)


@login_required
def cancel_registration(request, event_id):
    reg = EventRegistration.objects.filter(
        event_id=event_id,
        student=request.user
    ).first()

    if reg:
        reg.delete()
        messages.success(request, "Registration cancelled.")

    return redirect("events:my_events")