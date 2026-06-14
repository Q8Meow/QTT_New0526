from __future__ import annotations

from pathlib import Path

from src.qtt.stage1_prediction_markets.pr166_sf_r2_targeted_conversion_repair_retest import constants as c
from src.qtt.stage1_prediction_markets.pr166_sf_r2_targeted_conversion_repair_retest.io import read_json, records_from_report_payload

REPO_ROOT = Path(__file__).resolve().parents[3]


def report_payload(filename: str) -> dict:
    return read_json(REPO_ROOT / c.GENERATED_DIR / filename)


def report_rows(filename: str) -> list[dict]:
    return records_from_report_payload(REPO_ROOT, report_payload(filename))


def assert_report_contract(filename: str, *, allow_empty: bool = False) -> list[dict]:
    payload = report_payload(filename)
    assert payload["roadmap_pr_id"] == c.PR_ID
    assert payload["created_by_pr"] == c.PR_ID
    assert payload["schema_ref"] == c.REPORT_SCHEMA_REFS[filename]
    rows = report_rows(filename)
    assert payload["record_count"] == len(rows)
    if not allow_empty:
        assert rows, filename
    return rows


def assert_all_rows_connected(filename: str, *, allow_empty: bool = False) -> list[dict]:
    rows = assert_report_contract(filename, allow_empty=allow_empty)
    for row in rows:
        assert row["created_by_pr"] == c.PR_ID
        assert row["roadmap_pr_id"] == c.PR_ID
        assert row["downstream_pr_refs"]
        assert row["downstream_artifact_refs"]
        assert row["owning_agent"]
        assert row["validator_ref"] == c.VALIDATOR_REF
        assert row["manifest_ref"] == c.MANIFEST_REF
        assert row["connector_binding_allowed_in_this_pr"] is False
        assert row["live_order_authority_allowed_in_this_pr"] is False
        assert row["profit_evidence_allowed_in_this_pr"] is False
        assert row["quantum_backend_execution_allowed_in_this_pr"] is False
    return rows
