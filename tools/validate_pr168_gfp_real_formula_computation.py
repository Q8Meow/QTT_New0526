from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.validator import run_validation


if __name__ == "__main__":
    run_validation(REPO_ROOT, "real_formula_computation")
    print("PR168_GFP_REAL_FORMULA_COMPUTATION_OK")
