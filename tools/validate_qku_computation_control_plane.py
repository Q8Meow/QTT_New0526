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
    compare_golden_vector,
    compare_st12c_golden_vector,
    validate_domain,
)


DOMAIN_MATH_IDS = {
    "accounting": tuple(f"MATH-{value:02d}" for value in range(26, 37)),
    "agent": (),
    "architecture": tuple(f"MATH-{value:02d}" for value in range(1, 16)),
    "execution": ("MATH-37", "MATH-38"),
    "llm": (),
    "latency": (),
    "operations": (),
    "quantum": ("MATH-46", "MATH-47", "MATH-48", "MATH-49"),
    "security": (),
    "source": (),
}
SUCCESS_MARKER = "QKU_COMPUTATION_CONTROL_PLANE_VALIDATED"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", choices=tuple(DOMAIN_MATH_IDS), required=True)
    args = parser.parse_args()
    report = validate_domain(args.domain)
    comparator = (
        compare_st12c_golden_vector
        if args.domain in {"accounting", "execution"}
        else compare_golden_vector
    )
    failed_vectors = [
        math_id
        for math_id in DOMAIN_MATH_IDS[args.domain]
        if not comparator(math_id)
    ]
    if failed_vectors:
        print(
            f"{args.domain}: golden-vector failures: {failed_vectors}",
            file=sys.stderr,
        )
        return 1
    print(
        f"{SUCCESS_MARKER} domain={args.domain} "
        f"contract_checks={len(report.checks)} "
        f"golden_vectors={len(DOMAIN_MATH_IDS[args.domain])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
