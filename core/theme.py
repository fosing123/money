import colorsys
import re
from functools import lru_cache

from django.conf import settings


HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})")

PRESETS = {
    "violet": {"primary": "#7651F5", "accent": "#16C9D5", "background": "#F7F5FC", "surface": "#FFFFFF", "text": "#211A3B", "muted": "#817A98", "border": "#EAE5F4"},
    "mint": {"primary": "#0B8967", "accent": "#F1B85B", "background": "#F3F8F5", "surface": "#FFFFFF", "text": "#182D26", "muted": "#71847B", "border": "#E1ECE6"},
    "ocean": {"primary": "#256E9B", "accent": "#36BCD0", "background": "#F2F7FA", "surface": "#FFFFFF", "text": "#1B2D3A", "muted": "#71828D", "border": "#DFEAF0"},
    "sunset": {"primary": "#A75C43", "accent": "#E6A64D", "background": "#FBF5F1", "surface": "#FFFFFF", "text": "#34251F", "muted": "#8A766D", "border": "#EFE3DB"},
    "midnight": {"primary": "#9A83FF", "accent": "#27D0D3", "background": "#11111B", "surface": "#1C1B2A", "text": "#F2F0FF", "muted": "#AAA5C3", "border": "#363348"},
}
DEFAULT_PALETTE = PRESETS["violet"]
CUSTOM_KEYS = ("primary", "accent", "background", "surface", "text", "muted", "border")
HEX_VALUE_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _hex_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))


def _rgb_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*(max(0, min(255, round(channel))) for channel in rgb))


def _mix(first, second, amount):
    a, b = _hex_rgb(first), _hex_rgb(second)
    amount = max(0.0, min(1.0, amount))
    return _rgb_hex(tuple(x * (1 - amount) + y * amount for x, y in zip(a, b)))


def _darken(value, amount=0.22):
    red, green, blue = _hex_rgb(value)
    hue, lightness, saturation = colorsys.rgb_to_hls(red / 255, green / 255, blue / 255)
    lightness = max(0.10, lightness * (1 - amount))
    return _rgb_hex(tuple(component * 255 for component in colorsys.hls_to_rgb(hue, lightness, saturation)))


def _normalise_palette(theme, custom):
    base = PRESETS.get(theme, DEFAULT_PALETTE).copy()
    if theme == "custom" and isinstance(custom, dict):
        for key in CUSTOM_KEYS:
            candidate = custom.get(key)
            if isinstance(candidate, str) and HEX_VALUE_RE.fullmatch(candidate):
                base[key] = candidate.upper()
    primary, background, surface = base["primary"], base["background"], base["surface"]
    base.update({
        "primary_dark": _darken(primary, 0.27),
        "primary_soft": _mix(background, primary, 0.11),
        "surface_soft": _mix(background, surface, 0.55),
        "success": "#208D69",
        "danger": "#D94F68",
        "warning": "#C8872E",
        "focus": _mix(primary, "#FFFFFF", 0.30),
    })
    return base


def _unpack_hex(value):
    raw = value.lstrip("#")
    if len(raw) in (3, 4):
        raw = "".join(character * 2 for character in raw)
    if len(raw) == 6:
        raw += "FF"
    return tuple(int(raw[index:index + 2], 16) for index in (0, 2, 4)), int(raw[6:8], 16) / 255


def _source_colour(value, palette):
    rgb, alpha = _unpack_hex(value)
    red, green, blue = (channel / 255 for channel in rgb)
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
    original = _rgb_hex(rgb)

    # Keep soft shadow overlays and the app's semantic gold/red accents intact.
    if alpha < 0.42 and saturation < 0.2:
        mapped = original
    elif saturation < 0.18:
        if lightness >= 0.93:
            mapped = palette["surface"]
        elif lightness >= 0.80:
            mapped = _mix(palette["surface"], palette["background"], (0.93 - lightness) / 0.13 * 0.72)
        elif lightness >= 0.64:
            mapped = _mix(palette["muted"], palette["surface"], (lightness - 0.64) / 0.16 * 0.24)
        elif lightness >= 0.32:
            mapped = _mix(palette["text"], palette["muted"], (lightness - 0.32) / 0.32)
        else:
            mapped = _mix(palette["text"], palette["primary_dark"], 0.22)
    elif hue <= 0.035 or hue >= 0.965:
        mapped = palette["danger"]
    elif 0.07 <= hue <= 0.18:
        mapped = original
    else:
        chosen = palette["accent"] if 0.43 <= hue <= 0.73 else palette["primary"]
        chosen_hue, _, chosen_saturation = colorsys.rgb_to_hls(*(channel / 255 for channel in _hex_rgb(chosen)))
        mapped_saturation = max(0.28, min(0.94, saturation * (0.68 + chosen_saturation * 0.38)))
        mapped_lightness = max(0.12, min(0.91, lightness))
        mapped = _rgb_hex(tuple(component * 255 for component in colorsys.hls_to_rgb(chosen_hue, mapped_lightness, mapped_saturation)))

    if alpha < 0.999:
        return "rgba({}, {}, {}, {:.3f})".format(*_hex_rgb(mapped), alpha)
    return mapped


@lru_cache(maxsize=1)
def _source_colours():
    colours = set()
    sources = [
        settings.BASE_DIR / "static" / "nkem" / "app.css",
        settings.BASE_DIR / "static" / "nkem" / "theme.css",
    ]
    for source in sources:
        try:
            colours.update(match.lower() for match in HEX_RE.findall(source.read_text(encoding="utf-8")))
        except OSError:
            continue
    return tuple(sorted(colours))


def build_theme_variables(user=None):
    authenticated = bool(getattr(user, "is_authenticated", False))
    theme = getattr(user, "theme", "violet") if authenticated else "violet"
    custom = getattr(user, "custom_palette", {}) if authenticated else {}
    palette = _normalise_palette(theme, custom or {})
    _, background_lightness, _ = colorsys.rgb_to_hls(*(channel / 255 for channel in _hex_rgb(palette["background"])))
    variables = {
        "brand-primary": palette["primary"],
        "brand-dark": palette["primary_dark"],
        "brand-soft": palette["primary_soft"],
        "brand-accent": palette["accent"],
        "bg": palette["background"],
        "surface": palette["surface"],
        "surface-soft": palette["surface_soft"],
        "text": palette["text"],
        "muted": palette["muted"],
        "line": palette["border"],
        "success": palette["success"],
        "danger": palette["danger"],
        "warning": palette["warning"],
        "focus-ring": palette["focus"],
        "ui-color-scheme": "dark" if background_lightness < 0.42 else "light",
        "shadow": "0 16px 45px rgba(25, 20, 55, .075)",
        "shadow-sm": "0 7px 24px rgba(25, 20, 55, .06)",
    }
    for colour in _source_colours():
        variables[f"paint-{colour[1:]}"] = _source_colour(colour, palette)
    return variables
