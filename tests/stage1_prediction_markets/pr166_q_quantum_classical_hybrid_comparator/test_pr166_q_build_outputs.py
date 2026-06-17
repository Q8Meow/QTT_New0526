from __future__ import annotations

from .helpers import REPO_ROOT
from src.qtt.stage1_prediction_markets.pr166_q_quantum_classical_hybrid_comparator import constants as c


def test_pr166_q_required_reports_and_schemas_exist():
    assert len(c.REPORT_FILENAMES) == 44
    assert len(c.SCHEMA_FILENAMES) == len(c.REPORT_FILENAMES) + 1
    for filename in c.REPORT_FILENAMES:
        assert (REPO_ROOT / c.GENERATED_DIR / filename).exists(), filename
    for filename in c.SCHEMA_FILENAMES:
        assert (REPO_ROOT / c.SCHEMA_DIR / filename).exists(), filename
    assert not list((REPO_ROOT / c.GENERATED_DIR).glob("PR166_Q_*.sha256"))
    assert not list((REPO_ROOT / c.GENERATED_DIR).glob("PR166_Q_*checksum*.json"))
    assert not list((REPO_ROOT / c.GENERATED_DIR).glob("PR166_Q_*digest*.json"))
