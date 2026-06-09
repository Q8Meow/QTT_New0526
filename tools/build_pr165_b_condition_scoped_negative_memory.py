#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr165_b_condition_scoped_negative_memory import paths as p  # noqa: E402
from src.qtt.stage1_prediction_markets.pr165_b_condition_scoped_negative_memory.json_io import read_json  # noqa: E402
from src.qtt.stage1_prediction_markets.pr165_b_condition_scoped_negative_memory.report_builder import write_artifacts  # noqa: E402


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
            print("PR165_B_CONDITION_SCOPED_NEGATIVE_MEMORY_IDEMPOTENCE_FAILED", file=sys.stderr)
            return 1
        print("PR165_B_CONDITION_SCOPED_NEGATIVE_MEMORY_IDEMPOTENT")
    summary = artifacts.summary
    print("PR165_B_CONDITION_SCOPED_NEGATIVE_MEMORY_BUILT")
    for field in (
        "memory_candidate_rows",
        "condition_fingerprint_rows",
        "combination_fingerprint_rows",
        "scenario_outcome_rows",
        "negative_memory_rows",
        "positive_memory_rows",
        "fragile_memory_rows",
        "quantum_negative_memory_rows",
        "external_candidate_records_created",
        "exact_next_recommended_PR",
    ):
        print(f"{field}={summary[field]}")
    return 0


def _snapshot_outputs(repo_root: Path) -> dict[str, bytes]:
    paths: list[Path] = []
    for filename in p.REPORT_FILENAMES:
        root = repo_root / p.GENERATED_DIR / filename
        paths.append(root)
        payload = read_json(root)
        for shard in payload.get("shard_files") or []:
            paths.append(p.resolve_repo_relative(repo_root, shard))
    for filename in p.SCHEMA_FILENAMES:
        paths.append(repo_root / p.SCHEMA_DIR / filename)
    return {path.relative_to(repo_root).as_posix(): path.read_bytes() for path in sorted(paths)}


if __name__ == "__main__":
    raise SystemExit(main())
