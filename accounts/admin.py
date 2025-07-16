from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Branch


class CustomUserAdmin(UserAdmin):
    list_display = ("email", "full_name", "phone", "access_level", "branch")
    search_fields = ("email", "full_name", "phone", "branch__name")
    readonly_fields = ("unique_id",)
    ordering = ("email",)

    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


admin.site.register(CustomUser, CustomUserAdmin)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "created_at")
    search_fields = ("name", "address")
    ordering = ("name",)
