from django.db import models
from django.conf import settings

class UserActivityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_index=True)
    url = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    action_description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "User Activity Log"
        verbose_name_plural = "User Activity Logs"

    def __str__(self):
        return f"{self.user.email} - {self.method} {self.url} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
