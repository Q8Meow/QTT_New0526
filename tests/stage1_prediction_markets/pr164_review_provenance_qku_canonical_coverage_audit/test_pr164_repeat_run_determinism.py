from pathlib import Path

from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.json_io import json_text
from src.qtt.stage1_prediction_markets.pr164_review_provenance_qku_canonical_coverage_audit.report_builder import build_payloads


def test_pr164_repeat_run_determinism():
    root = Path(".").resolve()
    first = build_payloads(root)
    second = build_payloads(root)
    assert json_text(first, compact=True) == json_text(second, compact=True)
