from django.db.utils import OperationalError, ProgrammingError

from .models import AppAppearance, BrandAsset


def branding_context(request):
    """Expose optional, admin-managed visual settings to all templates."""
    try:
        appearance = AppAppearance.objects.first()
        assets = {asset.key: asset for asset in BrandAsset.objects.filter(is_active=True).select_related()}
    except (OperationalError, ProgrammingError):
        # Keep the public app renderable during the first migration on a new install.
        appearance, assets = None, {}
    return {"appearance": appearance, "brand_assets": assets}