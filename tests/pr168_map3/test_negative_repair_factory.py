from __future__ import annotations

from tests.pr168_map3._helpers import records


def test_negative_repair_factory_does_not_force_positives() -> None:
    rows = records("PR168_MAP3_NegRepairFactory.report.json")
    assert rows
    assert all(row["not_profit_proof_flag"] is True for row in rows)
    assert all(row["champion_allowed_flag"] is False for row in rows)
