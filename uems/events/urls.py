from django.urls import path
from . import views

urlpatterns = [

    path('my-events/', views.my_events, name='my_events'),

    path('submit-proposal/', views.submit_proposal, name='submit_proposal'),

    path('my-proposals/', views.my_proposals, name='my_proposals'),

    # Faculty Panel
    path('faculty-proposals/', views.faculty_proposals, name='faculty_proposals'),

    path('approve/<int:proposal_id>/', views.approve_proposal, name='approve_proposal'),

    path('reject/<int:proposal_id>/', views.reject_proposal, name='reject_proposal'),

]