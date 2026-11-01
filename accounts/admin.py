from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class TianaUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "currency", "theme", "is_premium", "premium_expires_at", "onboarding_completed", "is_staff")
    list_filter = ("theme", "currency", "is_premium", "onboarding_completed", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    fieldsets = UserAdmin.fieldsets + (
        ("TIANA preferences", {"fields": ("currency", "timezone", "phone_number", "avatar", "is_verified", "theme", "onboarding_completed")}),
        ("Money setup", {"fields": ("weekly_income", "weekly_savings_target", "payday_weekday", "financial_priorities")}),
        ("Premium access", {"fields": ("is_premium", "premium_expires_at")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("TIANA preferences", {"fields": ("email", "currency", "theme")}),
    )
