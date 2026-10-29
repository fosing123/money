from django.contrib import admin
from django.utils.html import format_html

from .models import Account, Transaction


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "account_type", "currency", "opening_balance", "balance", "is_active")
    list_filter = ("account_type", "currency", "is_active")
    search_fields = ("name", "owner__username", "owner__email")
    autocomplete_fields = ("owner",)
    readonly_fields = ("balance", "created_at", "updated_at")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("transaction_date", "owner", "kind", "category", "amount", "currency", "account")
    list_filter = ("kind", "category", "currency", "transaction_date")
    search_fields = ("description", "merchant", "owner__username", "owner__email")
    autocomplete_fields = ("owner", "account")
    date_hierarchy = "transaction_date"
    readonly_fields = ("created_at", "updated_at")