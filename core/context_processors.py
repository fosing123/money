from django.db.utils import OperationalError, ProgrammingError

from .models import AppAppearance, BrandAsset
from .theme import build_theme_variables


def branding_context(request):
    """Expose Nkem brand settings, theme tokens and the signed-in user's unread count."""
    appearance, assets, unread = None, {}, 0
    user = getattr(request, "user", None)
    theme_variables = build_theme_variables(user)
    try:
        appearance = AppAppearance.objects.first()
        assets = {asset.key: asset for asset in BrandAsset.objects.filter(is_active=True)}
        if user is not None and user.is_authenticated:
            from notifications.models import Notification
            unread = Notification.objects.filter(user=user, is_read=False).count()
    except (OperationalError, ProgrammingError):
        appearance, assets, unread = None, {}, 0
    return {
        "appearance": appearance,
        "brand_assets": assets,
        "unread_notification_count": unread,
        "theme_variables": theme_variables,
    }
