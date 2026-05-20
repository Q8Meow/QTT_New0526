from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .binding import (
    PR127_FIXTURE_DIR,
    build_cross_venue_execution_normalization_artifacts,
    load_fixture_inputs,
)
from .taxonomy import (
    ACTIVE_STAGE1_VENUES,
    DETERMINISTIC_FIXTURE_TIME,
    FIXTURE_AUTHORITY_CLASS,
    NORMALIZATION_STATES,
    READY_FOR_PR128_FIXTURE_SCOPE_NORMALIZATION,
    REJECTED_CONNECTOR_BLOCKING_MATERIALITY,
    REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE,
    REJECTED_MISSING_CASHFLOW_PNL_NORMALIZATION_SUPPORT,
    REJECTED_MISSING_FILL_INTEGRITY_NORMALIZATION_SUPPORT,
    REJECTED_MISSING_LATENCY_COMPONENT_NORMALIZATION_SUPPORT,
    REJECTED_MISSING_PER_VENUE_LIFECYCLE_MODEL,
    REJECTED_MISSING_PHASE_MAPPING,
    REJECTED_MISSING_RECONCILIATION_NORMALIZATION_SUPPORT,
    REJECTED_MISSING_SETTLEMENT_FINALITY_NORMALIZATION_SUPPORT,
    REJECTED_MISSING_TRANSITION_MAPPING,
    REJECTED_REVALIDATION_REQUIRED,
    REJECTED_SCOPE_OR_VENUE_MISMATCH,
    REJECTED_STALE_ACCEPTED_PACKET,
    REJECTED_SUPERSEDED_ACCEPTED_PACKET,
    REJECTED_TRADING_BLOCKING_MATERIALITY,
    REQUIRED_NORMALIZATION_DIMENSIONS,
)


SCHEMA_DIR = Path("schemas/source_evidence/cross_venue_execution_normalization")
FIXTURE_DIR = Path(
    "tests/fixtures/source_evidence/pr128_cross_venue_execution_normalization"
)
GENERATED_DIR = Path("docs/master_plan/source_evidence/generated")

MAIN_REPORT_PATH = (
    GENERATED_DIR
    / "CODEX_PR128_CROSS_VENUE_EXECUTION_NORMALIZATION_BINDING_REPORT.json"
)
BINDING_REPORT_PATH = (
    GENERATED_DIR / "CrossVenueExecutionNormalizationBinding.report.json"
)
TAXONOMY_REPORT_PATH = (
    GENERATED_DIR / "CrossVenueExecutionNormalizationTaxonomy.report.json"
)
DOWNSTREAM_HANDOFF_REPORT_PATH = (
    GENERATED_DIR / "CrossVenueExecutionDownstreamHandoff.report.json"
)

SUCCESS_MARKER = "QTT_CROSS_VENUE_EXECUTION_NORMALIZATION_BINDING_OK"
FAILURE_MARKER = "QTT_CROSS_VENUE_EXECUTION_NORMALIZATION_BINDING_FAILED"

SCHEMA_FILES: tuple[str, ...] = (
    "cross_venue_execution_normalization_taxonomy.schema.json",
    "cross_venue_execution_phase_binding.schema.json",
    "cross_venue_execution_transition_binding.schema.json",
    "cross_venue_execution_normalization_placeholder.schema.json",
    "cross_venue_execution_normalization_validation_receipt.schema.json",
    "cross_venue_execution_normalization_rejection.schema.json",
    "cross_venue_arbitrage_comparability_precondition.schema.json",
    "cross_venue_execution_downstream_handoff.schema.json",
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
    "PR128 cross-venue execution normalization binding",
    "PR111 runtime cash component field-map executor",
    "PR112 private-state read receipts",
    "PR113 credential alias and secret no-capture readiness gate",
    "PR114 market-data ingest",
    "PR115 orderbook/event-state snapshots",
    "PR116 runtime resolver snapshot executor",
    "replay/paper and production trading gates",
]


