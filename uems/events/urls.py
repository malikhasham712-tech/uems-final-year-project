from django.urls import path
from . import views

urlpatterns = [
    path('my_events/', views.my_events, name='my_events'),  # ← name must match
    path('submit-proposal/<int:event_id>/', views.submit_proposal, name='submit_proposal'),
    path('view-event/<int:event_id>/', views.view_event, name='view_event'),
    path('view-proposals/<int:event_id>/', views.view_proposals, name='view_proposals'),
]