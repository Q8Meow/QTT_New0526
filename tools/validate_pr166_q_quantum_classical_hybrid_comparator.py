#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr166_q_quantum_classical_hybrid_comparator.validator import validate_artifacts  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    result = validate_artifacts(Path(args.repo_root).resolve())
    if result.ok:
        print("PR166_Q_QUANTUM_CLASSICAL_HYBRID_COMPARATOR_VALIDATION_OK")
        return 0
    for failure in result.failures:
        print(f"PR166_Q_QUANTUM_CLASSICAL_HYBRID_COMPARATOR_VALIDATION_FAIL {failure}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
