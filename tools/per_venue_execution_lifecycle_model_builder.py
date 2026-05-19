from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.source_evidence.execution_lifecycle.validator import (
    BUILDER_REPORT_PATH,
    HANDOFF_REPORT_PATH,
    MAIN_REPORT_PATH,
    MODELS_REPORT_PATH,
    build_validation_artifacts,
)


SUCCESS_MARKER = "QTT_PER_VENUE_EXECUTION_LIFECYCLE_MODEL_BUILDER_FIXTURE_OUTPUT_WRITTEN"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--artifact",
        choices=("main", "builder", "models", "handoff"),
        default="builder",
    )
    parser.add_argument("--out", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    artifacts = build_validation_artifacts(args.repo_root)
    artifact_map = {
        "main": ("main_report", MAIN_REPORT_PATH),
        "builder": ("builder_report", BUILDER_REPORT_PATH),
        "models": ("models_report", MODELS_REPORT_PATH),
        "handoff": ("handoff_report", HANDOFF_REPORT_PATH),
    }
    artifact_key, default_out = artifact_map[args.artifact]
    out = args.out or args.repo_root / default_out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(artifacts[artifact_key], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
