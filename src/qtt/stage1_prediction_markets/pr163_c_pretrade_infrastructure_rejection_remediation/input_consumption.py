"""Input consumption audit for PR163-C."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths as p
from .deterministic_ids import plain_ref
from .json_io import read_json


def build_input_consumption_rows(repo_root: Path) -> list[dict[str, Any]]:
    artifacts = _declared_artifacts(repo_root)
    rows: list[dict[str, Any]] = []
    for index, artifact in enumerate(artifacts, start=1):
        rel = artifact["path"]
        path = repo_root / rel
        present = path.exists()
        readable = False
        record_count: int | None = None
        shard_count: int | None = None
        error = ""
        if present:
            try:
                if path.is_dir():
                    readable = True
                    record_count = len([item for item in path.rglob("*") if item.is_file()])
                    shard_count = record_count
                elif path.suffix == ".json":
                    payload = read_json(path)
                    readable = True
                    if isinstance(payload, dict):
                        record_count = int(payload.get("record_count", len(payload.get("records", []))))
                        shard_count = int(payload.get("shard_count", 0))
                    elif isinstance(payload, list):
                        record_count = len(payload)
                        shard_count = 0
                else:
                    path.read_text(encoding="utf-8", errors="ignore")
                    readable = True
                    record_count = 1
                    shard_count = 0
            except Exception as exc:  # pragma: no cover - exact message is validated by integration.
                error = f"{type(exc).__name__}: {exc}"
        rows.append(
            {
                "input_consumption_ref": plain_ref("PR163C_INPUT", index),
                "artifact_ref": rel.as_posix(),
                "artifact_role": artifact["role"],
                "required_for_trigger_consumption": artifact["required_for_trigger_consumption"],
                "present": present,
                "readable": readable,
                "missing_artifact_receipt": "" if present else f"MISSING_ARTIFACT::{rel.as_posix()}",
                "missing_artifact_is_fatal": (not present) and artifact["required_for_trigger_consumption"],
                "record_count": record_count,
                "shard_count": shard_count,
                "consumption_status": "CONSUMED" if present and readable else "MISSING_OR_UNREADABLE",
                "error": error,
                "validation_status": "PASS" if present and readable or not artifact["required_for_trigger_consumption"] else "FAIL",
            }
        )
    return rows


def source_inputs_from_consumption(rows: list[dict[str, Any]]) -> list[str]:
    return [row["artifact_ref"] for row in rows if row["present"] and row["readable"]]


def _declared_artifacts(repo_root: Path) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = [
        _artifact(Path("docs/master_plan/QTT_MasterPlan_Current.md"), "canonical_master_plan_no_edit", False),
        *[
            _artifact(p.GENERATED_DIR / filename, "required_pr164_report", True)
            for filename in p.PR164_REQUIRED_REPORTS
        ],
        _artifact(p.GENERATED_DIR / "pr164_shards", "required_pr164_shards_directory", True),
        _artifact(Path("tools/run_validation_gates.py"), "required_validation_gate_context", False),
        _artifact(Path("tools/ci_branch_context.py"), "required_branch_context", False),
        _artifact(Path("tests/fail_closed/test_run_validation_gates.py"), "required_gate_test_context", False),
        *[
            _artifact(Path(optional), "optional_pr163_b_artifact", False)
            for optional in p.OPTIONAL_INPUT_ARTIFACTS
        ],
    ]
    pr164_manifest_path = repo_root / p.GENERATED_DIR / "PR164_ReportManifest.report.json"
    if pr164_manifest_path.exists():
        manifest = read_json(pr164_manifest_path)
        for source in manifest.get("source_inputs", []):
            source_text = str(source)
            if "PR163_B_" in source_text or "pr163_b_shards/" in source_text:
                artifacts.append(
                    _artifact(Path(source_text), "pr163_b_artifact_consumed_through_pr164_manifest", False)
                )
    return _dedupe(artifacts)


def _artifact(path: Path, role: str, required_for_trigger_consumption: bool) -> dict[str, Any]:
    return {
        "path": path,
        "role": role,
        "required_for_trigger_consumption": required_for_trigger_consumption,
    }


def _dedupe(artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for artifact in artifacts:
        key = artifact["path"].as_posix()
        if key in seen:
            continue
        seen.add(key)
        result.append(artifact)
    return result
