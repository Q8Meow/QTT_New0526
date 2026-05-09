#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import sys
from typing import Any, Sequence

_SRC = pathlib.Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from qtt.core.testing.gate_result import (  # noqa: E402
    CANONICAL_ATOMICROWS_BUNDLE,
    CANONICAL_ATOMICROWS_BUNDLE_SHA,
    STATIC_AUTHORITY_FLAGS,
    canonical_atomicrows_absence_failures,
    canonical_atomicrows_presence,
    hidden_zip_paths,
    require_bool_map,
    require_exact_fields,
    static_metadata,
    true_claim_failures,
    write_json,
)

SUCCESS_MARKER = "QTT_CUMULATIVE_TEST_GATE_OK"
FAILURE_MARKER = "QTT_CUMULATIVE_TEST_GATE_FAILED"

REPORT_TYPE = "QTT_CUMULATIVE_TEST_GATE_REPORT"
REPORT_VERSION = "PR38_QTT_CUMULATIVE_TEST_GATE_REPORT_V1"
PHASE = "first-coding-runbook"
VALIDATION_HOOK = "QTT_CUMULATIVE_TEST_GATE_STATIC_AUDIT"

STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_PRESENT = "PRESENT"
STATUS_CONFIRMED_BY_MARKER = "REQUIRED_PRIOR_GATE_CONFIRMED_BY_VALIDATION_MARKER"
STATUS_STATIC_BOOTSTRAP = "REQUIRED_PRIOR_GATE_REPORT_NOT_CREATED_STATIC_BOOTSTRAP"
STATUS_MISSING_BLOCKED = "MISSING_BLOCKED"

RECEIPT_FIELDS = {
    "receipt_id",
    "description",
    "required",
    "satisfied",
    "status",
    "receipt_source",
    "paths",
    "validation_marker",
    "creates_source_fact_acceptance",
    "creates_connector_semantics",
    "creates_runtime_resolver_snapshot",
    "executes_replay_or_paper",
    "creates_live_reachability",
    "creates_runtime_cash_or_usable_cash",
    "creates_atomicrows_bundle_or_4183_rows",
    "reduces_blockers",
    "creates_profit_evidence",
}

ROOT_FIELDS = {
    "report_type",
    "report_version",
    "phase",
    "status",
    "strict_no_claim",
    "metadata",
    "prior_gate_receipts",
    "gate_checks",
    "filesystem_claim_checks",
    "no_claim_flags",
    "validation_hook_ids",
    "findings",
}

METADATA_FIELDS = set(STATIC_AUTHORITY_FLAGS) | {
    "generated_by",
    "generated_at_utc",
    "authority_class",
}

GATE_CHECK_FIELDS = {
    "owner_start_receipt_present_or_reported_missing",
    "master_plan_placement_receipt_present",
    "master_plan_hash_receipt_present_or_reported_missing",
    "section_manifest_receipt_present",
    "traceability_gate_receipt_present",
    "atomicrows_schema_checker_blocker_report_receipt_present",
    "generated_derivative_gate_receipt_present",
    "source_evidence_gate_confirmation_receipt_present",
    "stage1_packet_schema_gate_receipt_present",
    "venue_neutral_prediction_adapter_gate_receipt_present",
    "connector_scaffold_source_required_gate_receipt_present",
    "stage1_runtime_scaffold_gate_receipt_present",
    "source_fact_binding_connector_semantic_readiness_gate_receipt_present",
    "no_stale_generated_derivative_completion_claim",
    "no_hidden_zip_authority",
    "no_source_dependent_connector_semantic_values",
    "no_replay_paper_result_claims",
    "no_live_reachability_claims",
    "no_atomicrows_completion_claim",
    "no_blocker_reduction_claim",
    "no_profit_claim",
}

