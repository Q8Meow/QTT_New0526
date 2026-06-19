from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr168_gfp_real_computation.validator import (  # noqa: E402
    audit_formula_registry_integrity,
    run_validation,
)


if __name__ == "__main__":
    summary = audit_formula_registry_integrity(REPO_ROOT)
    print(json.dumps(summary, indent=2, sort_keys=True))
    run_validation(REPO_ROOT, "formula_registry_integrity")
    print("PR168_GFP_FORMULA_REGISTRY_INTEGRITY_OK")
