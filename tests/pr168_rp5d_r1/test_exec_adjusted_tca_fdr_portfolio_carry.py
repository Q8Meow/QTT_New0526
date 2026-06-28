from ._helpers import read_jsonl


def test_institutional_readiness_carry_forward_ledgers_exist() -> None:
    for name in ("exec_adj_delta.jsonl", "tca_delta.jsonl", "fdr_carry.jsonl", "port_cap_carry.jsonl"):
        assert read_jsonl(name), name