FILESYSTEM_CHECK_FIELDS = {
    "canonical_atomicrows_bundle_path",
    "canonical_atomicrows_bundle_present",
    "canonical_atomicrows_bundle_sha_path",
    "canonical_atomicrows_bundle_sha_present",
    "hidden_zip_authority_present",
    "hidden_zip_paths",
    "direct_main_bypass_claim_present",
}

NO_CLAIM_FLAGS = {
    "stale_generated_derivative_completion_claim": False,
    "hidden_zip_authority_claim": False,
    "direct_main_bypass_claim": False,
    "source_dependent_connector_semantic_values_claim": False,
    "replay_paper_result_claim": False,
    "live_reachability_claim": False,
    "atomicrows_completion_claim": False,
    "atomicrows_invention_claim": False,
    "blocker_reduction_claim": False,
    "profit_claim": False,
}

FORBIDDEN_TRUE_FIELDS = set(STATIC_AUTHORITY_FLAGS) | set(NO_CLAIM_FLAGS) | {
    "canonical_atomicrows_bundle_present",
    "canonical_atomicrows_bundle_sha_present",
    "hidden_zip_authority_present",
    "direct_main_bypass_claim_present",
}

REQUIRED_RECEIPTS: list[dict[str, Any]] = [
    {
        "receipt_id": "owner_start_receipt_present_or_reported_missing",
        "description": "Owner start receipt is explicitly represented as static bootstrap.",
        "receipt_source": "STATIC_BOOTSTRAP_MISSING_REPORT",
        "paths": [],
        "validation_marker": None,
    },
    {
        "receipt_id": "master_plan_placement_receipt_present",
        "description": "Master plan placement is represented by the generated section manifest.",
        "receipt_source": "GENERATED_REPORT_FILE",
        "paths": ["docs/master_plan/generated/SectionManifest.json"],
        "validation_marker": "MASTER_PLAN_INGEST_OK",
    },
    {
        "receipt_id": "master_plan_hash_receipt_present_or_reported_missing",
        "description": "Master plan hash receipt is explicitly missing without SHA authority.",
        "receipt_source": "STATIC_BOOTSTRAP_MISSING_REPORT",
        "paths": [],
        "validation_marker": None,
    },
    {
        "receipt_id": "section_manifest_receipt_present",
        "description": "Section manifest committed generated report is present.",
        "receipt_source": "GENERATED_REPORT_FILE",
        "paths": ["docs/master_plan/generated/SectionManifest.json"],
        "validation_marker": "MASTER_PLAN_INGEST_OK",
    },
    {
        "receipt_id": "traceability_gate_receipt_present",
        "description": "Traceability report committed generated report is present.",
        "receipt_source": "GENERATED_REPORT_FILE",
        "paths": ["docs/master_plan/generated/TraceabilityReport.json"],
        "validation_marker": "TRACEABILITY_GATE_OK",
    },
    {
        "receipt_id": "atomicrows_schema_checker_blocker_report_receipt_present",
        "description": "AtomicRows schema checker and blocker report are confirmed by prior validation marker.",
        "receipt_source": "STATIC_VALIDATION_MARKER",
        "paths": [
            "schemas/atomicrows/atomic_parameter_row.schema.json",
            "schemas/atomicrows/atomic_row_bundle.schema.json",
            "tests/fixtures/atomicrows/synthetic_atomicrows_bundle_bootstrap_absent.v1.fixture.json",
        ],
        "validation_marker": "ATOMICROWS_BUNDLE_SCHEMA_CHECKER_STATIC_VALIDATION_OK",
    },
    {
        "receipt_id": "generated_derivative_gate_receipt_present",
        "description": "Generated-derivative bootstrap gate is confirmed by prior validation marker.",
        "receipt_source": "STATIC_VALIDATION_MARKER",
        "paths": [
            "schemas/master_plan/generated_derivative_bootstrap_gate.schema.json",
            "tests/fixtures/master_plan/synthetic_generated_derivative_bootstrap_gate.v1.fixture.json",
        ],
        "validation_marker": "GENERATED_DERIVATIVE_BOOTSTRAP_GATE_STATIC_VALIDATION_OK",
    },
    {
        "receipt_id": "source_evidence_gate_confirmation_receipt_present",
        "description": "Source-evidence gate confirmation remains blocked and is confirmed by prior validation marker.",
        "receipt_source": "STATIC_VALIDATION_MARKER",
        "paths": [
            "schemas/source_evidence/source_evidence_gate_confirmation.schema.json",
            "tests/fixtures/source_evidence/synthetic_source_evidence_gate_confirmation_blocked.v1.fixture.json",
        ],
        "validation_marker": "SOURCE_EVIDENCE_GATE_CONFIRMATION_STATIC_VALIDATION_OK",
    },
    {
        "receipt_id": "stage1_packet_schema_gate_receipt_present",
        "description": "Stage-1 packet schema gate is confirmed by prior validation marker.",
        "receipt_source": "STATIC_VALIDATION_MARKER",
        "paths": [
            "schemas/stage1_prediction_markets/stage1_packet_schema_gate_report.schema.json",
            "tests/fixtures/stage1_prediction_markets/synthetic_stage1_packet_schema_gate_blocked.v1.fixture.json",
        ],
        "validation_marker": "STAGE1_PACKET_SCHEMA_GATE_STATIC_VALIDATION_OK",
    },
    {
        "receipt_id": "venue_neutral_prediction_adapter_gate_receipt_present",
        "description": "Venue-neutral prediction adapter gate is confirmed by prior validation marker.",
        "receipt_source": "STATIC_VALIDATION_MARKER",
        "paths": [
            "schemas/venue_neutral_prediction_adapter/venue_neutral_adapter_gate_report.schema.json",
            "tests/fixtures/venue_neutral_prediction_adapter/synthetic_venue_neutral_prediction_adapter_gate_blocked.v1.fixture.json",
        ],
        "validation_marker": "VENUE_NEUTRAL_PREDICTION_ADAPTER_GATE_STATIC_VALIDATION_OK",
    },
    {
        "receipt_id": "connector_scaffold_source_required_gate_receipt_present",
        "description": "Connector scaffold source-required gate is confirmed by prior validation marker.",
        "receipt_source": "STATIC_VALIDATION_MARKER",
        "paths": [
            "schemas/connectors/connector_scaffold_source_required_gate.schema.json",
            "tests/fixtures/connectors/synthetic_connector_scaffold_source_required_blocked.v1.fixture.json",
        ],
        "validation_marker": "CONNECTOR_SCAFFOLD_SOURCE_REQUIRED_GATE_STATIC_VALIDATION_OK",
    },
    {
        "receipt_id": "stage1_runtime_scaffold_gate_receipt_present",
        "description": "Stage-1 runtime scaffold gate is confirmed by prior validation marker.",
        "receipt_source": "STATIC_VALIDATION_MARKER",
        "paths": [
            "schemas/runtime_orchestration/stage1_runtime_scaffold_gate.schema.json",
            "tests/fixtures/runtime_orchestration/synthetic_stage1_runtime_scaffold_gate_blocked.v1.fixture.json",
        ],
        "validation_marker": "STAGE1_RUNTIME_SCAFFOLD_GATE_STATIC_VALIDATION_OK",
    },
    {
        "receipt_id": (
            "source_fact_binding_connector_semantic_readiness_gate_receipt_present"
        ),
        "description": (
            "PR38 source-fact binding and connector semantic readiness gate is "
            "confirmed by prior validation marker."
        ),
        "receipt_source": "STATIC_VALIDATION_MARKER",
        "paths": [
            (
                "schemas/source_fact_binding_readiness/"
                "stage1_source_to_connector_field_binding_matrix.schema.json"
            ),
            (
                "schemas/source_fact_binding_readiness/"
                "stage1_connector_semantic_target_field_matrix.schema.json"
            ),
            (
                "schemas/source_fact_binding_readiness/"
                "stage1_connector_semantic_readiness_gate_report.schema.json"
            ),
            (
                "tests/fixtures/source_fact_binding_readiness/"
                "synthetic_stage1_source_to_connector_field_binding_matrix.v1.fixture.json"
            ),
            (
                "tests/fixtures/source_fact_binding_readiness/"
                "synthetic_stage1_connector_semantic_target_field_matrix.v1.fixture.json"
            ),
            (
                "tests/fixtures/source_fact_binding_readiness/"
                "synthetic_stage1_connector_semantic_readiness_gate_report.v1.fixture.json"
            ),
        ],
        "validation_marker": (
            "SOURCE_FACT_BINDING_CONNECTOR_SEMANTIC_READINESS_STATIC_VALIDATION_OK"
        ),
    },
]


