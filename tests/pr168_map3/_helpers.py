from __future__ import annotations

import json
import shutil
import stat
import subprocess
import sys
import tempfile
from functools import lru_cache
from os import stat_result
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATED_PATH = Path("docs/master_plan/generated")
MAP3_TOOLS = (
    "build_pr168_map3.py",
    "validate_pr168_map3.py",
    "pr168_map3_config.py",
    "pr168_map3_external_intake.py",
    "pr168_map3_formula_factory.py",
    "pr168_map3_formula_family_matrix.py",
    "pr168_map3_formula_materialization.py",
    "pr168_map3_formula_provenance.py",
    "pr168_map3_online_scout.py",
    "pr168_map3_report_writer.py",
    "pr168_map3_source_triangulation.py",
    "pr168_map3_validator.py",
)
GENERATED_INPUT_PATTERNS = (
    "PR168_RP2*.report.json",
    "PR168_GFP2R_*.report.json",
    "PR168_DATA1A_*.report.json",
    "PR168_DATA1_*.report.json",
    "PR165_D2_*.report.json",
)
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


def _require_directory(path: Path) -> None:
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or _is_reparse_point(info):
        raise ValueError(f"MAP3 fixture requires an ordinary directory: {path}")


def _is_reparse_point(info: stat_result) -> bool:
    return bool(getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _seed_workspace(workspace: Path) -> None:
    generated = REPO_ROOT / GENERATED_PATH
    for directory in (REPO_ROOT / "tools", REPO_ROOT / "docs", generated.parent, generated):
        _require_directory(directory)
    sources = {REPO_ROOT / "tools" / name for name in MAP3_TOOLS}
    for pattern in GENERATED_INPUT_PATTERNS:
        sources.update(generated.glob(pattern))
    for name in ("rp2p", "pr168_gfp2r_candidate_compute"):
        folder = generated / name
        try:
            _require_directory(folder)
        except FileNotFoundError:
            continue
        sources.update(sorted(folder.glob("*.jsonl"))[:20])
        if name == "rp2p":
            sources.update(folder.glob("rank2_rows.jsonl"))

    for source in sorted(sources):
        info = source.lstat()
        if not stat.S_ISREG(info.st_mode) or _is_reparse_point(info) or info.st_nlink != 1:
            raise ValueError(f"MAP3 fixture requires an ordinary, unaliased input: {source}")
        target = workspace / source.relative_to(REPO_ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.open("rb") as original, target.open("xb") as copy:
            shutil.copyfileobj(original, copy)


def new_map3_workspace() -> tempfile.TemporaryDirectory[str]:
    parent = Path(tempfile.gettempdir()).resolve(strict=True)
    if parent.is_relative_to(REPO_ROOT):
        raise ValueError(f"MAP3 fixture temporary directory must be outside the checkout: {parent}")
    temporary = tempfile.TemporaryDirectory(prefix="map3-", dir=parent)
    try:
        workspace = Path(temporary.name)
        _require_directory(workspace)
        _seed_workspace(workspace)
    except BaseException:
        temporary.cleanup()
        raise
    return temporary


def run_map3_tool(workspace: Path, script: str, *args: str) -> None:
    subprocess.run(
        [sys.executable, "-I", "-B", f"tools/{script}", *args],
        cwd=workspace,
        check=True,
    )


@lru_cache(maxsize=1)
def _report_workspace() -> tempfile.TemporaryDirectory[str]:
    return new_map3_workspace()


def _run_build_once() -> Path:
    workspace = Path(_report_workspace().name)
    run_map3_tool(workspace, "build_pr168_map3.py", "--offline")
    return workspace / GENERATED_PATH


@lru_cache(maxsize=1)
def map3_reports() -> dict[str, dict[str, Any]]:
    generated = _run_build_once()
    reports = {}
    for name in REQUIRED_ONLINE_REPORTS:
        path = generated / name
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
    path = _run_build_once() / name
    assert path.exists(), f"missing report {name}"
    return json.loads(path.read_text(encoding="utf-8"))


def all_records() -> list[dict[str, Any]]:
    generated = _run_build_once()
    rows = []
    for path in generated.glob("PR168_MAP3_*.report.json"):
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
