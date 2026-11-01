from django.contrib import admin
from django.utils.html import format_html

from .models import Opportunity


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "category", "price_amount", "currency", "location", "is_featured", "is_active", "preview")
    list_filter = ("kind", "category", "is_featured", "is_active", "location")
    list_editable = ("is_featured", "is_active")
    search_fields = ("name", "description", "seller_name", "category", "location")
    readonly_fields = ("preview", "created_at", "updated_at")
    fields = ("name", "kind", "category", "description", "price_amount", "currency", "location", "seller_name", "image", "preview", "contact_url", "is_featured", "is_active", "published_at", "created_at", "updated_at")

    @admin.display(description="Image")
    def preview(self, obj):
        if not obj or not obj.image:
            return "No image"
        return format_html('<img src="{}" alt="" style="width:110px;height:80px;object-fit:cover;border-radius:10px"/>', obj.image.url)