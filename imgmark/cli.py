"""CLI entry point for imgmark."""

from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from PIL import Image
from .annotator import ImageAnnotator, SUPPORTED_INPUT_FORMATS
from .schema import OperationError, validate_operations

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
    op = {"type": "rectangle", "x1": args.rectangle[0], "y1": args.rectangle[1], "x2": args.rectangle[2], "y2": args.rectangle[3], "color": args.color, "width": args.width}
    annotator = ImageAnnotator(args.input); annotator.apply(op); annotator.save(args.output, args.overwrite)
    _emit({"success": True, "input": args.input, "output": args.output, "width": annotator.image.width, "height": annotator.image.height, "operations_applied": 1, **({"warnings": annotator.warnings} if annotator.warnings else {})}, args.json)

def build_parser():
    parser = argparse.ArgumentParser(prog="imgmark", description="Deterministic image annotation utility")
    sub = parser.add_subparsers(dest="command")
    info = sub.add_parser("info"); info.add_argument("input"); info.add_argument("--json", action="store_true")
    ann = sub.add_parser("annotate"); ann.add_argument("input"); ann.add_argument("--ops", required=True); ann.add_argument("--output", required=True); ann.add_argument("--overwrite", action="store_true"); ann.add_argument("--json", action="store_true")
    return parser

def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    # Convenient single-rectangle form: imgmark image.png --rectangle ...
    if argv and argv[0] not in {"info", "annotate", "-h", "--help"}:
        legacy = argparse.ArgumentParser(prog="imgmark")
        legacy.add_argument("input"); legacy.add_argument("--rectangle", nargs=4, type=float, required=True); legacy.add_argument("--color", default="red"); legacy.add_argument("--width", type=float, default=3); legacy.add_argument("--output", required=True); legacy.add_argument("--overwrite", action="store_true"); legacy.add_argument("--json", action="store_true")
        args = legacy.parse_args(argv)
        try: _legacy(args); return 0
        except Exception as exc: _emit_error(exc, args.json); return 1
    args = parser.parse_args(argv)
    if not args.command: parser.print_help(); return 2
    try:
        if args.command == "info": _info(args.input, args.json)
        else: _annotate(args)
        return 0
    except Exception as exc: _emit_error(exc, getattr(args, "json", False)); return 1

def _emit_error(exc, as_json):
    data = {"success": False, "error": getattr(exc, "code", "error"), "message": str(exc)}
    if isinstance(exc, OperationError) and exc.operation is not None: data["operation"] = exc.operation
    if as_json: print(json.dumps(data, sort_keys=True))
    else: print(f"error: {exc}", file=sys.stderr)

if __name__ == "__main__": raise SystemExit(main())
