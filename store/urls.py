from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    path("stock/add/", views.add_stock, name="add_stock"),
    path("stock/", views.stock_list, name="stock_list"),
    path("stock/export/", views.StockExportView.as_view(), name="stock_export"),
    path("stock/<str:pk>/", views.stock_detail, name="stock_detail"),
    path("sales/", views.sales_dashboard, name="sales_dashboard"),
    path("sales/list/", views.sales_list_by_branch, name="sales_list_by_branch"),
    path(
        "sales/list/branch/<str:branch_pk>/",
        views.sales_list_by_branch,
        name="sales_list_by_branch_filter",
    ),
    path("sales/create/", views.create_sales_record, name="create_sales_record"),
    path(
        "sales/<str:pk>/",
        views.SalesRecordDetailView.as_view(),
        name="sales_record_detail",
    ),
    path("sales/export/", views.SalesExportView.as_view(), name="sales_export"),
    path("stock/central/add/", views.central_add_stock_view, name="central_add_stock"),
    path(
        "stock/central/edit/<str:stock_name>/",
        views.central_add_stock_view,
        name="central_edit_stock",
    ),
]
