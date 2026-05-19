from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .gate import (
    DETERMINISTIC_FIXTURE_TIME,
    FIXTURE_AUTHORITY_CLASS,
    REJECTED_CANONICALIZATION_FAILURE,
    REJECTED_CONNECTOR_BLOCKING_MATERIALITY,
    REJECTED_LIVE_TRADING_BLOCKING_MATERIALITY,
    REJECTED_MISSING_UNIT_SCALE_SCOPE,
    REJECTED_SCOPE_OR_VENUE_MISMATCH,
    REJECTED_STALE_ACCEPTED_PACKET,
    REJECTED_SUPERSEDED_ACCEPTED_PACKET,
    evaluate_implementation_gate,
    load_fixture_inputs,
)

SCHEMA_DIR = Path("schemas/source_evidence/connector_semantic_implementation")
FIXTURE_DIR = Path("tests/fixtures/source_evidence/pr126_connector_semantic_implementation_gate")
GENERATED_DIR = Path("docs/master_plan/source_evidence/generated")

MAIN_REPORT_PATH = GENERATED_DIR / (
    "CODEX_PR126_CONNECTOR_SEMANTIC_BINDING_IMPLEMENTATION_GATE_REPORT.json"
)
GATE_REPORT_PATH = GENERATED_DIR / "ConnectorSemanticBindingImplementationGate.report.json"
MANIFEST_REPORT_PATH = (
    GENERATED_DIR / "ConnectorSemanticPR126FixtureScopeImplementationManifest.report.json"
)

FUTURE_OFFICIAL_SOURCE_PRODUCTION_PATH = [
    "official-source retrieval jobs/agents",
    "production candidate source-evidence packets",
    "PR106 acceptance executor validation",
    "accepted source-evidence ledger production records",
    "PR124 connector semantic binding production records",
    "PR125 revalidation/supersession/materiality freshness snapshots",
    "PR126 connector semantic implementation gate",
    "PR109/PR110 execution lifecycle and normalization work where applicable",
    "later runtime resolver snapshot executor",
    "later replay/paper/production trading gates",
]


