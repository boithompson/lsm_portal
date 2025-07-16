from django.contrib import admin
from .models import Vehicle, JobSheet, InternalEstimate, EstimatePart


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "vehicle_make",
        "model",
        "licence_plate",
        "customer_name",
        "branch",
        "status",
    )
    search_fields = (
        "vehicle_make",
        "model",
        "licence_plate",
        "customer_name",
        "chasis_no",
    )
    list_filter = ("status", "branch")
    ordering = ("-id",)


@admin.register(JobSheet)
class JobSheetAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "service_advisor", "assigned_to")
    search_fields = (
        "vehicle__licence_plate",
        "service_advisor__full_name",
        "assigned_to__full_name",
    )


@admin.register(InternalEstimate)
class InternalEstimateAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "grand_total")
    search_fields = ("vehicle__licence_plate",)


@admin.register(EstimatePart)
class EstimatePartAdmin(admin.ModelAdmin):
    list_display = ("name", "estimate", "price", "quantity")
    search_fields = ("name", "estimate__vehicle__licence_plate")
    list_filter = ("estimate__vehicle__branch",)
