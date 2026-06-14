#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr166_sf_r2_targeted_conversion_repair_retest import constants as c  # noqa: E402
from src.qtt.stage1_prediction_markets.pr166_sf_r2_targeted_conversion_repair_retest.io import read_json, resolve_repo_relative  # noqa: E402
from src.qtt.stage1_prediction_markets.pr166_sf_r2_targeted_conversion_repair_retest.report_writer import write_artifacts  # noqa: E402


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
            print("PR166_SF_R2_TARGETED_CONVERSION_REPAIR_RETEST_IDEMPOTENCE_FAILED", file=sys.stderr)
            return 1
        print("PR166_SF_R2_TARGETED_CONVERSION_REPAIR_RETEST_IDEMPOTENT")
    summary = artifacts.summary
    print("PR166_SF_R2_TARGETED_CONVERSION_REPAIR_RETEST_BUILT")
    for field in (
        "pr166_sm2_handoff_rows",
        "all_negative_conversion_plan_rows",
        "repaired_candidate_packet_rows",
        "retested_rows",
        "converted_positive_rows",
        "still_negative_rows",
        "no_fill_rows",
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
