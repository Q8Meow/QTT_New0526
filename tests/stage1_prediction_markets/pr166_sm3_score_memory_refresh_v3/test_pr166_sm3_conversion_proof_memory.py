from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_sm3_conversion_proof_memory_report_contract():
    rows = assert_report_contract("PR166_SM3_ConvProofMemory.report.json", 3213)
    assert rows
