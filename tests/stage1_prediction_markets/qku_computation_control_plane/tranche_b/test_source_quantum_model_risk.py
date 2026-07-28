"""Certified source, quantum, model-risk, and security closure predicates."""

from __future__ import annotations

import ast
from collections import Counter
import json
from pathlib import Path

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (
    TRANCHE_B_SOURCE_CLAIM_BINDING_RULES,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.quantum_adapter import (
    PR162EQuantumAdapterV1,
    QuantumModelKind,
    QuantumStructuralReadinessProjectionV1,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    TRANCHE_B_CLOSURE_ROWS,
    validate_tranche_b_domain,
)


EXPECTED_DOMAIN_COUNTS = {
    "latency": 5,
    "model_risk": 8,
    "operations": 5,
    "quantum": 8,
    "security": 3,
    "source": 9,
}
EXPECTED_QUANTUM_CLOSURES = {
    f"ST12-CLOSURE::ST11-QUANTUM::{index:03d}"
    for index in range(7, 15)
}


def test_exact_domain_closure_population_and_terminal_ownership() -> None:
    assert len(TRANCHE_B_CLOSURE_ROWS) == 38
    assert Counter(row.domain for row in TRANCHE_B_CLOSURE_ROWS) == Counter(
        EXPECTED_DOMAIN_COUNTS
    )
    assert len({row.closure_id for row in TRANCHE_B_CLOSURE_ROWS}) == 38
    for closure in TRANCHE_B_CLOSURE_ROWS:
        source = json.loads(closure.original_row_json)
        implementation = source["implementation_specification"]
        assert (
            source["research_completeness_state"]
            == "COMPLETE_TERMINAL_CLOSURE_SPECIFICATION"
        )
        assert (
            source["implementation_specification_state"]
            == "COMPLETE_RESEARCHED_EXECUTABLE_SPECIFICATION"
        )
        assert implementation["canonical_owner"]
        assert implementation["implementation_owner"]
        assert implementation["independent_validator_owner"]
        assert implementation["consume_existing_owner_refs"]
        assert implementation["tests"]
        assert implementation["validation_commands"]
        assert implementation["failure_behavior"]
        assert implementation["fallback"]
        assert implementation["open_research_questions"] == []
        assert not implementation["runtime_effect_authorized"]


def test_exact_source_rules_are_atomic_terminal_and_fail_closed() -> None:
    assert len(TRANCHE_B_SOURCE_CLAIM_BINDING_RULES) == 10
    assert (
        len(
            {
                rule.binding_rule_id
                for rule in TRANCHE_B_SOURCE_CLAIM_BINDING_RULES
            }
        )
        == 10
    )
    for rule in TRANCHE_B_SOURCE_CLAIM_BINDING_RULES:
        if rule.binding_rule_id == "ST12-SOURCE-RULE::011":
            # The exact immutable Tranche-A owner is reused rather than relabeled.
            assert rule.research_completeness_state == ""
        else:
            assert (
                rule.research_completeness_state
                == "COMPLETE_TERMINAL_EXACT_RULE"
            )
        assert rule.claim_selector in {
            "EXACT_ATOMIC_FACT_ID_MEMBERSHIP_ONLY",
            "EXACT_MATH_SPEC_ID_ONLY",
        }
        assert rule.exact_claims
        assert rule.permitted_consumers
        assert not rule.source_pack_as_primary_allowed
        assert not rule.broad_regex_or_alias_matching_allowed
        assert not rule.codex_source_selection_allowed
        assert rule.permits_exact_claim(
            rule.exact_claims[0],
            rule.permitted_consumers[0],
        )
        assert not rule.permits_exact_claim(
            rule.exact_claims[0] + " fuzzy",
            rule.permitted_consumers[0],
        )


def test_quantum_structural_readiness_is_typed_and_never_executes() -> None:
    rows = PR162EQuantumAdapterV1(
        Path.cwd()
    ).structural_readiness_requirements(QuantumModelKind.ISING)
    assert len(rows) == 8
    assert {row.closure_id for row in rows} == EXPECTED_QUANTUM_CLOSURES
    for row in rows:
        assert isinstance(row, QuantumStructuralReadinessProjectionV1)
        assert row.mapping_owner == "PR162E_Q_QUANTUM_AUTOMAPPER"
        assert row.original_formulation_refs
        assert row.objective_sense
        assert row.economic_scale
        assert row.variable_domains
        assert row.hard_constraints
        assert row.inverse_mapping
        assert row.economic_interpret_back
        assert row.original_model_feasibility
        assert row.independent_small_instance_oracle_refs
        assert (
            row.classical_fallback
            == "DETERMINISTIC_SAME_FORMULATION_CLASSICAL_FALLBACK"
        )
        assert row.no_trade_fallback == "NO_TRADE"
        assert row.blocker_codes
        assert not row.simulator_execution
        assert not row.qpu_execution
        assert not row.quantum_advantage_claim
        assert not row.order_effect


def test_model_risk_and_quantum_primary_closures_execute() -> None:
    model_risk = validate_tranche_b_domain("model_risk")
    quantum = validate_tranche_b_domain("quantum")
    assert model_risk.passed
    assert quantum.passed
    assert len(model_risk.checks) == 8
    assert len(quantum.checks) == 8


def test_new_production_modules_have_no_runtime_or_dynamic_import_surface() -> None:
    package = (
        Path("src")
        / "qtt"
        / "stage1_prediction_markets"
        / "qku_computation_control_plane"
    )
    new_modules = (
        "contextual_computability.py",
        "stack_resolver.py",
        "input_resolver.py",
        "unit_conversion.py",
        "freshness.py",
        "point_in_time.py",
        "fallback.py",
        "service.py",
    )
    forbidden_import_roots = {
        "asyncio",
        "importlib",
        "multiprocessing",
        "pickle",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "threading",
    }
    forbidden_calls = {"__import__", "eval", "exec"}
    for name in new_modules:
        path = package / name
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not (
                    {
                        alias.name.split(".", 1)[0]
                        for alias in node.names
                    }
                    & forbidden_import_roots
                )
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert (
                    node.module.split(".", 1)[0]
                    not in forbidden_import_roots
                )
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
            ):
                assert node.func.id not in forbidden_calls
