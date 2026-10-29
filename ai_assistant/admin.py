from django.contrib import admin

from .models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("user", "short_prompt", "created_at")
    search_fields = ("user__username", "user__email", "prompt")
    list_filter = ("created_at",)
    readonly_fields = ("user", "prompt", "response", "created_at")
    fields = ("user", "prompt", "response", "created_at")

    @admin.display(description="Prompt")
    def short_prompt(self, obj):
        return obj.prompt[:90]