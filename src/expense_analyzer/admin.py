from django.contrib import admin

from .models import ExpenseAnalysis


@admin.register(ExpenseAnalysis)
class ExpenseAnalysisAdmin(admin.ModelAdmin):
    list_display = ("description", "user", "analysis_type", "amount", "currency", "score", "verdict", "created_at")
    list_filter = ("analysis_type", "verdict", "currency", "created_at")
    search_fields = ("description", "category", "user__username", "user__email")
    readonly_fields = ("created_at",)
    list_select_related = ("user", "transaction")
