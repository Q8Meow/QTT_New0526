from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from src.qtt.source_evidence.connector_semantic_consumer.ledger import load_json_object

from .materiality import MATERIALITY_CLASSES
from .scheduler import (
    ACCEPTED_SOURCE_FIXTURE,
    CONNECTOR_BINDING_FIXTURE,
    DETERMINISTIC_FIXTURE_TIME,
    EVENT_TRIGGERED_REVALIDATION_LATENCY_CLASS,
    EXPECTED_MATERIALITY_FIXTURE,
    EXPECTED_SCHEDULE_FIXTURE,
    EXPECTED_SNAPSHOT_FIXTURE,
    EXPECTED_SUPERSESSION_FIXTURE,
    LOW_RISK_REVALIDATION_INTERVAL,
    LIVE_CRITICAL_REVALIDATION_INTERVAL,
    PR125_REPORT_PATH,
    REVALIDATION_EVENTS_FIXTURE,
    SCHEDULER_REPORT_PATH,
    SOURCE_CHANGE_SNAPSHOT_REPORT_PATH,
    load_pr125_fixture_inputs,
    run_revalidation_scheduler,
)


SCHEMA_ROOT = Path("schemas/source_evidence/revalidation")
REVALIDATION_POLICY_SCHEMA = SCHEMA_ROOT / "source_revalidation_policy.schema.json"
REVALIDATION_SCHEDULE_SCHEMA = SCHEMA_ROOT / "source_revalidation_schedule.schema.json"
REVALIDATION_DECISION_RECEIPT_SCHEMA = (
    SCHEMA_ROOT / "source_revalidation_decision_receipt.schema.json"
)
SOURCE_SUPERSESSION_RECORD_SCHEMA = SCHEMA_ROOT / "source_supersession_record.schema.json"
SOURCE_CHANGE_MATERIALITY_EVENT_SCHEMA = (
    SCHEMA_ROOT / "source_change_materiality_event.schema.json"
)
SOURCE_CHANGE_IMPACT_SNAPSHOT_SCHEMA = (
    SCHEMA_ROOT / "source_change_impact_snapshot.schema.json"
)

PR106_ACCEPTANCE_REPORT = Path(
    "docs/master_plan/source_evidence/generated/"
    "CODEX_PR123_ACCEPTED_SOURCE_EVIDENCE_ACCEPTANCE_EXECUTOR_LEDGER_REPORT.json"
)
PR124_CONNECTOR_REPORT = Path(
    "docs/master_plan/source_evidence/generated/"
    "CODEX_PR124_ACCEPTED_SOURCE_TO_CONNECTOR_SEMANTIC_BINDING_CONSUMER_GATE_REPORT.json"
)
RUN_VALIDATION_GATES = Path("tools/run_validation_gates.py")

SUCCESS_MARKER = "QTT_SOURCE_REVALIDATION_SUPERSESSION_AND_MATERIALITY_SCHEDULER_OK"
FAILURE_MARKER = "QTT_SOURCE_REVALIDATION_SUPERSESSION_AND_MATERIALITY_SCHEDULER_FAILED"

FUTURE_OFFICIAL_SOURCE_REVALIDATION_PATH = (
    "Official-source retrieval jobs/agents detect official source changes.",
    "Retrieval outputs create candidate source-change evidence packets.",
    "PR106 acceptance executor validates candidate evidence.",
    "Accepted source-evidence ledger receives production accepted revalidated packets/records.",
    "PR125 scheduler classifies revalidation, supersession, and materiality.",
    "PR124 connector semantic binding consumer updates source-backed connector semantic records in later production binding PRs.",
    "Later runtime resolver/replay/paper/live gates consume precomputed source-change snapshots.",
)


def _required_fields(schema: Mapping[str, Any]) -> set[str]:
    required = schema.get("required", [])
    return set(required) if isinstance(required, list) else set()


