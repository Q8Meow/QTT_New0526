"""No-orphan generated file audit."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c


def no_orphan_generated_file_records(repo_root: Path) -> list[dict[str, Any]]:
    existing = {
        path.name
        for path in (repo_root / c.GENERATED_DIR).glob("PR162R_A_*.report.json")
    }
    expected = set(c.REPORT_FILENAMES)
    return [
        {
            "audit_id": "PR162R_A_NO_ORPHAN_GENERATED_FILE",
            "expected_generated_file_count": len(expected),
            "observed_generated_file_count": len(existing),
            "orphan_generated_file_count": len(existing - expected),
            "missing_generated_file_count": len(expected - existing),
            "validation_status": "PASS" if not (existing - expected) else "FAIL",
            "live_order_authority": False,
        }
    ]
