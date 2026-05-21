from __future__ import annotations

import argparse
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.stage1_prediction_markets.replay_paper.historical_dataset_digest_and_loader import (
    write_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=Path("."), type=Path)
    args = parser.parse_args()
    write_artifacts(repo_root=args.repo_root.resolve())
    print("QTT_HISTORICAL_DATASET_DIGEST_AND_LOADER_FIXTURES_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
