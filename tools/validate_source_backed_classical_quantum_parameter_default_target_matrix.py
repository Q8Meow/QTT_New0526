#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence


_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.stage1_prediction_markets.source_backed_classical_quantum_parameter_default_target_matrix import (  # noqa: E402
    constants as c,
)
from src.qtt.stage1_prediction_markets.source_backed_classical_quantum_parameter_default_target_matrix.report import (  # noqa: E402
    validate_repository_artifacts,
    write_report_file,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional validation output path for a generated PR150 report copy.",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Opt-in tracked PR150 report regeneration.",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    if args.write_report:
        write_report_file(repo_root)

    failures = validate_repository_artifacts(
        repo_root,
        report_output_path=args.output,
        tracked_report_write_allowed=args.write_report,
    )
    if failures:
        for failure in failures:
            print(failure)
        return 1
    print(c.SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

