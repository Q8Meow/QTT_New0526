from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_external_intake_is_candidate_only_and_routed() -> None:
    for row in records("PR168_MAP3_ExtIntake.report.json"):
        assert row["candidate_only_flag"] is True
        assert row["accepted_truth_flag"] is False
        assert row["source_url"]
        assert row["source_tier"]
        assert row["formula_family_candidate"]
        assert row["required_inputs"]
        assert row["source_evidence_review_route"]
        assert row["no_orphan_status"] == "NO_ORPHAN_LINKED"
