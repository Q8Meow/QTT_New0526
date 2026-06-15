"""Validate PR165-D3 quantum-aware scenario selection v3 artifacts."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr165_d3_quantum_aware_scenario_selection_v3.validator import main


if __name__ == "__main__":
    raise SystemExit(main())
