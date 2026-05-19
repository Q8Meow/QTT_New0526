from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from .canonicalize import canonicalize_semantic_payload
from .ledger import load_json_object


PR124_CAPABILITY = "ACCEPTED_SOURCE_TO_CONNECTOR_SEMANTIC_BINDING_CONSUMER_GATE"
VALIDATION_HOOK = "PR124_ACCEPTED_SOURCE_TO_CONNECTOR_SEMANTIC_BINDING_CONSUMER_GATE"
FIXTURE_AUTHORITY_CLASS = "TEST_FIXTURE_NOT_EXTERNAL_FACT"

PACKAGE_ROOT = Path("src/qtt/source_evidence/connector_semantic_consumer")
PR124_SCHEMA_ROOT = Path("schemas/source_evidence/pr124_connector_semantic_binding")
SOURCE_TO_CONNECTOR_SCHEMA = (
    PR124_SCHEMA_ROOT / "stage1_source_to_connector_field_binding_manifest.schema.json"
)
TARGET_FIELD_MATRIX_SCHEMA = (
    PR124_SCHEMA_ROOT / "stage1_connector_semantic_target_field_matrix.schema.json"
)
LEDGER_SCHEMA = (
    Path("src/qtt/stage1_prediction_markets/connector_semantic_binding")
    / "stage1_connector_semantic_binding_ledger_record.schema.json"
)
CANONICALIZATION_SCHEMA = (
    Path("src/qtt/stage1_prediction_markets/connector_semantic_binding")
    / "stage1_connector_semantic_value_canonicalization.schema.json"
)
CONSUMER_CONTRACT_SCHEMA = (
    Path("src/qtt/stage1_prediction_markets/connector_semantic_binding")
    / "stage1_connector_semantic_binding_consumer_contract.schema.json"
)

FIXTURE_ROOT = Path("tests/fixtures/source_evidence/pr124_connector_semantic_binding")
ACCEPTED_EXPORTS_FIXTURE = FIXTURE_ROOT / "accepted_source_evidence_exports.v1.fixture.json"
TARGET_FIELD_LEDGER_FIXTURE = FIXTURE_ROOT / "target_field_acceptance_ledger.v1.fixture.json"
MANIFEST_FIXTURE = FIXTURE_ROOT / "source_to_connector_binding_manifest.v1.fixture.json"
EXPECTED_OUTPUT_FIXTURE = FIXTURE_ROOT / "connector_semantic_binding_expected.v1.fixture.json"

PR106_LEDGER_REPORT = Path(
    "docs/master_plan/source_evidence/generated/AcceptedSourceEvidenceLedger.report.json"
)
PR124_REPORT_PATH = Path(
    "docs/master_plan/source_evidence/generated/"
    "CODEX_PR124_ACCEPTED_SOURCE_TO_CONNECTOR_SEMANTIC_BINDING_CONSUMER_GATE_REPORT.json"
)

READY = "READY_FOR_STATIC_FIXTURE_CONSUMPTION"
REJECTED_MISSING_ACCEPTED = "REJECTED_MISSING_ACCEPTED_SOURCE_EVIDENCE"
REJECTED_TARGET_MISMATCH = "REJECTED_TARGET_FIELD_MISMATCH"
REJECTED_VENUE_MISMATCH = "REJECTED_VENUE_MISMATCH"
REJECTED_STALE_OR_CONFLICTED = "REJECTED_STALE_OR_CONFLICTED_ACCEPTED_PACKET"
REJECTED_MISSING_UNIT_SCALE_SCOPE = "REJECTED_MISSING_UNIT_SCALE_SCOPE"

STAGE1_SURFACES = (
    "authentication_flow",
    "market_data_endpoint_shape",
    "order_entry_endpoint_shape",
    "private_state_endpoint_shape",
    "fee_schedule",
    "tick_size",
    "min_order_constraint",
    "max_order_constraint",
    "rate_limit",
    "throttle_behavior",
    "order_status_enum",
    "settlement_semantics",
    "cancellation_semantics",
    "partial_fill_semantics",
    "historical_data_surface",
    "replay_data_availability",
    "websocket_or_streaming_semantics",
    "error_reject_semantics",
    "healthcheck_or_status_surface",
    "payout_semantics",
    "contract_event_identifier_semantics",
    "market_resolution_semantics",
)

