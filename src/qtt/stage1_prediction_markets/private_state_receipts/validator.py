from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.qtt.stage1_prediction_markets.private_state_receipts.canonical_redaction import (
    canonical_redacted_payload_digest,
    validate_redacted_payload_minimized,
)
from src.qtt.stage1_prediction_markets.private_state_receipts.handoff import (
    build_private_state_downstream_handoff,
)
from src.qtt.stage1_prediction_markets.private_state_receipts.linkage import (
    build_account_wallet_balance_receipts,
    build_linkage_receipts,
)
from src.qtt.stage1_prediction_markets.private_state_receipts.receipt import (
    build_private_state_read_receipt,
)
from src.qtt.stage1_prediction_markets.private_state_receipts.redaction import (
    build_no_secret_capture_attestation,
    build_redacted_payload,
    build_redaction_attestation,
)
from src.qtt.stage1_prediction_markets.private_state_receipts.request import (
    ACTIVE_STAGE1_VENUES,
    DETERMINISTIC_FIXTURE_TIME,
    FIXTURE_AUTHORITY_CLASS,
    READY_STATE,
    REJECTED_ATOMICROWS_AUTHORITY_ATTEMPT,
    REJECTED_CREDENTIAL_ALIAS_AUTHORITY_ATTEMPT,
    REJECTED_MISSING_CREDENTIAL_ALIAS_PLACEHOLDER,
    REJECTED_MISSING_NO_SECRET_CAPTURE_ATTESTATION,
    REJECTED_MISSING_REDACTION_ATTESTATION,
    REJECTED_MISSING_RUNTIME_CASH_FIELD_MAP,
    REJECTED_NETWORK_IO_ATTEMPT,
    REJECTED_PRODUCTION_PRIVATE_STATE_FETCH_ATTEMPT,
    REJECTED_PRODUCTION_RUNTIME_CASH_AUTHORITY_ATTEMPT,
    REJECTED_SCOPE_OR_VENUE_MISMATCH,
    REJECTED_SECRET_CAPTURE_ATTEMPT,
    REJECTED_STALE_PRIVATE_STATE_RECEIPT,
    REJECTED_SUPERSEDED_PRIVATE_STATE_RECEIPT,
    REJECTED_UNREDACTED_PRIVATE_STATE_PAYLOAD,
    SHARED_SCOPE_METADATA,
    build_private_state_read_requests,
)


GENERATED_DIR = Path("docs/master_plan/source_evidence/generated")
FIXTURE_DIR = Path("tests/fixtures/source_evidence/pr130_private_state_read_receipts")
MAIN_REPORT_PATH = GENERATED_DIR / (
    "CODEX_PR130_ACCOUNT_WALLET_BALANCE_PRIVATE_STATE_READ_RECEIPT_GATE_REPORT.json"
)
GATE_REPORT_PATH = GENERATED_DIR / "PrivateStateReadReceiptGate.report.json"
ACCOUNT_REPORT_PATH = GENERATED_DIR / "AccountWalletBalancePrivateStateReceipt.report.json"
REDACTION_REPORT_PATH = GENERATED_DIR / "PrivateStateRedactionNoSecretCapture.report.json"
LINKAGE_REPORT_PATH = GENERATED_DIR / "PrivateStateToRuntimeCashLinkage.report.json"
HANDOFF_REPORT_PATH = GENERATED_DIR / "PrivateStateDownstreamHandoff.report.json"

REPORT_PATHS = {
    "main_report": MAIN_REPORT_PATH,
    "gate_report": GATE_REPORT_PATH,
    "account_report": ACCOUNT_REPORT_PATH,
    "redaction_report": REDACTION_REPORT_PATH,
    "linkage_report": LINKAGE_REPORT_PATH,
    "handoff_report": HANDOFF_REPORT_PATH,
}

SCHEMA_DIR = Path("src/qtt/stage1_prediction_markets/private_state_receipts")
SCHEMA_FILES = (
    "private_state_read_request.schema.json",
    "private_state_read_receipt.schema.json",
    "account_wallet_balance_receipt.schema.json",
    "private_state_redaction_attestation.schema.json",
    "private_state_no_secret_capture_attestation.schema.json",
    "private_state_read_rejection_receipt.schema.json",
    "private_state_to_runtime_cash_linkage_receipt.schema.json",
    "private_state_downstream_handoff.schema.json",
)

