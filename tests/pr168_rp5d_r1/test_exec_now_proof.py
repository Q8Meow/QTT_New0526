from ._helpers import read_jsonl


def test_exec_now_proof_exists_for_each_promotion() -> None:
    assert len(read_jsonl("exec_now_proof.jsonl")) == len(read_jsonl("promote.jsonl"))
