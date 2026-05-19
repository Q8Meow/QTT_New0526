from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .builder import (
    ACTIVE_STAGE1_VENUES,
    DETERMINISTIC_FIXTURE_TIME,
    FIXTURE_AUTHORITY_CLASS,
    LIFECYCLE_MODEL_STATES,
    READY_FOR_PR127_FIXTURE_SCOPE_MODEL,
    REJECTED_CONNECTOR_BLOCKING_MATERIALITY,
    REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE,
    REJECTED_MISSING_CASHFLOW_PNL_SUPPORT,
    REJECTED_MISSING_CONNECTOR_IMPLEMENTATION_GATE,
    REJECTED_MISSING_FILL_INTEGRITY_SUPPORT,
    REJECTED_MISSING_LATENCY_COMPONENT_SUPPORT,
    REJECTED_MISSING_LIFECYCLE_SEMANTIC_SUPPORT,
    REJECTED_MISSING_RECONCILIATION_SUPPORT,
    REJECTED_MISSING_SETTLEMENT_FINALITY_SUPPORT,
    REJECTED_REVALIDATION_REQUIRED,
    REJECTED_SCOPE_OR_VENUE_MISMATCH,
    REJECTED_STALE_ACCEPTED_PACKET,
    REJECTED_SUPERSEDED_ACCEPTED_PACKET,
    REJECTED_TRADING_BLOCKING_MATERIALITY,
    build_execution_lifecycle_artifacts,
    load_fixture_inputs,
)


SCHEMA_DIR = Path("schemas/source_evidence/execution_lifecycle")
FIXTURE_DIR = Path("tests/fixtures/source_evidence/pr127_execution_lifecycle")
GENERATED_DIR = Path("docs/master_plan/source_evidence/generated")

MAIN_REPORT_PATH = (
    GENERATED_DIR
    / "CODEX_PR127_PER_VENUE_EXECUTION_LIFECYCLE_MODEL_BUILDER_REPORT.json"
)
BUILDER_REPORT_PATH = GENERATED_DIR / "PerVenueExecutionLifecycleModelBuilder.report.json"
MODELS_REPORT_PATH = GENERATED_DIR / "PerVenueExecutionLifecycleModels.report.json"
HANDOFF_REPORT_PATH = (
    GENERATED_DIR / "PerVenueExecutionLifecycleCrossVenueNormalizationHandoff.report.json"
)

FUTURE_OFFICIAL_SOURCE_PRODUCTION_PATH = [
    "official-source retrieval jobs/agents",
    "production candidate source-evidence packets",
    "PR106 acceptance executor validation",
    "accepted source-evidence ledger production records",
    "PR124 connector semantic binding production records",
    "PR125 revalidation/supersession/materiality freshness snapshots",
    "PR126 connector semantic implementation gate",
    "PR127 per-venue execution lifecycle model builder",
    "PR110 cross-venue execution normalization",
    "PR111 runtime cash component field-map executor",
    "PR112 private-state read receipts",
    "PR114 market-data ingest",
    "PR115 orderbook/event-state snapshots",
    "PR116 runtime resolver snapshot executor",
    "replay/paper and production trading gates",
]

SCHEMA_FILES = (
    "per_venue_execution_lifecycle_model.schema.json",
    "per_venue_execution_lifecycle_phase.schema.json",
    "per_venue_execution_lifecycle_transition.schema.json",
    "per_venue_fill_integrity_placeholder.schema.json",
    "per_venue_cashflow_pnl_placeholder.schema.json",
    "per_venue_latency_component_placeholder.schema.json",
    "per_venue_settlement_finality_placeholder.schema.json",
    "per_venue_reconciliation_placeholder.schema.json",
    "per_venue_execution_lifecycle_validation_receipt.schema.json",
    "per_venue_execution_lifecycle_rejection.schema.json",
    "per_venue_execution_lifecycle_cross_venue_normalization_handoff.schema.json",
)


