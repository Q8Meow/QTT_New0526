from __future__ import annotations

import json
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATED_ROOT = REPO_ROOT / "docs" / "master_plan" / "generated"
REQUIRED_ONLINE_REPORTS = [
    "PR168_MAP3_OnlineScout.report.json",
    "PR168_MAP3_ExtSources.report.json",
    "PR168_MAP3_ExtIntake.report.json",
    "PR168_MAP3_FamilyMatrix.report.json",
    "PR168_MAP3_FormulaFactory.report.json",
    "PR168_MAP3_FormulaMaterialization.report.json",
    "PR168_MAP3_FormulaProv.report.json",
    "PR168_MAP3_SourceTriangulation.report.json",
]


def _run_build_once() -> None:
    subprocess.run(
        [sys.executable, "tools/build_pr168_map3.py", "--offline"],
        cwd=REPO_ROOT,
        check=True,
    )


@lru_cache(maxsize=1)
def map3_reports() -> dict[str, dict[str, Any]]:
    _run_build_once()
    reports = {}
    for name in REQUIRED_ONLINE_REPORTS:
        path = GENERATED_ROOT / name
        assert path.exists(), f"missing report {name}"
        reports[name] = json.loads(path.read_text(encoding="utf-8"))
    return reports


def records(name: str) -> list[dict[str, Any]]:
    value = report(name).get("records")
    assert isinstance(value, list) and value, f"{name} has no records"
    return value


def report(name: str) -> dict[str, Any]:
    if name in REQUIRED_ONLINE_REPORTS:
        return map3_reports()[name]
    _run_build_once()
    path = GENERATED_ROOT / name
    assert path.exists(), f"missing report {name}"
    return json.loads(path.read_text(encoding="utf-8"))


def all_records() -> list[dict[str, Any]]:
    _run_build_once()
    rows = []
    for path in GENERATED_ROOT.glob("PR168_MAP3_*.report.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows.extend(payload.get("records", []))
    return rows


def summary() -> dict[str, Any]:
    return map3_reports()["PR168_MAP3_OnlineScout.report.json"].get("summary", {})


def assert_minimum_counts() -> None:
    data = summary()
    assert data["online_scout_row_count"] >= 30
    assert data["distinct_source_url_count"] >= 10
    assert data["query_family_count"] >= 8
    assert (
        data["mandatory_formula_family_covered_count"]
        + data["mandatory_formula_family_gap_routed_count"]
        >= 12
    )
    assert data["useful_formula_or_input_found_count"] > 0
    assert (
        data["materialized_formula_candidate_count"]
        + data["semantic_formula_repair_route_count"]
        > 0
    )
    assert data["formula_plugin_contract_count"] + data["semantic_formula_repair_route_count"] > 0
    assert (
        data["rp2_handoff_count"]
        + data["rank2_handoff_count"]
        + data["source_evidence_review_route_count"]
        + data["data1b_repair_route_count"]
        > 0
    )
    assert data["no_orphan_violation_count"] == 0
    assert data["source_truth_acceptance_created_count"] == 0
    assert data["real_positive_count"] == 0
    assert data["real_negative_count"] == 0
    assert data["champion_allowed_count"] == 0
    assert data["live_candidate_allowed_count"] == 0
