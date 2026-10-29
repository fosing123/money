from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class TianaUserAdmin(UserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "currency", "theme", "onboarding_completed", "is_staff")
    list_filter = ("theme", "currency", "onboarding_completed", "is_staff", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    fieldsets = UserAdmin.fieldsets + (
        ("TIANA preferences", {"fields": ("currency", "timezone", "phone_number", "is_verified", "theme", "onboarding_completed")}),
        ("Money setup", {"fields": ("weekly_income", "weekly_savings_target", "payday_weekday", "financial_priorities")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("TIANA preferences", {"fields": ("email", "currency", "theme")}),
    )