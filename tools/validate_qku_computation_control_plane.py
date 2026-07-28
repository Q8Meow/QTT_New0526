#!/usr/bin/env python3
"""Primary domain-dispatched validator for the centralized contract plane."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.qku_computation_control_plane.validation import (  # noqa: E402
    build_tranche_a_coverage_manifest,
    build_tranche_b_coverage_manifest,
    compare_golden_vector,
    validate_domain,
    validate_tranche_b_domain,
)


DOMAIN_MATH_IDS = {
    "architecture": tuple(f"MATH-{value:02d}" for value in range(1, 16)),
    "latency": (),
    "model_risk": (
        *(f"MATH-{value:02d}" for value in range(1, 26)),
        "MATH-36",
    ),
    "operations": (),
    "quantum": ("MATH-46", "MATH-47", "MATH-48", "MATH-49"),
    "security": (),
    "source": (),
}
A_DOMAINS = frozenset(
    {"architecture", "operations", "quantum", "security", "source"}
)
B_DOMAINS = frozenset(
    {"latency", "model_risk", "operations", "quantum", "security", "source"}
)
SUCCESS_MARKER = "QKU_COMPUTATION_CONTROL_PLANE_VALIDATED"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", choices=tuple(DOMAIN_MATH_IDS), required=True)
    args = parser.parse_args()
    reports = []
    if args.domain in A_DOMAINS:
        reports.append(validate_domain(args.domain))
    if args.domain in B_DOMAINS:
        reports.append(validate_tranche_b_domain(args.domain))
    tranche_a_manifest = build_tranche_a_coverage_manifest()
    tranche_b_manifest = (
        None
        if args.domain == "architecture"
        else build_tranche_b_coverage_manifest()
    )
    failed_vectors = [
        math_id
        for math_id in DOMAIN_MATH_IDS[args.domain]
        if not compare_golden_vector(math_id)
    ]
    if failed_vectors:
        print(
            f"{args.domain}: golden-vector failures: {failed_vectors}",
            file=sys.stderr,
        )
        return 1
    contract_checks = sum(len(report.checks) for report in reports)
    manifest_rows = tranche_a_manifest.executed_counts["total_rows"] + (
        0
        if tranche_b_manifest is None
        else tranche_b_manifest.executed_counts["total_rows"]
    )
    print(
        f"{SUCCESS_MARKER} domain={args.domain} "
        f"contract_checks={contract_checks} "
        f"golden_vectors={len(DOMAIN_MATH_IDS[args.domain])} "
        f"manifest_rows={manifest_rows}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
