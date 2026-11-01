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
    return {"appearance": appearance, "brand_assets": assets, "unread_notification_count": unread}