def _all_paths_present(repo_root: pathlib.Path, paths: Sequence[str]) -> bool:
    return all((repo_root / pathlib.Path(path)).exists() for path in paths)


def _receipt(spec: dict[str, Any], repo_root: pathlib.Path) -> dict[str, Any]:
    paths = list(spec["paths"])
    if spec["receipt_source"] == "STATIC_BOOTSTRAP_MISSING_REPORT":
        status = STATUS_STATIC_BOOTSTRAP
        satisfied = True
    elif _all_paths_present(repo_root, paths):
        status = (
            STATUS_PRESENT
            if spec["receipt_source"] == "GENERATED_REPORT_FILE"
            else STATUS_CONFIRMED_BY_MARKER
        )
        satisfied = True
    else:
        status = STATUS_MISSING_BLOCKED
        satisfied = False

    receipt = {
        "receipt_id": spec["receipt_id"],
        "description": spec["description"],
        "required": True,
        "satisfied": satisfied,
        "status": status,
        "receipt_source": spec["receipt_source"],
        "paths": paths,
        "validation_marker": spec["validation_marker"],
    }
    receipt.update(STATIC_AUTHORITY_FLAGS)
    return receipt


def _filesystem_checks(repo_root: pathlib.Path) -> dict[str, Any]:
    bundle_present, sha_present = canonical_atomicrows_presence(repo_root)
    zip_paths = [str(path) for path in hidden_zip_paths(repo_root)]
    return {
        "canonical_atomicrows_bundle_path": str(CANONICAL_ATOMICROWS_BUNDLE),
        "canonical_atomicrows_bundle_present": bundle_present,
        "canonical_atomicrows_bundle_sha_path": str(CANONICAL_ATOMICROWS_BUNDLE_SHA),
        "canonical_atomicrows_bundle_sha_present": sha_present,
        "hidden_zip_authority_present": bool(zip_paths),
        "hidden_zip_paths": zip_paths,
        "direct_main_bypass_claim_present": False,
    }


