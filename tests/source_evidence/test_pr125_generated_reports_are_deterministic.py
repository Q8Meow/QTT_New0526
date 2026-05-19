from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPORTS = [
    Path(
        "docs/master_plan/source_evidence/generated/"
        "CODEX_PR125_SOURCE_REVALIDATION_SUPERSESSION_MATERIALITY_SCHEDULER_REPORT.json"
    ),
    Path("docs/master_plan/source_evidence/generated/SourceRevalidationScheduler.report.json"),
    Path("docs/master_plan/source_evidence/generated/SourceChangeImpactSnapshot.report.json"),
]


def test_pr125_generated_reports_are_deterministic():
    first = {path: path.read_text(encoding="utf-8") for path in REPORTS}
    completed = subprocess.run(
        [
            sys.executable,
            "tools/validate_source_revalidation_scheduler.py",
            "--repo-root",
            ".",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    second = {path: path.read_text(encoding="utf-8") for path in REPORTS}

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == (
        "QTT_SOURCE_REVALIDATION_SUPERSESSION_AND_MATERIALITY_SCHEDULER_OK"
    )
    assert first == second
