"""Pillow drawing primitives. Each function draws onto an RGBA image.

A drawer may return a list of warning dicts (see `text`); returning None means
"nothing to report". ImageAnnotator stamps the operation index onto whatever
comes back.
"""

from __future__ import annotations

import os

import PIL
from PIL import ImageDraw, ImageFont

from .colors import parse_color
from .utils import arrow_head

# Scalable fonts to try, in order, for `text` labels. The bare "DejaVuSans.ttf"
# stays first for backwards compatibility: Pillow resolves a bare filename
# against the working directory and a few system font dirs, so anyone who
# dropped that file next to their script keeps the font they had.
_FONT_CANDIDATES = (
    "DejaVuSans.ttf",
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    # macOS
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/SFNS.ttf",
    "/System/Library/Fonts/Geneva.ttf",
    # Windows
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",
)

_UNRESOLVED = object()
_font_path = _UNRESOLVED  # cached across calls; None means "nothing found"


def font_path():
    """Path of the first usable scalable font, or None if there is none.

    $IMGMARK_FONT overrides the search entirely. Result is cached, so a font
    installed mid-process is not picked up (call `reset_font_cache` in tests).
    """
    global _font_path
    if _font_path is not _UNRESOLVED:
        return _font_path

    override = os.environ.get("IMGMARK_FONT")
    candidates = (override,) + _FONT_CANDIDATES if override else _FONT_CANDIDATES
    for candidate in candidates:
        try:
            ImageFont.truetype(candidate, 12)
        except (OSError, ValueError):
            continue
        _font_path = candidate
        return _font_path

    _font_path = None
    return _font_path


def reset_font_cache():
    """Forget the resolved font path. Exposed for tests."""
    global _font_path
    _font_path = _UNRESOLVED


def _draw(image): return ImageDraw.Draw(image, "RGBA")
def _box(op): return (op["x1"], op["y1"], op["x2"], op["y2"])


def _font(size):
    """Return (font, warnings) for `size`, never silently ignoring the size.

    The old implementation asked Pillow for "DejaVuSans.ttf" and fell back to
    `ImageFont.load_default()` on failure. That default is a fixed ~11px bitmap
    font which ignores `size` entirely, so on any machine without DejaVu (a
    stock macOS or Windows install) every label rendered tiny with no error.
    """
    size = int(size)
    path = font_path()
    if path is not None:
        try:
            return ImageFont.truetype(path, size), []
        except (OSError, ValueError):
            pass  # disappeared or unreadable since resolution; fall through

    # Pillow >= 10.1 scales its bundled fallback face when given a size.
    try:
        return ImageFont.load_default(size=size), [{
            "type": "font_fallback",
            "detail": (
                "no system font found; using Pillow's bundled default at "
                f"size {size}. Set $IMGMARK_FONT to a .ttf/.otf for a "
                "specific typeface."
            ),
        }]
    except TypeError:
        pass

    return ImageFont.load_default(), [{
        "type": "font_size_ignored",
        "detail": (
            f"no system font found and Pillow {PIL.__version__} cannot scale its "
            f"default font, so size {size} was ignored and the label rendered at "
            "roughly 11px. Set $IMGMARK_FONT to a .ttf/.otf, or upgrade to "
            "Pillow >= 10.1."
        ),
    }]

def rectangle(image, op): _draw(image).rectangle(_box(op), outline=parse_color(op["color"]), fill=parse_color(op["fill"]) if op.get("fill") else None, width=int(op.get("width", 3)))
def ellipse(image, op): _draw(image).ellipse(_box(op), outline=parse_color(op["color"]), fill=parse_color(op["fill"]) if op.get("fill") else None, width=int(op.get("width", 3)))
def circle(image, op):
    r = op["radius"]; ellipse(image, {**op, "x1": op["cx"] - r, "y1": op["cy"] - r, "x2": op["cx"] + r, "y2": op["cy"] + r})
def line(image, op): _draw(image).line((op["x1"], op["y1"], op["x2"], op["y2"]), fill=parse_color(op["color"]), width=int(op.get("width", 3)))
def arrow(image, op):
    line(image, op)
    head = arrow_head((op["x1"], op["y1"]), (op["x2"], op["y2"]), op.get("head_length", 18), op.get("head_width", 12))
    _draw(image).polygon(head, fill=parse_color(op["color"]))
def point(image, op):
    r = op.get("radius", 6); x, y = op["x"], op["y"]
    _draw(image).ellipse((x-r, y-r, x+r, y+r), fill=parse_color(op["color"]))
def marker(image, op):
    style, size, x, y, color = op.get("style", "dot"), op.get("size", 15), op["x"], op["y"], parse_color(op["color"])
    if style == "dot": point(image, {**op, "radius": size / 2}); return
    d = _draw(image); half = size / 2
    if style == "cross": d.line((x-half, y, x+half, y), fill=color, width=2); d.line((x, y-half, x, y+half), fill=color, width=2)
    else: d.line((x-half, y-half, x+half, y+half), fill=color, width=2); d.line((x-half, y+half, x+half, y-half), fill=color, width=2)
def polygon(image, op): _draw(image).polygon(op["points"], fill=parse_color(op["fill"]) if op.get("fill") else None, outline=parse_color(op["color"]), width=int(op.get("width", 3)))
def text(image, op):
    d = _draw(image); font, notes = _font(op.get("size", 24)); x, y = op["x"], op["y"]
    if op.get("background"):
        padding = op.get("padding", 5); box = d.textbbox((x, y), op["text"], font=font)
        d.rectangle((box[0]-padding, box[1]-padding, box[2]+padding, box[3]+padding), fill=parse_color(op["background"]))
    d.text((x, y), op["text"], fill=parse_color(op["color"]), font=font)
    return notes
def focus(image, op):
    """Darken all pixels outside the supplied rectangle."""
    overlay = image.copy(); d = _draw(overlay); alpha = round(255 * op.get("opacity", .65))
    d.rectangle((0, 0, image.width, image.height), fill=(0, 0, 0, alpha))
    d.rectangle(_box(op), fill=(0, 0, 0, 0))
    image.alpha_composite(overlay)

DRAWERS = {"rectangle": rectangle, "circle": circle, "ellipse": ellipse, "line": line, "arrow": arrow, "point": point, "marker": marker, "polygon": polygon, "text": text, "focus": focus}