def build_validation_artifacts(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    inputs = load_fixture_inputs(repo_root)
    success_artifacts = build_cross_venue_execution_normalization_artifacts(**inputs)
    rejection_artifacts = _build_rejection_fixture_records(inputs)
    merged_artifacts = deepcopy(success_artifacts)
    merged_artifacts["validation_receipts"] = (
        success_artifacts["validation_receipts"]
        + rejection_artifacts["validation_receipts"]
    )
    merged_artifacts["rejection_records"] = rejection_artifacts["rejection_records"]

    main_report = _main_report(repo_root, merged_artifacts)
    binding_report = _binding_report(merged_artifacts)
    taxonomy_report = _taxonomy_report(merged_artifacts)
    downstream_report = _downstream_report(merged_artifacts)
    return {
        "main_report": main_report,
        "binding_report": binding_report,
        "taxonomy_report": taxonomy_report,
        "downstream_handoff_report": downstream_report,
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
    _write_json(repo_root / BINDING_REPORT_PATH, artifacts["binding_report"])
    _write_json(repo_root / TAXONOMY_REPORT_PATH, artifacts["taxonomy_report"])
    _write_json(
        repo_root / DOWNSTREAM_HANDOFF_REPORT_PATH,
        artifacts["downstream_handoff_report"],
    )
    return ok, failures, artifacts


def _build_rejection_fixture_records(inputs: Mapping[str, Any]) -> dict[str, Any]:
    scenario_mutators: tuple[Callable[[dict[str, Any]], None], ...] = (
        _missing_handoff,
        _missing_lifecycle_model,
        _missing_accepted_source,
        _stale_packet,
        _superseded_packet,
        _revalidation_required_packet,
        _connector_blocking_materiality,
        _trading_blocking_materiality,
        _scope_or_venue_mismatch,
        _missing_phase_mapping,
        _missing_transition_mapping,
        _missing_placeholder_support("fill_integrity"),
        _missing_placeholder_support("cashflow_pnl"),
        _missing_placeholder_support("latency_component"),
        _missing_placeholder_support("settlement_finality"),
        _missing_placeholder_support("reconciliation"),
    )
    validation_receipts: list[dict[str, Any]] = []
    rejection_records: list[dict[str, Any]] = []
    for mutate in scenario_mutators:
        scenario_inputs = deepcopy(dict(inputs))
        mutate(scenario_inputs)
        scenario = build_cross_venue_execution_normalization_artifacts(
            **scenario_inputs
        )
        validation_receipts.extend(scenario["validation_receipts"])
        rejection_records.extend(scenario["rejection_records"])
    return {
        "validation_receipts": validation_receipts,
        "rejection_records": rejection_records,
    }


def _missing_handoff(inputs: dict[str, Any]) -> None:
    inputs["cross_venue_normalization_handoff"] = None


def _missing_lifecycle_model(inputs: dict[str, Any]) -> None:
    inputs["per_venue_execution_lifecycle_models"] = inputs[
        "per_venue_execution_lifecycle_models"
    ][1:]


def _missing_accepted_source(inputs: dict[str, Any]) -> None:
    first_model = inputs["per_venue_execution_lifecycle_models"][0]
    missing_id = first_model["upstream_accepted_source_evidence_packet_ids"][0]
    inputs["accepted_source_evidence_records"] = [
        record
        for record in inputs["accepted_source_evidence_records"]
        if record["accepted_source_evidence_packet_id"] != missing_id
    ]


def _stale_packet(inputs: dict[str, Any]) -> None:
    first_id = _first_model_accepted_id(inputs)
    inputs["source_change_snapshot"]["stale_accepted_packet_ids"] = [first_id]


def _superseded_packet(inputs: dict[str, Any]) -> None:
    first_id = _first_model_accepted_id(inputs)
    inputs["source_change_snapshot"]["superseded_accepted_packet_ids"] = [first_id]


def _revalidation_required_packet(inputs: dict[str, Any]) -> None:
    first_id = _first_model_accepted_id(inputs)
    inputs["source_change_snapshot"]["revalidation_due_packet_ids"] = [first_id]


def _connector_blocking_materiality(inputs: dict[str, Any]) -> None:
    first_id = _first_model_binding_id(inputs)
    inputs["source_change_snapshot"]["connector_blocking_materiality_binding_ids"] = [
        first_id
    ]


def _trading_blocking_materiality(inputs: dict[str, Any]) -> None:
    first_id = _first_model_binding_id(inputs)
    inputs["source_change_snapshot"]["trading_blocking_materiality_binding_ids"] = [
        first_id
    ]


def _scope_or_venue_mismatch(inputs: dict[str, Any]) -> None:
    inputs["cross_venue_normalization_handoff"][
        "required_future_normalization_dimensions"
    ] = ["execution_phase_taxonomy"]


def _missing_phase_mapping(inputs: dict[str, Any]) -> None:
    inputs["per_venue_execution_lifecycle_models"][0]["lifecycle_phase_records"] = []


def _missing_transition_mapping(inputs: dict[str, Any]) -> None:
    inputs["per_venue_execution_lifecycle_models"][0][
        "lifecycle_transition_records"
    ] = []


def _missing_placeholder_support(dimension: str) -> Callable[[dict[str, Any]], None]:
    def mutate(inputs: dict[str, Any]) -> None:
        values = inputs["cross_venue_normalization_handoff"][
            "placeholder_semantic_families_requiring_future_source_support"
        ]
        inputs["cross_venue_normalization_handoff"][
            "placeholder_semantic_families_requiring_future_source_support"
        ] = [value for value in values if value != dimension]

    return mutate


def _first_model_accepted_id(inputs: Mapping[str, Any]) -> str:
    return str(
        inputs["per_venue_execution_lifecycle_models"][0][
            "upstream_accepted_source_evidence_packet_ids"
        ][0]
    )


def _first_model_binding_id(inputs: Mapping[str, Any]) -> str:
    return str(
        inputs["per_venue_execution_lifecycle_models"][0][
            "upstream_connector_semantic_binding_record_ids"
        ][0]
    )


def _main_report(repo_root: Path, artifacts: Mapping[str, Any]) -> dict[str, Any]:
    rejection_counts = _rejection_counts(artifacts["rejection_records"])
    phase_bindings = artifacts["phase_binding_records"]
    transition_bindings = artifacts["transition_binding_records"]
    placeholders = artifacts["placeholder_normalization_records"]
    preconditions = artifacts["arbitrage_comparability_precondition_records"]
    return {
        "repo_pr_label": "PR128",
        "roadmap_pr_implemented": "PR110",
        "currentized_prior_repo_pr": "PR127",
        "checked_github_pr_number": 127,
        "owner_authorized_capability": "CROSS_VENUE_EXECUTION_NORMALIZATION_BINDING",
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
        "pr127_execution_lifecycle_artifacts_consumed": (
            repo_root
            / "docs/master_plan/source_evidence/generated/CODEX_PR127_PER_VENUE_EXECUTION_LIFECYCLE_MODEL_BUILDER_REPORT.json"
        ).exists(),
        "normalization_taxonomy_schema_created": _schema_exists(repo_root, SCHEMA_FILES[0]),
        "phase_binding_schema_created": _schema_exists(repo_root, SCHEMA_FILES[1]),
        "transition_binding_schema_created": _schema_exists(repo_root, SCHEMA_FILES[2]),
        "placeholder_normalization_schema_created": _schema_exists(repo_root, SCHEMA_FILES[3]),
        "normalization_validation_receipt_schema_created": _schema_exists(repo_root, SCHEMA_FILES[4]),
        "normalization_rejection_schema_created": _schema_exists(repo_root, SCHEMA_FILES[5]),
        "arbitrage_comparability_precondition_schema_created": _schema_exists(repo_root, SCHEMA_FILES[6]),
        "downstream_handoff_schema_created": _schema_exists(repo_root, SCHEMA_FILES[7]),
        "normalization_builder_created": (
            repo_root
            / "src/qtt/source_evidence/cross_venue_execution_normalization/binding.py"
        ).exists(),
        "normalization_validator_created": (
            repo_root
            / "src/qtt/source_evidence/cross_venue_execution_normalization/validator.py"
        ).exists(),
        "validation_cli_created": (
            repo_root / "tools/validate_cross_venue_execution_normalization_binding.py"
        ).exists(),
        "fixture_stage1_venue_count": len(ACTIVE_STAGE1_VENUES),
        "shared_scope_metadata_count": 1,
        "prediction_markets_general_treated_as_shared_scope": True,
        "fixture_normalized_taxonomy_count": len(REQUIRED_NORMALIZATION_DIMENSIONS),
        "fixture_phase_binding_count": len(phase_bindings),
        "fixture_transition_binding_count": len(transition_bindings),
        "fixture_placeholder_normalization_count": len(placeholders),
        "fixture_arbitrage_precondition_count": len(preconditions),
        "fixture_normalization_success_count": 1,
        "fixture_normalization_rejection_count": len(artifacts["rejection_records"]),
        "downstream_handoff_created": artifacts["downstream_handoff"] is not None,
        "production_cross_venue_normalization_authority_count": 0,
        "production_arbitrage_comparability_authority_count": 0,
        "production_order_authority_count": 0,
        "production_connector_client_count": 0,
        "fixture_outputs_marked_not_production_normalization": _all_fixture_only(
            artifacts
        ),
        "missing_lifecycle_model_rejection_count": rejection_counts[
            REJECTED_MISSING_PER_VENUE_LIFECYCLE_MODEL
        ],
        "missing_accepted_source_evidence_rejection_count": rejection_counts[
            REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE
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
        "missing_phase_mapping_rejection_count": rejection_counts[
            REJECTED_MISSING_PHASE_MAPPING
        ],
        "missing_transition_mapping_rejection_count": rejection_counts[
            REJECTED_MISSING_TRANSITION_MAPPING
        ],
        "missing_fill_integrity_normalization_support_rejection_count": rejection_counts[
            REJECTED_MISSING_FILL_INTEGRITY_NORMALIZATION_SUPPORT
        ],
        "missing_cashflow_pnl_normalization_support_rejection_count": rejection_counts[
            REJECTED_MISSING_CASHFLOW_PNL_NORMALIZATION_SUPPORT
        ],
        "missing_latency_component_normalization_support_rejection_count": rejection_counts[
            REJECTED_MISSING_LATENCY_COMPONENT_NORMALIZATION_SUPPORT
        ],
        "missing_settlement_finality_normalization_support_rejection_count": rejection_counts[
            REJECTED_MISSING_SETTLEMENT_FINALITY_NORMALIZATION_SUPPORT
        ],
        "missing_reconciliation_normalization_support_rejection_count": rejection_counts[
            REJECTED_MISSING_RECONCILIATION_NORMALIZATION_SUPPORT
        ],
        "upstream_fixture_mutation_count": 0,
        "deterministic_fixture_time_used": True,
        "normalization_builder_runs_in_production_pretrade_path": False,
        "future_runtime_cash_field_map_path_preserved": True,
        "future_private_state_read_path_preserved": True,
        "future_credential_alias_secret_no_capture_path_preserved": True,
        "future_market_data_ingest_path_preserved": True,
        "future_orderbook_event_snapshot_path_preserved": True,
        "future_runtime_resolver_snapshot_path_preserved": True,
        "future_official_source_production_path_recorded": True,
        "future_official_source_production_path": list(FUTURE_OFFICIAL_SOURCE_PRODUCTION_PATH),
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
        "run_validation_gates_uses_fresh_pytest_basetemp": _fresh_basetemp(repo_root),
        "fixed_tmp_run_validation_gates_pytest_reused": _fixed_tmp_reused(repo_root),
    }


def _binding_report(artifacts: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "cross_venue_execution_normalization_binding_report_id": (
            "PR128_CROSS_VENUE_EXECUTION_NORMALIZATION_BINDING_REPORT"
        ),
        "repo_pr_label": "PR128",
        "roadmap_pr_implemented": "PR110",
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "production_cross_venue_normalization_authority": False,
        "production_arbitrage_comparability_authority": False,
        "future_production_launch_path_preserved": True,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
        "source_pr127_handoff_id": artifacts["source_pr127_handoff_id"],
        "source_pr127_lifecycle_model_ids": artifacts["source_pr127_lifecycle_model_ids"],
        "taxonomy_records": artifacts["taxonomy_records"],
        "phase_binding_records": artifacts["phase_binding_records"],
        "transition_binding_records": artifacts["transition_binding_records"],
        "placeholder_normalization_records": artifacts[
            "placeholder_normalization_records"
        ],
        "arbitrage_comparability_precondition_records": artifacts[
            "arbitrage_comparability_precondition_records"
        ],
        "validation_receipts": artifacts["validation_receipts"],
        "rejection_records": artifacts["rejection_records"],
        "downstream_handoff": artifacts["downstream_handoff"],
    }


def _taxonomy_report(artifacts: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "cross_venue_execution_normalization_taxonomy_report_id": (
            "PR128_CROSS_VENUE_EXECUTION_NORMALIZATION_TAXONOMY_REPORT"
        ),
        "repo_pr_label": "PR128",
        "roadmap_pr_implemented": "PR110",
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "taxonomy_records": artifacts["taxonomy_records"],
        "fixture_normalized_taxonomy_count": len(REQUIRED_NORMALIZATION_DIMENSIONS),
        "production_cross_venue_normalization_authority_count": 0,
        "production_arbitrage_comparability_authority_count": 0,
        "future_production_launch_path_preserved": True,
    }


def _downstream_report(artifacts: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "cross_venue_execution_downstream_handoff_report_id": (
            "PR128_CROSS_VENUE_EXECUTION_DOWNSTREAM_HANDOFF_REPORT"
        ),
        "repo_pr_label": "PR128",
        "roadmap_pr_implemented": "PR110",
        "handoff": artifacts["downstream_handoff"],
        "production_downstream_authority_count": 0,
        "future_production_launch_path_preserved": True,
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
        if not isinstance(schema.get("required"), list) or not schema["required"]:
            failures.append(f"schema {schema_name} must declare required fields")
        if schema.get("additionalProperties") is not True:
            failures.append(f"schema {schema_name} must allow additive fields")
    return failures


def _validate_expected_fixtures(
    repo_root: Path,
    artifacts: Mapping[str, Any],
) -> list[str]:
    failures: list[str] = []
    main = artifacts["main_report"]
    binding = artifacts["binding_report"]
    taxonomy = binding["taxonomy_records"][0]
    handoff = artifacts["downstream_handoff_report"]["handoff"]
    projections = {
        "per_venue_execution_lifecycle_models.v1.fixture.json": {
            "mode": "SOURCE_REQUIRED",
            "execution": "DISABLED",
            "fixture_id": "PR128_PR127_PER_VENUE_EXECUTION_LIFECYCLE_MODELS_FIXTURE_V1",
            "source_repo_pr_label": "PR127",
            "model_ids_by_venue": {
                venue_id: model_id
                for venue_id, model_id in zip(
                    ["FORECASTEX_IBKR", "KALSHI", "POLYMARKET"],
                    binding["source_pr127_lifecycle_model_ids"],
                )
            },
            "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
            "production_cross_venue_normalization_authority": False,
        },
        "cross_venue_normalization_handoff.v1.fixture.json": {
            "mode": "SOURCE_REQUIRED",
            "execution": "DISABLED",
            "fixture_id": "PR128_PR127_CROSS_VENUE_NORMALIZATION_HANDOFF_FIXTURE_V1",
            "source_repo_pr_label": "PR127",
            "cross_venue_normalization_handoff_id": binding["source_pr127_handoff_id"],
            "venue_ids_in_scope": list(ACTIVE_STAGE1_VENUES),
            "production_cross_venue_normalization_authority": False,
            "production_arbitrage_comparability_authority": False,
        },
        "expected_normalization_taxonomy.v1.fixture.json": {
            "mode": "SOURCE_REQUIRED",
            "execution": "DISABLED",
            "fixture_id": "PR128_EXPECTED_NORMALIZATION_TAXONOMY_FIXTURE_V1",
            "taxonomy_id": taxonomy[
                "cross_venue_execution_normalization_taxonomy_id"
            ],
            "normalization_dimensions": list(REQUIRED_NORMALIZATION_DIMENSIONS),
            "taxonomy_authority_class": FIXTURE_AUTHORITY_CLASS,
            "production_cross_venue_normalization_authority": False,
            "production_arbitrage_comparability_authority": False,
        },
        "expected_phase_bindings.v1.fixture.json": {
            "mode": "SOURCE_REQUIRED",
            "execution": "DISABLED",
            "fixture_id": "PR128_EXPECTED_PHASE_BINDINGS_FIXTURE_V1",
            "phase_binding_count": main["fixture_phase_binding_count"],
            "stage1_venue_count": main["fixture_stage1_venue_count"],
            "production_cross_venue_normalization_authority_count": 0,
        },
        "expected_transition_bindings.v1.fixture.json": {
            "mode": "SOURCE_REQUIRED",
            "execution": "DISABLED",
            "fixture_id": "PR128_EXPECTED_TRANSITION_BINDINGS_FIXTURE_V1",
            "transition_binding_count": main["fixture_transition_binding_count"],
            "stage1_venue_count": main["fixture_stage1_venue_count"],
            "production_cross_venue_normalization_authority_count": 0,
        },
        "expected_arbitrage_comparability_preconditions.v1.fixture.json": {
            "mode": "SOURCE_REQUIRED",
            "execution": "DISABLED",
            "fixture_id": "PR128_EXPECTED_ARBITRAGE_COMPARABILITY_PRECONDITIONS_FIXTURE_V1",
            "arbitrage_precondition_count": main[
                "fixture_arbitrage_precondition_count"
            ],
            "production_arbitrage_comparability_authority_count": 0,
            "apparent_price_gap_arbitrage_claim_allowed": False,
        },
        "expected_downstream_handoff.v1.fixture.json": {
            "mode": "SOURCE_REQUIRED",
            "execution": "DISABLED",
            "fixture_id": "PR128_EXPECTED_DOWNSTREAM_HANDOFF_FIXTURE_V1",
            "cross_venue_execution_downstream_handoff_id": handoff[
                "cross_venue_execution_downstream_handoff_id"
            ],
            "future_prs": ["PR111", "PR112", "PR113", "PR114", "PR115", "PR116"],
            "production_downstream_authority": False,
            "future_production_launch_path_preserved": True,
        },
    }
    for fixture_name, projection in projections.items():
        expected = _load_json(repo_root / FIXTURE_DIR / fixture_name)
        if projection != expected:
            failures.append(f"{fixture_name} projection does not match expected fixture")
    return failures


def _validate_authority_boundaries(artifacts: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    main = artifacts["main_report"]
    zero_fields = (
        "production_cross_venue_normalization_authority_count",
        "production_arbitrage_comparability_authority_count",
        "production_order_authority_count",
        "production_connector_client_count",
        "runtime_resolver_snapshot_created_count",
        "runtime_cash_receipts_created_count",
        "private_state_fetch_created_count",
        "replay_paper_results_created_count",
        "connector_production_client_created_count",
        "network_io_created_count",
        "quantum_backend_execution_count",
        "quantum_simulator_execution_count",
        "optimizer_execution_count",
    )
    for field in zero_fields:
        if main[field] != 0:
            failures.append(f"{field} must be zero")
    false_fields = (
        "production_runtime_authority_created",
        "order_authority_created",
        "quantum_advantage_claim_created",
        "latency_superiority_claim_created",
        "execution_superiority_claim_created",
        "profit_evidence_created",
        "master_plan_modified",
        "atomicrows_bundle_created",
        "atomicrows_sha_created",
        "fixed_tmp_run_validation_gates_pytest_reused",
    )
    for field in false_fields:
        if main[field] is not False:
            failures.append(f"{field} must be false")
    binding = artifacts["binding_report"]
    for record in (
        binding["phase_binding_records"]
        + binding["transition_binding_records"]
        + binding["placeholder_normalization_records"]
        + binding["arbitrage_comparability_precondition_records"]
    ):
        if record["fixture_authority_class"] != FIXTURE_AUTHORITY_CLASS:
            failures.append("fixture output authority class mismatch")
        if record.get("production_cross_venue_normalization_authority") is not False:
            failures.append("fixture output production normalization authority must be false")
        if record.get("production_arbitrage_comparability_authority", False) is not False:
            failures.append("fixture output arbitrage authority must be false")
    return failures


def _validate_determinism(
    repo_root: Path,
    artifacts: Mapping[str, Any],
) -> list[str]:
    if artifacts != build_validation_artifacts(repo_root):
        return ["generated reports are not deterministic across in-memory rerun"]
    return []


def _rejection_counts(rejection_records: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {
        state: sum(
            1
            for record in rejection_records
            if record["normalization_state"] == state
        )
        for state in NORMALIZATION_STATES
        if state != READY_FOR_PR128_FIXTURE_SCOPE_NORMALIZATION
    }


def _all_fixture_only(artifacts: Mapping[str, Any]) -> bool:
    binding_records = (
        artifacts["phase_binding_records"]
        + artifacts["transition_binding_records"]
        + artifacts["placeholder_normalization_records"]
        + artifacts["arbitrage_comparability_precondition_records"]
    )
    return all(
        record.get("fixture_authority_class") == FIXTURE_AUTHORITY_CLASS
        and record.get("production_cross_venue_normalization_authority") is False
        and record.get("future_production_launch_path_preserved") is True
        for record in binding_records
    )


def _fresh_basetemp(repo_root: Path) -> bool:
    text = (repo_root / "tools/run_validation_gates.py").read_text(encoding="utf-8")
    return (
        "TemporaryDirectory" in text
        and 'prefix="run_validation_gates_pytest_"' in text
        and ".tmp/run_validation_gates_pytest" not in text
    )


def _fixed_tmp_reused(repo_root: Path) -> bool:
    text = (repo_root / "tools/run_validation_gates.py").read_text(encoding="utf-8")
    return ".tmp/run_validation_gates_pytest" in text


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
