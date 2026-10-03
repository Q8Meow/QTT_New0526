#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr166_qb_bounded_quantum_benchmark.validator import validate_artifacts  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    from contextlib import nullcontext
    import os
    from tools.validation_reliability import (
        _mapper_read_profile_for_process_v1, _mapper_bound_reads_v1, RUN_ID_ENV,
    )
    selected_root = Path(args.repo_root).resolve()
    binding = None
    if os.environ.get(RUN_ID_ENV) or any(k.upper().startswith("QTT_MAPPER_") for k in os.environ):
        _, binding = _mapper_read_profile_for_process_v1(selected_root,
            environment=os.environ, actual_argv=tuple(sys.orig_argv), role="PARENT")
    with nullcontext() if binding is None else _mapper_bound_reads_v1(binding):
        result = validate_artifacts(selected_root)
    if result.ok:
        print("PR166_QB_BOUNDED_QUANTUM_BENCHMARK_VALIDATION_OK")
        return 0
    for failure in result.failures:
        print(f"PR166_QB_BOUNDED_QUANTUM_BENCHMARK_VALIDATION_FAIL {failure}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
