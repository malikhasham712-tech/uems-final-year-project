from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as accounts_views
from events import views as events_views

admin.site.password_change_template = "admin/password_change_form.html"
admin.site.password_change_done_template = "admin/password_change_done.html"

urlpatterns = [
    path('admin/', lambda request: redirect('/admin/events/event/')),
    path('admin/', admin.site.urls),

    # Accounts
    path('', lambda request: redirect('login'), name='home'),
    path('accounts/', include('accounts.urls')),

    # Events (NO prefix)
    path('', include('events.urls')),   # 🔥 FIXED

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
