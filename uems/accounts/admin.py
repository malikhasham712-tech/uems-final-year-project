from django.contrib import admin
from django.contrib.auth.models import User
from .models import Profile

# Register Profile
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username',)

admin.site.register(Profile, ProfileAdmin)