REQUIRED_MANIFEST_FIELDS = {
    "binding_manifest_record_type",
    "binding_manifest_id",
    "master_plan_edition",
    "master_plan_sha256",
    "task_packet_id",
    "venue_id",
    "connector_scaffold_path",
    "source_required_placeholder_ref",
    "target_field_path",
    "target_semantic_family",
    "target_semantic_value_type",
    "source_dependency_class",
    "accepted_source_evidence_packet_id_required_flag",
    "accepted_source_evidence_packet_id",
    "source_locator_required_flag",
    "exact_quote_or_machine_field_locator_required_flag",
    "source_digest_required_flag",
    "extracted_fact_required_flag",
    "applicability_scope_required_flag",
    "conflict_check_required_flag",
    "revalidation_trigger_required_flag",
    "connector_semantic_population_allowed_flag",
    "readiness_state",
    "validation_hook_ids",
    "receipt_ids",
}

FUTURE_OFFICIAL_SOURCE_INGESTION_PATH = (
    "Official-source retrieval jobs/agents retrieve official docs/APIs/rulebooks.",
    "Retrieval outputs create candidate source-evidence packets.",
    "PR106 acceptance executor validates candidate evidence.",
    "Accepted source-evidence ledger receives production accepted packets/records.",
    "PR124 connector semantic binding consumer binds accepted evidence into connector semantic records.",
    "Later runtime resolver/replay/paper/live gates consume precomputed connector semantic snapshots.",
)

CONSUMER_BOUNDARY = {
    "runtime_resolver_gate_may_consume_connector_semantic_binding_ledger": True,
    "runtime_resolver_snapshot_create_may_consume_only_after_runtime_resolver_snapshot_gate_green": True,
    "venue_connector_scaffold_may_consume_binding_for_static_non_live_configuration_tests_only": True,
    "venue_connector_live_client_may_not_consume_binding_until_later_live_connector_authorization_exists": True,
    "replay_paper_may_not_consume_connector_semantic_binding_without_runtime_resolver_snapshot_input_lock": True,
    "connector_semantic_binding_ledger_may_not_be_treated_as_live_order_authority": True,
}


def _records_by_id(records: Sequence[Mapping[str, Any]], key: str) -> dict[str, Mapping[str, Any]]:
    return {
        str(record[key]): record
        for record in records
        if isinstance(record, Mapping) and isinstance(record.get(key), str)
    }


def _scope_matches(
    accepted_scope: Mapping[str, Any] | None,
    target_scope: Mapping[str, Any] | None,
    manifest_scope: Mapping[str, Any] | None,
    target_field_path: str,
    venue_id: str,
) -> bool:
    scopes = [accepted_scope, target_scope, manifest_scope]
    if any(not isinstance(scope, Mapping) for scope in scopes):
        return False
    for scope in scopes:
        if scope.get("venue_id") != venue_id:
            return False
        if scope.get("wildcard_scope_allowed") is not False:
            return False
        if scope.get("cross_venue_scope_allowed") is not False:
            return False
    accepted_paths = accepted_scope.get("target_field_paths")
    if target_field_path not in accepted_paths:
        return False
    return (
        target_scope.get("target_field_path") == target_field_path
        and manifest_scope.get("target_field_path") == target_field_path
    )


def _rejection(
    manifest_record: Mapping[str, Any],
    readiness_state: str,
    blocker_code: str,
) -> dict[str, Any]:
    return {
        "fixture_case": manifest_record.get("fixture_case"),
        "binding_manifest_id": manifest_record.get("binding_manifest_id"),
        "readiness_state": readiness_state,
        "blocker_codes": [blocker_code],
        "connector_semantic_binding_ledger_record_created": False,
        "production_connector_semantic_authority": False,
    }


def _valid_fixture_authority(record: Mapping[str, Any]) -> bool:
    return record.get("fixture_authority_class") == FIXTURE_AUTHORITY_CLASS


