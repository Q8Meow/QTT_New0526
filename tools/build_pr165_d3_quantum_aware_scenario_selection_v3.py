"""Build PR165-D3 quantum-aware scenario selection v3 artifacts."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build PR165-D3 generated reports, shards, and schemas.")
    parser.add_argument("--repo-root", default=".", type=Path)
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    sys.path.insert(0, str(repo_root))
    from src.qtt.stage1_prediction_markets.pr165_d3_quantum_aware_scenario_selection_v3.report_writer import write_artifacts

    artifacts = write_artifacts(repo_root)
    print(
        {
            "roadmap_pr_id": artifacts.summary["roadmap_pr_id"],
            "selected_combination_rows": artifacts.summary["selected_combination_rows"],
            "quantum_comparator_rows": artifacts.summary["quantum_comparator_rows"],
            "generated_shard_count": artifacts.summary["generated_shard_count"],
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
