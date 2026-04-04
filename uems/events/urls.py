from django.urls import path
from . import views

urlpatterns = [
    # DASHBOARD
    path('dashboard/', views.dashboard, name='dashboard'),

    # ORGANIZER / ADMIN
    path('my-events/', views.my_events, name='my_events'),
    path('proposals/<int:event_id>/', views.view_proposals, name='view_proposals'),
    path('proposals/submit/<int:event_id>/', views.submit_proposal, name='submit_proposal'),
    path('proposals/approve/<int:proposal_id>/', views.approve_proposal, name='approve_proposal'),
    path('proposals/reject/<int:proposal_id>/', views.reject_proposal, name='reject_proposal'),
    path('events/<int:event_id>/', views.view_event, name='view_event'),
    path('events/<int:event_id>/registrations/', views.event_registrations, name='event_registrations'),

    # STUDENT
    path('student-events/', views.student_events, name='student_events'),
    path('events/register/<int:event_id>/', views.register_event, name='register_event'),
    path('available-events/', views.available_events, name='available_events'),  # NEW
]