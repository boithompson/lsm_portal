from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from home import views as home_views # Import custom error views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("store.urls")),
    path("dashboard/", include("home.urls")),
    path("dashboard/", include("workshop.urls")), # Include workshop app URLs
]

# Custom error handlers
handler404 = home_views.custom_404
handler500 = home_views.custom_500
handler403 = home_views.custom_403
handler400 = home_views.custom_400

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # Add this line for static files
