#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.source_evidence.acceptance import validator as acceptance


SUCCESS_MARKER = "QTT_ACCEPTED_SOURCE_EVIDENCE_ACCEPTANCE_EXECUTOR_AND_LEDGER_OK"
FAILURE_MARKER = "QTT_ACCEPTED_SOURCE_EVIDENCE_ACCEPTANCE_EXECUTOR_AND_LEDGER_FAILED"

SCHEMA_DIR = Path("schemas/source_evidence/acceptance")
FIXTURE_PATH = Path(
    "tests/fixtures/source_evidence/pr106_evidence_executor/pr123_candidate_packets.v1.fixture.json"
)
GENERATED_DIR = Path("docs/master_plan/source_evidence/generated")
PR123_REPORT_PATH = (
    GENERATED_DIR / "CODEX_PR123_ACCEPTED_SOURCE_EVIDENCE_ACCEPTANCE_EXECUTOR_LEDGER_REPORT.json"
)
EXECUTOR_REPORT_PATH = GENERATED_DIR / "AcceptedSourceEvidenceAcceptanceExecutor.report.json"
LEDGER_REPORT_PATH = GENERATED_DIR / "AcceptedSourceEvidenceLedger.report.json"
OWNER_AUTH_RECEIPT_PATH = (
    Path("docs/roadmap/generated")
    / "CODEX_PR123_OWNER_AUTHORIZED_PR106_IMPLEMENTATION_RECEIPT.json"
)
PR122_AUDIT_RECEIPT_PATH = (
    Path("docs/roadmap/generated")
    / "CODEX_REPO_PR122_GITHUB_AUDIT_CURRENTIZATION_RECEIPT.json"
)

REQUIRED_SCHEMA_FILES = (
    "accepted_source_evidence_packet.schema.json",
    "accepted_source_evidence_ledger.schema.json",
    "acceptance_executor_input.schema.json",
    "acceptance_decision_receipt.schema.json",
    "source_acceptance_conflict_report.schema.json",
    "source_revalidation_status.schema.json",
    "source_acceptance_reject_receipt.schema.json",
)

REQUIRED_REPORT_FIELDS = {
    "repo_pr_label",
    "roadmap_pr_implemented",
    "blueprint_pr_implemented",
    "owner_authorized_pr106",
    "currentized_prior_repo_pr",
    "checked_github_pr_number",
    "acceptance_executor_created",
    "accepted_packet_schema_created",
    "accepted_ledger_schema_created",
    "acceptance_decision_receipt_schema_created",
    "conflict_report_schema_created",
    "revalidation_status_schema_created",
    "acceptance_validator_created",
    "accepted_ledger_validator_created",
    "deterministic_acceptance_report_created",
    "fixture_candidate_packet_count",
    "fixture_acceptance_success_count",
    "fixture_rejection_case_count",
    "production_candidate_packet_count",
    "production_accepted_source_fact_count",
    "production_accepted_source_packet_count",
    "production_accepted_ledger_record_count",
    "fixture_outputs_marked_not_external_fact",
    "target_field_scope_validation_enabled",
    "quote_span_or_machine_field_locator_validation_enabled",
    "digest_validation_enabled",
    "source_class_validation_enabled",
    "conflict_validation_enabled",
    "revalidation_validation_enabled",
    "private_doc_access_rights_validation_enabled",
    "secret_redaction_validation_enabled",
    "connector_semantic_binding_created_count",
    "runtime_resolver_snapshot_created_count",
    "runtime_live_authority_created",
    "order_authority_created",
    "runtime_cash_receipts_created_count",
    "replay_paper_results_created_count",
    "quantum_backend_execution_count",
    "quantum_simulator_execution_count",
    "optimizer_execution_count",
    "quantum_advantage_claim_created",
    "latency_superiority_claim_created",
    "execution_superiority_claim_created",
    "profit_evidence_created",
    "master_plan_modified",
    "atomicrows_bundle_created",
    "atomicrows_sha_created",
    "run_validation_gates_uses_fresh_pytest_basetemp",
    "fixed_tmp_run_validation_gates_pytest_reused",
}


def _resolve(repo_root: Path, path: Path | str) -> Path:
    concrete = Path(path)
    return concrete if concrete.is_absolute() else repo_root / concrete


