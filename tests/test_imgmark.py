import json
from PIL import Image
from imgmark import ImageAnnotator
from imgmark.cli import main
from imgmark import detect_ui_elements
from imgmark import crop_image

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

def test_heuristic_ui_detection_returns_precise_bounds(tmp_path, capsys):
    source = tmp_path / "ui.png"
    image = Image.new("RGB", (100, 80), "white")
    image.paste("#3366cc", (20, 30, 70, 55)); image.save(source)
    result = detect_ui_elements(source, background="#ffffff", min_area=10)
    assert result["objects"][0]["bbox"] == {"x1": 20, "y1": 30, "x2": 70, "y2": 55}
    assert result["objects"][0]["center"] == {"x": 45, "y": 42.5}
    assert main(["detect", str(source), "--background", "#ffffff", "--min-area", "10", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["objects"][0]["id"] == 1

def test_detection_padding_expands_and_clips_bounds(tmp_path):
    source = tmp_path / "ui.png"
    image = Image.new("RGB", (100, 80), "white"); image.paste("#3366cc", (2, 3, 20, 20)); image.save(source)
    result = detect_ui_elements(source, background="#ffffff", min_area=10, padding=5)
    assert result["objects"][0]["bbox"] == {"x1": 0, "y1": 0, "x2": 25, "y2": 25}

def test_single_operation_circle_cli(tmp_path, capsys):
    source, output = tmp_path / "in.png", tmp_path / "out.png"; make_image(source)
    assert main([str(source), "--circle", "30", "30", "10", "--color", "blue", "--output", str(output), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["operations_applied"] == 1

def test_crop_cli_and_api(tmp_path, capsys):
    source, output = tmp_path / "in.png", tmp_path / "crop.png"; make_image(source)
    result = crop_image(source, output, x1=10, y1=15, x2=50, y2=35)
    assert result["width"] == 40 and Image.open(output).size == (40, 20)
    cli_output = tmp_path / "crop-cli.png"
    assert main(["crop", str(source), "--x1", "0", "--y1", "0", "--x2", "20", "--y2", "10", "--output", str(cli_output), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["height"] == 10
