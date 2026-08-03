"""Compact manifest, lineage, identity, and capability-reference matrix."""

from __future__ import annotations

from collections import Counter
import json

import pytest

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (
    ACTIVATION_STATE,
    IDENTITY_MAPPING_UNMAPPED,
    NO_TRADE_REOPTIMIZATION_VARIABLE_IDS,
    ST12E_BINDING_EXACT,
    ST12E_BINDING_OUTSIDE_SCOPE,
    UPSTREAM_IDENTITY_CROSSWALK_REQUIRED,
    UPSTREAM_IDENTITY_FULLY_MAPPED,
    AgentIdentityMappingTypeV1,
    build_upstream_source_universe_registry,
    canonical_master_parameter_rows,
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
    resolve_st12e_value_policy_refs,
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


def _manifest() -> dict[str, object]:
    return json.loads(
        (ARTIFACT_DIR / "manifest.json").read_text(encoding="utf-8")
    )


def test_manifest_owns_exact_semantic_and_identity_denominators() -> None:
    manifest = _manifest()
    policy_rows = _jsonl("policy.jsonl")
    scope_rows = _jsonl("parameter_scope.jsonl")
    row_counts = Counter(str(row["row_type"]) for row in policy_rows)
    counts = manifest["counts"]

    assert counts == {
        "closure_controls": 23,
        "repository_dispositions": 9,
        "parameter_bindings": 87,
        "math_specifications": 3,
        "independent_oracle_specifications": 3,
        "golden_vectors_and_invariants": 3,
        "semantic_test_rows": 26,
        "validation_commands": 6,
        "parameter_source_universe": 3810,
    }
    assert row_counts == {
        "CONTROL": 23,
        "IDENTITY_COMPATIBILITY": 25,
        "PARAMETER_CAPABILITY_BINDING": 87,
    }
    assert len(scope_rows) == manifest["parameter_scope_row_count"] == 3810
    assert manifest["source_identity_row_count"] == 25
    assert manifest["exact_mapping_count"] == 12
    assert manifest["unmapped_mapping_count"] == 13
    assert manifest["exact_upstream_source_universe_count"] == 67
    assert manifest["fully_mapped_upstream_row_count"] == 1721
    assert manifest["crosswalk_required_upstream_row_count"] == 2089
    assert manifest["exact_st12e_binding_count"] == 87
    assert manifest["outside_st12e_binding_scope_count"] == 3723
    assert manifest["st12e_rows_with_upstream_crosswalk_gap"] == 34
    assert manifest["st12e_rows_with_fully_mapped_upstream_lineage"] == 53
    assert manifest["quota_reassignment_count"] == 0
    assert manifest["nearest_universe_assignment_count"] == 0
    assert manifest["source_set_rewrite_count"] == 0
    assert manifest["value_policy_ref_resolution_count"] == 87
    assert manifest["duplicated_value_body_count"] == 0
    assert manifest["opaque_semantic_payload_count"] == 0
    assert "parameter_scope_distribution_is_aggregate_only" not in manifest
    assert manifest["runtime_effect_authorized"] is False
    assert manifest["activation_state"] == ACTIVATION_STATE
    assert not any(manifest["no_effect_authority_flags"].values())
    assert tuple(manifest["no_trade_reoptimization_variable_ids"]) == (
        NO_TRADE_REOPTIMIZATION_VARIABLE_IDS
    )


def test_compact_semantic_registry_preserves_23_closures_and_26_cases() -> None:
    closure_ids = tuple(str(row["closure_id"]) for row in ST12E_CLOSURE_ROWS)
    test_ids = tuple(str(row["test_id"]) for row in ST12E_SEMANTIC_TEST_ROWS)
    predicate_groups = {
        str(row["predicate_group"]) for row in ST12E_CLOSURE_ROWS
    }
    physical_paths = {
        str(row["currentized_physical_path"])
        for row in ST12E_SEMANTIC_TEST_ROWS
        if "tranche_e/" in str(row["currentized_physical_path"])
    }

    assert len(closure_ids) == len(set(closure_ids)) == 23
    assert len(test_ids) == len(set(test_ids)) == 26
    assert all(
        row["closure_id"] == f"ST12-CLOSURE::{row['control_id']}"
        and set(row)
        == {
            "closure_id",
            "control_id",
            "domain",
            "control_slug",
            "predicate_group",
            "semantic_owner",
            "validator_owner",
        }
        for row in ST12E_CLOSURE_ROWS
    )
    assert len(predicate_groups) > 1
    assert physical_paths == {
        "tests/stage1_prediction_markets/qku_computation_control_plane/"
        "tranche_e/test_policy_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/"
        "tranche_e/test_integration_matrix.py",
        "tests/stage1_prediction_markets/qku_computation_control_plane/"
        "tranche_e/test_adversarial_matrix.py",
    }
    assert all(row["st12e_closure_refs"] for row in ST12E_SEMANTIC_TEST_ROWS)


def test_exact_identity_map_covers_25_sources_with_typed_12_13_split() -> None:
    manifest = _manifest()
    identity_map = policy_store().snapshot.identity_map
    exact = {
        source_id
        for source_id, binding in identity_map.bindings.items()
        if binding.mapping_type is not AgentIdentityMappingTypeV1.UNMAPPED
    }
    unmapped = set(identity_map.bindings) - exact

    assert len(identity_map.bindings) == 25
    assert len(exact) == 12
    assert len(unmapped) == 13
    assert sorted(unmapped) == manifest["unmapped_source_agent_ids"]
    assert all(
        binding.terminal_mapping_state == IDENTITY_MAPPING_UNMAPPED
        and not binding.current_principal_refs
        and not binding.current_role_refs
        and not binding.current_duty_refs
        and not binding.current_scope
        and not binding.intersection_scope
        and binding.activation_state == ACTIVATION_STATE
        for source_id, binding in identity_map.bindings.items()
        if source_id in unmapped
    )
    for source_id in unmapped:
        assert identity_map.describe_for_lineage(source_id).source_agent_id == source_id
        with pytest.raises(AuthorityDeniedError) as captured:
            identity_map.require_current_authority_mapping(source_id)
        assert captured.value.reason_code is ReasonCode.SOURCE_AGENT_ID_UNMAPPED


def test_all_3810_upstream_source_sets_and_partial_mappings_are_preserved() -> None:
    manifest = _manifest()
    generated_rows = _jsonl("parameter_scope.jsonl")
    generated_by_id = {
        str(row["parameter_id"]): row for row in generated_rows
    }
    master_text = (
        repo_root() / "docs/master_plan/QTT_MasterPlan_Current.md"
    ).read_text(encoding="utf-8")
    master_rows = canonical_master_parameter_rows(master_text)
    universe_registry, universe_refs = build_upstream_source_universe_registry(
        master_rows
    )
    exact_map = policy_store().snapshot.identity_map

    assert len(master_rows) == len(generated_rows) == 3810
    assert len(universe_registry) == 67
    assert manifest["exact_upstream_source_universes"] == {
        ref: {
            "source_agent_ids": list(spec["source_agent_ids"]),
            "parameter_count": spec["parameter_count"],
        }
        for ref, spec in universe_registry.items()
    }
    for parameter_id, symbol, source_ids in master_rows:
        row = generated_by_id[parameter_id]
        assert row["parameter_symbol"] == symbol
        assert row["upstream_source_universe_ref"] == universe_refs[source_ids]
        assert (
            tuple(
                universe_registry[row["upstream_source_universe_ref"]][
                    "source_agent_ids"
                ]
            )
            == source_ids
        )
        expected_unmapped = tuple(
            source_id
            for source_id in source_ids
            if exact_map.describe_for_lineage(source_id).mapping_type
            is AgentIdentityMappingTypeV1.UNMAPPED
        )
        assert row["upstream_identity_mapping_state"] == (
            UPSTREAM_IDENTITY_CROSSWALK_REQUIRED
            if expected_unmapped
            else UPSTREAM_IDENTITY_FULLY_MAPPED
        )


def test_e_binding_state_is_orthogonal_and_value_refs_are_canonical() -> None:
    master_text = (
        repo_root() / "docs/master_plan/QTT_MasterPlan_Current.md"
    ).read_text(encoding="utf-8")
    master_identities = {
        parameter_id: symbol
        for parameter_id, symbol, _ in canonical_master_parameter_rows(
            master_text
        )
    }
    resolved = resolve_st12e_value_policy_refs(master_identities)
    scope = policy_store().snapshot.parameter_scope_rows
    exact_rows = {
        parameter_id: row
        for parameter_id, row in scope.items()
        if row.st12e_binding_state == ST12E_BINDING_EXACT
    }
    outside_rows = tuple(
        row
        for row in scope.values()
        if row.st12e_binding_state == ST12E_BINDING_OUTSIDE_SCOPE
    )
    exact_with_upstream_gap = tuple(
        row
        for row in exact_rows.values()
        if row.upstream_identity_mapping_state
        == UPSTREAM_IDENTITY_CROSSWALK_REQUIRED
    )

    assert set(exact_rows) == set(ST12E_PARAMETER_CAPABILITY_BINDINGS)
    assert len(exact_rows) == len(resolved) == 87
    assert len(outside_rows) == 3723
    assert len(exact_with_upstream_gap) == 34
    assert all(
        exact_rows[parameter_id].value_policy_ref == binding.value_policy_ref
        and exact_rows[
            parameter_id
        ].st12e_capability_binding_ref_or_explicit_absence
        == binding.capability_policy_ref
        and all(
            policy_store()
            .snapshot.identity_map.require_current_authority_mapping(source_id)
            .intersection_scope
            for source_id in binding.certified_source_agent_ids
        )
        for parameter_id, binding in ST12E_PARAMETER_CAPABILITY_BINDINGS.items()
    )


def test_e_policy_rows_are_reference_only_and_payloads_are_readable() -> None:
    policy_rows = tuple(
        row
        for row in _jsonl("policy.jsonl")
        if row["row_type"] == "PARAMETER_CAPABILITY_BINDING"
    )
    forbidden_value_fields = {
        "raw",
        "day1_seed_or_resolution_rule",
        "reference_range_or_structural_constraint",
        "bounded_search_space_or_fit_constraint",
        "unit_or_basis",
        "precision_and_rounding_policy",
        "runtime_resolution_procedure",
        "fallback_behavior_when_value_unavailable",
        "value_source_class",
        "source_state_refs",
    }
    validation_source = (
        repo_root()
        / "src/qtt/stage1_prediction_markets/qku_computation_control_plane/"
        "validation.py"
    ).read_text(encoding="utf-8")
    parameter_source = (
        repo_root()
        / "src/qtt/stage1_prediction_markets/qku_computation_control_plane/"
        "parameter_policy.py"
    ).read_text(encoding="utf-8")

    assert len(policy_rows) == 87
    assert all(not forbidden_value_fields.intersection(row) for row in policy_rows)
    assert all(
        set(binding.__dataclass_fields__)
        == {
            "parameter_id",
            "parameter_symbol",
            "certified_source_agent_ids",
            "value_policy_ref",
            "capability_policy_ref",
            "st12e_binding_state",
        }
        for binding in ST12E_PARAMETER_CAPABILITY_BINDINGS.values()
    )
    assert "_ST12E_SEMANTIC_ROWS_B64" not in validation_source
    assert "_ST12E_PARAMETER_CAPABILITY_ROWS_B64" not in parameter_source


def test_reused_math_and_certified_commands_remain_exact_no_effect_refs() -> None:
    manifest = _manifest()

    assert tuple(row[0] for row in ST12E_REUSED_MATH_PACK) == (
        "MATH-01",
        "MATH-13",
        "MATH-15",
    )
    assert tuple(manifest["repository_disposition_ids"]) == (
        ST12E_REPOSITORY_DISPOSITIONS
    )
    assert tuple(manifest["validation_commands"]) == ST12E_CERTIFIED_COMMANDS
    for math_id, oracle_id, vector_id, comparison_policy in ST12E_REUSED_MATH_PACK:
        assert IMPLEMENTATION_REGISTRY[math_id].contract.math_spec_id == math_id
        assert oracle_id == f"ORACLE::{math_id}"
        assert vector_id == f"GOLDEN::{math_id}"
        assert comparison_policy
