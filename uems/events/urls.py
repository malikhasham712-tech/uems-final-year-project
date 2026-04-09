from django.urls import path
from . import views

app_name = 'events'


urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('my-events/', views.my_events, name='my_events'),

    # Proposals
    path('event/<int:event_id>/proposals/', views.view_proposals, name='view_proposals'),
    path('proposal/submit/<int:event_id>/', views.submit_proposal, name='submit_proposal'),
    path('proposal/approve/<int:proposal_id>/', views.approve_proposal, name='approve_proposal'),
    path('proposal/reject/<int:proposal_id>/', views.reject_proposal, name='reject_proposal'),

    # Event details
    path('event/<int:event_id>/', views.view_event, name='view_event'),
    path('event/<int:event_id>/registrations/', views.event_registrations, name='event_registrations'),

    # Student side
    path('available-events/', views.available_events, name='available_events'),
    path('event/register/<int:event_id>/', views.register_event, name='register_event'),
]