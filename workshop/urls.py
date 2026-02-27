from django.urls import path
from . import views

app_name = "workshop"

urlpatterns = [
    path(
        "vehicle/<int:vehicle_id>/internal_estimate/print/",
        views.print_proforma_invoice,
        name="print_proforma_invoice",
    ),
    path(
        "export/",
        views.WorkshopExportView.as_view(),
        name="workshop_export",
    ),
]
