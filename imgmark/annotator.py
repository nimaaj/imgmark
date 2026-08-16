"""ImageAnnotator, independent from command-line concerns."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from PIL import Image
from .primitives import DRAWERS
from .schema import validate_operation

SUPPORTED_INPUT_FORMATS = {"PNG", "JPEG", "WEBP"}

class ImageAnnotator:
    def __init__(self, input_path: str | Path):
        self.input_path = Path(input_path)
        if not self.input_path.is_file(): raise FileNotFoundError(f"input image does not exist: {self.input_path}")
        with Image.open(self.input_path) as source:
            if source.format not in SUPPORTED_INPUT_FORMATS: raise ValueError(f"unsupported input format: {source.format}")
            self.format = source.format
            self.image = source.convert("RGBA")
        self.warnings: list[dict[str, Any]] = []
        self.operations_applied = 0

    @property
    def size(self): return self.image.size
    def apply(self, operation: dict[str, Any]) -> "ImageAnnotator":
        op = validate_operation(operation, self.operations_applied + 1)
        index = self.operations_applied + 1
        self._warn_bounds(op, index)
        # A drawer may return warning dicts (e.g. text falling back to a font
        # that cannot honour `size`); None means nothing to report.
        notes = DRAWERS[op["type"]](self.image, op)
        for note in notes or []: self.warnings.append({"operation": index, **note})
        self.operations_applied += 1
        return self
    def apply_all(self, operations: list[dict[str, Any]]) -> "ImageAnnotator":
        for op in operations: self.apply(op)
        return self
    def _warn_bounds(self, op, index):
        coordinates = []
        endpoints = [(op[key], op[key.replace("x", "y", 1)]) for key in ("x1", "x2") if key in op]
        positions = [(op["x"], op["y"])] if "x" in op else []
        centers = [(op["cx"], op["cy"])] if "cx" in op else []
        for x, y in endpoints + positions + centers + [tuple(p) for p in op.get("points", [])]:
            if x < 0 or y < 0 or x >= self.image.width or y >= self.image.height: coordinates.append([x, y])
        for coordinate in coordinates: self.warnings.append({"operation": index, "type": "coordinate_out_of_bounds", "coordinate": coordinate})
    def save(self, output_path: str | Path, overwrite: bool = False) -> None:
        output = Path(output_path)
        if output.exists() and not overwrite: raise FileExistsError(f"output already exists: {output}; use --overwrite")
        if output.suffix.lower() != ".png": raise ValueError("v0.1 supports PNG output only")
        self.image.save(output, format="PNG")

def _method(kind):
    def draw(self, *args, **kwargs):
        keys = {"rectangle": ("x1", "y1", "x2", "y2"), "circle": ("cx", "cy", "radius"), "ellipse": ("x1", "y1", "x2", "y2"), "line": ("x1", "y1", "x2", "y2"), "arrow": ("x1", "y1", "x2", "y2"), "point": ("x", "y"), "marker": ("x", "y"), "text": ("x", "y", "text")}[kind]
        if len(args) > len(keys): raise TypeError(f"{kind} accepts at most {len(keys)} positional arguments")
        return self.apply({"type": kind, **dict(zip(keys, args)), **kwargs})
    return draw
for _kind in ("rectangle", "circle", "ellipse", "line", "arrow", "point", "marker", "text"):
    setattr(ImageAnnotator, _kind, _method(_kind))
