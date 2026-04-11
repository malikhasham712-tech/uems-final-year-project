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
    path('proposal/<int:proposal_id>/approve/', views.approve_proposal, name='approve_proposal'),
    path('proposal/<int:proposal_id>/reject/', views.reject_proposal, name='reject_proposal'),

    # ANNOUNCEMENTS
    path('send-announcement/', views.send_announcement, name='send_announcement'),

    # IMPORTANT FIXED ROUTES (NO DUPLICATES)
    path('event/<int:event_id>/announcements/', views.event_announcements, name='event_announcements'),

    # NOTIFICATIONS
    path('notifications/', views.notifications, name='notifications'),

    # FEEDBACK (ONLY ONE ROUTE)
    path('event/<int:event_id>/feedback/', views.event_feedback, name='event_feedback'),
]