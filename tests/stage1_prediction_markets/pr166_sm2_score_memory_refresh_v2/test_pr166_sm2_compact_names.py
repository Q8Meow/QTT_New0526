from __future__ import annotations

from .helpers import REPO_ROOT, summary
from src.qtt.stage1_prediction_markets.pr166_sm2_score_memory_refresh_v2 import constants as c


def test_pr166_sm2_compact_names_and_no_aliases():
    forbidden = [
        "PR166_SM2_PRFileConnectivityAudit.report.json",
        "PR166_SM2_RowValueConnectivityAudit.report.json",
        "PR166_SM2_AuthorityBoundaryAudit.report.json",
        "PR166_SM2_NoProfitEvidenceAudit.report.json",
    ]
    for filename in forbidden:
        assert not (REPO_ROOT / c.GENERATED_DIR / filename).exists()
    assert all(not schema.startswith("p_r166_s_m2") for schema in c.SCHEMA_FILENAMES)
    assert summary()["compact_report_rename_map"]