PR129_FIELD_MAP_REPORT_PATH = GENERATED_DIR / "RuntimeCashComponentFieldMap.report.json"
PR129_HANDOFF_REPORT_PATH = GENERATED_DIR / "RuntimeCashDownstreamHandoff.report.json"

REJECTION_STATES = (
    REJECTED_MISSING_RUNTIME_CASH_FIELD_MAP,
    REJECTED_MISSING_CREDENTIAL_ALIAS_PLACEHOLDER,
    REJECTED_CREDENTIAL_ALIAS_AUTHORITY_ATTEMPT,
    REJECTED_SECRET_CAPTURE_ATTEMPT,
    REJECTED_UNREDACTED_PRIVATE_STATE_PAYLOAD,
    REJECTED_MISSING_REDACTION_ATTESTATION,
    REJECTED_MISSING_NO_SECRET_CAPTURE_ATTESTATION,
    REJECTED_SCOPE_OR_VENUE_MISMATCH,
    REJECTED_STALE_PRIVATE_STATE_RECEIPT,
    REJECTED_SUPERSEDED_PRIVATE_STATE_RECEIPT,
    REJECTED_PRODUCTION_PRIVATE_STATE_FETCH_ATTEMPT,
    REJECTED_NETWORK_IO_ATTEMPT,
    REJECTED_PRODUCTION_RUNTIME_CASH_AUTHORITY_ATTEMPT,
    REJECTED_ATOMICROWS_AUTHORITY_ATTEMPT,
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _path_exists(repo_root: Path, path: str | Path) -> bool:
    return (repo_root / Path(path)).exists()


def _field_maps_by_venue(field_map_report: Mapping[str, Any]) -> dict[str, list[dict[str, object]]]:
    records = [
        dict(record)
        for record in field_map_report["runtime_cash_component_field_maps"]
    ]
    grouped: dict[str, list[dict[str, object]]] = {
        venue_id: [] for venue_id in ACTIVE_STAGE1_VENUES
    }
    for record in records:
        venue_id = str(record["venue_id"])
        if venue_id in grouped:
            grouped[venue_id].append(record)
    return grouped


def _runtime_cash_handoff(handoff_report: Mapping[str, Any]) -> dict[str, object]:
    return dict(handoff_report["runtime_cash_downstream_handoff"])


def _build_rejection_receipts() -> list[dict[str, object]]:
    receipts: list[dict[str, object]] = []
    for index, state in enumerate(REJECTION_STATES, start=1):
        venue_id = ACTIVE_STAGE1_VENUES[(index - 1) % len(ACTIVE_STAGE1_VENUES)]
        receipts.append(
            {
                "private_state_read_rejection_receipt_id": (
                    f"PR130_PRIVATE_STATE_READ_REJECTION_{index:02d}_V1"
                ),
                "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
                "private_state_read_receipt_state": state,
                "venue_id": venue_id,
                "platform_scope": "PREDICTION_MARKETS_GENERAL",
                "production_private_state_read_authority": False,
                "production_account_balance_authority": False,
                "production_wallet_balance_authority": False,
                "production_runtime_cash_receipt_authority": False,
                "production_new_exposure_cash_gate_authority": False,
                "credential_alias_authority_created": False,
                "credential_readiness_authority_created": False,
                "network_io_allowed_flag": False,
                "production_connector_use_allowed_flag": False,
                "order_execution_allowed_flag": False,
                "order_routing_authority_allowed_flag": False,
                "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
                "future_production_launch_path_preserved": True,
            }
        )
    return receipts


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
        "pr129_runtime_cash_artifacts_consumed": _path_exists(
            repo_root,
            PR129_FIELD_MAP_REPORT_PATH,
        )
        and _path_exists(repo_root, PR129_HANDOFF_REPORT_PATH),
    }


