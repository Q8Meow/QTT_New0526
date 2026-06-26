from __future__ import annotations

from ._helpers import load_rows


def test_rp5c_every_identity_has_derived_route_resolution() -> None:
    identities = load_rows("immutable_qku_formula_library")
    routes = load_rows("derived_agent_route_resolution_ledger")
    route_ids = {row["route_resolution_id"] for row in routes}

    assert len(routes) == len(identities)
    for row in identities:
        assert row["derived_route_resolution_refs"]
        assert set(row["derived_route_resolution_refs"]).issubset(route_ids)
        assert row["agent_responsibility_group_refs"]
        assert row["route_rule_refs"]
