from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError

from .models import AppAppearance, BrandAsset


def branding_context(request):
    """Expose admin-managed brand settings and the signed-in user's unread count."""
    appearance, assets, unread = None, {}, 0
    try:
        appearance = AppAppearance.objects.first()
        assets = {asset.key: asset for asset in BrandAsset.objects.filter(is_active=True)}
        if getattr(request, "user", None) is not None and request.user.is_authenticated:
            from notifications.models import Notification
            unread = Notification.objects.filter(user=request.user, is_read=False).count()
    except (OperationalError, ProgrammingError):
        appearance, assets, unread = None, {}, 0
    user = getattr(request, "user", None)
    premium_member = bool(
        user is not None
        and user.is_authenticated
        and getattr(user, "has_active_premium", False)
    )
    adsterra_enabled = bool(getattr(settings, "ADSTERRA_ENABLED", False) and not premium_member)
    return {
        "appearance": appearance,
        "brand_assets": assets,
        "unread_notification_count": unread,
        "adsterra_enabled": adsterra_enabled,
        "adsterra_website_id": getattr(settings, "ADSTERRA_WEBSITE_ID", ""),
        "adsterra_banner_320x50_code": (
            getattr(settings, "ADSTERRA_BANNER_320X50_CODE", "") if adsterra_enabled else ""
        ),
        "adsterra_banner_300x250_code": (
            getattr(settings, "ADSTERRA_BANNER_300X250_CODE", "") if adsterra_enabled else ""
        ),
    }