def build_report(
    *,
    repo_root: pathlib.Path,
    phase: str,
    strict_no_claim: bool,
) -> dict[str, Any]:
    root = repo_root.resolve()
    receipts = [_receipt(spec, root) for spec in REQUIRED_RECEIPTS]
    filesystem_checks = _filesystem_checks(root)
    no_claim_flags = dict(NO_CLAIM_FLAGS)

    gate_checks = {
        receipt["receipt_id"]: receipt["satisfied"] for receipt in receipts
    }
    gate_checks.update(
        {
            "no_stale_generated_derivative_completion_claim": not no_claim_flags[
                "stale_generated_derivative_completion_claim"
            ],
            "no_hidden_zip_authority": not filesystem_checks[
                "hidden_zip_authority_present"
            ],
            "no_source_dependent_connector_semantic_values": not no_claim_flags[
                "source_dependent_connector_semantic_values_claim"
            ],
            "no_replay_paper_result_claims": not no_claim_flags[
                "replay_paper_result_claim"
            ],
            "no_live_reachability_claims": not no_claim_flags[
                "live_reachability_claim"
            ],
            "no_atomicrows_completion_claim": (
                not no_claim_flags["atomicrows_completion_claim"]
                and not no_claim_flags["atomicrows_invention_claim"]
                and not filesystem_checks["canonical_atomicrows_bundle_present"]
                and not filesystem_checks["canonical_atomicrows_bundle_sha_present"]
            ),
            "no_blocker_reduction_claim": not no_claim_flags[
                "blocker_reduction_claim"
            ],
            "no_profit_claim": not no_claim_flags["profit_claim"],
        }
    )

    report = {
        "report_type": REPORT_TYPE,
        "report_version": REPORT_VERSION,
        "phase": phase,
        "status": STATUS_PASS,
        "strict_no_claim": strict_no_claim,
        "metadata": static_metadata("tools/qtt_test_gate.py"),
        "prior_gate_receipts": receipts,
        "gate_checks": gate_checks,
        "filesystem_claim_checks": filesystem_checks,
        "no_claim_flags": no_claim_flags,
        "validation_hook_ids": [VALIDATION_HOOK],
        "findings": [],
    }
    findings = validate_qtt_test_gate_report(
        report,
        repo_root=root,
        strict_no_claim=strict_no_claim,
    )
    report["findings"] = findings
    report["status"] = STATUS_FAIL if findings else STATUS_PASS
    return report


