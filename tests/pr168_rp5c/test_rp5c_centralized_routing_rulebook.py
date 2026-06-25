from __future__ import annotations

from tools.pr168_rp5c_config import ONTOLOGY_CATEGORIES

from ._helpers import load_rows


def test_rp5c_routing_is_central_rulebook_not_per_qku_authority() -> None:
    groups = load_rows("agent_responsibility_group_registry")
    rules = load_rows("agent_duty_routing_rulebook")

    assert len(groups) >= len(ONTOLOGY_CATEGORIES)
    assert len(rules) >= len(ONTOLOGY_CATEGORIES)
    assert all(row["manual_per_qku_override_allowed_flag"] is False for row in rules)
    assert all(row["responsibility_group_refs"] for row in rules)
    assert not any("qku_id" in row for row in rules)