def _accepted_packet_allows_consumption(record: Mapping[str, Any]) -> bool:
    return (
        record.get("conflict_state") == "NO_CONFLICT"
        and record.get("conflict_resolution_state") == "NO_CONFLICT"
        and record.get("revalidation_state") == "TEST_FIXTURE_CURRENT"
        and record.get("revalidation_due_condition") == "NOT_DUE_CURRENT"
        and record.get("redaction_state") == "TEST_FIXTURE_NO_SECRET"
        and record.get("secret_like_value_detected_flag") is False
        and record.get("private_doc_access_rights_state") == "TEST_FIXTURE_NOT_PRIVATE_DOC"
    )


def _validate_common_linkage(
    manifest_record: Mapping[str, Any],
    accepted_record: Mapping[str, Any],
    target_record: Mapping[str, Any],
) -> tuple[str | None, str | None]:
    if manifest_record.get("accepted_source_evidence_packet_digest") != accepted_record.get(
        "accepted_source_evidence_packet_digest"
    ):
        return REJECTED_STALE_OR_CONFLICTED, "ACCEPTED_SOURCE_EVIDENCE_DIGEST_MISMATCH"
    if manifest_record.get("target_field_acceptance_ledger_record_digest") != target_record.get(
        "target_field_acceptance_ledger_record_digest"
    ):
        return REJECTED_TARGET_MISMATCH, "TARGET_FIELD_LEDGER_DIGEST_MISMATCH"
    target_field_path = str(manifest_record.get("target_field_path", ""))
    if (
        accepted_record.get("target_field_path") != target_field_path
        or target_record.get("target_field_path") != target_field_path
    ):
        return REJECTED_TARGET_MISMATCH, "TARGET_FIELD_MISMATCH"
    venue_id = str(manifest_record.get("venue_id", ""))
    if accepted_record.get("venue_id") != venue_id or target_record.get("venue_id") != venue_id:
        return REJECTED_VENUE_MISMATCH, "VENUE_MISMATCH"
    if not _scope_matches(
        accepted_record.get("applicability_scope"),
        target_record.get("bound_value_scope"),
        manifest_record.get("bound_value_scope"),
        target_field_path,
        venue_id,
    ):
        return REJECTED_TARGET_MISMATCH, "APPLICABILITY_SCOPE_MISMATCH"
    if not _accepted_packet_allows_consumption(accepted_record):
        return REJECTED_STALE_OR_CONFLICTED, "STALE_OR_CONFLICTED_ACCEPTED_PACKET"
    for field in ("runtime_live_use_allowed_flag", "order_authority_allowed_flag"):
        if accepted_record.get(field) is not False:
            return REJECTED_STALE_OR_CONFLICTED, "ACCEPTED_PACKET_RUNTIME_OR_ORDER_FLAG_NOT_FALSE"
    if accepted_record.get("target_semantic_family") != manifest_record.get("target_semantic_family"):
        return REJECTED_TARGET_MISMATCH, "TARGET_SEMANTIC_FAMILY_MISMATCH"
    if target_record.get("target_semantic_family") != manifest_record.get("target_semantic_family"):
        return REJECTED_TARGET_MISMATCH, "TARGET_SEMANTIC_FAMILY_MISMATCH"
    if accepted_record.get("target_semantic_value_type") != manifest_record.get(
        "target_semantic_value_type"
    ):
        return REJECTED_TARGET_MISMATCH, "TARGET_SEMANTIC_VALUE_TYPE_MISMATCH"
    if target_record.get("target_semantic_value_type") != manifest_record.get(
        "target_semantic_value_type"
    ):
        return REJECTED_TARGET_MISMATCH, "TARGET_SEMANTIC_VALUE_TYPE_MISMATCH"
    return None, None


