#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.source_evidence.connector_semantic_consumer.ledger import (  # noqa: E402
    write_json_object,
)
from src.qtt.source_evidence.cross_venue_execution_normalization.binding import (  # noqa: E402
    build_cross_venue_execution_normalization_artifacts,
    load_fixture_inputs,
)
from src.qtt.source_evidence.cross_venue_execution_normalization.validator import (  # noqa: E402
    BINDING_REPORT_PATH,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--out", default=str(BINDING_REPORT_PATH))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    repo_root = Path(args.repo_root)
    artifacts = build_cross_venue_execution_normalization_artifacts(
        **load_fixture_inputs(repo_root)
    )
    write_json_object(repo_root / Path(args.out), artifacts)
    print("QTT_CROSS_VENUE_EXECUTION_NORMALIZATION_BINDING_FIXTURE_OUTPUT_WRITTEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
