from django.urls import path
from .views import login_view, logout_view, add_staff, edit_staff, delete_staff

app_name = "accounts"

urlpatterns = [
    path("", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("staffs/add/", add_staff, name="add_staff"),
    path("staffs/edit/<int:user_id>/", edit_staff, name="edit_staff"),
    path("staffs/delete/<int:user_id>/", delete_staff, name="delete_staff"),
]
