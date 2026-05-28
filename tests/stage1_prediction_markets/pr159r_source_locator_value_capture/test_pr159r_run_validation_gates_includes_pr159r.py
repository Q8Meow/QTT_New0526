from pathlib import Path


def test_pr159r_run_validation_gates_includes_pr159r():
    root = Path(__file__).resolve().parents[3]
    text = (root / "tools/run_validation_gates.py").read_text(encoding="utf-8")
    assert "validate_pr159r_source_locator_value_capture.py" in text

