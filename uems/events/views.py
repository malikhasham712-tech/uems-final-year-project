from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.urls import reverse

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
    Attendance,
    Notification,
    EventStatus,
    ProposalStatus,
)

from .forms import ProposalForm, EventRegistrationForm
from .notification_router import send_notification


# =====================================================
# NOTIFICATION CONTEXT
# =====================================================
def notif_context(request):

    if request.user.is_authenticated:

        notifications = request.user.notifications.all().order_by(
            "-created_at"
        )

        return {

            "notifications": notifications[:10],

            "unread_notifications": notifications.filter(
                is_read=False
            ).count()
        }

    return {}


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

    return (
        user.is_superuser
        or user == event.organizer
    )


# =====================================================
# DASHBOARD
# =====================================================
@login_required
def dashboard(request):

    if hasattr(request.user, 'profile') and request.user.profile.is_organizer:
        # ORGANIZER DASHBOARD
        events = Event.objects.filter(
            organizer=request.user
        ).annotate(
            total_registrations=Count("registrations"),
            total_attendance=Count("attendances")
        ).prefetch_related(
            "proposals",
            "registrations",
            "attendances"
        )

        return render(request, "accounts/dashboard.html", {
            "role": "organizer",
            "events": events,
            **notif_context(request)
        })

    else:
        # STUDENT - Go to available events
        return redirect("events:available_events")


# =====================================================
# EVENTS
# =====================================================
@login_required
def available_events(request):

    events = Event.objects.filter(
        status=EventStatus.ANNOUNCED
    )

    return render(request, "events/available_events.html", {
        "events": events,
        "role": "student",
        **notif_context(request)
    })


@login_required
def my_events(request):

    if hasattr(request.user, 'profile') and request.user.profile.is_organizer:
        # ORGANIZER - Show their events
        events = Event.objects.filter(
            organizer=request.user
        ).annotate(
            total_registrations=Count("registrations"),
            total_attendance=Count("attendances")
        )
        role = "organizer"

    else:
        # STUDENT - Show registered events
        events = Event.objects.filter(
            registrations__student=request.user
        ).distinct()
        role = "student"
        
        # ADD FEEDBACK STATUS FOR EACH EVENT
        for event in events:
            event.has_feedback = Feedback.objects.filter(
                event=event,
                student=request.user
            ).exists()

    return render(request, "events/my_events.html", {
        "events": events,
        "role": role,
        **notif_context(request)
    })


@login_required
def view_event(request, event_id):

    event = get_object_or_404(
        Event,
        id=event_id
    )

    proposal = EventProposal.objects.filter(
        event=event,
        status=ProposalStatus.ACCEPTED
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
        "role": get_role(request.user),
        **notif_context(request)
    })


# =====================================================
# REGISTRATION
# =====================================================
@login_required
def register_event(request, event_id):

    role = get_role(request.user)

    if role != "student":

        messages.error(
            request,
            "Only students allowed."
        )

        return redirect("events:available_events")

    event = get_object_or_404(
        Event,
        id=event_id,
        status=EventStatus.ANNOUNCED
    )

    if EventRegistration.objects.filter(
        event=event,
        student=request.user
    ).exists():

        messages.info(
            request,
            "Already registered."
        )

        return redirect("events:my_events")

    if request.method == "POST":

        form = EventRegistrationForm(request.POST)

        if form.is_valid():

            obj = form.save(commit=False)

            obj.event = event
            obj.student = request.user

            obj.save()

            messages.success(
                request,
                "Registered successfully!"
            )

            return redirect("events:my_events")

    return render(request, "events/register_event.html", {
        "form": EventRegistrationForm(),
        "event": event,
        "role": "student",
        **notif_context(request)
    })


@login_required
def event_registrations(request, event_id):

    event = get_object_or_404(
        Event,
        id=event_id
    )

    if not is_organizer_or_admin(
        request.user,
        event
    ):
        return redirect("events:my_events")

    regs = EventRegistration.objects.filter(
        event=event
    ).select_related("student")

    return render(request, "events/event_registrations.html", {
        "event": event,
        "registrations": regs,
        "total": regs.count(),
        "role": "organizer",
        **notif_context(request)
    })


