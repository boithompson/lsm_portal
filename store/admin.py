from django.contrib import admin
from .models import Inventory


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = (
        "vehicle_type",
        "make",
        "model",
        "year",
        "branch",
        "status",
        "price",
        "image_tag",
    )
    list_filter = ("branch", "status", "vehicle_type", "year")
    search_fields = ("make", "model", "vin")

    readonly_fields = ["image_tag"]

    def image_tag(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="100" height="60" style="object-fit:cover;" />'
        return "No Image"

    image_tag.allow_tags = True
    image_tag.short_description = "Image"
