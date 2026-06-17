from __future__ import annotations

from .helpers import assert_report_contract


def test_pr166_q_computability_dispositions_are_explicit_and_non_placeholder():
    rows = assert_report_contract("PR166_Q_ComputabilityDispositionLedger.report.json", 559)
    assert {row["computability_disposition"] for row in rows} == {"COMPUTABLE_NOW"}
    assert all(row["fill_action_ref"] for row in rows)
    assert all(row["repair_route_ref"] for row in rows)
    assert not any(row["metadata_only_ready_flag"] for row in rows)
    assert not any(row["solver_label_only_ready_flag"] for row in rows)
    assert not any(row["placeholder_ready_flag"] for row in rows)
    assert not any(row["future_consumer_note_only_ready_flag"] for row in rows)


def test_pr166_q_no_forbidden_authority_flags_are_created():
    for filename in (
        "PR166_Q_QuantumClassicalHybridRaceLedger.report.json",
        "PR166_Q_QuantumStructuralReadiness.report.json",
        "PR166_Q_PR166_QB_BoundedNonLiveQuantumBenchmarkHandoff.report.json",
        "PR166_Q_FinalSummary.report.json",
    ):
        assert_report_contract(filename)
