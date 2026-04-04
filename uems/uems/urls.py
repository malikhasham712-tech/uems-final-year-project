from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views
from events import views as events_views  # <-- import dashboard here

urlpatterns = [
    path('admin/', admin.site.urls),

    # Accounts
    path('', accounts_views.home, name='home'),
    path('accounts/', include('accounts.urls')),

    # Events
    path('events/', include('events.urls')),

    # Dashboard (single source of truth in events.views)
    path('dashboard/', events_views.dashboard, name='dashboard'),
]