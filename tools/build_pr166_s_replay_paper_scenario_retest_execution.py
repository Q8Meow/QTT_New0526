#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr166_s_replay_paper_scenario_retest_execution import paths as p  # noqa: E402
from src.qtt.stage1_prediction_markets.pr166_s_replay_paper_scenario_retest_execution.json_io import read_json  # noqa: E402
from src.qtt.stage1_prediction_markets.pr166_s_replay_paper_scenario_retest_execution.report_builder import write_artifacts  # noqa: E402


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
            print("PR166_S_REPLAY_PAPER_SCENARIO_RETEST_EXECUTION_IDEMPOTENCE_FAILED", file=sys.stderr)
            return 1
        print("PR166_S_REPLAY_PAPER_SCENARIO_RETEST_EXECUTION_IDEMPOTENT")
    summary = artifacts.summary
    print("PR166_S_REPLAY_PAPER_SCENARIO_RETEST_EXECUTION_BUILT")
    for field in (
        "selected_batch_consumption_rows",
        "replay_episode_rows",
        "paper_episode_rows",
        "order_intent_rows",
        "simulated_fill_rows",
        "execution_cost_rows",
        "result_attribution_rows",
        "score_refresh_candidate_rows",
        "memory_refresh_candidate_rows",
        "repair_feedback_route_rows",
        "quantum_advisory_passthrough_rows",
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
