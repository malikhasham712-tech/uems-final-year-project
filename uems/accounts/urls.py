from django.urls import path
from django.db.models import Count  # for counting registrations in dashboard
from . import views

urlpatterns = [
    path('', views.home, name='accounts-home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('verify/<uuid:token>/', views.verify_email, name='verify-email'),
    path('logout/', views.logout_view, name='logout'),
]