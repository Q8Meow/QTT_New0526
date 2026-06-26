from __future__ import annotations

from tools.pr168_rp5c_config import MARKET_SCOPES, ONTOLOGY_CATEGORIES

from ._helpers import load_rows


def test_rp5c_family_market_ontology_registries_are_centralized() -> None:
    families = load_rows("qku_formula_family_registry")
    markets = load_rows("market_scope_family_registry")
    ontology = load_rows("ontology_role_registry")
    formula_ontology = load_rows("formula_ontology")

    assert families
    assert {row["market_scope"] for row in markets} == set(MARKET_SCOPES)
    assert {row["ontology_category"] for row in ontology} == set(ONTOLOGY_CATEGORIES)
    assert formula_ontology
    assert all(row["route_rule_refs"] or row["ontology_category"] == "unknown_needs_review" for row in ontology)