def _schema_paths() -> tuple[Path, ...]:
    return (
        REVALIDATION_POLICY_SCHEMA,
        REVALIDATION_SCHEDULE_SCHEMA,
        REVALIDATION_DECISION_RECEIPT_SCHEMA,
        SOURCE_SUPERSESSION_RECORD_SCHEMA,
        SOURCE_CHANGE_MATERIALITY_EVENT_SCHEMA,
        SOURCE_CHANGE_IMPACT_SNAPSHOT_SCHEMA,
    )


def _validate_schemas(repo_root: Path) -> list[str]:
    failures: list[str] = []
    required_by_schema = {
        REVALIDATION_POLICY_SCHEMA: {
            "source_revalidation_policy_id",
            "live_critical_revalidation_interval",
            "low_risk_revalidation_interval",
            "event_triggered_revalidation_latency_class",
            "live_critical_source_field_classes",
            "low_risk_source_field_classes",
        },
        REVALIDATION_SCHEDULE_SCHEMA: {
            "source_revalidation_schedule_record_id",
            "accepted_source_evidence_packet_id",
            "revalidation_state",
            "revalidation_due_state",
            "production_revalidation_authority",
        },
        REVALIDATION_DECISION_RECEIPT_SCHEMA: {
            "source_revalidation_decision_receipt_id",
            "accepted_source_evidence_packet_id",
            "revalidation_state",
            "production_revalidation_authority",
        },
        SOURCE_SUPERSESSION_RECORD_SCHEMA: {
            "source_supersession_record_id",
            "superseded_packet_id",
            "superseding_packet_id",
            "supersession_state",
            "production_source_change_authority",
        },
        SOURCE_CHANGE_MATERIALITY_EVENT_SCHEMA: {
            "source_change_materiality_event_id",
            "materiality_class",
            "source_change_route",
            "production_source_change_authority",
        },
        SOURCE_CHANGE_IMPACT_SNAPSHOT_SCHEMA: {
            "source_change_snapshot_id",
            "snapshot_scope",
            "production_source_change_authority",
            "live_pretrade_consumption_mode",
        },
    }
    for schema_path, required_fields in required_by_schema.items():
        full_path = repo_root / schema_path
        if not full_path.exists():
            failures.append(f"missing schema: {schema_path.as_posix()}")
            continue
        schema = load_json_object(full_path)
        missing_fields = required_fields - _required_fields(schema)
        if missing_fields:
            failures.append(
                f"{schema_path.as_posix()} missing required fields: "
                + ", ".join(sorted(missing_fields))
            )
    return failures


def _all_records_marked_fixture_only(records: Sequence[Mapping[str, Any]]) -> bool:
    return all(
        record.get("fixture_authority_class") == "TEST_FIXTURE_NOT_EXTERNAL_FACT"
        and record.get("production_source_change_authority") is False
        for record in records
    )


def _count_true(records: Sequence[Mapping[str, Any]], field: str) -> int:
    return sum(1 for record in records if record.get(field) is True)


def _run_validation_gates_uses_fresh_basetemp(repo_root: Path) -> bool:
    text = (repo_root / RUN_VALIDATION_GATES).read_text(encoding="utf-8")
    return (
        "TemporaryDirectory" in text
        and 'prefix="run_validation_gates_pytest_"' in text
        and ".tmp/run_validation_gates_pytest" not in text
    )


def _fixed_tmp_reused(repo_root: Path) -> bool:
    text = (repo_root / RUN_VALIDATION_GATES).read_text(encoding="utf-8")
    return ".tmp/run_validation_gates_pytest" in text


def _scheduler_source_has_forbidden_io(repo_root: Path) -> bool:
    source_root = repo_root / Path("src/qtt/source_evidence/revalidation")
    forbidden_tokens = ("requests", "urllib", "socket", "http.client", "subprocess")
    for source_path in source_root.glob("*.py"):
        if source_path.name == "validator.py":
            continue
        text = source_path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden_tokens):
            return True
    return False


