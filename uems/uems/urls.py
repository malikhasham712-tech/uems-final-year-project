from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Accounts URLs
    path('accounts/', include('accounts.urls')),

    # Events URLs
    path('events/', include('events.urls')),

    # Root URL (home page)
    path('', include('accounts.urls')),
]