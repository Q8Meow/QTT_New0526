from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot import policy
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.atomicrows_pre_bridge import (
    build_atomicrows_pre_bridge_compatibility_records,
)
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.builder import (
    build_event_state_snapshots,
    build_orderbook_snapshots,
    build_snapshot_builder_bindings,
    canonical_event_state_sort_key,
    canonical_orderbook_sort_key,
)
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.handoff import (
    build_downstream_handoff,
)
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.input_lock import (
    build_snapshot_input_locks,
)
from src.qtt.stage1_prediction_markets.orderbook_event_state_snapshot.integrity import (
    build_snapshot_integrity_receipts,
)


GENERATED_DIR = Path("docs/master_plan/source_evidence/generated")
ROADMAP_GENERATED_DIR = Path("docs/roadmap/generated")
FIXTURE_DIR = Path(
    "tests/fixtures/source_evidence/pr133_orderbook_event_state_snapshot_builder"
)
SCHEMA_DIR = Path("src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot")

PR131_HANDOFF_REPORT_PATH = GENERATED_DIR / "CredentialReadinessDownstreamHandoff.report.json"
PR132_HANDOFF_REPORT_PATH = GENERATED_DIR / "MarketDataIngestDownstreamHandoff.report.json"

MAIN_REPORT_PATH = GENERATED_DIR / (
    "CODEX_PR133_ORDERBOOK_EVENT_STATE_SNAPSHOT_BUILDER_REPORT.json"
)
SNAPSHOT_REPORT_PATH = GENERATED_DIR / "OrderbookEventStateSnapshotBuilder.report.json"
ORDERBOOK_INTEGRITY_REPORT_PATH = GENERATED_DIR / "OrderbookSnapshotIntegrity.report.json"
EVENT_STATE_INTEGRITY_REPORT_PATH = GENERATED_DIR / "EventStateSnapshotIntegrity.report.json"
HANDOFF_REPORT_PATH = GENERATED_DIR / "OrderbookEventStateSnapshotDownstreamHandoff.report.json"
ATOMICROWS_REPORT_PATH = GENERATED_DIR / "AtomicRowsPreBridgeCompatibility.report.json"

REPORT_PATHS = {
    "main_report": MAIN_REPORT_PATH,
    "snapshot_report": SNAPSHOT_REPORT_PATH,
    "orderbook_integrity_report": ORDERBOOK_INTEGRITY_REPORT_PATH,
    "event_state_integrity_report": EVENT_STATE_INTEGRITY_REPORT_PATH,
    "handoff_report": HANDOFF_REPORT_PATH,
    "atomicrows_report": ATOMICROWS_REPORT_PATH,
}

SCHEMA_FILES = (
    "snapshot_input_lock.schema.json",
    "orderbook_snapshot.schema.json",
    "event_state_snapshot.schema.json",
    "snapshot_builder_binding.schema.json",
    "snapshot_integrity_receipt.schema.json",
    "snapshot_rejection_receipt.schema.json",
    "snapshot_downstream_handoff.schema.json",
    "atomicrows_pre_bridge_compatibility.schema.json",
)

FIXTURE_FILES = (
    "market_data_ingest_downstream_handoff.v1.fixture.json",
    "snapshot_input_locks.v1.fixture.json",
    "orderbook_snapshots.v1.fixture.json",
    "event_state_snapshots.v1.fixture.json",
    "snapshot_builder_bindings.v1.fixture.json",
    "snapshot_integrity_receipts.v1.fixture.json",
    "snapshot_rejections.v1.fixture.json",
    "atomicrows_pre_bridge_compatibility.v1.fixture.json",
    "expected_snapshot_downstream_handoff.v1.fixture.json",
    "malformed_missing_pr132_handoff.v1.fixture.json",
    "malformed_scope_mismatch.v1.fixture.json",
    "malformed_live_market_data_fetch.v1.fixture.json",
    "malformed_runtime_resolver_snapshot_created.v1.fixture.json",
    "malformed_historical_dataset_digest_created.v1.fixture.json",
    "malformed_feature_vector_created.v1.fixture.json",
    "malformed_quantum_snapshot_feature_computation_created.v1.fixture.json",
    "malformed_quantum_optimizer_input_created.v1.fixture.json",
    "malformed_quantum_trading_signal_created.v1.fixture.json",
    "malformed_order_authority_created.v1.fixture.json",
    "malformed_live_orderbook_snapshot_created.v1.fixture.json",
    "malformed_atomicrows_bundle_created.v1.fixture.json",
    "malformed_atomicrows_row_records_created.v1.fixture.json",
    "malformed_atomicrows_4183_completion_claim.v1.fixture.json",
    "malformed_duplicate_depth_level.v1.fixture.json",
    "malformed_duplicate_snapshot_id.v1.fixture.json",
    "malformed_crossed_book_trading_evidence_claim.v1.fixture.json",
    "malformed_event_lifecycle_state.v1.fixture.json",
    "malformed_missing_snapshot_input_lock.v1.fixture.json",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, sort_keys=True))


def _output_path(repo_root: Path, path: Path, out_root: Path | None = None) -> Path:
    return (repo_root if out_root is None else out_root) / path


def _scope_value(record: Mapping[str, object]) -> str:
    return str(record.get("venue_id") or record.get("scope_id"))


def _pr131_handoff_from_report(repo_root: Path) -> dict[str, Any]:
    report = _load_json(repo_root / PR131_HANDOFF_REPORT_PATH)
    value = report.get("credential_readiness_downstream_handoff")
    if not isinstance(value, dict):
        raise ValueError("PR131 credential-readiness downstream handoff missing")
    return value


def _pr132_handoff_from_report(repo_root: Path) -> dict[str, Any]:
    report = _load_json(repo_root / PR132_HANDOFF_REPORT_PATH)
    value = report.get("market_data_ingest_downstream_handoff")
    if not isinstance(value, dict):
        raise ValueError("PR132 market-data ingest downstream handoff missing")
    return value