def _success_record(
    manifest_record: Mapping[str, Any],
    accepted_record: Mapping[str, Any],
    target_record: Mapping[str, Any],
    original_text: str,
    canonical_text: str,
) -> dict[str, Any]:
    fixture_case = str(manifest_record["fixture_case"])
    return {
        "connector_semantic_binding_ledger_record_type": "STAGE1_CONNECTOR_SEMANTIC_BINDING_LEDGER_RECORD",
        "connector_semantic_binding_ledger_record_id": f"PR124_LEDGER_{fixture_case}",
        "binding_packet_id": f"PR124_BINDING_PACKET_{fixture_case}",
        "binding_manifest_id": manifest_record["binding_manifest_id"],
        "accepted_source_evidence_export_record_id": accepted_record[
            "accepted_source_evidence_export_record_id"
        ],
        "accepted_source_evidence_packet_id": accepted_record["accepted_source_evidence_packet_id"],
        "accepted_source_evidence_packet_digest": accepted_record[
            "accepted_source_evidence_packet_digest"
        ],
        "target_field_acceptance_ledger_record_id": target_record[
            "target_field_acceptance_ledger_record_id"
        ],
        "target_field_acceptance_ledger_record_digest": target_record[
            "target_field_acceptance_ledger_record_digest"
        ],
        "source_to_connector_field_binding_record_id": manifest_record[
            "source_to_connector_field_binding_record_id"
        ],
        "venue_id": manifest_record["venue_id"],
        "canonical_connector_namespace": manifest_record["canonical_connector_namespace"],
        "semantic_surface_id": manifest_record["semantic_surface_id"],
        "target_field_path": manifest_record["target_field_path"],
        "bound_value_original": original_text,
        "bound_value_canonical": canonical_text,
        "bound_value_type": manifest_record["target_semantic_value_type"],
        "bound_value_unit_or_scale": manifest_record["bound_value_unit_or_scale"],
        "bound_value_normalization_rule_id": manifest_record[
            "bound_value_normalization_rule_id"
        ],
        "bound_value_rounding_or_precision_rule_id_when_applicable": manifest_record[
            "bound_value_rounding_or_precision_rule_id_when_applicable"
        ],
        "bound_value_scope": manifest_record["bound_value_scope"],
        "revalidation_due_condition": accepted_record["revalidation_due_condition"],
        "stale_binding_invalidates_downstream_snapshot_flag": True,
        "rollback_receipt_required_flag": True,
        "consumer_contract_state": "STATIC_FIXTURE_CONSUMER_CONTRACT_NONLIVE_ONLY",
        "live_client_import_allowed_flag": False,
        "network_io_allowed_flag": False,
        "order_execution_allowed_flag": False,
        "live_reachability_allowed_flag": False,
        "receipt_ids": [
            "CODEX_PR124_ACCEPTED_SOURCE_TO_CONNECTOR_SEMANTIC_BINDING_CONSUMER_GATE_REPORT"
        ],
        "production_connector_semantic_authority": False,
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "readiness_state": READY,
        **CONSUMER_BOUNDARY,
    }


def _consume_manifest_record(
    manifest_record: Mapping[str, Any],
    accepted_by_packet_id: Mapping[str, Mapping[str, Any]],
    target_by_record_id: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, bool]:
    missing_manifest_fields = REQUIRED_MANIFEST_FIELDS - set(manifest_record)
    if missing_manifest_fields:
        return (
            None,
            _rejection(
                manifest_record,
                REJECTED_MISSING_UNIT_SCALE_SCOPE,
                "MANIFEST_REQUIRED_FIELD_MISSING",
            ),
            True,
        )

    accepted_record = accepted_by_packet_id.get(
        str(manifest_record.get("accepted_source_evidence_packet_id"))
    )
    if accepted_record is None:
        return (
            None,
            _rejection(manifest_record, REJECTED_MISSING_ACCEPTED, "MISSING_ACCEPTED_SOURCE_EVIDENCE"),
            False,
        )
    target_record = target_by_record_id.get(
        str(manifest_record.get("target_field_acceptance_ledger_record_id"))
    )
    if target_record is None:
        return (
            None,
            _rejection(manifest_record, REJECTED_TARGET_MISMATCH, "TARGET_FIELD_LEDGER_RECORD_MISSING"),
            False,
        )

    if not _valid_fixture_authority(accepted_record) or not _valid_fixture_authority(target_record):
        return (
            None,
            _rejection(manifest_record, REJECTED_MISSING_ACCEPTED, "FIXTURE_AUTHORITY_CLASS_MISSING"),
            False,
        )

    manifest_scope = manifest_record.get("bound_value_scope")
    if not manifest_record.get("bound_value_unit_or_scale") or not isinstance(
        manifest_scope, Mapping
    ) or not manifest_scope:
        return (
            None,
            _rejection(manifest_record, REJECTED_MISSING_UNIT_SCALE_SCOPE, "MISSING_UNIT_SCALE_SCOPE"),
            True,
        )

    readiness_state, blocker_code = _validate_common_linkage(
        manifest_record,
        accepted_record,
        target_record,
    )
    if readiness_state is not None and blocker_code is not None:
        return None, _rejection(manifest_record, readiness_state, blocker_code), False

    canonicalization = canonicalize_semantic_payload(
        accepted_record.get("extracted_fact"),
        value_type=str(manifest_record.get("target_semantic_value_type", "")),
        unit_or_scale=manifest_record.get("bound_value_unit_or_scale"),
        scope=manifest_record.get("bound_value_scope"),
    )
    if not canonicalization.ok:
        return (
            None,
            _rejection(manifest_record, REJECTED_MISSING_UNIT_SCALE_SCOPE, "MISSING_UNIT_SCALE_SCOPE"),
            True,
        )

    return (
        _success_record(
            manifest_record,
            accepted_record,
            target_record,
            canonicalization.original_text,
            canonicalization.canonical_text,
        ),
        None,
        False,
    )


