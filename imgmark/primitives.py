"""Pillow drawing primitives. Each function draws onto an RGBA image."""

from __future__ import annotations

from PIL import ImageDraw, ImageFont

from .colors import parse_color
from .utils import arrow_head


def _draw(image): return ImageDraw.Draw(image, "RGBA")
def _box(op): return (op["x1"], op["y1"], op["x2"], op["y2"])
def _font(size):
    try: return ImageFont.truetype("DejaVuSans.ttf", int(size))
    except OSError: return ImageFont.load_default()

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
    d, font = _draw(image), _font(op.get("size", 24)); x, y = op["x"], op["y"]
    if op.get("background"):
        padding = op.get("padding", 5); box = d.textbbox((x, y), op["text"], font=font)
        d.rectangle((box[0]-padding, box[1]-padding, box[2]+padding, box[3]+padding), fill=parse_color(op["background"]))
    d.text((x, y), op["text"], fill=parse_color(op["color"]), font=font)
def focus(image, op):
    """Darken all pixels outside the supplied rectangle."""
    overlay = image.copy(); d = _draw(overlay); alpha = round(255 * op.get("opacity", .65))
    d.rectangle((0, 0, image.width, image.height), fill=(0, 0, 0, alpha))
    d.rectangle(_box(op), fill=(0, 0, 0, 0))
    image.alpha_composite(overlay)

DRAWERS = {"rectangle": rectangle, "circle": circle, "ellipse": ellipse, "line": line, "arrow": arrow, "point": point, "marker": marker, "polygon": polygon, "text": text, "focus": focus}
