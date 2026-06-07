#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation import paths as p  # noqa: E402
from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.json_io import read_json  # noqa: E402
from src.qtt.stage1_prediction_markets.pr163_c_pretrade_infrastructure_rejection_remediation.report_builder import write_artifacts  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--verify-idempotent", action="store_true")
    args = parser.parse_args()
    repo_root = Path(args.repo_root).resolve()
    artifacts = write_artifacts(repo_root)
    if args.verify_idempotent:
        before = _snapshot_pr163c_outputs(repo_root)
        artifacts = write_artifacts(repo_root)
        after = _snapshot_pr163c_outputs(repo_root)
        if before != after:
            print("PR163_C_PRETRADE_INFRA_REPAIR_IDEMPOTENCE_FAILED", file=sys.stderr)
            return 1
        print("PR163_C_PRETRADE_INFRA_REPAIR_IDEMPOTENT")
    summary = artifacts.summary
    print("PR163_C_PRETRADE_INFRASTRUCTURE_REJECTION_REMEDIATION_BUILT")
    for field in (
        "pr164_pr163c_trigger_rows_consumed",
        "artificial_rejections_repaired",
        "valid_rejection_force_pass_count",
        "pr162d_r3_misroute_count",
        "repair_action_catalog_rows",
        "repair_formula_registry_rows",
        "repair_test_vector_rows",
        "candidate_value_imputation_rows",
        "counterfactual_repair_evaluation_rows",
        "pr165_ready_before_pr163c",
        "pr165_ready_after_pr163c",
        "pr165_blocked_before_pr163c",
        "pr165_blocked_after_pr163c",
    ):
        print(f"{field}={summary[field]}")
    return 0


def _snapshot_pr163c_outputs(repo_root: Path) -> dict[str, bytes]:
    paths: list[Path] = []
    for filename in p.REPORT_FILENAMES:
        report_path = repo_root / p.GENERATED_DIR / filename
        paths.append(report_path)
        payload = read_json(report_path)
        for shard in payload.get("shard_files") or []:
            paths.append(p.resolve_repo_relative(repo_root, shard))
    for filename in p.SCHEMA_FILENAMES:
        paths.append(repo_root / p.SCHEMA_DIR / filename)
    return {path.relative_to(repo_root).as_posix(): path.read_bytes() for path in sorted(paths)}


if __name__ == "__main__":
    raise SystemExit(main())
