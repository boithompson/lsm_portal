from django.urls import path
from .views import log_view

app_name = "user_activity"

urlpatterns = [
    path("logs/", log_view, name="log_view"),
]
