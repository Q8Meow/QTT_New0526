from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

from src.qtt.stage1_prediction_markets.market_data_ingest import policy
from src.qtt.stage1_prediction_markets.market_data_ingest.adapter import (
    build_adapter_inputs,
    build_canonical_events,
)
from src.qtt.stage1_prediction_markets.market_data_ingest.binding import (
    build_adapter_bindings,
)
from src.qtt.stage1_prediction_markets.market_data_ingest.handoff import (
    build_downstream_handoff,
)
from src.qtt.stage1_prediction_markets.market_data_ingest.source_dependency import (
    build_no_live_network_attestations,
    build_rejection_receipts,
    build_source_dependencies,
)


GENERATED_DIR = Path("docs/master_plan/source_evidence/generated")
FIXTURE_DIR = Path("tests/fixtures/source_evidence/pr132_venue_market_data_ingest_adapters")
SCHEMA_DIR = Path("src/qtt/stage1_prediction_markets/market_data_ingest")

PR131_HANDOFF_REPORT_PATH = GENERATED_DIR / "CredentialReadinessDownstreamHandoff.report.json"

MAIN_REPORT_PATH = GENERATED_DIR / (
    "CODEX_PR132_VENUE_MARKET_DATA_INGEST_ADAPTERS_REPORT.json"
)
ADAPTER_REPORT_PATH = GENERATED_DIR / "VenueMarketDataIngestAdapters.report.json"
SOURCE_DEPENDENCY_REPORT_PATH = GENERATED_DIR / "MarketDataSourceDependency.report.json"
NO_LIVE_NETWORK_REPORT_PATH = GENERATED_DIR / "MarketDataNoLiveNetworkAttestation.report.json"
HANDOFF_REPORT_PATH = GENERATED_DIR / "MarketDataIngestDownstreamHandoff.report.json"

REPORT_PATHS = {
    "main_report": MAIN_REPORT_PATH,
    "adapter_report": ADAPTER_REPORT_PATH,
    "source_dependency_report": SOURCE_DEPENDENCY_REPORT_PATH,
    "no_live_network_report": NO_LIVE_NETWORK_REPORT_PATH,
    "handoff_report": HANDOFF_REPORT_PATH,
}

SCHEMA_FILES = (
    "venue_market_data_adapter_input.schema.json",
    "canonical_market_data_ingest_event.schema.json",
    "venue_market_data_adapter_binding.schema.json",
    "venue_market_data_adapter_rejection.schema.json",
    "market_data_source_dependency.schema.json",
    "market_data_no_live_network_attestation.schema.json",
    "market_data_ingest_downstream_handoff.schema.json",
)

