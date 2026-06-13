from __future__ import annotations

from .helpers import assert_report_rows, summary


def test_pr166_s2_quantum_handoff_has_classical_evidence_and_no_backend():
    rows = assert_report_rows("PR166_S2_QuantumHandoff.report.json", summary()["quantum_handoff_rows"])
    row = rows[0]
    assert row["classical_replay_paper_evidence_ref"].startswith("PR166_S2_NET_EDGE_RESULT::")
    assert row["quantum_backend_execution_count"] == 0
    assert row["quantum_advantage_claim_count"] == 0
