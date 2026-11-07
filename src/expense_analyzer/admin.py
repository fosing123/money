from django.contrib import admin

from .models import AIPersonalization, ExpenseAnalysis


@admin.register(ExpenseAnalysis)
class ExpenseAnalysisAdmin(admin.ModelAdmin):
    list_display = ("description", "user", "analysis_type", "amount", "currency", "score", "verdict", "created_at")
    list_filter = ("analysis_type", "verdict", "currency", "created_at")
    search_fields = ("description", "category", "user__username", "user__email")
    readonly_fields = ("created_at",)
    list_select_related = ("user", "transaction")



@admin.register(AIPersonalization)
class AIPersonalizationAdmin(admin.ModelAdmin):
    list_display = ("user", "voice_style", "ambition", "current_stage", "updated_at")
    list_filter = ("voice_style", "ambition", "current_stage")
    search_fields = ("user__username", "user__email", "future_vision", "desired_career")
    readonly_fields = ("created_at", "updated_at")
