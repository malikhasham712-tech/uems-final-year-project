from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from accounts import views as accounts_views
from events import views as events_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Accounts
    path('', lambda request: redirect('login'), name='home'),
    path('accounts/', include('accounts.urls')),

    # Events (NO prefix)
    path('', include('events.urls')),   # 🔥 FIXED

    
]