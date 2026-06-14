#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr166_sm2_score_memory_refresh_v2 import constants as c  # noqa: E402
from src.qtt.stage1_prediction_markets.pr166_sm2_score_memory_refresh_v2.io import read_json, resolve_repo_relative  # noqa: E402
from src.qtt.stage1_prediction_markets.pr166_sm2_score_memory_refresh_v2.report_writer import write_artifacts  # noqa: E402


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
            print("PR166_SM2_SCORE_MEMORY_REFRESH_V2_IDEMPOTENCE_FAILED", file=sys.stderr)
            return 1
        print("PR166_SM2_SCORE_MEMORY_REFRESH_V2_IDEMPOTENT")
    summary = artifacts.summary
    print("PR166_SM2_SCORE_MEMORY_REFRESH_V2_BUILT")
    for field in (
        "pr166_s2_pr166_sm2_handoff_rows_consumed",
        "positive_replay_paper_rows_consumed",
        "negative_replay_paper_rows_consumed",
        "all_negative_conversion_plan_rows",
        "positive_expansion_rows",
        "pr166_q_handoff_rows",
        "next_recommended_pr",
        "secondary_next_recommended_pr",
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
    for filename in c.SCHEMA_FILENAMES:
        paths.append(repo_root / c.SCHEMA_DIR / filename)
    return {path.relative_to(repo_root).as_posix(): path.read_bytes() for path in sorted(paths)}


if __name__ == "__main__":
    raise SystemExit(main())
