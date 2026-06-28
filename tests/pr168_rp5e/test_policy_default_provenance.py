from ._helpers import read_jsonl


def test_policy_defaults_are_candidate_only_and_trace_to_params() -> None:
    provenance = read_jsonl("policy_prov.jsonl")
    params = read_jsonl("params.jsonl")
    prov_refs = {row["parameter_name"] for row in provenance}

    assert {"fdr_q_default", "max_formulas_per_stack"} <= prov_refs
    assert all(row["paper_authority_flag"] is False for row in provenance)
    assert all(row["live_authority_flag"] is False for row in provenance)
    assert all(row["profit_proof_flag"] is False for row in provenance)
    assert all(row["parameter_name"] in prov_refs for row in params)
