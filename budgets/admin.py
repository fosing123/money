from django.contrib import admin

from .models import Budget


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "period", "category", "amount", "currency", "start_date", "end_date")
    list_filter = ("period", "currency", "start_date")
    search_fields = ("name", "category", "owner__username", "owner__email")
    autocomplete_fields = ("owner",)