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
    list_display = (
        "name",
        "address",
        "workshop_manager_name",
        "service_advisor_name",
        "bank_name",
        "created_at",
    )
    search_fields = (
        "name",
        "address",
        "workshop_manager_name",
        "service_advisor_name",
        "bank_name",
        "account_name",
    )
    ordering = ("name",)
    fieldsets = (
        (None, {"fields": ("name", "address")}),
        (
            "Signatory Information",
            {
                "fields": (
                    "workshop_manager_name",
                    "workshop_manager_phone",
                    "workshop_manager_email",
                    "service_advisor_name",
                    "service_advisor_phone",
                    "service_advisor_email",
                ),
                "description": "Branch-specific signatory names and contact information for invoice printing",
            },
        ),
        (
            "Account Details",
            {
                "fields": ("bank_name", "account_number", "account_name"),
                "description": "Branch bank account details for payment processing",
            },
        ),
    )
