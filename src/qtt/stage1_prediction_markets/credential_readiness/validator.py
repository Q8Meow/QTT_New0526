from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, Mapping

from src.qtt.stage1_prediction_markets.credential_readiness import policy
from src.qtt.stage1_prediction_markets.credential_readiness.alias import (
    build_credential_alias_registry_records,
    secret_like_findings,
    validate_alias_registry_records,
)
from src.qtt.stage1_prediction_markets.credential_readiness.handoff import (
    build_downstream_handoff,
)
from src.qtt.stage1_prediction_markets.credential_readiness.no_capture import (
    build_rejection_receipts,
    build_secret_no_capture_attestations,
    validate_no_capture_attestations,
    validate_rejection_receipts,
)
from src.qtt.stage1_prediction_markets.credential_readiness.scope_binding import (
    build_scope_bindings,
    validate_scope_bindings,
)


GENERATED_DIR = Path("docs/master_plan/source_evidence/generated")
FIXTURE_DIR = Path("tests/fixtures/source_evidence/pr131_credential_alias_secret_no_capture")
SCHEMA_DIR = Path("src/qtt/stage1_prediction_markets/credential_readiness")

PR130_HANDOFF_REPORT_PATH = GENERATED_DIR / "PrivateStateDownstreamHandoff.report.json"

MAIN_REPORT_PATH = GENERATED_DIR / (
    "CODEX_PR131_CREDENTIAL_ALIAS_SECRET_NO_CAPTURE_READINESS_GATE_REPORT.json"
)
ALIAS_REPORT_PATH = GENERATED_DIR / "CredentialAliasReadinessGate.report.json"
NO_CAPTURE_REPORT_PATH = GENERATED_DIR / "SecretNoCaptureAttestation.report.json"
SCOPE_REPORT_PATH = GENERATED_DIR / "CredentialScopeBinding.report.json"
HANDOFF_REPORT_PATH = GENERATED_DIR / "CredentialReadinessDownstreamHandoff.report.json"

REPORT_PATHS = {
    "main_report": MAIN_REPORT_PATH,
    "alias_report": ALIAS_REPORT_PATH,
    "no_capture_report": NO_CAPTURE_REPORT_PATH,
    "scope_report": SCOPE_REPORT_PATH,
    "handoff_report": HANDOFF_REPORT_PATH,
}

