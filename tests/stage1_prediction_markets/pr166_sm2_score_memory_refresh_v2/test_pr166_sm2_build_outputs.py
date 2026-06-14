from __future__ import annotations

from .helpers import REPO_ROOT, assert_report_rows
from src.qtt.stage1_prediction_markets.pr166_sm2_score_memory_refresh_v2 import constants as c


def test_pr166_sm2_build_outputs_exist():
    for filename in c.REPORT_FILENAMES:
        assert_report_rows(filename)
    for schema in c.SCHEMA_FILENAMES:
        assert (REPO_ROOT / c.SCHEMA_DIR / schema).exists(), schema
