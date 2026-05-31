"""Artifact loading and result-like artifact discovery for PR161E."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .json_io import read_json, records_from_payload
from .paths import repo_relative_posix, resolve_repo_relative


def load_report(repo_root: Path, path: Path) -> dict[str, Any]:
    payload = read_json(repo_root / path)
    if not isinstance(payload, dict):
        raise ValueError(f"PR161E expected report object: {path.as_posix()}")
    return payload


def load_records(repo_root: Path, path: Path) -> list[dict[str, Any]]:
    payload = load_report(repo_root, path)
    records = records_from_payload(payload)
    if records or not payload.get("sharded_flag"):
        return records
    merged: list[dict[str, Any]] = []
    for shard_ref in payload.get("shard_files") or []:
        shard_payload = read_json(resolve_repo_relative(repo_root, shard_ref))
        merged.extend(records_from_payload(shard_payload))
    return merged


def existing_path_status(repo_root: Path, paths: list[Path] | tuple[Path, ...]) -> dict[str, bool]:
    return {path.as_posix(): (repo_root / path).exists() for path in paths}


def consume_text_artifacts(repo_root: Path, paths: list[Path] | tuple[Path, ...]) -> dict[str, bool]:
    status: dict[str, bool] = {}
    for path in paths:
        absolute = repo_root / path
        if absolute.exists() and absolute.is_file():
            absolute.read_text(encoding="utf-8", errors="replace")
            status[path.as_posix()] = True
        else:
            status[path.as_posix()] = False
    return status


def consume_json_report_map(repo_root: Path, report_paths: dict[str, Path]) -> dict[str, dict[str, Any] | None]:
    consumed: dict[str, dict[str, Any] | None] = {}
    for name, path in report_paths.items():
        absolute = repo_root / path
        if absolute.exists():
            consumed[name] = load_report(repo_root, path)
        else:
            consumed[name] = None
    return consumed


def discover_result_like_artifacts(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for root in c.RESULT_DISCOVERY_ROOTS:
        absolute_root = repo_root / root
        if not absolute_root.exists():
            continue
        paths = [absolute_root] if absolute_root.is_file() else sorted(absolute_root.rglob("*"))
        for path in paths:
            if not path.is_file():
                continue
            relative = repo_relative_posix(repo_root, path)
            lowered = relative.lower()
            if not any(token in lowered for token in ("result", "replay", "paper")):
                continue
            artifact_class, authenticity_class = classify_result_like_path(relative)
            records.append(
                {
                    "record_id": f"PR161E-RESULT-DISCOVERY-{len(records)+1:05d}",
                    "pr_label": c.PR_LABEL,
                    "source_artifact_path": relative,
                    "source_artifact_class": artifact_class,
                    "result_authenticity_class": authenticity_class,
                    "provenance_class": (
                        "SOURCE_EVIDENCE_FIXTURE"
                        if relative.startswith("tests/fixtures/")
                        else "LOCAL_REPO_ARTIFACT"
                    ),
                    "treated_as_qtt_result_evidence_flag": False,
                    "actual_replay_result_candidate_flag": artifact_class
                    == "ACTUAL_REPLAY_RESULT_PACKET_CANDIDATE",
                    "actual_paper_result_candidate_flag": artifact_class
                    == "ACTUAL_PAPER_RESULT_PACKET_CANDIDATE",
                    "no_profit_evidence_created_without_validated_result_packet_flag": True,
                    "no_live_authority_created_flag": True,
                }
            )
    return records


def classify_result_like_path(relative_path: str) -> tuple[str, str]:
    lowered = relative_path.lower()
    if "/pr161e_" in lowered and "outcomecapture" in lowered:
        return "EMPTY_PENDING_CAPTURE_SURFACE", "NO_VALIDATED_RESULT_PACKET"
    if lowered.endswith(".schema.json") or "/schemas/" in lowered:
        return "SCHEMA_ONLY_ARTIFACT", "SCHEMA_OR_CONTRACT_ONLY"
    if "fixture" in lowered or relative_path.startswith("tests/fixtures/"):
        return (
            "SYNTHETIC_TEST_FIXTURE_RESULT_PACKET",
            "SYNTHETIC_FIXTURE_NOT_PERFORMANCE_EVIDENCE",
        )
    if any(token in lowered for token in ("contract", "boundary", "check.py")):
        return "CONTRACT_ONLY_ARTIFACT", "SCHEMA_OR_CONTRACT_ONLY"
    if "pr161d_" in lowered and any(
        token in lowered for token in ("ranking", "scenario", "priority", "resultbacked")
    ):
        return (
            "PRE_RESULT_RANKING_ARTIFACT",
            "PRE_RESULT_PRIORITY_NOT_PERFORMANCE_EVIDENCE",
        )
    if "replay_result_packet" in lowered and lowered.endswith(".json"):
        return "ACTUAL_REPLAY_RESULT_PACKET_CANDIDATE", "NO_VALIDATED_RESULT_PACKET"
    if "paper_result_packet" in lowered and lowered.endswith(".json"):
        return "ACTUAL_PAPER_RESULT_PACKET_CANDIDATE", "NO_VALIDATED_RESULT_PACKET"
    return "NO_RESULT_ARTIFACT", "NO_VALIDATED_RESULT_PACKET"
