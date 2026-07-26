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


SUCCESS_MARKER = "QKU_COMPUTATION_CONTROL_PLANE_BUILD_VALIDATED"


def build_payload() -> dict[str, object]:
    """Return the centralized registry envelope without creating runtime state."""

    math_ids = tuple(IMPLEMENTATION_REGISTRY)
    manifest = build_tranche_a_coverage_manifest()
    return {
        "schema": "QKUComputationControlPlaneBuildV1",
        "contract_only": True,
        "runtime_effect_authorized": False,
        "implementation_ids": list(math_ids),
        "implementation_count": len(math_ids),
        "parameter_count": len(PARAMETER_POLICIES),
        "oracle_count": len(ORACLE_BY_MATH_ID),
        "golden_vector_count": len(GOLDEN_VECTOR_BY_MATH_ID),
        "certified_source_state_count": len(CERTIFIED_SOURCE_STATES),
        "source_overlay_count": len(SOURCE_CURRENTIZATION_OVERLAYS),
        "source_claim_binding_rule_count": len(SOURCE_CLAIM_BINDING_RULES),
        "coverage_manifest_schema": "TrancheACoverageManifestV1",
        "executed_coverage_rows": dict(manifest.executed_counts),
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
