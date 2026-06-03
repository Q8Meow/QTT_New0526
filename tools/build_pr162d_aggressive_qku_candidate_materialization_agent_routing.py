#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.aggressive_qku_candidate_materialization_agent_routing.report_builder import (  # noqa: E402
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    artifacts = write_artifacts(Path(args.repo_root).resolve())
    summary = artifacts.summary
    print("PR162D_AGGRESSIVE_QKU_CANDIDATE_MATERIALIZATION_AGENT_ROUTING")
    print(f"candidate_materialization_target_count={summary['candidate_materialization_target_count']}")
    print(f"generic_required_fields_blocker_remaining_count={summary['generic_required_fields_blocker_remaining_count']}")
    print(f"candidate_field_fill_progress_count={summary['candidate_field_fill_progress_count']}")
    print(f"candidate_formula_algorithm_value_expansion_count={summary['candidate_formula_algorithm_value_expansion_count']}")
    print(f"replay_paper_candidate_route_count={summary['replay_paper_candidate_route_count']}")
    print(f"qku_to_agent_route_count={summary['qku_to_agent_route_count']}")
    print(f"quantum_problem_model_count={summary['quantum_problem_model_count']}")
    print(f"local_exact_qubo_smoke_execution_count={summary['local_exact_qubo_smoke_execution_count']}")
    print(f"local_exact_ising_smoke_execution_count={summary['local_exact_ising_smoke_execution_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