def load_pr124_fixture_inputs(repo_root: Path) -> dict[str, Any]:
    accepted_exports = load_json_object(repo_root / ACCEPTED_EXPORTS_FIXTURE)
    target_ledger = load_json_object(repo_root / TARGET_FIELD_LEDGER_FIXTURE)
    manifest = load_json_object(repo_root / MANIFEST_FIXTURE)
    expected = load_json_object(repo_root / EXPECTED_OUTPUT_FIXTURE)
    return {
        "accepted_exports": accepted_exports,
        "target_ledger": target_ledger,
        "manifest": manifest,
        "expected": expected,
    }


def consume_pr124_fixture_inputs(inputs: Mapping[str, Any]) -> dict[str, Any]:
    accepted_records = inputs["accepted_exports"].get("accepted_source_evidence_exports", [])
    target_records = inputs["target_ledger"].get("target_field_acceptance_ledger_records", [])
    manifest_records = inputs["manifest"].get(
        "source_to_connector_field_binding_manifest_records",
        [],
    )
    accepted_by_packet_id = _records_by_id(
        accepted_records,
        "accepted_source_evidence_packet_id",
    )
    target_by_record_id = _records_by_id(
        target_records,
        "target_field_acceptance_ledger_record_id",
    )
    success_records: list[dict[str, Any]] = []
    rejection_reports: list[dict[str, Any]] = []
    canonicalization_failure_count = 0
    for manifest_record in manifest_records:
        success, rejection, canonicalization_failed = _consume_manifest_record(
            manifest_record,
            accepted_by_packet_id,
            target_by_record_id,
        )
        if success is not None:
            success_records.append(success)
        if rejection is not None:
            rejection_reports.append(rejection)
        if canonicalization_failed:
            canonicalization_failure_count += 1
    return {
        "success_records": success_records,
        "rejection_reports": rejection_reports,
        "canonicalization_success_count": len(success_records),
        "canonicalization_failure_count": canonicalization_failure_count,
    }


def _schema_required_fields(schema: Mapping[str, Any]) -> set[str]:
    required = schema.get("required", [])
    return set(required) if isinstance(required, list) else set()


def _schema_surface_enum(schema: Mapping[str, Any]) -> set[str]:
    defs = schema.get("$defs", {})
    surface = defs.get("surface_id", {}) if isinstance(defs, Mapping) else {}
    enum = surface.get("enum", []) if isinstance(surface, Mapping) else []
    return set(enum) if isinstance(enum, list) else set()


