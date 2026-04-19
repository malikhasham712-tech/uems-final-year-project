from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib import messages
from django.contrib.auth.models import User

from .models import (
    Event,
    EventProposal,
    EventRegistration,
    Announcement,
    Feedback
)

from .forms import ProposalForm, EventRegistrationForm
from .notification_router import send_notification


# ----------------------
# ROLE HELPER
# ----------------------
def get_role(user):
    if user.is_superuser:
        return "admin"
    if hasattr(user, "profile") and hasattr(user.profile, "role"):
        return user.profile.role
    return None


# ----------------------
# DASHBOARD
# ----------------------
@login_required
def dashboard(request):
    role = get_role(request.user)

    if role == "organizer":
        events = Event.objects.filter(organizer=request.user).prefetch_related(
            "proposals", "registrations"
        )
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
    role = get_role(request.user)

    if role != "student":
        messages.error(request, "Only students allowed.")
        return redirect("events:available_events")

    event = get_object_or_404(Event, id=event_id, status="announced")

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
        events = Event.objects.filter(registrations__student=request.user).distinct()

    elif role == "organizer":
        events = Event.objects.filter(organizer=request.user).annotate(
            total_registrations=Count("registrations")
        )

    else:
        return redirect("/admin/")

    return render(request, "events/my_events.html", {
        "events": events,
        "role": role
    })


# ----------------------
# VIEW EVENT
# ----------------------
@login_required
def view_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    proposal = EventProposal.objects.filter(event=event).order_by("-id").first()

    is_registered = event.registrations.filter(student=request.user).exists()

    return render(request, "events/view_event.html", {
        "event": event,
        "proposal": proposal,
        "is_registered": is_registered,
        "role": get_role(request.user)
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
            obj.status = "pending"
            obj.save()

            send_notification(
                user=request.user,
                event=event,
                ntype="general",
                message=f"📌 Proposal submitted for {event.name}"
            )

            return redirect("events:view_proposals", event_id=event.id)

    return render(request, "events/submit_proposal.html", {
        "form": ProposalForm(),
        "event": event,
        "role": "organizer"
    })


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
# ANNOUNCEMENTS (FIXED CORE LOGIC)
# ----------------------
@login_required
def send_announcement(request):
    if not request.user.is_superuser:
        return redirect("events:dashboard")

    events = Event.objects.filter(status="announced")

    if request.method == "POST":
        event = get_object_or_404(Event, id=request.POST.get("event_id"))
        message_text = request.POST.get("message")

        # Save announcement
        announcement = Announcement.objects.create(
            event=event,
            message=message_text,
            created_by=request.user
        )

        # Get all users (students + organizer)
        user_ids = list(event.registrations.values_list("student", flat=True))

        if event.organizer:
            user_ids.append(event.organizer.id)

        users = User.objects.filter(id__in=set(user_ids))

        # 🔥 FIXED NOTIFICATION MESSAGE (IMPORTANT)
        for user in users:
            send_notification(
                user=user,
                event=event,
                ntype="announcement",
                message=(
                    f"📢 {event.name}\n"
                    f"Announcement: {message_text}"
                )
            )

        messages.success(request, "Announcement sent successfully!")
        return redirect("events:send_announcement")

    return render(request, "events/send_announcement.html", {
        "events": events
    })


# ----------------------
# ANNOUNCEMENTS VIEW
# ----------------------
@login_required
def event_announcements(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    role = get_role(request.user)

    if role == "student":
        if not EventRegistration.objects.filter(event=event, student=request.user).exists():
            messages.error(request, "You are not registered for this event.")
            return redirect("events:available_events")

    elif role == "organizer":
        if event.organizer != request.user and not request.user.is_superuser:
            return redirect("events:my_events")

    announcements = Announcement.objects.filter(event=event).order_by("-created_at")

    return render(request, "events/event_announcements.html", {
        "event": event,
        "announcements": announcements,
        "role": role
    })


# ----------------------
# NOTIFICATIONS
# ----------------------
@login_required
def notifications(request):
    notifs = request.user.notifications.all().order_by("-created_at")
    notifs.filter(is_read=False).update(is_read=True)

    return render(request, "events/notifications.html", {
        "notifications": notifs
    })


# ----------------------
# NOTIFICATION DETAIL
# ----------------------
@login_required
def notification_detail(request, notification_id):
    notif = get_object_or_404(request.user.notifications, id=notification_id)

    notif.is_read = True
    notif.save()

    # -----------------------------------
    # SPECIAL CASE: ANNOUNCEMENT ROUTING
    # -----------------------------------
    if notif.notification_type == "announcement" and notif.event:
        return redirect("events:event_announcements", event_id=notif.event.id)

    # -----------------------------------
    # DEFAULT BEHAVIOR (ALL OTHER TYPES)
    # -----------------------------------
    return render(request, "events/notification_detail.html", {
        "notif": notif
    })

# ----------------------
# FEEDBACK
# ----------------------
@login_required
def submit_feedback(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if event.status != "completed":
        messages.error(request, "Feedback allowed only after event completion.")
        return redirect("events:my_events")

    is_registered = event.registrations.filter(student=request.user).exists()
    if not is_registered:
        messages.error(request, "You must be registered to give feedback.")
        return redirect("events:my_events")

    if Feedback.objects.filter(event=event, student=request.user).exists():
        messages.info(request, "Already submitted.")
        return redirect("events:my_events")

    if request.method == "POST":
        Feedback.objects.create(
            student=request.user,
            event=event,
            message=request.POST.get("message"),
            rating=request.POST.get("rating"),
            experience=(request.POST.get("experience") or "good").lower()
        )

        send_notification(
            user=request.user,
            event=event,
            ntype="feedback",
            message=f"⭐ Feedback submitted for {event.name}"
        )

        messages.success(request, "Feedback submitted successfully!")
        return redirect("events:my_events")

    return render(request, "events/feedback.html", {
        "event": event,
        "is_registered": is_registered,
        "already_submitted": False
    })


# ----------------------
# VIEW FEEDBACK
# ----------------------
@login_required
def view_feedbacks(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if get_role(request.user) not in ["organizer", "admin"]:
        return redirect("events:my_events")

    feedbacks = Feedback.objects.filter(event=event).order_by("-id")

    return render(request, "events/view_feedbacks.html", {
        "event": event,
        "feedbacks": feedbacks
    })


# ----------------------
# CANCEL REGISTRATION
# ----------------------
@login_required
def cancel_registration(request, event_id):
    reg = EventRegistration.objects.filter(event_id=event_id, student=request.user).first()

    if reg:
        reg.delete()
        messages.success(request, "Registration cancelled.")

    return redirect("events:my_events")


@login_required
def event_feedback(request, event_id):
    return submit_feedback(request, event_id)