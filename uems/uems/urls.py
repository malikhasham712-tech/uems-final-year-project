from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Accounts app URLs
    path('', accounts_views.home, name='home'),
    path('accounts/register/', accounts_views.register, name='register'),
    path('accounts/login/', accounts_views.login_view, name='login'),
    path('accounts/logout/', accounts_views.logout_view, name='logout'),
    path('dashboard/', accounts_views.dashboard, name='dashboard'),
    path('verify-email/<str:token>/', accounts_views.verify_email, name='verify-email'),

    # Events app URLs
    path('events/', include('events.urls')),  # ✅ this includes all URLs from events app
]