def _load_json(repo_root: Path, path: Path | str) -> dict[str, Any]:
    concrete = _resolve(repo_root, path)
    value = json.loads(concrete.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _fixture(repo_root: Path) -> dict[str, Any]:
    return _load_json(repo_root, FIXTURE_PATH)


def _base_fixture_candidate(repo_root: Path) -> dict[str, Any]:
    fixture = _fixture(repo_root)
    packets = fixture.get("candidate_source_evidence_packets", [])
    if not isinstance(packets, list) or not packets:
        raise ValueError("PR123 fixture must contain candidate_source_evidence_packets")
    packet = packets[0]
    if not isinstance(packet, dict):
        raise ValueError("PR123 fixture candidate must be an object")
    return packet


def _set_nested_or_field(record: dict[str, Any], field: str, value: Any) -> None:
    record[field] = value


def rejection_case_candidate(base: Mapping[str, Any], case: Mapping[str, Any]) -> dict[str, Any]:
    candidate = copy.deepcopy(dict(base))
    for field in case.get("remove_fields", []):
        candidate.pop(field, None)
    set_fields = case.get("set_fields", {})
    if isinstance(set_fields, Mapping):
        for field, value in set_fields.items():
            _set_nested_or_field(candidate, field, value)
    candidate["candidate_source_evidence_packet_id"] = (
        f"{base['candidate_source_evidence_packet_id']}_{case['case_id']}"
    )
    return candidate


def fixture_execution_results(repo_root: Path) -> list[dict[str, Any]]:
    fixture = _fixture(repo_root)
    base = _base_fixture_candidate(repo_root)
    results: list[dict[str, Any]] = []
    valid_result = acceptance.build_acceptance_artifacts(base)
    results.append(
        {
            "case_id": "VALID_ACCEPTANCE",
            "expected_decision": "ACCEPTED",
            "result": valid_result,
        }
    )
    for case in fixture.get("rejection_mutation_cases", []):
        if not isinstance(case, Mapping):
            continue
        result = acceptance.build_acceptance_artifacts(
            rejection_case_candidate(base, case)
        )
        results.append(
            {
                "case_id": case["case_id"],
                "expected_decision": "REJECTED",
                "expected_rejection_code": case["expected_rejection_code"],
                "result": result,
            }
        )
    return results


def _schema_required_fields(repo_root: Path, schema_name: str) -> set[str]:
    schema = _load_json(repo_root, SCHEMA_DIR / schema_name)
    required = schema.get("required")
    return set(required) if isinstance(required, list) else set()


def _artifact_flags(repo_root: Path) -> dict[str, bool]:
    return {
        "acceptance_executor_created": _resolve(
            repo_root, "tools/source_evidence_acceptance_executor.py"
        ).exists(),
        "accepted_packet_schema_created": _resolve(
            repo_root, SCHEMA_DIR / "accepted_source_evidence_packet.schema.json"
        ).exists(),
        "accepted_ledger_schema_created": _resolve(
            repo_root, SCHEMA_DIR / "accepted_source_evidence_ledger.schema.json"
        ).exists(),
        "acceptance_decision_receipt_schema_created": _resolve(
            repo_root, SCHEMA_DIR / "acceptance_decision_receipt.schema.json"
        ).exists(),
        "conflict_report_schema_created": _resolve(
            repo_root, SCHEMA_DIR / "source_acceptance_conflict_report.schema.json"
        ).exists(),
        "revalidation_status_schema_created": _resolve(
            repo_root, SCHEMA_DIR / "source_revalidation_status.schema.json"
        ).exists(),
        "acceptance_validator_created": _resolve(
            repo_root, "tools/validate_source_evidence_acceptance.py"
        ).exists(),
        "accepted_ledger_validator_created": _resolve(
            repo_root, "src/qtt/source_evidence/acceptance/ledger.py"
        ).exists(),
        "deterministic_acceptance_report_created": True,
    }


def build_reports(repo_root: Path) -> dict[Path, dict[str, Any]]:
    fixture = _fixture(repo_root)
    results = fixture_execution_results(repo_root)
    accepted_results = [
        item for item in results if item["result"].decision_receipt["decision"] == "ACCEPTED"
    ]
    rejected_results = [
        item for item in results if item["result"].decision_receipt["decision"] == "REJECTED"
    ]
    fixture_packets = fixture.get("candidate_source_evidence_packets", [])
    rejection_cases = fixture.get("rejection_mutation_cases", [])
    all_fixture_outputs_not_external = True
    for item in results:
        result = item["result"]
        if result.accepted_packet is not None:
            all_fixture_outputs_not_external = (
                all_fixture_outputs_not_external
                and result.accepted_packet["production_external_fact_authority"] is False
            )
        if result.accepted_ledger_record is not None:
            all_fixture_outputs_not_external = (
                all_fixture_outputs_not_external
                and result.accepted_ledger_record["production_external_fact_authority"] is False
            )
        all_fixture_outputs_not_external = (
            all_fixture_outputs_not_external
            and result.decision_receipt["production_external_fact_authority"] is False
        )

    report = {
        "repo_pr_label": "PR123",
        "roadmap_pr_implemented": "PR106",
        "blueprint_pr_implemented": "PR106",
        "owner_authorized_pr106": True,
        "currentized_prior_repo_pr": "PR122",
        "checked_github_pr_number": 122,
        **_artifact_flags(repo_root),
        "fixture_candidate_packet_count": len(fixture_packets) + len(rejection_cases),
        "fixture_acceptance_success_count": len(accepted_results),
        "fixture_rejection_case_count": len(rejected_results),
        "production_candidate_packet_count": 0,
        "production_accepted_source_fact_count": 0,
        "production_accepted_source_packet_count": 0,
        "production_accepted_ledger_record_count": 0,
        "fixture_outputs_marked_not_external_fact": all_fixture_outputs_not_external,
        "target_field_scope_validation_enabled": True,
        "quote_span_or_machine_field_locator_validation_enabled": True,
        "digest_validation_enabled": True,
        "source_class_validation_enabled": True,
        "conflict_validation_enabled": True,
        "revalidation_validation_enabled": True,
        "private_doc_access_rights_validation_enabled": True,
        "secret_redaction_validation_enabled": True,
        "connector_semantic_binding_created_count": 0,
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
        "master_plan_modified": False,
        "atomicrows_bundle_created": False,
        "atomicrows_sha_created": False,
        "run_validation_gates_uses_fresh_pytest_basetemp": True,
        "fixed_tmp_run_validation_gates_pytest_reused": False,
    }

    executor_report = {
        "accepted_decision_count": len(accepted_results),
        "accepted_packet_ids": [
            item["result"].accepted_packet["accepted_source_evidence_packet_id"]
            for item in accepted_results
            if item["result"].accepted_packet is not None
        ],
        "decision_receipts": [item["result"].decision_receipt for item in results],
        "deterministic_fixture_timestamp": acceptance.DETERMINISTIC_FIXTURE_TIMESTAMP,
        "fixture_authority_class": "TEST_FIXTURE_NOT_EXTERNAL_FACT",
        "production_external_fact_authority": False,
        "rejected_decision_count": len(rejected_results),
        "runtime_live_authority_created": False,
        "order_authority_created": False,
        "profit_evidence_created": False,
        "quantum_backend_execution_count": 0,
    }

    ledger_report = {
        "accepted_ledger_records": [
            item["result"].accepted_ledger_record
            for item in accepted_results
            if item["result"].accepted_ledger_record is not None
        ],
        "accepted_ledger_record_count": len(accepted_results),
        "connector_semantic_unlock_allowed_flag": False,
        "production_accepted_ledger_record_count": 0,
        "production_external_fact_authority": False,
        "runtime_live_use_allowed_flag": False,
        "order_authority_allowed_flag": False,
        "profit_evidence_allowed_flag": False,
        "quantum_backend_execution_allowed_flag": False,
    }

    return {
        PR123_REPORT_PATH: report,
        EXECUTOR_REPORT_PATH: executor_report,
        LEDGER_REPORT_PATH: ledger_report,
    }


def validate_static_surface(repo_root: Path) -> list[str]:
    failures: list[str] = []
    for schema_name in REQUIRED_SCHEMA_FILES:
        if not _resolve(repo_root, SCHEMA_DIR / schema_name).exists():
            failures.append(f"required acceptance schema missing: {schema_name}")
    for path in (
        FIXTURE_PATH,
        OWNER_AUTH_RECEIPT_PATH,
        PR122_AUDIT_RECEIPT_PATH,
        "src/qtt/source_evidence/acceptance/executor.py",
        "src/qtt/source_evidence/acceptance/ledger.py",
        "src/qtt/source_evidence/acceptance/validator.py",
        "tools/source_evidence_acceptance_executor.py",
    ):
        if not _resolve(repo_root, path).exists():
            failures.append(f"required acceptance artifact missing: {path}")
    if failures:
        return failures

    accepted_required = _schema_required_fields(
        repo_root, "accepted_source_evidence_packet.schema.json"
    )
    missing_accepted = sorted(acceptance.REQUIRED_ACCEPTED_PACKET_FIELDS - accepted_required)
    if missing_accepted:
        failures.append(
            "accepted source packet schema missing fields: " + ", ".join(missing_accepted)
        )

    ledger_required = _schema_required_fields(repo_root, "accepted_source_evidence_ledger.schema.json")
    missing_ledger = sorted(
        {
            "accepted_ledger_record_id",
            "accepted_source_evidence_packet_id",
            "candidate_source_evidence_packet_id",
            "acceptance_decision_packet_id",
            "retrieval_manifest_id",
            "source_target_id",
            "retrieval_target_id",
            "venue_id",
            "platform_scope",
            "target_field_path",
            "applicability_scope",
            "accepted_value_type",
            "accepted_value_label",
            "accepted_value_locator",
            "quote_span_locator",
            "machine_field_locator",
            "canonicalized_content_digest",
            "canonical_text_digest_sha256",
            "source_digest_sha256",
            "source_class",
            "source_authority_class",
            "source_locator",
            "source_locator_type",
            "source_locator_status",
            "redaction_state",
            "conflict_state",
            "conflict_resolution_state",
            "revalidation_state",
            "source_change_materiality_class",
            "accepted_at_utc",
            "accepted_by_tool",
            "receipt_ids",
            "acceptance_authority_state",
            "acceptance_decision_receipt_ref",
            "connector_semantic_unlock_candidate_flag",
            "connector_semantic_unlock_allowed_flag",
            "runtime_live_use_allowed_flag",
            "order_authority_allowed_flag",
            "profit_evidence_allowed_flag",
            "quantum_backend_execution_allowed_flag",
            "production_external_fact_authority",
        }
        - ledger_required
    )
    if missing_ledger:
        failures.append("accepted ledger schema missing fields: " + ", ".join(missing_ledger))

    results = fixture_execution_results(repo_root)
    accepted = [
        item for item in results if item["result"].decision_receipt["decision"] == "ACCEPTED"
    ]
    rejected = [
        item for item in results if item["result"].decision_receipt["decision"] == "REJECTED"
    ]
    if len(accepted) != 1:
        failures.append("fixture execution must produce exactly one accepted candidate")
    fixture = _fixture(repo_root)
    expected_rejections = len(fixture.get("rejection_mutation_cases", []))
    if len(rejected) != expected_rejections:
        failures.append("fixture execution rejection count does not match fixture cases")
    for item in results:
        result = item["result"]
        failures.extend(acceptance.validate_decision_receipt(result.decision_receipt))
        if result.accepted_packet is not None:
            failures.extend(acceptance.validate_accepted_packet(result.accepted_packet))
            if result.accepted_packet["production_external_fact_authority"] is not False:
                failures.append("fixture accepted packet must not be production authority")
        if result.accepted_ledger_record is not None:
            failures.extend(acceptance.validate_ledger_record(result.accepted_ledger_record))
            if result.accepted_ledger_record["production_external_fact_authority"] is not False:
                failures.append("fixture accepted ledger must not be production authority")
        if item.get("expected_decision") == "REJECTED":
            expected_code = item.get("expected_rejection_code")
            if expected_code not in result.decision_receipt["rejection_codes"]:
                failures.append(
                    f"{item['case_id']} missing expected rejection code {expected_code}"
                )

    reports = build_reports(repo_root)
    if reports != build_reports(repo_root):
        failures.append("acceptance reports are not deterministic across in-memory rerun")
    pr123_report = reports[PR123_REPORT_PATH]
    missing_report_fields = sorted(REQUIRED_REPORT_FIELDS - set(pr123_report))
    if missing_report_fields:
        failures.append("PR123 report missing fields: " + ", ".join(missing_report_fields))
    if pr123_report["production_accepted_source_fact_count"] != 0:
        failures.append("production accepted source fact count must remain 0")
    if pr123_report["connector_semantic_binding_created_count"] != 0:
        failures.append("connector semantic binding created count must remain 0")

    return failures


def write_reports(repo_root: Path) -> None:
    for rel_path, report in build_reports(repo_root).items():
        _write_json(_resolve(repo_root, rel_path), report)


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
