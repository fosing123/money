from pathlib import Path

from django.core.exceptions import ValidationError

MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def validate_uploaded_image(image):
    """Keep admin/user imagery to common raster formats and a sensible upload size."""
    if not image:
        return
    if getattr(image, "size", 0) > MAX_IMAGE_BYTES:
        raise ValidationError("Please upload an image smaller than 5 MB.")
    extension = Path(getattr(image, "name", "")).suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError("Use a JPG, PNG or WebP image.")