def _build_scheduler_report(result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "scheduler_report_id": "SourceRevalidationScheduler.report",
        "generated_by_tool": "tools/source_revalidation_scheduler.py",
        "deterministic_fixture_time": result["deterministic_fixture_time"],
        "source_revalidation_schedule_records": result[
            "source_revalidation_schedule_records"
        ],
        "source_revalidation_decision_receipts": result[
            "source_revalidation_decision_receipts"
        ],
        "source_supersession_records": result["source_supersession_records"],
        "source_change_materiality_events": result[
            "source_change_materiality_events"
        ],
        "production_revalidation_authority": False,
        "production_source_change_authority": False,
        "live_pretrade_use_allowed_flag": False,
        "network_io_allowed_flag": False,
        "source_retrieval_allowed_flag": False,
        "source_acceptance_allowed_flag": False,
        "connector_binding_mutation_allowed_flag": False,
        "order_execution_allowed_flag": False,
        "live_reachability_allowed_flag": False,
    }


def build_pr125_report(
    *,
    repo_root: Path,
    inputs: Mapping[str, Any],
    result: Mapping[str, Any],
    failures: Sequence[str],
) -> dict[str, Any]:
    accepted_records = inputs["accepted_source_evidence_records"][
        "accepted_source_evidence_records"
    ]
    connector_records = inputs["connector_semantic_binding_records"][
        "connector_semantic_binding_records"
    ]
    event_records = inputs["revalidation_events"]["revalidation_events"]
    schedule_records = result["source_revalidation_schedule_records"]
    supersession_records = result["source_supersession_records"]
    materiality_events = result["source_change_materiality_events"]
    snapshots = result["source_change_impact_snapshots"]

    return {
        "repo_pr_label": "PR125",
        "roadmap_pr_implemented": "PR107",
        "currentized_prior_repo_pr": "PR124",
        "checked_github_pr_number": 124,
        "owner_authorized_capability": "SOURCE_REVALIDATION_SUPERSESSION_AND_MATERIALITY_SCHEDULER",
        "validation_failures": list(failures),
        "pr106_acceptance_artifacts_consumed": (
            (repo_root / PR106_ACCEPTANCE_REPORT).exists()
            and any(
                record.get("source_chain_pr106_acceptance_fixture") is True
                for record in accepted_records
            )
        ),
        "pr124_connector_binding_artifacts_consumed": (
            (repo_root / PR124_CONNECTOR_REPORT).exists()
            and any(
                record.get("source_chain_pr124_connector_fixture") is True
                for record in connector_records
            )
        ),
        "revalidation_policy_schema_created": (repo_root / REVALIDATION_POLICY_SCHEMA).exists(),
        "revalidation_schedule_schema_created": (repo_root / REVALIDATION_SCHEDULE_SCHEMA).exists(),
        "revalidation_decision_receipt_schema_created": (
            repo_root / REVALIDATION_DECISION_RECEIPT_SCHEMA
        ).exists(),
        "source_supersession_record_schema_created": (
            repo_root / SOURCE_SUPERSESSION_RECORD_SCHEMA
        ).exists(),
        "source_change_materiality_event_schema_created": (
            repo_root / SOURCE_CHANGE_MATERIALITY_EVENT_SCHEMA
        ).exists(),
        "source_change_impact_snapshot_schema_created": (
            repo_root / SOURCE_CHANGE_IMPACT_SNAPSHOT_SCHEMA
        ).exists(),
        "scheduler_created": (repo_root / Path("src/qtt/source_evidence/revalidation/scheduler.py")).exists(),
        "materiality_classifier_created": (
            repo_root / Path("src/qtt/source_evidence/revalidation/materiality.py")
        ).exists(),
        "supersession_utility_created": (
            repo_root / Path("src/qtt/source_evidence/revalidation/supersession.py")
        ).exists(),
        "source_change_snapshot_generator_created": (
            repo_root / Path("src/qtt/source_evidence/revalidation/snapshot.py")
        ).exists(),
        "validation_cli_created": (
            repo_root / Path("tools/validate_source_revalidation_scheduler.py")
        ).exists(),
        "fixture_accepted_source_record_count": len(accepted_records),
        "fixture_connector_binding_record_count": len(connector_records),
        "fixture_revalidation_event_count": len(event_records),
        "fixture_revalidation_schedule_count": len(schedule_records),
        "fixture_supersession_record_count": len(supersession_records),
        "fixture_materiality_event_count": len(materiality_events),
        "fixture_source_change_snapshot_count": len(snapshots),
        "production_source_revalidation_count": 0,
        "production_source_change_authority_count": 0,
        "fixture_outputs_marked_not_production_source_change_authority": (
            _all_records_marked_fixture_only(supersession_records)
            and _all_records_marked_fixture_only(materiality_events)
            and all(
                snapshot.get("fixture_authority_class")
                == "TEST_FIXTURE_NOT_EXTERNAL_FACT"
                and snapshot.get("production_source_change_authority") is False
                for snapshot in snapshots
            )
        ),
        "deterministic_fixture_time_used": result["deterministic_fixture_time"]
        == DETERMINISTIC_FIXTURE_TIME,
        "live_critical_revalidation_interval": LIVE_CRITICAL_REVALIDATION_INTERVAL,
        "low_risk_revalidation_interval": LOW_RISK_REVALIDATION_INTERVAL,
        "event_triggered_revalidation_latency_class": EVENT_TRIGGERED_REVALIDATION_LATENCY_CLASS,
        "materiality_classes_supported": "_".join(MATERIALITY_CLASSES),
        "unknown_materiality_defaults_connector_blocking": any(
            event.get("unknown_materiality_defaulted_to_connector_blocking") is True
            and event.get("materiality_class") == "CONNECTOR_BLOCKING"
            for event in materiality_events
        ),
        "source_revalidation_runs_in_live_pretrade_path": False,
        "precomputed_source_change_snapshot_created": len(snapshots) == 1,
        "runtime_resolver_snapshot_created_count": 0,
        "runtime_live_authority_created": False,
        "order_authority_created": False,
        "runtime_cash_receipts_created_count": 0,
        "replay_paper_results_created_count": 0,
        "connector_binding_mutation_created_count": 0,
        "accepted_source_ledger_mutation_created_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_simulator_execution_count": 0,
        "optimizer_execution_count": 0,
        "quantum_advantage_claim_created": False,
        "latency_superiority_claim_created": False,
        "execution_superiority_claim_created": False,
        "profit_evidence_created": False,
        "future_official_source_revalidation_path_recorded": True,
        "future_official_source_revalidation_path": list(
            FUTURE_OFFICIAL_SOURCE_REVALIDATION_PATH
        ),
        "production_values_filled_by_later_official_source_prs": True,
        "master_plan_modified": False,
        "atomicrows_bundle_created": False,
        "atomicrows_sha_created": False,
        "run_validation_gates_uses_fresh_pytest_basetemp": _run_validation_gates_uses_fresh_basetemp(repo_root),
        "fixed_tmp_run_validation_gates_pytest_reused": _fixed_tmp_reused(repo_root),
        "network_io_violation_count": (
            1 if _scheduler_source_has_forbidden_io(repo_root) else 0
        )
        + _count_true(schedule_records, "network_io_allowed_flag")
        + _count_true(materiality_events, "network_io_allowed_flag"),
        "source_retrieval_violation_count": _count_true(
            schedule_records,
            "source_retrieval_allowed_flag",
        )
        + _count_true(materiality_events, "source_retrieval_allowed_flag"),
        "source_acceptance_violation_count": _count_true(
            schedule_records,
            "source_acceptance_allowed_flag",
        )
        + _count_true(materiality_events, "source_acceptance_allowed_flag"),
    }


