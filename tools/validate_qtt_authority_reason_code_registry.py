#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.qtt_authority_reason_code_registry import (  # noqa: E402
    AUTHORITY_BOUNDARY_CODES,
    GAP_REASON_CODES,
    NEGATIVE_RECOVERY_REASON_CODES,
    PRETRADE_DECISION_REASON_CODES,
    get_authority_boundary_code,
    get_gap_reason_code,
    get_negative_recovery_reason_code,
    get_pretrade_decision_reason_code,
)

SUCCESS_MARKER = "QTT_AUTHORITY_REASON_CODE_REGISTRY_OK"


def main() -> int:
    failures: list[str] = []
    for code in AUTHORITY_BOUNDARY_CODES:
        if not get_authority_boundary_code(code):
            failures.append(f"AUTHORITY_LOOKUP_EMPTY:{code}")
    for code in GAP_REASON_CODES:
        if not get_gap_reason_code(code):
            failures.append(f"GAP_LOOKUP_EMPTY:{code}")
    for code in NEGATIVE_RECOVERY_REASON_CODES:
        if not get_negative_recovery_reason_code(code):
            failures.append(f"NEGATIVE_LOOKUP_EMPTY:{code}")
    for code in PRETRADE_DECISION_REASON_CODES:
        if not get_pretrade_decision_reason_code(code):
            failures.append(f"PRETRADE_LOOKUP_EMPTY:{code}")

    for required in [
        "NO_LIVE_ORDER_AUTHORITY",
        "NO_CONNECTOR_TRUTH_OR_BINDING",
        "NO_SOURCE_TRUTH_AUTHORITY",
        "MISSING_NUMERIC_INPUTS",
        "MISSING_DEFAULT_THRESHOLD",
        "formula_inputs_missing",
        "no_trade_candidate_dominates",
        "FUTURE_LIVE_GATE_REQUIRED",
    ]:
        if required not in set().union(
            AUTHORITY_BOUNDARY_CODES,
            GAP_REASON_CODES,
            NEGATIVE_RECOVERY_REASON_CODES,
            PRETRADE_DECISION_REASON_CODES,
        ):
            failures.append(f"REQUIRED_CODE_MISSING:{required}")

    if AUTHORITY_BOUNDARY_CODES["NO_CONNECTOR_TRUTH_OR_BINDING"].get("connector_semantic_binding_state") != "NOT_BOUND_CANDIDATE_ONLY":
        failures.append("CONNECTOR_BOUNDARY_STATE_MISMATCH")

    if failures:
        print("\n".join(failures))
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
