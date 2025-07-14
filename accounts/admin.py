from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'full_name', 'phone', 'access_level', 'is_staff')
    search_fields = ('email', 'full_name', 'phone')
    readonly_fields = ('unique_id',)
    ordering = ('email',)

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

admin.site.register(CustomUser, CustomUserAdmin)