def validate_source_revalidation_scheduler(repo_root: Path) -> tuple[dict[str, Any], list[str]]:
    failures = _validate_schemas(repo_root)
    inputs = load_pr125_fixture_inputs(repo_root)
    accepted_records = inputs["accepted_source_evidence_records"][
        "accepted_source_evidence_records"
    ]
    connector_records = inputs["connector_semantic_binding_records"][
        "connector_semantic_binding_records"
    ]
    event_records = inputs["revalidation_events"]["revalidation_events"]
    result = run_revalidation_scheduler(
        accepted_records,
        connector_records,
        event_records,
        deterministic_fixture_time=DETERMINISTIC_FIXTURE_TIME,
    )
    if result["source_revalidation_schedule_records"] != inputs[
        "expected_revalidation_schedule"
    ]["source_revalidation_schedule_records"]:
        failures.append("PR125 revalidation schedule differs from expected fixture")
    if result["source_supersession_records"] != inputs[
        "expected_supersession_records"
    ]["source_supersession_records"]:
        failures.append("PR125 supersession records differ from expected fixture")
    if result["source_change_materiality_events"] != inputs[
        "expected_materiality_events"
    ]["source_change_materiality_events"]:
        failures.append("PR125 materiality events differ from expected fixture")
    if result["source_change_impact_snapshots"] != inputs[
        "expected_source_change_snapshot"
    ]["source_change_impact_snapshots"]:
        failures.append("PR125 source-change snapshot differs from expected fixture")

    for accepted_record in accepted_records:
        if accepted_record.get("fixture_authority_class") != "TEST_FIXTURE_NOT_EXTERNAL_FACT":
            failures.append("accepted fixture record must be marked TEST_FIXTURE_NOT_EXTERNAL_FACT")
        if accepted_record.get("production_external_fact_authority") is not False:
            failures.append("accepted fixture record must not be production external fact authority")
    for connector_record in connector_records:
        if connector_record.get("production_connector_semantic_authority") is not False:
            failures.append("connector fixture record must not be production connector authority")
    for schedule_record in result["source_revalidation_schedule_records"]:
        for flag in (
            "network_io_allowed_flag",
            "source_retrieval_allowed_flag",
            "source_acceptance_allowed_flag",
            "connector_binding_mutation_allowed_flag",
            "live_pretrade_use_allowed_flag",
            "order_execution_allowed_flag",
            "live_reachability_allowed_flag",
        ):
            if schedule_record.get(flag) is not False:
                failures.append(f"schedule record {flag} must be false")
    report = build_pr125_report(
        repo_root=repo_root,
        inputs=inputs,
        result=result,
        failures=failures,
    )
    return report, failures


def build_report_artifacts(
    repo_root: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    inputs = load_pr125_fixture_inputs(repo_root)
    result = run_revalidation_scheduler(
        inputs["accepted_source_evidence_records"]["accepted_source_evidence_records"],
        inputs["connector_semantic_binding_records"]["connector_semantic_binding_records"],
        inputs["revalidation_events"]["revalidation_events"],
        deterministic_fixture_time=DETERMINISTIC_FIXTURE_TIME,
    )
    pr125_report, failures = validate_source_revalidation_scheduler(repo_root)
    scheduler_report = _build_scheduler_report(result)
    snapshot_report = result["source_change_impact_snapshots"][0]
    return pr125_report, scheduler_report, snapshot_report, failures


__all__ = [
    "FAILURE_MARKER",
    "FUTURE_OFFICIAL_SOURCE_REVALIDATION_PATH",
    "PR125_REPORT_PATH",
    "SCHEDULER_REPORT_PATH",
    "SOURCE_CHANGE_SNAPSHOT_REPORT_PATH",
    "SUCCESS_MARKER",
    "build_pr125_report",
    "build_report_artifacts",
    "validate_source_revalidation_scheduler",
]
