from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools import validate_qtt_master_plan_section_roadmap_crosswalk as crosswalk_gate


REPORT = Path("docs/master_plan/generated/MasterPlanSectionCoverageReport.json")


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def test_crosswalk_validator_accepts_existing_section_coverage_family():
    result = crosswalk_gate.validate()

    assert result.ok, result.failures
    assert result.report is not None
    summary = result.report["roadmap_crosswalk_summary"]
    assert summary["repo_canonical_pr_label"] == "PR120"
    assert summary["roadmap_pr_label"] == "PR #103"
    assert summary["blueprint_pr_label"] == "PR #103"
    assert summary["missing_section_count"] == 0
    assert summary["duplicate_section_count"] == 0


def test_crosswalk_and_market_index_counts_match_report_sections():
    report = _report()
    rows = report["roadmap_crosswalk"]["rows"]
    section_count = report["coverage_summary"]["parser_visible_section_count"]

    assert len(rows) == section_count
    assert report["roadmap_crosswalk_summary"][
        "section_manifest_parser_visible_section_count"
    ] == section_count
    assert report["market_specific_section_index_summary"][
        "owner_review_required_market_candidate_counts"
    ]["OWNER_REVIEW_REQUIRED_MARKET_CANDIDATE"] >= 1
    assert report["roadmap_crosswalk_summary"][
        "quantum_backend_simulator_optimizer_execution_created"
    ] is False


def test_crosswalk_validator_prints_success_marker():
    completed = subprocess.run(
        [sys.executable, "tools/validate_qtt_master_plan_section_roadmap_crosswalk.py"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "QTT_MASTER_PLAN_SECTION_ROADMAP_CROSSWALK_OK"
