from __future__ import annotations

from tests.pr168_map3._helpers import records, summary


def test_identity_graph_edges_do_not_promote_ambiguous_components() -> None:
    rows = records("PR168_MAP3_IDGraph.report.json")
    assert rows
    assert summary()["ambiguous_identity_graph_component_count"] == 0
    assert all(row["graph_promotion_state"] != "EXACT_REPAIRED_EXISTING_QKU_FORMULA_BINDING" for row in rows)
