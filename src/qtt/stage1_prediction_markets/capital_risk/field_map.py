from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.qtt.stage1_prediction_markets.capital_risk.available_after_commitments import (
    compute_available_after_commitments_fixture,
)
from src.qtt.stage1_prediction_markets.capital_risk.field_map_constants import (
    ACTIVE_STAGE1_VENUES,
    COMPONENTS,
    DETERMINISTIC_FIXTURE_TIME,
    FIXTURE_AUTHORITY_CLASS,
    READY_STATE,
    REJECTED_ATOMICROWS_AUTHORITY_ATTEMPT,
    REJECTED_CONNECTOR_BLOCKING_MATERIALITY,
    REJECTED_MISSING_ACCEPTED_SOURCE_PACKET,
    REJECTED_MISSING_RAW_FIELD_LOCATOR,
    REJECTED_MISSING_TARGET_FIELD_PATH,
    REJECTED_PRIVATE_STATE_RECEIPT_REQUIRED_FUTURE_PR,
    REJECTED_REVALIDATION_REQUIRED,
    REJECTED_SCOPE_OR_VENUE_MISMATCH,
    REJECTED_STALE_ACCEPTED_PACKET,
    REJECTED_SUPERSEDED_ACCEPTED_PACKET,
    REJECTED_TRADING_BLOCKING_MATERIALITY,
    REJECTED_UNRECONCILED_CASH_COMPONENT,
    REJECTED_UNKNOWN_CASH_COMPONENT,
    SHARED_SCOPE_METADATA,
)
from src.qtt.stage1_prediction_markets.capital_risk.handoff import (
    build_runtime_cash_downstream_handoff,
)
from src.qtt.stage1_prediction_markets.capital_risk.money import money


