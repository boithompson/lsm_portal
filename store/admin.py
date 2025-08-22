from django.contrib import admin
from .models import Inventory, SalesRecord, SalesItem


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


class SalesItemInline(admin.TabularInline):
    model = SalesItem
    extra = 1
    raw_id_fields = ['inventory_item'] # Use raw_id_fields for ForeignKey to avoid dropdown for many items


@admin.register(SalesRecord)
class SalesRecordAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'branch', 'marketer', 'sale_date', 'total_amount', 'amount_paid_cash', 'credit_owed')
    list_filter = ('branch', 'sale_date')
    search_fields = ('customer_name', 'marketer', 'branch__name')
    inlines = [SalesItemInline]
    readonly_fields = ('total_amount', 'sale_date') # total_amount is calculated, sale_date is auto_now_add

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.access_level == "admin" or request.user.access_level == "manager":
            return qs
        return qs.filter(branch=request.user.branch)

    def save_model(self, request, obj, form, change):
        # Ensure branch is set for non-admins if not already set
        if not obj.branch and not request.user.is_superuser and request.user.access_level not in ["admin", "manager"]:
            obj.branch = request.user.branch
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, SalesItem):
                # Ensure inventory_item is linked and status updated
                if instance.inventory_item and instance.inventory_item.status != "sold":
                    instance.inventory_item.status = "sold"
                    instance.inventory_item.save()
            instance.save()
        formset.save_m2m()
