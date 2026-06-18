#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr167_open_trade_simulator_integration import constants as c  # noqa: E402
from src.qtt.stage1_prediction_markets.pr167_open_trade_simulator_integration.io import read_json, resolve_repo_relative  # noqa: E402
from src.qtt.stage1_prediction_markets.pr167_open_trade_simulator_integration.report_writer import write_artifacts  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--verify-idempotent", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    artifacts = write_artifacts(repo_root)
    if args.verify_idempotent:
        before = _snapshot_outputs(repo_root)
        artifacts = write_artifacts(repo_root)
        after = _snapshot_outputs(repo_root)
        if before != after:
            print("PR167_OPEN_TRADE_SIMULATOR_IDEMPOTENCE_FAILED", file=sys.stderr)
            return 1
        print("PR167_OPEN_TRADE_SIMULATOR_IDEMPOTENT")

    summary = artifacts.summary
    print("PR167_OPEN_TRADE_SIMULATOR_BUILT")
    for field in (
        "consumed_pr167_handoff_rows",
        "pr166_qc_open_trade_sim_handoff_count",
        "actual_sim_subset_count",
        "simulator_disposition_counts",
        "simulator_quality_grade_counts",
        "simulator_survivor_count",
        "simulator_failure_count",
        "forbidden_authority_counts_all_zero_flag",
    ):
        print(f"{field}={summary[field]}")
    return 0


def _snapshot_outputs(repo_root: Path) -> dict[str, bytes]:
    paths: list[Path] = []
    for filename in c.REPORT_FILENAMES:
        root = repo_root / c.GENERATED_DIR / filename
        paths.append(root)
        payload = read_json(root)
        for shard in payload.get("shard_files") or []:
            paths.append(resolve_repo_relative(repo_root, shard))
    for schema in sorted((repo_root / c.SCHEMA_DIR).glob("*.schema.json")):
        paths.append(schema)
    return {path.relative_to(repo_root).as_posix(): path.read_bytes() for path in sorted(paths)}


if __name__ == "__main__":
    raise SystemExit(main())
