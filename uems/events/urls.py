from django.urls import path
from . import views

urlpatterns = [
    path('my-events/', views.my_events, name='my_events'),
    path('my-proposals/', views.my_proposals, name='my_proposals'),
    path('submit-proposal/<int:event_id>/', views.submit_proposal, name='submit_proposal'),
]