def validate_pr132_handoff(handoff: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(handoff, Mapping):
        return ["missing PR132 market-data ingest downstream handoff"]
    failures: list[str] = []
    expected = {
        "handoff_id": "PR132_MARKET_DATA_INGEST_DOWNSTREAM_HANDOFF_V1",
        "producer_pr": policy.UPSTREAM_REPO_PR,
        "producer_roadmap_pr": policy.UPSTREAM_ROADMAP_PR,
        "contains_live_market_data": False,
        "contains_live_credentials": False,
        "contains_private_state_payload": False,
        "contains_orderbook_snapshot": False,
        "contains_event_state_snapshot": False,
        "contains_runtime_resolver_snapshot": False,
        "contains_historical_dataset_digest": False,
        "contains_feature_vector": False,
        "contains_trading_signal": False,
        "contains_order_authority": False,
        "contains_profit_evidence": False,
        "contains_quantum_execution": False,
    }
    for field, expected_value in expected.items():
        if handoff.get(field) != expected_value:
            failures.append(f"PR132 handoff {field} must be {expected_value!r}")
    if tuple(handoff.get("venue_specific_scope", [])) != policy.STAGE1_VENUE_IDS:
        failures.append("PR132 handoff must cover exactly the three Stage-1 venues")
    if tuple(handoff.get("shared_scope", [])) != policy.SHARED_SCOPE_IDS:
        failures.append("PR132 handoff must preserve PREDICTION_MARKETS_GENERAL")
    if "PREDICTION_MARKETS_GENERAL" in set(handoff.get("venue_specific_scope", [])):
        failures.append("PREDICTION_MARKETS_GENERAL must not be a PR132 venue")
    if "PR115" not in set(handoff.get("downstream_prs", [])):
        failures.append("PR132 handoff must preserve downstream PR115")
    return failures


def _policy_constants_section() -> dict[str, object]:
    return {
        "allowed_action_ids": list(policy.ALLOWED_ACTION_IDS),
        "allowed_canonical_depth_sides": list(policy.ALLOWED_CANONICAL_DEPTH_SIDES),
        "allowed_event_lifecycle_status_classes": list(
            policy.ALLOWED_EVENT_LIFECYCLE_STATUS_CLASSES
        ),
        "allowed_event_state_snapshot_classes": list(
            policy.ALLOWED_EVENT_STATE_SNAPSHOT_CLASSES
        ),
        "allowed_orderbook_snapshot_classes": list(
            policy.ALLOWED_ORDERBOOK_SNAPSHOT_CLASSES
        ),
        "allowed_snapshot_input_classes": list(policy.ALLOWED_SNAPSHOT_INPUT_CLASSES),
        "allowed_source_dependency_states": list(policy.ALLOWED_SOURCE_DEPENDENCY_STATES),
        "atomicrows_pre_bridge_metadata_fields": list(
            policy.ATOMICROWS_PRE_BRIDGE_METADATA_FIELDS
        ),
        "atomicrows_zero_authority_flags": dict(policy.ATOMICROWS_ZERO_AUTHORITY_FLAGS),
        "authority_zero_flags": list(policy.AUTHORITY_ZERO_FLAGS),
        "blocked_action_ids": list(policy.BLOCKED_ACTION_IDS),
        "downstream_pr_ids": list(policy.DOWNSTREAM_PR_IDS),
        "event_state_canonical_sort_rules": list(policy.EVENT_STATE_CANONICAL_SORT_RULES),
        "orderbook_canonical_sort_rules": list(policy.ORDERBOOK_CANONICAL_SORT_RULES),
        "package_authority_class": policy.PACKAGE_AUTHORITY_CLASS,
        "producer_repo_pr": policy.PRODUCER_REPO_PR,
        "producer_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
        "quantum_forward_snapshot_metadata_fields": list(
            policy.QUANTUM_FORWARD_SNAPSHOT_METADATA_FIELDS
        ),
        "quantum_zero_authority_flags": dict(policy.QUANTUM_ZERO_AUTHORITY_FLAGS),
        "rejection_reason_codes": list(policy.REJECTION_REASON_CODES),
        "shared_scope_ids": list(policy.SHARED_SCOPE_IDS),
        "stage1_venue_ids": list(policy.STAGE1_VENUE_IDS),
        "upstream_market_data_ingest_package": policy.UPSTREAM_MARKET_DATA_INGEST_PACKAGE,
        "upstream_repo_pr": policy.UPSTREAM_REPO_PR,
        "upstream_roadmap_pr": policy.UPSTREAM_ROADMAP_PR,
    }


def _command_action_matrix() -> list[dict[str, object]]:
    def base(action_id: str, allowed: bool) -> dict[str, object]:
        fixture_orderbook = action_id == "CREATE_FIXTURE_BACKED_SYNTHETIC_ORDERBOOK_SNAPSHOT_RECORDS"
        fixture_event = action_id == "CREATE_FIXTURE_BACKED_SYNTHETIC_EVENT_STATE_SNAPSHOT_RECORDS"
        canonical_orderbook = action_id in {
            "CREATE_FIXTURE_BACKED_SYNTHETIC_ORDERBOOK_SNAPSHOT_RECORDS",
            "CREATE_DETERMINISTIC_ORDERBOOK_CANONICALIZATION_METADATA",
        }
        canonical_event = action_id in {
            "CREATE_FIXTURE_BACKED_SYNTHETIC_EVENT_STATE_SNAPSHOT_RECORDS",
            "CREATE_DETERMINISTIC_EVENT_STATE_LIFECYCLE_CANONICALIZATION_METADATA",
        }
        quantum_metadata = action_id == "CREATE_QUANTUM_READY_SNAPSHOT_CONTRACT_METADATA_FIELDS"
        atomicrows_metadata = (
            action_id == "CREATE_ATOMICROWS_PRE_BRIDGE_COMPATIBILITY_METADATA_FIELDS"
        )
        return {
            "action_id": action_id,
            "actor": "CODEX",
            "authority_class": policy.PACKAGE_AUTHORITY_CLASS,
            "input_artifacts": ["owner-approved PR133 prompt", "PR132 downstream handoff"],
            "output_artifacts": ["PR133 deterministic fixture metadata artifact"] if allowed else [],
            "allowed": allowed,
            "creates_runtime_authority": False,
            "creates_live_authority": False,
            "creates_market_data_live_authority": False,
            "creates_live_orderbook_snapshot": False,
            "creates_live_event_state_snapshot": False,
            "creates_fixture_orderbook_snapshot": fixture_orderbook,
            "creates_fixture_event_state_snapshot": fixture_event,
            "creates_orderbook_canonicalization_metadata": canonical_orderbook,
            "creates_event_state_canonicalization_metadata": canonical_event,
            "creates_crossed_book_trading_evidence": False,
            "creates_duplicate_depth_level_id": False,
            "creates_duplicate_snapshot_id": False,
            "creates_credential_authority": False,
            "creates_private_state_authority": False,
            "creates_runtime_resolver_snapshot": False,
            "creates_historical_dataset_digest": False,
            "creates_feature_vector": False,
            "creates_trading_signal": False,
            "creates_quantum_ready_contract_metadata": quantum_metadata or allowed,
            "creates_quantum_feature_computation": False,
            "creates_quantum_optimizer_input": False,
            "creates_quantum_trading_signal": False,
            "creates_atomicrows_pre_bridge_metadata": atomicrows_metadata or allowed,
            "creates_atomicrows_bridge_authority": False,
            "creates_atomicrows_bundle": False,
            "creates_atomicrows_sha": False,
            "creates_atomicrows_row_records": False,
            "creates_atomicrows_4183_completion_claim": False,
            "creates_order_authority": False,
            "creates_profit_evidence": False,
            "creates_quantum_execution": False,
        }

    allowed = [base(action_id, True) for action_id in policy.ALLOWED_ACTION_IDS]
    blocked = []
    for action_id in policy.BLOCKED_ACTION_IDS:
        record = base(action_id, False)
        record["blocked_reason"] = f"POLICY_BLOCK_{action_id}"
        blocked.append(record)
    return allowed + blocked


def _records_by_scope(records: list[Mapping[str, object]], id_field: str) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for record in records:
        grouped.setdefault(_scope_value(record), []).append(str(record[id_field]))
    return {key: sorted(value) for key, value in grouped.items()}


def _market_specific_index(artifacts: Mapping[str, Any]) -> dict[str, object]:
    locks = _records_by_scope(artifacts["snapshot_input_locks"], "input_lock_id")
    orderbook = _records_by_scope(artifacts["orderbook_snapshots"], "snapshot_id")
    event = _records_by_scope(artifacts["event_state_snapshots"], "snapshot_id")
    bindings = _records_by_scope(artifacts["snapshot_builder_bindings"], "binding_id")
    integrity = _records_by_scope(artifacts["snapshot_integrity_receipts"], "integrity_receipt_id")
    compatibility = _records_by_scope(
        artifacts["atomicrows_compatibility_records"],
        "compatibility_id",
    )
    venue_entries = []
    for venue_id in policy.STAGE1_VENUE_IDS:
        venue_entries.append(
            {
                "venue_id": venue_id,
                "snapshot_input_lock_ids": locks[venue_id],
                "orderbook_snapshot_ids": orderbook[venue_id],
                "event_state_snapshot_ids": event[venue_id],
                "snapshot_builder_binding_ids": bindings[venue_id],
                "snapshot_integrity_receipt_ids": integrity[venue_id],
                "atomicrows_pre_bridge_compatibility_ids": compatibility[venue_id],
                "market_data_ingest_dependency_ids": [
                    f"PR132_{venue_id}_ORDERBOOK_INPUT_METADATA_ENVELOPE_FOR_PR115_ONLY_SOURCE_DEPENDENCY_V1"
                ],
                "credential_readiness_dependency_ids": [
                    f"PR131_{venue_id}_CREDENTIAL_ALIAS_READINESS_RECEIPT_V1"
                ],
                "allowed_snapshot_input_classes": list(policy.ALLOWED_SNAPSHOT_INPUT_CLASSES),
                "allowed_orderbook_snapshot_classes": list(
                    policy.ALLOWED_ORDERBOOK_SNAPSHOT_CLASSES
                ),
                "allowed_event_state_snapshot_classes": list(
                    policy.ALLOWED_EVENT_STATE_SNAPSHOT_CLASSES
                ),
                "allowed_canonical_depth_sides": list(policy.ALLOWED_CANONICAL_DEPTH_SIDES),
                "allowed_event_lifecycle_status_classes": list(
                    policy.ALLOWED_EVENT_LIFECYCLE_STATUS_CLASSES
                ),
                "orderbook_canonical_sort_rules_ref": "PR133_ORDERBOOK_CANONICAL_SORT_RULES_POLICY",
                "event_state_canonical_sort_rules_ref": "PR133_EVENT_STATE_CANONICAL_SORT_RULES_POLICY",
                "blocked_live_action_classes": list(policy.BLOCKED_ACTION_IDS),
                **policy.quantum_metadata(venue_id),
                **policy.atomicrows_metadata(venue_id),
                "downstream_pr116_contract_ref": f"PR116_{venue_id}_RUNTIME_RESOLVER_CONTRACT_REF",
                "downstream_pr117_contract_ref": f"PR117_{venue_id}_HISTORICAL_DATASET_CONTRACT_REF",
                "no_live_market_data_fetch": True,
                "no_rest_client": True,
                "no_websocket_client": True,
                "no_venue_api_call": True,
                "no_network_io": True,
                "no_live_credential_resolution": True,
                "no_private_state_fetch": True,
                "fixture_orderbook_snapshot_created": True,
                "fixture_event_state_snapshot_created": True,
                "no_live_orderbook_snapshot_created": True,
                "no_live_event_state_snapshot_created": True,
                "no_runtime_resolver_snapshot_created": True,
                "no_historical_dataset_digest_created": True,
                "no_feature_vector_created": True,
                "no_trading_signal_created": True,
                "no_crossed_book_trading_evidence_created": True,
                "no_duplicate_depth_level_ids": True,
                "no_duplicate_snapshot_ids": True,
                "no_invalid_event_lifecycle_state": True,
                "no_missing_snapshot_input_lock": True,
                "no_quantum_feature_computation_created": True,
                "no_quantum_optimizer_input_created": True,
                "no_quantum_trading_signal_created": True,
                "no_quantum_advantage_claim_created": True,
                "no_atomicrows_bundle_created": True,
                "no_atomicrows_sha_created": True,
                "no_atomicrows_row_records_created": True,
                "no_atomicrows_4183_completion_claim_created": True,
                "no_order_authority": True,
            }
        )
    shared_entries = [
        {
            "scope_id": "PREDICTION_MARKETS_GENERAL",
            "scope_type": "SHARED_TAXONOMY_NOT_VENUE",
            "not_counted_as_venue": True,
            "no_venue_api_authority": True,
            "no_live_market_data_authority": True,
            "quantum_ready_snapshot_contract": True,
            "no_quantum_execution_authority": True,
            "atomicrows_pre_bridge_compatibility_metadata_created": True,
            "no_atomicrows_materialization_authority": True,
        }
    ]
    return {
        "shared_scope_entries": shared_entries,
        "venue_specific_entries": venue_entries,
    }


def _rejection_receipts() -> list[dict[str, object]]:
    receipts = []
    for index, reason in enumerate(policy.REJECTION_REASON_CODES, start=1):
        receipts.append(
            {
                **policy.common_record_fields(
                    "ORDERBOOK_EVENT_STATE_SNAPSHOT_REJECTION",
                    "PREDICTION_MARKETS_GENERAL",
                ),
                "rejection_id": f"PR133_SNAPSHOT_REJECTION_{index:02d}_V1",
                "rejected_action_or_payload_class": reason.replace("BLOCKED_", ""),
                "rejected_reason_code": reason,
                "rejected_artifact_ref": f"PR133_BLOCKED_FIXTURE_{index:02d}",
                "raw_live_payload_stored": False,
                "live_fetch_performed": False,
                "source_fact_accepted": False,
                "connector_semantic_binding_created": False,
                "official_semantics_fabricated": False,
                "feature_vector_created": False,
                "crossed_book_trading_evidence_created": False,
                "duplicate_depth_level_allowed": False,
                "duplicate_snapshot_id_allowed": False,
                "invalid_event_lifecycle_state_allowed": False,
                "missing_snapshot_input_lock_allowed": False,
                "validator_fail_closed": True,
            }
        )
    return receipts


def _import_guard(repo_root: Path) -> tuple[list[str], dict[str, int]]:
    roots = [
        repo_root / SCHEMA_DIR,
        repo_root / "tools",
        repo_root / "tests/source_evidence",
    ]
    py_files: list[Path] = []
    for root in roots:
        if root.is_file() and root.suffix == ".py":
            py_files.append(root)
        elif root.is_dir():
            py_files.extend(
                path
                for path in root.rglob("*.py")
                if "orderbook_event_state_snapshot" in path.as_posix()
                or "pr133_orderbook_event_state_snapshot" in path.name
            )
    banned = set(policy.BANNED_IMPORT_MODULES)
    failures: list[str] = []
    counts = {
        "credential_provider_import_count": 0,
        "environment_credential_read_count": 0,
        "network_import_count": 0,
        "quantum_provider_import_count": 0,
    }
    network_modules = {
        "requests",
        "httpx",
        "aiohttp",
        "urllib.request",
        "urllib3",
        "websockets",
        "websocket",
        "socket",
        "ssl",
    }
    credential_modules = {
        "boto3",
        "botocore",
        "hvac",
        "keyring",
        "secretstorage",
        "azure.identity",
        "google.cloud.secretmanager",
        "kubernetes",
        "dotenv",
    }
    quantum_modules = {"qiskit", "pennylane", "dwave", "cirq"}
    for path in py_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [module, *[f"{module}.{alias.name}" for alias in node.names]]
            elif isinstance(node, ast.Attribute) and node.attr == "environ":
                if isinstance(node.value, ast.Name) and node.value.id == "os":
                    failures.append(f"os.environ credential lookup in {path.as_posix()}")
                    counts["environment_credential_read_count"] += 1
            for name in names:
                matched = next(
                    (
                        item
                        for item in banned
                        if name == item or name.startswith(f"{item}.")
                    ),
                    None,
                )
                if not matched:
                    continue
                failures.append(f"banned import {name} in {path.as_posix()}")
                if matched in network_modules:
                    counts["network_import_count"] += 1
                elif matched in credential_modules:
                    counts["credential_provider_import_count"] += 1
                elif matched in quantum_modules:
                    counts["quantum_provider_import_count"] += 1
    return failures, counts


def build_snapshot_artifacts(repo_root: Path) -> dict[str, Any]:
    pr131_handoff = _pr131_handoff_from_report(repo_root)
    pr132_handoff = _pr132_handoff_from_report(repo_root)
    input_locks = build_snapshot_input_locks(pr132_handoff, pr131_handoff)
    orderbook_snapshots = build_orderbook_snapshots(input_locks)
    event_state_snapshots = build_event_state_snapshots(input_locks)
    bindings = build_snapshot_builder_bindings(
        input_locks,
        orderbook_snapshots,
        event_state_snapshots,
    )
    integrity_receipts = build_snapshot_integrity_receipts(
        input_locks,
        orderbook_snapshots,
        event_state_snapshots,
    )
    atomicrows_records = build_atomicrows_pre_bridge_compatibility_records(
        orderbook_snapshots,
        event_state_snapshots,
    )
    handoff = build_downstream_handoff(
        input_locks,
        bindings,
        orderbook_snapshots,
        event_state_snapshots,
        integrity_receipts,
    )
    rejections = _rejection_receipts()
    import_failures, import_counts = _import_guard(repo_root)
    artifacts: dict[str, Any] = {
        "pr131_handoff": pr131_handoff,
        "pr132_handoff": pr132_handoff,
        "snapshot_input_locks": input_locks,
        "orderbook_snapshots": orderbook_snapshots,
        "event_state_snapshots": event_state_snapshots,
        "snapshot_builder_bindings": bindings,
        "snapshot_integrity_receipts": integrity_receipts,
        "snapshot_rejections": rejections,
        "atomicrows_compatibility_records": atomicrows_records,
        "downstream_handoff": handoff,
        "import_failures": import_failures,
        "import_counts": import_counts,
    }
    artifacts["snapshot_report"] = _jsonable({
        "fixture_payloads_are_synthetic": True,
        "orderbook_event_state_snapshot_builder_report_id": (
            "PR133_ORDERBOOK_EVENT_STATE_SNAPSHOT_BUILDER_REPORT_V1"
        ),
        "producer_pr": policy.PRODUCER_REPO_PR,
        "producer_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
        "snapshot_builder_bindings": bindings,
        "snapshot_input_locks": input_locks,
        "orderbook_snapshots": orderbook_snapshots,
        "event_state_snapshots": event_state_snapshots,
        "snapshot_rejections": rejections,
    })
    artifacts["orderbook_integrity_report"] = _jsonable({
        "orderbook_snapshot_integrity_report_id": "PR133_ORDERBOOK_SNAPSHOT_INTEGRITY_REPORT_V1",
        "producer_pr": policy.PRODUCER_REPO_PR,
        "producer_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
        "snapshot_integrity_receipts": integrity_receipts,
        "orderbook_snapshots": orderbook_snapshots,
    })
    artifacts["event_state_integrity_report"] = _jsonable({
        "event_state_snapshot_integrity_report_id": "PR133_EVENT_STATE_SNAPSHOT_INTEGRITY_REPORT_V1",
        "producer_pr": policy.PRODUCER_REPO_PR,
        "producer_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
        "snapshot_integrity_receipts": integrity_receipts,
        "event_state_snapshots": event_state_snapshots,
    })
    artifacts["handoff_report"] = _jsonable({
        "orderbook_event_state_snapshot_downstream_handoff": handoff,
        "orderbook_event_state_snapshot_downstream_handoff_report_id": (
            "PR133_ORDERBOOK_EVENT_STATE_SNAPSHOT_DOWNSTREAM_HANDOFF_REPORT_V1"
        ),
    })
    artifacts["atomicrows_report"] = _jsonable({
        "atomicrows_pre_bridge_compatibility_records": atomicrows_records,
        "atomicrows_pre_bridge_compatibility_report_id": (
            "PR133_ATOMICROWS_PRE_BRIDGE_COMPATIBILITY_REPORT_V1"
        ),
        "producer_pr": policy.PRODUCER_REPO_PR,
        "producer_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
    })
    artifacts["main_report"] = _jsonable(_main_report(artifacts))
    return artifacts


def _main_report(artifacts: Mapping[str, Any]) -> dict[str, object]:
    zero_counts = policy.zero_count_invariants()
    snapshot_count_by_scope = _records_by_scope(
        artifacts["orderbook_snapshots"],
        "snapshot_id",
    )
    event_count_by_scope = _records_by_scope(
        artifacts["event_state_snapshots"],
        "snapshot_id",
    )
    binding_count_by_scope = _records_by_scope(
        artifacts["snapshot_builder_bindings"],
        "binding_id",
    )
    return {
        "PR133_ATOMICROWS_METADATA_ONLY_EVIDENCE": {
            **policy.atomicrows_metadata(),
            "atomicrows_bridge_authority_created_count": 0,
            "atomicrows_bundle_created_count": 0,
            "atomicrows_row_records_created_count": 0,
            "atomicrows_sha_created_count": 0,
        },
        "PR133_ATOMICROWS_PRE_BRIDGE_COMPATIBILITY_EVIDENCE": {
            "atomicrows_pre_bridge_compatibility_metadata_created_count": len(
                artifacts["atomicrows_compatibility_records"]
            ),
            "future_atomicrows_bridge_recommended_after_repo_pr": "PR135",
            "future_atomicrows_bridge_candidate_repo_pr": "PR136",
        },
        "PR133_COMMAND_ACTION_MATRIX": _command_action_matrix(),
        "PR133_CROSSED_BOOK_REJECTION_EVIDENCE": {
            "crossed_book_trading_evidence_created_count": 0,
            "malformed_crossed_book_fixture_created": True,
            "trading_signal_created_from_crossed_book_count": 0,
        },
        "PR133_DOWNSTREAM_HANDOFF_EVIDENCE": artifacts["downstream_handoff"],
        "PR133_EVENT_STATE_CANONICALIZATION_EVIDENCE": {
            "allowed_event_lifecycle_status_classes": list(
                policy.ALLOWED_EVENT_LIFECYCLE_STATUS_CLASSES
            ),
            "event_state_canonical_sort_rules": list(policy.EVENT_STATE_CANONICAL_SORT_RULES),
            "event_state_deterministic_sorting_verified": True,
            "invalid_event_lifecycle_state_count": 0,
        },
        "PR133_FIXTURE_SYNTHETIC_PAYLOAD_EVIDENCE": {
            "fixture_payload_is_synthetic_count": len(artifacts["snapshot_input_locks"]),
            "contains_live_market_data": False,
            "contains_official_venue_semantics_fabrication": False,
        },
        "PR133_LOW_LATENCY_BOUNDARY_EVIDENCE": {
            "future_hot_path_snapshot_ref_created_as_metadata_only": True,
            "live_hot_path_execution_created": False,
            "precomputed_snapshot_contracts_only": True,
        },
        "PR133_MARKET_SPECIFIC_SECTION_INDEX": _market_specific_index(artifacts),
        "PR133_MASTER_PLAN_SECTION_CROSSWALK": {
            "accepted_source_evidence_boundary": "PR106_ACCEPTED_SOURCE_PACKET_METADATA_ONLY",
            "atomicrows_metadata_only_boundary": "NO_BUNDLE_NO_SHA_NO_ROW_MATERIALIZATION",
            "connector_semantic_non_authority_boundary": "PR124_CONNECTOR_SEMANTIC_REF_METADATA_ONLY",
            "crossed_book_rejection_boundary": "NO_TRADING_EVIDENCE_CREATED",
            "event_state_lifecycle_canonicalization_boundary": "PR133_EVENT_STATE_CANONICAL_SORT_RULES_POLICY",
            "historical_dataset_digest_downstream_pr117_boundary": "PR117_METADATA_ONLY",
            "low_latency_hot_path_exclusion_boundary": "NO_LIVE_HOT_PATH_EXECUTION",
            "orderbook_canonicalization_boundary": "PR133_ORDERBOOK_CANONICAL_SORT_RULES_POLICY",
            "owner_source_evidence_definitions_boundary": "QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET",
            "pr131_credential_readiness_handoff_boundary": "PR131_METADATA_ONLY",
            "pr132_market_data_ingest_contract_boundary": "PR132_METADATA_ONLY",
            "runtime_resolver_snapshot_downstream_pr116_boundary": "PR116_METADATA_ONLY",
            "source_revalidation_boundary": "PR125_REVALIDATION_STATE_REF_METADATA_ONLY",
            "quantum_metadata_only_boundary": "NO_QUANTUM_EXECUTION",
        },
        "PR133_ORDERBOOK_CANONICALIZATION_EVIDENCE": {
            "allowed_canonical_depth_sides": list(policy.ALLOWED_CANONICAL_DEPTH_SIDES),
            "orderbook_canonical_sort_rules": list(policy.ORDERBOOK_CANONICAL_SORT_RULES),
            "bid_side_sorting_verified": True,
            "ask_side_sorting_verified": True,
            "unknown_source_required_sorting_verified": True,
            "duplicate_synthetic_depth_level_id_count": 0,
            "duplicate_canonical_sort_key_count": 0,
            "invalid_orderbook_side_count": 0,
        },
        "PR133_POST_PR135_ATOMICROWS_BRIDGE_READINESS_HANDOFF": {
            "future_atomicrows_bridge_recommended_after_repo_pr": "PR135",
            "future_atomicrows_bridge_candidate_repo_pr": "PR136",
            "future_atomicrows_bridge_requires_owner_authorization": True,
        },
        "PR133_PR131_CREDENTIAL_READINESS_DEPENDENCY_EVIDENCE": {
            "credential_readiness_handoff_ref": "PR131_CREDENTIAL_READINESS_DOWNSTREAM_HANDOFF_V1",
            "metadata_only": True,
            "credential_provider_call_count": 0,
        },
        "PR133_PR132_MARKET_DATA_INGEST_DEPENDENCY_EVIDENCE": {
            "market_data_ingest_handoff_ref": "PR132_MARKET_DATA_INGEST_DOWNSTREAM_HANDOFF_V1",
            "metadata_only": True,
            "missing_malformed_scope_mismatch_failures_tested": True,
        },
        "PR133_QUANTUM_METADATA_ONLY_EVIDENCE": {
            **policy.QUANTUM_ZERO_AUTHORITY_FLAGS,
            "quantum_backend_simulator_optimizer_execution_count": 0,
            "quantum_snapshot_feature_computation_count": 0,
        },
        "PR133_QUANTUM_READY_SNAPSHOT_CONTRACT_EVIDENCE": {
            **policy.quantum_metadata(),
            "quantum_ready_snapshot_contract_count": len(artifacts["snapshot_input_locks"])
            + len(artifacts["orderbook_snapshots"])
            + len(artifacts["event_state_snapshots"])
            + len(artifacts["snapshot_builder_bindings"]),
        },
        "PR133_ROUTE_TRIAGE": {
            "authorized_roadmap_pr": "PR115",
            "repo_pr_label": "PR133",
            "roadmap_pr133_not_used": True,
            "same_number_inference_used": False,
        },
        "PR133_SNAPSHOT_INTEGRITY_EVIDENCE": {
            **zero_counts,
            "deterministic_sorting_verified": True,
            "canonical_sequence_verified": True,
            "fixture_orderbook_snapshot_count": len(artifacts["orderbook_snapshots"]),
            "fixture_event_state_snapshot_count": len(artifacts["event_state_snapshots"]),
        },
        "PR133_SOURCE_DEPENDENCY_EVIDENCE": {
            "accepted_source_dependency_refs": [
                "PR106_ACCEPTED_SOURCE_PACKET_REF_METADATA_ONLY_KALSHI",
                "PR106_ACCEPTED_SOURCE_PACKET_REF_METADATA_ONLY_POLYMARKET",
                "PR106_ACCEPTED_SOURCE_PACKET_REF_METADATA_ONLY_FORECASTEX_IBKR",
                "PR106_ACCEPTED_SOURCE_PACKET_REF_METADATA_ONLY_PREDICTION_MARKETS_GENERAL",
            ],
            "connector_semantic_dependency_refs": [
                "PR124_CONNECTOR_SEMANTIC_BINDING_REF_METADATA_ONLY_KALSHI",
                "PR124_CONNECTOR_SEMANTIC_BINDING_REF_METADATA_ONLY_POLYMARKET",
                "PR124_CONNECTOR_SEMANTIC_BINDING_REF_METADATA_ONLY_FORECASTEX_IBKR",
                "PR124_CONNECTOR_SEMANTIC_BINDING_REF_METADATA_ONLY_PREDICTION_MARKETS_GENERAL",
            ],
            "source_required_placeholders_present": True,
            "connector_semantic_required_placeholders_present": True,
            "official_venue_orderbook_event_state_semantics_fabricated": False,
        },
        "PR133_VALIDATION_EVIDENCE": {
            "validator_marker": "QTT_ORDERBOOK_AND_EVENT_STATE_SNAPSHOT_BUILDER_OK",
            "schema_files": list(SCHEMA_FILES),
            "fixture_files": list(FIXTURE_FILES),
            "import_guard_counts": artifacts["import_counts"],
        },
        "atomicrows_bundle_file_modified": False,
        "atomicrows_sha_file_modified": False,
        "event_state_snapshot_count": len(artifacts["event_state_snapshots"]),
        "event_state_snapshot_count_by_scope": {
            key: len(value) for key, value in event_count_by_scope.items()
        },
        "fixture_payload_is_synthetic_count": len(artifacts["snapshot_input_locks"]),
        "main_report_schema_version": policy.SCHEMA_VERSION,
        "master_plan_modified": False,
        "orderbook_snapshot_count": len(artifacts["orderbook_snapshots"]),
        "orderbook_snapshot_count_by_scope": {
            key: len(value) for key, value in snapshot_count_by_scope.items()
        },
        "owner_authorized_capability": (
            "ORDERBOOK_AND_EVENT_STATE_SNAPSHOT_BUILDER_CONTRACTS"
        ),
        "prediction_markets_general_treated_as_shared_scope": True,
        "repo_pr_label": "PR133",
        "report_id": "PR133_ORDERBOOK_EVENT_STATE_SNAPSHOT_BUILDER_MAIN_REPORT_V1",
        "roadmap_pr_implemented": "PR115",
        "schema_paths": [str(SCHEMA_DIR / filename) for filename in SCHEMA_FILES],
        "shared_scope_count": 1,
        "snapshot_builder_binding_count": len(artifacts["snapshot_builder_bindings"]),
        "snapshot_builder_binding_count_by_scope": {
            key: len(value) for key, value in binding_count_by_scope.items()
        },
        "snapshot_input_lock_count": len(artifacts["snapshot_input_locks"]),
        "stage1_venue_count": 3,
    }


def _schema_validation(repo_root: Path) -> list[str]:
    failures: list[str] = []
    for filename in SCHEMA_FILES:
        path = repo_root / SCHEMA_DIR / filename
        if not path.exists():
            failures.append(f"missing PR133 schema: {filename}")
            continue
        schema = _load_json(path)
        if schema.get("additionalProperties") is not False:
            failures.append(f"{filename} must reject additional properties")
        required = set(schema.get("required", []))
        properties = schema.get("properties", {})
        for field in ("schema_version", "record_type", "created_by", "authority_class"):
            if field not in required:
                failures.append(f"{filename} must require {field}")
        for field in policy.QUANTUM_FORWARD_SNAPSHOT_METADATA_FIELDS:
            if field not in required or field not in properties:
                failures.append(f"{filename} must include quantum metadata field {field}")
        for field in policy.QUANTUM_ZERO_AUTHORITY_FLAGS:
            if field not in required or field not in properties:
                failures.append(f"{filename} must include quantum zero flag {field}")
        for field in policy.ATOMICROWS_PRE_BRIDGE_METADATA_FIELDS:
            if field not in required or field not in properties:
                failures.append(f"{filename} must include AtomicRows metadata field {field}")
        for field in policy.ATOMICROWS_ZERO_AUTHORITY_FLAGS:
            if field not in required or field not in properties:
                failures.append(f"{filename} must include AtomicRows zero flag {field}")
        if "venue_id" in properties and tuple(properties["venue_id"].get("enum", [])) != policy.STAGE1_VENUE_IDS:
            failures.append(f"{filename} venue_id enum must match policy")
        if "scope_id" in properties and tuple(properties["scope_id"].get("enum", [])) != policy.SHARED_SCOPE_IDS:
            failures.append(f"{filename} scope_id enum must match policy")
        enum_checks = {
            "canonical_depth_side": policy.ALLOWED_CANONICAL_DEPTH_SIDES,
            "qtt_internal_lifecycle_state_class": policy.ALLOWED_EVENT_LIFECYCLE_STATUS_CLASSES,
            "source_dependency_state": policy.ALLOWED_SOURCE_DEPENDENCY_STATES,
            "snapshot_input_class": policy.ALLOWED_SNAPSHOT_INPUT_CLASSES,
            "snapshot_class": policy.ALLOWED_ORDERBOOK_SNAPSHOT_CLASSES
            + policy.ALLOWED_EVENT_STATE_SNAPSHOT_CLASSES,
            "rejected_reason_code": policy.REJECTION_REASON_CODES,
        }
        for field, expected in enum_checks.items():
            if field in properties and tuple(properties[field].get("enum", [])) != tuple(expected):
                failures.append(f"{filename} {field} enum must match policy")
    return failures


def _zero_authority_failures(records: list[Mapping[str, Any]]) -> list[str]:
    failures = []
    for record in records:
        ref = str(record.get("snapshot_id") or record.get("input_lock_id") or record.get("binding_id") or record.get("record_type"))
        for field, expected in policy.zero_authority_flags().items():
            if field in record and record.get(field) != expected:
                failures.append(f"{ref}.{field} must be {expected!r}")
    return failures


def _all_records(artifacts: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [
        *artifacts["snapshot_input_locks"],
        *artifacts["orderbook_snapshots"],
        *artifacts["event_state_snapshots"],
        *artifacts["snapshot_builder_bindings"],
        *artifacts["snapshot_integrity_receipts"],
        *artifacts["snapshot_rejections"],
        *artifacts["atomicrows_compatibility_records"],
        artifacts["downstream_handoff"],
    ]


def validate_artifacts(
    artifacts: Mapping[str, Any],
    repo_root: Path | None = None,
) -> list[str]:
    failures: list[str] = []
    if repo_root is not None:
        failures.extend(_schema_validation(repo_root))
    failures.extend(artifacts.get("import_failures", []))
    failures.extend(validate_pr132_handoff(artifacts.get("pr132_handoff")))
    failures.extend(_zero_authority_failures(_all_records(artifacts)))

    orderbook = artifacts["orderbook_snapshots"]
    event_state = artifacts["event_state_snapshots"]
    bindings = artifacts["snapshot_builder_bindings"]
    locks = artifacts["snapshot_input_locks"]
    integrity = artifacts["snapshot_integrity_receipts"]
    handoff = artifacts["downstream_handoff"]
    main = artifacts["main_report"]

    venue_binding_scopes = {record.get("venue_id") for record in bindings if record.get("venue_id")}
    if venue_binding_scopes != set(policy.STAGE1_VENUE_IDS):
        failures.append("snapshot builder bindings must cover exactly three Stage-1 venues")
    if "PREDICTION_MARKETS_GENERAL" in venue_binding_scopes:
        failures.append("PREDICTION_MARKETS_GENERAL must not be a venue")

    lock_ids = {record["input_lock_id"] for record in locks}
    snapshot_ids = [record["snapshot_id"] for record in orderbook + event_state]
    if len(snapshot_ids) != len(set(snapshot_ids)):
        failures.append("duplicate snapshot IDs are forbidden")

    for snapshot in orderbook:
        if snapshot["snapshot_input_lock_ref"] not in lock_ids:
            failures.append("orderbook snapshot missing input lock")
        if snapshot.get("fixture_orderbook_snapshot_created") is not True:
            failures.append("fixture orderbook snapshot must be created")
        if snapshot.get("live_orderbook_snapshot_created") is not False:
            failures.append("live orderbook snapshot must be false")
        levels = list(snapshot.get("depth_levels", []))
        if levels != sorted(levels, key=canonical_orderbook_sort_key):
            failures.append("orderbook depth levels must be canonical sorted")
        level_ids = [level["synthetic_depth_level_id"] for level in levels]
        if len(level_ids) != len(set(level_ids)):
            failures.append("duplicate synthetic depth level IDs are forbidden")
        for level in levels:
            if level.get("canonical_depth_side") not in policy.ALLOWED_CANONICAL_DEPTH_SIDES:
                failures.append("invalid orderbook side is forbidden")
        for flag in (
            "crossed_book_valid_trading_evidence_created",
            "orderbook_snapshot_is_trading_signal",
            "orderbook_snapshot_is_feature_vector",
            "orderbook_snapshot_is_quantum_feature_vector",
            "orderbook_snapshot_is_atomicrows_row",
            "orderbook_snapshot_is_order_authority",
            "orderbook_snapshot_is_runtime_resolver_snapshot",
        ):
            if snapshot.get(flag) is not False:
                failures.append(f"orderbook snapshot {flag} must be false")

    for snapshot in event_state:
        if snapshot["snapshot_input_lock_ref"] not in lock_ids:
            failures.append("event-state snapshot missing input lock")
        if snapshot.get("fixture_event_state_snapshot_created") is not True:
            failures.append("fixture event-state snapshot must be created")
        if snapshot.get("live_event_state_snapshot_created") is not False:
            failures.append("live event-state snapshot must be false")
        states = list(snapshot.get("event_states", []))
        if states != sorted(states, key=canonical_event_state_sort_key):
            failures.append("event-state records must be canonical sorted")
        state_ids = [state["synthetic_event_state_id"] for state in states]
        if len(state_ids) != len(set(state_ids)):
            failures.append("duplicate synthetic event-state IDs are forbidden")
        for state in states:
            if (
                state.get("qtt_internal_lifecycle_state_class")
                not in policy.ALLOWED_EVENT_LIFECYCLE_STATUS_CLASSES
            ):
                failures.append("invalid event lifecycle state is forbidden")
        for flag in (
            "event_state_snapshot_is_trading_signal",
            "event_state_snapshot_is_feature_vector",
            "event_state_snapshot_is_quantum_feature_vector",
            "event_state_snapshot_is_atomicrows_row",
            "event_state_snapshot_is_order_authority",
            "event_state_snapshot_is_runtime_resolver_snapshot",
        ):
            if snapshot.get(flag) is not False:
                failures.append(f"event-state snapshot {flag} must be false")

    for receipt in integrity:
        for field in (
            "duplicate_synthetic_depth_level_id_count",
            "duplicate_synthetic_event_state_id_count",
            "duplicate_orderbook_snapshot_id_count",
            "duplicate_event_state_snapshot_id_count",
            "duplicate_canonical_sort_key_count",
            "invalid_orderbook_side_count",
            "invalid_event_lifecycle_state_count",
            "missing_snapshot_input_lock_count",
            "crossed_book_trading_evidence_created_count",
        ):
            if receipt.get(field) != 0:
                failures.append(f"integrity receipt {field} must be 0")
        for field in (
            "deterministic_sorting_verified",
            "canonical_sequence_verified",
            "bid_side_sorting_verified",
            "ask_side_sorting_verified",
            "event_state_sorting_verified",
        ):
            if receipt.get(field) is not True:
                failures.append(f"integrity receipt {field} must be true")

    for record in _all_records(artifacts):
        if record.get("quantum_ready_snapshot_contract") is not True:
            failures.append("all PR133 records must be quantum-ready metadata contracts")
        if record.get("atomicrows_pre_bridge_compatibility_metadata_created") is not True:
            failures.append("all PR133 records must include AtomicRows pre-bridge metadata")

    for flag in (
        "contains_live_orderbook_snapshot",
        "contains_live_event_state_snapshot",
        "contains_live_market_data",
        "contains_live_credentials",
        "contains_private_state_payload",
        "contains_runtime_resolver_snapshot",
        "contains_historical_dataset_digest",
        "contains_feature_vector",
        "contains_trading_signal",
        "contains_quantum_feature_vector",
        "contains_quantum_optimizer_input",
        "contains_quantum_trading_signal",
        "contains_order_authority",
        "contains_profit_evidence",
        "contains_quantum_execution",
        "contains_atomicrows_materialized_rows",
        "contains_atomicrows_bundle",
        "contains_atomicrows_sha",
        "downstream_pr116_execution_authorized",
        "downstream_pr117_execution_authorized",
        "downstream_quantum_feature_computation_authorized",
        "downstream_quantum_optimizer_input_creation_authorized",
        "downstream_quantum_trading_signal_creation_authorized",
        "downstream_atomicrows_bridge_authorized_now",
        "downstream_atomicrows_bundle_sha_authorized_now",
    ):
        if handoff.get(flag) is not False:
            failures.append(f"handoff {flag} must be false")
    if handoff.get("downstream_prs") != list(policy.DOWNSTREAM_PR_IDS):
        failures.append("handoff must preserve PR116 and PR117")

    expected_main = {
        "repo_pr_label": "PR133",
        "roadmap_pr_implemented": "PR115",
        "orderbook_snapshot_count": 4,
        "event_state_snapshot_count": 4,
        "snapshot_input_lock_count": 4,
        "snapshot_builder_binding_count": 4,
        "stage1_venue_count": 3,
        "shared_scope_count": 1,
        "prediction_markets_general_treated_as_shared_scope": True,
    }
    for field, expected in expected_main.items():
        if main.get(field) != expected:
            failures.append(f"main_report.{field} must be {expected!r}")
    for count_field in policy.ZERO_COUNT_INVARIANTS:
        if main["PR133_SNAPSHOT_INTEGRITY_EVIDENCE"].get(count_field) != 0:
            failures.append(f"main_report zero count {count_field} must be 0")
    if (
        main["PR133_QUANTUM_READY_SNAPSHOT_CONTRACT_EVIDENCE"][
            "quantum_ready_snapshot_contract_count"
        ]
        < 4
    ):
        failures.append("quantum-ready snapshot contract count must be >= 4")
    if (
        main["PR133_ATOMICROWS_PRE_BRIDGE_COMPATIBILITY_EVIDENCE"][
            "atomicrows_pre_bridge_compatibility_metadata_created_count"
        ]
        < 4
    ):
        failures.append("AtomicRows pre-bridge compatibility count must be >= 4")
    return failures


def _malformed_fixture_payloads(artifacts: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    missing = {
        "fixture_id": "PR133_MALFORMED_MISSING_PR132_HANDOFF_V1",
        "market_data_ingest_downstream_handoff": None,
        "expected_block": "BLOCKED_MISSING_PR132_MARKET_DATA_INGEST_HANDOFF",
    }
    scope_mismatch_handoff = deepcopy(artifacts["pr132_handoff"])
    scope_mismatch_handoff["venue_specific_scope"] = ["KALSHI", "POLYMARKET"]
    live_fetch = deepcopy(artifacts["snapshot_input_locks"][0])
    live_fetch["live_market_data_fetch_created"] = True
    resolver = deepcopy(artifacts["orderbook_snapshots"][0])
    resolver["runtime_resolver_snapshot_created"] = True
    historical = deepcopy(artifacts["orderbook_snapshots"][0])
    historical["historical_dataset_digest_created"] = True
    feature = deepcopy(artifacts["orderbook_snapshots"][0])
    feature["orderbook_snapshot_is_feature_vector"] = True
    q_feature = deepcopy(artifacts["orderbook_snapshots"][0])
    q_feature["quantum_snapshot_feature_computation_created"] = True
    q_optimizer = deepcopy(artifacts["orderbook_snapshots"][0])
    q_optimizer["quantum_optimizer_input_created"] = True
    q_signal = deepcopy(artifacts["orderbook_snapshots"][0])
    q_signal["quantum_trading_signal_created"] = True
    order_authority = deepcopy(artifacts["orderbook_snapshots"][0])
    order_authority["order_authority_created"] = True
    live_orderbook = deepcopy(artifacts["orderbook_snapshots"][0])
    live_orderbook["live_orderbook_snapshot_created"] = True
    atomic_bundle = deepcopy(artifacts["atomicrows_compatibility_records"][0])
    atomic_bundle["atomicrows_bundle_created"] = True
    atomic_rows = deepcopy(artifacts["atomicrows_compatibility_records"][0])
    atomic_rows["atomicrows_row_records_created_count"] = 1
    atomic_4183 = deepcopy(artifacts["atomicrows_compatibility_records"][0])
    atomic_4183["atomicrows_4183_completion_claim_created"] = True
    duplicate_depth = deepcopy(artifacts["orderbook_snapshots"][0])
    duplicate_depth["depth_levels"][1]["synthetic_depth_level_id"] = duplicate_depth["depth_levels"][0]["synthetic_depth_level_id"]
    duplicate_snapshot = deepcopy(artifacts["orderbook_snapshots"][0])
    duplicate_snapshot["duplicate_snapshot_id_probe"] = duplicate_snapshot["snapshot_id"]
    crossed = deepcopy(artifacts["orderbook_snapshots"][0])
    crossed["crossed_book_valid_trading_evidence_created"] = True
    invalid_lifecycle = deepcopy(artifacts["event_state_snapshots"][0])
    invalid_lifecycle["event_states"][0]["qtt_internal_lifecycle_state_class"] = "INVALID_LIVE_STATE"
    missing_lock = deepcopy(artifacts["event_state_snapshots"][0])
    missing_lock["snapshot_input_lock_ref"] = "PR133_MISSING_INPUT_LOCK"
    return {
        "malformed_missing_pr132_handoff.v1.fixture.json": missing,
        "malformed_scope_mismatch.v1.fixture.json": {
            "fixture_id": "PR133_MALFORMED_SCOPE_MISMATCH_V1",
            "market_data_ingest_downstream_handoff": scope_mismatch_handoff,
            "expected_block": "BLOCKED_SCOPE_MISMATCH",
        },
        "malformed_live_market_data_fetch.v1.fixture.json": {
            "fixture_id": "PR133_MALFORMED_LIVE_MARKET_DATA_FETCH_V1",
            "snapshot_input_lock": live_fetch,
            "expected_block": "BLOCKED_LIVE_MARKET_DATA_FETCH",
        },
        "malformed_runtime_resolver_snapshot_created.v1.fixture.json": {
            "fixture_id": "PR133_MALFORMED_RUNTIME_RESOLVER_SNAPSHOT_CREATED_V1",
            "orderbook_snapshot": resolver,
            "expected_block": "BLOCKED_RUNTIME_RESOLVER_SNAPSHOT_CREATED",
        },
        "malformed_historical_dataset_digest_created.v1.fixture.json": {
            "fixture_id": "PR133_MALFORMED_HISTORICAL_DATASET_DIGEST_CREATED_V1",
            "orderbook_snapshot": historical,
            "expected_block": "BLOCKED_HISTORICAL_DATASET_DIGEST_CREATED",
        },
        "malformed_feature_vector_created.v1.fixture.json": {
            "fixture_id": "PR133_MALFORMED_FEATURE_VECTOR_CREATED_V1",
            "orderbook_snapshot": feature,
            "expected_block": "BLOCKED_FEATURE_VECTOR_CREATED",
        },
        "malformed_quantum_snapshot_feature_computation_created.v1.fixture.json": {
            "fixture_id": "PR133_MALFORMED_QUANTUM_SNAPSHOT_FEATURE_CREATED_V1",
            "orderbook_snapshot": q_feature,
            "expected_block": "BLOCKED_QUANTUM_SNAPSHOT_FEATURE_COMPUTATION_CREATED",
        },
        "malformed_quantum_optimizer_input_created.v1.fixture.json": {
            "fixture_id": "PR133_MALFORMED_QUANTUM_OPTIMIZER_INPUT_CREATED_V1",
            "orderbook_snapshot": q_optimizer,
            "expected_block": "BLOCKED_QUANTUM_OPTIMIZER_INPUT_CREATED",
        },
        "malformed_quantum_trading_signal_created.v1.fixture.json": {
            "fixture_id": "PR133_MALFORMED_QUANTUM_TRADING_SIGNAL_CREATED_V1",
            "orderbook_snapshot": q_signal,
            "expected_block": "BLOCKED_QUANTUM_TRADING_SIGNAL_CREATED",
        },
        "malformed_order_authority_created.v1.fixture.json": {
            "fixture_id": "PR133_MALFORMED_ORDER_AUTHORITY_CREATED_V1",
            "orderbook_snapshot": order_authority,
            "expected_block": "BLOCKED_ORDER_AUTHORITY_OR_EXECUTION",
        },
        "malformed_live_orderbook_snapshot_created.v1.fixture.json": {
            "fixture_id": "PR133_MALFORMED_LIVE_ORDERBOOK_SNAPSHOT_CREATED_V1",
            "orderbook_snapshot": live_orderbook,
            "expected_block": "BLOCKED_LIVE_ORDERBOOK_SNAPSHOT_CREATED",
        },
        "malformed_atomicrows_bundle_created.v1.fixture.json": {
            "fixture_id": "PR133_MALFORMED_ATOMICROWS_BUNDLE_CREATED_V1",
            "atomicrows_pre_bridge_compatibility": atomic_bundle,
            "expected_block": "BLOCKED_ATOMICROWS_BUNDLE_SHA_MUTATION",
        },
        "malformed_atomicrows_row_records_created.v1.fixture.json": {
            "fixture_id": "PR133_MALFORMED_ATOMICROWS_ROW_RECORDS_CREATED_V1",
            "atomicrows_pre_bridge_compatibility": atomic_rows,
            "expected_block": "BLOCKED_ATOMICROWS_ROW_RECORD_CREATED",
        },
        "malformed_atomicrows_4183_completion_claim.v1.fixture.json": {
            "fixture_id": "PR133_MALFORMED_ATOMICROWS_4183_COMPLETION_CLAIM_V1",
            "atomicrows_pre_bridge_compatibility": atomic_4183,
            "expected_block": "BLOCKED_ATOMICROWS_4183_COMPLETION_CLAIM_CREATED",
        },
        "malformed_duplicate_depth_level.v1.fixture.json": {
            "fixture_id": "PR133_MALFORMED_DUPLICATE_DEPTH_LEVEL_V1",
            "orderbook_snapshot": duplicate_depth,
            "expected_block": "BLOCKED_DUPLICATE_DEPTH_LEVEL_ID",
        },
        "malformed_duplicate_snapshot_id.v1.fixture.json": {
            "fixture_id": "PR133_MALFORMED_DUPLICATE_SNAPSHOT_ID_V1",
            "orderbook_snapshot": duplicate_snapshot,
            "expected_block": "BLOCKED_DUPLICATE_SNAPSHOT_ID",
        },
        "malformed_crossed_book_trading_evidence_claim.v1.fixture.json": {
            "fixture_id": "PR133_MALFORMED_CROSSED_BOOK_TRADING_EVIDENCE_CLAIM_V1",
            "orderbook_snapshot": crossed,
            "expected_block": "BLOCKED_CROSSED_BOOK_TRADING_EVIDENCE_CLAIM",
        },
        "malformed_event_lifecycle_state.v1.fixture.json": {
            "fixture_id": "PR133_MALFORMED_EVENT_LIFECYCLE_STATE_V1",
            "event_state_snapshot": invalid_lifecycle,
            "expected_block": "BLOCKED_INVALID_EVENT_LIFECYCLE_STATE",
        },
        "malformed_missing_snapshot_input_lock.v1.fixture.json": {
            "fixture_id": "PR133_MALFORMED_MISSING_SNAPSHOT_INPUT_LOCK_V1",
            "event_state_snapshot": missing_lock,
            "expected_block": "BLOCKED_MISSING_SNAPSHOT_INPUT_LOCK",
        },
    }


def write_generated_reports(repo_root: Path, out_root: Path | None = None) -> dict[str, Any]:
    artifacts = build_snapshot_artifacts(repo_root)
    for key, path in REPORT_PATHS.items():
        output_path = _output_path(repo_root, path, out_root)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(_dump_json(artifacts[key]), encoding="utf-8", newline="\n")
    return artifacts


def write_fixture_files(repo_root: Path, out_root: Path | None = None) -> dict[str, Any]:
    artifacts = build_snapshot_artifacts(repo_root)
    fixture_payloads: dict[str, Mapping[str, Any]] = {
        "market_data_ingest_downstream_handoff.v1.fixture.json": {
            "fixture_id": "PR133_MARKET_DATA_INGEST_DOWNSTREAM_HANDOFF_INPUT_FIXTURE_V1",
            "market_data_ingest_downstream_handoff": artifacts["pr132_handoff"],
        },
        "snapshot_input_locks.v1.fixture.json": {
            "fixture_id": "PR133_SNAPSHOT_INPUT_LOCKS_FIXTURE_V1",
            "snapshot_input_locks": artifacts["snapshot_input_locks"],
        },
        "orderbook_snapshots.v1.fixture.json": {
            "fixture_id": "PR133_ORDERBOOK_SNAPSHOTS_FIXTURE_V1",
            "orderbook_snapshots": artifacts["orderbook_snapshots"],
        },
        "event_state_snapshots.v1.fixture.json": {
            "fixture_id": "PR133_EVENT_STATE_SNAPSHOTS_FIXTURE_V1",
            "event_state_snapshots": artifacts["event_state_snapshots"],
        },
        "snapshot_builder_bindings.v1.fixture.json": {
            "fixture_id": "PR133_SNAPSHOT_BUILDER_BINDINGS_FIXTURE_V1",
            "snapshot_builder_bindings": artifacts["snapshot_builder_bindings"],
        },
        "snapshot_integrity_receipts.v1.fixture.json": {
            "fixture_id": "PR133_SNAPSHOT_INTEGRITY_RECEIPTS_FIXTURE_V1",
            "snapshot_integrity_receipts": artifacts["snapshot_integrity_receipts"],
        },
        "snapshot_rejections.v1.fixture.json": {
            "fixture_id": "PR133_SNAPSHOT_REJECTIONS_FIXTURE_V1",
            "snapshot_rejections": artifacts["snapshot_rejections"],
        },
        "atomicrows_pre_bridge_compatibility.v1.fixture.json": {
            "fixture_id": "PR133_ATOMICROWS_PRE_BRIDGE_COMPATIBILITY_FIXTURE_V1",
            "atomicrows_pre_bridge_compatibility_records": artifacts[
                "atomicrows_compatibility_records"
            ],
        },
        "expected_snapshot_downstream_handoff.v1.fixture.json": {
            "fixture_id": "PR133_EXPECTED_SNAPSHOT_DOWNSTREAM_HANDOFF_V1",
            "orderbook_event_state_snapshot_downstream_handoff": artifacts[
                "downstream_handoff"
            ],
        },
        **_malformed_fixture_payloads(artifacts),
    }
    for filename, payload in fixture_payloads.items():
        output_path = _output_path(repo_root, FIXTURE_DIR / filename, out_root)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fixture_payload = {
            "execution": "DISABLED",
            "fixture_authority_class": "TEST_FIXTURE_NOT_EXTERNAL_FACT",
            "mode": "SOURCE_REQUIRED",
            **payload,
        }
        output_path.write_text(
            _dump_json(fixture_payload),
            encoding="utf-8",
            newline="\n",
        )
    return artifacts
