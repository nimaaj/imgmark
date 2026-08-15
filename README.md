# imgmark

`imgmark` is a deterministic Pillow-based image annotation utility intended for
AI agents and scripts. It accepts ordered JSON drawing operations and always
writes a new PNG unless `--overwrite` is supplied.

```bash
uv run imgmark info screenshot.png --json
uv run imgmark annotate screenshot.png --ops operations.json --output marked.png --json
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
