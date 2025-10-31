from django.contrib import admin
from .models import UserActivityLog

class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'url', 'method', 'timestamp', 'action_description')
    list_filter = ('user', 'method', 'timestamp')
    search_fields = ('user__email', 'url', 'action_description')
    readonly_fields = ('user', 'url', 'method', 'action_description', 'timestamp')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(UserActivityLog, UserActivityLogAdmin)