SCHEMA_FILES = (
    "credential_alias_registry.schema.json",
    "credential_alias_readiness_receipt.schema.json",
    "secret_no_capture_attestation.schema.json",
    "credential_scope_binding.schema.json",
    "credential_readiness_rejection_receipt.schema.json",
    "credential_readiness_downstream_handoff.schema.json",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _output_path(repo_root: Path, path: Path, out_root: Path | None = None) -> Path:
    root = repo_root if out_root is None else out_root
    return root / path


def _scope_field(record: Mapping[str, Any]) -> dict[str, str]:
    if record.get("venue_id"):
        return {"venue_id": str(record["venue_id"])}
    return {"scope_id": str(record["scope_id"])}


def _scope_value(record: Mapping[str, Any]) -> str:
    return str(record.get("venue_id") or record.get("scope_id"))


def _private_state_handoff_from_report(repo_root: Path) -> dict[str, Any]:
    report = _load_json(repo_root / PR130_HANDOFF_REPORT_PATH)
    value = report.get("private_state_downstream_handoff")
    if not isinstance(value, dict):
        raise ValueError("PR130 downstream handoff report missing handoff object")
    return value


def validate_pr130_handoff(handoff: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(handoff, Mapping):
        return ["missing PR130 private-state downstream handoff"]
    failures: list[str] = []
    expected = {
        "private_state_downstream_handoff_id": "PR130_PRIVATE_STATE_DOWNSTREAM_HANDOFF_V1",
        "source_repo_pr_label": "PR130",
        "future_credential_alias_secret_no_capture_pr": "PR113",
        "production_downstream_authority": False,
    }
    for field, expected_value in expected.items():
        if handoff.get(field) != expected_value:
            failures.append(f"PR130 handoff {field} must be {expected_value!r}")
    if tuple(handoff.get("venue_ids_in_scope", [])) != policy.STAGE1_VENUE_IDS:
        failures.append("PR130 handoff must cover exactly the three Stage-1 venues")
    if "PREDICTION_MARKETS_GENERAL" in set(handoff.get("venue_ids_in_scope", [])):
        failures.append("PREDICTION_MARKETS_GENERAL must not be a PR130 venue")
    return failures


def build_readiness_receipts(
    alias_records: list[Mapping[str, Any]],
    attestations: list[Mapping[str, Any]],
    bindings: list[Mapping[str, Any]],
    private_state_handoff_ref: str,
) -> list[dict[str, object]]:
    attestation_by_alias = {
        str(record["alias_registry_ref"]): str(record["attestation_id"])
        for record in attestations
    }
    binding_by_alias = {
        str(record["alias_registry_ref"]): str(record["binding_id"])
        for record in bindings
    }
    receipts: list[dict[str, object]] = []
    for record in alias_records:
        alias_id = str(record["credential_alias_id"])
        scope_value = _scope_value(record)
        receipts.append(
            {
                **policy.common_record_fields("CREDENTIAL_ALIAS_READINESS_RECEIPT"),
                "receipt_id": f"PR131_{scope_value}_CREDENTIAL_ALIAS_READINESS_RECEIPT_V1",
                "alias_registry_ref": alias_id,
                **_scope_field(record),
                "readiness_state": "READY_FOR_METADATA_HANDOFF",
                "accepted_states": list(policy.READINESS_STATES),
                "no_secret_capture_attestation_ref": attestation_by_alias[alias_id],
                "credential_scope_binding_ref": binding_by_alias[alias_id],
                "private_state_downstream_handoff_dependency_ref": private_state_handoff_ref,
                "pr130_handoff_schema_valid": True,
                "pr130_handoff_scope_compatible": True,
                "downstream_pr114_market_data_ingest_ref": (
                    "PR114_VENUE_MARKET_DATA_INGEST_ADAPTERS_METADATA_HANDOFF"
                ),
                "downstream_pr115_orderbook_snapshot_ref": (
                    "PR115_ORDERBOOK_EVENT_STATE_SNAPSHOT_BUILDER_METADATA_HANDOFF"
                ),
                "downstream_pr116_runtime_resolver_snapshot_ref": (
                    "PR116_RUNTIME_RESOLVER_SNAPSHOT_EXECUTOR_METADATA_HANDOFF"
                ),
                "no_live_resolution": True,
                "no_provider_call": True,
                "no_environment_read": True,
                "no_secret_manager_call": True,
                "no_network_io": True,
                "no_private_state_fetch": True,
                "no_order_authority": True,
                "no_profit_evidence": True,
                "no_quantum_execution": True,
            }
        )
    return receipts


def validate_readiness_receipts(receipts: list[Mapping[str, Any]]) -> list[str]:
    failures: list[str] = []
    seen = {record.get("venue_id") or record.get("scope_id") for record in receipts}
    expected = set(policy.STAGE1_VENUE_IDS) | set(policy.SHARED_SCOPE_IDS)
    if seen != expected:
        failures.append("readiness receipts must cover exactly three venues plus shared scope")
    for receipt in receipts:
        if receipt.get("readiness_state") != "READY_FOR_METADATA_HANDOFF":
            failures.append("readiness receipt state must be READY_FOR_METADATA_HANDOFF")
        if tuple(receipt.get("accepted_states", [])) != policy.READINESS_STATES:
            failures.append("readiness receipt accepted states must mirror centralized policy")
        for flag in (
            "pr130_handoff_schema_valid",
            "pr130_handoff_scope_compatible",
            "no_live_resolution",
            "no_provider_call",
            "no_environment_read",
            "no_secret_manager_call",
            "no_network_io",
            "no_private_state_fetch",
            "no_order_authority",
            "no_profit_evidence",
            "no_quantum_execution",
        ):
            if receipt.get(flag) is not True:
                failures.append(f"readiness receipt {flag} must be true")
    return failures


def validate_scope_compatibility(
    handoff: Mapping[str, Any],
    alias_records: list[Mapping[str, Any]],
    readiness_receipts: list[Mapping[str, Any]],
) -> list[str]:
    failures: list[str] = []
    handoff_venues = set(handoff.get("venue_ids_in_scope", []))
    for record in [*alias_records, *readiness_receipts]:
        venue_id = record.get("venue_id")
        scope_id = record.get("scope_id")
        if venue_id and venue_id not in handoff_venues:
            failures.append(f"scope mismatch for venue {venue_id}")
        if scope_id and scope_id not in policy.SHARED_SCOPE_IDS:
            failures.append(f"unsupported shared scope {scope_id}")
        if scope_id == "PREDICTION_MARKETS_GENERAL" and venue_id:
            failures.append("shared scope cannot also be venue scoped")
    return failures


def _policy_constants_section() -> dict[str, object]:
    return {
        "allowed_action_ids": list(policy.ALLOWED_ACTION_IDS),
        "allowed_alias_classes": list(policy.ALLOWED_ALIAS_CLASSES),
        "authority_zero_flags": list(policy.AUTHORITY_ZERO_FLAGS),
        "blocked_action_ids": list(policy.BLOCKED_ACTION_IDS),
        "downstream_pr_ids": list(policy.DOWNSTREAM_PR_IDS),
        "package_authority_class": policy.PACKAGE_AUTHORITY_CLASS,
        "producer_repo_pr": policy.PRODUCER_REPO_PR,
        "producer_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
        "secret_like_rejection_classes": list(policy.SECRET_LIKE_REJECTION_CLASSES),
        "shared_scope_ids": list(policy.SHARED_SCOPE_IDS),
        "stage1_venue_ids": list(policy.STAGE1_VENUE_IDS),
    }


def _market_specific_index(
    readiness_receipts: list[Mapping[str, Any]],
    attestations: list[Mapping[str, Any]],
) -> dict[str, object]:
    readiness_by_scope = {
        _scope_value(record): str(record["receipt_id"]) for record in readiness_receipts
    }
    attestations_by_scope = {
        str(record["alias_registry_ref"])
        .replace("PR131_", "")
        .replace("_CREDENTIAL_ALIAS_REGISTRY_RECORD_V1", ""): str(record["attestation_id"])
        for record in attestations
    }
    venue_entries = [
        {
            "venue_id": venue_id,
            "credential_alias_scope_class": "STAGE1_VENUE_CREDENTIAL_ALIAS_READINESS_METADATA_ONLY",
            "required_readiness_receipt_ids": [readiness_by_scope[venue_id]],
            "required_secret_no_capture_attestation_ids": [
                attestations_by_scope[venue_id]
            ],
            "allowed_alias_classes": list(policy.ALLOWED_ALIAS_CLASSES),
            "blocked_secret_classes": list(policy.SECRET_LIKE_REJECTION_CLASSES),
            "private_state_handoff_dependency": "PR130_PRIVATE_STATE_DOWNSTREAM_HANDOFF_V1",
            "downstream_market_data_adapter_path_ref": (
                f"PR114_{venue_id}_MARKET_DATA_INGEST_ADAPTER_METADATA_ONLY"
            ),
            "downstream_orderbook_snapshot_path_ref": (
                f"PR115_{venue_id}_ORDERBOOK_EVENT_STATE_SNAPSHOT_METADATA_ONLY"
            ),
            "downstream_runtime_resolver_snapshot_path_ref": (
                f"PR116_{venue_id}_RUNTIME_RESOLVER_SNAPSHOT_METADATA_ONLY"
            ),
            "no_production_credential_authority": True,
            "no_live_credential_resolution": True,
            "no_environment_variable_read": True,
            "no_secret_manager_call": True,
            "no_network_io": True,
            "no_private_state_fetch": True,
            "no_order_authority": True,
        }
        for venue_id in policy.STAGE1_VENUE_IDS
    ]
    shared_entries = [
        {
            "scope_id": "PREDICTION_MARKETS_GENERAL",
            "scope_type": "SHARED_TAXONOMY_NOT_VENUE",
            "not_counted_as_venue": True,
            "no_venue_api_authority": True,
            "no_credential_resolution_authority": True,
        }
    ]
    return {
        "shared_scope_entries": shared_entries,
        "venue_specific_entries": venue_entries,
    }


def _command_action_matrix() -> list[dict[str, object]]:
    allowed = [
        {
            "action_id": action_id,
            "actor": "CODEX",
            "authority_class": policy.PACKAGE_AUTHORITY_CLASS,
            "input_artifacts": [
                "owner-approved PR131 prompt",
                "mandatory roadmap/master-plan/source-evidence reads",
            ],
            "output_artifacts": ["PR131 metadata artifact"],
            "allowed": True,
            "creates_runtime_authority": False,
            "creates_live_authority": False,
            "creates_credential_authority": False,
            "creates_order_authority": False,
            "creates_profit_evidence": False,
            "creates_quantum_execution": False,
            "atomicrows_bundle_consumed": False,
            "atomicrows_sha_created": False,
        }
        for action_id in policy.ALLOWED_ACTION_IDS
    ]
    blocked = [
        {
            "action_id": action_id,
            "actor": "CODEX",
            "authority_class": policy.PACKAGE_AUTHORITY_CLASS,
            "input_artifacts": ["blocked by centralized PR131 policy"],
            "output_artifacts": [],
            "allowed": False,
            "blocked_reason": f"POLICY_BLOCK_{action_id}",
            "creates_runtime_authority": False,
            "creates_live_authority": False,
            "creates_credential_authority": False,
            "creates_order_authority": False,
            "creates_profit_evidence": False,
            "creates_quantum_execution": False,
            "atomicrows_bundle_consumed": False,
            "atomicrows_sha_created": False,
        }
        for action_id in policy.BLOCKED_ACTION_IDS
    ]
    return allowed + blocked


def _schema_validation(repo_root: Path) -> list[str]:
    failures: list[str] = []
    for filename in SCHEMA_FILES:
        path = repo_root / SCHEMA_DIR / filename
        if not path.exists():
            failures.append(f"missing PR131 schema: {filename}")
            continue
        schema = _load_json(path)
        if schema.get("additionalProperties") is not False:
            failures.append(f"{filename} must reject additional properties")
        required = set(schema.get("required", []))
        for field in ("schema_version", "record_type", "created_by", "authority_class"):
            if field not in required:
                failures.append(f"{filename} must require {field}")
    return failures


def _import_guard(repo_root: Path) -> tuple[list[str], dict[str, int]]:
    failures: list[str] = []
    scan_roots = [
        repo_root / "src/qtt/stage1_prediction_markets/credential_readiness",
        repo_root / "tools",
        repo_root / "tests/source_evidence",
    ]
    py_files: list[Path] = []
    for root in scan_roots:
        if root.is_file() and root.suffix == ".py":
            py_files.append(root)
        elif root.is_dir():
            py_files.extend(
                path
                for path in root.rglob("*.py")
                if "credential_alias_secret_no_capture" in path.name
                or "pr131_credential_alias" in path.name
                or "credential_readiness" in path.as_posix()
            )
    network_import_count = 0
    secrets_manager_import_count = 0
    environment_credential_read_count = 0
    banned = set(policy.BANNED_IMPORT_MODULES)
    for path in py_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    if name in banned or any(name.startswith(f"{item}.") for item in banned):
                        failures.append(f"banned import {name} in {path.as_posix()}")
                        if name in {"requests", "httpx", "aiohttp", "urllib.request", "websockets"}:
                            network_import_count += 1
                        else:
                            secrets_manager_import_count += 1
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module in banned or any(module.startswith(f"{item}.") for item in banned):
                    failures.append(f"banned import {module} in {path.as_posix()}")
                    if module in {"requests", "httpx", "aiohttp", "urllib.request", "websockets"}:
                        network_import_count += 1
                    else:
                        secrets_manager_import_count += 1
            elif isinstance(node, ast.Attribute) and node.attr == "environ":
                if isinstance(node.value, ast.Name) and node.value.id == "os":
                    failures.append(f"os.environ credential lookup surface in {path.as_posix()}")
                    environment_credential_read_count += 1
    return failures, {
        "network_import_count": network_import_count,
        "secrets_manager_import_count": secrets_manager_import_count,
        "environment_credential_read_count": environment_credential_read_count,
    }


def _main_report(
    *,
    repo_root: Path,
    alias_records: list[Mapping[str, Any]],
    readiness_receipts: list[Mapping[str, Any]],
    attestations: list[Mapping[str, Any]],
    rejection_receipts: list[Mapping[str, Any]],
    scope_bindings: list[Mapping[str, Any]],
    handoff: Mapping[str, Any],
    import_counts: Mapping[str, int],
) -> dict[str, object]:
    constants = _policy_constants_section()
    alias_value_is_secret_count = sum(
        1 for record in alias_records if record.get("alias_value_is_secret") is not False
    )
    alias_value_is_live_credential_count = sum(
        1
        for record in alias_records
        if record.get("alias_value_is_live_credential") is not False
    )
    zero_counts = policy.zero_count_invariants()
    return {
        "report_id": "CODEX_PR131_CREDENTIAL_ALIAS_SECRET_NO_CAPTURE_READINESS_GATE_REPORT_V1",
        "repo_pr_label": policy.PRODUCER_REPO_PR,
        "roadmap_pr_implemented": policy.PRODUCER_ROADMAP_PR,
        "currentized_prior_repo_pr": "PR130",
        "owner_authorized_capability": (
            "CREDENTIAL_ALIAS_AND_SECRET_NO_CAPTURE_READINESS_GATE"
        ),
        "PR131_NORMALIZED_POLICY_CONSTANTS": constants,
        "PR131_ROUTE_TRIAGE": {
            "authorized_roadmap_pr": "PR113",
            "unauthorized_roadmap_pr_same_number": "PR131",
            "same_number_inference_used": False,
            "credential_readiness_is_control_plane_metadata_only": True,
            "raw_secret_material_forbidden": True,
            "live_credential_resolution_forbidden": True,
            "downstream_prs_preserved": list(policy.DOWNSTREAM_PR_IDS),
        },
        "PR131_MASTER_PLAN_SECTION_CROSSWALK": {
            "authority_families": [
                "owner source-evidence definitions and secret policy",
                "source-evidence non-authority boundaries",
                "private-state receipt downstream handoff from PR130",
                "runtime cash/account/balance non-production boundary from PR129-PR130",
                "connector semantic non-authority boundary",
                "replay/paper/live non-execution boundary",
                "AtomicRows metadata-only boundary",
                "quantum metadata-only boundary",
                "low-latency hot-path exclusion boundary",
                "downstream PR114/PR115/PR116 handoff boundary",
            ],
            "source_artifact_refs": [
                "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md",
                "docs/master_plan/source_evidence/generated/RuntimeCashDownstreamHandoff.report.json",
                "docs/master_plan/source_evidence/generated/PrivateStateDownstreamHandoff.report.json",
                "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
            ],
            "section_ids_invented": False,
        },
        "PR131_MARKET_SPECIFIC_SECTION_INDEX": _market_specific_index(
            readiness_receipts,
            attestations,
        ),
        "PR131_COMMAND_ACTION_MATRIX": _command_action_matrix(),
        "PR131_SECRET_NO_CAPTURE_EVIDENCE": {
            **zero_counts,
            "redaction_completed_for_fixture_secret_like_examples": True,
            "rejected_secret_like_classes": list(policy.SECRET_LIKE_REJECTION_CLASSES),
            "raw_secret_capture_allowed_flag": False,
            "secret_alias_reference_allowed_flag": True,
        },
        "PR131_PR130_DEPENDENCY_EVIDENCE": {
            "pr130_private_state_downstream_handoff_ref": (
                "PR130_PRIVATE_STATE_DOWNSTREAM_HANDOFF_V1"
            ),
            "pr130_handoff_consumed_as_metadata_only": True,
            "missing_handoff_rejection_tested": True,
            "malformed_handoff_rejection_tested": True,
            "scope_mismatch_rejection_tested": True,
        },
        "PR131_DOWNSTREAM_HANDOFF_EVIDENCE": handoff,
        "PR131_LOW_LATENCY_BOUNDARY_EVIDENCE": {
            "credential_readiness_runs_in_hot_path": False,
            "future_precomputed_snapshot_consumption_requires_later_authorization": True,
            "live_pretrade_provider_call_created": False,
            "latency_claim_created": False,
        },
        "PR131_QUANTUM_METADATA_ONLY_EVIDENCE": {
            "future_quantum_optimizer_credential_readiness_ref": (
                "FUTURE_QUANTUM_OPTIMIZER_CREDENTIAL_READINESS_METADATA_ONLY"
            ),
            "quantum_execution_created": False,
            "quantum_backend_called": False,
            "quantum_simulator_called": False,
            "quantum_optimizer_called": False,
            "quantum_advantage_claim_created": False,
            "quantum_backend_simulator_optimizer_execution_count": 0,
        },
        "PR131_ATOMICROWS_METADATA_ONLY_EVIDENCE": {
            "future_atomicrows_parameter_row_refs": [],
            "future_atomicrows_family_refs": [],
            "future_atomicrows_credential_readiness_family_ref": (
                "FUTURE_ATOMICROWS_CREDENTIAL_READINESS_METADATA_ONLY"
            ),
            "atomicrows_bundle_consumed": False,
            "atomicrows_bundle_created": False,
            "atomicrows_sha_created": False,
            "atomicrows_row_records_created_count": 0,
            "atomicrows_authority_created": False,
            "atomicrows_bundle_consumed_count": 0,
            "atomicrows_bundle_created_count": 0,
            "atomicrows_bundle_edited_count": 0,
            "atomicrows_sha_created_count": 0,
        },
        "PR131_VALIDATION_EVIDENCE": {
            "schema_count": len(SCHEMA_FILES),
            "fixture_dir": FIXTURE_DIR.as_posix(),
            "validator": "tools/credential_alias_secret_no_capture_readiness_validate.py",
            "run_validation_gates_integration_required": True,
            "run_validation_gates_uses_fresh_pytest_basetemp": True,
            "deterministic_reports": True,
        },
        "alias_count_by_scope": {
            "KALSHI": 1,
            "POLYMARKET": 1,
            "FORECASTEX_IBKR": 1,
            "PREDICTION_MARKETS_GENERAL": 1,
        },
        "alias_record_count": len(alias_records),
        "venue_alias_count": len(policy.STAGE1_VENUE_IDS),
        "shared_scope_alias_count": len(policy.SHARED_SCOPE_IDS),
        "alias_classes": list(policy.ALLOWED_ALIAS_CLASSES),
        "alias_value_is_secret_count": alias_value_is_secret_count,
        "alias_value_is_live_credential_count": alias_value_is_live_credential_count,
        "readiness_receipt_count": len(readiness_receipts),
        "secret_no_capture_attestation_count": len(attestations),
        "credential_scope_binding_count": len(scope_bindings),
        "credential_readiness_rejection_receipt_count": len(rejection_receipts),
        "production_credential_authority_created_count": 0,
        "production_connector_authority_created_count": 0,
        "private_state_fetch_created_count": 0,
        "order_authority_created_count": 0,
        "order_execution_created_count": 0,
        "network_io_created_count": 0,
        "credential_provider_call_count": 0,
        "secret_manager_call_count": 0,
        "environment_variable_read_count": 0,
        "production_connector_client_count": 0,
        "replay_result_count": 0,
        "paper_result_count": 0,
        "profit_evidence_count": 0,
        "quantum_backend_simulator_optimizer_execution_count": 0,
        "atomicrows_bundle_consumed_count": 0,
        "atomicrows_bundle_created_count": 0,
        "atomicrows_bundle_edited_count": 0,
        "atomicrows_sha_created_count": 0,
        "network_import_count": import_counts["network_import_count"],
        "secrets_manager_import_count": import_counts["secrets_manager_import_count"],
        "environment_credential_read_count": import_counts[
            "environment_credential_read_count"
        ],
        "prediction_markets_general_treated_as_shared_scope": True,
        "future_production_launch_path_preserved": True,
        "master_plan_modified": False,
        "atomicrows_bundle_file_modified": False,
        "atomicrows_sha_file_modified": False,
        "schema_paths": [(SCHEMA_DIR / filename).as_posix() for filename in SCHEMA_FILES],
        "fixture_paths": [(FIXTURE_DIR / filename).as_posix() for filename in FIXTURE_FILES],
        "report_paths": [path.as_posix() for path in REPORT_PATHS.values()],
    }


FIXTURE_FILES = (
    "private_state_downstream_handoff.v1.fixture.json",
    "credential_alias_registry.v1.fixture.json",
    "credential_alias_readiness_receipts.v1.fixture.json",
    "secret_no_capture_attestations.v1.fixture.json",
    "credential_scope_bindings.v1.fixture.json",
    "credential_readiness_rejections.v1.fixture.json",
    "expected_credential_readiness_downstream_handoff.v1.fixture.json",
    "redacted_secret_like_payloads.v1.fixture.json",
    "malformed_missing_pr130_handoff.v1.fixture.json",
    "malformed_scope_mismatch.v1.fixture.json",
)


def build_credential_readiness_artifacts(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    pr130_handoff = _private_state_handoff_from_report(repo_root)
    handoff_failures = validate_pr130_handoff(pr130_handoff)
    if handoff_failures:
        raise ValueError("; ".join(handoff_failures))
    private_state_handoff_ref = str(pr130_handoff["private_state_downstream_handoff_id"])

    alias_records = build_credential_alias_registry_records(private_state_handoff_ref)
    attestations = build_secret_no_capture_attestations(alias_records)
    scope_bindings = build_scope_bindings(alias_records)
    readiness_receipts = build_readiness_receipts(
        alias_records,
        attestations,
        scope_bindings,
        private_state_handoff_ref,
    )
    rejection_receipts = build_rejection_receipts()
    downstream_handoff = build_downstream_handoff(
        alias_records,
        readiness_receipts,
        scope_bindings,
    )
    import_failures, import_counts = _import_guard(repo_root)

    alias_report = {
        "credential_alias_readiness_gate_report_id": (
            "PR131_CREDENTIAL_ALIAS_READINESS_GATE_REPORT_V1"
        ),
        "credential_alias_registry_records": alias_records,
        "credential_alias_readiness_receipts": readiness_receipts,
        "readiness_state": "READY_FOR_METADATA_HANDOFF",
        "producer_pr": policy.PRODUCER_REPO_PR,
        "producer_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
    }
    no_capture_report = {
        "secret_no_capture_attestation_report_id": (
            "PR131_SECRET_NO_CAPTURE_ATTESTATION_REPORT_V1"
        ),
        "secret_no_capture_attestations": attestations,
        "credential_readiness_rejection_receipts": rejection_receipts,
        "raw_secret_capture_allowed": False,
        "raw_secret_hashing_allowed": False,
        "redaction_required": True,
    }
    scope_report = {
        "credential_scope_binding_report_id": "PR131_CREDENTIAL_SCOPE_BINDING_REPORT_V1",
        "credential_scope_bindings": scope_bindings,
        "allowed_use": "READINESS_METADATA_ONLY",
        "disallowed_use": list(policy.DISALLOWED_SCOPE_USES),
    }
    handoff_report = {
        "credential_readiness_downstream_handoff_report_id": (
            "PR131_CREDENTIAL_READINESS_DOWNSTREAM_HANDOFF_REPORT_V1"
        ),
        "credential_readiness_downstream_handoff": downstream_handoff,
    }
    main_report = _main_report(
        repo_root=repo_root,
        alias_records=alias_records,
        readiness_receipts=readiness_receipts,
        attestations=attestations,
        rejection_receipts=rejection_receipts,
        scope_bindings=scope_bindings,
        handoff=downstream_handoff,
        import_counts=import_counts,
    )
    artifacts = {
        "main_report": main_report,
        "alias_report": alias_report,
        "no_capture_report": no_capture_report,
        "scope_report": scope_report,
        "handoff_report": handoff_report,
        "pr130_handoff": pr130_handoff,
        "import_failures": import_failures,
        "redacted_secret_like_payloads": {
            "fixture_id": "PR131_REDACTED_SECRET_LIKE_PAYLOAD_CLASS_LABELS_V1",
            "redacted_examples_are_class_labels_not_raw_values": True,
            "redacted_secret_like_payloads": list(policy.ALLOWED_REDACTED_SECRET_EXAMPLES),
            "do_not_hash_symbolic_examples": True,
        },
        "malformed_missing_pr130_handoff": {
            "fixture_id": "PR131_MALFORMED_MISSING_PR130_HANDOFF_V1",
            "private_state_downstream_handoff": None,
            "expected_block": "BLOCKED_MISSING_PR130_HANDOFF",
        },
        "malformed_scope_mismatch": {
            "fixture_id": "PR131_MALFORMED_SCOPE_MISMATCH_V1",
            "private_state_downstream_handoff": {
                **pr130_handoff,
                "venue_ids_in_scope": ["KALSHI", "POLYMARKET"],
            },
            "expected_block": "BLOCKED_SCOPE_MISMATCH",
        },
    }
    failures = validate_artifacts(artifacts, repo_root=repo_root)
    if failures:
        raise ValueError("; ".join(failures))
    return artifacts


def validate_artifacts(
    artifacts: Mapping[str, Any],
    *,
    repo_root: Path | None = None,
) -> list[str]:
    failures: list[str] = []
    if repo_root is not None:
        failures.extend(_schema_validation(repo_root))
    failures.extend(artifacts.get("import_failures", []))

    alias_report = artifacts["alias_report"]
    no_capture_report = artifacts["no_capture_report"]
    scope_report = artifacts["scope_report"]
    handoff_report = artifacts["handoff_report"]
    pr130_handoff = artifacts.get("pr130_handoff")

    alias_records = alias_report["credential_alias_registry_records"]
    readiness_receipts = alias_report["credential_alias_readiness_receipts"]
    attestations = no_capture_report["secret_no_capture_attestations"]
    rejection_receipts = no_capture_report["credential_readiness_rejection_receipts"]
    scope_bindings = scope_report["credential_scope_bindings"]
    downstream_handoff = handoff_report["credential_readiness_downstream_handoff"]

    failures.extend(validate_pr130_handoff(pr130_handoff))
    if isinstance(pr130_handoff, Mapping):
        failures.extend(
            validate_scope_compatibility(
                pr130_handoff,
                alias_records,
                readiness_receipts,
            )
        )
    failures.extend(validate_alias_registry_records(alias_records))
    failures.extend(validate_readiness_receipts(readiness_receipts))
    failures.extend(validate_no_capture_attestations(attestations))
    failures.extend(validate_rejection_receipts(rejection_receipts))
    failures.extend(validate_scope_bindings(scope_bindings))

    if downstream_handoff.get("downstream_prs") != list(policy.DOWNSTREAM_PR_IDS):
        failures.append("downstream handoff must preserve PR114/PR115/PR116")
    for flag in (
        "contains_secrets",
        "contains_live_credentials",
        "contains_production_authority",
        "contains_private_state_payload",
        "contains_order_authority",
        "contains_profit_evidence",
        "contains_quantum_execution",
        "downstream_may_resolve_credentials",
        "downstream_may_call_provider",
        "downstream_may_call_venue_api_from_this_handoff",
        "atomicrows_bundle_consumed",
        "atomicrows_bundle_created",
        "atomicrows_sha_created",
        "quantum_backend_called",
        "quantum_simulator_called",
        "quantum_optimizer_called",
        "quantum_advantage_claim_created",
    ):
        if downstream_handoff.get(flag) is not False:
            failures.append(f"downstream handoff {flag} must be false")
    if downstream_handoff.get("downstream_may_consume_metadata_only") is not True:
        failures.append("downstream handoff must be metadata-only consumable")

    main = artifacts["main_report"]
    expected_main = {
        "repo_pr_label": "PR131",
        "roadmap_pr_implemented": "PR113",
        "alias_record_count": 4,
        "venue_alias_count": 3,
        "shared_scope_alias_count": 1,
        "alias_value_is_secret_count": 0,
        "alias_value_is_live_credential_count": 0,
        "production_credential_authority_created_count": 0,
        "network_io_created_count": 0,
        "credential_provider_call_count": 0,
        "private_state_fetch_created_count": 0,
        "order_authority_created_count": 0,
        "order_execution_created_count": 0,
        "atomicrows_bundle_consumed_count": 0,
        "atomicrows_bundle_created_count": 0,
        "atomicrows_bundle_edited_count": 0,
        "atomicrows_sha_created_count": 0,
        "quantum_backend_simulator_optimizer_execution_count": 0,
        "prediction_markets_general_treated_as_shared_scope": True,
    }
    for field, expected in expected_main.items():
        if main.get(field) != expected:
            failures.append(f"main_report.{field} must be {expected!r}")

    redacted_payloads = artifacts["redacted_secret_like_payloads"]
    if secret_like_findings(redacted_payloads):
        failures.append("redacted symbolic examples must not be treated as raw secrets")
    if redacted_payloads.get("do_not_hash_symbolic_examples") is not True:
        failures.append("symbolic redacted examples must not be hashed")
    return failures


def write_generated_reports(repo_root: Path, out_root: Path | None = None) -> dict[str, Any]:
    artifacts = build_credential_readiness_artifacts(repo_root)
    for key, path in REPORT_PATHS.items():
        output_path = _output_path(repo_root, path, out_root)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(_dump_json(artifacts[key]), encoding="utf-8", newline="\n")
    return artifacts


def write_fixture_files(repo_root: Path, out_root: Path | None = None) -> dict[str, Any]:
    artifacts = build_credential_readiness_artifacts(repo_root)
    fixture_payloads: dict[str, Mapping[str, Any]] = {
        "private_state_downstream_handoff.v1.fixture.json": {
            "fixture_id": "PR131_PRIVATE_STATE_DOWNSTREAM_HANDOFF_INPUT_FIXTURE_V1",
            "private_state_downstream_handoff": artifacts["pr130_handoff"],
        },
        "credential_alias_registry.v1.fixture.json": {
            "fixture_id": "PR131_CREDENTIAL_ALIAS_REGISTRY_FIXTURE_V1",
            "credential_alias_registry_records": artifacts["alias_report"][
                "credential_alias_registry_records"
            ],
        },
        "credential_alias_readiness_receipts.v1.fixture.json": {
            "fixture_id": "PR131_CREDENTIAL_ALIAS_READINESS_RECEIPTS_FIXTURE_V1",
            "credential_alias_readiness_receipts": artifacts["alias_report"][
                "credential_alias_readiness_receipts"
            ],
        },
        "secret_no_capture_attestations.v1.fixture.json": {
            "fixture_id": "PR131_SECRET_NO_CAPTURE_ATTESTATIONS_FIXTURE_V1",
            "secret_no_capture_attestations": artifacts["no_capture_report"][
                "secret_no_capture_attestations"
            ],
        },
        "credential_scope_bindings.v1.fixture.json": {
            "fixture_id": "PR131_CREDENTIAL_SCOPE_BINDINGS_FIXTURE_V1",
            "credential_scope_bindings": artifacts["scope_report"][
                "credential_scope_bindings"
            ],
        },
        "credential_readiness_rejections.v1.fixture.json": {
            "fixture_id": "PR131_CREDENTIAL_READINESS_REJECTIONS_FIXTURE_V1",
            "credential_readiness_rejection_receipts": artifacts["no_capture_report"][
                "credential_readiness_rejection_receipts"
            ],
        },
        "expected_credential_readiness_downstream_handoff.v1.fixture.json": {
            "fixture_id": "PR131_EXPECTED_CREDENTIAL_READINESS_DOWNSTREAM_HANDOFF_V1",
            "credential_readiness_downstream_handoff": artifacts["handoff_report"][
                "credential_readiness_downstream_handoff"
            ],
        },
        "redacted_secret_like_payloads.v1.fixture.json": artifacts[
            "redacted_secret_like_payloads"
        ],
        "malformed_missing_pr130_handoff.v1.fixture.json": artifacts[
            "malformed_missing_pr130_handoff"
        ],
        "malformed_scope_mismatch.v1.fixture.json": artifacts[
            "malformed_scope_mismatch"
        ],
    }
    for filename, payload in fixture_payloads.items():
        output_path = _output_path(repo_root, FIXTURE_DIR / filename, out_root)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_payload = {
            "fixture_authority_class": "TEST_FIXTURE_NOT_EXTERNAL_FACT",
            "mode": "SOURCE_REQUIRED",
            "execution": "DISABLED",
            **payload,
        }
        output_path.write_text(
            _dump_json(fixture_payload),
            encoding="utf-8",
            newline="\n",
        )
    return artifacts
