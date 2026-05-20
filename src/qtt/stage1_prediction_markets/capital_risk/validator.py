from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.qtt.stage1_prediction_markets.capital_risk.field_map import (
    build_runtime_cash_artifacts,
)
from src.qtt.stage1_prediction_markets.capital_risk.field_map_constants import (
    ACTIVE_STAGE1_VENUES,
    COMPONENTS,
    DETERMINISTIC_FIXTURE_TIME,
    FIXTURE_AUTHORITY_CLASS,
)


GENERATED_DIR = Path("docs/master_plan/source_evidence/generated")
MAIN_REPORT_PATH = GENERATED_DIR / "CODEX_PR129_RUNTIME_CASH_COMPONENT_FIELD_MAP_EXECUTOR_REPORT.json"
FIELD_MAP_REPORT_PATH = GENERATED_DIR / "RuntimeCashComponentFieldMap.report.json"
RECONCILIATION_REPORT_PATH = GENERATED_DIR / "RuntimeCashComponentReconciliation.report.json"
AVAILABLE_REPORT_PATH = GENERATED_DIR / "RuntimeAvailableAfterCommitmentsFixture.report.json"
HANDOFF_REPORT_PATH = GENERATED_DIR / "RuntimeCashDownstreamHandoff.report.json"
GATE_REPORT_PATH = GENERATED_DIR / "NewExposureCashGateFixture.report.json"

REPORT_PATHS = {
    "main_report": MAIN_REPORT_PATH,
    "field_map_report": FIELD_MAP_REPORT_PATH,
    "reconciliation_report": RECONCILIATION_REPORT_PATH,
    "available_report": AVAILABLE_REPORT_PATH,
    "handoff_report": HANDOFF_REPORT_PATH,
    "gate_report": GATE_REPORT_PATH,
}


def _dump_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _all_flags_false(record: Mapping[str, Any], fields: tuple[str, ...]) -> bool:
    return all(record.get(field) is False for field in fields)


def validate_artifacts(artifacts: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    main = artifacts["main_report"]
    field_map_report = artifacts["field_map_report"]
    available_report = artifacts["available_report"]
    gate_report = artifacts["gate_report"]
    handoff = artifacts["handoff_report"]["runtime_cash_downstream_handoff"]
    field_maps = field_map_report["runtime_cash_component_field_maps"]
    venue_bindings = field_map_report["venue_balance_semantic_bindings"]
    source_rejections = field_map_report["source_packet_required_rejection_receipts"]
    unknown_rejections = field_map_report["unknown_cash_component_rejection_receipts"]
    available_receipts = available_report["runtime_available_after_commitments_receipts"]
    gate_receipts = gate_report["new_exposure_cash_gate_receipts"]

    if len(field_maps) != len(ACTIVE_STAGE1_VENUES) * len(COMPONENTS):
        failures.append("field-map packet count must equal three venues times known components")
    if {record["venue_id"] for record in field_maps} != set(ACTIVE_STAGE1_VENUES):
        failures.append("field-map packets must cover exactly the three Stage-1 venues")
    if len(venue_bindings) != len(ACTIVE_STAGE1_VENUES):
        failures.append("venue balance semantic binding count must equal three")
    for record in field_maps:
        if record.get("fixture_authority_class") != FIXTURE_AUTHORITY_CLASS:
            failures.append("field maps must be TEST_FIXTURE_NOT_EXTERNAL_FACT")
        if record.get("production_runtime_cash_authority") is not False:
            failures.append("field maps must not create production runtime cash authority")
        if not record.get("source_packet_ids_by_component"):
            failures.append("each field map must include a source packet")
        if not record.get("accepted_source_packet_digest_by_component"):
            failures.append("each field map must include a source packet digest")
        if not record.get("target_field_path_by_component"):
            failures.append("each field map must include a target field path")
        if not record.get("raw_venue_field_locator_by_component"):
            failures.append("each field map must include a raw venue field locator")
        if record.get("deterministic_fixture_time") != DETERMINISTIC_FIXTURE_TIME:
            failures.append("field maps must use deterministic fixture time")
    authority_false_fields = (
        "account_wallet_balance_private_state_fetch_allowed_flag",
        "production_connector_use_allowed_flag",
        "order_execution_allowed_flag",
        "order_routing_authority_allowed_flag",
        "network_io_allowed_flag",
        "replay_paper_execution_allowed_flag",
        "runtime_resolver_snapshot_creation_allowed_flag",
    )
    for receipt in available_receipts:
        if receipt.get("production_runtime_cash_receipt_authority") is not False:
            failures.append("available-after-commitments receipts must remain fixture-only")
        if not _all_flags_false(receipt, authority_false_fields):
            failures.append("available-after-commitments receipt authority flags must be false")
    for receipt in gate_receipts:
        if receipt.get("production_new_exposure_cash_gate_authority") is not False:
            failures.append("new-exposure cash gate receipts must remain fixture-only")
        if receipt.get("order_authority_allowed_flag") is not False:
            failures.append("new-exposure cash gate receipts must not create order authority")
    if len(source_rejections) < 3:
        failures.append("source-packet rejection receipts must cover missing packet/path/locator")
    if not unknown_rejections:
        failures.append("unknown-cash-component rejection receipt is required")
    if handoff.get("production_downstream_authority") is not False:
        failures.append("runtime cash downstream handoff must not create production authority")
    expected_main = {
        "repo_pr_label": "PR129",
        "roadmap_pr_implemented": "PR111",
        "checked_github_pr_number": 128,
        "fixture_stage1_venue_count": 3,
        "fixture_runtime_cash_field_map_count": len(field_maps),
        "production_runtime_cash_authority_count": 0,
        "production_runtime_cash_receipt_authority_count": 0,
        "production_new_exposure_cash_gate_authority_count": 0,
        "decimal_cash_math_used": True,
        "binary_float_cash_math_used": False,
        "atomicrows_bundle_consumed": False,
        "atomicrows_bundle_created": False,
        "atomicrows_sha_created": False,
        "quantum_backend_execution_count": 0,
        "optimizer_execution_count": 0,
        "profit_evidence_created": False,
    }
    for field, expected in expected_main.items():
        if main.get(field) != expected:
            failures.append(f"main_report.{field} must be {expected!r}")
    return failures


def write_generated_reports(repo_root: Path) -> dict[str, Any]:
    artifacts = build_runtime_cash_artifacts(repo_root)
    failures = validate_artifacts(artifacts)
    if failures:
        raise ValueError("; ".join(failures))
    for key, path in REPORT_PATHS.items():
        output_path = repo_root / path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(_dump_json(artifacts[key]), encoding="utf-8", newline="\n")
    return artifacts
