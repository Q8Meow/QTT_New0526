from tests.pr162e.helpers import plugin_rows


def test_quantum_repair_plugins_have_repair_surfaces():
    rows = [row for row in plugin_rows() if row["plugin_family"] in {"QUANTUM_ENCODING_REPAIR_PLUGIN", "PENALTY_SCALING_REPAIR_PLUGIN", "CONSTRAINT_REPAIR_PLUGIN", "HYBRID_FALLBACK_REPAIR_PLUGIN"}]
    assert rows
    assert all(row["repair_action_refs"] for row in rows)
