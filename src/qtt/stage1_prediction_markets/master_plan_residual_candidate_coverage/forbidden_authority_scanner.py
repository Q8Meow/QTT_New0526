"""Forbidden-authority scanner for PR161B files and reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c


def scan_forbidden_authority(root: Path | str) -> dict[str, Any]:
    repo_root = Path(root).resolve()
    paths = [
        *sorted((repo_root / c.PACKAGE_DIR).rglob("*.py"), key=lambda path: path.as_posix()),
        *sorted((repo_root / c.TEST_DIR).rglob("*.py"), key=lambda path: path.as_posix()),
        repo_root / "tools/build_pr161b_master_plan_residual_candidate_coverage.py",
        repo_root / "tools/validate_pr161b_master_plan_residual_candidate_coverage.py",
    ]
    findings: list[dict[str, str]] = []
    for path in paths:
        if not path.exists() or path.suffix not in {".py", ".json"}:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in c.FORBIDDEN_SCAN_PATTERNS:
            if pattern in text:
                findings.append(
                    {
                        "path": path.relative_to(repo_root).as_posix(),
                        "pattern": pattern,
                    }
                )
    return {
        "scan_id": "PR161B_FORBIDDEN_AUTHORITY_SCAN",
        "scanned_path_count": len([path for path in paths if path.exists()]),
        "finding_count": len(findings),
        "findings": findings,
        "forbidden_authority_scan_status": "PASS" if not findings else "FAIL",
        "atomicrows_final_bundle_created_flag": False,
        "atomicrows_forbidden_bundle_digest_reference_added_flag": False,
        "qtt_integrity_authority_created_flag": False,
        "optimizer_execution_evidence_created_flag": False,
        "quantum_backend_execution_evidence_created_flag": False,
        "profit_evidence_created_flag": False,
    }
