"""Manifest-driven ST12-E policy, LLM, and parameter matrix checks."""

from __future__ import annotations

from collections import Counter
import json

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (
    ACTIVATION_STATE,
    CURRENT_DUTY_REF,
    CURRENT_ROSTER_REF,
    LLM_ADVISORY_TASK_FIELDS,
    NO_TRADE_REOPTIMIZATION_VARIABLE_IDS,
    PARAMETER_MAPPING_BLOCKED,
    PARAMETER_MAPPING_EXACT,
    PARAMETER_MAPPING_BLOCKER_REF,
    QUANTUM_FORMULATION_FIELDS,
    SOURCE_UNIVERSE_DEFINITIONS,
    AgentIdentityCompatibilityMapV1,
    AgentIdentityMappingTypeV1,
    AgentPrincipalBindingV1,
    no_effect_authority_is_closed,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.errors import (
    AuthorityDeniedError,
    ReasonCode,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (
    IMPLEMENTATION_REGISTRY,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (
    ST12E_PARAMETER_CAPABILITY_BINDINGS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (
    ST12E_CERTIFIED_COMMANDS,
    ST12E_CLOSURE_ROWS,
    ST12E_REPOSITORY_DISPOSITIONS,
    ST12E_REUSED_MATH_PACK,
    ST12E_SEMANTIC_TEST_ROWS,
)

from . import policy_store, repo_root


ARTIFACT_DIR = (
    repo_root()
    / "docs/master_plan/generated/qku_control_plane/agent_capability"
)


def _jsonl(name: str) -> tuple[dict[str, object], ...]:
    return tuple(
        json.loads(line)
        for line in (ARTIFACT_DIR / name)
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    )


def test_manifest_is_the_single_denominator_owner() -> None:
    manifest = json.loads(
        (ARTIFACT_DIR / "manifest.json").read_text(encoding="utf-8")
    )
    policy_rows = _jsonl("policy.jsonl")
    scope_rows = _jsonl("parameter_scope.jsonl")
    row_counts = Counter(str(row["row_type"]) for row in policy_rows)
    counts = manifest["counts"]

    assert counts["closure_controls"] == row_counts["CONTROL"]
    assert counts["parameter_bindings"] == row_counts[
        "PARAMETER_CAPABILITY_BINDING"
    ]
    assert counts["parameter_source_universe"] == len(scope_rows)
    exact_scope_rows = tuple(
        row for row in scope_rows if row["mapping_state"] == PARAMETER_MAPPING_EXACT
    )
    blocked_scope_rows = tuple(
        row for row in scope_rows if row["mapping_state"] == PARAMETER_MAPPING_BLOCKED
    )
    assert len(exact_scope_rows) == counts["parameter_bindings"]
    assert len(blocked_scope_rows) == len(scope_rows) - len(exact_scope_rows)
    assert manifest["parameter_scope_eligible_count"] == len(exact_scope_rows)
    assert manifest["parameter_scope_blocker_count"] == len(blocked_scope_rows)
    assert manifest["parameter_scope_distribution_is_aggregate_only"] is True
    assert {
        str(row["parameter_id"]) for row in exact_scope_rows
    } == set(ST12E_PARAMETER_CAPABILITY_BINDINGS)
    assert all(
        row["current_principal_refs_or_gap"] == [PARAMETER_MAPPING_BLOCKER_REF]
        and row["terminal_route"]
        == "SOURCE_UNIVERSE_PER_ROW_CURRENTIZATION_REVIEW_REQUIRED"
        for row in blocked_scope_rows
    )
    assert counts["repository_dispositions"] == len(
        manifest["repository_disposition_ids"]
    )
    assert counts["semantic_test_rows"] == len(manifest["semantic_test_ids"])
    assert counts["validation_commands"] == len(
        manifest["validation_commands"]
    )
    assert counts["math_specifications"] == len(
        manifest["reused_math_oracle_vector_refs"]
    )
    assert counts["independent_oracle_specifications"] == counts[
        "math_specifications"
    ]
    assert counts["golden_vectors_and_invariants"] == counts[
        "math_specifications"
    ]
    assert manifest["runtime_effect_authorized"] is False
    assert manifest["activation_state"] == ACTIVATION_STATE
    assert not any(manifest["no_effect_authority_flags"].values())
    assert tuple(manifest["no_trade_reoptimization_variable_ids"]) == (
        NO_TRADE_REOPTIMIZATION_VARIABLE_IDS
    )
    assert tuple(manifest["quantum_formulation_required_fields"]) == (
        QUANTUM_FORMULATION_FIELDS
    )
    assert tuple(manifest["llm_advisory_task_fields"]) == (
        LLM_ADVISORY_TASK_FIELDS
    )


@pytest.mark.parametrize(
    "row", ST12E_CLOSURE_ROWS, ids=lambda row: str(row["control_id"])
)
def test_all_closure_controls_are_typed_no_effect_rows(
    row: dict[str, object],
) -> None:
    expected_group = {
        "agent": {
            "test_policy_matrix.py",
            "test_integration_matrix.py",
            "test_adversarial_matrix.py",
        },
        "llm": {"test_policy_matrix.py", "test_adversarial_matrix.py"},
        "security": {"test_adversarial_matrix.py"},
    }
    assert row["closure_id"] == f"ST12-CLOSURE::{row['control_id']}"
    assert row["capability_binding_owner"] == "AgentCapabilityResolverV1"
    assert row["runtime_effect_authorized"] is False
    assert row["reason_codes"]
    assert any(
        str(row["currentized_test_group"]).endswith(filename)
        for filename in expected_group[str(row["domain"])]
    )


@pytest.mark.parametrize(
    "row", ST12E_SEMANTIC_TEST_ROWS, ids=lambda row: str(row["test_id"])
)
def test_all_semantic_cases_use_the_three_matrices_or_thin_wrappers(
    row: dict[str, object],
) -> None:
    path = str(row["currentized_physical_path"])
    allowed_matrix_suffixes = (
        "tranche_e/test_policy_matrix.py",
        "tranche_e/test_integration_matrix.py",
        "tranche_e/test_adversarial_matrix.py",
    )
    allowed_wrapper_suffixes = (
        "independent_validate_qku_computation_control_plane_agent.py",
        "independent_validate_qku_computation_control_plane_llm.py",
        "independent_validate_qku_computation_control_plane_security.py",
    )
    assert path.endswith(allowed_matrix_suffixes + allowed_wrapper_suffixes)
    assert row["independent_expected_value_required"] is True
    assert row["production_expected_value_import_allowed"] is False
    assert row["st12e_closure_refs"]


@pytest.mark.parametrize(
    "binding",
    ST12E_PARAMETER_CAPABILITY_BINDINGS.values(),
    ids=lambda binding: binding.parameter_id,
)
def test_all_e_parameter_rows_bind_capability_without_mutating_values(
    binding,
) -> None:
    row = binding.raw
    identity_map = policy_store().snapshot.identity_map

    assert row["capability_binding_owner"] == "AgentCapabilityResolverV1"
    assert row["underlying_value_semantics_owner"].endswith(
        "ComputationParameterPolicyV1"
    )
    assert row["formula_or_qku_mutation_authorized_by_st12e"] is False
    assert row["value_mutation_authorized_by_st12e"] is False
    assert row["no_trade_fallback_preserved"] is True
    assert row["missing_stale_invalid_behavior"]
    assert row["runtime_resolution_procedure"]
    for source_agent_id in binding.certified_source_agent_ids:
        assert identity_map.resolve(source_agent_id).intersection_scope


def test_source_universes_are_distinct_and_exactly_projected() -> None:
    manifest = json.loads(
        (ARTIFACT_DIR / "manifest.json").read_text(encoding="utf-8")
    )
    rows = _jsonl("parameter_scope.jsonl")
    actual = Counter(str(row["source_universe_id"]) for row in rows)
    expected = {
        universe_id: int(spec["parameter_count"])
        for universe_id, spec in manifest[
            "source_universe_definitions"
        ].items()
    }
    source_slices = {
        tuple(spec["source_agent_ids"])
        for spec in manifest["source_universe_definitions"].values()
    }

    assert actual == expected
    assert len(source_slices) == len(SOURCE_UNIVERSE_DEFINITIONS)
    assert sum(actual.values()) == manifest["counts"][
        "parameter_source_universe"
    ]


def test_explicit_unmapped_identity_is_representable_but_never_resolves() -> None:
    binding = AgentPrincipalBindingV1(
        source_agent_id="AGENT_NL_99",
        source_role_label="Certified Source Gap",
        mapping_type=AgentIdentityMappingTypeV1.UNMAPPED,
        current_principal_refs=(),
        current_role_refs=(),
        current_duty_refs=(),
        source_scope=("route",),
        current_scope=(),
        intersection_scope=(),
        evidence_refs=("SOURCE_UNIVERSE_MAPPING_GAP::AGENT_NL_99",),
        terminal_mapping_state="UNMAPPED_FAIL_CLOSED",
    )
    compatibility = AgentIdentityCompatibilityMapV1(
        {binding.source_agent_id: binding}
    )

    with pytest.raises(AuthorityDeniedError) as captured:
        compatibility.resolve(binding.source_agent_id)
    assert captured.value.reason_code is ReasonCode.SOURCE_AGENT_ID_UNMAPPED


def test_existing_math_oracle_vector_owners_are_reused_unchanged() -> None:
    assert tuple(row[0] for row in ST12E_REUSED_MATH_PACK) == (
        "MATH-01",
        "MATH-13",
        "MATH-15",
    )
    for math_id, oracle_id, vector_id, comparison_policy in (
        ST12E_REUSED_MATH_PACK
    ):
        assert IMPLEMENTATION_REGISTRY[math_id].contract.math_spec_id == math_id
        assert oracle_id == f"ORACLE::{math_id}"
        assert vector_id == f"GOLDEN::{math_id}"
        assert comparison_policy
    assert no_effect_authority_is_closed()


def test_manifest_lists_the_certified_dispositions_and_commands() -> None:
    manifest = json.loads(
        (ARTIFACT_DIR / "manifest.json").read_text(encoding="utf-8")
    )
    roster_rows = json.loads(
        (repo_root() / CURRENT_ROSTER_REF).read_text(encoding="utf-8")
    )["records"]
    duty_rows = json.loads(
        (repo_root() / CURRENT_DUTY_REF).read_text(encoding="utf-8")
    )["records"]
    roster_by_id = {row["agent_id"]: row for row in roster_rows}
    duty_by_id = {row["agent_id"]: row for row in duty_rows}
    assert tuple(manifest["repository_disposition_ids"]) == (
        ST12E_REPOSITORY_DISPOSITIONS
    )
    assert tuple(manifest["validation_commands"]) == ST12E_CERTIFIED_COMMANDS
    assert len(policy_store().snapshot.identity_map.bindings) == manifest[
        "identity_mapping_count"
    ]
    for binding in policy_store().snapshot.identity_map.bindings.values():
        assert binding.current_principal_refs
        assert binding.current_role_refs == binding.current_duty_refs
        assert binding.current_scope == binding.intersection_scope
        for principal_id in binding.current_principal_refs:
            assert (
                f"{CURRENT_ROSTER_REF}::{roster_by_id[principal_id]['row_id']}"
                in binding.evidence_refs
            )
            assert (
                f"{CURRENT_DUTY_REF}::{duty_by_id[principal_id]['row_id']}"
                in binding.evidence_refs
            )
