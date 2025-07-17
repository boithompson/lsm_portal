from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    path("inventory/add/", views.add_inventory, name="add_inventory"),
    path("inventory/", views.inventory_list, name="inventory_list"),
    path("inventory/<str:pk>/", views.inventory_detail, name="inventory_detail"),
]
