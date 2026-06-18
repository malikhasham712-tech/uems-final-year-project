from django.urls import path
from django.db.models import Count  # For counting registrations in dashboard
from . import views

urlpatterns = [
    path('', views.home, name='accounts-home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('forgot-password/', views.forgot_password, name='forgot-password'),
    path('reset-password/<uidb64>/<token>/', views.reset_password_confirm, name='password-reset-confirm'),
    path('verify/<uuid:token>/', views.verify_email, name='verify-email'),
    path('logout/', views.logout_view, name='logout'),
    
]
