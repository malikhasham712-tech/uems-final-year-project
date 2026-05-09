from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse

from openpyxl import Workbook

import qrcode
import base64

from io import BytesIO

from .models import (
    Event,
    EventProposal,
    EventRegistration,
    Announcement,
    Feedback,
    Attendance
)

from .forms import ProposalForm, EventRegistrationForm
from .notification_router import send_notification


# =====================================================
# ROLE HELPER
# =====================================================
def get_role(user):
    if user.is_superuser:
        return "admin"

    if hasattr(user, "profile") and hasattr(user.profile, "role"):
        return user.profile.role

    return "student"


def is_organizer_or_admin(user, event):
    return user.is_superuser or user == event.organizer


# =====================================================
# DASHBOARD
# =====================================================
@login_required
def dashboard(request):

    role = get_role(request.user)

    if role == "organizer":

        events = Event.objects.filter(
            organizer=request.user
        ).prefetch_related(
            "proposals",
            "registrations"
        )

        return render(request, "accounts/dashboard.html", {
            "role": role,
            "events": events
        })

    if role == "student":
        return redirect("events:available_events")

    return redirect("/admin/")


# =====================================================
# EVENTS
# =====================================================
@login_required
def available_events(request):

    events = Event.objects.filter(status="announced")

    return render(request, "events/available_events.html", {
        "events": events,
        "role": "student"
    })


@login_required
def my_events(request):

    role = get_role(request.user)

    if role == "student":

        events = Event.objects.filter(
            registrations__student=request.user
        ).distinct()

    elif role == "organizer":

        events = Event.objects.filter(
            organizer=request.user
        ).annotate(
            total_registrations=Count("registrations")
        )

    else:
        return redirect("/admin/")

    return render(request, "events/my_events.html", {
        "events": events,
        "role": role
    })


