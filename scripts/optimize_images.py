#!/usr/bin/env python3
"""Build responsive WebP derivatives for TIANA's large photographic assets.

Run before collectstatic:
    uv run python scripts/optimize_images.py

Original files remain untouched. Generated files live under static/assets/optimized
and are picked up by Django collectstatic and Cloudflare Workers Assets.
"""
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "static" / "assets"
OUTPUT_DIR = SOURCE_DIR / "optimized"

# (source file, [(output stem, max width, WebP quality), ...])
ASSETS = [
    ("tiana-welcome-student-campus-4k.jpg", [
        ("tiana-welcome-student-campus-800.webp", 800, 77),
        ("tiana-welcome-student-campus-1440.webp", 1440, 80),
        ("tiana-welcome-student-campus-1920.webp", 1920, 82),
    ]),
    ("tiana-logo-transparent.png", [
        ("tiana-logo-transparent-320.webp", 320, 88),
        ("tiana-logo-transparent-640.webp", 640, 90),
    ]),
    ("tiana-auth-campus.webp", [
        ("tiana-auth-campus-640.webp", 640, 78),
        ("tiana-auth-campus-1280.webp", 1280, 80),
    ]),
    ("tiana-onboarding-money-clarity-4k.webp", [
        ("tiana-onboarding-money-clarity-640.webp", 640, 78),
        ("tiana-onboarding-money-clarity-1200.webp", 1200, 80),
    ]),
    ("tiana-onboarding-savings-goals-4k.webp", [
        ("tiana-onboarding-savings-goals-640.webp", 640, 78),
        ("tiana-onboarding-savings-goals-1200.webp", 1200, 80),
    ]),
    ("tiana-onboarding-ai-coach-4k.webp", [
        ("tiana-onboarding-ai-coach-640.webp", 640, 78),
        ("tiana-onboarding-ai-coach-1200.webp", 1200, 80),
    ]),
    ("tiana-signup-welcome.webp", [
        ("tiana-signup-welcome-640.webp", 640, 78),
        ("tiana-signup-welcome-1200.webp", 1200, 80),
    ]),
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    original_total = 0
    optimized_total = 0

    for source_name, variants in ASSETS:
        source = SOURCE_DIR / source_name
        if not source.is_file():
            raise FileNotFoundError(f"Required source image is missing: {source}")

        original_total += source.stat().st_size
        with Image.open(source) as opened:
            image = ImageOps.exif_transpose(opened)
            has_alpha = image.mode in {"RGBA", "LA"} or "transparency" in image.info
            image = image.convert("RGBA" if has_alpha else "RGB")

            for output_name, max_width, quality in variants:
                variant = image.copy()
                if variant.width > max_width:
                    height = max(1, round(variant.height * max_width / variant.width))
                    variant = variant.resize(
                        (max_width, height),
                        Image.Resampling.LANCZOS,
                    )
                destination = OUTPUT_DIR / output_name
                variant.save(
                    destination,
                    format="WEBP",
                    quality=quality,
                    method=6,
                    lossless=False,
                    alpha_quality=90,
                )
                size = destination.stat().st_size
                optimized_total += size
                print(
                    f"{source_name} -> optimized/{output_name}: "
                    f"{size / 1024:.1f} KiB ({variant.width}x{variant.height})"
                )

    if original_total:
        savings = max(0.0, 1 - optimized_total / original_total) * 100
        print(
            f"\nOriginal source total: {original_total / 1024:.1f} KiB"
            f"\nGenerated variants total: {optimized_total / 1024:.1f} KiB"
            f"\nCombined size reduction across generated variants: {savings:.1f}%"
        )


if __name__ == "__main__":
    main()
