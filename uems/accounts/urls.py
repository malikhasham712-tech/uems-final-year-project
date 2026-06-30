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
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('admin-profile/', views.admin_profile, name='admin_profile'),
    path('admin-profile/edit/', views.admin_edit_profile, name='admin_edit_profile'),
    path('password/change/', views.change_password, name='password_change'),
]
