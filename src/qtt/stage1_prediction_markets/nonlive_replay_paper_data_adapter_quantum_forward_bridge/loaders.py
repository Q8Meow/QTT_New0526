"""Load PR162 upstream report inputs."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from src.qtt.stage1_prediction_markets.replay_paper_executor_input_run_artifact_generation.compact_records import (
    expand_payload_records as expand_pr161f_payload_records,
)

from . import constants as c
from .json_io import read_json, records_from_payload
from .paths import normalize_repo_relative_ref, resolve_repo_relative


def current_branch(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def ensure_required_inputs(repo_root: Path) -> list[str]:
    missing = [
        ref
        for ref in c.REQUIRED_INPUT_REPORTS
        if not resolve_repo_relative(repo_root, ref).exists()
    ]
    if missing:
        raise FileNotFoundError("missing PR162 required inputs: " + ", ".join(missing))
    return [normalize_repo_relative_ref(repo_root, ref) for ref in c.REQUIRED_INPUT_REPORTS]


def load_pr161f_records(repo_root: Path) -> dict[str, list[dict[str, Any]]]:
    reports = {
        filename: read_json(repo_root / c.GENERATED_DIR / filename)
        for filename in c.PR161F_REPORTS_REQUIRED
    }
    shared_payload = read_json(
        repo_root / c.GENERATED_DIR / "PR161F_SharedDictionary.report.json"
    )
    shared_dictionary = shared_payload["shared_dictionary"]
    manifest_payload = read_json(
        repo_root / c.GENERATED_DIR / "PR161F_ReportShardManifest.report.json"
    )
    manifest_by_report = {
        record["report_filename"]: record
        for record in records_from_payload(manifest_payload)
    }

    loaded: dict[str, list[dict[str, Any]]] = {}
    for filename, payload in reports.items():
        if not payload.get("sharded_flag"):
            loaded[filename] = expand_pr161f_payload_records(payload, shared_dictionary)
            continue
        merged: list[dict[str, Any]] = []
        manifest_record = manifest_by_report[filename]
        for shard_ref in manifest_record["shard_files"]:
            shard_payload = read_json(resolve_repo_relative(repo_root, shard_ref))
            merged.extend(expand_pr161f_payload_records(shard_payload, shared_dictionary))
        loaded[filename] = merged
    return loaded


def index_by_qku(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {record["qku_id"]: record for record in records if isinstance(record.get("qku_id"), str)}

