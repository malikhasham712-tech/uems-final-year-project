from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Profile

# Register Profile
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username',)

    def get_fields(self, request, obj=None):
        if obj:
            return ('user_detail', 'role', 'email_verified', 'is_organizer')

        return ('user', 'role', 'email_verified', 'is_organizer')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('user_detail', 'email_verified', 'is_organizer')

        return ()

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'role':
            kwargs['choices'] = (
                ('student', 'Student'),
                ('faculty', 'Faculty'),
            )

        return super().formfield_for_choice_field(db_field, request, **kwargs)

    @admin.display(description='User')
    def user_detail(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.id])

        return format_html(
            '{} <a class="related-widget-wrapper-link view-related" href="{}" '
            'target="_blank" rel="noopener noreferrer" title="View selected user" '
            'style="margin-left:18px; vertical-align:middle;">'
            '<img src="/static/admin/img/icon-viewlink.svg" alt="" width="24" height="24"></a>',
            obj.user.username,
            url
        )

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        response = super().render_change_form(
            request,
            context,
            add=add,
            change=change,
            form_url=form_url,
            obj=obj
        )

        response.context_data['show_save_and_add_another'] = False
        response.context_data['show_save_and_continue'] = False

        return response

admin.site.register(Profile, ProfileAdmin)