def _main_report(
    *,
    repo_root: Path,
    requests: list[dict[str, object]],
    private_state_receipts: list[dict[str, object]],
    account_receipts: list[dict[str, object]],
    redaction_attestations: list[dict[str, object]],
    no_secret_attestations: list[dict[str, object]],
    rejection_receipts: list[dict[str, object]],
    linkage_receipts: list[dict[str, object]],
    handoff: Mapping[str, object],
) -> dict[str, object]:
    states = [record["private_state_read_receipt_state"] for record in rejection_receipts]
    report = {
        "repo_pr_label": "PR130",
        "roadmap_pr_implemented": "PR112",
        "currentized_prior_repo_pr": "PR129",
        "checked_github_pr_number": 129,
        "owner_authorized_capability": (
            "ACCOUNT_WALLET_BALANCE_AND_PRIVATE_STATE_READ_RECEIPT_GATE"
        ),
        **_report_paths(repo_root),
        "private_state_read_request_schema_created": _path_exists(
            repo_root, SCHEMA_DIR / "private_state_read_request.schema.json"
        ),
        "private_state_read_receipt_schema_created": _path_exists(
            repo_root, SCHEMA_DIR / "private_state_read_receipt.schema.json"
        ),
        "account_wallet_balance_receipt_schema_created": _path_exists(
            repo_root, SCHEMA_DIR / "account_wallet_balance_receipt.schema.json"
        ),
        "private_state_redaction_attestation_schema_created": _path_exists(
            repo_root, SCHEMA_DIR / "private_state_redaction_attestation.schema.json"
        ),
        "private_state_no_secret_capture_attestation_schema_created": _path_exists(
            repo_root, SCHEMA_DIR / "private_state_no_secret_capture_attestation.schema.json"
        ),
        "private_state_read_rejection_receipt_schema_created": _path_exists(
            repo_root, SCHEMA_DIR / "private_state_read_rejection_receipt.schema.json"
        ),
        "private_state_to_runtime_cash_linkage_receipt_schema_created": _path_exists(
            repo_root,
            SCHEMA_DIR / "private_state_to_runtime_cash_linkage_receipt.schema.json",
        ),
        "private_state_downstream_handoff_schema_created": _path_exists(
            repo_root, SCHEMA_DIR / "private_state_downstream_handoff.schema.json"
        ),
        "canonical_redaction_digest_helper_created": True,
        "private_state_receipt_gate_validator_created": True,
        "redaction_no_secret_validator_created": True,
        "validation_cli_created": _path_exists(
            repo_root,
            "tools/private_state_read_receipt_gate_validate.py",
        ),
        "fixture_stage1_venue_count": len(ACTIVE_STAGE1_VENUES),
        "shared_scope_metadata_count": len(SHARED_SCOPE_METADATA),
        "prediction_markets_general_treated_as_shared_scope": True,
        "fixture_private_state_read_request_count": len(requests),
        "fixture_private_state_read_receipt_count": len(private_state_receipts),
        "fixture_account_wallet_balance_receipt_count": len(account_receipts),
        "fixture_redaction_attestation_count": len(redaction_attestations),
        "fixture_no_secret_capture_attestation_count": len(no_secret_attestations),
        "fixture_private_state_to_runtime_cash_linkage_count": len(linkage_receipts),
        "fixture_private_state_downstream_handoff_count": 1,
        "fixture_private_state_rejection_receipt_count": len(rejection_receipts),
        "production_private_state_read_authority_count": 0,
        "production_account_balance_authority_count": 0,
        "production_wallet_balance_authority_count": 0,
        "production_runtime_cash_receipt_authority_count": 0,
        "production_credential_alias_authority_count": 0,
        "production_credential_readiness_authority_count": 0,
        "production_order_authority_count": 0,
        "production_connector_client_count": 0,
        "fixture_outputs_marked_not_production_private_state": True,
        "missing_runtime_cash_field_map_rejection_count": states.count(
            REJECTED_MISSING_RUNTIME_CASH_FIELD_MAP
        ),
        "missing_credential_alias_placeholder_rejection_count": states.count(
            REJECTED_MISSING_CREDENTIAL_ALIAS_PLACEHOLDER
        ),
        "credential_alias_authority_attempt_rejection_count": states.count(
            REJECTED_CREDENTIAL_ALIAS_AUTHORITY_ATTEMPT
        ),
        "secret_capture_attempt_rejection_count": states.count(
            REJECTED_SECRET_CAPTURE_ATTEMPT
        ),
        "unredacted_private_state_payload_rejection_count": states.count(
            REJECTED_UNREDACTED_PRIVATE_STATE_PAYLOAD
        ),
        "missing_redaction_attestation_rejection_count": states.count(
            REJECTED_MISSING_REDACTION_ATTESTATION
        ),
        "missing_no_secret_capture_attestation_rejection_count": states.count(
            REJECTED_MISSING_NO_SECRET_CAPTURE_ATTESTATION
        ),
        "scope_or_venue_mismatch_rejection_count": states.count(
            REJECTED_SCOPE_OR_VENUE_MISMATCH
        ),
        "stale_private_state_receipt_rejection_count": states.count(
            REJECTED_STALE_PRIVATE_STATE_RECEIPT
        ),
        "superseded_private_state_receipt_rejection_count": states.count(
            REJECTED_SUPERSEDED_PRIVATE_STATE_RECEIPT
        ),
        "production_private_state_fetch_attempt_rejection_count": states.count(
            REJECTED_PRODUCTION_PRIVATE_STATE_FETCH_ATTEMPT
        ),
        "raw_api_key_stored_count": 0,
        "raw_bearer_token_stored_count": 0,
        "raw_oauth_token_stored_count": 0,
        "raw_token_stored_count": 0,
        "raw_cookie_stored_count": 0,
        "raw_wallet_secret_stored_count": 0,
        "raw_private_key_stored_count": 0,
        "raw_session_identifier_stored_count": 0,
        "raw_private_payload_stored_count": 0,
        "canonical_redacted_payload_digest_deterministic": True,
        "data_minimization_enforced": True,
        "upstream_fixture_mutation_count": 0,
        "deterministic_fixture_time_used": True,
        "private_state_read_receipt_gate_runs_in_production_pretrade_path": False,
        "future_credential_alias_secret_no_capture_path_preserved": True,
        "future_market_data_ingest_path_preserved": True,
        "future_orderbook_event_snapshot_path_preserved": True,
        "future_runtime_resolver_snapshot_path_preserved": True,
        "future_atomicrows_bridge_path_preserved": True,
        "future_atomicrows_bridge_materialization_recommended_after_repo_pr": "PR135",
        "future_official_source_private_state_production_path_recorded": True,
        "future_production_launch_path_preserved": True,
        "production_values_filled_by_later_private_state_receipt_or_runtime_prs": True,
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
        "future_official_source_private_state_production_path": [
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
            "PR130 account/wallet/balance/private-state read receipt gate",
            "PR113 credential alias and secret no-capture readiness",
            "PR114 market-data ingest",
            "PR115 orderbook/event-state snapshots",
            "PR116 runtime resolver snapshot executor",
            "replay/paper and production trading gates",
        ],
        "private_state_downstream_handoff_id": handoff["private_state_downstream_handoff_id"],
    }
    return report


