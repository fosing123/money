from django.contrib import admin
from django.utils.html import format_html

from .models import AppAppearance, BrandAsset


@admin.register(AppAppearance)
class AppAppearanceAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Brand", {"fields": ("app_name", "tagline")}),
        ("Colour palette", {"fields": ("primary_color", "dark_color", "soft_color", "background_color", "text_color")}),
    )
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        return not AppAppearance.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BrandAsset)
class BrandAssetAdmin(admin.ModelAdmin):
    list_display = ("title", "key", "preview", "is_active", "updated_at")
    list_filter = ("is_active", "key")
    search_fields = ("title", "alt_text")
    list_editable = ("is_active",)
    readonly_fields = ("preview", "updated_at")
    fields = ("key", "title", "image", "preview", "alt_text", "is_active", "updated_at")

    @admin.display(description="Preview")
    def preview(self, obj):
        if not obj or not obj.image:
            return "No image uploaded"
        return format_html(
            '<img src="{}" alt="" style="max-width:160px;max-height:100px;object-fit:cover;border-radius:12px" />',
            obj.image.url,
        )