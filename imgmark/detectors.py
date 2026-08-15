"""Deterministic UI-region detection backends.

This module deliberately has no dependency on the annotation layer. The
heuristic backend identifies contiguous, visually distinct regions; it does not
claim to understand text or semantics. Model/OCR backends can implement the
same ``detect_ui_elements`` return contract later.
"""

from __future__ import annotations

from collections import Counter, deque
from pathlib import Path
from typing import Any

from PIL import Image

from .colors import parse_color
from .annotator import SUPPORTED_INPUT_FORMATS


def _dominant_background(image: Image.Image) -> tuple[int, int, int]:
    """Use 16-level RGB buckets so near-identical background pixels agree."""
    samples = []
    for y in range(0, image.height, max(1, image.height // 300)):
        for x in range(0, image.width, max(1, image.width // 300)):
            r, g, b, _ = image.getpixel((x, y))
            samples.append((r // 16, g // 16, b // 16))
    bucket = Counter(samples).most_common(1)[0][0]
    return tuple(value * 16 + 8 for value in bucket)


def _distance(pixel: tuple[int, int, int, int], background: tuple[int, int, int]) -> int:
    return max(abs(pixel[i] - background[i]) for i in range(3))


def detect_ui_elements(
    input_path: str | Path,
    *,
    background: str | None = None,
    color_threshold: int = 28,
    min_area: int = 100,
    min_width: int = 8,
    min_height: int = 8,
    padding: int = 0,
) -> dict[str, Any]:
    """Return bounding boxes for contiguous regions distinct from background.

    Coordinates use half-open bounds: x1/y1 are inclusive and x2/y2 are one
    pixel beyond the element. This makes width exactly ``x2 - x1``.
    """
    if color_threshold < 0 or min_area <= 0 or min_width <= 0 or min_height <= 0 or padding < 0:
        raise ValueError("threshold and minimum dimensions must be positive")
    path = Path(input_path)
    if not path.is_file():
        raise FileNotFoundError(f"input image does not exist: {path}")
    with Image.open(path) as source:
        if source.format not in SUPPORTED_INPUT_FORMATS:
            raise ValueError(f"unsupported input format: {source.format}")
        image = source.convert("RGBA")
    bg_rgba = parse_color(background) if background else (*_dominant_background(image), 255)
    bg = bg_rgba[:3]
    width, height = image.size
    foreground = bytearray(width * height)
    pixels = image.load()
    for y in range(height):
        offset = y * width
        for x in range(width):
            foreground[offset + x] = _distance(pixels[x, y], bg) > color_threshold

    seen = bytearray(width * height)
    elements: list[dict[str, Any]] = []
    for start in range(width * height):
        if not foreground[start] or seen[start]:
            continue
        queue = deque([start]); seen[start] = 1
        count = 0; min_x = max_x = start % width; min_y = max_y = start // width
        while queue:
            current = queue.popleft(); x, y = current % width, current // width; count += 1
            min_x, max_x, min_y, max_y = min(min_x, x), max(max_x, x), min(min_y, y), max(max_y, y)
            for ny in range(max(0, y - 1), min(height, y + 2)):
                for nx in range(max(0, x - 1), min(width, x + 2)):
                    candidate = ny * width + nx
                    if foreground[candidate] and not seen[candidate]:
                        seen[candidate] = 1; queue.append(candidate)
        x2, y2 = max_x + 1, max_y + 1
        if count >= min_area and x2 - min_x >= min_width and y2 - min_y >= min_height:
            padded_x1, padded_y1 = max(0, min_x - padding), max(0, min_y - padding)
            padded_x2, padded_y2 = min(width, x2 + padding), min(height, y2 + padding)
            elements.append({"type": "region", "bbox": {"x1": padded_x1, "y1": padded_y1, "x2": padded_x2, "y2": padded_y2}, "width": padded_x2 - padded_x1, "height": padded_y2 - padded_y1, "area": count, "center": {"x": (padded_x1 + padded_x2) / 2, "y": (padded_y1 + padded_y2) / 2}, "confidence": 0.5})
    elements.sort(key=lambda element: (element["bbox"]["y1"], element["bbox"]["x1"]))
    for identifier, element in enumerate(elements, 1):
        element["id"] = identifier
    return {"success": True, "input": str(path), "detector": "heuristic-ui", "coordinate_system": "pixel", "bbox_convention": "x1/y1 inclusive; x2/y2 exclusive", "image": {"width": width, "height": height}, "parameters": {"background": background or "auto", "color_threshold": color_threshold, "min_area": min_area, "min_width": min_width, "min_height": min_height, "padding": padding}, "objects": elements}
