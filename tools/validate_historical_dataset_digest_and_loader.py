from __future__ import annotations

from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.qtt.stage1_prediction_markets.replay_paper.historical_dataset_digest_and_loader import (
    main,
)


if __name__ == "__main__":
    raise SystemExit(main())
