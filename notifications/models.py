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



class PushDevice(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_devices")
    token = models.CharField(max_length=4096, unique=True)
    device_id = models.CharField(max_length=128, blank=True, default="")
    platform = models.CharField(max_length=20, default="web")
    user_agent = models.CharField(max_length=512, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-last_seen_at", "-updated_at"]
        indexes = [models.Index(fields=["user", "is_active"], name="push_user_active_idx")]

    def __str__(self):
        return f"{self.user_id} · {self.platform}"