def _validate_receipt(receipt: Any, index: int) -> list[str]:
    label = f"prior_gate_receipts[{index}]"
    if not isinstance(receipt, dict):
        return [f"{label} must be an object"]
    failures = require_exact_fields(receipt, RECEIPT_FIELDS, label)
    if receipt.get("required") is not True:
        failures.append(f"{label}.required must be true")
    if receipt.get("satisfied") is not True:
        failures.append(f"{label}.{receipt.get('receipt_id')} must be satisfied")
    if receipt.get("status") not in {
        STATUS_PRESENT,
        STATUS_CONFIRMED_BY_MARKER,
        STATUS_STATIC_BOOTSTRAP,
    }:
        failures.append(f"{label}.status is not an accepted receipt status")
    failures.extend(_validate_static_flags(receipt, label))
    return failures


def _validate_static_flags(value: dict[str, Any], label: str) -> list[str]:
    failures: list[str] = []
    for field, expected in sorted(STATIC_AUTHORITY_FLAGS.items()):
        if value.get(field) is not expected:
            failures.append(f"{label}.{field} must be {expected}")
    return failures


def validate_qtt_test_gate_report(
    report: dict[str, Any],
    *,
    repo_root: pathlib.Path,
    strict_no_claim: bool = False,
) -> list[str]:
    failures = require_exact_fields(report, ROOT_FIELDS, "qtt test gate report")

    if report.get("report_type") != REPORT_TYPE:
        failures.append(f"report_type must be {REPORT_TYPE}")
    if report.get("report_version") != REPORT_VERSION:
        failures.append(f"report_version must be {REPORT_VERSION}")
    if report.get("phase") != PHASE:
        failures.append(f"phase must be {PHASE}")
    if report.get("status") not in {STATUS_PASS, STATUS_FAIL}:
        failures.append("status must be PASS or FAIL")
    if report.get("strict_no_claim") is not strict_no_claim:
        failures.append("strict_no_claim must match invocation")

    metadata = report.get("metadata")
    if not isinstance(metadata, dict):
        failures.append("metadata must be an object")
    else:
        failures.extend(require_exact_fields(metadata, METADATA_FIELDS, "metadata"))
        failures.extend(_validate_static_flags(metadata, "metadata"))
        if metadata.get("authority_class") != "STATIC_REPORT_ONLY_NOT_TRADING_AUTHORITY":
            failures.append("metadata.authority_class must be static report only")

    receipts = report.get("prior_gate_receipts")
    if not isinstance(receipts, list):
        failures.append("prior_gate_receipts must be a list")
    else:
        expected_ids = [spec["receipt_id"] for spec in REQUIRED_RECEIPTS]
        actual_ids = [
            item.get("receipt_id") for item in receipts if isinstance(item, dict)
        ]
        if actual_ids != expected_ids:
            failures.append("prior_gate_receipts must preserve required cumulative order")
        for index, receipt in enumerate(receipts):
            failures.extend(_validate_receipt(receipt, index))

    gate_checks = report.get("gate_checks")
    if not isinstance(gate_checks, dict):
        failures.append("gate_checks must be an object")
    else:
        failures.extend(require_exact_fields(gate_checks, GATE_CHECK_FIELDS, "gate_checks"))
        for field in sorted(GATE_CHECK_FIELDS):
            if gate_checks.get(field) is not True:
                failures.append(f"gate_checks.{field} must be true")

    filesystem_checks = report.get("filesystem_claim_checks")
    if not isinstance(filesystem_checks, dict):
        failures.append("filesystem_claim_checks must be an object")
    else:
        failures.extend(
            require_exact_fields(
                filesystem_checks,
                FILESYSTEM_CHECK_FIELDS,
                "filesystem_claim_checks",
            )
        )
        bundle_present, sha_present = canonical_atomicrows_presence(repo_root)
        if filesystem_checks.get("canonical_atomicrows_bundle_present") is not bundle_present:
            failures.append(
                "filesystem_claim_checks.canonical_atomicrows_bundle_present must "
                f"match filesystem presence {bundle_present}"
            )
        if filesystem_checks.get("canonical_atomicrows_bundle_sha_present") is not sha_present:
            failures.append(
                "filesystem_claim_checks.canonical_atomicrows_bundle_sha_present must "
                f"match filesystem presence {sha_present}"
            )
        zip_paths = [str(path) for path in hidden_zip_paths(repo_root)]
        if filesystem_checks.get("hidden_zip_paths") != zip_paths:
            failures.append("filesystem_claim_checks.hidden_zip_paths must match repo scan")
        if filesystem_checks.get("hidden_zip_authority_present") is not bool(zip_paths):
            failures.append("filesystem_claim_checks.hidden_zip_authority_present must match repo scan")
        if filesystem_checks.get("direct_main_bypass_claim_present") is not False:
            failures.append("filesystem_claim_checks.direct_main_bypass_claim_present must be false")

    failures.extend(
        require_bool_map(
            report.get("no_claim_flags"),
            NO_CLAIM_FLAGS,
            "no_claim_flags",
        )
    )
    failures.extend(
        true_claim_failures(
            report,
            forbidden_true_fields=FORBIDDEN_TRUE_FIELDS,
            label="qtt test gate report",
        )
    )
    failures.extend(
        canonical_atomicrows_absence_failures(
            repo_root,
            label="qtt test gate report",
        )
    )
    if hidden_zip_paths(repo_root):
        failures.append("qtt test gate report: hidden ZIP authority must remain absent")

    if report.get("validation_hook_ids") != [VALIDATION_HOOK]:
        failures.append(f"validation_hook_ids must contain only {VALIDATION_HOOK}")
    if not isinstance(report.get("findings"), list):
        failures.append("findings must be a list")

    return failures


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True, choices=[PHASE])
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--strict-no-claim", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    repo_root = pathlib.Path(args.repo_root)
    report = build_report(
        repo_root=repo_root,
        phase=args.phase,
        strict_no_claim=args.strict_no_claim,
    )
    write_json(repo_root / pathlib.Path(args.out), report)

    if report["findings"]:
        print(FAILURE_MARKER)
        for finding in report["findings"]:
            print(f"- {finding}")
        return 1
    print(SUCCESS_MARKER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