PR129_FIXTURE_DIR = Path("tests/fixtures/source_evidence/pr129_runtime_cash_component_field_map")
PR128_HANDOFF_REPORT_PATH = Path(
    "docs/master_plan/source_evidence/generated/CrossVenueExecutionDownstreamHandoff.report.json"
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _path_exists(repo_root: Path, path: str | Path) -> bool:
    return (repo_root / Path(path)).exists()


def _component_lookup(accepted_fixture: Mapping[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    lookup: dict[tuple[str, str], dict[str, Any]] = {}
    for venue_record in accepted_fixture["component_records"]:
        venue_id = venue_record["venue_id"]
        for component_record in venue_record["components"]:
            lookup[(venue_id, component_record["cash_component_class"])] = dict(component_record)
    return lookup


def _common_false_flags() -> dict[str, bool]:
    return {
        "account_wallet_balance_private_state_fetch_allowed_flag": False,
        "production_connector_use_allowed_flag": False,
        "order_execution_allowed_flag": False,
        "order_routing_authority_allowed_flag": False,
        "network_io_allowed_flag": False,
        "replay_paper_execution_allowed_flag": False,
        "runtime_resolver_snapshot_creation_allowed_flag": False,
    }


def _future_path_flags() -> dict[str, bool]:
    return {
        "future_private_state_read_receipt_path_preserved": True,
        "future_credential_alias_secret_no_capture_path_preserved": True,
        "future_market_data_ingest_path_preserved": True,
        "future_orderbook_event_snapshot_path_preserved": True,
        "future_runtime_resolver_snapshot_path_preserved": True,
        "future_atomicrows_bridge_path_preserved": True,
        "future_production_launch_path_preserved": True,
    }


def _atomicrows_metadata() -> dict[str, object]:
    return {
        "future_atomicrows_parameter_row_refs": [],
        "future_atomicrows_family_refs": ["FUTURE_ATOMICROWS_RUNTIME_CASH_COMPONENT_FAMILY"],
        "future_atomicrows_runtime_cash_component_family_ref": (
            "FUTURE_ATOMICROWS_RUNTIME_CASH_COMPONENT_FAMILY"
        ),
        "atomicrows_bundle_consumed": False,
        "atomicrows_bundle_created": False,
        "atomicrows_sha_created": False,
        "atomicrows_row_records_created_count": 0,
        "atomicrows_authority_created": False,
    }


def _field_map_record(
    *,
    venue_id: str,
    account_scope_id: str,
    component: Any,
    source_record: Mapping[str, str],
) -> dict[str, object]:
    component_key = component.name
    record = {
        "runtime_cash_component_field_map_id": (
            f"PR129_{venue_id}_{component.class_name}_FIELD_MAP_V1"
        ),
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "production_runtime_cash_authority": False,
        "venue_id": venue_id,
        "account_scope_id": account_scope_id,
        "runtime_cash_field_map_state": READY_STATE,
        "source_packet_ids_by_component": {
            component_key: source_record["accepted_source_packet_id"]
        },
        "accepted_source_packet_digest_by_component": {
            component_key: source_record["accepted_source_packet_digest"]
        },
        "target_field_path_by_component": {
            component_key: source_record["target_field_path"]
        },
        "raw_venue_field_locator_by_component": {
            component_key: source_record["raw_venue_field_locator"]
        },
        "canonical_cash_component_name": component_key,
        "cash_component_class": component.class_name,
        "cash_component_sign": component.sign,
        "cash_component_currency": "USD",
        "cash_component_timestamp_policy": "DETERMINISTIC_FIXTURE_TIMESTAMP_ONLY",
        "cash_component_staleness_policy": "REJECT_IF_STALE_OR_REVALIDATION_REQUIRED",
        "open_order_lock_component_included_flag": component.class_name == "OPEN_ORDER_LOCK",
        "required_reserve_component_included_flag": component.class_name == "REQUIRED_RESERVE",
        "margin_lock_component_included_flag": component.class_name == "MARGIN_LOCK",
        "unsettled_component_included_flag": component.class_name == "UNSETTLED_FUNDS",
        "locked_or_withdrawal_restricted_component_included_flag": (
            component.class_name == "LOCKED_OR_WITHDRAWAL_RESTRICTED_FUNDS"
        ),
        "pending_use_component_included_flag": component.class_name == "PENDING_USE_FUNDS",
        "unknown_component_blocks_new_exposure_flag": True,
        "unreconciled_component_blocks_new_exposure_flag": True,
        "accepted_source_evidence_required_flag": True,
        "private_state_read_receipt_required_future_pr": "PR112",
        "runtime_resolver_snapshot_future_pr": "PR116",
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
        "future_production_launch_path_preserved": True,
    }
    record.update(_atomicrows_metadata())
    record.update(_common_false_flags())
    record.update(_future_path_flags())
    return record


def _venue_binding(venue_id: str, account_scope_id: str, field_map_ids: list[str]) -> dict[str, object]:
    return {
        "venue_balance_semantic_binding_id": f"PR129_{venue_id}_BALANCE_SEMANTIC_BINDING_V1",
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "venue_balance_semantic_binding_state": READY_STATE,
        "production_runtime_cash_authority": False,
        "venue_id": venue_id,
        "account_scope_id": account_scope_id,
        "runtime_cash_component_field_map_ids": field_map_ids,
        "accepted_source_evidence_required_flag": True,
        "production_runtime_cash_receipt_authority": False,
        "production_new_exposure_cash_gate_authority": False,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
        **_common_false_flags(),
        **_future_path_flags(),
        **_atomicrows_metadata(),
    }


def _source_packet_rejections() -> list[dict[str, object]]:
    states = [
        REJECTED_MISSING_ACCEPTED_SOURCE_PACKET,
        REJECTED_MISSING_TARGET_FIELD_PATH,
        REJECTED_MISSING_RAW_FIELD_LOCATOR,
        REJECTED_STALE_ACCEPTED_PACKET,
        REJECTED_SUPERSEDED_ACCEPTED_PACKET,
        REJECTED_REVALIDATION_REQUIRED,
        REJECTED_CONNECTOR_BLOCKING_MATERIALITY,
        REJECTED_TRADING_BLOCKING_MATERIALITY,
        REJECTED_SCOPE_OR_VENUE_MISMATCH,
        REJECTED_PRIVATE_STATE_RECEIPT_REQUIRED_FUTURE_PR,
        REJECTED_ATOMICROWS_AUTHORITY_ATTEMPT,
    ]
    return [
        {
            "runtime_cash_component_source_packet_required_rejection_receipt_id": (
                f"PR129_SOURCE_PACKET_REJECTION_{index:02d}"
            ),
            "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
            "runtime_cash_field_map_state": state,
            "production_runtime_cash_authority": False,
            "venue_id": ACTIVE_STAGE1_VENUES[(index - 1) % len(ACTIVE_STAGE1_VENUES)],
            "canonical_cash_component_name": "verified_available_cash",
            "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
            "future_production_launch_path_preserved": True,
        }
        for index, state in enumerate(states, start=1)
    ]


def _unknown_component_rejections() -> list[dict[str, object]]:
    return [
        {
            "runtime_cash_component_unknown_rejection_receipt_id": (
                "PR129_FORECASTEX_IBKR_UNKNOWN_COMPONENT_REJECTION_V1"
            ),
            "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
            "runtime_cash_field_map_state": REJECTED_UNKNOWN_CASH_COMPONENT,
            "cash_component_reconciliation_state": REJECTED_UNRECONCILED_CASH_COMPONENT,
            "production_runtime_cash_authority": False,
            "venue_id": "FORECASTEX_IBKR",
            "canonical_cash_component_name": "fixture_unknown_cash_component",
            "cash_component_class": "UNKNOWN_OR_UNRECONCILED_COMPONENT",
            "unknown_component_blocks_new_exposure_flag": True,
            "unreconciled_component_blocks_new_exposure_flag": True,
            "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
            "future_production_launch_path_preserved": True,
        }
    ]


def _reconciliation_report(
    field_maps_by_venue: Mapping[str, list[dict[str, object]]],
    unknown_rejections: list[dict[str, object]],
) -> dict[str, object]:
    excluded_classes = {
        "MARGIN_LOCK",
        "UNSETTLED_FUNDS",
        "LOCKED_OR_WITHDRAWAL_RESTRICTED_FUNDS",
        "PENDING_USE_FUNDS",
    }
    excluded = [
        record["runtime_cash_component_field_map_id"]
        for field_maps in field_maps_by_venue.values()
        for record in field_maps
        if record["cash_component_class"] in excluded_classes
    ]
    reserve_component_ids = [
        record["runtime_cash_component_field_map_id"]
        for field_maps in field_maps_by_venue.values()
        for record in field_maps
        if record["cash_component_class"] == "REQUIRED_RESERVE"
    ]
    return {
        "runtime_cash_component_reconciliation_report_id": (
            "PR129_RUNTIME_CASH_COMPONENT_RECONCILIATION_REPORT_V1"
        ),
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "cash_component_reconciliation_state": READY_STATE,
        "production_runtime_cash_authority": False,
        "production_new_exposure_cash_gate_authority": False,
        "venue_ids": list(ACTIVE_STAGE1_VENUES),
        "excluded_component_ids": excluded,
        "reserved_component_ids": reserve_component_ids,
        "blocked_component_ids": [
            record["runtime_cash_component_unknown_rejection_receipt_id"]
            for record in unknown_rejections
        ],
        "unknown_component_present_flag": True,
        "unreconciled_component_present_flag": True,
        "excluded_reserved_cash_component_count": len(reserve_component_ids),
        "excluded_margin_lock_component_count": len(ACTIVE_STAGE1_VENUES),
        "excluded_unsettled_funds_component_count": len(ACTIVE_STAGE1_VENUES),
        "excluded_locked_or_withdrawal_restricted_component_count": len(ACTIVE_STAGE1_VENUES),
        "excluded_pending_use_component_count": len(ACTIVE_STAGE1_VENUES),
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
        **_common_false_flags(),
        **_future_path_flags(),
    }


def _available_receipts(
    *,
    accepted_fixture: Mapping[str, Any],
    field_maps_by_venue: Mapping[str, list[dict[str, object]]],
    reconciliation_report: Mapping[str, object],
) -> list[dict[str, object]]:
    receipts: list[dict[str, object]] = []
    amount_fixtures = accepted_fixture["fixture_amounts_by_venue"]
    for venue_id in ACTIVE_STAGE1_VENUES:
        amounts = amount_fixtures[venue_id]
        computed = compute_available_after_commitments_fixture(
            owner_policy_capital_remaining_for_venue_fixture=amounts[
                "owner_policy_capital_remaining_for_venue_fixture"
            ],
            runtime_verified_available_cash_fixture=amounts[
                "runtime_verified_available_cash_fixture"
            ],
            open_order_lock_total_fixture=amounts["open_order_lock_total_fixture"],
            required_reserve_total_fixture=amounts["required_reserve_total_fixture"],
        )
        field_maps = field_maps_by_venue[venue_id]
        excluded = [
            record["runtime_cash_component_field_map_id"]
            for record in field_maps
            if record["cash_component_class"]
            in {
                "MARGIN_LOCK",
                "UNSETTLED_FUNDS",
                "LOCKED_OR_WITHDRAWAL_RESTRICTED_FUNDS",
                "PENDING_USE_FUNDS",
            }
        ]
        blocked = (
            list(reconciliation_report["blocked_component_ids"])
            if venue_id == "FORECASTEX_IBKR"
            else []
        )
        record = {
            "runtime_available_after_commitments_receipt_id": (
                f"PR129_{venue_id}_AVAILABLE_AFTER_COMMITMENTS_RECEIPT_V1"
            ),
            "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
            "production_runtime_cash_receipt_authority": False,
            "available_after_commitments_state": READY_STATE,
            "runtime_cash_component_field_map_id": field_maps[0][
                "runtime_cash_component_field_map_id"
            ],
            "venue_id": venue_id,
            "owner_policy_capital_remaining_for_venue_fixture": amounts[
                "owner_policy_capital_remaining_for_venue_fixture"
            ],
            "runtime_verified_available_cash_fixture": amounts[
                "runtime_verified_available_cash_fixture"
            ],
            "open_order_lock_total_fixture": amounts["open_order_lock_total_fixture"],
            "required_reserve_total_fixture": amounts["required_reserve_total_fixture"],
            "excluded_component_ids": excluded,
            "blocked_component_ids": blocked,
            "cash_component_reconciliation_report_id": reconciliation_report[
                "runtime_cash_component_reconciliation_report_id"
            ],
            "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
            **computed,
            **_common_false_flags(),
            **_future_path_flags(),
        }
        receipts.append(record)
    return receipts


def _new_exposure_gate_receipts(
    *,
    available_receipts: list[dict[str, object]],
    field_maps_by_venue: Mapping[str, list[dict[str, object]]],
) -> list[dict[str, object]]:
    gate_receipts: list[dict[str, object]] = []
    for receipt in available_receipts:
        venue_id = str(receipt["venue_id"])
        amount = receipt["available_after_commitments_for_new_exposure_fixture"]["amount"]
        negative_or_zero = amount in {"0.00", "-0.00"}
        unknown = venue_id == "FORECASTEX_IBKR"
        blocked_reason_codes: list[str] = []
        if unknown:
            blocked_reason_codes.extend(
                ["UNKNOWN_CASH_COMPONENT_PRESENT", "UNRECONCILED_CASH_COMPONENT_PRESENT"]
            )
        if negative_or_zero:
            blocked_reason_codes.append("NEGATIVE_OR_ZERO_AVAILABLE_AFTER_COMMITMENTS")
        gate_receipts.append(
            {
                "new_exposure_cash_gate_receipt_id": (
                    f"PR129_{venue_id}_NEW_EXPOSURE_CASH_GATE_RECEIPT_V1"
                ),
                "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
                "production_new_exposure_cash_gate_authority": False,
                "new_exposure_cash_gate_state": (
                    READY_STATE if not blocked_reason_codes else REJECTED_UNRECONCILED_CASH_COMPONENT
                ),
                "venue_id": venue_id,
                "runtime_available_after_commitments_receipt_id": receipt[
                    "runtime_available_after_commitments_receipt_id"
                ],
                "runtime_cash_component_field_map_id": field_maps_by_venue[venue_id][0][
                    "runtime_cash_component_field_map_id"
                ],
                "source_change_snapshot_id": f"PR129_SOURCE_CHANGE_SNAPSHOT_{venue_id}",
                "new_or_increased_exposure_allowed_fixture": not blocked_reason_codes,
                "blocked_reason_codes": blocked_reason_codes,
                "unknown_component_present_flag": unknown,
                "unreconciled_component_present_flag": unknown,
                "stale_cash_source_present_flag": False,
                "connector_blocking_cash_materiality_present_flag": False,
                "trading_blocking_cash_materiality_present_flag": False,
                "negative_or_zero_available_after_commitments_flag": negative_or_zero,
                "order_authority_allowed_flag": False,
                "production_order_authority_allowed_flag": False,
                "future_production_launch_path_preserved": True,
                "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
            }
        )
    return gate_receipts


def _decimal_policy_fixture() -> dict[str, object]:
    return {
        "runtime_cash_decimal_policy_id": "PR129_RUNTIME_CASH_DECIMAL_POLICY_V1",
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "runtime_cash_decimal_policy_state": READY_STATE,
        "cash_math_type": "decimal.Decimal",
        "binary_float_cash_math_allowed": False,
        "monetary_values_stored_as_strings": True,
        "currency_scales": {"USD": 2},
        "rounding_mode": "ROUND_HALF_EVEN",
        "missing_unknown_values_silent_zero_allowed": False,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
    }


def _report_paths(repo_root: Path) -> dict[str, bool]:
    return {
        "pr106_acceptance_artifacts_consumed": _path_exists(
            repo_root,
            "docs/master_plan/source_evidence/generated/AcceptedSourceEvidenceAcceptanceExecutor.report.json",
        ),
        "pr124_connector_binding_artifacts_consumed": _path_exists(
            repo_root,
            "docs/master_plan/source_evidence/generated/CODEX_PR124_ACCEPTED_SOURCE_TO_CONNECTOR_SEMANTIC_BINDING_CONSUMER_GATE_REPORT.json",
        ),
        "pr125_revalidation_artifacts_consumed": _path_exists(
            repo_root,
            "docs/master_plan/source_evidence/generated/SourceRevalidationScheduler.report.json",
        ),
        "pr126_implementation_gate_artifacts_consumed": _path_exists(
            repo_root,
            "docs/master_plan/source_evidence/generated/ConnectorSemanticBindingImplementationGate.report.json",
        ),
        "pr127_execution_lifecycle_artifacts_consumed": _path_exists(
            repo_root,
            "docs/master_plan/source_evidence/generated/PerVenueExecutionLifecycleModelBuilder.report.json",
        ),
        "pr128_cross_venue_normalization_artifacts_consumed": _path_exists(
            repo_root,
            "docs/master_plan/source_evidence/generated/CrossVenueExecutionDownstreamHandoff.report.json",
        ),
    }


def _main_report(
    *,
    repo_root: Path,
    field_maps: list[dict[str, object]],
    venue_bindings: list[dict[str, object]],
    source_rejections: list[dict[str, object]],
    unknown_rejections: list[dict[str, object]],
    reconciliation_report: Mapping[str, object],
    available_receipts: list[dict[str, object]],
    gate_receipts: list[dict[str, object]],
    handoff: Mapping[str, object],
) -> dict[str, object]:
    source_rejection_states = [record["runtime_cash_field_map_state"] for record in source_rejections]
    report = {
        "repo_pr_label": "PR129",
        "roadmap_pr_implemented": "PR111",
        "currentized_prior_repo_pr": "PR128",
        "checked_github_pr_number": 128,
        "owner_authorized_capability": "RUNTIME_CASH_COMPONENT_FIELD_MAP_EXECUTOR",
        **_report_paths(repo_root),
        "runtime_cash_component_field_map_schema_created": True,
        "venue_balance_semantic_binding_schema_created": True,
        "runtime_cash_decimal_policy_schema_created": True,
        "runtime_available_after_commitments_receipt_schema_created": True,
        "source_packet_required_rejection_receipt_schema_created": True,
        "unknown_cash_component_rejection_receipt_schema_created": True,
        "runtime_cash_component_reconciliation_report_schema_created": True,
        "new_exposure_cash_gate_receipt_schema_created": True,
        "runtime_cash_downstream_handoff_schema_created": True,
        "runtime_cash_field_map_validator_created": True,
        "available_after_commitments_fixture_computer_created": True,
        "deterministic_decimal_money_helper_created": True,
        "validation_cli_created": True,
        "fixture_stage1_venue_count": len(ACTIVE_STAGE1_VENUES),
        "shared_scope_metadata_count": len(SHARED_SCOPE_METADATA),
        "prediction_markets_general_treated_as_shared_scope": True,
        "fixture_runtime_cash_field_map_count": len(field_maps),
        "fixture_venue_balance_semantic_binding_count": len(venue_bindings),
        "fixture_available_after_commitments_receipt_count": len(available_receipts),
        "fixture_source_packet_required_rejection_receipt_count": len(source_rejections),
        "fixture_unknown_cash_component_rejection_receipt_count": len(unknown_rejections),
        "fixture_reconciliation_report_count": 1,
        "fixture_new_exposure_cash_gate_receipt_count": len(gate_receipts),
        "fixture_runtime_cash_downstream_handoff_count": 1,
        "production_runtime_cash_authority_count": 0,
        "production_runtime_cash_receipt_authority_count": 0,
        "production_new_exposure_cash_gate_authority_count": 0,
        "production_order_authority_count": 0,
        "production_connector_client_count": 0,
        "fixture_outputs_marked_not_production_runtime_cash": True,
        "missing_source_packet_rejection_count": source_rejection_states.count(
            REJECTED_MISSING_ACCEPTED_SOURCE_PACKET
        ),
        "missing_target_field_path_rejection_count": source_rejection_states.count(
            REJECTED_MISSING_TARGET_FIELD_PATH
        ),
        "missing_raw_field_locator_rejection_count": source_rejection_states.count(
            REJECTED_MISSING_RAW_FIELD_LOCATOR
        ),
        "unknown_cash_component_block_count": len(unknown_rejections),
        "unreconciled_cash_component_block_count": len(unknown_rejections),
        "stale_packet_rejection_count": source_rejection_states.count(REJECTED_STALE_ACCEPTED_PACKET),
        "superseded_packet_rejection_count": source_rejection_states.count(
            REJECTED_SUPERSEDED_ACCEPTED_PACKET
        ),
        "revalidation_required_rejection_count": source_rejection_states.count(
            REJECTED_REVALIDATION_REQUIRED
        ),
        "connector_blocking_cash_materiality_rejection_count": source_rejection_states.count(
            REJECTED_CONNECTOR_BLOCKING_MATERIALITY
        ),
        "trading_blocking_cash_materiality_rejection_count": source_rejection_states.count(
            REJECTED_TRADING_BLOCKING_MATERIALITY
        ),
        "scope_or_venue_mismatch_rejection_count": source_rejection_states.count(
            REJECTED_SCOPE_OR_VENUE_MISMATCH
        ),
        "excluded_reserved_cash_component_count": reconciliation_report[
            "excluded_reserved_cash_component_count"
        ],
        "excluded_margin_lock_component_count": reconciliation_report[
            "excluded_margin_lock_component_count"
        ],
        "excluded_unsettled_funds_component_count": reconciliation_report[
            "excluded_unsettled_funds_component_count"
        ],
        "excluded_locked_or_withdrawal_restricted_component_count": reconciliation_report[
            "excluded_locked_or_withdrawal_restricted_component_count"
        ],
        "excluded_pending_use_component_count": reconciliation_report[
            "excluded_pending_use_component_count"
        ],
        "conservative_min_formula_applied": True,
        "negative_available_after_commitments_clamped_to_zero_count": sum(
            1
            for receipt in available_receipts
            if receipt["negative_available_after_commitments_clamped_to_zero_flag"]
        ),
        "decimal_cash_math_used": True,
        "binary_float_cash_math_used": False,
        "upstream_fixture_mutation_count": 0,
        "deterministic_fixture_time_used": True,
        "runtime_cash_field_map_runs_in_production_pretrade_path": False,
        "future_private_state_read_receipt_path_preserved": True,
        "future_credential_alias_secret_no_capture_path_preserved": True,
        "future_market_data_ingest_path_preserved": True,
        "future_orderbook_event_snapshot_path_preserved": True,
        "future_runtime_resolver_snapshot_path_preserved": True,
        "future_atomicrows_bridge_path_preserved": True,
        "future_atomicrows_bridge_materialization_recommended_after_repo_pr": "PR135",
        "future_official_source_production_path_recorded": True,
        "future_production_launch_path_preserved": True,
        "production_values_filled_by_later_official_source_or_private_state_receipt_prs": True,
        "atomicrows_bundle_consumed": False,
        "atomicrows_bundle_created": False,
        "atomicrows_sha_created": False,
        "atomicrows_row_records_created_count": 0,
        "atomicrows_authority_created": False,
        "runtime_resolver_snapshot_created_count": 0,
        "production_runtime_authority_created": False,
        "order_authority_created": False,
        "runtime_cash_receipts_created_count": 0,
        "private_state_fetch_created_count": 0,
        "replay_paper_results_created_count": 0,
        "connector_production_client_created_count": 0,
        "network_io_created_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_simulator_execution_count": 0,
        "optimizer_execution_count": 0,
        "quantum_advantage_claim_created": False,
        "latency_superiority_claim_created": False,
        "execution_superiority_claim_created": False,
        "profit_evidence_created": False,
        "master_plan_modified": False,
        "atomicrows_bundle_file_modified": False,
        "atomicrows_sha_file_modified": False,
        "run_validation_gates_uses_fresh_pytest_basetemp": True,
        "fixed_tmp_run_validation_gates_pytest_reused": False,
        "future_official_source_production_path": [
            "official-source retrieval jobs/agents",
            "production candidate source-evidence packets",
            "PR106 acceptance executor validation",
            "accepted source-evidence ledger production records",
            "PR124 connector semantic binding production records",
            "PR125 revalidation/supersession/materiality freshness snapshots",
            "PR126 connector semantic implementation gate",
            "PR127 per-venue execution lifecycle model builder",
            "PR128 cross-venue execution normalization binding",
            "PR129 runtime cash component field-map executor",
            "PR112 account/wallet/balance/private-state read receipts",
            "PR113 credential alias and secret no-capture readiness",
            "PR114 market-data ingest",
            "PR115 orderbook/event-state snapshots",
            "PR116 runtime resolver snapshot executor",
            "replay/paper and production trading gates",
        ],
        "runtime_cash_downstream_handoff_id": handoff["runtime_cash_downstream_handoff_id"],
    }
    return report


def build_runtime_cash_artifacts(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    fixture_path = repo_root / PR129_FIXTURE_DIR / "accepted_source_evidence_records.v1.fixture.json"
    accepted_fixture = _load_json(fixture_path)
    if tuple(accepted_fixture["active_stage1_venues"]) != ACTIVE_STAGE1_VENUES:
        raise ValueError("PR129 fixture must contain exactly the three active Stage-1 venues")
    if tuple(accepted_fixture["shared_scope_metadata"]) != SHARED_SCOPE_METADATA:
        raise ValueError("PREDICTION_MARKETS_GENERAL must remain shared scope metadata")

    lookup = _component_lookup(accepted_fixture)
    field_maps: list[dict[str, object]] = []
    field_maps_by_venue: dict[str, list[dict[str, object]]] = {venue_id: [] for venue_id in ACTIVE_STAGE1_VENUES}
    venue_bindings: list[dict[str, object]] = []
    for venue_id in ACTIVE_STAGE1_VENUES:
        account_scope_id = f"PR129_{venue_id}_FIXTURE_ACCOUNT_SCOPE"
        venue_field_maps: list[dict[str, object]] = []
        for component in COMPONENTS:
            source_record = lookup[(venue_id, component.class_name)]
            field_map = _field_map_record(
                venue_id=venue_id,
                account_scope_id=account_scope_id,
                component=component,
                source_record=source_record,
            )
            venue_field_maps.append(field_map)
            field_maps.append(field_map)
        field_maps_by_venue[venue_id] = venue_field_maps
        venue_bindings.append(
            _venue_binding(
                venue_id,
                account_scope_id,
                [record["runtime_cash_component_field_map_id"] for record in venue_field_maps],
            )
        )

    source_rejections = _source_packet_rejections()
    unknown_rejections = _unknown_component_rejections()
    reconciliation = _reconciliation_report(field_maps_by_venue, unknown_rejections)
    available_receipts = _available_receipts(
        accepted_fixture=accepted_fixture,
        field_maps_by_venue=field_maps_by_venue,
        reconciliation_report=reconciliation,
    )
    gate_receipts = _new_exposure_gate_receipts(
        available_receipts=available_receipts,
        field_maps_by_venue=field_maps_by_venue,
    )
    handoff = build_runtime_cash_downstream_handoff(
        field_map_ids=[record["runtime_cash_component_field_map_id"] for record in field_maps],
        available_receipt_ids=[
            record["runtime_available_after_commitments_receipt_id"]
            for record in available_receipts
        ],
        gate_receipt_ids=[
            record["new_exposure_cash_gate_receipt_id"] for record in gate_receipts
        ],
    )
    field_map_report = {
        "runtime_cash_component_field_map_report_id": (
            "PR129_RUNTIME_CASH_COMPONENT_FIELD_MAP_REPORT_V1"
        ),
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "runtime_cash_field_map_state": READY_STATE,
        "active_stage1_venues": list(ACTIVE_STAGE1_VENUES),
        "shared_scope_metadata": list(SHARED_SCOPE_METADATA),
        "prediction_markets_general_treated_as_shared_scope": True,
        "runtime_cash_decimal_policy": _decimal_policy_fixture(),
        "runtime_cash_component_field_maps": field_maps,
        "venue_balance_semantic_bindings": venue_bindings,
        "source_packet_required_rejection_receipts": source_rejections,
        "unknown_cash_component_rejection_receipts": unknown_rejections,
        "production_runtime_cash_authority": False,
        "production_runtime_cash_receipt_authority": False,
        "production_new_exposure_cash_gate_authority": False,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
    }
    reconciliation_report = {
        "runtime_cash_component_reconciliation_report_package_id": (
            "PR129_RUNTIME_CASH_COMPONENT_RECONCILIATION_PACKAGE_V1"
        ),
        "reconciliation_reports": [reconciliation],
    }
    available_report = {
        "runtime_available_after_commitments_fixture_report_id": (
            "PR129_RUNTIME_AVAILABLE_AFTER_COMMITMENTS_FIXTURE_REPORT_V1"
        ),
        "available_after_commitments_state": READY_STATE,
        "runtime_available_after_commitments_receipts": available_receipts,
        "production_runtime_cash_receipt_authority": False,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
    }
    gate_report = {
        "new_exposure_cash_gate_fixture_report_id": "PR129_NEW_EXPOSURE_CASH_GATE_FIXTURE_REPORT_V1",
        "new_exposure_cash_gate_state": READY_STATE,
        "new_exposure_cash_gate_receipts": gate_receipts,
        "production_new_exposure_cash_gate_authority": False,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
    }
    handoff_report = {
        "runtime_cash_downstream_handoff_report_id": "PR129_RUNTIME_CASH_DOWNSTREAM_HANDOFF_REPORT_V1",
        "runtime_cash_downstream_handoff": handoff,
    }
    main_report = _main_report(
        repo_root=repo_root,
        field_maps=field_maps,
        venue_bindings=venue_bindings,
        source_rejections=source_rejections,
        unknown_rejections=unknown_rejections,
        reconciliation_report=reconciliation,
        available_receipts=available_receipts,
        gate_receipts=gate_receipts,
        handoff=handoff,
    )
    return {
        "main_report": main_report,
        "field_map_report": field_map_report,
        "reconciliation_report": reconciliation_report,
        "available_report": available_report,
        "handoff_report": handoff_report,
        "gate_report": gate_report,
    }
