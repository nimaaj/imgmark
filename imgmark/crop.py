"""Explicit, deterministic image cropping independent of annotations."""

from __future__ import annotations

from pathlib import Path
from numbers import Real
from typing import Any

from PIL import Image

from .annotator import SUPPORTED_INPUT_FORMATS


def crop_image(
    input_path: str | Path,
    output_path: str | Path,
    *,
    x1: int | float,
    y1: int | float,
    x2: int | float,
    y2: int | float,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Crop an image using half-open pixel bounds and save it as a PNG.

    Bounds are deliberately not clamped: callers receive a clear error rather
    than an output whose geometry differs from the request.
    """
    values = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
    if any(not isinstance(value, Real) or isinstance(value, bool) or int(value) != value for value in values.values()):
        raise ValueError("crop coordinates must be integer pixel values")
    x1, y1, x2, y2 = (int(values[key]) for key in ("x1", "y1", "x2", "y2"))
    if x2 <= x1 or y2 <= y1:
        raise ValueError("crop bounds require x2 > x1 and y2 > y1")
    source_path, destination = Path(input_path), Path(output_path)
    if not source_path.is_file():
        raise FileNotFoundError(f"input image does not exist: {source_path}")
    if destination.exists() and not overwrite:
        raise FileExistsError(f"output already exists: {destination}; use --overwrite")
    if destination.suffix.lower() != ".png":
        raise ValueError("v0.1 supports PNG output only")
    with Image.open(source_path) as source:
        if source.format not in SUPPORTED_INPUT_FORMATS:
            raise ValueError(f"unsupported input format: {source.format}")
        width, height = source.size
        if x1 < 0 or y1 < 0 or x2 > width or y2 > height:
            raise ValueError(f"crop bounds [{x1}, {y1}, {x2}, {y2}] are outside image dimensions {width}x{height}")
        source.convert("RGBA").crop((x1, y1, x2, y2)).save(destination, format="PNG")
    return {"success": True, "input": str(source_path), "output": str(destination), "crop": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}, "width": x2 - x1, "height": y2 - y1}
