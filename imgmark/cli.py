"""CLI entry point for imgmark."""

from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from PIL import Image
from .annotator import ImageAnnotator, SUPPORTED_INPUT_FORMATS
from .schema import OperationError, validate_operations
from .detectors import detect_ui_elements
from .crop import crop_image

def _emit(payload, as_json):
    if as_json: print(json.dumps(payload, sort_keys=True))
    else: print(payload.get("message") or json.dumps(payload, indent=2))

def _info(path, as_json):
    with Image.open(path) as image:
        if image.format not in SUPPORTED_INPUT_FORMATS: raise ValueError(f"unsupported input format: {image.format}")
        result = {"path": str(path), "width": image.width, "height": image.height, "mode": image.mode, "format": image.format}
    _emit(result, as_json)

def _annotate(args):
    with open(args.ops, encoding="utf-8") as stream: operations = validate_operations(json.load(stream))
    annotator = ImageAnnotator(args.input)
    annotator.apply_all(operations); annotator.save(args.output, args.overwrite)
    result = {"success": True, "input": str(args.input), "output": str(args.output), "width": annotator.image.width, "height": annotator.image.height, "operations_applied": annotator.operations_applied}
    if annotator.warnings: result["warnings"] = annotator.warnings
    _emit(result, args.json)

def _legacy(args):
    selected = next(name for name in ("rectangle", "circle", "ellipse", "line", "arrow", "point", "marker", "polygon", "focus", "text") if getattr(args, name) is not None)
    values = getattr(args, selected)
    op = {"type": selected, "color": args.color, "width": args.width}
    if selected in {"rectangle", "ellipse", "line", "arrow", "focus"}:
        op.update(dict(zip(("x1", "y1", "x2", "y2"), values)))
    elif selected == "circle": op.update(dict(zip(("cx", "cy", "radius"), values)))
    elif selected in {"point", "marker"}: op.update(dict(zip(("x", "y"), values)))
    elif selected == "polygon": op["points"] = json.loads(values)
    if args.text is not None:
        op.update({"type": "text", "x": args.x, "y": args.y, "text": args.text, "size": args.size})
        if args.background: op["background"] = args.background
    else:
        if args.fill: op["fill"] = args.fill
        if selected == "arrow": op.update({"head_length": args.head_length, "head_width": args.head_width})
        if selected == "marker": op.update({"style": args.style, "size": args.size})
        if selected == "point": op["radius"] = args.radius
        if selected == "focus": op["opacity"] = args.opacity
    annotator = ImageAnnotator(args.input); annotator.apply(op); annotator.save(args.output, args.overwrite)
    _emit({"success": True, "input": args.input, "output": args.output, "width": annotator.image.width, "height": annotator.image.height, "operations_applied": 1, **({"warnings": annotator.warnings} if annotator.warnings else {})}, args.json)

def _detect(args):
    if args.detector != "heuristic-ui":
        raise ValueError(f"unsupported detector: {args.detector}")
    result = detect_ui_elements(args.input, background=args.background, color_threshold=args.color_threshold, min_area=args.min_area, min_width=args.min_width, min_height=args.min_height, padding=args.padding)
    _emit(result, args.json)

def _crop(args):
    result = crop_image(args.input, args.output, x1=args.x1, y1=args.y1, x2=args.x2, y2=args.y2, overwrite=args.overwrite)
    _emit(result, args.json)

def build_parser():
    parser = argparse.ArgumentParser(prog="imgmark", description="Deterministic image annotation utility")
    sub = parser.add_subparsers(dest="command")
    info = sub.add_parser("info"); info.add_argument("input"); info.add_argument("--json", action="store_true")
    ann = sub.add_parser("annotate"); ann.add_argument("input"); ann.add_argument("--ops", required=True); ann.add_argument("--output", required=True); ann.add_argument("--overwrite", action="store_true"); ann.add_argument("--json", action="store_true")
    detect = sub.add_parser("detect", help="detect visually distinct UI regions")
    detect.add_argument("input"); detect.add_argument("--detector", default="heuristic-ui", choices=["heuristic-ui"])
    detect.add_argument("--background", help="background color, e.g. #ffffff; default auto-detect")
    detect.add_argument("--color-threshold", type=int, default=28)
    detect.add_argument("--min-area", type=int, default=100); detect.add_argument("--min-width", type=int, default=8); detect.add_argument("--min-height", type=int, default=8); detect.add_argument("--padding", type=int, default=0, help="expand returned boxes by this many pixels")
    detect.add_argument("--json", action="store_true")
    crop = sub.add_parser("crop", help="crop an image using explicit pixel bounds")
    crop.add_argument("input"); crop.add_argument("--x1", type=int, required=True); crop.add_argument("--y1", type=int, required=True)
    crop.add_argument("--x2", type=int, required=True); crop.add_argument("--y2", type=int, required=True)
    crop.add_argument("--output", required=True); crop.add_argument("--overwrite", action="store_true"); crop.add_argument("--json", action="store_true")
    return parser

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    # Convenient single-operation form: imgmark image.png --circle ...
    if argv and argv[0] not in {"info", "annotate", "detect", "crop", "-h", "--help"}:
        legacy = argparse.ArgumentParser(prog="imgmark")
        legacy.add_argument("input")
        choices = legacy.add_mutually_exclusive_group(required=True)
        choices.add_argument("--rectangle", nargs=4, type=float); choices.add_argument("--circle", nargs=3, type=float); choices.add_argument("--ellipse", nargs=4, type=float); choices.add_argument("--line", nargs=4, type=float); choices.add_argument("--arrow", nargs=4, type=float); choices.add_argument("--point", nargs=2, type=float); choices.add_argument("--marker", nargs=2, type=float); choices.add_argument("--polygon", help="JSON array of [x, y] pairs"); choices.add_argument("--focus", nargs=4, type=float); choices.add_argument("--text", help="text to draw; requires --x and --y")
        legacy.add_argument("--x", type=float); legacy.add_argument("--y", type=float); legacy.add_argument("--color", default="red"); legacy.add_argument("--width", type=float, default=3); legacy.add_argument("--fill"); legacy.add_argument("--background"); legacy.add_argument("--size", type=float, default=24); legacy.add_argument("--radius", type=float, default=6); legacy.add_argument("--style", default="dot"); legacy.add_argument("--head-length", type=float, default=18); legacy.add_argument("--head-width", type=float, default=12); legacy.add_argument("--opacity", type=float, default=.65); legacy.add_argument("--output", required=True); legacy.add_argument("--overwrite", action="store_true"); legacy.add_argument("--json", action="store_true")
        args = legacy.parse_args(argv)
        if args.text is not None and (args.x is None or args.y is None): legacy.error("--text requires --x and --y")
        try: _legacy(args); return 0
        except Exception as exc: _emit_error(exc, args.json); return 1
    args = parser.parse_args(argv)
    if not args.command: parser.print_help(); return 2
    try:
        if args.command == "info": _info(args.input, args.json)
        elif args.command == "detect": _detect(args)
        elif args.command == "crop": _crop(args)
        else: _annotate(args)
        return 0
    except Exception as exc: _emit_error(exc, getattr(args, "json", False)); return 1

def _emit_error(exc, as_json):
    data = {"success": False, "error": getattr(exc, "code", "error"), "message": str(exc)}
    if isinstance(exc, OperationError) and exc.operation is not None: data["operation"] = exc.operation
    if as_json: print(json.dumps(data, sort_keys=True))
    else: print(f"error: {exc}", file=sys.stderr)

if __name__ == "__main__": raise SystemExit(main())
