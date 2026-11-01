from django.contrib import admin

from .models import AIResponseCache, AIUsage, ChatMessage


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


@admin.register(AIUsage)
class AIUsageAdmin(admin.ModelAdmin):
    list_display = ("user", "usage_date", "request_count", "updated_at")
    list_filter = ("usage_date",)
    search_fields = ("user__username", "user__email")
    readonly_fields = ("user", "usage_date", "request_count", "created_at", "updated_at")


@admin.register(AIResponseCache)
class AIResponseCacheAdmin(admin.ModelAdmin):
    list_display = ("user", "fingerprint", "created_at")
    search_fields = ("user__username", "user__email", "fingerprint")
    readonly_fields = ("user", "fingerprint", "response", "created_at")
