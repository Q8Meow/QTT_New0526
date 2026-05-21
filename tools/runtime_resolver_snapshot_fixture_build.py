from __future__ import annotations

import argparse
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.stage1_prediction_markets.runtime_resolver_snapshot_executor.validator import (
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path("."), type=Path)
    parser.add_argument("--output-root", default=None, type=Path)
    args = parser.parse_args()
    write_artifacts(repo_root=args.repo_root, output_root=args.output_root)
    print("QTT_RUNTIME_RESOLVER_SNAPSHOT_FIXTURES_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
