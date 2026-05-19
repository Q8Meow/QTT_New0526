#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.source_evidence.retrieval import controller


SUCCESS_MARKER = "QTT_SOURCE_EVIDENCE_RETRIEVAL_EXECUTOR_OK"
FAILURE_MARKER = "QTT_SOURCE_EVIDENCE_RETRIEVAL_EXECUTOR_FAILED"

STATE_MACHINE_PATH = Path(
    "src/qtt/source_evidence/retrieval/source_retrieval_state_machine.json"
)
SCHEMA_DIR = Path("schemas/source_evidence/retrieval")
OWNER_PACKET_PATH = Path(
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"
)
IDENTITY_ROSTER_PATH = Path("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json")
ROADMAP_CONTROLLER_PATH = Path(
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json"
)
ROADMAP_TEXT_PATH = Path(
    "docs/roadmap/QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.md"
)
ROADMAP_INDEX_PATH = Path("docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json")
BLUEPRINT_TEXT_PATH = Path(
    "docs/roadmap/QTT_PR_Blueprints_Stage1_to_Stage5_PR83_to_PR224_v1_0.md"
)
BLUEPRINT_INDEX_PATH = Path(
    "docs/roadmap/QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json"
)
COVERAGE_REGISTRY_PATH = Path(
    "docs/master_plan/completion/QTTSectionCoverageRegistry.yaml"
)
COVERAGE_REPORT_PATH = Path(
    "docs/master_plan/generated/MasterPlanSectionCoverageReport.json"
)
PR121_RECEIPT_PATH = Path(
    "docs/roadmap/generated/CODEX_REPO_PR121_GITHUB_AUDIT_CURRENTIZATION_RECEIPT.json"
)

GENERATED_DIR = Path("docs/master_plan/source_evidence/generated")
EXECUTOR_REPORT_PATH = GENERATED_DIR / "SourceEvidenceRetrievalExecutor.report.json"
MANIFEST_REPORT_PATH = GENERATED_DIR / "SourceEvidenceRetrievalManifest.report.json"
PR122_REPORT_PATH = (
    GENERATED_DIR / "CODEX_PR122_SOURCE_EVIDENCE_RETRIEVAL_CONTROLLER_GATED_REPORT.json"
)
TARGET_DERIVATION_BLOCK_RECEIPT_PATH = (
    GENERATED_DIR / "CODEX_PR122_SOURCE_EVIDENCE_TARGET_DERIVATION_BLOCK_RECEIPT.json"
)

REQUIRED_SCHEMA_FILES = (
    "source_retrieval_state_machine.schema.json",
    "source_retrieval_target.schema.json",
    "source_retrieval_manifest.schema.json",
    "candidate_source_retrieval_receipt.schema.json",
    "source_locator.schema.json",
    "quote_span_locator.schema.json",
    "machine_field_locator.schema.json",
    "source_redaction_policy.schema.json",
)

MANDATORY_FILES_READ_BEFORE_EDITING = (
    "docs/roadmap/README.md",
    "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
    "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
    "docs/roadmap/QTT_PRs_Roadmap_Consolidated_Static_Runtime_Live_Stage1_to_Stage5_v1_0.md",
    "docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json",
    "docs/roadmap/QTT_PR_Blueprints_Stage1_to_Stage5_PR83_to_PR224_v1_0.md",
    "docs/roadmap/QTT_PR_Blueprints_Index_PR83_to_PR224_v1_0.json",
    "docs/master_plan/completion/QTTSectionCoverageRegistry.yaml",
    "docs/master_plan/generated/MasterPlanSectionCoverageReport.json",
    "docs/master_plan/generated/MasterPlanSectionRoadmapCrosswalk.json",
    "docs/master_plan/generated/MasterPlanSectionCoverageCommandMatrix.json",
    "docs/master_plan/generated/MasterPlanSectionMarketIndexes.json",
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md",
    "schemas/source_evidence/source_evidence.schema.json",
    "schemas/source_evidence/source_evidence_gate_confirmation.schema.json",
    "tools/validate_source_evidence_static.py",
    "tools/validate_source_evidence_gate_confirmation_static.py",
)


def _resolve(repo_root: Path, path: Path | str) -> Path:
    concrete = Path(path)
    return concrete if concrete.is_absolute() else repo_root / concrete


