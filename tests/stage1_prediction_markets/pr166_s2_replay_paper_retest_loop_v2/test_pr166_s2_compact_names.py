from __future__ import annotations

from .helpers import REPO_ROOT
from src.qtt.stage1_prediction_markets.pr166_s2_replay_paper_retest_loop_v2 import constants as c


def test_pr166_s2_compact_report_schema_and_test_names():
    assert "PR166_S2_EdgeAttributionLedger.report.json" in c.REPORT_FILENAMES
    assert not any("PositivePreferenceCandidateLedger" in name for name in c.REPORT_FILENAMES)
    bad_fragments = ("p_r166", "q_k_u", "t_c_a", "d_a_g", "k_p_i", "s_f_feedback")
    for schema in c.SCHEMA_FILENAMES:
        assert not any(fragment in schema for fragment in bad_fragments)
    assert (REPO_ROOT / "tests" / "stage1_prediction_markets" / "pr166_s2_replay_paper_retest_loop_v2" / "test_pr166_s2_compact_names.py").exists()
