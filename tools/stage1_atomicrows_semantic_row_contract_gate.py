#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.stage1_prediction_markets.atomicrows_semantic_contract import (  # noqa: E402
    constants as c,
)
from src.qtt.stage1_prediction_markets.atomicrows_semantic_contract.fixtures import (  # noqa: E402
    write_fixture_file,
)
from src.qtt.stage1_prediction_markets.atomicrows_semantic_contract.report import (  # noqa: E402
    write_report_files,
)
from src.qtt.stage1_prediction_markets.atomicrows_semantic_contract.schema import (  # noqa: E402
    json_dump,
)
from src.qtt.stage1_prediction_markets.atomicrows_semantic_contract.validator import (  # noqa: E402
    validate_report_payload,
    validate_repository_artifacts,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--write-report", type=Path, default=None)
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    outputs = write_report_files(repo_root)
    write_fixture_file(repo_root)
    if args.write_report is not None and args.write_report != c.REPORT_PATH:
        report_path = repo_root / args.write_report
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json_dump(outputs["report"]),
            encoding="utf-8",
            newline="\n",
        )

    failures = validate_repository_artifacts(repo_root)
    outcome = validate_report_payload(
        outputs["report"],
        repo_root=repo_root,
        enforce_environment=True,
        enforce_protected_diff=True,
    )
    failures.extend(outcome.failures)
    unique_failures = tuple(sorted(set(failures)))
    if unique_failures:
        for failure in unique_failures:
            print(failure)
        return 1
    for receipt in outcome.receipts:
        print(receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

