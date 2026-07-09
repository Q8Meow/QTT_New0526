#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import validate_pr169_val1 as validator  # noqa: E402

SUCCESS_MARKER = "QTT_PR169_VAL1_BUILD_OK"


def build(repo_root: Path) -> None:
    report_dir = repo_root / validator.REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)
    payloads = validator.build_report_payloads(repo_root)
    for name in validator.REQUIRED_REPORT_NAMES:
        path = report_dir / name
        path.write_text(
            json.dumps(payloads[name], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    build(repo_root)
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