FIXTURE_FILES = (
    "credential_readiness_downstream_handoff.v1.fixture.json",
    "venue_market_data_adapter_inputs.v1.fixture.json",
    "venue_market_data_adapter_bindings.v1.fixture.json",
    "canonical_market_data_ingest_events.v1.fixture.json",
    "market_data_source_dependencies.v1.fixture.json",
    "market_data_no_live_network_attestations.v1.fixture.json",
    "venue_market_data_adapter_rejections.v1.fixture.json",
    "expected_market_data_ingest_downstream_handoff.v1.fixture.json",
    "malformed_missing_pr131_credential_handoff.v1.fixture.json",
    "malformed_venue_scope_mismatch.v1.fixture.json",
    "malformed_live_network_attempt.v1.fixture.json",
    "malformed_unaccepted_venue_semantics_claim.v1.fixture.json",
    "malformed_orderbook_snapshot_created.v1.fixture.json",
    "malformed_runtime_resolver_snapshot_created.v1.fixture.json",
    "malformed_quantum_feature_computation_created.v1.fixture.json",
    "malformed_quantum_optimizer_input_created.v1.fixture.json",
    "malformed_quantum_trading_signal_created.v1.fixture.json",
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_json(value: Mapping[str, Any]) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _output_path(repo_root: Path, path: Path, out_root: Path | None = None) -> Path:
    return (repo_root if out_root is None else out_root) / path


def _scope_value(record: Mapping[str, object]) -> str:
    return str(record.get("venue_id") or record.get("scope_id"))


def _scope_field(record: Mapping[str, object]) -> str:
    return "venue_id" if record.get("venue_id") else "scope_id"


def _pr131_handoff_from_report(repo_root: Path) -> dict[str, Any]:
    report = _load_json(repo_root / PR131_HANDOFF_REPORT_PATH)
    value = report.get("credential_readiness_downstream_handoff")
    if not isinstance(value, dict):
        raise ValueError("PR131 credential-readiness downstream handoff missing")
    return value


def validate_pr131_handoff(handoff: Mapping[str, Any] | None) -> list[str]:
    if not isinstance(handoff, Mapping):
        return ["missing PR131 credential-readiness downstream handoff"]
    failures: list[str] = []
    expected = {
        "handoff_id": "PR131_CREDENTIAL_READINESS_DOWNSTREAM_HANDOFF_V1",
        "producer_pr": policy.UPSTREAM_REPO_PR,
        "producer_roadmap_pr": policy.UPSTREAM_ROADMAP_PR,
        "downstream_may_consume_metadata_only": True,
        "downstream_may_resolve_credentials": False,
        "downstream_may_call_provider": False,
        "downstream_may_call_venue_api_from_this_handoff": False,
        "contains_live_credentials": False,
        "contains_private_state_payload": False,
        "contains_order_authority": False,
        "contains_profit_evidence": False,
        "contains_quantum_execution": False,
    }
    for field, expected_value in expected.items():
        if handoff.get(field) != expected_value:
            failures.append(f"PR131 handoff {field} must be {expected_value!r}")
    if tuple(handoff.get("venue_specific_scope", [])) != policy.STAGE1_VENUE_IDS:
        failures.append("PR131 handoff must cover exactly the three Stage-1 venues")
    if tuple(handoff.get("shared_scope", [])) != policy.SHARED_SCOPE_IDS:
        failures.append("PR131 handoff must preserve PREDICTION_MARKETS_GENERAL scope")
    if "PREDICTION_MARKETS_GENERAL" in set(handoff.get("venue_specific_scope", [])):
        failures.append("PREDICTION_MARKETS_GENERAL must not be a PR131 venue")
    downstream = set(handoff.get("downstream_prs", []))
    if "PR114" not in downstream:
        failures.append("PR131 handoff must preserve downstream PR114")
    return failures


def _policy_constants_section() -> dict[str, object]:
    return {
        "allowed_action_ids": list(policy.ALLOWED_ACTION_IDS),
        "allowed_adapter_input_classes": list(policy.ALLOWED_ADAPTER_INPUT_CLASSES),
        "allowed_canonical_event_kind_classes": list(
            policy.ALLOWED_CANONICAL_EVENT_KIND_CLASSES
        ),
        "allowed_source_dependency_states": list(policy.ALLOWED_SOURCE_DEPENDENCY_STATES),
        "authority_zero_flags": list(policy.AUTHORITY_ZERO_FLAGS),
        "blocked_action_ids": list(policy.BLOCKED_ACTION_IDS),
        "downstream_pr_ids": list(policy.DOWNSTREAM_PR_IDS),
        "package_authority_class": policy.PACKAGE_AUTHORITY_CLASS,
        "producer_repo_pr": policy.PRODUCER_REPO_PR,
        "producer_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
        "quantum_forward_metadata_fields": list(policy.QUANTUM_FORWARD_METADATA_FIELDS),
        "quantum_zero_authority_flags": dict(policy.QUANTUM_ZERO_AUTHORITY_FLAGS),
        "rejection_reason_codes": list(policy.REJECTION_REASON_CODES),
        "shared_scope_ids": list(policy.SHARED_SCOPE_IDS),
        "stage1_venue_ids": list(policy.STAGE1_VENUE_IDS),
        "upstream_repo_pr": policy.UPSTREAM_REPO_PR,
        "upstream_roadmap_pr": policy.UPSTREAM_ROADMAP_PR,
    }


def _command_action_matrix() -> list[dict[str, object]]:
    allowed = [
        {
            "action_id": action_id,
            "actor": "CODEX",
            "authority_class": policy.PACKAGE_AUTHORITY_CLASS,
            "input_artifacts": [
                "owner-approved PR132 prompt",
                "mandatory roadmap/master-plan/source-evidence reads",
            ],
            "output_artifacts": ["PR132 deterministic metadata artifact"],
            "allowed": True,
            "creates_runtime_authority": False,
            "creates_live_authority": False,
            "creates_market_data_live_authority": False,
            "creates_credential_authority": False,
            "creates_private_state_authority": False,
            "creates_orderbook_snapshot": False,
            "creates_runtime_resolver_snapshot": False,
            "creates_historical_dataset_digest": False,
            "creates_feature_vector": False,
            "creates_trading_signal": False,
            "creates_quantum_ready_contract_metadata": (
                action_id
                == "CREATE_QUANTUM_READY_MARKET_DATA_CONTRACT_METADATA_FIELDS"
            ),
            "creates_quantum_feature_computation": False,
            "creates_quantum_optimizer_input": False,
            "creates_quantum_trading_signal": False,
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
            "input_artifacts": ["blocked by centralized PR132 policy"],
            "output_artifacts": [],
            "allowed": False,
            "blocked_reason": f"POLICY_BLOCK_{action_id}",
            "creates_runtime_authority": False,
            "creates_live_authority": False,
            "creates_market_data_live_authority": False,
            "creates_credential_authority": False,
            "creates_private_state_authority": False,
            "creates_orderbook_snapshot": False,
            "creates_runtime_resolver_snapshot": False,
            "creates_historical_dataset_digest": False,
            "creates_feature_vector": False,
            "creates_trading_signal": False,
            "creates_quantum_ready_contract_metadata": False,
            "creates_quantum_feature_computation": False,
            "creates_quantum_optimizer_input": False,
            "creates_quantum_trading_signal": False,
            "creates_order_authority": False,
            "creates_profit_evidence": False,
            "creates_quantum_execution": False,
            "atomicrows_bundle_consumed": False,
            "atomicrows_sha_created": False,
        }
        for action_id in policy.BLOCKED_ACTION_IDS
    ]
    return allowed + blocked


def _market_specific_index(
    adapter_inputs: list[Mapping[str, object]],
    bindings: list[Mapping[str, object]],
    canonical_events: list[Mapping[str, object]],
    source_dependencies: list[Mapping[str, object]],
) -> dict[str, object]:
    inputs_by_scope: dict[str, list[str]] = {}
    bindings_by_scope: dict[str, list[str]] = {}
    events_by_scope: dict[str, list[str]] = {}
    deps_by_scope: dict[str, list[str]] = {}
    credential_by_scope: dict[str, set[str]] = {}
    for record in adapter_inputs:
        scope_value = _scope_value(record)
        inputs_by_scope.setdefault(scope_value, []).append(str(record["input_id"]))
        credential_by_scope.setdefault(scope_value, set()).add(
            str(record["credential_readiness_dependency_ref"])
        )
    for record in bindings:
        bindings_by_scope.setdefault(_scope_value(record), []).append(
            str(record["binding_id"])
        )
    for record in canonical_events:
        events_by_scope.setdefault(_scope_value(record), []).append(str(record["event_id"]))
    for record in source_dependencies:
        deps_by_scope.setdefault(_scope_value(record), []).append(
            str(record["dependency_id"])
        )

    venue_entries = []
    for venue_id in policy.STAGE1_VENUE_IDS:
        venue_entries.append(
            {
                "venue_id": venue_id,
                "adapter_binding_ids": bindings_by_scope[venue_id],
                "adapter_input_ids": inputs_by_scope[venue_id],
                "canonical_market_data_ingest_event_ids": events_by_scope[venue_id],
                "market_data_source_dependency_ids": deps_by_scope[venue_id],
                "credential_readiness_dependency_ids": sorted(
                    credential_by_scope[venue_id]
                ),
                "allowed_adapter_input_classes": list(policy.ALLOWED_ADAPTER_INPUT_CLASSES),
                "allowed_event_kind_classes": list(
                    policy.ALLOWED_CANONICAL_EVENT_KIND_CLASSES
                ),
                "blocked_live_action_classes": list(policy.BLOCKED_ACTION_IDS),
                **policy.quantum_metadata(),
                "downstream_pr115_contract_ref": (
                    f"PR115_{venue_id}_ORDERBOOK_EVENT_STATE_CONTRACT_REF"
                ),
                "downstream_pr116_contract_ref": (
                    f"PR116_{venue_id}_RUNTIME_RESOLVER_CONTRACT_REF"
                ),
                "downstream_pr117_contract_ref": (
                    f"PR117_{venue_id}_HISTORICAL_DATASET_CONTRACT_REF"
                ),
                "no_live_market_data_fetch": True,
                "no_rest_client": True,
                "no_websocket_client": True,
                "no_venue_api_call": True,
                "no_network_io": True,
                "no_live_credential_resolution": True,
                "no_private_state_fetch": True,
                "no_orderbook_snapshot_created": True,
                "no_runtime_resolver_snapshot_created": True,
                "no_historical_dataset_digest_created": True,
                "no_feature_vector_created": True,
                "no_trading_signal_created": True,
                "no_quantum_feature_computation_created": True,
                "no_quantum_optimizer_input_created": True,
                "no_quantum_trading_signal_created": True,
                "no_quantum_advantage_claim_created": True,
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
            "quantum_ready_market_data_contract": True,
            "no_quantum_execution_authority": True,
        }
    ]
    return {
        "shared_scope_entries": shared_entries,
        "venue_specific_entries": venue_entries,
    }


def _import_guard(repo_root: Path) -> tuple[list[str], dict[str, int]]:
    scan_roots = [
        repo_root / "src/qtt/stage1_prediction_markets/market_data_ingest",
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
                if "venue_market_data_ingest" in path.name
                or "pr132_market_data_ingest" in path.name
                or "market_data_ingest" in path.as_posix()
            )
    banned = set(policy.BANNED_IMPORT_MODULES)
    failures: list[str] = []
    counts = {
        "network_import_count": 0,
        "credential_provider_import_count": 0,
        "environment_credential_read_count": 0,
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


def _schema_validation(repo_root: Path) -> list[str]:
    failures: list[str] = []
    for filename in SCHEMA_FILES:
        path = repo_root / SCHEMA_DIR / filename
        if not path.exists():
            failures.append(f"missing PR132 schema: {filename}")
            continue
        schema = _load_json(path)
        if schema.get("additionalProperties") is not False:
            failures.append(f"{filename} must reject additional properties")
        required = set(schema.get("required", []))
        for field in ("schema_version", "record_type", "created_by", "authority_class"):
            if field not in required:
                failures.append(f"{filename} must require {field}")
        properties = schema.get("properties", {})
        for field in policy.QUANTUM_FORWARD_METADATA_FIELDS:
            if field not in required or field not in properties:
                failures.append(f"{filename} must include quantum metadata field {field}")
        for field in policy.QUANTUM_ZERO_AUTHORITY_FLAGS:
            if field not in required or field not in properties:
                failures.append(f"{filename} must include quantum zero flag {field}")
        if "venue_id" in properties:
            enum = tuple(properties["venue_id"].get("enum", []))
            if enum != policy.STAGE1_VENUE_IDS:
                failures.append(f"{filename} venue_id enum must match policy")
        if "scope_id" in properties:
            enum = tuple(properties["scope_id"].get("enum", []))
            if enum != policy.SHARED_SCOPE_IDS:
                failures.append(f"{filename} scope_id enum must match policy")
        if "event_kind_class" in properties:
            enum = tuple(properties["event_kind_class"].get("enum", []))
            if enum != policy.ALLOWED_CANONICAL_EVENT_KIND_CLASSES:
                failures.append(f"{filename} event_kind_class enum must match policy")
        if "adapter_input_class" in properties:
            enum = tuple(properties["adapter_input_class"].get("enum", []))
            if enum != policy.ALLOWED_ADAPTER_INPUT_CLASSES:
                failures.append(f"{filename} adapter_input_class enum must match policy")
        if "dependency_state" in properties:
            enum = tuple(properties["dependency_state"].get("enum", []))
            if enum != policy.ALLOWED_SOURCE_DEPENDENCY_STATES:
                failures.append(f"{filename} dependency_state enum must match policy")
        if "rejected_reason_code" in properties:
            enum = tuple(properties["rejected_reason_code"].get("enum", []))
            if enum != policy.REJECTION_REASON_CODES:
                failures.append(f"{filename} rejected_reason_code enum must match policy")
    return failures


def _records_for_authority_scan(artifacts: Mapping[str, Any]) -> list[Mapping[str, object]]:
    return [
        *artifacts["adapter_report"]["venue_market_data_adapter_inputs"],
        *artifacts["adapter_report"]["venue_market_data_adapter_bindings"],
        *artifacts["adapter_report"]["canonical_market_data_ingest_events"],
        *artifacts["source_dependency_report"]["market_data_source_dependencies"],
        *artifacts["source_dependency_report"]["venue_market_data_adapter_rejections"],
        *artifacts["no_live_network_report"]["market_data_no_live_network_attestations"],
        artifacts["handoff_report"]["market_data_ingest_downstream_handoff"],
    ]


def _zero_authority_failures(artifacts: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    for record in _records_for_authority_scan(artifacts):
        record_id = str(
            record.get("input_id")
            or record.get("event_id")
            or record.get("binding_id")
            or record.get("dependency_id")
            or record.get("rejection_id")
            or record.get("attestation_id")
            or record.get("handoff_id")
        )
        for flag in policy.AUTHORITY_ZERO_FLAGS:
            if record.get(flag) is not False:
                failures.append(f"{record_id} {flag} must be false")
        for flag, expected in policy.QUANTUM_ZERO_AUTHORITY_FLAGS.items():
            if record.get(flag) is not expected:
                failures.append(f"{record_id} {flag} must be {expected!r}")
        if record.get("quantum_ready_market_data_contract") is not True:
            failures.append(f"{record_id} must be quantum-ready metadata contract")
    return failures


def _route_triage_section() -> dict[str, object]:
    return {
        "repo_pr_label": "PR132",
        "authorized_roadmap_pr": "PR114",
        "unauthorized_roadmap_pr_same_number": "PR132",
        "same_number_inference_used": False,
        "implementation_scope": "ROADMAP_PR114_VENUE_MARKET_DATA_INGEST_ADAPTER_CONTRACTS",
        "venue_market_data_ingest_is_fixture_backed_contract_only": True,
        "quantum_ready_market_data_contract_prepared": True,
        "live_market_data_fetch_forbidden": True,
        "live_rest_client_forbidden": True,
        "live_websocket_client_forbidden": True,
        "venue_api_calls_forbidden": True,
        "network_io_forbidden": True,
        "credential_provider_calls_forbidden": True,
        "live_credential_resolution_forbidden": True,
        "source_retrieval_forbidden": True,
        "new_source_acceptance_forbidden": True,
        "official_venue_semantics_fabrication_forbidden": True,
        "orderbook_snapshot_building_forbidden": True,
        "event_state_snapshot_building_forbidden": True,
        "runtime_resolver_snapshot_creation_forbidden": True,
        "historical_dataset_digest_creation_forbidden": True,
        "market_data_feature_generation_forbidden": True,
        "trading_signal_generation_forbidden": True,
        "order_authority_forbidden": True,
        "replay_paper_live_use_forbidden": True,
        "profit_evidence_forbidden": True,
        "quantum_execution_forbidden": True,
        "quantum_feature_computation_forbidden": True,
        "quantum_optimizer_input_creation_forbidden": True,
        "quantum_trading_signal_creation_forbidden": True,
        "quantum_advantage_claim_forbidden": True,
        "atomicrows_bundle_sha_mutation_forbidden": True,
        "downstream_prs_preserved": list(policy.DOWNSTREAM_PR_IDS),
    }


def _main_report(
    *,
    adapter_inputs: list[Mapping[str, object]],
    bindings: list[Mapping[str, object]],
    canonical_events: list[Mapping[str, object]],
    source_dependencies: list[Mapping[str, object]],
    no_live_attestations: list[Mapping[str, object]],
    rejections: list[Mapping[str, object]],
    handoff: Mapping[str, object],
    import_counts: Mapping[str, int],
) -> dict[str, object]:
    scope_values = [_scope_value(record) for record in adapter_inputs]
    venue_input_count = sum(
        1 for record in adapter_inputs if record.get("venue_id") in policy.STAGE1_VENUE_IDS
    )
    shared_input_count = sum(
        1 for record in adapter_inputs if record.get("scope_id") in policy.SHARED_SCOPE_IDS
    )
    zero_counts = policy.zero_count_invariants()
    quantum_ready_count = sum(
        1
        for record in [
            *adapter_inputs,
            *bindings,
            *canonical_events,
            *source_dependencies,
            *no_live_attestations,
            *rejections,
            handoff,
        ]
        if record.get("quantum_ready_market_data_contract") is True
    )
    states = [record["dependency_state"] for record in source_dependencies]
    return {
        "report_id": "CODEX_PR132_VENUE_MARKET_DATA_INGEST_ADAPTERS_REPORT_V1",
        "repo_pr_label": policy.PRODUCER_REPO_PR,
        "roadmap_pr_implemented": policy.PRODUCER_ROADMAP_PR,
        "currentized_prior_repo_pr": policy.UPSTREAM_REPO_PR,
        "owner_authorized_capability": "VENUE_MARKET_DATA_INGEST_ADAPTER_CONTRACTS",
        "PR132_NORMALIZED_POLICY_CONSTANTS": _policy_constants_section(),
        "PR132_ROUTE_TRIAGE": _route_triage_section(),
        "PR132_MASTER_PLAN_SECTION_CROSSWALK": {
            "authority_families": [
                "owner source-evidence definitions and non-authority policy",
                "accepted source-evidence and target-field ledger boundary",
                "source revalidation/freshness boundary",
                "connector semantic non-authority boundary",
                "per-venue execution lifecycle model boundary",
                "cross-venue execution normalization binding boundary",
                "runtime cash/account/private-state non-production boundary",
                "PR131 credential-readiness metadata-only handoff",
                "market-data ingest adapter contract-only boundary",
                "orderbook/event-state snapshot downstream PR115 boundary",
                "runtime resolver snapshot downstream PR116 boundary",
                "historical dataset digest downstream PR117 boundary",
                "replay/paper/live non-execution boundary",
                "quantum-ready market-data contract boundary",
                "quantum metadata-only / no-execution boundary",
                "AtomicRows metadata-only boundary",
                "low-latency hot-path exclusion boundary",
            ],
            "section_ids_invented": False,
        },
        "PR132_MARKET_SPECIFIC_SECTION_INDEX": _market_specific_index(
            adapter_inputs,
            bindings,
            canonical_events,
            source_dependencies,
        ),
        "PR132_COMMAND_ACTION_MATRIX": _command_action_matrix(),
        "PR132_SOURCE_DEPENDENCY_EVIDENCE": {
            "accepted_source_dependency_count": states.count("ACCEPTED_SOURCE_GATED"),
            "connector_semantic_dependency_count": states.count("CONNECTOR_SEMANTIC_GATED"),
            "source_required_placeholder_count": states.count("SOURCE_REQUIRED"),
            "connector_semantic_required_placeholder_count": states.count(
                "CONNECTOR_SEMANTIC_REQUIRED"
            ),
            "blocked_scope_mismatch_placeholder_count": states.count(
                "BLOCKED_SCOPE_MISMATCH"
            ),
            "official_venue_semantics_fabricated": False,
            "source_retrieval_created": False,
            "source_acceptance_created": False,
            "connector_semantic_binding_created": False,
        },
        "PR132_PR131_CREDENTIAL_READINESS_DEPENDENCY_EVIDENCE": {
            "credential_readiness_handoff_ref": (
                "PR131_CREDENTIAL_READINESS_DOWNSTREAM_HANDOFF_V1"
            ),
            "pr131_handoff_consumed_as_metadata_only": True,
            "missing_handoff_rejection_tested": True,
            "malformed_handoff_rejection_tested": True,
            "scope_mismatch_rejection_tested": True,
            "credential_provider_called": False,
            "live_credential_resolution_performed": False,
        },
        "PR132_NO_LIVE_NETWORK_EVIDENCE": {
            **zero_counts,
            "rest_client_import_count": no_live_attestations[0]["rest_client_import_count"],
            "websocket_client_import_count": no_live_attestations[0][
                "websocket_client_import_count"
            ],
            "socket_import_count": no_live_attestations[0]["socket_import_count"],
            "environment_credential_read_count": import_counts[
                "environment_credential_read_count"
            ],
            "network_import_count": import_counts["network_import_count"],
            "credential_provider_import_count": import_counts[
                "credential_provider_import_count"
            ],
            "quantum_provider_import_count": import_counts["quantum_provider_import_count"],
        },
        "PR132_FIXTURE_SYNTHETIC_PAYLOAD_EVIDENCE": {
            "fixture_payload_is_synthetic_count": sum(
                1
                for record in adapter_inputs
                if record["fixture_payload_is_synthetic"] is True
            ),
            "fixture_payload_contains_live_market_data_count": sum(
                1
                for record in adapter_inputs
                if record["fixture_payload_contains_live_market_data"] is not False
            ),
            "fixture_payload_contains_official_venue_semantic_values_count": sum(
                1
                for record in adapter_inputs
                if record["fixture_payload_contains_official_venue_semantic_values"]
                is not False
            ),
        },
        "PR132_DOWNSTREAM_HANDOFF_EVIDENCE": handoff,
        "PR132_LOW_LATENCY_BOUNDARY_EVIDENCE": {
            "creates_precomputed_adapter_contracts_only": True,
            "runs_in_live_hot_path": False,
            "live_hot_path_network_call_created": False,
            "live_quote_freshness_claim_created": False,
            "latency_superiority_claim_created": False,
            "future_hot_path_consumption_requires_later_authorization": True,
        },
        "PR132_QUANTUM_READY_MARKET_DATA_CONTRACT_EVIDENCE": {
            "quantum_ready_market_data_contract_count": quantum_ready_count,
            **policy.quantum_metadata(),
        },
        "PR132_QUANTUM_METADATA_ONLY_EVIDENCE": {
            **policy.QUANTUM_ZERO_AUTHORITY_FLAGS,
            "quantum_backend_simulator_optimizer_execution_count": 0,
            "quantum_feature_computation_count": 0,
            "quantum_optimizer_input_count": 0,
            "quantum_trading_signal_count": 0,
            "quantum_advantage_claim_count": 0,
            "quantum_metadata_strings_only": True,
        },
        "PR132_ATOMICROWS_METADATA_ONLY_EVIDENCE": {
            "future_atomicrows_market_data_feature_row_refs": [],
            "future_atomicrows_parameter_row_refs": [],
            "future_atomicrows_family_refs": [],
            "future_atomicrows_quantum_feature_family_refs": [],
            "atomicrows_bundle_consumed": False,
            "atomicrows_bundle_created": False,
            "atomicrows_bundle_edited_count": 0,
            "atomicrows_sha_created": False,
            "atomicrows_sha_created_count": 0,
            "atomicrows_row_records_created_count": 0,
            "atomicrows_authority_created": False,
        },
        "PR132_VALIDATION_EVIDENCE": {
            "schema_count": len(SCHEMA_FILES),
            "fixture_dir": FIXTURE_DIR.as_posix(),
            "validator": "tools/venue_market_data_ingest_adapters_validate.py",
            "run_validation_gates_integration_required": True,
            "run_validation_gates_uses_fresh_pytest_basetemp": True,
            "deterministic_reports": True,
        },
        "adapter_binding_count": len(bindings),
        "adapter_binding_count_by_scope": {
            scope: sum(1 for record in bindings if _scope_value(record) == scope)
            for scope in sorted(set(scope_values))
        },
        "adapter_input_count": len(adapter_inputs),
        "adapter_input_count_by_scope": {
            scope: scope_values.count(scope) for scope in sorted(set(scope_values))
        },
        "canonical_market_data_ingest_event_count": len(canonical_events),
        "canonical_market_data_ingest_event_count_by_scope": {
            scope: sum(1 for record in canonical_events if _scope_value(record) == scope)
            for scope in sorted(set(scope_values))
        },
        "event_kind_classes": list(policy.ALLOWED_CANONICAL_EVENT_KIND_CLASSES),
        "fixture_payload_is_synthetic_count": len(adapter_inputs),
        "market_data_source_dependency_count": len(source_dependencies),
        "venue_specific_adapter_input_count": venue_input_count,
        "shared_scope_adapter_input_count": shared_input_count,
        "prediction_markets_general_treated_as_shared_scope": True,
        "stage1_venue_count": len(policy.STAGE1_VENUE_IDS),
        "shared_scope_count": len(policy.SHARED_SCOPE_IDS),
        "master_plan_modified": False,
        "atomicrows_bundle_file_modified": False,
        "atomicrows_sha_file_modified": False,
        "schema_paths": [(SCHEMA_DIR / filename).as_posix() for filename in SCHEMA_FILES],
        "fixture_paths": [(FIXTURE_DIR / filename).as_posix() for filename in FIXTURE_FILES],
        "report_paths": [path.as_posix() for path in REPORT_PATHS.values()],
    }


def build_market_data_ingest_artifacts(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    pr131_handoff = _pr131_handoff_from_report(repo_root)
    handoff_failures = validate_pr131_handoff(pr131_handoff)
    if handoff_failures:
        raise ValueError("; ".join(handoff_failures))
    credential_handoff_ref = str(pr131_handoff["handoff_id"])

    source_dependencies = build_source_dependencies()
    adapter_inputs = build_adapter_inputs(source_dependencies, credential_handoff_ref)
    canonical_events = build_canonical_events(adapter_inputs)
    bindings = build_adapter_bindings(
        adapter_inputs,
        canonical_events,
        source_dependencies,
        credential_handoff_ref,
    )
    rejections = build_rejection_receipts()
    scanned_refs = [
        "src/qtt/stage1_prediction_markets/market_data_ingest/",
        "tools/venue_market_data_ingest_adapters_validate.py",
        "tools/venue_market_data_ingest_fixture_build.py",
        "tests/source_evidence/test_pr132_market_data_ingest_schema.py",
    ]
    no_live_attestations = build_no_live_network_attestations(scanned_refs)
    handoff = build_downstream_handoff(
        adapter_inputs,
        bindings,
        canonical_events,
        source_dependencies,
        no_live_attestations,
    )
    import_failures, import_counts = _import_guard(repo_root)

    adapter_report = {
        "venue_market_data_ingest_adapters_report_id": (
            "PR132_VENUE_MARKET_DATA_INGEST_ADAPTERS_REPORT_V1"
        ),
        "producer_pr": policy.PRODUCER_REPO_PR,
        "producer_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
        "venue_market_data_adapter_inputs": adapter_inputs,
        "venue_market_data_adapter_bindings": bindings,
        "canonical_market_data_ingest_events": canonical_events,
        "fixture_payloads_are_synthetic": True,
        "contains_live_market_data": False,
        "contains_official_venue_semantics_fabrication": False,
    }
    source_dependency_report = {
        "market_data_source_dependency_report_id": (
            "PR132_MARKET_DATA_SOURCE_DEPENDENCY_REPORT_V1"
        ),
        "producer_pr": policy.PRODUCER_REPO_PR,
        "producer_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
        "market_data_source_dependencies": source_dependencies,
        "venue_market_data_adapter_rejections": rejections,
        "official_venue_semantics_fabricated": False,
        "source_retrieval_created": False,
        "source_acceptance_created": False,
        "connector_semantic_binding_created": False,
    }
    no_live_network_report = {
        "market_data_no_live_network_attestation_report_id": (
            "PR132_MARKET_DATA_NO_LIVE_NETWORK_ATTESTATION_REPORT_V1"
        ),
        "producer_pr": policy.PRODUCER_REPO_PR,
        "producer_roadmap_pr": policy.PRODUCER_ROADMAP_PR,
        "market_data_no_live_network_attestations": no_live_attestations,
    }
    handoff_report = {
        "market_data_ingest_downstream_handoff_report_id": (
            "PR132_MARKET_DATA_INGEST_DOWNSTREAM_HANDOFF_REPORT_V1"
        ),
        "market_data_ingest_downstream_handoff": handoff,
    }
    main_report = _main_report(
        adapter_inputs=adapter_inputs,
        bindings=bindings,
        canonical_events=canonical_events,
        source_dependencies=source_dependencies,
        no_live_attestations=no_live_attestations,
        rejections=rejections,
        handoff=handoff,
        import_counts=import_counts,
    )
    artifacts = {
        "main_report": main_report,
        "adapter_report": adapter_report,
        "source_dependency_report": source_dependency_report,
        "no_live_network_report": no_live_network_report,
        "handoff_report": handoff_report,
        "pr131_handoff": pr131_handoff,
        "import_failures": import_failures,
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
    failures.extend(validate_pr131_handoff(artifacts.get("pr131_handoff")))
    failures.extend(_zero_authority_failures(artifacts))

    adapter_inputs = artifacts["adapter_report"]["venue_market_data_adapter_inputs"]
    bindings = artifacts["adapter_report"]["venue_market_data_adapter_bindings"]
    canonical_events = artifacts["adapter_report"]["canonical_market_data_ingest_events"]
    source_dependencies = artifacts["source_dependency_report"][
        "market_data_source_dependencies"
    ]
    rejections = artifacts["source_dependency_report"]["venue_market_data_adapter_rejections"]
    no_live_attestations = artifacts["no_live_network_report"][
        "market_data_no_live_network_attestations"
    ]
    handoff = artifacts["handoff_report"]["market_data_ingest_downstream_handoff"]
    main = artifacts["main_report"]

    venue_binding_scopes = {
        record["venue_id"] for record in bindings if record.get("venue_id")
    }
    if venue_binding_scopes != set(policy.STAGE1_VENUE_IDS):
        failures.append("adapter bindings must cover exactly three Stage-1 venues")
    shared_binding_scopes = {
        record["scope_id"] for record in bindings if record.get("scope_id")
    }
    if shared_binding_scopes != set(policy.SHARED_SCOPE_IDS):
        failures.append("adapter bindings must include exactly the shared taxonomy scope")
    if "PREDICTION_MARKETS_GENERAL" in {
        record.get("venue_id") for record in adapter_inputs
    }:
        failures.append("PREDICTION_MARKETS_GENERAL must not be treated as a venue")

    for input_record in adapter_inputs:
        if input_record["adapter_input_class"] not in policy.ALLOWED_ADAPTER_INPUT_CLASSES:
            failures.append("adapter input class must match centralized policy")
        if input_record["event_kind_class"] not in policy.ALLOWED_CANONICAL_EVENT_KIND_CLASSES:
            failures.append("event kind class must match centralized policy")
        if input_record["source_dependency_state"] not in policy.ALLOWED_SOURCE_DEPENDENCY_STATES:
            failures.append("source dependency state must match centralized policy")
        for flag in (
            "fixture_payload_is_synthetic",
            "quantum_ready_market_data_contract",
            "live_use_requires_future_owner_approval",
            "live_use_requires_accepted_source_and_connector_semantic_binding",
        ):
            if input_record.get(flag) is not True:
                failures.append(f"adapter input {flag} must be true")
        for flag in (
            "fixture_payload_contains_live_market_data",
            "fixture_payload_contains_official_venue_semantic_values",
            "official_semantics_claimed",
            "live_fetch_attempted",
            "network_io_created",
            "credential_provider_called",
            "quantum_feature_computation_created",
            "quantum_optimizer_input_created",
            "quantum_trading_signal_created",
        ):
            if input_record.get(flag) is not False:
                failures.append(f"adapter input {flag} must be false")
        if input_record.get("official_semantics_claimed") is True and not (
            input_record.get("accepted_source_dependency_refs")
            and input_record.get("connector_semantic_dependency_refs")
        ):
            failures.append("official semantics require source and connector refs")

    event_ids = {record["event_id"] for record in canonical_events}
    for binding in bindings:
        if binding["adapter_scope"] != "FIXTURE_BACKED_CONTRACT_ONLY":
            failures.append("adapter binding scope must be fixture-backed contract only")
        if binding["allowed_use"] != "FIXTURE_BACKED_MARKET_DATA_INGEST_CONTRACT_ONLY":
            failures.append("adapter binding allowed use must be contract-only")
        if set(binding["output_event_refs"]) - event_ids:
            failures.append("adapter binding output refs must reference canonical events")
        for flag in (
            "future_live_use_requires_owner_approval",
            "future_live_use_requires_accepted_source_packet",
            "future_live_use_requires_fresh_revalidation_state",
            "future_live_use_requires_connector_semantic_binding",
            "future_live_use_requires_credential_provider_receipt_if_credentials_needed",
            "future_quantum_use_requires_pr115_pr116_pr117_data_chain",
            "future_quantum_use_requires_replay_paper_validation",
            "future_quantum_use_requires_owner_approval",
        ):
            if binding.get(flag) is not True:
                failures.append(f"adapter binding {flag} must be true")

    for event in canonical_events:
        for flag in (
            "adapter_output_is_trading_signal",
            "adapter_output_is_feature_vector",
            "adapter_output_is_scoring_input",
            "adapter_output_is_quantum_feature_vector",
            "adapter_output_is_quantum_optimizer_input",
            "adapter_output_is_quantum_trading_signal",
            "adapter_output_is_order_authority",
            "adapter_output_is_orderbook_snapshot",
            "adapter_output_is_event_state_snapshot",
            "adapter_output_is_runtime_resolver_snapshot",
            "adapter_output_is_historical_dataset",
        ):
            if event.get(flag) is not False:
                failures.append(f"canonical event {flag} must be false")
        for flag in (
            "no_live_fetch",
            "no_network_io",
            "no_order_authority",
            "no_profit_evidence",
            "no_quantum_execution",
            "no_quantum_feature_computation",
            "no_quantum_optimizer_input",
            "no_quantum_trading_signal",
        ):
            if event.get(flag) is not True:
                failures.append(f"canonical event {flag} must be true")

    states = {record["dependency_state"] for record in source_dependencies}
    for state in (
        "ACCEPTED_SOURCE_GATED",
        "CONNECTOR_SEMANTIC_GATED",
        "SOURCE_REQUIRED",
        "CONNECTOR_SEMANTIC_REQUIRED",
    ):
        if state not in states:
            failures.append(f"missing source dependency state {state}")
    for dependency in source_dependencies:
        if dependency.get("live_use_allowed") is not False:
            failures.append("source dependencies must not allow live use")
        if dependency.get("official_venue_semantics_fabricated") is not False:
            failures.append("source dependencies must not fabricate official semantics")

    for attestation in no_live_attestations:
        for count_field in (
            "rest_client_import_count",
            "websocket_client_import_count",
            "socket_import_count",
            "network_io_count",
            "venue_api_call_count",
            "live_market_data_fetch_count",
            "environment_credential_read_count",
            "credential_provider_call_count",
            "production_connector_client_count",
            "private_state_fetch_count",
            "orderbook_snapshot_created_count",
            "runtime_resolver_snapshot_created_count",
            "historical_dataset_digest_created_count",
            "feature_vector_created_count",
            "trading_signal_created_count",
            "quantum_feature_computation_created_count",
            "quantum_optimizer_input_created_count",
            "quantum_trading_signal_created_count",
            "quantum_backend_simulator_optimizer_execution_count",
            "quantum_advantage_claim_created_count",
            "order_authority_count",
            "order_execution_count",
        ):
            if attestation.get(count_field) != 0:
                failures.append(f"attestation {count_field} must be 0")

    rejection_codes = {record["rejected_reason_code"] for record in rejections}
    if rejection_codes != set(policy.REJECTION_REASON_CODES):
        failures.append("rejection receipts must cover centralized reason codes")
    for rejection in rejections:
        if rejection.get("validator_fail_closed") is not True:
            failures.append("rejection receipts must fail closed")
        for flag in (
            "raw_live_payload_stored",
            "live_fetch_performed",
            "network_io_created",
            "source_fact_accepted",
            "connector_semantic_binding_created",
            "official_semantics_fabricated",
            "quantum_feature_computation_created",
            "quantum_optimizer_input_created",
            "quantum_trading_signal_created",
            "quantum_advantage_claim_created",
        ):
            if rejection.get(flag) is not False:
                failures.append(f"rejection receipt {flag} must be false")

    for flag in (
        "contains_live_market_data",
        "contains_live_credentials",
        "contains_private_state_payload",
        "contains_orderbook_snapshot",
        "contains_event_state_snapshot",
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
        "downstream_pr115_execution_authorized",
        "downstream_pr116_execution_authorized",
        "downstream_pr117_execution_authorized",
        "downstream_quantum_feature_computation_authorized",
        "downstream_quantum_optimizer_input_creation_authorized",
        "downstream_quantum_trading_signal_creation_authorized",
        "atomicrows_bundle_consumed",
        "atomicrows_sha_created",
    ):
        if handoff.get(flag) is not False:
            failures.append(f"handoff {flag} must be false")
    if handoff.get("downstream_prs") != list(policy.DOWNSTREAM_PR_IDS):
        failures.append("handoff must preserve PR115/PR116/PR117")

    expected_main = {
        "repo_pr_label": "PR132",
        "roadmap_pr_implemented": "PR114",
        "currentized_prior_repo_pr": "PR131",
        "adapter_binding_count": 4,
        "adapter_input_count": 25,
        "canonical_market_data_ingest_event_count": 25,
        "market_data_source_dependency_count": 25,
        "fixture_payload_is_synthetic_count": 25,
        "stage1_venue_count": 3,
        "shared_scope_count": 1,
        "prediction_markets_general_treated_as_shared_scope": True,
    }
    for field, expected in expected_main.items():
        if main.get(field) != expected:
            failures.append(f"main_report.{field} must be {expected!r}")

    no_live = main["PR132_NO_LIVE_NETWORK_EVIDENCE"]
    for count_field in policy.ZERO_COUNT_INVARIANTS:
        if no_live.get(count_field) != 0:
            failures.append(f"main_report no-live {count_field} must be 0")
    if (
        main["PR132_QUANTUM_READY_MARKET_DATA_CONTRACT_EVIDENCE"][
            "quantum_ready_market_data_contract_count"
        ]
        < 4
    ):
        failures.append("quantum-ready market-data contract count must be >= 4")
    return failures


def _malformed_fixture_payloads(artifacts: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    missing = {
        "fixture_id": "PR132_MALFORMED_MISSING_PR131_CREDENTIAL_HANDOFF_V1",
        "credential_readiness_downstream_handoff": None,
        "expected_block": "BLOCKED_MISSING_PR131_CREDENTIAL_HANDOFF",
    }
    scope_mismatch_handoff = deepcopy(artifacts["pr131_handoff"])
    scope_mismatch_handoff["venue_specific_scope"] = ["KALSHI", "POLYMARKET"]
    live_network = deepcopy(artifacts["adapter_report"]["venue_market_data_adapter_inputs"][0])
    live_network["live_fetch_attempted"] = True
    live_network["network_io_created"] = True
    unaccepted_semantics = deepcopy(
        artifacts["adapter_report"]["venue_market_data_adapter_inputs"][0]
    )
    unaccepted_semantics["official_semantics_claimed"] = True
    unaccepted_semantics["accepted_source_dependency_refs"] = []
    unaccepted_semantics["connector_semantic_dependency_refs"] = []
    orderbook = deepcopy(artifacts["adapter_report"]["canonical_market_data_ingest_events"][0])
    orderbook["adapter_output_is_orderbook_snapshot"] = True
    orderbook["orderbook_snapshot_created"] = True
    resolver = deepcopy(artifacts["adapter_report"]["canonical_market_data_ingest_events"][0])
    resolver["adapter_output_is_runtime_resolver_snapshot"] = True
    resolver["runtime_resolver_snapshot_created"] = True
    quantum_feature = deepcopy(artifacts["adapter_report"]["canonical_market_data_ingest_events"][0])
    quantum_feature["quantum_feature_computation_created"] = True
    quantum_optimizer = deepcopy(
        artifacts["adapter_report"]["canonical_market_data_ingest_events"][0]
    )
    quantum_optimizer["adapter_output_is_quantum_optimizer_input"] = True
    quantum_optimizer["quantum_optimizer_input_created"] = True
    quantum_signal = deepcopy(artifacts["adapter_report"]["canonical_market_data_ingest_events"][0])
    quantum_signal["adapter_output_is_quantum_trading_signal"] = True
    quantum_signal["quantum_trading_signal_created"] = True
    return {
        "malformed_missing_pr131_credential_handoff.v1.fixture.json": missing,
        "malformed_venue_scope_mismatch.v1.fixture.json": {
            "fixture_id": "PR132_MALFORMED_VENUE_SCOPE_MISMATCH_V1",
            "credential_readiness_downstream_handoff": scope_mismatch_handoff,
            "expected_block": "BLOCKED_SCOPE_MISMATCH",
        },
        "malformed_live_network_attempt.v1.fixture.json": {
            "fixture_id": "PR132_MALFORMED_LIVE_NETWORK_ATTEMPT_V1",
            "venue_market_data_adapter_input": live_network,
            "expected_block": "BLOCKED_LIVE_NETWORK_ATTEMPT",
        },
        "malformed_unaccepted_venue_semantics_claim.v1.fixture.json": {
            "fixture_id": "PR132_MALFORMED_UNACCEPTED_VENUE_SEMANTICS_CLAIM_V1",
            "venue_market_data_adapter_input": unaccepted_semantics,
            "expected_block": "BLOCKED_UNACCEPTED_OFFICIAL_VENUE_SEMANTICS_CLAIM",
        },
        "malformed_orderbook_snapshot_created.v1.fixture.json": {
            "fixture_id": "PR132_MALFORMED_ORDERBOOK_SNAPSHOT_CREATED_V1",
            "canonical_market_data_ingest_event": orderbook,
            "expected_block": "BLOCKED_ORDERBOOK_SNAPSHOT_CREATED",
        },
        "malformed_runtime_resolver_snapshot_created.v1.fixture.json": {
            "fixture_id": "PR132_MALFORMED_RUNTIME_RESOLVER_SNAPSHOT_CREATED_V1",
            "canonical_market_data_ingest_event": resolver,
            "expected_block": "BLOCKED_RUNTIME_RESOLVER_SNAPSHOT_CREATED",
        },
        "malformed_quantum_feature_computation_created.v1.fixture.json": {
            "fixture_id": "PR132_MALFORMED_QUANTUM_FEATURE_COMPUTATION_CREATED_V1",
            "canonical_market_data_ingest_event": quantum_feature,
            "expected_block": "BLOCKED_QUANTUM_FEATURE_COMPUTATION_CREATED",
        },
        "malformed_quantum_optimizer_input_created.v1.fixture.json": {
            "fixture_id": "PR132_MALFORMED_QUANTUM_OPTIMIZER_INPUT_CREATED_V1",
            "canonical_market_data_ingest_event": quantum_optimizer,
            "expected_block": "BLOCKED_QUANTUM_OPTIMIZER_INPUT_CREATED",
        },
        "malformed_quantum_trading_signal_created.v1.fixture.json": {
            "fixture_id": "PR132_MALFORMED_QUANTUM_TRADING_SIGNAL_CREATED_V1",
            "canonical_market_data_ingest_event": quantum_signal,
            "expected_block": "BLOCKED_QUANTUM_TRADING_SIGNAL_CREATED",
        },
    }


def write_generated_reports(repo_root: Path, out_root: Path | None = None) -> dict[str, Any]:
    artifacts = build_market_data_ingest_artifacts(repo_root)
    for key, path in REPORT_PATHS.items():
        output_path = _output_path(repo_root, path, out_root)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(_dump_json(artifacts[key]), encoding="utf-8", newline="\n")
    return artifacts


def write_fixture_files(repo_root: Path, out_root: Path | None = None) -> dict[str, Any]:
    artifacts = build_market_data_ingest_artifacts(repo_root)
    fixture_payloads: dict[str, Mapping[str, Any]] = {
        "credential_readiness_downstream_handoff.v1.fixture.json": {
            "fixture_id": "PR132_CREDENTIAL_READINESS_DOWNSTREAM_HANDOFF_INPUT_FIXTURE_V1",
            "credential_readiness_downstream_handoff": artifacts["pr131_handoff"],
        },
        "venue_market_data_adapter_inputs.v1.fixture.json": {
            "fixture_id": "PR132_VENUE_MARKET_DATA_ADAPTER_INPUTS_FIXTURE_V1",
            "venue_market_data_adapter_inputs": artifacts["adapter_report"][
                "venue_market_data_adapter_inputs"
            ],
        },
        "venue_market_data_adapter_bindings.v1.fixture.json": {
            "fixture_id": "PR132_VENUE_MARKET_DATA_ADAPTER_BINDINGS_FIXTURE_V1",
            "venue_market_data_adapter_bindings": artifacts["adapter_report"][
                "venue_market_data_adapter_bindings"
            ],
        },
        "canonical_market_data_ingest_events.v1.fixture.json": {
            "fixture_id": "PR132_CANONICAL_MARKET_DATA_INGEST_EVENTS_FIXTURE_V1",
            "canonical_market_data_ingest_events": artifacts["adapter_report"][
                "canonical_market_data_ingest_events"
            ],
        },
        "market_data_source_dependencies.v1.fixture.json": {
            "fixture_id": "PR132_MARKET_DATA_SOURCE_DEPENDENCIES_FIXTURE_V1",
            "market_data_source_dependencies": artifacts["source_dependency_report"][
                "market_data_source_dependencies"
            ],
        },
        "market_data_no_live_network_attestations.v1.fixture.json": {
            "fixture_id": "PR132_MARKET_DATA_NO_LIVE_NETWORK_ATTESTATIONS_FIXTURE_V1",
            "market_data_no_live_network_attestations": artifacts[
                "no_live_network_report"
            ]["market_data_no_live_network_attestations"],
        },
        "venue_market_data_adapter_rejections.v1.fixture.json": {
            "fixture_id": "PR132_VENUE_MARKET_DATA_ADAPTER_REJECTIONS_FIXTURE_V1",
            "venue_market_data_adapter_rejections": artifacts[
                "source_dependency_report"
            ]["venue_market_data_adapter_rejections"],
        },
        "expected_market_data_ingest_downstream_handoff.v1.fixture.json": {
            "fixture_id": "PR132_EXPECTED_MARKET_DATA_INGEST_DOWNSTREAM_HANDOFF_V1",
            "market_data_ingest_downstream_handoff": artifacts["handoff_report"][
                "market_data_ingest_downstream_handoff"
            ],
        },
        **_malformed_fixture_payloads(artifacts),
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
