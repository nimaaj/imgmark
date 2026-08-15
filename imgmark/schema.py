"""Validation of the stable JSON operation schema."""

from __future__ import annotations

from numbers import Real
from typing import Any

from .colors import parse_color
from .utils import DEFAULT_ARROW_HEAD_LENGTH, DEFAULT_ARROW_HEAD_WIDTH, DEFAULT_COLOR, DEFAULT_FONT_SIZE, DEFAULT_LINE_WIDTH, DEFAULT_POINT_RADIUS

OPERATION_TYPES = {"rectangle", "circle", "ellipse", "line", "arrow", "point", "marker", "polygon", "text", "focus"}


class OperationError(ValueError):
    def __init__(self, message: str, operation: int | None = None, code: str = "invalid_operation"):
        super().__init__(message)
        self.operation, self.code = operation, code


def _number(op: dict[str, Any], key: str, index: int) -> float:
    value = op.get(key)
    if not isinstance(value, Real) or isinstance(value, bool):
        raise OperationError(f"{key} must be numeric", index)
    return float(value)


def _positive(op: dict[str, Any], key: str, index: int, default: int | None = None) -> float:
    value = default if key not in op else _number(op, key, index)
    if value is None or value <= 0:
        raise OperationError(f"{key} must be positive", index)
    return value


def validate_operation(raw: Any, index: int) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise OperationError("operation must be an object", index)
    op = dict(raw)
    kind = op.get("type")
    if kind not in OPERATION_TYPES:
        raise OperationError(f"unknown operation type: {kind!r}", index, "unknown_operation")
    if kind in {"rectangle", "ellipse", "line", "arrow"}:
        for key in ("x1", "y1", "x2", "y2"):
            _number(op, key, index)
    if kind == "circle":
        _number(op, "cx", index); _number(op, "cy", index); _positive(op, "radius", index)
    if kind in {"point", "marker", "text"}:
        _number(op, "x", index); _number(op, "y", index)
    if kind == "polygon":
        points = op.get("points")
        if not isinstance(points, list) or len(points) < 3:
            raise OperationError("polygon points must contain at least three points", index)
        for point in points:
            if not isinstance(point, list) or len(point) != 2 or not all(isinstance(v, Real) and not isinstance(v, bool) for v in point):
                raise OperationError("each polygon point must be [x, y]", index)
    if kind == "text" and not isinstance(op.get("text"), str):
        raise OperationError("text must be a string", index)
    if kind == "marker" and op.get("style", "dot") not in {"dot", "cross", "x"}:
        raise OperationError("marker style must be dot, cross, or x", index)
    if kind == "focus":
        for key in ("x1", "y1", "x2", "y2"): _number(op, key, index)
        opacity = op.get("opacity", 0.65)
        if not isinstance(opacity, Real) or not 0 <= opacity <= 1: raise OperationError("opacity must be between 0 and 1", index)
    if kind not in {"focus"}:
        for key in ("color", "fill", "background"):
            if key in op:
                try: parse_color(op[key])
                except ValueError as exc: raise OperationError(str(exc), index, "invalid_color") from exc
    if kind in {"rectangle", "circle", "ellipse", "line", "arrow", "polygon"}: _positive(op, "width", index, DEFAULT_LINE_WIDTH)
    if kind == "arrow": _positive(op, "head_length", index, DEFAULT_ARROW_HEAD_LENGTH); _positive(op, "head_width", index, DEFAULT_ARROW_HEAD_WIDTH)
    if kind == "point": _positive(op, "radius", index, DEFAULT_POINT_RADIUS)
    if kind == "marker": _positive(op, "size", index, 15)
    if kind == "text": _positive(op, "size", index, DEFAULT_FONT_SIZE); _positive(op, "padding", index, 5) if "padding" in op else None
    op.setdefault("color", DEFAULT_COLOR)
    return op


def validate_operations(data: Any) -> list[dict[str, Any]]:
    operations = data.get("operations") if isinstance(data, dict) else None
    if not isinstance(operations, list):
        raise OperationError("JSON document must contain an operations array", code="invalid_document")
    return [validate_operation(operation, i + 1) for i, operation in enumerate(operations)]
