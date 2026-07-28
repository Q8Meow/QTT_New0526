#!/usr/bin/env python3
"""Build a deterministic, data-only summary of the Tranche-A contract plane."""

from __future__ import annotations

import argparse
from collections import Counter
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
    STEP12_PARAMETER_POLICIES,
    TRANCHE_B_CLOSURE_ROWS,
    TRANCHE_B_MATH_SPECIFICATIONS,
    TRANCHE_B_REPOSITORY_DISPOSITIONS,
    TRANCHE_B_TEST_ROWS,
    TRANCHE_B_VALIDATION_COMMANDS,
    build_tranche_a_coverage_manifest,
    build_tranche_b_coverage_manifest,
    deterministic_json,
    validate_relative_path,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.bindings import (  # noqa: E402
    TRANCHE_A_SOURCE_CLAIM_BINDING_RULES,
    TRANCHE_B_SOURCE_CLAIM_BINDING_RULES,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.implementation_registry import (  # noqa: E402
    TRANCHE_A_MATH_IDS,
    TRANCHE_B_MATH_IDS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.oracle_contracts import (  # noqa: E402
    TRANCHE_A_ORACLE_PACK,
    TRANCHE_B_ORACLE_COVERAGE_ROWS,
)
from src.qtt.stage1_prediction_markets.qku_computation_control_plane.parameter_policy import (  # noqa: E402
    TRANCHE_A_PARAMETER_POLICIES,
    TRANCHE_B_PARAMETER_POLICIES,
)


SUCCESS_MARKER = "QKU_COMPUTATION_CONTROL_PLANE_BUILD_VALIDATED"


def build_payload() -> dict[str, object]:
    """Return the centralized registry envelope without creating runtime state."""

    math_ids = tuple(TRANCHE_A_MATH_IDS)
    manifest = build_tranche_a_coverage_manifest()
    tranche_b_manifest = build_tranche_b_coverage_manifest()
    b_domain_counts = Counter(
        row.domain for row in TRANCHE_B_CLOSURE_ROWS
    )
    a_math = set(TRANCHE_A_MATH_IDS)
    b_math = set(TRANCHE_B_MATH_IDS)
    a_sources = {
        row.binding_rule_id
        for row in TRANCHE_A_SOURCE_CLAIM_BINDING_RULES
    }
    b_sources = {
        row.binding_rule_id
        for row in TRANCHE_B_SOURCE_CLAIM_BINDING_RULES
    }
    return {
        "schema": "QKUComputationControlPlaneBuildV1",
        "contract_only": True,
        "runtime_effect_authorized": False,
        "implementation_ids": list(math_ids),
        "implementation_count": len(math_ids),
        "parameter_count": len(PARAMETER_POLICIES),
        "oracle_count": len(TRANCHE_A_ORACLE_PACK),
        "golden_vector_count": len(TRANCHE_A_ORACLE_PACK),
        "certified_source_state_count": len(CERTIFIED_SOURCE_STATES),
        "source_overlay_count": len(SOURCE_CURRENTIZATION_OVERLAYS),
        "source_claim_binding_rule_count": len(
            TRANCHE_A_SOURCE_CLAIM_BINDING_RULES
        ),
        "coverage_manifest_schema": "TrancheACoverageManifestV1",
        "executed_coverage_rows": dict(manifest.executed_counts),
        "tranche_b": {
            "schema": "TrancheBCoverageManifestV1",
            "closure_rows": len(TRANCHE_B_CLOSURE_ROWS),
            "closure_domain_counts": dict(sorted(b_domain_counts.items())),
            "repository_dispositions": len(
                TRANCHE_B_REPOSITORY_DISPOSITIONS
            ),
            "parameter_policy_rows": len(TRANCHE_B_PARAMETER_POLICIES),
            "mathematical_specifications": len(
                TRANCHE_B_MATH_SPECIFICATIONS
            ),
            "implementation_identity_rows": len(TRANCHE_B_MATH_IDS),
            "new_implementation_identity_rows": len(b_math - a_math),
            "independent_oracle_specifications": len(
                TRANCHE_B_ORACLE_COVERAGE_ROWS
            ),
            "golden_vectors_and_invariants": len(
                TRANCHE_B_ORACLE_COVERAGE_ROWS
            ),
            "test_rows": len(TRANCHE_B_TEST_ROWS),
            "validation_command_rows": len(
                TRANCHE_B_VALIDATION_COMMANDS
            ),
            "validation_commands": [
                row.command for row in TRANCHE_B_VALIDATION_COMMANDS
            ],
            "source_claim_binding_rules": len(
                TRANCHE_B_SOURCE_CLAIM_BINDING_RULES
            ),
            "executed_coverage_rows": dict(
                tranche_b_manifest.executed_counts
            ),
            "derived_predicates": dict(
                tranche_b_manifest.derived_predicates
            ),
        },
        "step12_cumulative": {
            "derivation": (
                "IMMUTABLE_TRANCHE_A_AND_TRANCHE_B_MANIFEST_UNION"
            ),
            "parameter_policy_rows": len(STEP12_PARAMETER_POLICIES),
            "math_implementation_identities": len(
                set(IMPLEMENTATION_REGISTRY)
            ),
            "math_identity_overlap": len(a_math & b_math),
            "independent_oracle_identities": len(ORACLE_BY_MATH_ID),
            "golden_vector_identities": len(GOLDEN_VECTOR_BY_MATH_ID),
            "source_claim_binding_rule_identities": len(
                SOURCE_CLAIM_BINDING_RULES
            ),
            "source_rule_overlap": len(a_sources & b_sources),
            "tranche_a_coverage_rows": manifest.executed_counts[
                "total_rows"
            ],
            "tranche_b_coverage_rows": tranche_b_manifest.executed_counts[
                "total_rows"
            ],
            "tranche_a_parameter_rows": len(
                TRANCHE_A_PARAMETER_POLICIES
            ),
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
