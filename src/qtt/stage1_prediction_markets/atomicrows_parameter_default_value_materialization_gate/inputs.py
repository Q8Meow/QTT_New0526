"""Read-only input loading for PR154."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping

from src.qtt.stage1_prediction_markets.pr153s_source_value_capture_closure_classifier import (
    classifier as pr153s_classifier,
    inputs as pr153s_inputs,
    taxonomy as pr153s_tx,
)

from . import taxonomy as tx


@dataclass(frozen=True)
class PR154Inputs:
    repo_root: Path
    pr153s_report: Mapping[str, Any]
    pr153s_records: tuple[Mapping[str, Any], ...]
    pr153s_upstream: pr153s_inputs.UpstreamInputs
    consumed_artifact_receipts: tuple[Mapping[str, Any], ...]
    quantum_artifact_receipts: tuple[Mapping[str, Any], ...]


def read_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.as_posix()} must contain a JSON object")
    return payload


def _artifact_receipt(repo_root: Path, rel_path: Path, role: str) -> dict[str, Any]:
    path = repo_root / rel_path
    exists = path.exists()
    receipt: dict[str, Any] = {
        "artifact_path": rel_path.as_posix(),
        "exists": exists,
        "consumed": exists,
        "role": role,
        "read_mode": "READ_ONLY_CONTEXT",
        "artifact_type": "dir" if exists and path.is_dir() else "file" if exists else "missing",
    }
    if exists and path.is_file() and path.suffix.lower() == ".json":
        try:
            payload = read_json_object(path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            receipt["parse_status"] = f"PARSE_ERROR: {exc}"
        else:
            receipt["parse_status"] = "JSON_OBJECT_PARSED"
            for key in (
                "report_id",
                "validator_marker",
                "validation_marker",
                "final_status_label",
                "readiness_class",
                "authority_class",
                "pr_id",
                "report_version",
            ):
                if key in payload:
                    receipt[key] = payload.get(key)
    elif exists and path.is_file():
        receipt["parse_status"] = "TEXT_EXISTS"
    elif exists:
        receipt["parse_status"] = "DIRECTORY_EXISTS"
    else:
        receipt["parse_status"] = "MISSING"
    return receipt


def _all_artifact_receipts(repo_root: Path) -> tuple[Mapping[str, Any], ...]:
    seen: set[str] = set()
    receipts: list[Mapping[str, Any]] = []
    for rel_path in tx.CONSUMED_ARTIFACT_PATHS:
        path_key = rel_path.as_posix()
        if path_key in seen:
            continue
        seen.add(path_key)
        role = (
            "QUANTUM_FORWARD_CONTEXT"
            if rel_path in tx.QUANTUM_FORWARD_ARTIFACT_PATHS
            else "ORCHESTRATION"
            if rel_path in tx.ORCHESTRATION_ARTIFACT_PATHS
            else "SOURCE_VALUE_INPUT"
            if rel_path in tx.SOURCE_VALUE_ARTIFACT_PATHS
            else "VALIDATOR_AND_MODULE_CONTEXT"
        )
        receipts.append(_artifact_receipt(repo_root, rel_path, role))
    return tuple(receipts)


def _quantum_receipts(
    receipts: tuple[Mapping[str, Any], ...],
) -> tuple[Mapping[str, Any], ...]:
    quantum_paths = {path.as_posix() for path in tx.QUANTUM_FORWARD_ARTIFACT_PATHS}
    return tuple(
        receipt
        for receipt in receipts
        if str(receipt.get("artifact_path")) in quantum_paths
    )


def load_inputs(repo_root: Path | str) -> PR154Inputs:
    root = Path(repo_root).resolve()
    pr153s_records, upstream = pr153s_classifier.classify_targets(root)
    pr153s_report = read_json_object(root / pr153s_tx.REPORT_PATH)
    receipts = _all_artifact_receipts(root)
    return PR154Inputs(
        repo_root=root,
        pr153s_report=pr153s_report,
        pr153s_records=tuple(pr153s_records),
        pr153s_upstream=upstream,
        consumed_artifact_receipts=receipts,
        quantum_artifact_receipts=_quantum_receipts(receipts),
    )
