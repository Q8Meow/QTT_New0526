from __future__ import annotations

from .helpers import assert_report_contract, summary


def test_pr166_q_consumes_expected_quantum_handoffs_and_roots():
    handoff_rows = assert_report_contract("PR166_Q_ComputabilityDispositionLedger.report.json", 559)
    root_rows = assert_report_contract("PR166_Q_RootReportConsumptionLedger.report.json", 109)
    input_rows = assert_report_contract("PR166_Q_InputHandoffConsumption.report.json")
    assert summary()["actual_consumed_quantum_comparator_row_count"] == 559
    assert summary()["pr166_sm3_root_report_count_discovered"] == 109
    assert all(row["consumed_by_PR166_Q_flag"] for row in root_rows)
    consumed = {row["input_report_ref"]: row for row in input_rows}
    assert consumed["PR166_SM3_PR166QHandoff.report.json"]["row_count"] == 559
    assert consumed["PR166_SM3_PR166QBHandoff.report.json"]["row_count"] == 559
    assert consumed["PR166_SM3_PR166QCHandoff.report.json"]["row_count"] == 559
    assert handoff_rows[0]["upstream_row_ref"].startswith("PR166_SM3_PR166Q")
