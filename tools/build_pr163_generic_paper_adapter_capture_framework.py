#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr163_generic_paper_adapter_capture_framework.report_builder import (  # noqa: E402
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    artifacts = write_artifacts(Path(args.repo_root).resolve())
    summary = artifacts.summary
    print("PR163_GENERIC_PAPER_ADAPTER_CAPTURE_FRAMEWORK_BUILT")
    for field in (
        "candidate_packet_universe_count",
        "paper_adapter_input_rows",
        "paper_decision_intent_rows",
        "paper_order_intent_rows",
        "paper_pretrade_receipt_rows",
        "paper_synthetic_fill_event_rows",
        "paper_capture_bundle_rows",
        "ledger_invariant_violation_count",
        "quantum_advisory_rows",
        "llm_future_handoff_exclusion_receipt_rows",
        "recommendation_next_step",
    ):
        print(f"{field}={summary[field]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
