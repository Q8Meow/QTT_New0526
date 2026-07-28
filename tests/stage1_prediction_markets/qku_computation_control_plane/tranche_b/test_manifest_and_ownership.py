"""Exact Tranche-B manifest, ownership, route, and compatibility proofs."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (
    SOURCE_CLAIM_BINDING_RULES,
    TRANCHE_A_SOURCE_CLAIM_BINDING_RULES,
    TRANCHE_B_SOURCE_CLAIM_BINDING_RULES,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    ContractValidationError,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    IMPLEMENTATION_REGISTRY,
    TRANCHE_A_MATH_IDS,
    TRANCHE_B_MATH_IDS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.oracle_contracts import (
    ORACLE_PACK,
    TRANCHE_A_ORACLE_PACK,
    TRANCHE_B_ORACLE_COVERAGE_ROWS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
    STEP12_PARAMETER_POLICIES,
    TRANCHE_A_PARAMETER_POLICIES,
    TRANCHE_B_PARAMETER_POLICIES,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.service import (
    AGENT_DUTY_ROUTES,
    INSTITUTIONAL_FEATURE_SOCKETS,
    TRANCHE_B_SERVICE_BINDINGS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.specification import (
    TRANCHE_B_MATH_SPECIFICATIONS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    TRANCHE_A_OPERATION_CONTRACTS,
    TRANCHE_B_CLOSURE_ROWS,
    TRANCHE_B_REPOSITORY_DISPOSITIONS,
    TRANCHE_B_TEST_ROWS,
    TRANCHE_B_VALIDATION_COMMANDS,
    build_tranche_a_coverage_manifest,
    build_tranche_b_coverage_manifest,
)


EXPECTED_B_COUNTS = {
    "closure_rows": 38,
    "repository_dispositions": 8,
    "parameter_policy_rows": 344,
    "mathematical_specifications": 30,
    "independent_oracle_specifications": 30,
    "golden_vectors_and_invariants": 30,
    "test_rows": 44,
    "validation_command_rows": 12,
    "source_claim_binding_rules": 10,
    "total_rows": 546,
}
EXPECTED_PRODUCTION_BASENAMES = {
    "contextual_computability.py",
    "stack_resolver.py",
    "input_resolver.py",
    "unit_conversion.py",
    "freshness.py",
    "point_in_time.py",
    "fallback.py",
    "service.py",
}
EXPECTED_AGENT_IDS = {
    "research_agent",
    "parameter_selector_agent",
    "risk_manager_agent",
    "quantum_optimizer_agent",
    "commander_agent",
    "governance_agent",
    "dashboard_agent",
    "connector_venue_readiness_future_consumer",
}
EXPECTED_COMMANDS = (
    "python tools/independent_validate_qku_computation_control_plane_latency.py",
    "python tools/independent_validate_qku_computation_control_plane_model_risk.py",
    "python tools/independent_validate_qku_computation_control_plane_operations.py",
    "python tools/independent_validate_qku_computation_control_plane_quantum.py",
    "python tools/independent_validate_qku_computation_control_plane_security.py",
    "python tools/independent_validate_qku_computation_control_plane_source.py",
    "python tools/validate_qku_computation_control_plane.py --domain latency",
    "python tools/validate_qku_computation_control_plane.py --domain model_risk",
    "python tools/validate_qku_computation_control_plane.py --domain operations",
    "python tools/validate_qku_computation_control_plane.py --domain quantum",
    "python tools/validate_qku_computation_control_plane.py --domain security",
    "python tools/validate_qku_computation_control_plane.py --domain source",
)


@pytest.fixture(scope="module")
def tranche_b_manifest():
    return build_tranche_b_coverage_manifest()


def test_exact_incremental_and_union_counts_are_derived() -> None:
    assert len(TRANCHE_B_CLOSURE_ROWS) == 38
    assert len(TRANCHE_B_REPOSITORY_DISPOSITIONS) == 8
    assert len(TRANCHE_B_PARAMETER_POLICIES) == 344
    assert len(TRANCHE_B_MATH_SPECIFICATIONS) == 30
    assert len(TRANCHE_B_ORACLE_COVERAGE_ROWS) == 30
    assert len(TRANCHE_B_TEST_ROWS) == 44
    assert len(TRANCHE_B_VALIDATION_COMMANDS) == 12
    assert len(TRANCHE_B_SOURCE_CLAIM_BINDING_RULES) == 10

    assert len(TRANCHE_A_PARAMETER_POLICIES) == 135
    assert len(STEP12_PARAMETER_POLICIES) == 479
    assert len(TRANCHE_A_MATH_IDS) == 19
    assert len(TRANCHE_B_MATH_IDS) == 30
    assert len(IMPLEMENTATION_REGISTRY) == len(
        set(TRANCHE_A_MATH_IDS) | set(TRANCHE_B_MATH_IDS)
    )
    assert len(TRANCHE_A_ORACLE_PACK) == 19
    assert len(ORACLE_PACK) == 30
    assert len(TRANCHE_A_SOURCE_CLAIM_BINDING_RULES) == 1
    assert len(SOURCE_CLAIM_BINDING_RULES) == 10


def test_exact_eight_production_dispositions_exist_without_ninth_module() -> None:
    paths = tuple(
        row.repository_path
        for row in TRANCHE_B_REPOSITORY_DISPOSITIONS
    )
    assert {Path(path).name for path in paths} == EXPECTED_PRODUCTION_BASENAMES
    assert all(Path(path).is_file() for path in paths)
    package = Path(paths[0]).parent
    declared = {
        path.name
        for path in package.glob("*.py")
        if path.name in EXPECTED_PRODUCTION_BASENAMES
    }
    assert declared == EXPECTED_PRODUCTION_BASENAMES


def test_44_certified_test_rows_map_to_five_coherent_modules() -> None:
    assert len({row.test_id for row in TRANCHE_B_TEST_ROWS}) == 44
    mapped = {row.mapped_test_path for row in TRANCHE_B_TEST_ROWS}
    expected = {
        (
            "tests/stage1_prediction_markets/qku_computation_control_plane/"
            "tranche_b/test_resolution_pipeline.py"
        ),
        (
            "tests/stage1_prediction_markets/qku_computation_control_plane/"
            "tranche_b/test_service_operations.py"
        ),
        (
            "tests/stage1_prediction_markets/qku_computation_control_plane/"
            "tranche_b/test_source_quantum_model_risk.py"
        ),
        (
            "tests/stage1_prediction_markets/qku_computation_control_plane/"
            "tranche_b/test_manifest_and_ownership.py"
        ),
    }
    assert mapped == expected
    actual_modules = {
        path.as_posix()
        for path in Path(
            "tests/stage1_prediction_markets/"
            "qku_computation_control_plane/tranche_b"
        ).glob("test_*.py")
    }
    assert actual_modules == {
        *expected,
        (
            "tests/stage1_prediction_markets/qku_computation_control_plane/"
            "tranche_b/test_math_oracle_vectors.py"
        ),
    }


def test_b_manifest_executes_exact_rows_and_eight_derived_proofs(
    tranche_b_manifest,
) -> None:
    assert dict(tranche_b_manifest.executed_counts) == EXPECTED_B_COUNTS
    assert len(tranche_b_manifest.rows) == 546
    assert len({row.row_id for row in tranche_b_manifest.rows}) == 546
    assert len(tranche_b_manifest.derived_predicates) == 8
    assert all(value for _, value in tranche_b_manifest.derived_predicates)
    assert all(
        row.upstream_owner
        and row.exact_selector
        and row.transformation
        and row.canonical_owner
        and row.responsible_agent
        and row.central_service_operations
        and row.downstream_consumers
        and row.test_path
        and row.independent_validator
        and row.terminal_route
        and row.no_orphan_disposition == "VALIDATED_AND_CONSUMED"
        for row in tranche_b_manifest.rows
    )


def test_forced_false_and_unexpected_manifest_predicates_fail_closed() -> None:
    first = TRANCHE_B_CLOSURE_ROWS[0].closure_id
    with pytest.raises(ContractValidationError):
        build_tranche_b_coverage_manifest(
            predicate_overrides={first: False}
        )
    with pytest.raises(ContractValidationError):
        build_tranche_b_coverage_manifest(
            predicate_overrides={"UNEXPECTED": True}
        )


def test_tranche_a_manifest_and_operation_roster_remain_exact() -> None:
    manifest = build_tranche_a_coverage_manifest()
    assert len(manifest.rows) == 311
    assert manifest.executed_counts["total_rows"] == 311
    assert len(TRANCHE_A_OPERATION_CONTRACTS) == 15
    assert len(TRANCHE_B_SERVICE_BINDINGS) == 15
    assert set(TRANCHE_B_SERVICE_BINDINGS) == {
        operation.operation_id
        for operation in TRANCHE_A_OPERATION_CONTRACTS
    }
    assert all(
        operation.schema_version == "1.4.0"
        and operation.capability_class.value
        == "CONTRACT_DEFINITION_ONLY"
        for operation in TRANCHE_A_OPERATION_CONTRACTS
    )
    assert all(
        binding.pure_in_process
        and not binding.external_or_durable_effect_allowed
        for binding in TRANCHE_B_SERVICE_BINDINGS.values()
    )


def test_exact_agent_routes_and_scope_pure_feature_sockets() -> None:
    assert {route.agent_id for route in AGENT_DUTY_ROUTES} == EXPECTED_AGENT_IDS
    assert len(AGENT_DUTY_ROUTES) == 8
    assert all(
        route.historical_duty_source
        and route.current_orchestration_owner == "AGENT-ORCH1::AgentOrchService"
        and route.operation_ids
        and route.upstream_refs
        and route.downstream_refs
        and route.reviewer_ref
        and route.terminal_route
        and len(route.authority_non_effects) == 6
        for route in AGENT_DUTY_ROUTES
    )
    assert len(INSTITUTIONAL_FEATURE_SOCKETS) == 9
    assert Counter(
        socket.canonical_owner
        for socket in INSTITUTIONAL_FEATURE_SOCKETS
    ) == Counter(
        {
            "RANK4": 4,
            "PRETRADE1": 3,
            "MEM1": 1,
            "QOPT1+PR162E-Q": 1,
        }
    )
    assert all(
        not socket.implements_economic_engine
        and socket.field_ids
        and socket.point_in_time_and_freshness
        and socket.unavailable_disposition
        and socket.operation_ids
        and socket.downstream_consumer
        for socket in INSTITUTIONAL_FEATURE_SOCKETS
    )


def test_validation_commands_preserve_exact_certified_order() -> None:
    assert tuple(row.command for row in TRANCHE_B_VALIDATION_COMMANDS) == (
        EXPECTED_COMMANDS
    )
    assert len({row.command_id for row in TRANCHE_B_VALIDATION_COMMANDS}) == 12
    assert all(Path(row.script_path).is_file() for row in TRANCHE_B_VALIDATION_COMMANDS)
