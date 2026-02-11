from .models import UserActivityLog
from django.urls import reverse
from django.utils import timezone


class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Log activity for authenticated users, excluding static/media files and admin logs page itself
        if (
            request.user.is_authenticated
            and not request.path.startswith(reverse("admin:index"))
            and not request.path.startswith(reverse("user_activity:log_view"))
        ):
            # Exclude static and media files
            if not (
                request.path.startswith("/static/")
                or request.path.startswith("/media/")
            ):
                UserActivityLog.objects.create(
                    user=request.user,
                    url=request.path,
                    method=request.method,
                    timestamp=timezone.now(),
                    # action_description can be added here if more specific logic is implemented
                )
        return response
