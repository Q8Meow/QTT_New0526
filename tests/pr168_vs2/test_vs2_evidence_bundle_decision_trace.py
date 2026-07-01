from .test_support import packet_ids, read_jsonl


def test_evidence_bundle_contains_numeric_upstream_refs() -> None:
    for row in read_jsonl("packet_evidence_bundle.jsonl"):
        assert row["paper_intent_candidate_id"] in packet_ids()
        assert row["numeric_evidence_refs"]
        assert row["net_expected_pnl_cash"] != ""
        assert row["metadata_label_only_proof_flag"] is False


def test_decision_trace_explains_readiness_without_recompute() -> None:
    for row in read_jsonl("packet_decision_trace.jsonl"):
        assert row["decision_reason_codes"]
        assert row["formula_computation_created_by_vs2_flag"] is False
        assert row["rank4_recomputed_by_vs2_flag"] is False
        assert row["qopt1_recomputed_by_vs2_flag"] is False
