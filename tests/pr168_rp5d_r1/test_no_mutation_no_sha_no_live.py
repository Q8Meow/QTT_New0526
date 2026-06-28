from ._helpers import read_jsonl


def test_no_mutation_no_sha_no_live_proofs_pass() -> None:
    assert read_jsonl("no_mut.jsonl")[0]["formula_or_qku_mutation_count"] == 0
    assert read_jsonl("no_sha.jsonl")[0]["qtt_sha_or_atomicrows_ref_count"] == 0
    assert read_jsonl("no_auth.jsonl")[0]["forbidden_authority_count"] == 0
