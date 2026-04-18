from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [

    # DASHBOARD
    path('dashboard/', views.dashboard, name='dashboard'),

    # EVENTS
    path('my-events/', views.my_events, name='my_events'),
    path('available-events/', views.available_events, name='available_events'),
    path('event/<int:event_id>/', views.view_event, name='view_event'),

    # REGISTRATION
    path('event/<int:event_id>/register/', views.register_event, name='register_event'),
    path('event/<int:event_id>/registrations/', views.event_registrations, name='event_registrations'),

    # PROPOSALS
    path('event/<int:event_id>/proposals/', views.view_proposals, name='view_proposals'),
    path('event/<int:event_id>/submit-proposal/', views.submit_proposal, name='submit_proposal'),

    # ANNOUNCEMENTS
    path('send-announcement/', views.send_announcement, name='send_announcement'),
    path('event/<int:event_id>/announcements/', views.event_announcements, name='event_announcements'),

    # NOTIFICATIONS
    path('notifications/', views.notifications, name='notifications'),

    path('notifications/<int:notification_id>/', views.notification_detail, name='notification_detail'),

    # FEEDBACK (STUDENT SUBMIT)
    path('event/<int:event_id>/feedback/', views.event_feedback, name='event_feedback'),

    # FEEDBACK (ORGANIZER/ADMIN VIEW)
    path('event/<int:event_id>/feedbacks/', views.view_feedbacks, name='view_feedbacks'),

    # CANCEL
    path('event/<int:event_id>/cancel/', views.cancel_registration, name='cancel_registration'),
]