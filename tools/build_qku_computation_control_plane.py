#!/usr/bin/env python3
"""Build a deterministic, data-only summary of the Tranche-A contract plane."""

from __future__ import annotations

import argparse
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
    ST12B_AGENT_CONSUMER_DAG,
    ST12B_AGENT_IDS,
    ST12B_OPERATION_CAPABILITY_BY_ID,
    validate_tranche_b_frozen_manifest,
)


SUCCESS_MARKER = "QKU_COMPUTATION_CONTROL_PLANE_BUILD_VALIDATED"


def build_payload() -> dict[str, object]:
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
    text = deterministic_json(build_payload()) + "\n"
    if args.output:
        try:
            output = resolve_output_path(args.output)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8", newline="\n")
    else:
        print(text, end="")
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
