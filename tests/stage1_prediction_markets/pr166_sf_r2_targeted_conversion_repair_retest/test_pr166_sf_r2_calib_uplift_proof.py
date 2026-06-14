from __future__ import annotations

from .helpers import assert_all_rows_connected


def test_pr166_sf_r2_calib_uplift_proof():
    rows = assert_all_rows_connected("PR166_SF_R2_CalibUpliftProof.report.json", allow_empty=False)
    if not False:
        assert rows
