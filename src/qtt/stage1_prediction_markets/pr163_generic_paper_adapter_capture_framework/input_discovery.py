"""Input discovery and PR162R-B artifact loading for PR163."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import paths as p
from .authority_policy import no_authority_fields, plain_ref
from .json_io import read_json, read_jsonl, records_from_payload


PR162RB_FIXTURE_DIR = Path(
    "tests/fixtures/stage1_prediction_markets/"
    "pr162r_b_replay_paper_data_binding_completion"
)


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
                    record_count = len(data.get("records", [])) if isinstance(data.get("records"), list) else data.get("record_count")
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
                else "Required reading path absent in upstream checkout; PR163 records exact absence and does not fabricate a substitute.",
                "fallback_lineage_used": False,
                "validation_status": "PASS",
                **no_authority_fields(),
            }
        )
    return rows


def load_report(repo_root: Path, filename: str) -> dict[str, Any]:
    return read_json(repo_root / p.GENERATED_DIR / filename)


def load_records(repo_root: Path, filename: str) -> list[dict[str, Any]]:
    return records_from_payload(load_report(repo_root, filename))


def load_pr162rb_reports(repo_root: Path) -> dict[str, dict[str, Any]]:
    return {filename: load_report(repo_root, filename) for filename in p.PR162RB_REQUIRED_ARTIFACTS}


def build_pr162rb_consumption_ledger(repo_root: Path, reports: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for idx, filename in enumerate(p.PR162RB_REQUIRED_ARTIFACTS, 1):
        payload = reports[filename]
        rows.append(
            {
                "artifact_consumption_ref": plain_ref("PR162RB_CONSUMPTION", idx),
                "artifact_filename": filename,
                "record_count": payload.get("record_count", 0),
                "report_id": payload.get("report_id"),
                "consumed_for_pr163": True,
                "consumption_role": "PAPER_ADAPTER_INPUT_AND_CAPTURE_MATERIALIZATION",
                "validation_status": "PASS",
                **no_authority_fields(),
            }
        )
    return rows


def load_fixture_payloads(repo_root: Path) -> dict[str, Any]:
    fixture_root = repo_root / PR162RB_FIXTURE_DIR
    return {
        "orderbook": read_jsonl(fixture_root / "synthetic_binary_market_orderbook_1s.fixture.jsonl"),
        "latency": read_jsonl(fixture_root / "synthetic_latency_observations.fixture.jsonl"),
        "portfolio": read_json(fixture_root / "synthetic_paper_portfolio_state.fixture.json"),
        "fee_slippage": read_json(fixture_root / "synthetic_fee_slippage_model.fixture.json"),
        "market_state": read_json(fixture_root / "synthetic_paper_market_state.fixture.json"),
    }


def candidate_index(candidate_packet_id: str) -> int:
    digits = "".join(ch for ch in candidate_packet_id.split("::")[-1] if ch.isdigit())
    return int(digits)


def compact_json_record(row: dict[str, Any]) -> str:
    return json.dumps(row, ensure_ascii=True, sort_keys=True)