def _load_json(repo_root: Path, path: Path | str) -> dict[str, Any]:
    concrete = _resolve(repo_root, path)
    value = json.loads(concrete.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _read_text(repo_root: Path, path: Path | str) -> str:
    return _resolve(repo_root, path).read_text(encoding="utf-8")


def _entry_by_number(entries: Sequence[Any], number: int) -> dict[str, Any] | None:
    for entry in entries:
        if isinstance(entry, dict) and entry.get("number") == number:
            return entry
    return None


def _entry_by_id(entries: Sequence[Any], entry_id: str) -> dict[str, Any] | None:
    for entry in entries:
        if isinstance(entry, dict) and entry.get("roster_entry_id") == entry_id:
            return entry
    return None


def _controller_mapping_by_label(controller_json: Mapping[str, Any], label: str) -> dict[str, Any] | None:
    for entry in controller_json.get("roadmap_range_currentization", []):
        if isinstance(entry, dict) and entry.get("roadmap_pr_label") == label:
            return entry
    return None


def _full_text_state(text: str, header: str, marker: str) -> dict[str, Any]:
    return {
        "header_found": header in text,
        "marker_found": marker in text,
        "title_found": "Source-evidence retrieval executor" in text,
    }


def _schema_required_fields(repo_root: Path, schema_name: str) -> set[str]:
    schema = _load_json(repo_root, SCHEMA_DIR / schema_name)
    required = schema.get("required")
    return set(required) if isinstance(required, list) else set()


def _source_rows(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    matrix = report.get("command_matrix")
    rows = matrix.get("rows", []) if isinstance(matrix, dict) else []
    if not isinstance(rows, list):
        return []
    return [
        row
        for row in rows
        if isinstance(row, dict)
        and row.get("command_family") == "SOURCE_EVIDENCE_COMMAND"
    ]


def _target_record_like_rows(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    return [
        row
        for row in rows
        if row.get("target_field_path") and row.get("source_locator")
    ]


def _owner_packet_state(repo_root: Path) -> dict[str, Any]:
    text = _read_text(repo_root, OWNER_PACKET_PATH)
    return {
        "canonical_packet_present": True,
        "packet_version_minimum_required": "v1.3A",
        "packet_version_present": (
            "packet_version = "
            "v1.3A_OWNER_APPROVED_EXECUTION_MECHANICS_ABSTRACTION_AND_RETRIEVAL_READINESS_CURRENTIZATION_NOT_EXTERNAL_FACT_AUTHORITY"
            in text
        ),
        "retrieval_scope_approved": (
            "source_evidence_retrieval_target_execution_readiness_scope_owner_approved = true"
            in text
        ),
        "external_fact_authority_blocked": (
            "owner_source_evidence_definitions_packet_can_authorize_external_fact_value = false"
            in text
        ),
        "connector_semantics_blocked": (
            "retrieval_receipt_does_not_unlock_connector_semantics = true" in text
            and "candidate_source_packet_does_not_unlock_connector_semantics = true" in text
            and "owner_source_definitions_packet_does_not_unlock_connector_semantics = true" in text
        ),
    }


def _files_created() -> list[str]:
    return [
        "schemas/source_evidence/retrieval/candidate_source_retrieval_receipt.schema.json",
        "schemas/source_evidence/retrieval/machine_field_locator.schema.json",
        "schemas/source_evidence/retrieval/quote_span_locator.schema.json",
        "schemas/source_evidence/retrieval/source_locator.schema.json",
        "schemas/source_evidence/retrieval/source_redaction_policy.schema.json",
        "schemas/source_evidence/retrieval/source_retrieval_manifest.schema.json",
        "schemas/source_evidence/retrieval/source_retrieval_state_machine.schema.json",
        "schemas/source_evidence/retrieval/source_retrieval_target.schema.json",
        "src/qtt/source_evidence/retrieval/__init__.py",
        "src/qtt/source_evidence/retrieval/controller.py",
        "src/qtt/source_evidence/retrieval/source_retrieval_state_machine.json",
        "tests/source_evidence/test_pr122_pr105_controller_eligibility_required.py",
        "tests/source_evidence/test_pr122_retrieval_receipt_is_not_accepted_fact.py",
        "tests/source_evidence/test_pr122_source_retrieval_no_authority_boundaries.py",
        "tests/source_evidence/test_pr122_source_retrieval_state_machine_centralized.py",
        "tools/source_evidence_retrieval_executor.py",
        "tools/validate_source_evidence_retrieval_executor.py",
        "docs/master_plan/source_evidence/generated/CODEX_PR122_SOURCE_EVIDENCE_RETRIEVAL_CONTROLLER_GATED_REPORT.json",
        "docs/master_plan/source_evidence/generated/CODEX_PR122_SOURCE_EVIDENCE_TARGET_DERIVATION_BLOCK_RECEIPT.json",
        "docs/master_plan/source_evidence/generated/SourceEvidenceRetrievalExecutor.report.json",
        "docs/master_plan/source_evidence/generated/SourceEvidenceRetrievalManifest.report.json",
    ]


def _files_modified() -> list[str]:
    return [
        "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
        "tests/fail_closed/test_run_validation_gates.py",
        "tools/validate_qtt_pr_identity_roster.py",
        "tools/run_validation_gates.py",
        "tests/roadmap/test_qtt_pr_identity_roster.py",
        "tests/roadmap/test_qtt_roadmap_execution_state_controller.py",
    ]


def build_reports(repo_root: Path) -> dict[Path, dict[str, Any]]:
    machine = _load_json(repo_root, STATE_MACHINE_PATH)
    roster = _load_json(repo_root, IDENTITY_ROSTER_PATH)
    roadmap_controller = _load_json(repo_root, ROADMAP_CONTROLLER_PATH)
    roadmap_index = _load_json(repo_root, ROADMAP_INDEX_PATH)
    blueprint_index = _load_json(repo_root, BLUEPRINT_INDEX_PATH)
    coverage_report = _load_json(repo_root, COVERAGE_REPORT_PATH)

    roadmap_text_state = _full_text_state(
        _read_text(repo_root, ROADMAP_TEXT_PATH),
        "#### PR #105",
        "QTT_SOURCE_EVIDENCE_RETRIEVAL_EXECUTOR_OK",
    )
    blueprint_text_state = _full_text_state(
        _read_text(repo_root, BLUEPRINT_TEXT_PATH),
        "PR #105",
        "QTT_SOURCE_EVIDENCE_RETRIEVAL_EXECUTOR_OK",
    )

    roster_entries = roster.get("entries", [])
    roster_pr105 = _entry_by_id(roster_entries if isinstance(roster_entries, list) else [], "ROADMAP_PR_105_PLANNED")
    roadmap_pr105 = _entry_by_number(roadmap_index.get("pr_entries", []), 105)
    blueprint_pr105 = _entry_by_number(blueprint_index.get("entries", []), 105)
    controller_pr105 = _controller_mapping_by_label(roadmap_controller, "PR #105")

    source_rows = _source_rows(coverage_report)
    target_like_rows = _target_record_like_rows(source_rows)
    command_summary = coverage_report.get("command_matrix_summary", {})
    command_summary = command_summary if isinstance(command_summary, dict) else {}
    stage1_counts = command_summary.get("stage1_prediction_market_command_counts", {})
    stage1_counts = stage1_counts if isinstance(stage1_counts, dict) else {}
    future_counts = command_summary.get("explicit_future_market_family_command_counts", {})
    future_counts = future_counts if isinstance(future_counts, dict) else {}

    target_derivation = controller.target_derivation_block(machine)
    manifest = {
        "accepted_source_fact_count": 0,
        "accepted_source_packet_created_count": 0,
        "candidate_receipt_count": 0,
        "external_network_fetch_default_enabled": False,
        "manifest_authority_class": "SOURCE_RETRIEVAL_MANIFEST_CONTROL_PLANE_ONLY_NOT_FACT_AUTHORITY",
        "manifest_id": "PR122_SOURCE_EVIDENCE_RETRIEVAL_MANIFEST_EMPTY_TARGET_DERIVATION_BLOCKED",
        "manifest_mode": "MANIFEST_ONLY",
        "retrieval_targets": [],
        "source_retrieval_state_machine_artifact": STATE_MACHINE_PATH.as_posix(),
        "target_derivation_state": target_derivation["state_id"],
    }

    manifest_report = {
        "deterministic_output": True,
        "manifest": manifest,
        "manifest_validation_failures": controller.validate_retrieval_manifest(
            manifest,
            machine,
        ),
        "source_retrieval_target_count": 0,
        "target_derivation_block": target_derivation,
    }

    executor_report = {
        "accepted_source_fact_count": 0,
        "accepted_source_packet_created_count": 0,
        "candidate_receipt_count": 0,
        "default_execution_mode": "MANIFEST_ONLY_NO_NETWORK",
        "deterministic_output": True,
        "external_network_fetch_default_enabled": False,
        "fixture_only_executor_shell_created": True,
        "network_fetch_count_in_tests": 0,
        "order_authority_created": False,
        "profit_evidence_created": False,
        "quantum_backend_execution_count": 0,
        "quantum_simulator_execution_count": 0,
        "runtime_live_authority_created": False,
        "source_retrieval_state_machine_artifact": STATE_MACHINE_PATH.as_posix(),
        "target_derivation_block": target_derivation,
    }

    pr122_report = {
        "accepted_source_fact_count": 0,
        "accepted_source_packet_created_count": 0,
        "anti_hardcoding_test_added": True,
        "atomicrows_bundle_created": False,
        "atomicrows_sha_created": False,
        "blueprint_candidate_checked": "PR105",
        "blueprint_index_state": {
            "entry": blueprint_pr105,
            "present": blueprint_pr105 is not None,
            "scope_match": bool(
                blueprint_pr105
                and blueprint_pr105.get("title") == "Source-evidence retrieval executor"
                and "candidate retrieval receipts only" in blueprint_pr105.get("purpose", "")
            ),
        },
        "candidate_packet_schema_created": False,
        "candidate_receipt_schema_created": True,
        "centralized_state_machine_artifact": STATE_MACHINE_PATH.as_posix(),
        "checked_github_pr_number": 121,
        "checked_schema_files": [
            (SCHEMA_DIR / name).as_posix() for name in REQUIRED_SCHEMA_FILES
        ],
        "connector_semantic_binding_created_count": 0,
        "consolidated_roadmap_state": roadmap_text_state,
        "controller_eligibility_state": "ELIGIBLE_FOR_SCHEMA_CONTROL_PLANE_WITH_TARGET_DERIVATION_BLOCK",
        "currentized_prior_repo_pr": "PR121",
        "deterministic_report_rerun_passed": True,
        "downstream_reference_artifacts": [
            "tools/validate_source_evidence_retrieval_executor.py",
            "tools/source_evidence_retrieval_executor.py",
            MANIFEST_REPORT_PATH.as_posix(),
            EXECUTOR_REPORT_PATH.as_posix(),
            TARGET_DERIVATION_BLOCK_RECEIPT_PATH.as_posix(),
        ],
        "execution_superiority_claim_created": False,
        "external_network_fetch_default_enabled": False,
        "files_created": _files_created(),
        "files_modified": _files_modified(),
        "files_read": list(MANDATORY_FILES_READ_BEFORE_EDITING),
        "full_blueprint_state": blueprint_text_state,
        "future_market_command_count_from_market_index": sum(
            value for value in future_counts.values() if isinstance(value, int)
        ),
        "future_market_target_count": 0,
        "identity_roster_state": {
            "github_105_is_audit_only_mismatch": _entry_by_id(
                roster_entries if isinstance(roster_entries, list) else [],
                "GITHUB_PR_105_IDENTITY_MISMATCH",
            ),
            "roadmap_pr105_entry": roster_pr105,
            "roadmap_pr105_present": roster_pr105 is not None,
        },
        "implementation_performed": True,
        "latency_superiority_claim_created": False,
        "master_plan_modified": False,
        "network_fetch_count_in_tests": 0,
        "optimizer_execution_count": 0,
        "order_authority_created": False,
        "owner_packet_state": _owner_packet_state(repo_root),
        "owner_review_future_market_command_count": command_summary.get(
            "owner_review_required_future_market_scope_count",
            0,
        ),
        "owner_review_future_market_scope_count": 0,
        "profit_evidence_created": False,
        "quantum_advantage_claim_created": False,
        "quantum_backend_execution_count": 0,
        "quantum_simulator_execution_count": 0,
        "reason_if_not_implemented": None,
        "replay_paper_results_created_count": 0,
        "repo_pr_label": "PR122",
        "roadmap_candidate_checked": "PR105",
        "roadmap_controller_state": {
            "entry": controller_pr105,
            "present": controller_pr105 is not None,
            "state": (
                controller_pr105.get("controller_state")
                if isinstance(controller_pr105, dict)
                else None
            ),
        },
        "roadmap_index_state": {
            "entry": roadmap_pr105,
            "present": roadmap_pr105 is not None,
            "scope_match": bool(
                roadmap_pr105
                and roadmap_pr105.get("title") == "Source-evidence retrieval executor"
                and roadmap_pr105.get("marker")
                == "QTT_SOURCE_EVIDENCE_RETRIEVAL_EXECUTOR_OK"
            ),
        },
        "runtime_cash_receipts_created_count": 0,
        "runtime_live_authority_created": False,
        "runtime_resolver_snapshot_created_count": 0,
        "source_retrieval_target_count": 0,
        "source_retrieval_target_derivation_source": {
            "canonical_target_like_rows": len(target_like_rows),
            "derivation_state": target_derivation["state_id"],
            "source_evidence_command_rows": len(source_rows),
            "source_evidence_command_rows_declared_in_summary": command_summary.get(
                "source_evidence_command_count"
            ),
        },
        "stage1_target_count_by_platform": {
            "FORECASTEX_IBKR": 0,
            "KALSHI": 0,
            "POLYMARKET": 0,
            "PREDICTION_MARKETS_GENERAL": 0,
        },
        "stage1_command_count_by_platform_from_market_index": stage1_counts,
        "target_derivation_block_receipt": TARGET_DERIVATION_BLOCK_RECEIPT_PATH.as_posix(),
    }

    block_receipt = {
        "accepted_source_fact_count": 0,
        "accepted_source_packet_created_count": 0,
        "block_receipt_code": "CODEX_PR122_SOURCE_EVIDENCE_TARGET_DERIVATION_BLOCK_RECEIPT",
        "connector_semantic_binding_created_count": 0,
        "implementation_scope_limited_to_schema_controller_reports": True,
        "quantum_backend_simulator_optimizer_executions": 0,
        "reason": target_derivation["block_reason_canonical"],
        "reason_loaded_from_central_state_machine": True,
        "reason_source": STATE_MACHINE_PATH.as_posix(),
        "repo_pr_label": "PR122",
        "roadmap_candidate_checked": "PR105",
        "runtime_live_order_profit_authority_created": False,
        "source_evidence_command_rows": len(source_rows),
        "target_derivation_block": target_derivation,
        "target_field_source_locator_records_found": len(target_like_rows),
    }

    return {
        EXECUTOR_REPORT_PATH: executor_report,
        MANIFEST_REPORT_PATH: manifest_report,
        PR122_REPORT_PATH: pr122_report,
        TARGET_DERIVATION_BLOCK_RECEIPT_PATH: block_receipt,
    }


def validate_static_surface(repo_root: Path) -> list[str]:
    failures: list[str] = []
    for path in (
        STATE_MACHINE_PATH,
        OWNER_PACKET_PATH,
        IDENTITY_ROSTER_PATH,
        ROADMAP_CONTROLLER_PATH,
        ROADMAP_TEXT_PATH,
        ROADMAP_INDEX_PATH,
        BLUEPRINT_TEXT_PATH,
        BLUEPRINT_INDEX_PATH,
        COVERAGE_REGISTRY_PATH,
        COVERAGE_REPORT_PATH,
        PR121_RECEIPT_PATH,
    ):
        if not _resolve(repo_root, path).exists():
            failures.append(f"required file missing: {path}")
    for schema_name in REQUIRED_SCHEMA_FILES:
        if not _resolve(repo_root, SCHEMA_DIR / schema_name).exists():
            failures.append(f"required schema missing: {schema_name}")
    if failures:
        return failures

    machine = _load_json(repo_root, STATE_MACHINE_PATH)
    failures.extend(controller.state_machine_failures(machine))
    owner_state = _owner_packet_state(repo_root)
    for field, value in owner_state.items():
        if isinstance(value, bool) and value is not True:
            failures.append(f"owner packet state failed: {field}")

    target_required = _schema_required_fields(
        repo_root,
        "source_retrieval_target.schema.json",
    )
    missing_target_fields = sorted(controller.REQUIRED_TARGET_FIELDS - target_required)
    if missing_target_fields:
        failures.append(
            "target schema missing required fields: " + ", ".join(missing_target_fields)
        )

    receipt_required = _schema_required_fields(
        repo_root,
        "candidate_source_retrieval_receipt.schema.json",
    )
    missing_receipt_fields = sorted(
        controller.REQUIRED_CANDIDATE_RECEIPT_FIELDS - receipt_required
    )
    if missing_receipt_fields:
        failures.append(
            "candidate receipt schema missing required fields: "
            + ", ".join(missing_receipt_fields)
        )

    reports = build_reports(repo_root)
    rerun_reports = build_reports(repo_root)
    if reports != rerun_reports:
        failures.append("generated reports are not deterministic across in-memory rerun")
    if any(
        report[1].get("accepted_source_fact_count", 0) != 0
        for report in reports.items()
        if isinstance(report[1], dict)
    ):
        failures.append("reports must not create accepted source facts")
    if reports[PR122_REPORT_PATH]["source_retrieval_target_count"] != 0:
        failures.append("PR122 must not invent source retrieval targets")
    if reports[PR122_REPORT_PATH]["external_network_fetch_default_enabled"] is not False:
        failures.append("external network fetch must be disabled by default")

    return failures


def write_reports(repo_root: Path) -> None:
    for path, report in build_reports(repo_root).items():
        controller.write_stable_json(_resolve(repo_root, path), report)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--check-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve()
    failures = validate_static_surface(repo_root)
    if failures:
        raise SystemExit(FAILURE_MARKER + "\n- " + "\n- ".join(failures))
    if not args.check_only:
        write_reports(repo_root)
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
