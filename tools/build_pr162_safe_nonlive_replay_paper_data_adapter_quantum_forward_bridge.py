#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.nonlive_replay_paper_data_adapter_quantum_forward_bridge.report_builder import (
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    artifacts = write_artifacts(Path(args.repo_root).resolve())
    summary = artifacts.summary
    print("PR162_SAFE_NONLIVE_REPLAY_PAPER_DATA_ADAPTER_QUANTUM_FORWARD_BRIDGE")
    print(f"qkus_covered={summary['qkus_covered']}")
    print(f"quantum_applicable_qkus_covered={summary['quantum_applicable_qkus_covered']}")
    print(
        "real_nonlive_replay_artifact_candidates_produced="
        f"{summary['real_nonlive_replay_artifact_candidates_produced']}"
    )
    print(
        "real_nonlive_paper_artifact_candidates_produced="
        f"{summary['real_nonlive_paper_artifact_candidates_produced']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

