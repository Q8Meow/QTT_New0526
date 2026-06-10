#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.changed_area_validation_router import build_routing_policy_report
from tools.cross_platform_path_invariant import invariant_report_payload
from tools.validation_inventory import (
    inventory_counts,
    inventory_report_rows,
    validate_inventory,
)

SUCCESS_MARKER = "VALIDATION_INVENTORY_OK"
OBSERVED_PR207_MAIN_RUNTIME_SECONDS = 23 * 60 + 32
OBSERVED_PR207_MAIN_RUNTIME_SOURCE = (
    "gh run list --branch main --limit 5 reported QTT Validation run "
    "27248003677 as 23m32s at 2026-06-10T01:58:35Z"
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _summary_payload() -> dict[str, object]:
    counts = inventory_counts()
    return {
        **counts,
        "current_recent_main_runtime_seconds_if_available": (
            OBSERVED_PR207_MAIN_RUNTIME_SECONDS
        ),
        "current_recent_main_runtime_source": OBSERVED_PR207_MAIN_RUNTIME_SOURCE,
        "estimated_small_pr_runtime_seconds": None,
        "estimated_runtime_reduction_percent": None,
        "estimated_runtime_note": (
            "Exact reduced-mode timing is intentionally null until PR208 runs in "
            "GitHub CI on a non-infrastructure small pull request."
        ),
        "full_validation_runtime_expected_on_main": (
            "Full validation remains required on main push, schedule, workflow_dispatch "
            "full mode, and QTT_FORCE_FULL_VALIDATION=1."
        ),
        "force_full_override_supported": True,
        "fail_closed_unknown_change_supported": True,
        "cross_platform_path_invariant_supported": True,
        "pr152_currentization_decision_supported": True,
        "remaining_risks": [
            "Reduced-mode runtime is not measured until a future non-infrastructure PR exercises it in CI.",
            "Unknown non-generated changes intentionally force full validation.",
            "Generated reports without an owning validator fail closed.",
        ],
        "next_recommended_pr": (
            "After PR208 lands, observe one small non-infrastructure PR and tune "
            "owner globs only if a necessary validator is over- or under-routed."
        ),
    }


def _final_summary_payload() -> dict[str, object]:
    counts = inventory_counts()
    return {
        "pr_id": "PR208_CI_RUNTIME_RATIONALIZATION",
        "github_pr_expected_number": "NEXT_GITHUB_PR_AFTER_207_OR_ACTUAL",
        "qtt_roadmap_pr": False,
        "infrastructure_only": True,
        "trading_logic_changed": False,
        "validators_deleted_count": counts["validators_deleted_count"],
        "tests_deleted_count": counts["tests_deleted_count"],
        "pull_request_reduced_mode_enabled": True,
        "main_full_validation_preserved": True,
        "nightly_or_manual_full_validation_preserved": True,
        "force_full_override_supported": True,
        "cross_platform_path_invariant_supported": True,
        "pr152_currentization_decision": (
            "Required only when PR152-tracked generated reports, report counts, "
            "inventory, or currentization tooling changes."
        ),
        "local_validation_summary": {
            "status": "recorded in PR body after local validation completes",
            "required_commands": [
                "compileall",
                "validate_validation_inventory",
                "focused pytest suites",
                "fast-preflight phase",
                "deterministic-validators phase",
                "full run_validation_gates",
                "grand audit",
                "diff checks",
            ],
        },
        "remaining_risks": [
            "Reduced-mode timing awaits the first ordinary small PR after PR208.",
        ],
        "next_recommended_pr": (
            "Add empirical reduced-mode timing to PR208 reports after one small "
            "post-merge PR, without changing correctness routing."
        ),
    }


def write_pr208_reports(repo_root: Path) -> None:
    generated = repo_root / "docs" / "master_plan" / "generated"
    _write_json(
        generated / "PR208_ValidatorClassificationRegistry.report.json",
        {
            "validator_inventory_version": 1,
            "counts": inventory_counts(),
            "validators": inventory_report_rows(),
        },
    )
    _write_json(
        generated / "PR208_ChangedAreaRoutingPolicy.report.json",
        build_routing_policy_report(),
    )
    _write_json(
        generated / "PR208_CrossPlatformPathInvariant.report.json",
        invariant_report_payload(),
    )
    _write_json(
        generated / "PR208_CIRuntimeRationalizationSummary.report.json",
        _summary_payload(),
    )
    _write_json(
        generated / "PR208_FinalSummary.report.json",
        _final_summary_payload(),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--write-pr208-reports", action="store_true")
    args = parser.parse_args(argv)

    failures = validate_inventory()
    if failures:
        for failure in failures:
            print(failure)
        return 1
    if args.write_pr208_reports:
        write_pr208_reports(args.repo_root)
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
