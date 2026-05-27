#!/usr/bin/env python3
"""Validate PR155 agent-consumable parameter default registry."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence


_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.stage1_prediction_markets.agent_consumable_parameter_default_registry import (  # noqa: E402
    constants as c,
)
from src.qtt.stage1_prediction_markets.agent_consumable_parameter_default_registry.validator import (  # noqa: E402
    validate_repository_artifacts,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Opt-in tracked PR155 registry/report regeneration.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate without writing generated artifacts.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Run strict deterministic and forbidden-output checks.",
    )
    args = parser.parse_args(argv)

    failures = validate_repository_artifacts(
        args.repo_root.resolve(),
        write_report=args.write_report,
        check_only=args.check_only,
        strict=args.strict,
    )
    if failures:
        for failure in failures:
            print(failure)
        return 1
    print(c.SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
