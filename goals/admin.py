from django.contrib import admin
from django.utils.html import format_html

from .models import Goal, GoalContribution


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "status", "target_amount", "current_amount", "target_date", "preview")
    list_filter = ("status", "currency", "target_date")
    search_fields = ("name", "owner__username", "owner__email")
    autocomplete_fields = ("owner",)
    readonly_fields = ("preview", "created_at", "updated_at")

    def has_delete_permission(self, request, obj=None):
        if obj and obj.contributions.exists():
            return False
        return super().has_delete_permission(request, obj)

    @admin.display(description="Goal image")
    def preview(self, obj):
        if not obj or not obj.image:
            return "No image"
        return format_html('<img src="{}" alt="" style="width:110px;height:80px;object-fit:cover;border-radius:10px"/>', obj.image.url)


@admin.register(GoalContribution)
class GoalContributionAdmin(admin.ModelAdmin):
    list_display = ("goal", "owner", "transaction", "created_at")
    list_filter = ("created_at",)
    search_fields = ("goal__name", "owner__username", "owner__email", "note")
    readonly_fields = ("owner", "goal", "transaction", "note", "created_at")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
