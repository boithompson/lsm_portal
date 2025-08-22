from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    path("inventory/add/", views.add_inventory, name="add_inventory"),
    path("inventory/", views.inventory_list, name="inventory_list"),
    path("inventory/export/", views.InventoryExportView.as_view(), name="inventory_export"),
    path("inventory/<str:pk>/", views.inventory_detail, name="inventory_detail"),
    path("sales/", views.sales_dashboard, name="sales_dashboard"),
    path(
        "sales/branch/<str:branch_pk>/",
        views.sales_detail_branch,
        name="sales_detail_branch",
    ),
    path("sales/create/", views.create_sales_record, name="create_sales_record"),
    path("sales/export/", views.SalesExportView.as_view(), name="sales_export"),
]