# =====================================================
# QR CODE GENERATOR
# =====================================================
@login_required
def generate_qr(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    if not is_organizer_or_admin(request.user, event):
        return redirect("events:dashboard")

    attendance_path = reverse(
        "events:mark_attendance",
        args=[event.id]
    )

    # 🔥 AUTO BASE URL (NO IP ISSUE EVER)
    base_url = request.build_absolute_uri("/")[:-1]

    attendance_url = f"{base_url}{attendance_path}"

    qr = qrcode.make(attendance_url)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    qr_image = base64.b64encode(buffer.getvalue()).decode()

    return render(request, "events/generate_qr.html", {
        "event": event,
        "qr_image": qr_image,
        "attendance_url": attendance_url,
        **notif_context(request)
    })

# =====================================================
# MARK ATTENDANCE
# =====================================================
@login_required
def mark_attendance(request, event_id):

    event = get_object_or_404(Event, id=event_id)
    user = request.user

    # STEP 1: CHECK REGISTRATION (STRICT)
    registration_exists = EventRegistration.objects.filter(
        event=event,
        student_id=user.id
    ).exists()

    if not registration_exists:
        return render(request, "events/attendance_result.html", {
            "success": False,
            "event": event,
            "message": "❌ You are not registered for this event."
        })

    # STEP 2: CREATE OR GET ATTENDANCE (NO DUPLICATE ISSUES)
    attendance, created = Attendance.objects.get_or_create(
        event=event,
        student=user
    )

    if created:
        return render(request, "events/attendance_result.html", {
            "success": True,
            "event": event,
            "message": "✅ Attendance marked successfully!"
        })

    # STEP 3: ALREADY EXISTS
    return render(request, "events/attendance_result.html", {
        "success": True,
        "event": event,
        "message": "Attendance already marked."
    })

# =====================================================
# ATTENDANCE RECORDS
# =====================================================
@login_required
def attendance_records(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    is_organizer = hasattr(request.user, 'profile') and request.user.profile.is_organizer
    is_admin = request.user.is_superuser

    if not is_admin and not is_organizer:
        return redirect("events:dashboard")

    # Get registrations
    registrations = EventRegistration.objects.filter(
        event=event
    ).select_related("student")

    # Attendance lookup (FAST + CLEAN)
    attendance_map = {
        a.student_id: a.marked_at
        for a in Attendance.objects.filter(event=event)
    }

    # Build unified data structure (THIS IS FINAL STANDARD)
    data = []

    for reg in registrations:
        data.append({
            "name": reg.student.username,
            "reg_no": reg.registration_no if hasattr(reg, "registration_no") else reg.student_id,
            "department": getattr(reg, "department", "-"),
            "email": reg.student.email,
            "status": "present" if reg.student_id in attendance_map else "absent",
            "marked_at": attendance_map.get(reg.student_id)
        })

    present_count = sum(1 for d in data if d["status"] == "present")
    absent_count = len(data) - present_count

    percentage = round((present_count / len(data)) * 100, 2) if data else 0

    return render(request, "events/view_attendance.html", {
        "event": event,
        "data": data,
        "total_students": len(data),
        "present": present_count,
        "absent": absent_count,
        "percentage": percentage,
        "role": "organizer" if is_organizer else "admin",
        **notif_context(request)
    })

# =====================================================
# PROPOSALS
# =====================================================
@login_required
def view_proposals(request, event_id):

    event = get_object_or_404(
        Event,
        id=event_id
    )

    if not is_organizer_or_admin(
        request.user,
        event
    ):
        return redirect("events:my_events")

    return render(request, "events/view_proposals.html", {
        "event": event,
        "proposals": EventProposal.objects.filter(
            event=event
        ).order_by("-submitted_at"),
        "form": ProposalForm(),
        "role": "organizer",
        **notif_context(request)
    })


@login_required
def submit_proposal(request, event_id):

    event = get_object_or_404(
        Event,
        id=event_id
    )

    if not is_organizer_or_admin(
        request.user,
        event
    ):
        return redirect("events:my_events")

    if request.method == "POST":

        form = ProposalForm(request.POST)

        if form.is_valid():

            obj = form.save(commit=False)

            obj.event = event
            obj.organizer = request.user
            obj.status = ProposalStatus.PENDING

            obj.save()

            messages.success(
                request,
                "Proposal submitted successfully."
            )

            return redirect(
                "events:view_proposals",
                event_id=event.id
            )

    return render(request, "events/submit_proposal.html", {
        "form": ProposalForm(),
        "event": event,
        "role": "organizer",
        **notif_context(request)
    })


# =====================================================
# ANNOUNCEMENTS
# =====================================================
@login_required
def send_announcement(request):

    if not request.user.is_superuser:
        return redirect("events:dashboard")

    events = Event.objects.filter(
        status=EventStatus.ANNOUNCED
    )

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
                message=f"{event.name}\nAnnouncement: {message_text}"
            )

        messages.success(
            request,
            "Announcement sent successfully!"
        )

        return redirect("events:send_announcement")

    return render(request, "events/send_announcement.html", {
        "events": events,
        **notif_context(request)
    })


@login_required
def event_announcements(request, event_id):

    event = get_object_or_404(
        Event,
        id=event_id
    )

    role = get_role(request.user)

    announcements = Announcement.objects.filter(
        event=event
    ).order_by("-created_at")

    return render(request, "events/event_announcements.html", {
        "event": event,
        "announcements": announcements,
        "role": role,
        **notif_context(request)
    })


# =====================================================
# NOTIFICATIONS
# =====================================================
@login_required
def notifications(request):

    notifs = request.user.notifications.all().order_by(
        "-created_at"
    )

    notifs.update(is_read=True)

    return render(request, "events/notifications.html", {
        "notifications": notifs,
        **notif_context(request)
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

    if notif.event:

        return redirect(
            "events:view_event",
            event_id=notif.event.id
        )

    return redirect("events:notifications")


# =====================================================
# FEEDBACK
# =====================================================
@login_required
def submit_feedback(request, event_id):

    event = get_object_or_404(
        Event,
        id=event_id
    )

    if event.status != EventStatus.COMPLETED:

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
        "feedback": existing,
        **notif_context(request)
    })


@login_required
def event_feedback(request, event_id):

    return submit_feedback(
        request,
        event_id
    )


@login_required
def view_feedbacks(request, event_id):

    event = get_object_or_404(
        Event,
        id=event_id
    )

    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_organizer)):
        return redirect("events:my_events")

    feedbacks = Feedback.objects.filter(
        event=event
    ).order_by("-id")

    return render(request, "events/view_feedbacks.html", {
        "event": event,
        "feedbacks": feedbacks,
        **notif_context(request)
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

    events = Event.objects.filter(
        status=EventStatus.COMPLETED
    )

    data = [
        {
            "event": e,
            "url": f"/events/reports/{e.id}/"
        }
        for e in events
    ]

    return render(request, "events/event_report_list.html", {
        "data": data,
        **notif_context(request)
    })


@login_required
def event_report(request, event_id):

    event = get_object_or_404(Event, id=event_id)

    feedbacks = Feedback.objects.filter(event=event)

    registrations = EventRegistration.objects.filter(
        event=event
    ).select_related("student")

    attendance_qs = Attendance.objects.filter(event=event)

    # =========================
    # SINGLE SOURCE OF TRUTH
    # =========================
    attendance_map = {
        a.student_id: a for a in attendance_qs
    }

    # =========================
    # FEEDBACK SUMMARY
    # =========================
    summary = {
        "excellent": feedbacks.filter(experience="excellent").count(),
        "good": feedbacks.filter(experience="good").count(),
        "average": feedbacks.filter(experience="average").count(),
        "poor": feedbacks.filter(experience="poor").count(),
    }

    # =========================
    # STATS
    # =========================
    registered_ids = set(registrations.values_list("student_id", flat=True))
    attended_ids = set(attendance_map.keys())

    present_ids = registered_ids & attended_ids
    absent_ids = registered_ids - attended_ids

    total_students = len(registered_ids)
    present = len(present_ids)
    absent = len(absent_ids)
    percentage = round((present / total_students) * 100, 2) if total_students else 0

    # =========================
    # TABLE DATA
    # =========================
    data = []

    for reg in registrations:
        att = attendance_map.get(reg.student_id)

        data.append({
            "name": reg.student.username,
            "reg_no": reg.student_id,
            "status": "present" if att else "absent",
            "marked_at": att.marked_at if att else None
        })

    return render(request, "admin/attendance_report_change.html", {
        "event": event,
        "data": data,

        "total_students": total_students,
        "present": present,
        "absent": absent,
        "percentage": percentage,

        "summary": summary,

        **notif_context(request)
    })

@login_required
def export_event_report(request, event_id):

    event = get_object_or_404(Event, id=event_id)
    mode = request.GET.get("mode", "attendance")

    wb = Workbook()
    ws = wb.active

    # =========================
    # ATTENDANCE EXPORT
    # =========================
    if mode == "attendance":

        registrations = EventRegistration.objects.filter(
            event=event
        ).select_related("student")

        attendance_map = {
            a.student_id: a for a in Attendance.objects.filter(event=event)
        }

        ws.title = "Attendance Report"

        ws.append(["Event Attendance Report", event.name])
        ws.append([])
        ws.append(["Student", "Status"])

        for reg in registrations:

            status = "Present" if reg.student_id in attendance_map else "Absent"

            ws.append([
                reg.student.username,
                status
            ])

    # =========================
    # FEEDBACK EXPORT
    # =========================
    else:

        feedbacks = Feedback.objects.filter(event=event)

        ws.title = "Feedback Report"

        ws.append(["Event Feedback Report", event.name])
        ws.append([])
        ws.append(["Student", "Experience", "Message"])

        for fb in feedbacks:
            ws.append([
                fb.student.username,
                fb.experience,
                fb.message
            ])

        ws.append([])
        ws.append(["Summary"])
        ws.append(["Excellent", feedbacks.filter(experience="excellent").count()])
        ws.append(["Good", feedbacks.filter(experience="good").count()])
        ws.append(["Average", feedbacks.filter(experience="average").count()])
        ws.append(["Poor", feedbacks.filter(experience="poor").count()])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = (
        f'attachment; filename={mode}_report_{event.id}.xlsx'
    )

    wb.save(response)
    return response