from collections import Counter

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (
    FORMULA_INPUT_AUTHORITY_BINDINGS,
    NUMERIC_VALUE_AUTHORITY_BINDINGS,
    PRIMARY_SOURCE_REGISTRY,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    IMPLEMENTATION_REGISTRY,
    IMPLEMENTATION_VERSION_REGISTRY,
    PREDECESSOR_IMPLEMENTATION_REGISTRY,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (
    OperationCapabilityClass,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
    CUMULATIVE_PARAMETER_POLICIES,
    INCREMENTAL_TRANCHE_B_PARAMETER_POLICIES,
    OPTIMIZER_DEFAULT_CURRENTIZATIONS,
    RUNTIME_PARAMETER_OWNER_BINDINGS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.specification import (
    FROZEN_FORMULA_REPOSITORY_DISPOSITIONS,
    FROZEN_NAMED_OUTPUT_CONTRACTS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    ST12B_AGENT_CONSUMER_DAG,
    ST12B_AGENT_IDS,
    ST12B_OPERATION_CAPABILITY_BY_ID,
    validate_tranche_b_frozen_manifest,
)
from tools.build_qku_computation_control_plane import build_payload


def test_exact_frozen_manifest_is_complete() -> None:
    report = validate_tranche_b_frozen_manifest()

    assert report.passed
    assert len(report.checks) == 14
    assert all(check.passed for check in report.checks)


def test_formula_identity_and_successor_ownership_is_preserved() -> None:
    dispositions = Counter(
        row.disposition
        for row in FROZEN_FORMULA_REPOSITORY_DISPOSITIONS.values()
    )

    assert dispositions == {
        "REUSE_EXISTING_EXACT_VERSION": 10,
        "REGISTER_SEMANTIC_SUCCESSOR": 9,
        "NEW_TRANCHE_B_IMPLEMENTATION": 11,
    }
    assert len(IMPLEMENTATION_REGISTRY) == 30
    assert len(PREDECESSOR_IMPLEMENTATION_REGISTRY) == 19
    assert len(IMPLEMENTATION_VERSION_REGISTRY) == 39
    for math_id, disposition in FROZEN_FORMULA_REPOSITORY_DISPOSITIONS.items():
        active = IMPLEMENTATION_REGISTRY[math_id]
        assert active.contract.implementation_id == disposition.implementation_target
        if disposition.disposition == "REUSE_EXISTING_EXACT_VERSION":
            predecessor = PREDECESSOR_IMPLEMENTATION_REGISTRY[math_id]
            assert active.contract is predecessor.contract
            assert active.callable is predecessor.callable
        elif disposition.disposition == "REGISTER_SEMANTIC_SUCCESSOR":
            predecessor = PREDECESSOR_IMPLEMENTATION_REGISTRY[math_id]
            assert predecessor.contract.implementation_id in (
                IMPLEMENTATION_VERSION_REGISTRY
            )
            assert active.contract.implementation_id != (
                predecessor.contract.implementation_id
            )
        else:
            assert math_id not in PREDECESSOR_IMPLEMENTATION_REGISTRY


def test_input_parameter_and_terminal_consumer_ownership_is_exact() -> None:
    assert len(FORMULA_INPUT_AUTHORITY_BINDINGS) == 142
    assert len(CUMULATIVE_PARAMETER_POLICIES) == 479
    assert len(INCREMENTAL_TRANCHE_B_PARAMETER_POLICIES) == 344
    assert len(RUNTIME_PARAMETER_OWNER_BINDINGS) == 190
    assert len(OPTIMIZER_DEFAULT_CURRENTIZATIONS) == 479
    assert set(CUMULATIVE_PARAMETER_POLICIES) == set(
        OPTIMIZER_DEFAULT_CURRENTIZATIONS
    )
    assert len(NUMERIC_VALUE_AUTHORITY_BINDINGS) == 621
    assert Counter(
        row.subject_kind for row in NUMERIC_VALUE_AUTHORITY_BINDINGS.values()
    ) == {"PARAMETER": 479, "FORMULA_INPUT": 142}

    application_ids = set()
    ultimate_ids = set()
    for parameter_id, row in CUMULATIVE_PARAMETER_POLICIES.items():
        assert row.application_binding_id == f"PAB::{parameter_id}"
        assert row.ultimate_binding_id == f"PUCB::{parameter_id}"
        assert (
            row.ultimate_consumer["generic_compiler_is_sole_terminal_consumer"]
            is False
        )
        application_ids.add(row.application_binding_id)
        ultimate_ids.add(row.ultimate_binding_id)
    assert len(application_ids) == len(ultimate_ids) == 479


def test_agent_and_operation_rosters_are_closed_without_effect_authority() -> None:
    assert ST12B_AGENT_IDS == (
        "research_agent",
        "parameter_selector_agent",
        "risk_manager_agent",
        "quantum_optimizer_agent",
        "commander_agent",
        "governance_agent",
        "dashboard_agent",
        "connector_venue_readiness_future_consumer",
    )
    assert len(ST12B_AGENT_CONSUMER_DAG) == 1351
    assert not any(row.orphan_state for row in ST12B_AGENT_CONSUMER_DAG)
    assert {
        row.responsible_agent for row in ST12B_AGENT_CONSUMER_DAG
    } <= set(ST12B_AGENT_IDS)
    assert Counter(ST12B_OPERATION_CAPABILITY_BY_ID.values()) == {
        OperationCapabilityClass.PURE_DETERMINISTIC_COMPUTATION: 8,
        OperationCapabilityClass.READ_ONLY_PROJECTION: 2,
        OperationCapabilityClass.NO_EFFECT_RECORD: 2,
        OperationCapabilityClass.CONTRACT_DEFINITION_ONLY: 3,
    }


def test_build_envelope_reports_frozen_v34_without_changing_tranche_a() -> None:
    payload = build_payload()
    tranche_b = payload["tranche_b"]

    assert payload["implementation_count"] == 19
    assert payload["parameter_count"] == 135
    assert payload["runtime_effect_authorized"] is False
    assert tranche_b["implementation_count"] == 30
    assert tranche_b["implementation_version_count"] == 39
    assert tranche_b["named_output_contract_count"] == 30
    assert tranche_b["named_output_member_count"] == sum(
        len(row.members) for row in FROZEN_NAMED_OUTPUT_CONTRACTS.values()
    ) == 130
    assert tranche_b["primary_source_count"] == len(PRIMARY_SOURCE_REGISTRY) == 55
    assert tranche_b["numeric_value_authority_count"] == 621
    assert tranche_b["agent_consumer_route_count"] == 1351
    assert tranche_b["manifest_passed"] is True
    assert tranche_b["runtime_effect_authorized"] is False
