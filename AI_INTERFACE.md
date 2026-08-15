# imgmark AI Tool Interface

Use `imgmark` to inspect images, locate visually distinct UI regions, and
produce a new annotated PNG. It is designed for deterministic, one-shot agent
calls: use pixel coordinates exactly as returned, and put all annotations in a
single ordered JSON file.

Run commands through `uv`:

```bash
UV_CACHE_DIR=/tmp/imgmark-uv-cache uv run imgmark <command> ...
```

## Coordinate contract

- Image origin: `(0, 0)` is top-left.
- `x` increases right; `y` increases down.
- All v0.1 coordinates are pixels.
- Detector bounding boxes are half-open: `x1`/`y1` are inclusive;
  `x2`/`y2` are exclusive. Therefore `width = x2 - x1`.
- Annotation rectangles use the supplied coordinates unchanged.

## Tool: inspect image

```bash
imgmark info INPUT_IMAGE --json
```

Returns:

```json
{
  "path": "screenshot.png",
  "width": 1920,
  "height": 1080,
  "mode": "RGB",
  "format": "PNG"
}
```

Use this first when coordinates are not already known.

## Tool: detect UI regions

```bash
imgmark detect INPUT_IMAGE --detector heuristic-ui --json
```

The built-in `heuristic-ui` backend finds contiguous regions visually distinct
from the dominant background. For a known solid canvas color, use
`--background '#ffffff'` for more stable results.

Useful controls:

```bash
imgmark detect INPUT_IMAGE \
  --background '#ffffff' \
  --color-threshold 28 \
  --min-area 100 \
  --min-width 8 \
  --min-height 8 \
  --padding 8 \
  --json
```

Example result:

```json
{
  "success": true,
  "detector": "heuristic-ui",
  "coordinate_system": "pixel",
  "bbox_convention": "x1/y1 inclusive; x2/y2 exclusive",
  "image": {"width": 1920, "height": 1080},
  "objects": [
    {
      "id": 1,
      "type": "region",
      "bbox": {"x1": 500, "y1": 700, "x2": 640, "y2": 750},
      "width": 140,
      "height": 50,
      "area": 6320,
      "center": {"x": 570, "y": 725},
      "confidence": 0.5
    }
  ]
}
```

`type: "region"` is intentionally non-semantic: this backend does not claim
that a region is a button, input, label, or icon. Treat `confidence` as a
fixed heuristic signal rather than a calibrated probability. An AI should use
the returned geometry alongside visual reasoning, then annotate selected
objects.

`--padding N` expands each recognized box by `N` pixels in every direction.
The expansion is clipped at image edges and is reflected directly in each
returned `bbox`, `width`, `height`, and `center`.

## Tool: annotate image

```bash
imgmark annotate INPUT_IMAGE --ops OPERATIONS_JSON --output OUTPUT.png --json
```

- Input formats: PNG, JPEG, WEBP.
- Output format: PNG only.
- The command fails if the output already exists; add `--overwrite` only when
  replacement is intended.
- Operations are applied in array order; later items are drawn above earlier
  items.

Operation document:

```json
{
  "operations": [
    {"type": "rectangle", "x1": 500, "y1": 700, "x2": 640, "y2": 750, "color": "red", "width": 4},
    {"type": "arrow", "x1": 760, "y1": 620, "x2": 640, "y2": 700, "color": "yellow", "width": 4},
    {"type": "text", "x": 770, "y": 590, "text": "Likely target", "color": "yellow", "size": 24, "background": "black", "padding": 5}
  ]
}
```

Successful JSON result:

```json
{
  "success": true,
  "input": "screenshot.png",
  "output": "annotated.png",
  "width": 1920,
  "height": 1080,
  "operations_applied": 3
}
```

Out-of-bounds coordinates are retained and reported in `warnings`; they are
not silently clamped. Invalid requests return `{ "success": false, ... }`.

## Tool: crop image

