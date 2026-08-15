"""Geometry and default values."""

from __future__ import annotations

import math

DEFAULT_COLOR = "red"
DEFAULT_LINE_WIDTH = 3
DEFAULT_FONT_SIZE = 24
DEFAULT_POINT_RADIUS = 6
DEFAULT_ARROW_HEAD_LENGTH = 18
DEFAULT_ARROW_HEAD_WIDTH = 12


def arrow_head(start: tuple[float, float], end: tuple[float, float], length: float, width: float) -> list[tuple[float, float]]:
    """Return a triangular arrowhead whose tip is *end*."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    magnitude = math.hypot(dx, dy)
    if magnitude == 0:
        return [end, end, end]
    ux, uy = dx / magnitude, dy / magnitude
    base_x, base_y = end[0] - length * ux, end[1] - length * uy
    px, py = -uy * width / 2, ux * width / 2
    return [end, (base_x + px, base_y + py), (base_x - px, base_y - py)]
