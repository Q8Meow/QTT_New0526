from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_formula_provenance_keeps_candidate_non_truth_authority() -> None:
    for row in records("PR168_MAP3_FormulaProv.report.json"):
        assert row["formula_provenance_id"].startswith("PROV_")
        assert row["candidate_only_flag"] is True
        assert row["accepted_truth_flag"] is False
        assert row["source_evidence_review_route"] == "SOURCE_EVIDENCE_REVIEW"
        assert row["triangulation_state"] in {
            "SINGLE_SOURCE_CANDIDATE",
            "MULTI_SOURCE_CANDIDATE",
            "OFFICIAL_PLUS_RESEARCH_CANDIDATE",
        }
