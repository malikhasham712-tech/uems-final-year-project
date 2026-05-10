from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [

    # ======================
    # DASHBOARD
    # ======================
    path(
        'dashboard/',
        views.dashboard,
        name='dashboard'
    ),

    # ======================
    # EVENTS
    # ======================
    path(
        'my-events/',
        views.my_events,
        name='my_events'
    ),

    path(
        'available-events/',
        views.available_events,
        name='available_events'
    ),

    path(
        'event/<int:event_id>/',
        views.view_event,
        name='view_event'
    ),

    # ======================
    # REGISTRATION
    # ======================
    path(
        'event/<int:event_id>/register/',
        views.register_event,
        name='register_event'
    ),

    path(
        'event/<int:event_id>/registrations/',
        views.event_registrations,
        name='event_registrations'
    ),

    # ======================
    # QR ATTENDANCE SYSTEM
    # ======================
    path(
        'event/<int:event_id>/generate-qr/',
        views.generate_qr,
        name='generate_qr'
    ),

    path(
        'attendance/<int:event_id>/',
        views.mark_attendance,
        name='mark_attendance'
    ),

    # ======================
    # ATTENDANCE RECORDS
    # ======================
    path(
        'event/<int:event_id>/attendance/',
        views.attendance_records,
        name='view_attendance'
    ),

    # ======================
    # PROPOSALS
    # ======================
    path(
        'event/<int:event_id>/proposals/',
        views.view_proposals,
        name='view_proposals'
    ),

    path(
        'event/<int:event_id>/submit-proposal/',
        views.submit_proposal,
        name='submit_proposal'
    ),

    # ======================
    # ANNOUNCEMENTS
    # ======================
    path(
        'send-announcement/',
        views.send_announcement,
        name='send_announcement'
    ),

    path(
        'event/<int:event_id>/announcements/',
        views.event_announcements,
        name='event_announcements'
    ),

    # ======================
    # NOTIFICATIONS
    # ======================
    path(
        'notifications/',
        views.notifications,
        name='notifications'
    ),

    path(
        'notifications/<int:notification_id>/',
        views.notification_detail,
        name='notification_detail'
    ),

    # ======================
    # FEEDBACK
    # ======================
    path(
        'event/<int:event_id>/feedback/',
        views.event_feedback,
        name='event_feedback'
    ),

    path(
        'event/<int:event_id>/feedbacks/',
        views.view_feedbacks,
        name='view_feedbacks'
    ),

    # ======================
    # CANCEL REGISTRATION
    # ======================
    path(
        'event/<int:event_id>/cancel/',
        views.cancel_registration,
        name='cancel_registration'
    ),

    # ======================
    # EVENT REPORT MODULE
    # ======================
    path(
        'reports/',
        views.event_report_list,
        name='event_report_list'
    ),

    path(
        'reports/<int:event_id>/',
        views.event_report,
        name='event_report'
    ),

    path(
        'reports/<int:event_id>/export/',
        views.export_event_report,
        name='export_event_report'
    ),
]