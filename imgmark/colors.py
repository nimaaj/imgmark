"""Stable color parsing used by all drawing primitives."""

from __future__ import annotations

import re

NAMED_COLORS: dict[str, tuple[int, int, int, int]] = {
    "red": (255, 0, 0, 255), "green": (0, 128, 0, 255),
    "blue": (0, 0, 255, 255), "yellow": (255, 255, 0, 255),
    "orange": (255, 165, 0, 255), "purple": (128, 0, 128, 255),
    "cyan": (0, 255, 255, 255), "magenta": (255, 0, 255, 255),
    "white": (255, 255, 255, 255), "black": (0, 0, 0, 255),
    "gray": (128, 128, 128, 255), "grey": (128, 128, 128, 255),
}
_HEX = re.compile(r"^#(?P<value>[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
_RGBA = re.compile(r"^rgba\((\d+),(\d+),(\d+),(?:\s*)?([01](?:\.\d+)?)\)$")


def parse_color(value: str | tuple[int, ...] | list[int]) -> tuple[int, int, int, int]:
    """Return an RGBA color, raising ValueError for unsupported values."""
    if isinstance(value, (tuple, list)):
        if len(value) not in (3, 4) or any(not isinstance(v, int) or not 0 <= v <= 255 for v in value):
            raise ValueError(f"invalid color: {value!r}")
        return tuple(value) + (255,) if len(value) == 3 else tuple(value)  # type: ignore[return-value]
    if not isinstance(value, str):
        raise ValueError(f"invalid color: {value!r}")
    if value.lower() in NAMED_COLORS:
        return NAMED_COLORS[value.lower()]
    match = _HEX.match(value)
    if match:
        raw = match.group("value")
        return tuple(int(raw[i:i + 2], 16) for i in range(0, len(raw), 2)) + (() if len(raw) == 8 else (255,))  # type: ignore[return-value]
    match = _RGBA.match(value.replace(" ", ""))
    if match:
        r, g, b, alpha = match.groups()
        values = [int(r), int(g), int(b)]
        if any(v > 255 for v in values):
            raise ValueError(f"invalid color: {value!r}")
        return (*values, round(float(alpha) * 255))
    raise ValueError(f"invalid color: {value!r}")
