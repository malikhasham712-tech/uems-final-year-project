from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views
from events import views as events_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Accounts
    path('', accounts_views.home, name='home'),
    path('accounts/', include('accounts.urls')),

    # Events (NO prefix)
    path('', include('events.urls')),   # 🔥 FIXED

    # Dashboard
    path('dashboard/', events_views.dashboard, name='dashboard'),
]