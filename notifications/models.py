from django.conf import settings
from django.db import models


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    kind = models.CharField(max_length=30, default='info')
    source = models.CharField(
        max_length=20,
        choices=[("system", "System"), ("ai", "AI")],
        default="system",
    )
    dedupe_key = models.CharField(max_length=160, blank=True, default="")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=["user", "dedupe_key"],
                condition=~models.Q(dedupe_key=""),
                name="notification_user_dedupe_unique",
            ),
        ]

    def __str__(self):
        return self.title