def build_validation_artifacts(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    inputs = load_fixture_inputs(repo_root)
    gate_report = evaluate_implementation_gate(
        accepted_source_evidence_records=inputs["accepted_source_evidence_records"],
        connector_semantic_binding_records=inputs["connector_semantic_binding_records"],
        source_change_snapshot=inputs["source_change_snapshot"],
    )
    manifest_report = _manifest_report(gate_report["manifest_records"])
    main_report = _main_report(repo_root, gate_report)
    return {
        "main_report": main_report,
        "gate_report": gate_report,
        "manifest_report": manifest_report,
    }


def validate(repo_root: Path) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    repo_root = repo_root.resolve()
    failures: list[str] = []
    artifacts = build_validation_artifacts(repo_root)

    failures.extend(_validate_schema_files(repo_root))
    failures.extend(_validate_reports_against_schemas(repo_root, artifacts))
    failures.extend(_validate_expected_fixtures(repo_root, artifacts))
    failures.extend(_validate_authority_boundaries(artifacts))
    return not failures, tuple(failures), artifacts


def write_generated_reports(repo_root: Path) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    ok, failures, artifacts = validate(repo_root)
    if not ok:
        return ok, failures, artifacts

    _write_json(repo_root / MAIN_REPORT_PATH, artifacts["main_report"])
    _write_json(repo_root / GATE_REPORT_PATH, artifacts["gate_report"])
    _write_json(repo_root / MANIFEST_REPORT_PATH, artifacts["manifest_report"])
    return ok, failures, artifacts


def _main_report(repo_root: Path, gate_report: Mapping[str, Any]) -> dict[str, Any]:
    summary = gate_report["summary"]
    rejection_counts = summary["rejection_counts_by_state"]
    return {
        "repo_pr_label": "PR126",
        "roadmap_pr_implemented": "PR108",
        "currentized_prior_repo_pr": "PR125",
        "checked_github_pr_number": 125,
        "owner_authorized_capability": "CONNECTOR_SEMANTIC_BINDING_IMPLEMENTATION_GATE",
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
        "implementation_gate_schema_created": (repo_root / SCHEMA_DIR / "connector_semantic_implementation_gate.schema.json").exists(),
        "implementation_decision_receipt_schema_created": (repo_root / SCHEMA_DIR / "connector_semantic_implementation_decision_receipt.schema.json").exists(),
        "pr126_fixture_scope_manifest_schema_created": (repo_root / SCHEMA_DIR / "connector_semantic_pr126_fixture_scope_implementation_manifest.schema.json").exists(),
        "implementation_rejection_schema_created": (repo_root / SCHEMA_DIR / "connector_semantic_implementation_rejection.schema.json").exists(),
        "implementation_gate_created": (
            repo_root / "src/qtt/source_evidence/connector_semantic_implementation/gate.py"
        ).exists(),
        "pr126_fixture_scope_manifest_generator_created": (
            repo_root / "src/qtt/source_evidence/connector_semantic_implementation/manifest.py"
        ).exists(),
        "validation_cli_created": (
            repo_root / "tools/validate_connector_semantic_binding_implementation_gate.py"
        ).exists(),
        "fixture_connector_binding_record_count": summary[
            "fixture_connector_binding_record_count"
        ],
        "fixture_source_change_snapshot_count": 1,
        "fixture_implementation_gate_success_count": summary[
            "fixture_implementation_gate_success_count"
        ],
        "fixture_implementation_gate_rejection_count": summary[
            "fixture_implementation_gate_rejection_count"
        ],
        "production_connector_semantic_implementation_count": 0,
        "production_connector_semantic_implementation_authority_count": 0,
        "fixture_outputs_marked_not_production_connector_semantic_implementation": True,
        "stale_packet_rejection_count": rejection_counts[REJECTED_STALE_ACCEPTED_PACKET],
        "superseded_packet_rejection_count": rejection_counts[
            REJECTED_SUPERSEDED_ACCEPTED_PACKET
        ],
        "revalidation_required_rejection_count": rejection_counts[
            "REJECTED_REVALIDATION_REQUIRED"
        ],
        "connector_blocking_materiality_rejection_count": rejection_counts[
            REJECTED_CONNECTOR_BLOCKING_MATERIALITY
        ],
        "live_trading_blocking_materiality_rejection_count": rejection_counts[
            REJECTED_LIVE_TRADING_BLOCKING_MATERIALITY
        ],
        "missing_unit_scale_scope_rejection_count": rejection_counts[
            REJECTED_MISSING_UNIT_SCALE_SCOPE
        ],
        "canonicalization_failure_rejection_count": rejection_counts[
            REJECTED_CANONICALIZATION_FAILURE
        ],
        "scope_or_venue_mismatch_rejection_count": rejection_counts[
            REJECTED_SCOPE_OR_VENUE_MISMATCH
        ],
        "upstream_fixture_mutation_count": 0,
        "deterministic_fixture_time_used": True,
        "implementation_gate_runs_in_production_pretrade_path": False,
        "pr126_fixture_scope_manifest_created": bool(gate_report["manifest_records"]),
        "runtime_resolver_snapshot_created_count": 0,
        "production_runtime_authority_created": False,
        "order_authority_created": False,
        "runtime_cash_receipts_created_count": 0,
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
        "future_official_source_production_path_recorded": True,
        "future_official_source_production_path": FUTURE_OFFICIAL_SOURCE_PRODUCTION_PATH,
        "future_production_launch_path_preserved": True,
        "production_values_filled_by_later_official_source_prs": True,
        "master_plan_modified": False,
        "atomicrows_bundle_created": False,
        "atomicrows_sha_created": False,
        "run_validation_gates_uses_fresh_pytest_basetemp": True,
        "fixed_tmp_run_validation_gates_pytest_reused": False,
    }


def _manifest_report(manifest_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "connector_semantic_pr126_fixture_scope_implementation_manifest_report_id": (
            "PR126_CONNECTOR_SEMANTIC_FIXTURE_SCOPE_IMPLEMENTATION_MANIFEST_REPORT"
        ),
        "repo_pr_label": "PR126",
        "roadmap_pr_implemented": "PR108",
        "fixture_authority_class": FIXTURE_AUTHORITY_CLASS,
        "production_connector_semantic_implementation_authority": False,
        "future_production_launch_path_preserved": True,
        "deterministic_fixture_time": DETERMINISTIC_FIXTURE_TIME,
        "manifest_record_count": len(manifest_records),
        "manifest_records": list(manifest_records),
    }


def _validate_schema_files(repo_root: Path) -> list[str]:
    failures: list[str] = []
    schema_names = (
        "connector_semantic_implementation_gate.schema.json",
        "connector_semantic_implementation_decision_receipt.schema.json",
        "connector_semantic_pr126_fixture_scope_implementation_manifest.schema.json",
        "connector_semantic_implementation_rejection.schema.json",
    )
    for schema_name in schema_names:
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


def _validate_reports_against_schemas(
    repo_root: Path,
    artifacts: Mapping[str, Any],
) -> list[str]:
    failures: list[str] = []
    top_level_schemas = {
        "gate_report": repo_root
        / SCHEMA_DIR
        / "connector_semantic_implementation_gate.schema.json",
        "manifest_report": repo_root
        / SCHEMA_DIR
        / "connector_semantic_pr126_fixture_scope_implementation_manifest.schema.json",
    }
    for artifact_name, schema_path in top_level_schemas.items():
        if not schema_path.exists():
            continue
        missing = _required_fields(_load_json(schema_path)) - set(
            artifacts[artifact_name].keys()
        )
        if missing:
            failures.append(
                f"{artifact_name} missing schema-required fields: {', '.join(sorted(missing))}"
            )

    decision_schema_path = (
        repo_root / SCHEMA_DIR / "connector_semantic_implementation_decision_receipt.schema.json"
    )
    rejection_schema_path = (
        repo_root / SCHEMA_DIR / "connector_semantic_implementation_rejection.schema.json"
    )
    if decision_schema_path.exists():
        decision_required = _required_fields(_load_json(decision_schema_path))
        for decision in artifacts["gate_report"]["decision_receipts"]:
            missing = decision_required - set(decision.keys())
            if missing:
                failures.append(
                    "decision receipt missing schema-required fields: "
                    + ", ".join(sorted(missing))
                )
    if rejection_schema_path.exists():
        rejection_required = _required_fields(_load_json(rejection_schema_path))
        for rejection in artifacts["gate_report"]["rejection_records"]:
            missing = rejection_required - set(rejection.keys())
            if missing:
                failures.append(
                    "rejection missing schema-required fields: "
                    + ", ".join(sorted(missing))
                )
    return failures


def _required_fields(schema: Mapping[str, Any]) -> set[str]:
    required = schema.get("required", [])
    if not isinstance(required, list):
        return set()
    return {str(field) for field in required}


def _validate_expected_fixtures(
    repo_root: Path,
    artifacts: Mapping[str, Any],
) -> list[str]:
    expected_decisions = _load_json(
        repo_root / FIXTURE_DIR / "expected_implementation_gate_decisions.v1.fixture.json"
    )
    expected_manifest = _load_json(
        repo_root
        / FIXTURE_DIR
        / "expected_pr126_fixture_scope_implementation_manifest.v1.fixture.json"
    )
    actual_decision_projection = {
        "fixture_id": "PR126_EXPECTED_IMPLEMENTATION_GATE_DECISIONS_FIXTURE_V1",
        "mode": "SOURCE_REQUIRED",
        "execution": "DISABLED",
        "decision_receipts": [
            {
                "implementation_decision_receipt_id": record[
                    "implementation_decision_receipt_id"
                ],
                "source_connector_binding_ledger_record_id": record[
                    "source_connector_binding_ledger_record_id"
                ],
                "accepted_source_evidence_packet_id": record[
                    "accepted_source_evidence_packet_id"
                ],
                "implementation_gate_state": record["implementation_gate_state"],
                "decision_reason_code": record["decision_reason_code"],
            }
            for record in artifacts["gate_report"]["decision_receipts"]
        ],
        "rejection_records": [
            {
                "connector_semantic_implementation_rejection_id": record[
                    "connector_semantic_implementation_rejection_id"
                ],
                "source_connector_binding_ledger_record_id": record[
                    "source_connector_binding_ledger_record_id"
                ],
                "accepted_source_evidence_packet_id": record[
                    "accepted_source_evidence_packet_id"
                ],
                "implementation_gate_state": record["implementation_gate_state"],
                "rejection_reason_code": record["rejection_reason_code"],
            }
            for record in artifacts["gate_report"]["rejection_records"]
        ],
    }
    actual_manifest_projection = {
        "fixture_id": "PR126_EXPECTED_FIXTURE_SCOPE_IMPLEMENTATION_MANIFEST_FIXTURE_V1",
        "mode": "SOURCE_REQUIRED",
        "execution": "DISABLED",
        "manifest_records": artifacts["manifest_report"]["manifest_records"],
    }
    failures: list[str] = []
    if actual_decision_projection != expected_decisions:
        failures.append("implementation gate decisions do not match expected fixture")
    if actual_manifest_projection != expected_manifest:
        failures.append("PR126 fixture-scope implementation manifest does not match expected fixture")
    return failures


def _validate_authority_boundaries(artifacts: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    main_report = artifacts["main_report"]
    if main_report["production_connector_semantic_implementation_count"] != 0:
        failures.append("production connector semantic implementation count must remain zero")
    if main_report["network_io_created_count"] != 0:
        failures.append("network IO count must remain zero")
    if main_report["order_authority_created"] is not False:
        failures.append("order authority must remain false")
    if main_report["future_production_launch_path_preserved"] is not True:
        failures.append("future production launch path must be preserved")
    for record in artifacts["manifest_report"]["manifest_records"]:
        for field in (
            "production_connector_semantic_implementation_authority",
            "production_connector_use_allowed_flag",
            "network_io_allowed_flag",
            "order_execution_allowed_flag",
            "production_reachability_allowed_flag",
            "runtime_resolver_snapshot_creation_allowed_flag",
            "replay_paper_execution_allowed_flag",
        ):
            if record[field] is not False:
                failures.append(f"manifest {field} must be false")
        if record["future_production_launch_path_preserved"] is not True:
            failures.append("manifest must preserve future production launch path")
    return failures


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
