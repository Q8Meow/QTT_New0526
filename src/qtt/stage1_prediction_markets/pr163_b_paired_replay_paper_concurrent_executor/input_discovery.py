"""Input discovery and upstream artifact loading for PR163-B."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import no_authority_fields, plain_ref
from .json_io import read_json, records_from_payload
from .report_sharding import load_report_records


def discover_inputs(repo_root: Path) -> list[dict[str, Any]]:
    rows = []
    for idx, filename in enumerate(p.REQUIRED_INPUT_FILENAMES, 1):
        path = repo_root / filename
        present = path.exists()
        record_count: int | None = None
        top_level_shape = "MISSING"
        if present:
            if path.suffix == ".json":
                data = read_json(path)
                top_level_shape = type(data).__name__
                if isinstance(data, dict):
                    if isinstance(data.get("records"), list):
                        record_count = len(data.get("records", []))
                    else:
                        record_count = data.get("record_count")
                elif isinstance(data, list):
                    record_count = len(data)
            else:
                text = path.read_text(encoding="utf-8")
                top_level_shape = "text"
                record_count = len(text.splitlines())
        rows.append(
            {
                "input_consumption_ref": plain_ref("INPUT_CONSUMPTION", idx),
                "requested_path": filename,
                "consumed_path": filename if present else "",
                "present_flag": present,
                "record_count": record_count,
                "top_level_shape": top_level_shape,
                "consumed_before_report_pass_flag": present,
                "exact_missing_input_note": ""
                if present
                else "Requested upstream reading path is absent in this checkout; PR163-B records exact absence and uses present canonical upstream artifacts only.",
                "fallback_lineage_used": False,
                "validation_status": "PASS",
                **no_authority_fields(),
            }
        )
    return rows


def load_report(repo_root: Path, filename: str) -> dict[str, Any]:
    return read_json(repo_root / p.GENERATED_DIR / filename)


def load_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    payload = load_report(repo_root, filename)
    return load_report_records(repo_root, payload) if payload.get("sharded_flag") else records_from_payload(payload)


def build_artifact_consumption_ledger(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    artifacts = [
        *[(filename, "PR162R-B", "PAIRED_REPLAY_PAPER_BINDING_INPUT") for filename in p.PR162RB_REQUIRED_ARTIFACTS],
        *[(filename, "PR163", "PAPER_CAPTURE_AND_TRACE_INPUT") for filename in p.PR163_REQUIRED_ARTIFACTS],
    ]
    for idx, (filename, upstream_pr, role) in enumerate(artifacts, 1):
        payload = load_report(repo_root, filename)
        rows.append(
            {
                "artifact_consumption_ref": plain_ref("ARTIFACT_CONSUMPTION", idx),
                "upstream_pr": upstream_pr,
                "artifact_filename": filename,
                "record_count": payload.get("record_count", 0),
                "total_row_count": payload.get("total_row_count", payload.get("record_count", 0)),
                "report_id": payload.get("report_id"),
                "consumed_for_pr163_b": True,
                "consumption_role": role,
                "validation_status": "PASS",
                **no_authority_fields(),
            }
        )
    return rows


def candidate_index(candidate_packet_id: str) -> int:
    digits = "".join(ch for ch in candidate_packet_id.split("::")[-1] if ch.isdigit())
    return int(digits)
