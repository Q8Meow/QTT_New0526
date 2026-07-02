from tests.pr169_dash1.conftest import jsonl


def test_decision_queue_is_sorted_by_fail_closed_priority() -> None:
    rows = jsonl("owner_decision_queue.generated.jsonl")
    keys = [(row["severity_rank"], row["gate_priority"], row["unresolved_order"]) for row in rows]
    assert keys == sorted(keys)
    assert rows[0]["severity_badge"] == "S4_CRITICAL"
