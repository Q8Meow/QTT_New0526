from __future__ import annotations

from .helpers import assert_report_rows


def test_pr166_sm2_positive_seed_and_driver_rows():
    seeds = assert_report_rows("PR166_SM2_PosSeedLedger.report.json", 2)
    drivers = assert_report_rows("PR166_SM2_PosDriverLedger.report.json", 2)
    assert all(row["seed_shrinkage_penalty"] >= 0 for row in seeds)
    assert all(row["driver_quantum_structure_bucket"] for row in drivers)