```bash
imgmark crop INPUT_IMAGE --x1 100 --y1 100 --x2 500 --y2 400 --output CROP.png --json
```

Crop bounds are explicit, half-open pixel coordinates. The result has width
`x2 - x1` and height `y2 - y1`. Bounds must be completely inside the source
image; the command never clamps or alters them. Output is PNG and is protected
from replacement unless `--overwrite` is supplied.

```json
{
  "success": true,
  "input": "screenshot.png",
  "output": "target.png",
  "crop": {"x1": 500, "y1": 700, "x2": 640, "y2": 750},
  "width": 140,
  "height": 50
}
```

Use a detector result directly as crop coordinates:

```python
from imgmark import crop_image, detect_ui_elements

box = detect_ui_elements("screenshot.png")["objects"][0]["bbox"]
crop_image("screenshot.png", "element.png", **box)
```

## Annotation operation schemas

All operations default to `color: "red"`. Named colors are `red`, `green`,
`blue`, `yellow`, `orange`, `purple`, `cyan`, `magenta`, `white`, `black`, and
`gray`. Hex `#RRGGBB`, hex `#RRGGBBAA`, and `rgba(r,g,b,a)` are also accepted.

| Type | Required fields | Optional fields |
| --- | --- | --- |
| `rectangle` | `x1`, `y1`, `x2`, `y2` | `color`, `width`, `fill` |
| `circle` | `cx`, `cy`, `radius` | `color`, `width`, `fill` |
| `ellipse` | `x1`, `y1`, `x2`, `y2` | `color`, `width`, `fill` |
| `line` | `x1`, `y1`, `x2`, `y2` | `color`, `width` |
| `arrow` | `x1`, `y1`, `x2`, `y2` | `color`, `width`, `head_length`, `head_width` |
| `point` | `x`, `y` | `color`, `radius` |
| `marker` | `x`, `y` | `color`, `style` (`dot`, `cross`, `x`), `size` |
| `polygon` | `points` (three or more `[x, y]` pairs) | `color`, `width`, `fill` |
| `text` | `x`, `y`, `text` | `color`, `size`, `background`, `padding` |
| `focus` | `x1`, `y1`, `x2`, `y2` | `opacity` (default `0.65`) |

## One-operation CLI shortcuts

For a single operation, omit `annotate` and select one flag after the input
path. Every form requires `--output OUTPUT.png`.

```bash
imgmark image.png --rectangle X1 Y1 X2 Y2 --output out.png
imgmark image.png --circle CX CY RADIUS --output out.png
imgmark image.png --ellipse X1 Y1 X2 Y2 --output out.png
imgmark image.png --line X1 Y1 X2 Y2 --output out.png
imgmark image.png --arrow X1 Y1 X2 Y2 --head-length 20 --head-width 14 --output out.png
imgmark image.png --point X Y --radius 8 --output out.png
imgmark image.png --marker X Y --style cross --size 15 --output out.png
imgmark image.png --polygon '[[100,100],[300,120],[350,250]]' --output out.png
imgmark image.png --text 'Click here' --x 610 --y 280 --size 28 --background black --output out.png
imgmark image.png --focus X1 Y1 X2 Y2 --opacity .65 --output out.png
```

Use exactly one shortcut primitive per call. Use `annotate --ops` for an
ordered sequence of multiple operations.

## Direct Python functions

```python
from imgmark import ImageAnnotator, detect_ui_elements

regions = detect_ui_elements("screenshot.png", background="#ffffff")
box = regions["objects"][0]["bbox"]

annotator = ImageAnnotator("screenshot.png")
annotator.rectangle(**box, color="red", width=4)
annotator.text(box["x1"], box["y1"] - 30, "Target", color="yellow", background="black")
annotator.save("annotated.png")
```

Available `ImageAnnotator` methods: `rectangle`, `circle`, `ellipse`, `line`,
`arrow`, `point`, `marker`, `text`, `apply`, `apply_all`, and `save`.
Use `apply` for `polygon` and `focus` operations.
