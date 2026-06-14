from __future__ import annotations

from .helpers import REPO_ROOT, assert_report_contract
from src.qtt.stage1_prediction_markets.pr166_sf_r2_targeted_conversion_repair_retest import constants as c


def test_pr166_sf_r2_build_outputs_exist():
    for filename in c.REPORT_FILENAMES:
        assert_report_contract(
            filename,
            allow_empty=filename == "PR166_SF_R2_TerminalRows.report.json",
        )
    for schema in c.SCHEMA_FILENAMES:
        assert (REPO_ROOT / c.SCHEMA_DIR / schema).exists(), schema
