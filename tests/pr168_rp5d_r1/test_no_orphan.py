from ._helpers import read_jsonl


def test_no_orphan_proofs_pass() -> None:
    assert read_jsonl("orph_art.jsonl")[0]["proof_pass_flag"] is True
    assert read_jsonl("orph_qku.jsonl")[0]["proof_pass_flag"] is True
