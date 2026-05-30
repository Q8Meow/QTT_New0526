#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.qku_candidate_quality_replay_paper_prioritization.report_builder import (
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    artifacts = write_artifacts(Path(args.repo_root).resolve())
    summary = artifacts.summary
    print("PR161D_QKU_CANDIDATE_QUALITY_REPLAY_PAPER_PRIORITIZATION")
    print(f"qkus_scored_count={summary['qkus_scored_count']}")
    print(f"category_ranking_records_created={summary['category_ranking_records_created']}")
    print(f"scenario_outcome_matrix_records_created={summary['scenario_outcome_matrix_records_created']}")
    print(f"qku_bundle_candidate_records_created={summary['qku_bundle_candidate_records_created']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
