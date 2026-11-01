from django.conf import settings
from django.db import models


class ChatMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_messages')
    prompt = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.prompt[:60]



class AIUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tiana_ai_usage")
    usage_date = models.DateField()
    request_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-usage_date"]
        constraints = [
            models.UniqueConstraint(fields=["user", "usage_date"], name="ai_user_daily_usage_uniq"),
        ]

    def __str__(self):
        return f"{self.user} · {self.usage_date} · {self.request_count}"


class AIResponseCache(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tiana_ai_cache")
    fingerprint = models.CharField(max_length=64)
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "fingerprint"], name="ai_user_response_fingerprint_uniq"),
        ]

    def __str__(self):
        return f"Cached TIANA response · {self.user}"