@login_required
def view_event(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    proposal = EventProposal.objects.filter(
        event=event
    ).order_by("-id").first()

    is_registered = event.registrations.filter(
        student=request.user
    ).exists()

    feedback_obj = Feedback.objects.filter(
        event=event,
        student=request.user
    ).first()

    return render(request, "events/view_event.html", {
        "event": event,
        "proposal": proposal,
        "is_registered": is_registered,
        "feedback": feedback_obj,
        "feedback_submitted": feedback_obj is not None,
        "role": get_role(request.user)
    })


# =====================================================
# REGISTRATION
# =====================================================
@login_required
def register_event(request, event_id):

    role = get_role(request.user)

    if role != "student":
        messages.error(request, "Only students allowed.")
        return redirect("events:available_events")

    event = get_object_or_404(
        Event,
        id=event_id,
        status="announced"
    )

    if EventRegistration.objects.filter(
        event=event,
        student=request.user
    ).exists():

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


@login_required
def event_registrations(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    if not is_organizer_or_admin(request.user, event):
        return redirect("events:my_events")

    regs = EventRegistration.objects.filter(
        event=event
    ).select_related("student")

    return render(request, "events/event_registrations.html", {
        "event": event,
        "registrations": regs,
        "total": regs.count(),
        "role": "organizer"
    })


# =====================================================
# QR CODE GENERATOR
# =====================================================
@login_required
def generate_qr(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    if not is_organizer_or_admin(request.user, event):
        return redirect("events:dashboard")

    # 🔥 IMPORTANT: use your PC WiFi IP here
    base_url = "http://192.168.1.10:8000"   # <-- your IP

    attendance_url = f"{base_url}/events/attendance/{event.id}/"

    import qrcode
    from io import BytesIO
    import base64

    qr = qrcode.make(attendance_url)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    qr_image = base64.b64encode(buffer.getvalue()).decode()

    return render(request, "events/generate_qr.html", {
        "event": event,
        "qr_image": qr_image,
        "attendance_url": attendance_url
    })


# =====================================================
# MARK ATTENDANCE
# =====================================================
def mark_attendance(request, event_id):

    if not request.user.is_authenticated:
        return redirect(f"/accounts/login/?next=/events/attendance/{event_id}/")

    event = get_object_or_404(Event, id=event_id)

    is_registered = EventRegistration.objects.filter(
        event=event,
        student=request.user
    ).exists()

    if not is_registered:
        return render(request, "events/attendance_result.html", {
            "success": False,
            "event": event,
            "message": "You are not registered in this event. Your attendance is NOT marked."
        })

    already_marked = Attendance.objects.filter(
        event=event,
        student=request.user
    ).exists()

    if already_marked:
        return render(request, "events/attendance_result.html", {
            "success": True,
            "event": event,
            "message": "Your attendance has already been marked."
        })

    Attendance.objects.create(
        event=event,
        student=request.user
    )

    EventRegistration.objects.filter(
        event=event,
        student=request.user
    ).update(status="attended")

    return render(request, "events/attendance_result.html", {
        "success": True,
        "event": event,
        "message": "Your attendance is marked successfully."
    })


# =====================================================
# PROPOSALS
# =====================================================
@login_required
def view_proposals(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    if not is_organizer_or_admin(request.user, event):
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

    if not is_organizer_or_admin(request.user, event):
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

            return redirect(
                "events:view_proposals",
                event_id=event.id
            )

    return render(request, "events/submit_proposal.html", {
        "form": ProposalForm(),
        "event": event,
        "role": "organizer"
    })


# =====================================================
# ANNOUNCEMENTS
# =====================================================
@login_required
def send_announcement(request):

    if not request.user.is_superuser:
        return redirect("events:dashboard")

    events = Event.objects.filter(status="announced")

    if request.method == "POST":

        event = get_object_or_404(
            Event,
            id=request.POST.get("event_id")
        )

        message_text = request.POST.get("message")

        Announcement.objects.create(
            event=event,
            message=message_text,
            created_by=request.user
        )

        users = User.objects.filter(
            id__in=set(
                list(
                    event.registrations.values_list(
                        "student",
                        flat=True
                    )
                )
                +
                (
                    [event.organizer.id]
                    if event.organizer else []
                )
            )
        )

        for user in users:

            send_notification(
                user=user,
                event=event,
                ntype="announcement",
                message=f"📢 {event.name}\nAnnouncement: {message_text}"
            )

        messages.success(
            request,
            "Announcement sent successfully!"
        )

        return redirect("events:send_announcement")

    return render(request, "events/send_announcement.html", {
        "events": events
    })


@login_required
def event_announcements(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    role = get_role(request.user)

    if role not in ["student", "organizer", "admin"]:
        return redirect("events:dashboard")

    announcements = Announcement.objects.filter(
        event=event
    ).order_by("-created_at")

    return render(request, "events/event_announcements.html", {
        "event": event,
        "announcements": announcements,
        "role": role
    })


# =====================================================
# NOTIFICATIONS
# =====================================================
@login_required
def notifications(request):

    notifs = request.user.notifications.all().order_by(
        "-created_at"
    )

    notifs.filter(is_read=False).update(is_read=True)

    return render(request, "events/notifications.html", {
        "notifications": notifs
    })


@login_required
def notification_detail(request, notification_id):

    notif = get_object_or_404(
        request.user.notifications,
        id=notification_id
    )

    notif.is_read = True
    notif.save()

    if (
        notif.notification_type == "announcement"
        and notif.event
    ):

        return redirect(
            "events:event_announcements",
            event_id=notif.event.id
        )

    return render(request, "events/notification_detail.html", {
        "notif": notif
    })


# =====================================================
# FEEDBACK
# =====================================================
@login_required
def submit_feedback(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    if event.status != "completed":

        messages.error(
            request,
            "Feedback allowed only after event completion."
        )

        return redirect("events:my_events")

    existing = Feedback.objects.filter(
        event=event,
        student=request.user
    ).first()

    if request.method == "POST":

        if existing:

            messages.info(
                request,
                "Feedback already submitted."
            )

            return redirect("events:my_events")

        Feedback.objects.create(
            student=request.user,
            event=event,
            message=request.POST.get("message"),
            rating=request.POST.get("rating"),
            experience=(
                request.POST.get("experience")
                or "good"
            ).lower()
        )

        messages.success(
            request,
            "Feedback submitted successfully!"
        )

        return redirect("events:my_events")

    return render(request, "events/feedback.html", {
        "event": event,
        "feedback": existing
    })


@login_required
def event_feedback(request, event_id):
    return submit_feedback(request, event_id)


@login_required
def view_feedbacks(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    if get_role(request.user) not in [
        "organizer",
        "admin"
    ]:
        return redirect("events:my_events")

    feedbacks = Feedback.objects.filter(
        event=event
    ).order_by("-id")

    return render(request, "events/view_feedbacks.html", {
        "event": event,
        "feedbacks": feedbacks
    })


# =====================================================
# CANCEL REGISTRATION
# =====================================================
@login_required
def cancel_registration(request, event_id):

    reg = EventRegistration.objects.filter(
        event_id=event_id,
        student=request.user
    ).first()

    if reg:

        reg.delete()

        messages.success(
            request,
            "Registration cancelled."
        )

    return redirect("events:my_events")


# =====================================================
# EVENT REPORT MODULE
# =====================================================
@login_required
def event_report_list(request):

    if not request.user.is_superuser:
        return redirect("events:dashboard")

    events = Event.objects.filter(status="completed")

    data = [
        {
            "event": e,
            "url": f"/events/reports/{e.id}/"
        }
        for e in events
    ]

    return render(request, "events/event_report_list.html", {
        "data": data
    })


@login_required
def event_report(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    feedbacks = Feedback.objects.filter(event=event)

    summary = {
        "excellent": feedbacks.filter(
            experience="excellent"
        ).count(),

        "good": feedbacks.filter(
            experience="good"
        ).count(),

        "average": feedbacks.filter(
            experience="average"
        ).count(),

        "poor": feedbacks.filter(
            experience="poor"
        ).count(),
    }

    return render(request, "events/event_report.html", {
        "event": event,
        "feedbacks": feedbacks,
        "summary": summary
    })


@login_required
def export_event_report(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    feedbacks = Feedback.objects.filter(event=event)

    wb = Workbook()
    ws = wb.active

    ws.append(["Event Report", event.name])
    ws.append([])

    ws.append([
        "Student",
        "Experience",
        "Message"
    ])

    for fb in feedbacks:

        ws.append([
            fb.student.username,
            fb.experience,
            fb.message
        ])

    ws.append([])
    ws.append(["Summary"])

    ws.append([
        "Excellent",
        feedbacks.filter(
            experience="excellent"
        ).count()
    ])

    ws.append([
        "Good",
        feedbacks.filter(
            experience="good"
        ).count()
    ])

    ws.append([
        "Average",
        feedbacks.filter(
            experience="average"
        ).count()
    ])

    ws.append([
        "Poor",
        feedbacks.filter(
            experience="poor"
        ).count()
    ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response[
        "Content-Disposition"
    ] = f'attachment; filename=report_{event.id}.xlsx'

    wb.save(response)

    return response