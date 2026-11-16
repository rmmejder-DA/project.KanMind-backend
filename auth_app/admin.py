"""Admin configuration for the authentication app."""

from django.contrib import admin

from auth_app.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Lists and edits users; passwords are set via createsuperuser."""

    list_display = ['email', 'fullname', 'is_staff']
    search_fields = ['email', 'fullname']
    exclude = ['password', 'last_login']
