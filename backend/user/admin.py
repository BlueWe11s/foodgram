from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from user.models import Follow, Users


class UserAdmin(BaseUserAdmin):
    list_display = (
        'first_name',
        'last_name',
        'username',
        'email',
    )
    search_fields = (
        'email',
        'username',
    )


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'author'
    )


admin.site.register(Users, UserAdmin)
admin.site.register(Follow, SubscriptionAdmin)
