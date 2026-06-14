from __future__ import annotations

from .helpers import REPO_ROOT
from src.qtt.stage1_prediction_markets.pr166_sf_r2_targeted_conversion_repair_retest import constants as c


def test_pr166_sf_r2_compact_names_and_no_aliases():
    generated = REPO_ROOT / c.GENERATED_DIR
    assert "PR166_SF_R2_RepairFrontier.report.json" in c.REPORT_FILENAMES
    forbidden = [
        "PR166_SF_R2_PRFileConnectivityAudit.report.json",
        "PR166_SF_R2_RowValueConnectivityAudit.report.json",
        "PR166_SF_R2_AuthorityBoundaryAudit.report.json",
        "PR166_SF_R2_NoProfitEvidenceAudit.report.json",
        "PR166_SF_R2_OrphanArtifactAudit.report.json",
    ]
    for name in forbidden:
        assert not (generated / name).exists(), name
