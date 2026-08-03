#!/usr/bin/env python3
"""Build a deterministic, data-only summary of the Tranche-A contract plane."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.qku_computation_control_plane import (  # noqa: E402
    CERTIFIED_SOURCE_STATES,
    GOLDEN_VECTOR_BY_MATH_ID,
    IMPLEMENTATION_REGISTRY,
    ORACLE_BY_MATH_ID,
    PARAMETER_POLICIES,
    APPEND_ONLY_TABLES_V1,
    ST12C_CONTROL_COVERAGE_MATRIX,
    ST12C_GOLDEN_VECTOR_BY_MATH_ID,
    ST12C_LATER_PHASE_BLOCKERS,
    ST12C_PRODUCTION_MODULE_PATHS,
    ST12C_ORACLE_BY_MATH_ID,
    TRANCHE_C_IMPLEMENTATION_REGISTRY,
    TRANCHE_C_PARAMETER_APPLICATION_BINDINGS,
    TRANCHE_C_PARAMETER_POLICIES,
    SOURCE_CLAIM_BINDING_RULES,
    SOURCE_CURRENTIZATION_OVERLAYS,
    build_tranche_a_coverage_manifest,
    deterministic_json,
    validate_relative_path,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (  # noqa: E402
    IMPLEMENTATION_VERSION_REGISTRY,
    PREDECESSOR_IMPLEMENTATION_REGISTRY,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (  # noqa: E402
    FORMULA_INPUT_AUTHORITY_BINDINGS,
    FROZEN_ONLINE_CURRENTIZATION_RECEIPTS,
    NUMERIC_VALUE_AUTHORITY_BINDINGS,
    PRIMARY_SOURCE_REGISTRY,
    SOURCE_CONFLICT_RESOLUTIONS,
    SOURCE_CURRENTIZATION_REGISTRY,
    SOURCE_POPULATION_COUNTS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.dependency_graph import (  # noqa: E402
    FROZEN_DEPENDENCY_RELATIONSHIPS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.models import (  # noqa: E402
    OperationCapabilityClass,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.oracle_contracts import (  # noqa: E402
    ST12B_PROPERTY_TESTS,
    ST12B_VECTOR_PACK,
    TRANCHE_A_GOLDEN_VECTOR_BY_MATH_ID,
    TRANCHE_A_ORACLE_BY_MATH_ID,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (  # noqa: E402
    CUMULATIVE_PARAMETER_POLICIES,
    INCREMENTAL_TRANCHE_B_PARAMETER_POLICIES,
    OPTIMIZER_DEFAULT_CURRENTIZATIONS,
    RUNTIME_PARAMETER_OWNER_BINDINGS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.quantum_adapter import (  # noqa: E402
    QUANTUM_STRUCTURAL_READINESS_BY_MATH_ID,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.specification import (  # noqa: E402
    FROZEN_FORMULA_REPOSITORY_DISPOSITIONS,
    FROZEN_NAMED_OUTPUT_CONTRACTS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.stack_resolver import (  # noqa: E402
    REGISTERED_FORMULA_STACKS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (  # noqa: E402
    ST12E_CERTIFIED_COMMANDS,
    ST12E_CLOSURE_ROWS,
    ST12E_REPOSITORY_DISPOSITIONS,
    ST12E_REUSED_MATH_PACK,
    ST12E_SEMANTIC_TEST_ROWS,
    ST12B_AGENT_CONSUMER_DAG,
    ST12B_AGENT_IDS,
    ST12B_OPERATION_CAPABILITY_BY_ID,
    validate_tranche_b_frozen_manifest,
    st12e_semantic_counts,
)
from src.qtt.agents.pr169_agent_orch1_resolvers import AgentOrchService  # noqa: E402
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.agent_policy import (  # noqa: E402
    ACTIVATION_STATE,
    AGENT_ORCH_PREFIX,
    CENTRAL_VALIDATOR_REF,
    HELD_OPERATION_IDS,
    IMPLEMENTED_OPERATION_IDS,
    NO_EFFECT_PROFILE_REF,
    NO_TRADE_REOPTIMIZATION_VARIABLE_IDS,
    OWNER_ACTION_IDS,
    POLICY_VERSION,
    QUANTUM_FORMULATION_FIELDS,
    LLM_ADVISORY_TASK_FIELDS,
    ST12E_BINDING_EXACT,
    ST12E_BINDING_OUTSIDE_SCOPE,
    UPSTREAM_IDENTITY_CROSSWALK_REQUIRED,
    UPSTREAM_IDENTITY_FULLY_MAPPED,
    AgentIdentityMappingTypeV1,
    build_generated_policy_rows,
    build_identity_compatibility_map,
    build_parameter_scope_projection,
    build_st12e_certified_source_universe_registry,
    build_upstream_source_universe_registry,
    canonical_master_parameter_rows,
    canonical_parameter_identity_registry,
    canonical_source_agent_ids,
    canonical_source_role_labels,
    current_owner_action_ids,
    no_effect_authority_is_closed,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (  # noqa: E402
    resolve_st12e_value_policy_refs,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.authority import (  # noqa: E402
    TRANCHE_A_AUTHORITY,
)


SUCCESS_MARKER = "QKU_COMPUTATION_CONTROL_PLANE_BUILD_VALIDATED"
ST12E_GENERATED_PREFIX = Path(
    "docs/master_plan/generated/qku_control_plane/agent_capability"
)
ST12EProjectionSet = tuple[
    dict[str, object],
    tuple[dict[str, object], ...],
    tuple[dict[str, object], ...],
]


def build_st12e_projections() -> ST12EProjectionSet:
    """Build all E outputs in memory from frozen canonical owners."""

    master_text = (
        REPO_ROOT / "docs/master_plan/QTT_MasterPlan_Current.md"
    ).read_text(encoding="utf-8")
    master_rows = canonical_master_parameter_rows(master_text)
    source_agent_ids = canonical_source_agent_ids(master_text)
    orch_snapshot = AgentOrchService(repo_root=REPO_ROOT).load_policy_snapshot()
    identity_map = build_identity_compatibility_map(
        orch_snapshot,
        source_agent_ids=source_agent_ids,
        source_role_labels=canonical_source_role_labels(master_text),
    )
    parameter_scope = build_parameter_scope_projection(
        master_plan_text=master_text,
        identity_map=identity_map,
    )
    policy_rows = build_generated_policy_rows(
        control_rows=ST12E_CLOSURE_ROWS,
        identity_map=identity_map,
    )
    scope_rows = tuple(
        {
            name: getattr(row, name)
            for name in row.__dataclass_fields__
        }
        for row in parameter_scope
    )
    counts = dict(st12e_semantic_counts())
    upstream_universes, _ = build_upstream_source_universe_registry(master_rows)
    st12e_universes, _ = build_st12e_certified_source_universe_registry()
    exact_mappings = tuple(
        binding
        for binding in identity_map.bindings.values()
        if binding.mapping_type is not AgentIdentityMappingTypeV1.UNMAPPED
    )
    unmapped_mappings = tuple(
        binding
        for binding in identity_map.bindings.values()
        if binding.mapping_type is AgentIdentityMappingTypeV1.UNMAPPED
    )
    fully_mapped_scope = tuple(
        row
        for row in parameter_scope
        if row.upstream_identity_mapping_state
        == UPSTREAM_IDENTITY_FULLY_MAPPED
    )
    crosswalk_required_scope = tuple(
        row
        for row in parameter_scope
        if row.upstream_identity_mapping_state
        == UPSTREAM_IDENTITY_CROSSWALK_REQUIRED
    )
    exact_e_scope = tuple(
        row
        for row in parameter_scope
        if row.st12e_binding_state == ST12E_BINDING_EXACT
    )
    outside_e_scope = tuple(
        row
        for row in parameter_scope
        if row.st12e_binding_state == ST12E_BINDING_OUTSIDE_SCOPE
    )
    e_scope_with_gap = sum(
        row.upstream_identity_mapping_state
        == UPSTREAM_IDENTITY_CROSSWALK_REQUIRED
        for row in exact_e_scope
    )
    resolved_value_refs = resolve_st12e_value_policy_refs(
        canonical_parameter_identity_registry(master_text)
    )
    manifest: dict[str, object] = {
        "schema": "AgentCapabilityPolicyManifestV1",
        "policy_version": POLICY_VERSION,
        "registry_version": orch_snapshot.manifest_version,
        "semantic_owner": "QKUComputationControlPlaneV1",
        "implementation_owner": "AgentCapabilityResolverV1",
        "parameter_value_owner": "ComputationParameterPolicyV1",
        "agent_orchestration_owner": "AGENT-ORCH1",
        "owner_action_owner": "OwnerActionRegistry",
        "final_release_owner": "ExecutionRouterV1",
        "activation_state": ACTIVATION_STATE,
        "no_effect_profile_ref": NO_EFFECT_PROFILE_REF,
        "no_effect_authority_flags": {
            name: getattr(TRANCHE_A_AUTHORITY, name)
            for name in TRANCHE_A_AUTHORITY.__dataclass_fields__
        },
        "runtime_effect_authorized": False,
        "manual_edit_allowed": False,
        "counts": counts,
        "policy_row_count": len(policy_rows),
        "identity_mapping_count": len(identity_map.bindings),
        "source_identity_row_count": len(identity_map.bindings),
        "exact_mapping_count": len(exact_mappings),
        "unmapped_mapping_count": len(unmapped_mappings),
        "unmapped_source_agent_ids": [
            binding.source_agent_id for binding in unmapped_mappings
        ],
        "parameter_scope_row_count": len(scope_rows),
        "exact_upstream_source_universe_count": len(upstream_universes),
        "exact_upstream_source_agent_id_count": len(source_agent_ids),
        "fully_mapped_upstream_row_count": len(fully_mapped_scope),
        "crosswalk_required_upstream_row_count": len(
            crosswalk_required_scope
        ),
        "exact_st12e_binding_count": len(exact_e_scope),
        "outside_st12e_binding_scope_count": len(outside_e_scope),
        "exact_st12e_certified_mapping_count": len(exact_e_scope),
        "st12e_binding_with_unmapped_certified_id_count": 0,
        "st12e_rows_with_upstream_crosswalk_gap": e_scope_with_gap,
        "st12e_rows_with_fully_mapped_upstream_lineage": (
            len(exact_e_scope) - e_scope_with_gap
        ),
        "quota_reassignment_count": 0,
        "nearest_universe_assignment_count": 0,
        "source_set_rewrite_count": 0,
        "value_policy_ref_resolution_count": len(resolved_value_refs),
        "duplicated_value_body_count": 0,
        "opaque_semantic_payload_count": 0,
        "exact_upstream_source_universes": {
            universe_ref: {
                "source_agent_ids": list(specification["source_agent_ids"]),
                "parameter_count": specification["parameter_count"],
            }
            for universe_ref, specification in upstream_universes.items()
        },
        "st12e_certified_source_universes": {
            universe_ref: {
                "source_agent_ids": list(specification["source_agent_ids"]),
                "parameter_count": specification["parameter_count"],
                "authority_created": False,
            }
            for universe_ref, specification in st12e_universes.items()
        },
        "closure_ids": [row["closure_id"] for row in ST12E_CLOSURE_ROWS],
        "repository_disposition_ids": list(ST12E_REPOSITORY_DISPOSITIONS),
        "reused_math_oracle_vector_refs": [
            list(row) for row in ST12E_REUSED_MATH_PACK
        ],
        "semantic_test_ids": [
            row["test_id"] for row in ST12E_SEMANTIC_TEST_ROWS
        ],
        "validation_commands": list(ST12E_CERTIFIED_COMMANDS),
        "owner_action_ids": list(current_owner_action_ids()),
        "implemented_operation_ids": list(IMPLEMENTED_OPERATION_IDS),
        "held_operation_ids": list(HELD_OPERATION_IDS),
        "no_trade_reoptimization_variable_ids": list(
            NO_TRADE_REOPTIMIZATION_VARIABLE_IDS
        ),
        "quantum_formulation_required_fields": list(
            QUANTUM_FORMULATION_FIELDS
        ),
        "llm_advisory_task_fields": list(LLM_ADVISORY_TASK_FIELDS),
        "agent_orch_source_prefix": AGENT_ORCH_PREFIX,
        "central_validator_ref": CENTRAL_VALIDATOR_REF,
        "identity_join_state": "EXACT_OR_TYPED_UNMAPPED_NO_AUTHORITY",
        "qku_formula_mutation_authorized": False,
        "trade_plan_candidate_is_only_mutable_optimization_object": True,
        "no_trade_reoptimization_route_preserved": True,
        "memory_is_condition_scoped_prior_only": True,
        "llm_inference_allowed": False,
        "quantum_mapping_or_execution_allowed": False,
        "raw_jsonl_request_time_scan_allowed": False,
        "no_effect_authority_closed": no_effect_authority_is_closed(),
        "terminal_route": "NO_EFFECT_ELIGIBILITY_OR_TYPED_DENIAL",
    }
    return manifest, policy_rows, scope_rows


def _jsonl(rows: tuple[dict[str, object], ...]) -> str:
    return "".join(deterministic_json(row) + "\n" for row in rows)


def materialize_st12e_projections(
    manifest: dict[str, object],
    policy_rows: tuple[dict[str, object], ...],
    scope_rows: tuple[dict[str, object], ...],
) -> None:
    output_dir = REPO_ROOT / ST12E_GENERATED_PREFIX
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(
        deterministic_json(manifest) + "\n", encoding="utf-8", newline="\n"
    )
    (output_dir / "policy.jsonl").write_text(
        _jsonl(policy_rows), encoding="utf-8", newline="\n"
    )
    (output_dir / "parameter_scope.jsonl").write_text(
        _jsonl(scope_rows), encoding="utf-8", newline="\n"
    )


def build_payload(
    st12e_projections: ST12EProjectionSet | None = None,
) -> dict[str, object]:
    """Return the centralized registry envelope without creating runtime state."""

    math_ids = tuple(PREDECESSOR_IMPLEMENTATION_REGISTRY)
    manifest = build_tranche_a_coverage_manifest()
    tranche_b_manifest = validate_tranche_b_frozen_manifest()
    dispositions = tuple(
        row.disposition
        for row in FROZEN_FORMULA_REPOSITORY_DISPOSITIONS.values()
    )
    operation_capabilities = tuple(
        ST12B_OPERATION_CAPABILITY_BY_ID.values()
    )
    output_member_count = sum(
        len(contract.members)
        for contract in FROZEN_NAMED_OUTPUT_CONTRACTS.values()
    )
    st12e_manifest, st12e_policy, st12e_scope = (
        st12e_projections or build_st12e_projections()
    )
    return {
        "schema": "QKUComputationControlPlaneBuildV1",
        "contract_only": True,
        "runtime_effect_authorized": False,
        "implementation_ids": list(math_ids),
        "implementation_count": len(math_ids),
        "parameter_count": len(PARAMETER_POLICIES),
        "oracle_count": len(TRANCHE_A_ORACLE_BY_MATH_ID),
        "golden_vector_count": len(TRANCHE_A_GOLDEN_VECTOR_BY_MATH_ID),
        "certified_source_state_count": len(CERTIFIED_SOURCE_STATES),
        "source_overlay_count": len(SOURCE_CURRENTIZATION_OVERLAYS),
        "source_claim_binding_rule_count": len(SOURCE_CLAIM_BINDING_RULES),
        "coverage_manifest_schema": "TrancheACoverageManifestV1",
        "executed_coverage_rows": dict(manifest.executed_counts),
        "tranche_e": {
            "schema": st12e_manifest["schema"],
            "policy_version": st12e_manifest["policy_version"],
            "contract_only": True,
            "runtime_effect_authorized": False,
            "semantic_counts": st12e_manifest["counts"],
            "policy_row_count": len(st12e_policy),
            "parameter_scope_row_count": len(st12e_scope),
            "identity_mapping_count": st12e_manifest[
                "identity_mapping_count"
            ],
            "no_effect_authority_closed": st12e_manifest[
                "no_effect_authority_closed"
            ],
        },
        "tranche_c": {
            "schema": "ST12C_DETERMINISTIC_RECEIPTS_PERSISTENCE_ACCOUNTING_AND_TRANSACTIONS_V1",
            "contract_only": True,
            "runtime_effect_authorized": False,
            "control_matrix_count": len(ST12C_CONTROL_COVERAGE_MATRIX),
            "accounting_control_count": sum(row.domain == "accounting" for row in ST12C_CONTROL_COVERAGE_MATRIX),
            "execution_control_count": sum(row.domain == "execution" for row in ST12C_CONTROL_COVERAGE_MATRIX),
            "repository_disposition_count": len(ST12C_PRODUCTION_MODULE_PATHS),
            "parameter_policy_count": len(TRANCHE_C_PARAMETER_POLICIES),
            "parameter_application_binding_count": len(TRANCHE_C_PARAMETER_APPLICATION_BINDINGS),
            "math_implementation_count": len(TRANCHE_C_IMPLEMENTATION_REGISTRY),
            "independent_oracle_count": len(ST12C_ORACLE_BY_MATH_ID),
            "golden_vector_or_invariant_count": len(ST12C_GOLDEN_VECTOR_BY_MATH_ID),
            "semantic_test_denominator": len(ST12C_CONTROL_COVERAGE_MATRIX) + 2,
            "validation_command_count": 4,
            "later_phase_blocker_count": len(ST12C_LATER_PHASE_BLOCKERS),
            "production_persistence_selected": False,
            "outbox_dispatcher_implemented": False,
            "public_operation_additions": 0,
        },
        "tranche_b": {
            "schema": "ST12B_FROZEN_IMPLEMENTATION_SPEC_V3_4",
            "contract_only": True,
            "runtime_effect_authorized": False,
            "implementation_ids": list(IMPLEMENTATION_REGISTRY),
            "implementation_count": len(IMPLEMENTATION_REGISTRY),
            "implementation_version_count": len(
                IMPLEMENTATION_VERSION_REGISTRY
            ),
            "reused_implementation_count": dispositions.count(
                "REUSE_EXISTING_EXACT_VERSION"
            ),
            "semantic_successor_count": dispositions.count(
                "REGISTER_SEMANTIC_SUCCESSOR"
            ),
            "new_implementation_count": dispositions.count(
                "NEW_TRANCHE_B_IMPLEMENTATION"
            ),
            "named_output_contract_count": len(
                FROZEN_NAMED_OUTPUT_CONTRACTS
            ),
            "named_output_member_count": output_member_count,
            "formula_input_owner_count": len(
                FORMULA_INPUT_AUTHORITY_BINDINGS
            ),
            "parameter_count": len(CUMULATIVE_PARAMETER_POLICIES),
            "incremental_parameter_count": len(
                INCREMENTAL_TRANCHE_B_PARAMETER_POLICIES
            ),
            "runtime_parameter_owner_count": len(
                RUNTIME_PARAMETER_OWNER_BINDINGS
            ),
            "optimizer_default_currentization_count": len(
                OPTIMIZER_DEFAULT_CURRENTIZATIONS
            ),
            "primary_source_count": len(PRIMARY_SOURCE_REGISTRY),
            "primary_source_class_counts": dict(SOURCE_POPULATION_COUNTS),
            "source_conflict_resolution_count": len(
                SOURCE_CONFLICT_RESOLUTIONS
            ),
            "source_currentization_count": len(
                SOURCE_CURRENTIZATION_REGISTRY
            ),
            "frozen_online_currentization_count": len(
                FROZEN_ONLINE_CURRENTIZATION_RECEIPTS
            ),
            "numeric_value_authority_count": len(
                NUMERIC_VALUE_AUTHORITY_BINDINGS
            ),
            "dependency_relationship_count": len(
                FROZEN_DEPENDENCY_RELATIONSHIPS
            ),
            "registered_stack_count": len(REGISTERED_FORMULA_STACKS),
            "oracle_count": len(ORACLE_BY_MATH_ID),
            "vector_count": len(ST12B_VECTOR_PACK),
            "property_count": len(ST12B_PROPERTY_TESTS),
            "quantum_structural_readiness_count": len(
                QUANTUM_STRUCTURAL_READINESS_BY_MATH_ID
            ),
            "central_service_operation_count": len(
                ST12B_OPERATION_CAPABILITY_BY_ID
            ),
            "pure_deterministic_operation_count": operation_capabilities.count(
                OperationCapabilityClass.PURE_DETERMINISTIC_COMPUTATION
            ),
            "read_only_operation_count": operation_capabilities.count(
                OperationCapabilityClass.READ_ONLY_PROJECTION
            ),
            "no_effect_operation_count": operation_capabilities.count(
                OperationCapabilityClass.NO_EFFECT_RECORD
            ),
            "held_operation_count": operation_capabilities.count(
                OperationCapabilityClass.CONTRACT_DEFINITION_ONLY
            ),
            "agent_identity_count": len(ST12B_AGENT_IDS),
            "agent_consumer_route_count": len(ST12B_AGENT_CONSUMER_DAG),
            "manifest_passed": tranche_b_manifest.passed,
        },
    }


def resolve_output_path(value: str) -> Path:
    relative = validate_relative_path(value)
    output = (REPO_ROOT / relative).resolve()
    temporary_root = (REPO_ROOT / ".tmp").resolve()
    try:
        output.relative_to(temporary_root)
    except ValueError as exc:
        raise ValueError("output must remain below repository .tmp") from exc
    if output == temporary_root:
        raise ValueError("output must name a file below repository .tmp")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        help="Optional JSON path below the repository .tmp directory.",
    )
    args = parser.parse_args()
    st12e_projections = build_st12e_projections()
    text = deterministic_json(build_payload(st12e_projections)) + "\n"
    if args.output:
        try:
            output = resolve_output_path(args.output)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8", newline="\n")
        materialize_st12e_projections(*st12e_projections)
    else:
        print(text, end="")
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
