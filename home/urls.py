from django.urls import path
from . import views

app_name = "home"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("staffs/", views.staffs, name="staffs"),
    path("workshop/", views.workshop, name="workshop"),
    path("vehicle/add/", views.add_vehicle, name="add_vehicle"),
    path("vehicle/<int:vehicle_id>/", views.vehicle_detail, name="vehicle_detail"),
    path("vehicle/<int:vehicle_id>/edit/", views.edit_vehicle, name="edit_vehicle"),
    path(
        "vehicle/<int:vehicle_id>/update_status/",
        views.update_vehicle_status,
        name="update_vehicle_status",
    ),
    path(
        "vehicle/<int:vehicle_id>/delete/", views.delete_vehicle, name="delete_vehicle"
    ),
    path(
        "vehicle/<int:vehicle_id>/job_sheet/create/",
        views.create_job_sheet,
        name="create_job_sheet",
    ),
    path(
        "vehicle/<int:vehicle_id>/job_sheet/edit/",
        views.edit_job_sheet,
        name="edit_job_sheet",
    ),
    path(
        "vehicle/<int:vehicle_id>/internal_estimate/create/",
        views.create_internal_estimate,
        name="create_internal_estimate",
    ),
    path(
        "vehicle/<int:vehicle_id>/internal_estimate/edit/",
        views.edit_internal_estimate,
        name="edit_internal_estimate",
    ),
]
