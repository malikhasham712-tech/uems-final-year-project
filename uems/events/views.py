from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.http import JsonResponse
from django.urls import reverse
from django.db.models import Q

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
    EventMessage,
    Notification,
    EventStatus,
    ProposalStatus,
)

from .forms import EventMessageForm, ProposalForm, EventRegistrationForm
from .notification_router import send_notification


# =====================================================
# NOTIFICATION CONTEXT
# =====================================================
def notif_context(request):

    if request.user.is_authenticated:

        notifications = request.user.notifications.all().order_by(
            "-created_at"
        )
        unread_event_messages = EventMessage.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()

        return {

            "notifications": notifications[:10],

            "unread_notifications": notifications.filter(
                is_read=False
            ).count(),

            "unread_event_messages": unread_event_messages
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


def is_registered_for_event(user, event):
    return EventRegistration.objects.filter(
        event=event,
        student=user
    ).exists()


def get_message_partner(user, event, partner_id):
    partner = get_object_or_404(User, id=partner_id)

    if user == event.organizer:
        if is_registered_for_event(partner, event):
            return partner

        return None

    if (
        event.organizer_id == partner.id
        and is_registered_for_event(user, event)
    ):
        return partner

    return None


def get_event_thread(event, user, partner):
    return EventMessage.objects.filter(
        event=event
    ).filter(
        Q(sender=user, recipient=partner)
        | Q(sender=partner, recipient=user)
    ).select_related(
        "sender",
        "recipient"
    )


def serialize_event_messages(messages_qs, user):
    return [
        {
            "id": msg.id,
            "sender": msg.sender.username,
            "message": msg.message,
            "created_at": msg.created_at.strftime("%d %b %Y, %I:%M %p"),
            "is_mine": msg.sender_id == user.id,
        }
        for msg in messages_qs
    ]


# =====================================================
# DASHBOARD
# =====================================================
@login_required
def dashboard(request):

    has_assigned_events = Event.objects.filter(
        organizer=request.user
    ).exists()

    if (
        hasattr(request.user, 'profile')
        and (
            request.user.profile.is_organizer
            or has_assigned_events
        )
    ):
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

    elif hasattr(request.user, 'profile') and request.user.profile.role == 'faculty':
        # FACULTY DASHBOARD - View registered students
        students = User.objects.filter(
            profile__role='student'
        ).select_related('profile')

        total_students = students.count()

        return render(request, "accounts/faculty_dashboard.html", {
            "role": "faculty",
            "students": students,
            "total_students": total_students,
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

    has_assigned_events = Event.objects.filter(
        organizer=request.user
    ).exists()

    if (
        hasattr(request.user, 'profile')
        and (
            request.user.profile.is_organizer
            or has_assigned_events
        )
    ):
        return redirect("events:dashboard")

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
def manage_event(request, event_id):

    event = get_object_or_404(
        Event.objects.select_related("category", "organizer"),
        id=event_id
    )

    if not is_organizer_or_admin(request.user, event):
        return redirect("events:dashboard")

    registrations = EventRegistration.objects.filter(event=event)
    attendance = Attendance.objects.filter(event=event)
    feedbacks = Feedback.objects.filter(event=event)
    announcements = Announcement.objects.filter(event=event)

    latest_proposal = EventProposal.objects.filter(
        event=event
    ).order_by("-submitted_at").first()

    accepted_proposal = EventProposal.objects.filter(
        event=event,
        status=ProposalStatus.ACCEPTED
    ).order_by("-submitted_at").first()

    total_registrations = registrations.count()
    total_attendance = attendance.count()

    return render(request, "events/manage_event.html", {
        "event": event,
        "latest_proposal": latest_proposal,
        "accepted_proposal": accepted_proposal,
        "total_registrations": total_registrations,
        "total_attendance": total_attendance,
        "total_absent": max(total_registrations - total_attendance, 0),
        "total_feedback": feedbacks.count(),
        "total_announcements": announcements.count(),
        "role": "admin" if request.user.is_superuser else "organizer",
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
# EVENT MESSAGING
# =====================================================
@login_required
def message_inbox(request):

    user = request.user
    has_assigned_events = Event.objects.filter(
        organizer=user
    ).exists()
    role = (
        "organizer"
        if (
            hasattr(user, "profile")
            and (
                user.profile.is_organizer
                or has_assigned_events
            )
        )
        else get_role(user)
    )

    message_qs = EventMessage.objects.filter(
        Q(sender=user) | Q(recipient=user)
    ).select_related(
        "event",
        "sender",
        "recipient"
    ).order_by(
        "-created_at"
    )

    conversations = []
    seen = set()

    for msg in message_qs:

        partner = (
            msg.recipient
            if msg.sender_id == user.id
            else msg.sender
        )

        key = (
            msg.event_id,
            partner.id
        )

        if key in seen:
            continue

        if not get_message_partner(
            user,
            msg.event,
            partner.id
        ):
            continue

        seen.add(key)

        conversations.append({
            "event": msg.event,
            "partner": partner,
            "latest_message": msg,
            "unread_count": EventMessage.objects.filter(
                event=msg.event,
                sender=partner,
                recipient=user,
                is_read=False
            ).count()
        })

    return render(request, "events/message_inbox.html", {
        "conversations": conversations,
        "role": role,
        **notif_context(request)
    })


@login_required
def unread_message_count(request):
    unread_count = EventMessage.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()

    return JsonResponse({
        "success": True,
        "unread_count": unread_count
    })


@login_required
def event_message_thread(request, event_id, user_id):

    event = get_object_or_404(
        Event.objects.select_related("organizer"),
        id=event_id
    )
    role = (
        "organizer"
        if request.user == event.organizer
        else get_role(request.user)
    )

    partner = get_message_partner(
        request.user,
        event,
        user_id
    )

    if not partner:
        messages.error(
            request,
            "You are not allowed to message this participant for this event."
        )

        return redirect("events:my_events")

    if request.method == "POST":

        form = EventMessageForm(request.POST)

        if form.is_valid():

            obj = form.save(commit=False)
            obj.event = event
            obj.sender = request.user
            obj.recipient = partner
            obj.save()

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return JsonResponse({"success": True})

            return redirect(
                "events:event_message_thread",
                event_id=event.id,
                user_id=partner.id
            )

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({
                "success": False,
                "errors": form.errors
            }, status=400)

    EventMessage.objects.filter(
        event=event,
        sender=partner,
        recipient=request.user,
        is_read=False
    ).update(
        is_read=True
    )

    thread_messages = get_event_thread(
        event,
        request.user,
        partner
    )

    return render(request, "events/event_message_thread.html", {
        "event": event,
        "partner": partner,
        "messages": thread_messages,
        "form": EventMessageForm(),
        "role": role,
        **notif_context(request)
    })


@login_required
def event_messages_latest(request, event_id, user_id):

    event = get_object_or_404(
        Event.objects.select_related("organizer"),
        id=event_id
    )

    partner = get_message_partner(
        request.user,
        event,
        user_id
    )

    if not partner:
        return JsonResponse({
            "success": False,
            "message": "Not allowed"
        }, status=403)

    EventMessage.objects.filter(
        event=event,
        sender=partner,
        recipient=request.user,
        is_read=False
    ).update(
        is_read=True
    )

    return JsonResponse({
        "success": True,
        "messages": serialize_event_messages(
            get_event_thread(event, request.user, partner),
            request.user
        )
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
