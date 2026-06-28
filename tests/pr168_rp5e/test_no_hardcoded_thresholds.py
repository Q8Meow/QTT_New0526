from ._helpers import read_jsonl


def test_no_hardcode_proof_routes_tunables_through_params_and_policy() -> None:
    proof = read_jsonl("no_hardcode.jsonl")[0]
    params = read_jsonl("params.jsonl")

    assert proof["hardcoded_threshold_attempt_count"] == 0
    assert proof["all_tunable_defaults_in_params_flag"] is True
    assert proof["policy_provenance_complete_flag"] is True
    assert {row["parameter_name"] for row in params} >= {
        "near_clone_jaccard_threshold",
        "role_coverage_min",
        "fdr_q_default",
        "w_role",
        "w_edge",
    }
