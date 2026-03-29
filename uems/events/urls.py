from django.urls import path
from . import views

urlpatterns = [
    # Organizer/Admin
    path('my_events/', views.my_events, name='my_events'),
    path('submit_proposal/<int:event_id>/', views.submit_proposal, name='submit_proposal'),
    path('view_event/<int:event_id>/', views.view_event, name='view_event'),
    path('view_proposals/<int:event_id>/', views.view_proposals, name='view_proposals'),
    path('proposal/<int:proposal_id>/approve/', views.approve_proposal, name='approve_proposal'),
    path('proposal/<int:proposal_id>/reject/', views.reject_proposal, name='reject_proposal'),
    path('event_registrations/<int:event_id>/', views.event_registrations, name='event_registrations'),
    path('my_proposals/', views.my_proposals, name='my_proposals'),

    # Student
    path('student_events/', views.student_events, name='student_events'),
    path('register_event/<int:event_id>/', views.register_event, name='register_event'),
]