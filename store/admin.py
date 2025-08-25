from django.contrib import admin
from .models import Stock, SalesRecord, SalesItem


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "quantity",
        "unit_value",
        "branch",
        "added_on",
    )
    list_filter = ("branch", "added_on")
    search_fields = ("name", "branch__name")


class SalesItemInline(admin.TabularInline):
    model = SalesItem
    extra = 1
    raw_id_fields = [
        "stock_item"
    ]
    fields = ("stock_item", "quantity_sold", "price_at_sale")


@admin.register(SalesRecord)
class SalesRecordAdmin(admin.ModelAdmin):
    list_display = (
        "customer_name",
        "branch",
        "marketer",
        "sale_date",
        "total_amount",
        "amount_paid_cash",
        "credit_owed",
    )
    list_filter = ("branch", "sale_date")
    search_fields = ("customer_name", "marketer", "branch__name")
    inlines = [SalesItemInline]
    readonly_fields = (
        "total_amount",
        "sale_date",
    )  # total_amount is calculated, sale_date is auto_now_add

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if (
            request.user.is_superuser
            or request.user.access_level == "admin"
            or request.user.access_level == "manager"
        ):
            return qs
        return qs.filter(branch=request.user.branch)

    def save_model(self, request, obj, form, change):
        # Ensure branch is set for non-admins if not already set
        if (
            not obj.branch
            and not request.user.is_superuser
            and request.user.access_level not in ["admin", "manager"]
        ):
            obj.branch = request.user.branch
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, SalesItem):
                # Update stock quantity
                if instance.stock_item and instance.quantity_sold:
                    instance.stock_item.quantity -= instance.quantity_sold
                    instance.stock_item.save()
            instance.save()
        formset.save_m2m()
