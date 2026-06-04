from django.contrib import admin
from .models import Vehicle, JobSheet, InternalEstimate, EstimatePart


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "vehicle_make",
        "model",
        "licence_plate",
        "chasis_no",
        "customer_name",
        "branch",
        "status",
        "date_created",
    )
    search_fields = (
        "uuid",
        "vehicle_make",
        "model",
        "licence_plate",
        "chasis_no",
        "customer_name",
        "phone",
    )
    list_filter = ("status", "branch", "vehicle_make", "year")
    ordering = ("-date_created",)
    readonly_fields = ("uuid", "date_created", "date_updated")
    fieldsets = (
        (None, {"fields": ("uuid", "branch", "customer_name", "address", "phone")}),
        (
            "Vehicle Information",
            {
                "fields": (
                    "vehicle_make",
                    "model",
                    "year",
                    "chasis_no",
                    "licence_plate",
                    "date_of_first_registration",
                    "mileage",
                )
            },
        ),
        ("Service Information", {"fields": ("job_no", "complaint", "status")}),
        (
            "System Information",
            {
                "fields": (
                    "date_created",
                    "date_updated",
                    "is_master_record",
                    "master_vehicle",
                ),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(JobSheet)
class JobSheetAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "service_advisor", "assigned_to", "job_summary")
    search_fields = (
        "vehicle__licence_plate",
        "vehicle__job_no",
        "vehicle__chasis_no",
        "service_advisor__full_name",
        "assigned_to",
        "job_description",
    )
    list_select_related = ("vehicle", "service_advisor")
    ordering = ("vehicle__job_no", "-vehicle__date_created")

    @admin.display(description="Job Summary")
    def job_summary(self, obj):
        return obj.job_description[:80] if obj.job_description else "-"


@admin.register(InternalEstimate)
class InternalEstimateAdmin(admin.ModelAdmin):
    list_display = (
        "vehicle",
        "discount_amount",
        "apply_vat",
        "is_invoice",
        "grand_total",
    )
    search_fields = (
        "vehicle__licence_plate",
        "vehicle__job_no",
        "vehicle__chasis_no",
        "vehicle__customer_name",
    )
    list_filter = ("apply_vat", "is_invoice", "vehicle__branch")
    list_select_related = ("vehicle",)
    fieldsets = (
        (None, {"fields": ("vehicle",)}),
        (
            "Estimate Details",
            {"fields": ("discount_amount", "apply_vat", "is_invoice")},
        ),
    )


@admin.register(EstimatePart)
class EstimatePartAdmin(admin.ModelAdmin):
    list_display = ("name", "estimate", "price", "quantity")
    search_fields = (
        "name",
        "estimate__vehicle__licence_plate",
        "estimate__vehicle__job_no",
        "estimate__vehicle__chasis_no",
    )
    list_filter = ("estimate__vehicle__branch", "estimate__is_invoice")
    list_select_related = ("estimate", "estimate__vehicle")
