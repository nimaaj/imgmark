# imgmark

`imgmark` is a deterministic Pillow-based image annotation utility intended for
AI agents and scripts. It accepts ordered JSON drawing operations and always
writes a new PNG unless `--overwrite` is supplied.

```bash
uv run imgmark info screenshot.png --json
uv run imgmark annotate screenshot.png --ops operations.json --output marked.png --json
uv run imgmark detect screenshot.png --detector heuristic-ui --json
uv run imgmark crop screenshot.png --x1 100 --y1 100 --x2 500 --y2 400 --output crop.png --json
uv run imgmark screenshot.png --circle 400 300 40 --color blue --output marked.png --json
```

The Python API exposes the same operations:

```python
from imgmark import ImageAnnotator

annotator = ImageAnnotator("input.png")
annotator.rectangle(100, 100, 400, 300, color="red", width=3)
annotator.arrow(600, 200, 450, 250, color="yellow")
annotator.save("output.png")
```

Supported operation types are `rectangle`, `circle`, `ellipse`, `line`,
`arrow`, `point`, `marker`, `polygon`, and `text`. See the tests for compact
JSON examples. Coordinates are pixels with `(0, 0)` at the top-left.

`focus` is also available for the common “darken background, focus an element”
pattern. Supply `x1`, `y1`, `x2`, `y2`, and optionally `opacity` (default
`0.65`); the rectangle remains at its original brightness.

For an exact AI-agent CLI/API contract and copyable JSON examples, see
[AI_INTERFACE.md](AI_INTERFACE.md).

## UI recognition

The `heuristic-ui` detector finds contiguous visual regions that differ from a
dominant (or explicitly provided) background color. It is deterministic and
does not require a model, OpenCV, or network access. Its output is designed for
an AI workflow: every object has an ID, bounding box, dimensions, center point,
pixel area, and a deliberately conservative heuristic confidence (`0.5`).

```bash
uv run imgmark detect screenshot.png --background '#ffffff' --min-area 200 --json
```

Bounding boxes use half-open pixel coordinates: `x1`/`y1` are inclusive;
`x2`/`y2` are exclusive. The detector finds regions, not semantic labels; OCR,
component classification, and ML-based backends remain separate future layers.

Use `--padding N` with `detect` to expand every returned box by `N` pixels.
Padding is clipped at image edges, making the returned boxes convenient for
annotation and cropping around controls.