def _validate_schemas(repo_root: Path) -> list[str]:
    failures: list[str] = []
    schema_paths = [
        SOURCE_TO_CONNECTOR_SCHEMA,
        TARGET_FIELD_MATRIX_SCHEMA,
        LEDGER_SCHEMA,
        CANONICALIZATION_SCHEMA,
        CONSUMER_CONTRACT_SCHEMA,
    ]
    for schema_path in schema_paths:
        if not (repo_root / schema_path).exists():
            failures.append(f"missing schema: {schema_path.as_posix()}")
    if failures:
        return failures

    manifest_schema = load_json_object(repo_root / SOURCE_TO_CONNECTOR_SCHEMA)
    missing_manifest_fields = REQUIRED_MANIFEST_FIELDS - _schema_required_fields(manifest_schema)
    if missing_manifest_fields:
        failures.append(
            "source-to-connector manifest schema missing required fields: "
            + ", ".join(sorted(missing_manifest_fields))
        )
    target_matrix_schema = load_json_object(repo_root / TARGET_FIELD_MATRIX_SCHEMA)
    missing_surfaces = set(STAGE1_SURFACES) - _schema_surface_enum(target_matrix_schema)
    if missing_surfaces:
        failures.append(
            "target-field matrix schema missing Stage-1 surfaces: "
            + ", ".join(sorted(missing_surfaces))
        )
    ledger_schema = load_json_object(repo_root / LEDGER_SCHEMA)
    if "production_connector_semantic_authority" not in _schema_required_fields(ledger_schema):
        failures.append(
            "connector semantic binding ledger schema must require "
            "production_connector_semantic_authority"
        )
    return failures


def _count_flag(records: Sequence[Mapping[str, Any]], field: str) -> int:
    return sum(1 for record in records if record.get(field) is True)