def build_private_state_read_receipt_artifacts(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    field_map_report = _load_json(repo_root / PR129_FIELD_MAP_REPORT_PATH)
    runtime_cash_handoff = _runtime_cash_handoff(
        _load_json(repo_root / PR129_HANDOFF_REPORT_PATH)
    )
    field_maps_by_venue = _field_maps_by_venue(field_map_report)
    if set(field_maps_by_venue) != set(ACTIVE_STAGE1_VENUES):
        raise ValueError("PR130 requires exactly the three active Stage-1 venues")
    if tuple(runtime_cash_handoff["venue_ids_in_scope"]) != ACTIVE_STAGE1_VENUES:
        raise ValueError("PR129 runtime cash handoff must cover exactly Stage-1 venues")

    requests = build_private_state_read_requests(field_maps_by_venue)
    redacted_payloads_by_receipt: dict[str, dict[str, object]] = {}
    private_state_receipts: list[dict[str, object]] = []
    redaction_attestations: list[dict[str, object]] = []
    no_secret_attestations: list[dict[str, object]] = []
    for request in requests:
        redacted_payload = build_redacted_payload(request)
        private_state_receipt = build_private_state_read_receipt(
            request=request,
            redacted_payload=redacted_payload,
        )
        receipt_id = str(private_state_receipt["private_state_read_receipt_id"])
        redacted_payloads_by_receipt[receipt_id] = redacted_payload
        private_state_receipts.append(private_state_receipt)
        redaction_attestations.append(
            build_redaction_attestation(
                receipt_id=receipt_id,
                redacted_payload=redacted_payload,
            )
        )
        no_secret_attestations.append(
            build_no_secret_capture_attestation(
                receipt_id=receipt_id,
                credential_placeholder=str(request["credential_alias_placeholder_ref"]),
            )
        )

    account_receipts = build_account_wallet_balance_receipts(
        private_state_receipts=private_state_receipts,
        field_maps_by_venue=field_maps_by_venue,
    )
    linkage_receipts = build_linkage_receipts(
        private_state_receipts=private_state_receipts,
        account_wallet_balance_receipts=account_receipts,
        runtime_cash_handoff=runtime_cash_handoff,
    )
    rejection_receipts = _build_rejection_receipts()
    handoff = build_private_state_downstream_handoff(
        private_state_read_receipts=private_state_receipts,
        account_wallet_balance_receipts=account_receipts,
        linkage_receipts=linkage_receipts,
    )
    gate_report = {
        "private_state_read_receipt_gate_report_id": "PR130_PRIVATE_STATE_READ_RECEIPT_GATE_REPORT_V1",
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "private_state_read_request_state": READY_STATE,
        "private_state_read_receipt_state": READY_STATE,
        "active_stage1_venues": list(ACTIVE_STAGE1_VENUES),
        "shared_scope_metadata": list(SHARED_SCOPE_METADATA),
        "prediction_markets_general_treated_as_shared_scope": True,
        "private_state_read_requests": requests,
        "private_state_read_receipts": private_state_receipts,
        "private_state_read_rejection_receipts": rejection_receipts,
        "production_private_state_read_authority": False,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
    }
    account_report = {
        "account_wallet_balance_private_state_receipt_report_id": (
            "PR130_ACCOUNT_WALLET_BALANCE_PRIVATE_STATE_RECEIPT_REPORT_V1"
        ),
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "account_wallet_balance_receipt_state": READY_STATE,
        "account_wallet_balance_receipts": account_receipts,
        "production_account_balance_authority": False,
        "production_wallet_balance_authority": False,
        "production_runtime_cash_receipt_authority": False,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
    }
    redaction_report = {
        "private_state_redaction_no_secret_capture_report_id": (
            "PR130_PRIVATE_STATE_REDACTION_NO_SECRET_CAPTURE_REPORT_V1"
        ),
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "redaction_attestation_state": READY_STATE,
        "no_secret_capture_state": READY_STATE,
        "private_state_redaction_attestations": redaction_attestations,
        "private_state_no_secret_capture_attestations": no_secret_attestations,
        "raw_secret_capture_allowed_flag": False,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
    }
    linkage_report = {
        "private_state_to_runtime_cash_linkage_report_id": (
            "PR130_PRIVATE_STATE_TO_RUNTIME_CASH_LINKAGE_REPORT_V1"
        ),
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "private_state_to_runtime_cash_linkage_state": READY_STATE,
        "private_state_to_runtime_cash_linkage_receipts": linkage_receipts,
        "production_runtime_cash_receipt_authority": False,
        "production_new_exposure_cash_gate_authority": False,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
    }
    handoff_report = {
        "private_state_downstream_handoff_report_id": (
            "PR130_PRIVATE_STATE_DOWNSTREAM_HANDOFF_REPORT_V1"
        ),
        "private_state_downstream_handoff": handoff,
    }
    main_report = _main_report(
        repo_root=repo_root,
        requests=requests,
        private_state_receipts=private_state_receipts,
        account_receipts=account_receipts,
        redaction_attestations=redaction_attestations,
        no_secret_attestations=no_secret_attestations,
        rejection_receipts=rejection_receipts,
        linkage_receipts=linkage_receipts,
        handoff=handoff,
    )
    return {
        "main_report": main_report,
        "gate_report": gate_report,
        "account_report": account_report,
        "redaction_report": redaction_report,
        "linkage_report": linkage_report,
        "handoff_report": handoff_report,
        "redacted_payloads_by_receipt": redacted_payloads_by_receipt,
        "field_maps_by_venue": field_maps_by_venue,
        "runtime_cash_handoff": runtime_cash_handoff,
    }


def validate_artifacts(artifacts: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    main = artifacts["main_report"]
    gate_report = artifacts["gate_report"]
    account_report = artifacts["account_report"]
    redaction_report = artifacts["redaction_report"]
    linkage_report = artifacts["linkage_report"]
    handoff = artifacts["handoff_report"]["private_state_downstream_handoff"]
    redacted_payloads = artifacts["redacted_payloads_by_receipt"]
    field_maps_by_venue = artifacts["field_maps_by_venue"]
    runtime_cash_handoff = artifacts["runtime_cash_handoff"]

    requests = gate_report["private_state_read_requests"]
    private_state_receipts = gate_report["private_state_read_receipts"]
    rejections = gate_report["private_state_read_rejection_receipts"]
    account_receipts = account_report["account_wallet_balance_receipts"]
    redaction_attestations = redaction_report["private_state_redaction_attestations"]
    no_secret_attestations = redaction_report["private_state_no_secret_capture_attestations"]
    linkage_receipts = linkage_report["private_state_to_runtime_cash_linkage_receipts"]

    if {record["venue_id"] for record in requests} != set(ACTIVE_STAGE1_VENUES):
        failures.append("private-state read requests must cover exactly the three Stage-1 venues")
    if "PREDICTION_MARKETS_GENERAL" in {record["venue_id"] for record in requests}:
        failures.append("PREDICTION_MARKETS_GENERAL must not be treated as a venue")
    field_map_ids = {
        record["runtime_cash_component_field_map_id"]
        for venue_records in field_maps_by_venue.values()
        for record in venue_records
    }
    handoff_field_map_ids = set(runtime_cash_handoff["runtime_cash_component_field_map_ids"])
    if not field_map_ids.issubset(handoff_field_map_ids):
        failures.append("PR130 field-map references must come from PR129 runtime cash handoff")

    for request in requests:
        if request.get("fixture_authority_class") != FIXTURE_AUTHORITY_CLASS:
            failures.append("read requests must be TEST_FIXTURE_NOT_EXTERNAL_FACT")
        if request.get("credential_alias_placeholder_ref") in {None, ""}:
            failures.append("read requests require a credential alias placeholder")
        if request.get("credential_alias_authority_created") is not False:
            failures.append("read requests must not create credential alias authority")
        if request.get("runtime_cash_component_field_map_id") not in field_map_ids:
            failures.append("read requests require a PR129 runtime cash field-map reference")
        for flag in (
            "production_private_state_read_authority",
            "raw_secret_capture_allowed_flag",
            "network_io_allowed_flag",
            "production_connector_use_allowed_flag",
        ):
            if request.get(flag) is not False:
                failures.append(f"read request {flag} must be false")
        if request.get("deterministic_fixture_time") != DETERMINISTIC_FIXTURE_TIME:
            failures.append("read requests must use deterministic fixture time")

    redaction_ids = {record["redaction_attestation_id"] for record in redaction_attestations}
    no_secret_ids = {
        record["no_secret_capture_attestation_id"] for record in no_secret_attestations
    }
    account_by_private = {
        record["private_state_read_receipt_id"]: record for record in account_receipts
    }
    for receipt in private_state_receipts:
        receipt_id = receipt["private_state_read_receipt_id"]
        payload = redacted_payloads[receipt_id]
        payload_failures = validate_redacted_payload_minimized(payload)
        if payload_failures:
            failures.extend(payload_failures)
        digest = canonical_redacted_payload_digest(payload)
        if receipt.get("redacted_payload_digest") != digest:
            failures.append("redacted payload digest must match canonical fixture payload")
        if receipt.get("canonicalized_redacted_payload_digest") != digest:
            failures.append("canonicalized redacted payload digest must match canonical fixture payload")
        if receipt.get("redaction_attestation_id") not in redaction_ids:
            failures.append("private-state receipt requires redaction attestation")
        if receipt.get("no_secret_capture_attestation_id") not in no_secret_ids:
            failures.append("private-state receipt requires no-secret-capture attestation")
        if receipt_id not in account_by_private:
            failures.append("private-state receipt requires account/wallet/balance receipt")
        for flag in (
            "production_private_state_read_authority",
            "production_account_balance_authority",
            "production_wallet_balance_authority",
            "production_runtime_cash_receipt_authority",
            "network_io_allowed_flag",
            "production_connector_use_allowed_flag",
            "order_execution_allowed_flag",
            "order_routing_authority_allowed_flag",
        ):
            if receipt.get(flag) is not False:
                failures.append(f"private-state receipt {flag} must be false")

    for attestation in redaction_attestations:
        if attestation.get("raw_payload_stored_flag") is not False:
            failures.append("raw payload must not be stored")
        if attestation.get("secret_like_value_detected_flag") is not False:
            failures.append("redaction attestation must not detect secret-like values")
        if attestation.get("unredacted_private_payload_detected_flag") is not False:
            failures.append("redaction attestation must not detect unredacted payloads")
    for attestation in no_secret_attestations:
        for flag in (
            "credential_secret_capture_allowed_flag",
            "credential_alias_authority_created",
            "credential_readiness_authority_created",
            "raw_api_key_stored_flag",
            "raw_bearer_token_stored_flag",
            "raw_oauth_token_stored_flag",
            "raw_token_stored_flag",
            "raw_cookie_stored_flag",
            "raw_wallet_secret_stored_flag",
            "raw_private_key_stored_flag",
            "raw_session_identifier_stored_flag",
            "production_credential_authority_created",
        ):
            if attestation.get(flag) is not False:
                failures.append(f"no-secret attestation {flag} must be false")

    for account_receipt in account_receipts:
        if account_receipt.get("runtime_cash_component_field_map_id") not in field_map_ids:
            failures.append("account/wallet/balance receipt must reference PR129 field map")
        if account_receipt.get("amount_value_is_production_private_state") is not False:
            failures.append("account/wallet/balance fixture must not be production private state")
    for linkage in linkage_receipts:
        if linkage.get("production_runtime_cash_receipt_authority") is not False:
            failures.append("linkage must not create production runtime cash authority")
        if linkage.get("production_new_exposure_cash_gate_authority") is not False:
            failures.append("linkage must not create production new-exposure cash gate authority")
        if linkage.get("order_authority_allowed_flag") is not False:
            failures.append("linkage must not create order authority")
        if linkage.get("runtime_cash_component_field_map_id") not in field_map_ids:
            failures.append("linkage must reference PR129 runtime cash field map")

    rejection_states = {record["private_state_read_receipt_state"] for record in rejections}
    for state in REJECTION_STATES:
        if state not in rejection_states:
            failures.append(f"missing private-state rejection receipt for {state}")
    if handoff.get("production_downstream_authority") is not False:
        failures.append("private-state downstream handoff must not create production authority")

    expected_main = {
        "repo_pr_label": "PR130",
        "roadmap_pr_implemented": "PR112",
        "checked_github_pr_number": 129,
        "fixture_stage1_venue_count": 3,
        "fixture_private_state_read_request_count": 3,
        "fixture_private_state_read_receipt_count": 3,
        "fixture_account_wallet_balance_receipt_count": 3,
        "fixture_redaction_attestation_count": 3,
        "fixture_no_secret_capture_attestation_count": 3,
        "fixture_private_state_to_runtime_cash_linkage_count": 3,
        "fixture_private_state_downstream_handoff_count": 1,
        "production_private_state_read_authority_count": 0,
        "production_account_balance_authority_count": 0,
        "production_wallet_balance_authority_count": 0,
        "production_runtime_cash_receipt_authority_count": 0,
        "production_credential_alias_authority_count": 0,
        "production_credential_readiness_authority_count": 0,
        "atomicrows_bundle_consumed": False,
        "atomicrows_bundle_created": False,
        "atomicrows_sha_created": False,
        "order_authority_created": False,
        "network_io_created_count": 0,
        "quantum_backend_execution_count": 0,
        "optimizer_execution_count": 0,
        "profit_evidence_created": False,
    }
    for field, expected in expected_main.items():
        if main.get(field) != expected:
            failures.append(f"main_report.{field} must be {expected!r}")
    return failures


def write_generated_reports(repo_root: Path) -> dict[str, Any]:
    artifacts = build_private_state_read_receipt_artifacts(repo_root)
    failures = validate_artifacts(artifacts)
    if failures:
        raise ValueError("; ".join(failures))
    for key, path in REPORT_PATHS.items():
        output_path = repo_root / path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(_dump_json(artifacts[key]), encoding="utf-8", newline="\n")
    return artifacts


def write_fixture_files(repo_root: Path) -> dict[str, Any]:
    artifacts = build_private_state_read_receipt_artifacts(repo_root)
    failures = validate_artifacts(artifacts)
    if failures:
        raise ValueError("; ".join(failures))
    field_maps = [
        record
        for venue_records in artifacts["field_maps_by_venue"].values()
        for record in venue_records
    ]
    fixture_payloads: dict[str, Mapping[str, Any]] = {
        "runtime_cash_downstream_handoff.v1.fixture.json": {
            "fixture_id": "PR130_RUNTIME_CASH_DOWNSTREAM_HANDOFF_INPUT_FIXTURE_V1",
            "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
            "runtime_cash_downstream_handoff": artifacts["runtime_cash_handoff"],
        },
        "runtime_cash_component_field_map.v1.fixture.json": {
            "fixture_id": "PR130_RUNTIME_CASH_COMPONENT_FIELD_MAP_INPUT_FIXTURE_V1",
            "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
            "runtime_cash_component_field_maps": field_maps,
        },
        "private_state_read_requests.v1.fixture.json": {
            "fixture_id": "PR130_PRIVATE_STATE_READ_REQUESTS_FIXTURE_V1",
            "private_state_read_requests": artifacts["gate_report"][
                "private_state_read_requests"
            ],
        },
        "private_state_read_receipts.v1.fixture.json": {
            "fixture_id": "PR130_PRIVATE_STATE_READ_RECEIPTS_FIXTURE_V1",
            "private_state_read_receipts": artifacts["gate_report"][
                "private_state_read_receipts"
            ],
        },
        "account_wallet_balance_receipts.v1.fixture.json": {
            "fixture_id": "PR130_ACCOUNT_WALLET_BALANCE_RECEIPTS_FIXTURE_V1",
            "account_wallet_balance_receipts": artifacts["account_report"][
                "account_wallet_balance_receipts"
            ],
        },
        "private_state_redaction_attestations.v1.fixture.json": {
            "fixture_id": "PR130_PRIVATE_STATE_REDACTION_ATTESTATIONS_FIXTURE_V1",
            "private_state_redaction_attestations": artifacts["redaction_report"][
                "private_state_redaction_attestations"
            ],
        },
        "private_state_no_secret_capture_attestations.v1.fixture.json": {
            "fixture_id": "PR130_PRIVATE_STATE_NO_SECRET_CAPTURE_ATTESTATIONS_FIXTURE_V1",
            "private_state_no_secret_capture_attestations": artifacts["redaction_report"][
                "private_state_no_secret_capture_attestations"
            ],
        },
        "private_state_read_rejections.v1.fixture.json": {
            "fixture_id": "PR130_PRIVATE_STATE_READ_REJECTIONS_FIXTURE_V1",
            "private_state_read_rejection_receipts": artifacts["gate_report"][
                "private_state_read_rejection_receipts"
            ],
        },
        "expected_private_state_to_runtime_cash_linkage_receipts.v1.fixture.json": {
            "fixture_id": "PR130_EXPECTED_PRIVATE_STATE_TO_RUNTIME_CASH_LINKAGES_V1",
            "private_state_to_runtime_cash_linkage_receipts": artifacts["linkage_report"][
                "private_state_to_runtime_cash_linkage_receipts"
            ],
        },
        "expected_private_state_downstream_handoff.v1.fixture.json": {
            "fixture_id": "PR130_EXPECTED_PRIVATE_STATE_DOWNSTREAM_HANDOFF_V1",
            "private_state_downstream_handoff": artifacts["handoff_report"][
                "private_state_downstream_handoff"
            ],
        },
    }
    for filename, payload in fixture_payloads.items():
        output_path = repo_root / FIXTURE_DIR / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_payload = {
            "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
            "mode": "SOURCE_REQUIRED",
            "execution": "DISABLED",
            **payload,
        }
        output_path.write_text(
            _dump_json(fixture_payload), encoding="utf-8", newline="\n"
        )
    return artifacts
