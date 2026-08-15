import json
from PIL import Image
from imgmark import ImageAnnotator
from imgmark.cli import main

def make_image(path): Image.new("RGB", (100, 80), "white").save(path)

def test_python_api_rectangle_and_save(tmp_path):
    source, output = tmp_path / "in.png", tmp_path / "out.png"; make_image(source)
    ImageAnnotator(source).rectangle(10, 10, 50, 40, color="#ff0000", width=3).save(output)
    assert Image.open(output).getpixel((10, 10))[:3] == (255, 0, 0)

def test_json_operations_and_warning(tmp_path, capsys):
    source, output, ops = tmp_path / "in.png", tmp_path / "out.png", tmp_path / "ops.json"; make_image(source)
    ops.write_text(json.dumps({"operations": [{"type": "circle", "cx": 20, "cy": 20, "radius": 8}, {"type": "arrow", "x1": 50, "y1": 50, "x2": 200, "y2": 20, "color": "blue"}]}))
    assert main(["annotate", str(source), "--ops", str(ops), "--output", str(output), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out); assert payload["operations_applied"] == 2 and payload["warnings"]

def test_info_json(tmp_path, capsys):
    source = tmp_path / "in.png"; make_image(source)
    assert main(["info", str(source), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["width"] == 100

def test_invalid_operation_is_structured(tmp_path, capsys):
    source, output, ops = tmp_path / "in.png", tmp_path / "out.png", tmp_path / "ops.json"; make_image(source)
    ops.write_text('{"operations":[{"type":"banana"}]}')
    assert main(["annotate", str(source), "--ops", str(ops), "--output", str(output), "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "unknown_operation"
