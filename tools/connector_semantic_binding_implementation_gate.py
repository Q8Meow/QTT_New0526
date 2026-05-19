from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.source_evidence.connector_semantic_implementation.validator import (
    GATE_REPORT_PATH,
    MAIN_REPORT_PATH,
    MANIFEST_REPORT_PATH,
    build_validation_artifacts,
)

SUCCESS_MARKER = "QTT_CONNECTOR_SEMANTIC_BINDING_IMPLEMENTATION_GATE_FIXTURE_OUTPUT_WRITTEN"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--artifact",
        choices=("main", "gate", "manifest"),
        default="gate",
    )
    parser.add_argument("--out", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    artifacts = build_validation_artifacts(args.repo_root)
    artifact_map = {
        "main": ("main_report", MAIN_REPORT_PATH),
        "gate": ("gate_report", GATE_REPORT_PATH),
        "manifest": ("manifest_report", MANIFEST_REPORT_PATH),
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
