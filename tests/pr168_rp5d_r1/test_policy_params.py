from ._helpers import read_jsonl


def test_policy_params_have_provenance() -> None:
    params = read_jsonl("params.jsonl")
    policy = read_jsonl("policy_prov.jsonl")
    assert params
    assert policy
    assert all(row["policy_provenance_ref"] for row in params)
    assert all(row["profit_proof_flag"] is False for row in policy)