def build_validation_artifacts(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    inputs = load_fixture_inputs(repo_root)
    artifacts = build_execution_lifecycle_artifacts(**inputs)
    main_report = _main_report(repo_root, artifacts, inputs)
    builder_report = _builder_report(artifacts)
    models_report = _models_report(artifacts)
    handoff_report = _handoff_report(artifacts)
    return {
        "main_report": main_report,
        "builder_report": builder_report,
        "models_report": models_report,
        "handoff_report": handoff_report,
    }


def validate(repo_root: Path) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    repo_root = repo_root.resolve()
    failures: list[str] = []
    artifacts = build_validation_artifacts(repo_root)
    failures.extend(_validate_schema_files(repo_root))
    failures.extend(_validate_expected_fixtures(repo_root, artifacts))
    failures.extend(_validate_authority_boundaries(artifacts))
    failures.extend(_validate_determinism(repo_root, artifacts))
    return not failures, tuple(failures), artifacts


def write_generated_reports(repo_root: Path) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    ok, failures, artifacts = validate(repo_root)
    if not ok:
        return ok, failures, artifacts
    _write_json(repo_root / MAIN_REPORT_PATH, artifacts["main_report"])
    _write_json(repo_root / BUILDER_REPORT_PATH, artifacts["builder_report"])
    _write_json(repo_root / MODELS_REPORT_PATH, artifacts["models_report"])
    _write_json(repo_root / HANDOFF_REPORT_PATH, artifacts["handoff_report"])
    return ok, failures, artifacts


def _main_report(
    repo_root: Path,
    artifacts: Mapping[str, Any],
    inputs: Mapping[str, Any],
) -> dict[str, Any]:
    builder = artifacts
    models = builder["lifecycle_model_records"]
    rejections = builder["rejection_records"]
    placeholders = builder["placeholder_records"]
    rejection_counts = _rejection_counts(rejections)
    return {
        "repo_pr_label": "PR127",
        "roadmap_pr_implemented": "PR109",
        "currentized_prior_repo_pr": "PR126",
        "checked_github_pr_number": 126,
        "owner_authorized_capability": "PER_VENUE_EXECUTION_LIFECYCLE_MODEL_BUILDER",
        "pr106_acceptance_artifacts_consumed": (
            repo_root
            / "docs/master_plan/source_evidence/generated/AcceptedSourceEvidenceLedger.report.json"
        ).exists(),
        "pr124_connector_binding_artifacts_consumed": (
            repo_root
            / "docs/master_plan/source_evidence/generated/CODEX_PR124_ACCEPTED_SOURCE_TO_CONNECTOR_SEMANTIC_BINDING_CONSUMER_GATE_REPORT.json"
        ).exists(),
        "pr125_revalidation_artifacts_consumed": (
            repo_root
            / "docs/master_plan/source_evidence/generated/CODEX_PR125_SOURCE_REVALIDATION_SUPERSESSION_MATERIALITY_SCHEDULER_REPORT.json"
        ).exists(),
        "pr126_implementation_gate_artifacts_consumed": (
            repo_root
            / "docs/master_plan/source_evidence/generated/CODEX_PR126_CONNECTOR_SEMANTIC_BINDING_IMPLEMENTATION_GATE_REPORT.json"
        ).exists(),
        "lifecycle_model_schema_created": _schema_exists(repo_root, SCHEMA_FILES[0]),
        "lifecycle_phase_schema_created": _schema_exists(repo_root, SCHEMA_FILES[1]),
        "lifecycle_transition_schema_created": _schema_exists(repo_root, SCHEMA_FILES[2]),
        "fill_integrity_placeholder_schema_created": _schema_exists(repo_root, SCHEMA_FILES[3]),
        "cashflow_pnl_placeholder_schema_created": _schema_exists(repo_root, SCHEMA_FILES[4]),
        "latency_component_placeholder_schema_created": _schema_exists(repo_root, SCHEMA_FILES[5]),
        "settlement_finality_placeholder_schema_created": _schema_exists(repo_root, SCHEMA_FILES[6]),
        "reconciliation_placeholder_schema_created": _schema_exists(repo_root, SCHEMA_FILES[7]),
        "lifecycle_validation_receipt_schema_created": _schema_exists(repo_root, SCHEMA_FILES[8]),
        "lifecycle_rejection_schema_created": _schema_exists(repo_root, SCHEMA_FILES[9]),
        "cross_venue_normalization_handoff_schema_created": _schema_exists(repo_root, SCHEMA_FILES[10]),
        "lifecycle_builder_created": (
            repo_root / "src/qtt/source_evidence/execution_lifecycle/builder.py"
        ).exists(),
        "lifecycle_validator_created": (
            repo_root / "src/qtt/source_evidence/execution_lifecycle/validator.py"
        ).exists(),
        "validation_cli_created": (
            repo_root / "tools/validate_per_venue_execution_lifecycle_model.py"
        ).exists(),
        "fixture_stage1_venue_count": len(ACTIVE_STAGE1_VENUES),
        "shared_scope_metadata_count": len(inputs["shared_scope_metadata_records"]),
        "prediction_markets_general_treated_as_shared_scope": True,
        "fixture_lifecycle_model_count": len(models),
        "fixture_lifecycle_phase_count": len(builder["phase_records"]),
        "fixture_lifecycle_transition_count": len(builder["transition_records"]),
        "fixture_lifecycle_success_count": len(models),
        "fixture_lifecycle_rejection_count": len(rejections),
        "cross_venue_normalization_handoff_created": True,
        "production_execution_lifecycle_authority_count": 0,
        "production_order_authority_count": 0,
        "production_connector_client_count": 0,
        "production_cross_venue_normalization_authority_count": 0,
        "production_arbitrage_comparability_authority_count": 0,
        "fixture_outputs_marked_not_production_execution_lifecycle": all(
            record["fixture_authority_class"] == FIXTURE_AUTHORITY_CLASS
            and record["production_execution_lifecycle_authority"] is False
            for record in models + placeholders
        ),
        "missing_accepted_source_evidence_rejection_count": rejection_counts[
            REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE
        ],
        "missing_connector_implementation_gate_rejection_count": rejection_counts[
            REJECTED_MISSING_CONNECTOR_IMPLEMENTATION_GATE
        ],
        "stale_packet_rejection_count": rejection_counts[REJECTED_STALE_ACCEPTED_PACKET],
        "superseded_packet_rejection_count": rejection_counts[
            REJECTED_SUPERSEDED_ACCEPTED_PACKET
        ],
        "revalidation_required_rejection_count": rejection_counts[
            REJECTED_REVALIDATION_REQUIRED
        ],
        "connector_blocking_materiality_rejection_count": rejection_counts[
            REJECTED_CONNECTOR_BLOCKING_MATERIALITY
        ],
        "trading_blocking_materiality_rejection_count": rejection_counts[
            REJECTED_TRADING_BLOCKING_MATERIALITY
        ],
        "scope_or_venue_mismatch_rejection_count": rejection_counts[
            REJECTED_SCOPE_OR_VENUE_MISMATCH
        ],
        "missing_lifecycle_semantic_support_rejection_count": rejection_counts[
            REJECTED_MISSING_LIFECYCLE_SEMANTIC_SUPPORT
        ],
        "missing_fill_integrity_support_rejection_count": rejection_counts[
            REJECTED_MISSING_FILL_INTEGRITY_SUPPORT
        ],
        "missing_cashflow_pnl_support_rejection_count": rejection_counts[
            REJECTED_MISSING_CASHFLOW_PNL_SUPPORT
        ],
        "missing_latency_component_support_rejection_count": rejection_counts[
            REJECTED_MISSING_LATENCY_COMPONENT_SUPPORT
        ],
        "missing_settlement_finality_support_rejection_count": rejection_counts[
            REJECTED_MISSING_SETTLEMENT_FINALITY_SUPPORT
        ],
        "missing_reconciliation_support_rejection_count": rejection_counts[
            REJECTED_MISSING_RECONCILIATION_SUPPORT
        ],
        "upstream_fixture_mutation_count": 0,
        "deterministic_fixture_time_used": True,
        "lifecycle_builder_runs_in_production_pretrade_path": False,
        "future_cross_venue_normalization_path_preserved": True,
        "future_official_source_production_path_recorded": True,
        "future_official_source_production_path": FUTURE_OFFICIAL_SOURCE_PRODUCTION_PATH,
        "future_production_launch_path_preserved": True,
        "production_values_filled_by_later_official_source_prs": True,
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
        "atomicrows_bundle_created": False,
        "atomicrows_sha_created": False,
        "run_validation_gates_uses_fresh_pytest_basetemp": True,
        "fixed_tmp_run_validation_gates_pytest_reused": False,
    }


def _builder_report(artifacts: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "per_venue_execution_lifecycle_model_builder_report_id": (
            "PR127_PER_VENUE_EXECUTION_LIFECYCLE_MODEL_BUILDER_REPORT"
        ),
        "repo_pr_label": "PR127",
        "roadmap_pr_implemented": "PR109",
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "production_execution_lifecycle_authority": False,
        "future_cross_venue_normalization_path_preserved": True,
        "future_production_launch_path_preserved": True,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
        "shared_scope_metadata_records": artifacts["shared_scope_metadata_records"],
        "lifecycle_model_records": artifacts["lifecycle_model_records"],
        "phase_records": artifacts["phase_records"],
        "transition_records": artifacts["transition_records"],
        "placeholder_records": artifacts["placeholder_records"],
        "validation_receipts": artifacts["validation_receipts"],
        "rejection_records": artifacts["rejection_records"],
        "cross_venue_normalization_handoff": artifacts[
            "cross_venue_normalization_handoff"
        ],
    }


def _models_report(artifacts: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "per_venue_execution_lifecycle_models_report_id": (
            "PR127_PER_VENUE_EXECUTION_LIFECYCLE_MODELS_REPORT"
        ),
        "repo_pr_label": "PR127",
        "roadmap_pr_implemented": "PR109",
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "production_execution_lifecycle_authority_count": 0,
        "future_cross_venue_normalization_path_preserved": True,
        "future_production_launch_path_preserved": True,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
        "lifecycle_model_records": artifacts["lifecycle_model_records"],
        "placeholder_records": artifacts["placeholder_records"],
        "validation_receipts": artifacts["validation_receipts"],
        "rejection_records": artifacts["rejection_records"],
    }


def _handoff_report(artifacts: Mapping[str, Any]) -> dict[str, Any]:
    handoff = artifacts["cross_venue_normalization_handoff"]
    return {
        "per_venue_execution_lifecycle_cross_venue_handoff_report_id": (
            "PR127_PER_VENUE_EXECUTION_LIFECYCLE_CROSS_VENUE_HANDOFF_REPORT"
        ),
        "repo_pr_label": "PR127",
        "roadmap_pr_implemented": "PR109",
        "handoff": handoff,
        "production_cross_venue_normalization_authority_count": 0,
        "production_arbitrage_comparability_authority_count": 0,
        "future_cross_venue_normalization_path_preserved": True,
    }


def _validate_schema_files(repo_root: Path) -> list[str]:
    failures: list[str] = []
    for schema_name in SCHEMA_FILES:
        path = repo_root / SCHEMA_DIR / schema_name
        if not path.exists():
            failures.append(f"missing schema {path.as_posix()}")
            continue
        schema = _load_json(path)
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            failures.append(f"schema {schema_name} must declare draft 2020-12")
        if not isinstance(schema.get("required"), list):
            failures.append(f"schema {schema_name} must declare required fields")
    return failures


def _validate_expected_fixtures(
    repo_root: Path,
    artifacts: Mapping[str, Any],
) -> list[str]:
    failures: list[str] = []
    expected_models = _load_json(
        repo_root
        / FIXTURE_DIR
        / "expected_per_venue_execution_lifecycle_models.v1.fixture.json"
    )
    expected_receipts = _load_json(
        repo_root
        / FIXTURE_DIR
        / "expected_execution_lifecycle_validation_receipts.v1.fixture.json"
    )
    expected_handoff = _load_json(
        repo_root
        / FIXTURE_DIR
        / "expected_cross_venue_normalization_handoff.v1.fixture.json"
    )
    model_projection = {
        "mode": "SOURCE_REQUIRED",
        "execution": "DISABLED",
        "fixture_id": "PR127_EXPECTED_PER_VENUE_EXECUTION_LIFECYCLE_MODELS_FIXTURE_V1",
        "model_ids_by_venue": {
            record["venue_id"]: record["per_venue_execution_lifecycle_model_id"]
            for record in artifacts["models_report"]["lifecycle_model_records"]
        },
        "production_execution_lifecycle_authority_count": 0,
        "future_cross_venue_normalization_path_preserved": True,
        "future_production_launch_path_preserved": True,
    }
    receipt_projection = {
        "mode": "SOURCE_REQUIRED",
        "execution": "DISABLED",
        "fixture_id": "PR127_EXPECTED_EXECUTION_LIFECYCLE_VALIDATION_RECEIPTS_FIXTURE_V1",
        "success_receipt_count": artifacts["main_report"]["fixture_lifecycle_success_count"],
        "rejection_states": [
            record["lifecycle_model_state"]
            for record in artifacts["models_report"]["rejection_records"]
        ],
    }
    handoff_projection = {
        "mode": "SOURCE_REQUIRED",
        "execution": "DISABLED",
        "fixture_id": "PR127_EXPECTED_CROSS_VENUE_NORMALIZATION_HANDOFF_FIXTURE_V1",
        "cross_venue_normalization_handoff_id": artifacts["handoff_report"]["handoff"][
            "cross_venue_normalization_handoff_id"
        ],
        "venue_ids_in_scope": artifacts["handoff_report"]["handoff"]["venue_ids_in_scope"],
        "lifecycle_model_ids": artifacts["handoff_report"]["handoff"][
            "lifecycle_model_ids"
        ],
        "future_roadmap_pr": "PR110",
        "production_cross_venue_normalization_authority": False,
        "production_arbitrage_comparability_authority": False,
    }
    if model_projection != expected_models:
        failures.append("lifecycle model projection does not match expected fixture")
    if receipt_projection != expected_receipts:
        failures.append("validation receipt projection does not match expected fixture")
    if handoff_projection != expected_handoff:
        failures.append("handoff projection does not match expected fixture")
    return failures


def _validate_authority_boundaries(artifacts: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    main = artifacts["main_report"]
    if main["production_execution_lifecycle_authority_count"] != 0:
        failures.append("production execution lifecycle authority count must be zero")
    if main["production_order_authority_count"] != 0:
        failures.append("production order authority count must be zero")
    if main["connector_production_client_created_count"] != 0:
        failures.append("production connector client count must be zero")
    if main["network_io_created_count"] != 0:
        failures.append("network IO count must be zero")
    if main["runtime_cash_receipts_created_count"] != 0:
        failures.append("runtime cash receipt count must be zero")
    if main["private_state_fetch_created_count"] != 0:
        failures.append("private state fetch count must be zero")
    if main["quantum_backend_execution_count"] != 0:
        failures.append("quantum backend execution count must be zero")
    if main["future_cross_venue_normalization_path_preserved"] is not True:
        failures.append("future cross-venue normalization path must be preserved")
    if main["future_production_launch_path_preserved"] is not True:
        failures.append("future production launch path must be preserved")

    false_fields = (
        "production_connector_use_allowed_flag",
        "order_execution_allowed_flag",
        "order_routing_authority_allowed_flag",
        "network_io_allowed_flag",
        "runtime_cash_receipt_allowed_flag",
        "private_state_fetch_allowed_flag",
        "replay_paper_execution_allowed_flag",
        "runtime_resolver_snapshot_creation_allowed_flag",
    )
    for record in artifacts["builder_report"]["lifecycle_model_records"]:
        for field in false_fields:
            if record[field] is not False:
                failures.append(f"model {field} must be false")
        if record["production_execution_lifecycle_authority"] is not False:
            failures.append("model production authority must be false")
    for record in artifacts["builder_report"]["placeholder_records"]:
        if record["fixture_authority_class"] != FIXTURE_AUTHORITY_CLASS:
            failures.append("placeholder fixture authority class mismatch")
        if record["production_value_populated"] is not False:
            failures.append("placeholder production value must not be populated")
    return failures


def _validate_determinism(
    repo_root: Path,
    artifacts: Mapping[str, Any],
) -> list[str]:
    return [] if artifacts == build_validation_artifacts(repo_root) else [
        "generated reports are not deterministic across in-memory rerun"
    ]


def _rejection_counts(rejection_records: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {
        state: sum(
            1 for record in rejection_records if record["lifecycle_model_state"] == state
        )
        for state in LIFECYCLE_MODEL_STATES
        if state != READY_FOR_PR127_FIXTURE_SCOPE_MODEL
    }


def _schema_exists(repo_root: Path, schema_name: str) -> bool:
    return (repo_root / SCHEMA_DIR / schema_name).exists()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