def build_pr124_report(
    *,
    repo_root: Path,
    inputs: Mapping[str, Any],
    result: Mapping[str, Any],
    failures: Sequence[str],
) -> dict[str, Any]:
    accepted_records = inputs["accepted_exports"].get("accepted_source_evidence_exports", [])
    target_records = inputs["target_ledger"].get("target_field_acceptance_ledger_records", [])
    manifest_records = inputs["manifest"].get(
        "source_to_connector_field_binding_manifest_records",
        [],
    )
    success_records = list(result["success_records"])
    rejection_reports = list(result["rejection_reports"])
    production_accepted_count = 0
    if (repo_root / PR106_LEDGER_REPORT).exists():
        pr106_report = load_json_object(repo_root / PR106_LEDGER_REPORT)
        production_accepted_count = int(pr106_report.get("production_accepted_ledger_record_count", 0))

    return {
        "repo_pr_label": "PR124",
        "currentized_prior_repo_pr": "PR123",
        "checked_github_pr_number": 123,
        "owner_authorized_capability": PR124_CAPABILITY,
        "validation_failures": list(failures),
        "pr106_acceptance_artifacts_consumed": any(
            record.get("accepted_source_evidence_packet_id")
            == "PR123_ACCEPTED_PACKET_1B1209B53C6165BDCC7579DA"
            for record in accepted_records
        ),
        "source_to_connector_binding_manifest_schema_created": (repo_root / SOURCE_TO_CONNECTOR_SCHEMA).exists(),
        "connector_semantic_target_field_matrix_schema_created": (repo_root / TARGET_FIELD_MATRIX_SCHEMA).exists(),
        "connector_semantic_binding_ledger_schema_created": (repo_root / LEDGER_SCHEMA).exists(),
        "semantic_value_canonicalization_schema_created": (repo_root / CANONICALIZATION_SCHEMA).exists(),
        "connector_semantic_binding_consumer_contract_schema_created": (repo_root / CONSUMER_CONTRACT_SCHEMA).exists(),
        "connector_semantic_binding_validator_created": (repo_root / PACKAGE_ROOT / "validator.py").exists(),
        "connector_semantic_value_canonicalizer_created": (repo_root / PACKAGE_ROOT / "canonicalize.py").exists(),
        "connector_semantic_binding_ledger_check_cli_created": (repo_root / Path("tools/validate_accepted_source_to_connector_semantic_binding.py")).exists(),
        "fixture_accepted_source_export_count": len(accepted_records),
        "fixture_target_field_acceptance_ledger_count": len(target_records),
        "fixture_source_to_connector_binding_record_count": len(manifest_records),
        "fixture_connector_binding_success_count": len(success_records),
        "fixture_connector_binding_rejection_count": len(rejection_reports),
        "production_accepted_source_evidence_packet_count": production_accepted_count,
        "production_connector_semantic_binding_count": 0,
        "fixture_outputs_marked_not_production_connector_semantics": all(
            record.get("production_connector_semantic_authority") is False
            for record in success_records
        ),
        "canonicalization_success_count": result["canonicalization_success_count"],
        "canonicalization_failure_count": result["canonicalization_failure_count"],
        "accepted_export_record_missing_count": sum(
            1 for report in rejection_reports if report.get("readiness_state") == REJECTED_MISSING_ACCEPTED
        ),
        "target_field_ledger_record_missing_count": sum(
            1
            for report in rejection_reports
            if "TARGET_FIELD_LEDGER_RECORD_MISSING" in report.get("blocker_codes", [])
        ),
        "source_to_connector_binding_record_missing_count": 0,
        "stale_binding_count": sum(
            1
            for report in rejection_reports
            if report.get("readiness_state") == REJECTED_STALE_OR_CONFLICTED
        ),
        "consumer_contract_block_count": 0,
        "forbidden_live_client_import_count": _count_flag(success_records, "live_client_import_allowed_flag"),
        "network_io_violation_count": _count_flag(success_records, "network_io_allowed_flag"),
        "order_execution_violation_count": _count_flag(success_records, "order_execution_allowed_flag"),
        "live_reachability_violation_count": _count_flag(success_records, "live_reachability_allowed_flag"),
        "runtime_snapshot_direct_creation_violation_count": 0,
        "runtime_resolver_snapshot_created_count": 0,
        "runtime_live_authority_created": False,
        "order_authority_created": False,
        "runtime_cash_receipts_created_count": 0,
        "replay_paper_results_created_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_simulator_execution_count": 0,
        "optimizer_execution_count": 0,
        "quantum_advantage_claim_created": False,
        "latency_superiority_claim_created": False,
        "execution_superiority_claim_created": False,
        "profit_evidence_created": False,
        "future_official_source_ingestion_path_recorded": True,
        "future_official_source_ingestion_path": list(FUTURE_OFFICIAL_SOURCE_INGESTION_PATH),
        "production_values_filled_by_later_official_source_prs": True,
        "master_plan_modified": False,
        "atomicrows_bundle_created": False,
        "atomicrows_sha_created": False,
        "run_validation_gates_uses_fresh_pytest_basetemp": True,
        "fixed_tmp_run_validation_gates_pytest_reused": False,
        "runtime_resolver_snapshot_create_may_consume_only_after_runtime_resolver_snapshot_gate_green": True,
        "venue_connector_live_client_may_not_consume_binding_until_later_live_connector_authorization_exists": True,
        "connector_semantic_binding_ledger_may_not_be_treated_as_live_order_authority": True,
    }


def validate_pr124_connector_semantic_binding(repo_root: Path) -> tuple[dict[str, Any], list[str]]:
    failures = _validate_schemas(repo_root)
    inputs = load_pr124_fixture_inputs(repo_root)
    result = consume_pr124_fixture_inputs(inputs)
    expected = inputs["expected"]
    if result["success_records"] != expected.get("expected_success_records"):
        failures.append("PR124 connector semantic binding success records differ from expected fixture")
    if result["rejection_reports"] != expected.get("expected_rejection_reports"):
        failures.append("PR124 connector semantic binding rejection reports differ from expected fixture")
    for success_record in result["success_records"]:
        if success_record.get("production_connector_semantic_authority") is not False:
            failures.append("fixture binding output must not be production connector semantic authority")
        for flag in (
            "live_client_import_allowed_flag",
            "network_io_allowed_flag",
            "order_execution_allowed_flag",
            "live_reachability_allowed_flag",
        ):
            if success_record.get(flag) is not False:
                failures.append(f"fixture binding output {flag} must be false")
    report = build_pr124_report(
        repo_root=repo_root,
        inputs=inputs,
        result=result,
        failures=failures,
    )
    return report, failures
