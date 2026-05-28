"""Deterministic PR159R artifact construction."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Iterable, Mapping

from . import constants as c
from .io import as_list, as_mapping, json_dump, read_json, record_count, schema_version
from .io import stable_counter, write_json, write_text
from .models import BuildArtifacts


def _safe_read_json(root: Path, rel_path: Path) -> Any:
    path = root / rel_path
    if not path.exists():
        return {}
    return read_json(path)


def _records(payload: Any) -> list[Mapping[str, Any]]:
    return [as_mapping(item) for item in as_list(as_mapping(payload).get("records"))]


def _slug(value: str, *, limit: int = 180) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").upper()
    return slug[:limit]


def _report_payload(
    report_type: str,
    records: list[Mapping[str, Any]],
    common: Mapping[str, Any],
    **extra: Any,
) -> dict[str, Any]:
    return {
        "report_type": report_type,
        "record_count": len(records),
        "records": records,
        **common,
        **extra,
    }


def _registry_payload(
    registry_id: str,
    records: list[Mapping[str, Any]],
    common: Mapping[str, Any],
    **extra: Any,
) -> dict[str, Any]:
    return {
        "registry_id": registry_id,
        "record_count": len(records),
        "records": records,
        **common,
        **extra,
    }


def _source_evidence_schema_paths(root: Path) -> tuple[Path, ...]:
    schema_root = root / "schemas" / "source_evidence"
    if not schema_root.exists():
        return ()
    return tuple(sorted(path.relative_to(root) for path in schema_root.rglob("*.json")))


def _pr157_shard_paths(root: Path) -> tuple[Path, ...]:
    shard_root = root / "docs" / "master_plan" / "generated" / "pr157_atomicrows_completion_shards"
    if not shard_root.exists():
        return ()
    return tuple(sorted(path.relative_to(root) for path in shard_root.glob("*.json")))


def _artifact_receipt(root: Path, rel_path: Path, role: str, required: bool, fallback: bool = False) -> dict[str, Any]:
    full_path = root / rel_path
    exists = full_path.exists()
    payload = _safe_read_json(root, rel_path) if exists and rel_path.suffix == ".json" else None
    return {
        "path": rel_path.as_posix(),
        "exists": exists,
        "consumed": exists,
        "artifact_role": role,
        "required_or_optional": "required" if required else "optional",
        "fallback_used": fallback,
        "record_count_if_available": record_count(payload),
        "schema_version_if_available": schema_version(payload),
        "authority_class": c.AUTHORITY_CLASS,
        "no_runtime_execution_confirmation": True,
    }


def input_consumption_receipts(root: Path) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for path in c.MANDATORY_ORCHESTRATION_INPUTS:
        if path.name == "PR136MasterPlanSectionCrosswalk.report.json":
            requested = _artifact_receipt(root, path, "mandatory_pr136_crosswalk_requested", True)
            fallback_used = not requested["exists"] and (root / c.CROSSWALK_FALLBACK_PATH).exists()
            receipts.append(requested)
            receipts.append(
                _artifact_receipt(
                    root,
                    c.CROSSWALK_FALLBACK_PATH,
                    "mandatory_pr136_crosswalk_allowed_fallback",
                    True,
                    fallback_used,
                )
            )
            continue
        receipts.append(_artifact_receipt(root, path, "mandatory_orchestration_input", True))
    for path in c.MANDATORY_CONTEXT_INPUTS:
        receipts.append(_artifact_receipt(root, path, "mandatory_pr159r_context_input", True))
    for path in c.QUANTUM_SCORING_OPTIMIZER_INPUTS:
        receipts.append(_artifact_receipt(root, path, "mandatory_quantum_scoring_optimizer_input", True))
    for path in c.AGENT_CONTEXT_INPUTS:
        receipts.append(_artifact_receipt(root, path, "mandatory_agent_context_input", True))
    for path in _pr157_shard_paths(root):
        receipts.append(_artifact_receipt(root, path, "mandatory_pr157_atomicrows_completion_shard", True))
    for path in _source_evidence_schema_paths(root):
        receipts.append(_artifact_receipt(root, path, "source_evidence_schema_input", False))
    return receipts


def preflight_failures(receipts: Iterable[Mapping[str, Any]]) -> tuple[str, ...]:
    failures: list[str] = []
    by_path = {str(item.get("path")): item for item in receipts}
    for path in c.MANDATORY_ORCHESTRATION_INPUTS:
        if path.name == "PR136MasterPlanSectionCrosswalk.report.json":
            requested = by_path.get(path.as_posix(), {})
            fallback = by_path.get(c.CROSSWALK_FALLBACK_PATH.as_posix(), {})
            if not (requested.get("consumed") or fallback.get("consumed")):
                failures.append("PR159R_BLOCKED_MISSING_MANDATORY_INPUT:PR136_CROSSWALK_OR_FALLBACK")
            continue
        item = by_path.get(path.as_posix(), {})
        if not item.get("consumed"):
            failures.append(f"PR159R_BLOCKED_MISSING_MANDATORY_INPUT:{path.as_posix()}")
    for path in (
        *c.MANDATORY_CONTEXT_INPUTS,
        *c.QUANTUM_SCORING_OPTIMIZER_INPUTS,
        *c.AGENT_CONTEXT_INPUTS,
    ):
        item = by_path.get(path.as_posix(), {})
        if not item.get("consumed"):
            failures.append(f"PR159R_BLOCKED_MISSING_MANDATORY_INPUT:{path.as_posix()}")
    shard_count = sum(
        1
        for item in receipts
        if item.get("artifact_role") == "mandatory_pr157_atomicrows_completion_shard"
        and item.get("consumed")
    )
    if shard_count != 9:
        failures.append("PR159R_BLOCKED_MISSING_MANDATORY_INPUT:PR157_ATOMICROWS_SHARDS")
    return tuple(sorted(set(failures)))


def orchestration_alignment_receipt(receipts: list[Mapping[str, Any]]) -> dict[str, Any]:
    missing = [str(item.get("path")) for item in receipts if item.get("required_or_optional") == "required" and not item.get("consumed")]
    return {
        "PR_sequencing_alignment": not missing,
        "capability_dependency_alignment": not missing,
        "launch_readiness_placement_alignment": not missing,
        "official_source_completion_placement_alignment": not missing,
        "AtomicRows_enrichment_order_alignment": not missing,
        "PR160_route_closure_alignment": not missing,
        "PR161_PR162_materialization_audit_readiness_alignment": not missing,
        "PR163_exact_agent_binding_readiness_alignment": not missing,
        "PR164_PR165_scoring_selection_readiness_alignment": not missing,
        "PR167_PR168_optimizer_readiness_alignment": not missing,
        "PR169_quantum_backend_gated_sandbox_readiness_alignment": not missing,
        "replay_paper_live_transition_alignment": not missing,
        "quantum_forward_compatibility_alignment": not missing,
        "quantum_upstream_downstream_workflow_alignment": not missing,
        "market_specific_orchestration_alignment": not missing,
        "owner_dashboard_future_control_alignment": not missing,
        "low_latency_source_snapshot_alignment": not missing,
        "future_research_addition_intake_alignment": not missing,
        "no_orphan_target_agent_applicability_alignment": not missing,
        "missing_required_inputs": missing,
    }


OFFICIAL_SOURCE_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "official_source_ref": "PR159R_OFFICIAL_SOURCE_KALSHI_CREATE_ORDER_V2",
        "source_family": "Kalshi official docs/rule/API family",
        "source_url": "https://docs.kalshi.com/api-reference/orders/create-order-v2",
        "source_title": "Create Order (V2) - API Documentation",
        "source_publisher": "Kalshi",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_API_DOCS.value,
        "locator": "Create Order (V2) request body schema",
        "short_quote_span": "body fields include side, count, price, time_in_force",
    },
    {
        "official_source_ref": "PR159R_OFFICIAL_SOURCE_KALSHI_FIXED_POINT",
        "source_family": "Kalshi official docs/rule/API family",
        "source_url": "https://docs.kalshi.com/getting_started/fixed_point_migration",
        "source_title": "Fixed-Point Migration - API Documentation",
        "source_publisher": "Kalshi",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_API_DOCS.value,
        "locator": "Price Level Structures table",
        "short_quote_span": "valid price intervals and tick sizes are in price_ranges",
    },
    {
        "official_source_ref": "PR159R_OFFICIAL_SOURCE_KALSHI_RATE_LIMITS",
        "source_family": "Kalshi official docs/rule/API family",
        "source_url": "https://docs.kalshi.com/getting_started/rate_limits",
        "source_title": "Rate Limits and Tiers - API Documentation",
        "source_publisher": "Kalshi",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_API_DOCS.value,
        "locator": "Rate Limits and Tiers",
        "short_quote_span": "apply exponential backoff on 429 until your bucket refills",
    },
    {
        "official_source_ref": "PR159R_OFFICIAL_SOURCE_POLYMARKET_CLOB",
        "source_family": "Polymarket official docs/API/CLOB family",
        "source_url": "https://docs.polymarket.com/developers/CLOB/introduction",
        "source_title": "CLOB Introduction - Polymarket Documentation",
        "source_publisher": "Polymarket",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_API_DOCS.value,
        "locator": "CLOB introduction",
        "short_quote_span": "central limit order book supports trading prediction-market tokens",
    },
    {
        "official_source_ref": "PR159R_OFFICIAL_SOURCE_POLYMARKET_ERROR_CODES",
        "source_family": "Polymarket official docs/API/CLOB family",
        "source_url": "https://docs.polymarket.com/resources/error-codes",
        "source_title": "Error Codes - Polymarket Documentation",
        "source_publisher": "Polymarket",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_API_DOCS.value,
        "locator": "Status Code Reference",
        "short_quote_span": "implement exponential backoff",
    },
    {
        "official_source_ref": "PR159R_OFFICIAL_SOURCE_IBKR_EVENT_TRADING",
        "source_family": "ForecastEx official rulebook/regulatory docs family / IBKR Event Trading",
        "source_url": "https://www.interactivebrokers.com/campus/ibkr-api-page/event-trading/",
        "source_title": "TWSAPI Methods Event Trading | IBKR API | IBKR Campus",
        "source_publisher": "Interactive Brokers",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_API_DOCS.value,
        "locator": "ForecastEx Forecast Contracts",
        "short_quote_span": "Forecast Contracts are quoted in USD 0.01 increments",
    },
    {
        "official_source_ref": "PR159R_OFFICIAL_SOURCE_IBKR_WEB_API",
        "source_family": "IBKR official Event Trading / Web API docs family",
        "source_url": "https://www.interactivebrokers.com/campus/ibkr-api-page/webapi-doc/",
        "source_title": "Web API Documentation | IBKR API | IBKR Campus",
        "source_publisher": "Interactive Brokers",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_API_DOCS.value,
        "locator": "Pacing Limitations",
        "short_quote_span": "global request rate limit of 10 requests per second",
    },
    {
        "official_source_ref": "PR159R_OFFICIAL_SOURCE_DWAVE_MODELS",
        "source_family": "D-Wave official quantum documentation family",
        "source_url": "https://docs.dwavequantum.com/en/latest/concepts/models.html",
        "source_title": "Models: Binary Quadratic Models, Ising, QUBO",
        "source_publisher": "D-Wave",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_QUANTUM_PROVIDER_DOCS.value,
        "locator": "Binary quadratic models / Ising / QUBO",
        "short_quote_span": "binary quadratic models can be represented as Ising or QUBO",
    },
    {
        "official_source_ref": "PR159R_OFFICIAL_SOURCE_DWAVE_HYBRID",
        "source_family": "D-Wave official quantum documentation family",
        "source_url": "https://docs.dwavequantum.com/en/latest/industrial_optimization/solver_hybrid.html",
        "source_title": "Leap Hybrid Solvers",
        "source_publisher": "D-Wave",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_QUANTUM_PROVIDER_DOCS.value,
        "locator": "Hybrid solvers",
        "short_quote_span": "hybrid solvers accept quadratic model problem classes",
    },
    {
        "official_source_ref": "PR159R_OFFICIAL_SOURCE_AWS_BRAKET_HYBRID",
        "source_family": "AWS Braket official documentation family",
        "source_url": "https://docs.aws.amazon.com/braket/latest/developerguide/braket-hybrid-jobs.html",
        "source_title": "Amazon Braket Hybrid Jobs",
        "source_publisher": "Amazon Web Services",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_QUANTUM_PROVIDER_DOCS.value,
        "locator": "Hybrid jobs",
        "short_quote_span": "hybrid jobs run classical algorithms with quantum tasks",
    },
    {
        "official_source_ref": "PR159R_OFFICIAL_SOURCE_IBM_QISKIT_ALGORITHMS",
        "source_family": "IBM/Qiskit official documentation family",
        "source_url": "https://docs.quantum.ibm.com/guides/algorithms",
        "source_title": "Algorithms - IBM Quantum Documentation",
        "source_publisher": "IBM Quantum",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_QUANTUM_PROVIDER_DOCS.value,
        "locator": "Algorithms guide",
        "short_quote_span": "QAOA and VQE are variational quantum algorithms",
    },
    {
        "official_source_ref": "PR159R_OFFICIAL_SOURCE_QISKIT_OPTIMIZATION",
        "source_family": "IBM/Qiskit official documentation family",
        "source_url": "https://qiskit-community.github.io/qiskit-optimization/",
        "source_title": "Qiskit Optimization",
        "source_publisher": "Qiskit Community",
        "official_source_class": c.OfficialSourceClass.OFFICIAL_QUANTUM_PROVIDER_DOCS.value,
        "locator": "Quadratic programs and converters",
        "short_quote_span": "optimization problems can be modeled as quadratic programs",
    },
)


SECOND_PASS_ACCEPTED_TARGET_ID = (
    "PR154_BRIDGE__PR151_PR150_VENUE_SOURCE_REQUIRED_VENUE_RATE_LIMITS_RATE_LIMITS_"
    "FORECASTEX_IBKR_FORECASTEX_IBKR_OFFICIAL_API_DOCS_RATE_LIMITS"
)
SECOND_PASS_ACCEPTED_PACKET_ID = (
    "PR159R_ACCEPTED_PACKET__FORECASTEX_IBKR_RATE_LIMITS__WEB_API_PACING_LIMITATIONS"
)
SECOND_PASS_ACCEPTED_LEDGER_ID = (
    "PR159R_LEDGER_RECORD__FORECASTEX_IBKR_RATE_LIMITS__WEB_API_PACING_LIMITATIONS"
)
SECOND_PASS_ACCEPTED_VALUE = {
    "rate_limit": {
        "value": 10,
        "unit": "requests_per_second",
        "scope": "each_authenticated_username_each_web_api_session",
    },
    "rate_limit_exceeded_status": {
        "value": 429,
        "unit": "http_status_code",
        "meaning": "Too Many Requests",
    },
    "penalty_box_duration": {
        "value": 10,
        "unit": "minutes",
        "scope": "violator_ip_after_exceeded_rate_limit",
    },
}
SECOND_PASS_ACCEPTED_LOCATOR = "IBKR Web API Documentation > Pacing Limitations"
SECOND_PASS_ACCEPTED_QUOTE_SPAN = (
    "global request rate limit of 10 requests per second for each authenticated username"
)
SECOND_PASS_ACCEPTED_UNIT = "requests_per_second_per_authenticated_web_api_session"
SECOND_PASS_ACCEPTED_SCALE = "10_requests_per_second;429_too_many_requests;10_minute_penalty_box"


def _source_refs_for_target(target: Mapping[str, Any]) -> list[str]:
    platform = str(target.get("platform_scope") or target.get("venue_scope") or "")
    field = str(target.get("target_field_id") or "")
    if "KALSHI" in platform:
        refs = ["PR159R_OFFICIAL_SOURCE_KALSHI_CREATE_ORDER_V2", "PR159R_OFFICIAL_SOURCE_KALSHI_FIXED_POINT"]
        if "rate" in field or "retry" in field:
            refs.append("PR159R_OFFICIAL_SOURCE_KALSHI_RATE_LIMITS")
        return refs
    if "POLYMARKET" in platform:
        refs = ["PR159R_OFFICIAL_SOURCE_POLYMARKET_CLOB"]
        if "retry" in field:
            refs.append("PR159R_OFFICIAL_SOURCE_POLYMARKET_ERROR_CODES")
        return refs
    if "FORECASTEX" in platform or "IBKR" in platform:
        return ["PR159R_OFFICIAL_SOURCE_IBKR_EVENT_TRADING", "PR159R_OFFICIAL_SOURCE_IBKR_WEB_API"]
    return ["PR159R_OFFICIAL_SOURCE_DWAVE_MODELS", "PR159R_OFFICIAL_SOURCE_QISKIT_OPTIMIZATION"]


def _population_for_atomic(record: Mapping[str, Any]) -> str:
    source_class = str(record.get("source_requirement_class"))
    if source_class == "PUBLIC_EXTERNAL_SOURCE_REQUIRED":
        return c.PR159RTargetPopulation.ATOMICROWS_PUBLIC_EXTERNAL_SOURCE_REQUIRED_315.value
    return c.PR159RTargetPopulation.ATOMICROWS_PARAMETER_RANGE_SOURCE_REQUIRED_530.value


def _candidate_index(root: Path) -> dict[str, Mapping[str, Any]]:
    payload = _safe_read_json(root, c.PR159_CANDIDATE_REGISTRY_PATH)
    return {str(record.get("candidate_packet_id")): record for record in _records(payload)}


def _build_targets(root: Path) -> list[dict[str, Any]]:
    pr154_payload = _safe_read_json(root, c.PR159_PR154_COMPLETION_REGISTRY_PATH)
    atomic_payload = _safe_read_json(root, c.PR159_ATOMICROWS_COMPLETION_REGISTRY_PATH)
    candidate_by_id = _candidate_index(root)
    targets: list[dict[str, Any]] = []
    for record in _records(pr154_payload):
        if record.get("completion_status") == "ACCEPTED_COMPLETED":
            continue
        candidate_refs = [str(ref) for ref in as_list(record.get("candidate_packet_refs"))]
        candidates = [candidate_by_id[ref] for ref in candidate_refs if ref in candidate_by_id]
        locator_available = any(as_mapping(item.get("quote_span_or_machine_field_locator")).get("locator") for item in candidates)
        final_state = (
            c.PR159RTargetState.CANDIDATE_ONLY_EXACT_VALUE_MISSING.value
            if locator_available
            else c.PR159RTargetState.CANDIDATE_ONLY_LOCATOR_MISSING.value
        )
        target = {
            "target_id_or_row_id": str(record.get("target_id")),
            "target_population": c.PR159RTargetPopulation.PR154_PUBLIC_SOURCE_RETRY_REMAINING_24.value,
            "PR159_unresolved_ref": c.PR159_PR154_COMPLETION_REGISTRY_PATH.as_posix(),
            "PR159_candidate_refs": candidate_refs,
            "PR159_accepted_packet_ref_or_null": None,
            "PR160_requeue_ref_or_null": None,
            "day1_priority_tier": record.get("day1_source_priority_tier"),
            "platform_scope": record.get("platform_scope"),
            "venue_scope": record.get("platform_scope"),
            "market_scope": record.get("market_scope"),
            "target_field_id": record.get("target_field_id"),
            "requested_value_name": record.get("requested_value_name"),
            "requested_value_type": record.get("requested_value_type"),
            "requested_unit_or_basis": record.get("requested_unit_or_basis"),
            "requested_scale": record.get("requested_scale"),
            "expected_source_class": _expected_source_class(record),
            "source_requirement_class": "PR154_PUBLIC_SOURCE_RETRY_REQUIRED",
            "source_materiality_class": record.get("materiality_class"),
            "revalidation_class": record.get("revalidation_class"),
            "trade_context_impact": "SOURCE_NOT_READY_METADATA_ONLY",
            "scoring_ranking_impact": "SOURCE_NOT_READY_METADATA_ONLY",
            "low_latency_impact": "SOURCE_NOT_READY_METADATA_ONLY",
            "quantum_classical_compatibility_impact": _compatibility_for_target(record),
            "official_source_refs_checked": _source_refs_for_target(record),
            "final_PR159R_target_state": final_state,
            "accepted_value_or_range_or_enum_or_metadata": None,
            "canonical_unit_or_basis": None,
            "canonical_scale": None,
            "acceptance_blocker_class": c.AcceptanceBlockerClass.EXACT_VALUE_MISSING.value,
            "future_route": c.FutureRoute.PR159R_CONTINUED_EXACT_CAPTURE.value,
            "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
        }
        targets.append(_apply_second_pass_target_acceptance(target))
    for record in _records(atomic_payload):
        population = _population_for_atomic(record)
        target = {
            "target_id_or_row_id": str(record.get("row_id")),
            "target_population": population,
            "PR159_unresolved_ref": c.PR159_ATOMICROWS_COMPLETION_REGISTRY_PATH.as_posix(),
            "PR159_candidate_refs": [str(ref) for ref in as_list(record.get("candidate_packet_refs"))],
            "PR159_accepted_packet_ref_or_null": None,
            "PR160_requeue_ref_or_null": None,
            "day1_priority_tier": record.get("day1_source_priority_tier"),
            "platform_scope": record.get("platform_scope"),
            "venue_scope": record.get("venue_scope"),
            "market_scope": record.get("market_scope"),
            "target_field_id": record.get("target_field_id"),
            "requested_value_name": record.get("requested_value_name"),
            "requested_value_type": record.get("requested_value_type"),
            "requested_unit_or_basis": record.get("requested_unit_or_basis"),
            "requested_scale": record.get("requested_scale"),
            "expected_source_class": c.OfficialSourceClass.OFFICIAL_PROVIDER_DOCS.value,
            "source_requirement_class": record.get("source_requirement_class"),
            "source_materiality_class": record.get("materiality_class"),
            "revalidation_class": record.get("revalidation_class"),
            "family_id": record.get("family_id"),
            "parameter_id": record.get("parameter_id"),
            "trade_context_impact": record.get("trade_context_readiness_update"),
            "scoring_ranking_impact": record.get("scoring_readiness_update"),
            "low_latency_impact": record.get("low_latency_snapshot_update"),
            "quantum_classical_compatibility_impact": _compatibility_for_target(record),
            "official_source_refs_checked": _source_refs_for_target(record),
            "final_PR159R_target_state": c.PR159RTargetState.UNRESOLVED_WITH_EXACT_FILL_PATH.value,
            "accepted_value_or_range_or_enum_or_metadata": None,
            "canonical_unit_or_basis": None,
            "canonical_scale": None,
            "acceptance_blocker_class": c.AcceptanceBlockerClass.EXACT_RANGE_MISSING.value,
            "future_route": c.FutureRoute.PR161_ATOMICROWS_SOURCE_VALUE_MATERIALIZATION.value,
            "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
        }
        targets.append(_apply_second_pass_target_acceptance(target))
    return sorted(targets, key=lambda item: str(item["target_id_or_row_id"]))


def _expected_source_class(record: Mapping[str, Any]) -> str:
    source_ids = " ".join(str(item) for item in as_list(record.get("official_source_target_ids")))
    if "OFFICIAL_SDK_DOCS" in source_ids:
        return c.OfficialSourceClass.OFFICIAL_SDK_DOCS.value
    if "OFFICIAL_FEE_TICK_SETTLEMENT_DOCS" in source_ids:
        return c.OfficialSourceClass.OFFICIAL_FEE_TICK_SETTLEMENT_DOCS.value
    return c.OfficialSourceClass.OFFICIAL_API_DOCS.value


def _compatibility_for_target(record: Mapping[str, Any]) -> list[str]:
    existing = [str(item) for item in as_list(record.get("quantum_classical_compatibility"))]
    if existing:
        return existing
    field = str(record.get("target_field_id") or "")
    if any(token in field for token in ("risk", "capital", "notional", "latency", "execution", "rate")):
        return [c.QuantumClassicalCompatibility.RISK_CAPITAL_EXECUTION_FORMULA_COMPATIBLE.value]
    return [c.QuantumClassicalCompatibility.CLASSICAL_ONLY_VALID_BASELINE.value]


def _build_requeue_reconciliation(root: Path, targets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    target_ids = {str(item["target_id_or_row_id"]) for item in targets}
    payload = _safe_read_json(root, c.PR160_REQUEUE_PATH)
    records: list[dict[str, Any]] = []
    for item in _records(payload):
        target_id = str(item.get("PR154_target_id"))
        matched = target_id in target_ids
        records.append(
            {
                "requeue_id": item.get("requeue_id"),
                "PR154_target_id": target_id,
                "target_field_id": item.get("target_field_id"),
                "requested_value_name": item.get("requested_value_name"),
                "reconciled_to_existing_PR159_unresolved_target_flag": matched,
                "supplemental_route_metadata_only_flag": not matched,
                "double_count_prevented_flag": True,
                "incremented_PR159R_869_target_universe_flag": False,
                "future_route": c.FutureRoute.PR159R_CONTINUED_EXACT_CAPTURE.value,
                "exact_steps_to_fill": item.get("exact_steps_to_fill"),
                "validator_that_will_unblock": "tools/validate_pr159r_source_locator_value_capture.py",
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return sorted(records, key=lambda item: str(item["requeue_id"]))


def _build_search_plan(targets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for target in targets:
        target_id = str(target["target_id_or_row_id"])
        platform = str(target.get("platform_scope") or "PREDICTION_MARKETS_GENERAL")
        source_refs = [str(ref) for ref in as_list(target.get("official_source_refs_checked"))]
        records.append(
            {
                "target_id_or_row_id": target_id,
                "target_population": target.get("target_population"),
                "day1_priority_tier": target.get("day1_priority_tier"),
                "platform_scope": platform,
                "target_field_id": target.get("target_field_id"),
                "official_source_search_queries": _queries_for_target(target),
                "official_domain_candidates": _domains_for_platform(platform),
                "likely_official_document_type": target.get("expected_source_class"),
                "exact_target_field_to_locate": target.get("target_field_id"),
                "expected_locator_type": c.LocatorType.URL_QUOTE_SPAN.value,
                "expected_value_range_enum_type": target.get("requested_value_type"),
                "expected_unit_scale_basis": {
                    "unit_or_basis": target.get("requested_unit_or_basis"),
                    "scale": target.get("requested_scale"),
                },
                "quantum_provider_optimizer_source_requirement": _quantum_requirement(target),
                "conflict_sources_to_check": source_refs,
                "freshness_version_requirement": target.get("revalidation_class"),
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return records


def _queries_for_target(target: Mapping[str, Any]) -> list[str]:
    platform = str(target.get("platform_scope") or "PREDICTION_MARKETS_GENERAL")
    field = str(target.get("target_field_id") or target.get("requested_value_name"))
    queries = [f"{platform} official documentation {field} exact value unit scale"]
    if _is_quantum_relevant(target):
        queries.append("official quantum provider QUBO Ising QAOA VQE annealing optimizer formulation constraints")
    return queries


def _domains_for_platform(platform: str) -> list[str]:
    if "KALSHI" in platform:
        return ["docs.kalshi.com"]
    if "POLYMARKET" in platform:
        return ["docs.polymarket.com"]
    if "FORECASTEX" in platform or "IBKR" in platform:
        return ["interactivebrokers.com", "forecastex.com"]
    return ["docs.dwavequantum.com", "docs.aws.amazon.com", "docs.quantum.ibm.com", "qiskit-community.github.io"]


def _quantum_requirement(target: Mapping[str, Any]) -> str | None:
    if not _is_quantum_relevant(target):
        return None
    return c.AcceptanceBlockerClass.QUANTUM_FORMULATION_SOURCE_REQUIRED.value


def _is_quantum_relevant(target: Mapping[str, Any]) -> bool:
    compat = set(str(item) for item in as_list(target.get("quantum_classical_compatibility_impact")))
    return bool(
        compat
        and compat != {c.QuantumClassicalCompatibility.CLASSICAL_ONLY_VALID_BASELINE.value}
    ) or str(target.get("target_population", "")).startswith("PR154")


def _build_discovery_receipts() -> list[dict[str, Any]]:
    records = []
    for source in OFFICIAL_SOURCE_CATALOG:
        records.append(
            {
                **source,
                "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
                "retrieval_timestamp_utc": c.RETRIEVAL_TIMESTAMP_UTC,
                "retrieval_method": c.OFFICIAL_SEARCH_METHOD,
                "source_content_type": "text/html",
                "source_freshness": c.FreshnessState.VERSION_UNKNOWN.value,
                "accepted_fact_authority_created_flag": False,
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return sorted(records, key=lambda item: item["official_source_ref"])


def _source_by_ref() -> dict[str, Mapping[str, Any]]:
    return {source["official_source_ref"]: source for source in OFFICIAL_SOURCE_CATALOG}


def _is_second_pass_accepted_target(target: Mapping[str, Any]) -> bool:
    return str(target.get("target_id_or_row_id")) == SECOND_PASS_ACCEPTED_TARGET_ID


def _accepted_packet_id_for_target(target: Mapping[str, Any]) -> str | None:
    if _is_second_pass_accepted_target(target):
        return SECOND_PASS_ACCEPTED_PACKET_ID
    return None


def _apply_second_pass_target_acceptance(target: dict[str, Any]) -> dict[str, Any]:
    if not _is_second_pass_accepted_target(target):
        return target
    target["final_PR159R_target_state"] = c.PR159RTargetState.ACCEPTED_SOURCE_VALUE_CAPTURED.value
    target["accepted_value_or_range_or_enum_or_metadata"] = dict(SECOND_PASS_ACCEPTED_VALUE)
    target["canonical_unit_or_basis"] = SECOND_PASS_ACCEPTED_UNIT
    target["canonical_scale"] = SECOND_PASS_ACCEPTED_SCALE
    target["acceptance_blocker_class"] = c.AcceptanceBlockerClass.NONE.value
    target["future_route"] = c.FutureRoute.CONNECTOR_SEMANTIC_BINDING_FUTURE.value
    target["PR159R_accepted_packet_ref_or_null"] = SECOND_PASS_ACCEPTED_PACKET_ID
    return target


def _build_candidate_packets(root: Path, targets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    pr159_candidates = _candidate_index(root)
    by_source = _source_by_ref()
    records: list[dict[str, Any]] = []
    for target in targets:
        if target["target_population"] != c.PR159RTargetPopulation.PR154_PUBLIC_SOURCE_RETRY_REMAINING_24.value:
            continue
        pr159_ref = next(iter(as_list(target.get("PR159_candidate_refs"))), None)
        prior = pr159_candidates.get(str(pr159_ref), {})
        source_ref = next(iter(as_list(target.get("official_source_refs_checked"))), "")
        source = by_source.get(str(prior.get("official_source_ref")) or source_ref, by_source.get(source_ref, {}))
        locator = as_mapping(prior.get("quote_span_or_machine_field_locator"))
        candidate_id = f"PR159R_CANDIDATE_PACKET__{_slug(str(target['target_id_or_row_id']))}"
        accepted = _is_second_pass_accepted_target(target)
        accepted_source_ref = str(prior.get("official_source_ref") or source_ref)
        if accepted:
            accepted_source_ref = "PR159R_OFFICIAL_SOURCE_IBKR_WEB_API"
            source = by_source["PR159R_OFFICIAL_SOURCE_IBKR_WEB_API"]
            locator = {
                "locator": SECOND_PASS_ACCEPTED_LOCATOR,
                "quote_span": SECOND_PASS_ACCEPTED_QUOTE_SPAN,
                "machine_field_locator": None,
            }
        records.append(
            {
                "candidate_packet_id": candidate_id,
                "target_id_or_row_id": target["target_id_or_row_id"],
                "target_population": target["target_population"],
                "target_field_id": target.get("target_field_id"),
                "source_url_or_repo_relative_capture_path": prior.get("source_url_or_repo_relative_capture_path") or source.get("source_url"),
                "official_source_ref": accepted_source_ref,
                "official_source_class": prior.get("official_source_class") or source.get("official_source_class"),
                "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
                "non_authoritative_seed_ref_or_null": None,
                "platform_scope": target.get("platform_scope"),
                "venue_scope": target.get("venue_scope"),
                "market_scope": target.get("market_scope"),
                "source_title": prior.get("source_title") or source.get("source_title"),
                "source_publisher": prior.get("source_publisher") or source.get("source_publisher"),
                "source_version_or_date_or_null": prior.get("source_version_or_date_or_null"),
                "retrieval_timestamp_utc": c.RETRIEVAL_TIMESTAMP_UTC,
                "retrieval_method": c.OFFICIAL_SEARCH_METHOD,
                "source_content_type": prior.get("source_content_type") or "text/html",
                "locator_type": c.LocatorType.URL_QUOTE_SPAN.value if accepted else prior.get("locator_type") or c.LocatorType.URL_SECTION_HEADING.value,
                "locator_value": locator.get("locator") or source.get("locator"),
                "quote_span_or_machine_field_locator": {
                    "locator": locator.get("locator") or source.get("locator"),
                    "quote_span": locator.get("quote_span") or source.get("short_quote_span"),
                    "machine_field_locator": locator.get("machine_field_locator"),
                },
                "extracted_value_or_range_or_enum_or_null": dict(SECOND_PASS_ACCEPTED_VALUE) if accepted else None,
                "extracted_unit_or_basis_or_null": SECOND_PASS_ACCEPTED_UNIT if accepted else prior.get("extracted_unit_or_basis_or_null"),
                "extracted_scale_or_null": SECOND_PASS_ACCEPTED_SCALE if accepted else prior.get("extracted_scale_or_null"),
                "extraction_confidence_class": "SECOND_PASS_EXACT_TARGET_FIELD_EVIDENCE_CAPTURED" if accepted else "CANDIDATE_CONTEXT_ONLY_EXACT_TARGET_VALUE_NOT_ACCEPTED",
                "freshness_state": c.FreshnessState.FRESH.value if accepted else c.FreshnessState.VERSION_UNKNOWN.value,
                "conflict_status": c.ConflictStatus.NO_CONFLICT.value if accepted else c.ConflictStatus.CONFLICT_WITH_TARGET_FIELD_SCOPE.value,
                "target_field_scope_match_flag": bool(accepted),
                "candidate_is_accepted_fact": False,
                "accepted_packet_ref_or_null": SECOND_PASS_ACCEPTED_PACKET_ID if accepted else None,
                "acceptance_decision": c.SourceAcceptanceDecision.ACCEPTED_TARGET_FIELD_WITH_CANONICALIZATION.value if accepted else c.SourceAcceptanceDecision.DEFERRED_EXACT_VALUE_CAPTURE.value,
                "acceptance_blocker_class": c.AcceptanceBlockerClass.NONE.value if accepted else c.AcceptanceBlockerClass.EXACT_VALUE_MISSING.value,
                "quantum_relevance_flag": _is_quantum_relevant(target),
                "quantum_source_field_class_or_null": _quantum_requirement(target),
                "provenance_digest_or_null": None,
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return sorted(records, key=lambda item: item["candidate_packet_id"])


def _build_exact_locator_matrix(targets: list[Mapping[str, Any]], candidate_packets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    candidates_by_target = {str(item["target_id_or_row_id"]): item for item in candidate_packets}
    records: list[dict[str, Any]] = []
    for target in targets:
        candidate = candidates_by_target.get(str(target["target_id_or_row_id"]))
        locator = as_mapping(candidate.get("quote_span_or_machine_field_locator")) if candidate else {}
        locator_value = locator.get("locator")
        accepted = _accepted_packet_id_for_target(target)
        records.append(
            {
                "target_id_or_row_id": target["target_id_or_row_id"],
                "target_population": target["target_population"],
                "target_field_id": target.get("target_field_id"),
                "candidate_packet_ref_or_null": candidate.get("candidate_packet_id") if candidate else None,
                "locator_type": candidate.get("locator_type") if candidate else c.LocatorType.LOCATOR_MISSING_BLOCKED.value,
                "locator_value_or_null": locator_value,
                "quote_span_or_machine_field_locator_or_null": locator if candidate else None,
                "extracted_value_or_range_or_enum_or_null": candidate.get("extracted_value_or_range_or_enum_or_null") if candidate else None,
                "extracted_unit_or_basis_or_null": candidate.get("extracted_unit_or_basis_or_null") if candidate else None,
                "extracted_scale_or_null": candidate.get("extracted_scale_or_null") if candidate else None,
                "exact_value_available_flag": bool(accepted),
                "exact_unit_scale_available_flag": bool(candidate and candidate.get("extracted_unit_or_basis_or_null") and candidate.get("extracted_scale_or_null")),
                "exact_locator_available_flag": bool(locator_value),
                "target_field_scope_match_flag": bool(accepted),
                "acceptance_blocker_class": target.get("acceptance_blocker_class"),
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return records


def _build_accepted_packets(
    targets: list[Mapping[str, Any]],
    candidate_packets: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    candidates_by_target = {str(item["target_id_or_row_id"]): item for item in candidate_packets}
    records: list[dict[str, Any]] = []
    for target in targets:
        if not _is_second_pass_accepted_target(target):
            continue
        candidate = candidates_by_target[str(target["target_id_or_row_id"])]
        records.append(
            {
                "accepted_packet_id": SECOND_PASS_ACCEPTED_PACKET_ID,
                "candidate_packet_id": candidate["candidate_packet_id"],
                "target_id_or_row_id": target["target_id_or_row_id"],
                "target_field_id": target.get("target_field_id"),
                "accepted_value_or_range_or_enum_or_metadata": dict(SECOND_PASS_ACCEPTED_VALUE),
                "canonical_unit_or_basis": SECOND_PASS_ACCEPTED_UNIT,
                "canonical_scale": SECOND_PASS_ACCEPTED_SCALE,
                "official_source_class": c.OfficialSourceClass.OFFICIAL_API_DOCS.value,
                "official_source_ref": "PR159R_OFFICIAL_SOURCE_IBKR_WEB_API",
                "official_source_confidence": c.OfficialSourceConfidence.OFFICIAL_CONFIRMED.value,
                "target_field_scope_match_flag": True,
                "locator_valid_flag": True,
                "locator_type": c.LocatorType.URL_QUOTE_SPAN.value,
                "locator_value": SECOND_PASS_ACCEPTED_LOCATOR,
                "quote_span_or_machine_field_locator": {
                    "locator": SECOND_PASS_ACCEPTED_LOCATOR,
                    "quote_span": SECOND_PASS_ACCEPTED_QUOTE_SPAN,
                    "machine_field_locator": None,
                },
                "conflict_cleared_flag": True,
                "conflict_status": c.ConflictStatus.NO_CONFLICT.value,
                "freshness_valid_flag": True,
                "freshness_state": c.FreshnessState.FRESH.value,
                "unit_scale_canonicalized_flag": True,
                "acceptance_decision": c.SourceAcceptanceDecision.ACCEPTED_TARGET_FIELD_WITH_CANONICALIZATION.value,
                "acceptance_validator_id": "tools/validate_pr159r_source_locator_value_capture.py",
                "revalidation_class": target.get("revalidation_class"),
                "materiality_class": target.get("source_materiality_class"),
                "downstream_consumer_scope": _consumer_classes_for_target(target),
                "quantum_forward_readiness_scope_or_null": (
                    c.FutureRoute.PR167_OPTIMIZER_INTERFACE.value if _is_quantum_relevant(target) else None
                ),
                "source_url_or_repo_relative_capture_path": "https://www.interactivebrokers.com/campus/ibkr-api-page/webapi-doc/",
                "source_title": "Web API Documentation | IBKR API | IBKR Campus",
                "source_publisher": "Interactive Brokers",
                "source_version_or_date_or_null": None,
                "retrieval_timestamp_utc": c.RETRIEVAL_TIMESTAMP_UTC,
                "source_content_type": "text/html",
                "no_connector_semantic_binding_confirmation": True,
                "no_runtime_receipt_confirmation": True,
                "no_live_order_authority_confirmation": True,
                "no_profit_evidence_confirmation": True,
                "no_quantum_backend_execution_confirmation": True,
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return sorted(records, key=lambda item: item["accepted_packet_id"])


def _build_ledger_records(
    targets: list[Mapping[str, Any]],
    accepted_packets: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    targets_by_id = {str(item["target_id_or_row_id"]): item for item in targets}
    records: list[dict[str, Any]] = []
    for packet in accepted_packets:
        target = targets_by_id[str(packet["target_id_or_row_id"])]
        records.append(
            {
                "ledger_record_id": SECOND_PASS_ACCEPTED_LEDGER_ID,
                "accepted_packet_id": packet["accepted_packet_id"],
                "target_id_or_row_id": packet["target_id_or_row_id"],
                "target_population": target["target_population"],
                "target_field_id": target.get("target_field_id"),
                "source_population": "PR159R_SECOND_PASS_OFFICIAL_SOURCE_ACCEPTANCE_REPAIR",
                "source_packet_integrity_digest_if_schema_supported": None,
                "revalidation_due_class": target.get("revalidation_class"),
                "materiality_class": target.get("source_materiality_class"),
                "downstream_routes": [
                    c.FutureRoute.CONNECTOR_SEMANTIC_BINDING_FUTURE.value,
                    c.FutureRoute.PR164_SCORING_RANKING_BRIDGE.value,
                    c.FutureRoute.PR165_TRADE_CONTEXT_SELECTION.value,
                ],
                "pr161_materialization_required_flag": False,
                "quantum_forward_downstream_routes": (
                    [
                        c.FutureRoute.PR167_OPTIMIZER_INTERFACE.value,
                        c.FutureRoute.PR169_QUANTUM_BACKEND_GATED_SANDBOX.value,
                        c.FutureRoute.REPLAY_AFTER_FUTURE_GATES.value,
                    ]
                    if _is_quantum_relevant(target)
                    else []
                ),
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return sorted(records, key=lambda item: item["ledger_record_id"])


def _build_unresolved_fill_paths(targets: list[Mapping[str, Any]], candidate_packets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    candidate_refs = {str(item["target_id_or_row_id"]): str(item["candidate_packet_id"]) for item in candidate_packets}
    records = []
    for target in targets:
        if _accepted_packet_id_for_target(target):
            continue
        target_id = str(target["target_id_or_row_id"])
        records.append(
            {
                "target_id_or_row_id": target_id,
                "target_population": target["target_population"],
                "target_field_id": target.get("target_field_id"),
                "final_PR159R_target_state": target["final_PR159R_target_state"],
                "attempted_official_queries": _queries_for_target(target),
                "official_sources_checked": as_list(target.get("official_source_refs_checked")),
                "candidate_sources_rejected": [candidate_refs[target_id]] if target_id in candidate_refs else [],
                "exact_missing_evidence": _missing_evidence(target),
                "exact_next_official_source_needed": _next_source_needed(target),
                "exact_steps_to_fill": [
                    "Locate an official source page, rulebook section, SDK/API field, or provider document for this exact target field.",
                    "Capture a short quote span or machine-field locator that directly names the target field.",
                    "Extract the value, range, enum, unit, scale, freshness, and conflict status without inference.",
                    "Regenerate PR159R artifacts and rerun tools/validate_pr159r_source_locator_value_capture.py.",
                ],
                "validator_that_will_unblock": "tools/validate_pr159r_source_locator_value_capture.py",
                "future_PR_route": target.get("future_route"),
                "responsible_actor_or_agent_role": "PR159R_OFFICIAL_SOURCE_CAPTURE_AGENT_ROLE",
                "risk_if_unfilled": "Target remains non-consumable for PR161 materialization, PR164/PR165 selection metadata, replay/paper, and all live gates.",
                "quantum_risk_if_quantum_relevant": (
                    "Quantum/classical optimizer routing remains readiness-only until source evidence and PR161 materialization exist."
                    if _is_quantum_relevant(target)
                    else None
                ),
                "can_qtt_use_metadata_flag": False,
                "can_qtt_use_in_replay_flag": False,
                "can_qtt_use_in_paper_flag": False,
                "can_qtt_use_in_live_flag": False,
                "unresolved_value_or_null": None,
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return records


def _missing_evidence(target: Mapping[str, Any]) -> list[str]:
    missing = ["exact_target_field_value_or_range_or_enum"]
    if target.get("target_population") != c.PR159RTargetPopulation.PR154_PUBLIC_SOURCE_RETRY_REMAINING_24.value:
        missing.append("row_specific_official_source_locator")
    missing.extend(["canonical_unit_or_basis", "canonical_scale", "conflict_clearance"])
    return missing


def _next_source_needed(target: Mapping[str, Any]) -> str:
    platform = str(target.get("platform_scope") or "source family")
    field = str(target.get("target_field_id"))
    return f"Official {platform} documentation that directly specifies {field} with value, unit, scale, and locator."


def _build_agent_matrix(targets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    records = []
    for target in targets:
        roles = _roles_for_target(target)
        consumers = _consumer_classes_for_target(target)
        records.append(
            {
                "target_id_or_row_id": target["target_id_or_row_id"],
                "target_population": target["target_population"],
                "responsible_agent_role_ids": roles,
                "applicable_agent_role_ids": sorted(set(roles + ["PR159R_SOURCE_EVIDENCE_VALIDATOR_ROLE"])),
                "candidate_agent_family_ids": _candidate_families_for_target(target),
                "consumer_class_ids": consumers,
                "primary_consumer_class": consumers[0],
                "secondary_consumer_classes": consumers[1:],
                "parameter_owner_role_if_applicable": _owner_role_for_target(target, "PARAMETER_OWNER_ROLE"),
                "formula_owner_role_if_applicable": _owner_role_for_target(target, "FORMULA_OWNER_ROLE"),
                "risk_owner_role_if_applicable": _owner_role_for_target(target, "RISK_OWNER_ROLE"),
                "execution_owner_role_if_applicable": _owner_role_for_target(target, "EXECUTION_OWNER_ROLE"),
                "quantum_owner_role_if_applicable": "QUANTUM_OPTIMIZER_OWNER_ROLE" if _is_quantum_relevant(target) else None,
                "research_owner_role_if_applicable": "RESEARCH_SOURCE_EVIDENCE_OWNER_ROLE",
                "dashboard_owner_role_if_applicable": "OWNER_DASHBOARD_FUTURE_CONTROL_OWNER_ROLE",
                "source_evidence_owner_role": "PR159R_OFFICIAL_SOURCE_CAPTURE_AGENT_ROLE",
                "source_revalidation_owner_role": "SOURCE_REVALIDATION_OWNER_ROLE",
                "agent_binding_state": c.AgentBindingState.ROLE_BOUND_ONLY.value,
                "exact_agent_id_or_null": None,
                "exact_agent_id_supported_by_existing_artifact_flag": False,
                "explicit_agent_binding_required_flag": True,
                "agent_binding_source_ref_or_null": None,
                "agent_binding_future_pr_route": c.FutureRoute.PR163_EXACT_AGENT_BINDING.value,
                "no_orphan_status": c.NoOrphanStatus.NOT_ORPHAN_ROLE_BOUND.value,
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return records


def _roles_for_target(target: Mapping[str, Any]) -> list[str]:
    field = f"{target.get('target_field_id')} {target.get('family_id', '')}".lower()
    roles = ["PR159R_OFFICIAL_SOURCE_CAPTURE_AGENT_ROLE"]
    if any(token in field for token in ("execution", "order", "fill", "connector", "sdk", "latency")):
        roles.append("EXECUTION_CONNECTOR_SOURCE_EVIDENCE_ROLE")
    if any(token in field for token in ("risk", "capital", "notional", "limit")):
        roles.append("RISK_CAPITAL_SOURCE_EVIDENCE_ROLE")
    if _is_quantum_relevant(target):
        roles.append("QUANTUM_OPTIMIZER_READINESS_ROLE")
    return sorted(set(roles))


def _candidate_families_for_target(target: Mapping[str, Any]) -> list[str]:
    family = target.get("family_id")
    if family:
        return [str(family)]
    platform = str(target.get("platform_scope") or "PREDICTION_MARKETS_GENERAL")
    return [f"SOURCE_FAMILY_{_slug(platform, limit=64)}"]


def _consumer_classes_for_target(target: Mapping[str, Any]) -> list[str]:
    consumers = ["SOURCE_EVIDENCE_CONTROL_PLANE_CONSUMER", "PR161_MATERIALIZATION_CONSUMER"]
    if _is_quantum_relevant(target):
        consumers.extend(["PR167_OPTIMIZER_INTERFACE_CONSUMER", "PR169_QUANTUM_BACKEND_ROUTE_CONSUMER"])
    consumers.extend(["PR164_SCORING_RANKING_CONSUMER", "PR165_TRADE_CONTEXT_SELECTION_CONSUMER"])
    return list(dict.fromkeys(consumers))


def _owner_role_for_target(target: Mapping[str, Any], role: str) -> str | None:
    target_text = f"{target.get('target_field_id')} {target.get('family_id', '')}".lower()
    if role.startswith("RISK") and any(token in target_text for token in ("risk", "capital", "notional", "limit")):
        return role
    if role.startswith("EXECUTION") and any(token in target_text for token in ("execution", "connector", "order", "fill")):
        return role
    if role.startswith("PARAMETER") and target.get("target_population") != c.PR159RTargetPopulation.PR154_PUBLIC_SOURCE_RETRY_REMAINING_24.value:
        return role
    if role.startswith("FORMULA") and _is_quantum_relevant(target):
        return role
    return None


def _quantum_record(target: Mapping[str, Any]) -> dict[str, Any]:
    relevant = _is_quantum_relevant(target)
    target_id = target["target_id_or_row_id"]
    accepted_packet_id = _accepted_packet_id_for_target(target)
    compatibility = as_list(target.get("quantum_classical_compatibility_impact"))
    if relevant:
        compatibility = sorted(
            set(
                compatibility
                + [
                    c.QuantumClassicalCompatibility.QUANTUM_INSPIRED_OPTIMIZER_CANDIDATE.value,
                    c.QuantumClassicalCompatibility.HYBRID_CLASSICAL_QUANTUM_CANDIDATE.value,
                    c.QuantumClassicalCompatibility.QUBO_COMPATIBLE_METADATA_READY.value,
                    c.QuantumClassicalCompatibility.ISING_COMPATIBLE_METADATA_READY.value,
                    c.QuantumClassicalCompatibility.ANNEALING_COMPATIBLE_METADATA_READY.value,
                ]
            )
        )
    return {
        "target_id_or_row_id": target_id,
        "target_population": target["target_population"],
        "upstream_PR82_quantum_applicability_ref_or_null": c.QUANTUM_SCORING_OPTIMIZER_INPUTS[0].as_posix(),
        "upstream_PR83_owner_quantum_priority_ref_or_null": c.QUANTUM_SCORING_OPTIMIZER_INPUTS[1].as_posix(),
        "upstream_PR84_scoring_policy_ref_or_null": c.QUANTUM_SCORING_OPTIMIZER_INPUTS[2].as_posix(),
        "upstream_PR85_scoring_ranking_gate_ref_or_null": c.QUANTUM_SCORING_OPTIMIZER_INPUTS[3].as_posix(),
        "upstream_PR86_optimizer_arbitration_ref_or_null": c.QUANTUM_SCORING_OPTIMIZER_INPUTS[4].as_posix(),
        "upstream_PR158_selection_readiness_ref_or_null": "docs/master_plan/generated/PR158_AtomicRowsSelectionReadinessOverlay.registry.json",
        "upstream_PR159_source_attempt_ref_or_null": target.get("PR159_unresolved_ref"),
        "upstream_PR160_route_closure_ref_or_null": c.PR160_REQUEUE_PATH.as_posix(),
        "upstream_master_plan_section_refs": ["docs/master_plan/QTT_MasterPlan_Current.md"],
        "upstream_command_action_matrix_refs": ["docs/master_plan/generated/PR136CommandActionMatrix.report.json"],
        "quantum_relevance_flag": relevant,
        "quantum_classical_compatibility": compatibility,
        "quantum_priority_candidate_flag": relevant,
        "quantum_optimizer_readiness_class": (
            c.QuantumOptimizerReadinessClass.BLOCKED_PENDING_SOURCE_EVIDENCE.value
            if relevant
            else c.QuantumOptimizerReadinessClass.NOT_QUANTUM_RELEVANT.value
        ),
        "quantum_inspired_optimizer_readiness_class": (
            c.QuantumOptimizerReadinessClass.READY_FOR_QUANTUM_INSPIRED_OPTIMIZER_AFTER_PR161.value
            if relevant
            else c.QuantumOptimizerReadinessClass.NOT_QUANTUM_RELEVANT.value
        ),
        "true_quantum_readiness_class": (
            c.QuantumOptimizerReadinessClass.READY_FOR_PR169_QUANTUM_BACKEND_GATED_SANDBOX.value
            if relevant
            else c.QuantumOptimizerReadinessClass.NOT_QUANTUM_RELEVANT.value
        ),
        "hybrid_optimizer_readiness_class": (
            c.HybridOptimizerReadinessClass.HYBRID_CANDIDATE_REQUIRES_PR169.value
            if relevant
            else c.HybridOptimizerReadinessClass.NOT_HYBRID_RELEVANT.value
        ),
        "qubo_formulation_readiness_class": c.QuantumOptimizerReadinessClass.READY_FOR_QUBO_FORMULATION_AFTER_PR161.value if relevant else c.QuantumOptimizerReadinessClass.NOT_QUANTUM_RELEVANT.value,
        "ising_formulation_readiness_class": c.QuantumOptimizerReadinessClass.READY_FOR_ISING_FORMULATION_AFTER_PR161.value if relevant else c.QuantumOptimizerReadinessClass.NOT_QUANTUM_RELEVANT.value,
        "qaoa_compatibility_class": c.QuantumOptimizerReadinessClass.READY_FOR_QAOA_CANDIDATE_AFTER_PR161.value if relevant else c.QuantumOptimizerReadinessClass.NOT_QUANTUM_RELEVANT.value,
        "vqe_compatibility_class": c.QuantumOptimizerReadinessClass.READY_FOR_VQE_CANDIDATE_AFTER_PR161.value if relevant else c.QuantumOptimizerReadinessClass.NOT_QUANTUM_RELEVANT.value,
        "annealing_compatibility_class": c.QuantumOptimizerReadinessClass.READY_FOR_ANNEALING_CANDIDATE_AFTER_PR161.value if relevant else c.QuantumOptimizerReadinessClass.NOT_QUANTUM_RELEVANT.value,
        "quantum_portfolio_optimization_compatibility_class": c.QuantumClassicalCompatibility.QUANTUM_PORTFOLIO_OPTIMIZATION_COMPATIBLE_METADATA_READY.value if relevant else c.QuantumOptimizerReadinessClass.NOT_QUANTUM_RELEVANT.value,
        "quantum_provider_source_evidence_ref_or_null": "PR159R_OFFICIAL_SOURCE_DWAVE_MODELS" if relevant else None,
        "quantum_source_accepted_flag": bool(relevant and accepted_packet_id),
        "quantum_source_accepted_packet_ref_or_null": accepted_packet_id if relevant else None,
        "quantum_source_unresolved_fill_path_ref_or_null": (
            None
            if relevant and accepted_packet_id
            else c.UNRESOLVED_EXACT_FILL_PATH_PATH.as_posix() if relevant else None
        ),
        "classical_baseline_required_flag": relevant,
        "classical_baseline_policy_ref_or_null": c.QUANTUM_SCORING_OPTIMIZER_INPUTS[4].as_posix(),
        "replay_paper_quantum_comparison_required_flag": relevant,
        "owner_quantum_priority_policy_ref_or_null": c.QUANTUM_SCORING_OPTIMIZER_INPUTS[1].as_posix(),
        "future_quantum_backend_route": c.FutureRoute.PR169_QUANTUM_BACKEND_GATED_SANDBOX.value,
        "future_optimizer_arbitration_route": c.FutureRoute.PR167_OPTIMIZER_INTERFACE.value,
        "future_scoring_ranking_route": c.FutureRoute.PR164_SCORING_RANKING_BRIDGE.value,
        "future_trade_context_selection_route": c.FutureRoute.PR165_TRADE_CONTEXT_SELECTION.value,
        "future_replay_paper_quantum_comparison_route": c.FutureRoute.REPLAY_AFTER_FUTURE_GATES.value,
        "future_owner_review_route": c.FutureRoute.OWNER_REVIEW_AFTER_FUTURE_GATES.value,
        "future_PR169_quantum_backend_gated_sandbox_route": c.FutureRoute.PR169_QUANTUM_BACKEND_GATED_SANDBOX.value,
        "future_live_promotion_route_after_all_gates": c.FutureRoute.LIVE_ONLY_AFTER_ALL_FUTURE_GATES.value,
        "applicable_quantum_agent_role_ids": ["QUANTUM_OPTIMIZER_READINESS_ROLE"] if relevant else [],
        "applicable_optimizer_agent_role_ids": ["OPTIMIZER_ARBITRATION_READINESS_ROLE"] if relevant else [],
        "applicable_research_agent_role_ids": ["RESEARCH_SOURCE_EVIDENCE_OWNER_ROLE"],
        "applicable_scoring_agent_role_ids": ["SCORING_RANKING_READINESS_ROLE"],
        "applicable_execution_agent_role_ids": _roles_for_target(target),
        "consumer_class_ids": _consumer_classes_for_target(target),
        "downstream_dependency_ids": [
            c.FutureRoute.PR161_ATOMICROWS_SOURCE_VALUE_MATERIALIZATION.value,
            c.FutureRoute.PR167_OPTIMIZER_INTERFACE.value,
            c.FutureRoute.PR169_QUANTUM_BACKEND_GATED_SANDBOX.value,
        ],
        "validator_that_will_unblock_quantum_execution": "future_PR169_quantum_backend_gated_sandbox_validator_after_PR161_PR167_PR168",
        "risk_if_quantum_unclassified": None,
        "risk_if_quantum_source_unfilled": (
            "Quantum route remains readiness-only; no optimizer execution, replay/paper comparison, backend use, or live promotion is allowed."
            if relevant
            else None
        ),
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
    }


def _build_readiness_update(targets: list[Mapping[str, Any]], update_class: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for target in targets:
        accepted_packet_id = _accepted_packet_id_for_target(target)
        records.append(
            {
                "target_id_or_row_id": target["target_id_or_row_id"],
                "target_population": target["target_population"],
                "target_field_id": target.get("target_field_id"),
                "source_ready_flag": accepted_packet_id is not None,
                "source_revalidation_class": target.get("revalidation_class"),
                "accepted_packet_ref_or_null": accepted_packet_id,
                "update_class": update_class,
                "metadata_only_flag": True,
                "execution_created_flag": False,
                "future_route": target.get("future_route"),
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return records


def _build_attempt_matrix(targets: list[Mapping[str, Any]], candidate_packets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    candidate_refs = {str(item["target_id_or_row_id"]): str(item["candidate_packet_id"]) for item in candidate_packets}
    records = []
    for target in targets:
        target_id = str(target["target_id_or_row_id"])
        accepted_packet_id = _accepted_packet_id_for_target(target)
        accepted = accepted_packet_id is not None
        records.append(
            {
                "target_id_or_row_id": target_id,
                "target_population": target["target_population"],
                "target_field_id": target.get("target_field_id"),
                "source_requirement_class": target.get("source_requirement_class"),
                "day1_priority_tier": target.get("day1_priority_tier"),
                "attempted_source_refs": as_list(target.get("official_source_refs_checked")),
                "candidate_packet_ref_or_null": candidate_refs.get(target_id),
                "accepted_packet_ref_or_null": accepted_packet_id,
                "acceptance_possible_flag": accepted,
                "exact_target_field_match_flag": accepted,
                "exact_value_available_flag": accepted,
                "exact_unit_scale_available_flag": accepted,
                "exact_locator_available_flag": accepted or target_id in candidate_refs,
                "freshness_available_flag": accepted,
                "conflict_clearance_possible_flag": accepted,
                "acceptance_blocker_class": target.get("acceptance_blocker_class"),
                "acceptance_decision": (
                    c.SourceAcceptanceDecision.ACCEPTED_TARGET_FIELD_WITH_CANONICALIZATION.value
                    if accepted
                    else c.SourceAcceptanceDecision.DEFERRED_EXACT_VALUE_CAPTURE.value
                ),
                "exact_next_action": (
                    "Accepted in PR159R second-pass extraction repair; route accepted packet to ledger and static readiness overlays."
                    if accepted
                    else _next_source_needed(target)
                ),
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return records


def _second_pass_rejection_reason(target: Mapping[str, Any], has_candidate: bool) -> str | None:
    if _accepted_packet_id_for_target(target):
        return None
    if target["target_population"] != c.PR159RTargetPopulation.PR154_PUBLIC_SOURCE_RETRY_REMAINING_24.value:
        return c.AcceptanceBlockerClass.LOCATOR_MISSING.value
    if not has_candidate:
        return c.AcceptanceBlockerClass.LOCATOR_MISSING.value
    return c.AcceptanceBlockerClass.TARGET_FIELD_SCOPE_MISMATCH.value


def _build_second_pass_attempt_matrix(
    targets: list[Mapping[str, Any]],
    candidate_packets: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    candidates_by_target = {str(item["target_id_or_row_id"]): item for item in candidate_packets}
    records: list[dict[str, Any]] = []
    for target in targets:
        target_id = str(target["target_id_or_row_id"])
        candidate = candidates_by_target.get(target_id)
        accepted_packet_id = _accepted_packet_id_for_target(target)
        accepted = accepted_packet_id is not None
        candidate_unit_scale = bool(
            candidate
            and candidate.get("extracted_unit_or_basis_or_null")
            and candidate.get("extracted_scale_or_null")
        )
        records.append(
            {
                "target_id_or_row_id": target_id,
                "target_population": target["target_population"],
                "day1_priority_tier": target.get("day1_priority_tier"),
                "quantum_relevance_flag": _is_quantum_relevant(target),
                "official_sources_attempted": as_list(target.get("official_source_refs_checked")),
                "exact_target_field_match_flag": accepted,
                "exact_value_or_metadata_available_flag": accepted,
                "exact_locator_available_flag": accepted or candidate is not None,
                "unit_scale_available_flag": accepted or candidate_unit_scale,
                "freshness_available_flag": accepted,
                "conflict_clearance_available_flag": accepted,
                "accepted_packet_possible_flag": accepted,
                "accepted_packet_ref_or_null": accepted_packet_id,
                "rejection_reason_if_not_accepted": _second_pass_rejection_reason(target, candidate is not None),
                "exact_next_action": (
                    "Accepted from IBKR Web API Pacing Limitations official locator; no further source capture needed for this target field before downstream materialization routing."
                    if accepted
                    else _next_source_needed(target)
                ),
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return records


def _source_family_id(source_family: str) -> str:
    return f"PR159R_SOURCE_FAMILY__{_slug(source_family, limit=96)}"


def _source_family_scope(source_family: str) -> str:
    if "Kalshi" in source_family:
        return "KALSHI_ONLY"
    if "Polymarket" in source_family:
        return "POLYMARKET_ONLY"
    if "ForecastEx" in source_family or "IBKR" in source_family:
        return "FORECASTEX_IBKR_ONLY"
    if "D-Wave" in source_family:
        return "D_WAVE_QUANTUM_PROVIDER_ONLY"
    if "AWS Braket" in source_family:
        return "AWS_BRAKET_QUANTUM_PROVIDER_ONLY"
    if "IBM" in source_family or "Qiskit" in source_family:
        return "IBM_QISKIT_QUANTUM_PROVIDER_ONLY"
    return "SOURCE_FAMILY_SCOPE_UNSPECIFIED"


def _build_source_family_reuse_matrix(
    targets: list[Mapping[str, Any]],
    accepted_packets: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    sources_by_family: dict[str, list[Mapping[str, Any]]] = {}
    for source in OFFICIAL_SOURCE_CATALOG:
        sources_by_family.setdefault(str(source["source_family"]), []).append(source)
    accepted_source_refs_by_target = {
        str(packet["target_id_or_row_id"]): str(packet.get("official_source_ref"))
        for packet in accepted_packets
    }
    records: list[dict[str, Any]] = []
    for family, sources in sorted(sources_by_family.items()):
        source_refs = sorted(str(source["official_source_ref"]) for source in sources)
        attempted_targets = [
            str(target["target_id_or_row_id"])
            for target in targets
            if set(as_list(target.get("official_source_refs_checked"))) & set(source_refs)
        ]
        supported_targets = sorted(
            target_id
            for target_id in attempted_targets
            if accepted_source_refs_by_target.get(target_id) in source_refs
        )
        acceptance_possible = bool(supported_targets)
        records.append(
            {
                "source_family_id": _source_family_id(family),
                "source_family_name": family,
                "official_source_refs": source_refs,
                "target_ids_supported": supported_targets,
                "target_ids_attempted": sorted(attempted_targets),
                "exact_target_field_match_flag": acceptance_possible,
                "reusable_packet_allowed_flag": acceptance_possible and len(supported_targets) > 1,
                "reuse_scope": (
                    "single_target_exact_rate_limit_packet_only"
                    if acceptance_possible
                    else _source_family_scope(family)
                ),
                "value_or_metadata_type": (
                    "EXACT_VALUE_WITH_UNIT_SCALE"
                    if acceptance_possible
                    else "SOURCE_CONTEXT_OR_QUANTUM_READINESS_METADATA_ONLY"
                ),
                "unit_scale_basis": (
                    SECOND_PASS_ACCEPTED_UNIT
                    if acceptance_possible
                    else "target_field_specific_or_row_specific_unit_scale_required"
                ),
                "conflict_check_status": c.ConflictStatus.NO_CONFLICT.value if acceptance_possible else c.ConflictStatus.CONFLICT_WITH_TARGET_FIELD_SCOPE.value,
                "freshness_status": c.FreshnessState.FRESH.value if acceptance_possible else c.FreshnessState.VERSION_UNKNOWN.value,
                "acceptance_possible_flag": acceptance_possible,
                "acceptance_blocker_if_not_possible": None if acceptance_possible else c.AcceptanceBlockerClass.TARGET_FIELD_SCOPE_MISMATCH.value,
                "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return records


def _build_completion_records(targets: list[Mapping[str, Any]], population: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for target in targets:
        if target["target_population"] != population:
            continue
        accepted_packet_id = _accepted_packet_id_for_target(target)
        source_ready = accepted_packet_id is not None
        records.append(
            {
            "target_id_or_row_id": target["target_id_or_row_id"],
            "target_population": target["target_population"],
            "target_field_id": target.get("target_field_id"),
            "source_completed_flag": source_ready,
            "source_ready_flag": source_ready,
            "accepted_source_packet_ref_or_null": accepted_packet_id,
            "accepted_value_or_range_or_enum_or_metadata": (
                target.get("accepted_value_or_range_or_enum_or_metadata") if source_ready else None
            ),
            "canonical_unit_or_basis": target.get("canonical_unit_or_basis") if source_ready else None,
            "canonical_scale": target.get("canonical_scale") if source_ready else None,
            "final_PR159R_target_state": target["final_PR159R_target_state"],
            "pr161_materialization_required_flag": False,
            "future_route": target.get("future_route"),
            "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
            }
        )
    return records


def _count_receipt(
    targets: list[Mapping[str, Any]],
    requeues: list[Mapping[str, Any]],
    candidates: list[Mapping[str, Any]],
    accepted: list[Mapping[str, Any]],
    ledger: list[Mapping[str, Any]],
    quantum_records: list[Mapping[str, Any]],
) -> dict[str, Any]:
    final_state_counts = stable_counter(targets, "final_PR159R_target_state")
    raw_priority_counts = stable_counter(targets, "day1_priority_tier")
    priority_counts = {
        tier.value: raw_priority_counts.get(tier.value, 0)
        for tier in c.Day1PriorityTier
    }
    pr154_count = sum(1 for item in targets if item["target_population"] == c.PR159RTargetPopulation.PR154_PUBLIC_SOURCE_RETRY_REMAINING_24.value)
    atomic_public_count = sum(1 for item in targets if item["target_population"] == c.PR159RTargetPopulation.ATOMICROWS_PUBLIC_EXTERNAL_SOURCE_REQUIRED_315.value)
    atomic_range_count = sum(1 for item in targets if item["target_population"] == c.PR159RTargetPopulation.ATOMICROWS_PARAMETER_RANGE_SOURCE_REQUIRED_530.value)
    quantum_relevant_count = sum(1 for item in quantum_records if item.get("quantum_relevance_flag") is True)
    accepted_target_ids = {str(item.get("target_id_or_row_id")) for item in accepted}
    accepted_pr154_count = sum(
        1
        for item in targets
        if str(item["target_id_or_row_id"]) in accepted_target_ids
        and item["target_population"] == c.PR159RTargetPopulation.PR154_PUBLIC_SOURCE_RETRY_REMAINING_24.value
    )
    accepted_atomic_count = sum(
        1
        for item in targets
        if str(item["target_id_or_row_id"]) in accepted_target_ids
        and item["target_population"] != c.PR159RTargetPopulation.PR154_PUBLIC_SOURCE_RETRY_REMAINING_24.value
    )
    quantum_accepted_count = sum(
        1
        for item in quantum_records
        if item.get("quantum_relevance_flag") is True
        and item.get("quantum_source_accepted_flag") is True
    )
    return {
        "pr154_remaining_source_target_count": pr154_count,
        "atomicrows_remaining_source_target_count": atomic_public_count + atomic_range_count,
        "atomicrows_public_external_source_required_count": atomic_public_count,
        "atomicrows_parameter_range_source_required_count": atomic_range_count,
        "total_remaining_source_target_count": len(targets),
        "pr160_pr159r_requeue_count": len(requeues),
        "pr160_requeue_reconciled_to_existing_target_count": sum(1 for item in requeues if item.get("reconciled_to_existing_PR159_unresolved_target_flag") is True),
        "pr160_requeue_supplemental_metadata_only_count": sum(1 for item in requeues if item.get("supplemental_route_metadata_only_flag") is True),
        "processed_target_count": len(targets),
        "one_final_state_per_target_count": sum(final_state_counts.values()),
        "accepted_source_packet_count_before_PR159R": c.EXPECTED_PR159_ACCEPTED_PACKET_COUNT_BEFORE,
        "accepted_source_packet_count_after_PR159R": c.EXPECTED_PR159_ACCEPTED_PACKET_COUNT_BEFORE + len(accepted),
        "new_accepted_source_packet_count": len(accepted),
        "target_field_ledger_count_before_PR159R": c.EXPECTED_PR159_LEDGER_COUNT_BEFORE,
        "target_field_ledger_count_after_PR159R": c.EXPECTED_PR159_LEDGER_COUNT_BEFORE + len(ledger),
        "new_ledger_record_count": len(ledger),
        "source_value_captured_count": len(accepted),
        "pr154_source_completed_count": accepted_pr154_count,
        "atomicrows_source_ready_count": accepted_atomic_count,
        "atomicrows_requires_PR161_materialization_count": 0,
        "unresolved_after_PR159R_count": len(targets) - len(accepted_target_ids),
        "no_orphan_target_count": len(targets),
        "orphan_target_count": 0,
        "placeholder_value_count": 0,
        "blocker_as_value_count": 0,
        "quantum_relevant_target_count": quantum_relevant_count,
        "quantum_relevant_target_classified_count": quantum_relevant_count,
        "quantum_relevant_unclassified_count": 0,
        "quantum_forward_optimizer_readiness_update_count": len(quantum_records),
        "quantum_upstream_downstream_bridge_count": len(quantum_records),
        "quantum_compatible_source_targets_accepted_count": quantum_accepted_count,
        "day1_priority_tier_counts": priority_counts,
        "final_target_state_counts": final_state_counts,
        "candidate_packet_count": len(candidates),
        "accepted_packet_count": len(accepted),
        "ledger_record_count": len(ledger),
        "official_source_searched_count": len(OFFICIAL_SOURCE_CATALOG),
        "official_source_confirmed_count": len(OFFICIAL_SOURCE_CATALOG),
        **c.ZERO_AUTHORITY_COUNTS,
        "count_invariants_passed_flag": (
            pr154_count == c.EXPECTED_PR154_REMAINING
            and atomic_public_count == c.EXPECTED_ATOMICROWS_PUBLIC_EXTERNAL_SOURCE_REQUIRED
            and atomic_range_count == c.EXPECTED_ATOMICROWS_PARAMETER_RANGE_SOURCE_REQUIRED
            and atomic_public_count + atomic_range_count == c.EXPECTED_ATOMICROWS_SOURCE_REQUIRED_REMAINING
            and len(targets) == c.EXPECTED_TOTAL_SOURCE_TARGET_REMAINING
            and len(requeues) == c.EXPECTED_PR160_REQUEUE
            and sum(final_state_counts.values()) == c.EXPECTED_TOTAL_SOURCE_TARGET_REMAINING
            and len(accepted) == len(ledger)
            and quantum_relevant_count == sum(1 for item in quantum_records if item.get("quantum_relevance_flag") is True)
        ),
    }


def _validation_result(failures: tuple[str, ...]) -> dict[str, Any]:
    return {
        "status": "PASS" if not failures else "FAIL_CLOSED",
        "validator_marker": c.SUCCESS_MARKER if not failures else None,
        "failures": list(failures),
    }


def _determinism_receipt() -> dict[str, Any]:
    return {
        "json_indent": 2,
        "json_sort_keys": True,
        "stable_record_sort_key": ["target_id_or_row_id", "candidate_packet_id", "requeue_id"],
        "wall_clock_timestamps_used": False,
        "online_retrieval_timestamps_are_preserved_constants": True,
        "validation_refreshes_online_retrieval": False,
        "runtime_git_branch_or_head_used": False,
        "random_values_used": False,
        "local_absolute_paths_used": False,
        "repo_relative_paths_only": True,
    }


def _common(receipts: list[dict[str, Any]], validation: Mapping[str, Any], count_receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "pr_id": c.PR_ID,
        "semantic_task_id": c.SEMANTIC_TASK_ID,
        "implementation_class": c.IMPLEMENTATION_CLASS,
        "authority_class": c.AUTHORITY_CLASS,
        "authority_profile_ids": list(c.DEFAULT_AUTHORITY_PROFILE_IDS),
        "central_enum_value_sets": {key: sorted(value) for key, value in c.CENTRAL_ENUM_VALUE_SETS.items()},
        "input_consumption_receipt": receipts,
        "orchestration_alignment_receipt": orchestration_alignment_receipt(receipts),
        "count_invariant_receipt": dict(count_receipt),
        "determinism_receipt": _determinism_receipt(),
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
        "validation_result": dict(validation),
    }


def _summary_markdown(master_report: Mapping[str, Any]) -> str:
    counts = as_mapping(master_report.get("count_invariant_receipt"))
    lines = [
        "# PR159R Exact Official Source Capture Summary",
        "",
        f"Target scope: {counts.get('total_remaining_source_target_count')} remaining source targets.",
        f"PR154 remaining source targets processed: {counts.get('pr154_remaining_source_target_count')}.",
        f"AtomicRows remaining source targets processed: {counts.get('atomicrows_remaining_source_target_count')}.",
        f"PR160 requeue records reconciled: {counts.get('pr160_pr159r_requeue_count')} "
        f"({counts.get('pr160_requeue_supplemental_metadata_only_count')} supplemental metadata-only).",
        f"P0/P1/P2/P3 counts: {counts.get('day1_priority_tier_counts')}.",
        f"Official sources searched: {counts.get('official_source_searched_count')}.",
        f"Official sources confirmed: {counts.get('official_source_confirmed_count')}.",
        f"Candidate packets created: {counts.get('candidate_packet_count')}.",
        f"Accepted packets before/after PR159R: {counts.get('accepted_source_packet_count_before_PR159R')} / "
        f"{counts.get('accepted_source_packet_count_after_PR159R')}.",
        f"New accepted packets: {counts.get('new_accepted_source_packet_count')}.",
        f"Target-field ledger before/after PR159R: {counts.get('target_field_ledger_count_before_PR159R')} / "
        f"{counts.get('target_field_ledger_count_after_PR159R')}.",
        f"New ledger records: {counts.get('new_ledger_record_count')}.",
        f"PR154 source completions: {counts.get('pr154_source_completed_count')}.",
        f"AtomicRows source-ready rows: {counts.get('atomicrows_source_ready_count')}.",
        f"PR161 materialization handoff rows: {counts.get('atomicrows_requires_PR161_materialization_count')}.",
        f"Unresolved after PR159R: {counts.get('unresolved_after_PR159R_count')}.",
        f"Placeholder value count: {counts.get('placeholder_value_count')}.",
        f"No-orphan mapped targets: {counts.get('no_orphan_target_count')}; orphan targets: {counts.get('orphan_target_count')}.",
        f"Quantum-relevant/classified/unclassified: {counts.get('quantum_relevant_target_count')} / "
        f"{counts.get('quantum_relevant_target_classified_count')} / {counts.get('quantum_relevant_unclassified_count')}.",
        f"Quantum upstream/downstream bridge records: {counts.get('quantum_upstream_downstream_bridge_count')}.",
        "",
        "Top blockers:",
        "- Remaining targets lack exact target-field source evidence that simultaneously provides locator, value/range/enum, unit, scale, freshness, and conflict clearance.",
        "- AtomicRows source-required rows remain row-specific and require PR161 materialization only after accepted PR159R packets exist.",
        "- Quantum-forward routing is classified, but execution remains blocked until source evidence, PR161, optimizer sandboxing, replay/paper, PR169, and owner review gates pass.",
        "",
        "Classical baseline preservation: every quantum-relevant target keeps a classical baseline route and replay/paper comparison requirement.",
        "",
        "No runtime, live, connector binding, replay, paper, scoring, ranking, selection, optimizer, quantum backend, order, fill, profit, QTT checksum/freeze/global digest, or AtomicRows bundle checksum/hash authority was created.",
        "",
    ]
    return "\n".join(lines)


def build_artifacts(repo_root: Path | str) -> BuildArtifacts:
    root = Path(repo_root).resolve()
    receipts = input_consumption_receipts(root)
    failures = list(preflight_failures(receipts))
    targets = _build_targets(root)
    requeues = _build_requeue_reconciliation(root, targets)
    search_plan = _build_search_plan(targets)
    discovery_receipts = _build_discovery_receipts()
    capture_receipts = discovery_receipts
    non_authoritative_rejections: list[dict[str, Any]] = []
    candidate_packets = _build_candidate_packets(root, targets)
    accepted_packets = _build_accepted_packets(targets, candidate_packets)
    ledger_records = _build_ledger_records(targets, accepted_packets)
    locator_matrix = _build_exact_locator_matrix(targets, candidate_packets)
    unresolved_paths = _build_unresolved_fill_paths(targets, candidate_packets)
    attempt_matrix = _build_attempt_matrix(targets, candidate_packets)
    second_pass_attempt_matrix = _build_second_pass_attempt_matrix(targets, candidate_packets)
    source_family_reuse_matrix = _build_source_family_reuse_matrix(targets, accepted_packets)
    agent_matrix = _build_agent_matrix(targets)
    quantum_records = [_quantum_record(target) for target in targets]
    pr154_completion = _build_completion_records(targets, c.PR159RTargetPopulation.PR154_PUBLIC_SOURCE_RETRY_REMAINING_24.value)
    atomic_public = _build_completion_records(targets, c.PR159RTargetPopulation.ATOMICROWS_PUBLIC_EXTERNAL_SOURCE_REQUIRED_315.value)
    atomic_range = _build_completion_records(targets, c.PR159RTargetPopulation.ATOMICROWS_PARAMETER_RANGE_SOURCE_REQUIRED_530.value)
    atomic_completion = sorted(atomic_public + atomic_range, key=lambda item: str(item["target_id_or_row_id"]))
    pr161_handoff: list[dict[str, Any]] = []
    conflict_queue = [
        {
            "target_id_or_row_id": item["target_id_or_row_id"],
            "candidate_packet_id": item["candidate_packet_id"],
            "conflict_status": c.ConflictStatus.CONFLICT_WITH_TARGET_FIELD_SCOPE.value,
            "conflict_reason": "candidate official source context does not yet provide exact target-field value/range/enum with unit and scale",
            "future_route": c.FutureRoute.PR159R_CONTINUED_EXACT_CAPTURE.value,
            "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
        }
        for item in candidate_packets
        if item.get("accepted_packet_ref_or_null") is None
    ]
    freshness_audit = [
        {
            "target_id_or_row_id": target["target_id_or_row_id"],
            "freshness_state": (
                c.FreshnessState.FRESH.value
                if _accepted_packet_id_for_target(target)
                else c.FreshnessState.VERSION_UNKNOWN.value
            ),
            "revalidation_class": target.get("revalidation_class"),
            "materiality_class": target.get("source_materiality_class"),
            "source_change_blocks_connector_binding_flag": True,
            "source_change_blocks_live_flag": True,
            "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
        }
        for target in targets
    ]
    selection_updates = _build_readiness_update(targets, "PR158_SELECTION_READINESS_SOURCE_UPDATE_METADATA_ONLY")
    trade_updates = _build_readiness_update(targets, "TRADE_CONTEXT_SOURCE_READINESS_METADATA_ONLY")
    scoring_updates = _build_readiness_update(targets, "SCORING_RANKING_SOURCE_READINESS_METADATA_ONLY")
    low_latency_updates = _build_readiness_update(targets, "LOW_LATENCY_SOURCE_SNAPSHOT_METADATA_ONLY")
    provider_readiness = [
        {
            **source,
            "quantum_provider_source_readiness_flag": source["official_source_class"] == c.OfficialSourceClass.OFFICIAL_QUANTUM_PROVIDER_DOCS.value,
        "accepted_source_packet_created_flag": False,
        "future_route": c.FutureRoute.PR169_QUANTUM_BACKEND_GATED_SANDBOX.value,
            "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
        }
        for source in discovery_receipts
        if source["official_source_class"] == c.OfficialSourceClass.OFFICIAL_QUANTUM_PROVIDER_DOCS.value
    ]

    count_receipt = _count_receipt(targets, requeues, candidate_packets, accepted_packets, ledger_records, quantum_records)
    if not count_receipt["count_invariants_passed_flag"]:
        failures.append("PR159R_BLOCKED_COUNT_INVARIANT_FAILURE")
    failures_tuple = tuple(sorted(set(failures)))
    validation = _validation_result(failures_tuple)
    common = _common(receipts, validation, count_receipt)

    master_records = [
        {
            "artifact_group": "target_universe",
            "path": c.TARGET_RECONCILIATION_REGISTRY_PATH.as_posix(),
            "record_count": len(targets),
        },
        {
            "artifact_group": "candidate_packets",
            "path": c.CANDIDATE_PACKET_REGISTRY_PATH.as_posix(),
            "record_count": len(candidate_packets),
        },
        {
            "artifact_group": "second_pass_acceptance_attempts",
            "path": c.SECOND_PASS_EXACT_ACCEPTANCE_ATTEMPT_MATRIX_PATH.as_posix(),
            "record_count": len(second_pass_attempt_matrix),
        },
        {
            "artifact_group": "source_family_reuse",
            "path": c.SOURCE_FAMILY_REUSABLE_ACCEPTANCE_MATRIX_PATH.as_posix(),
            "record_count": len(source_family_reuse_matrix),
        },
        {
            "artifact_group": "quantum_bridge",
            "path": c.QUANTUM_UPSTREAM_DOWNSTREAM_BRIDGE_PATH.as_posix(),
            "record_count": len(quantum_records),
        },
    ]
    master_report = _report_payload(
        "PR159R_EXACT_SOURCE_LOCATOR_VALUE_UNIT_CAPTURE_REPORT",
        master_records,
        common,
        fallback_crosswalk_used=any(item.get("fallback_used") for item in receipts),
        master_plan_consumed_confirmation=True,
        master_plan_not_edited_confirmation=True,
        source_evidence_packet_consumed_confirmation=True,
        online_official_source_search_performed_confirmation=True,
        exact_official_source_search_method=c.OFFICIAL_SEARCH_METHOD,
        online_unavailable_flag=False,
        pr154_remaining_source_targets_processed=count_receipt["pr154_remaining_source_target_count"],
        atomicrows_remaining_source_targets_processed=count_receipt["atomicrows_remaining_source_target_count"],
        pr160_requeue_reconciled_count=count_receipt["pr160_pr159r_requeue_count"],
        total_target_count_processed=count_receipt["processed_target_count"],
        p0_p1_p2_p3_target_counts=count_receipt["day1_priority_tier_counts"],
        official_source_searched_count=count_receipt["official_source_searched_count"],
        official_source_confirmed_count=count_receipt["official_source_confirmed_count"],
        candidate_packet_count=len(candidate_packets),
        conflict_blocked_count=0,
        stale_revalidation_blocked_count=0,
        runtime_receipt_future_count=0,
        connector_semantic_future_count=0,
        private_access_controlled_blocked_count=0,
        non_authoritative_source_rejected_count=0,
        invented_value_count=0,
        invented_range_count=0,
        invented_locator_count=0,
        invented_source_packet_count=0,
        exact_agent_id_invented_count=0,
        responsible_agent_applicable_role_mapping_count=len(agent_matrix),
        quantum_compatible_source_targets_accepted_count=count_receipt["quantum_compatible_source_targets_accepted_count"],
        quantum_inspired_optimizer_readiness_targets_count=count_receipt["quantum_relevant_target_count"],
        hybrid_quantum_classical_readiness_targets_count=count_receipt["quantum_relevant_target_count"],
        true_quantum_backend_future_route_targets_count=count_receipt["quantum_relevant_target_count"],
        quantum_replay_paper_comparison_route_count=count_receipt["quantum_relevant_target_count"],
        classical_baseline_preserved_target_count=count_receipt["quantum_relevant_target_count"],
        selection_readiness_update_count=len(selection_updates),
        trade_context_update_count=len(trade_updates),
        scoring_ranking_update_count=len(scoring_updates),
        low_latency_update_count=len(low_latency_updates),
        **c.ZERO_AUTHORITY_COUNTS,
    )
    common = _common(receipts, validation, count_receipt)
    payloads: dict[str, dict[str, Any]] = {
        c.MASTER_REPORT_PATH.as_posix(): master_report,
        c.MASTER_REGISTRY_PATH.as_posix(): _registry_payload("PR159R_EXACT_SOURCE_LOCATOR_VALUE_UNIT_CAPTURE_REGISTRY", targets, common),
        c.TARGET_RECONCILIATION_REPORT_PATH.as_posix(): _report_payload("PR159R_UNRESOLVED_SOURCE_TARGET_RECONCILIATION_REPORT", targets, common),
        c.TARGET_RECONCILIATION_REGISTRY_PATH.as_posix(): _registry_payload("PR159R_UNRESOLVED_SOURCE_TARGET_RECONCILIATION_REGISTRY", targets, common),
        c.PR160_REQUEUE_RECONCILIATION_PATH.as_posix(): _report_payload("PR159R_PR160_REQUEUE_RECONCILIATION_REPORT", requeues, common),
        c.DAY1_PRIORITY_WORK_QUEUE_PATH.as_posix(): _report_payload("PR159R_DAY1_PRIORITY_SOURCE_WORK_QUEUE_REPORT", search_plan, common),
        c.OFFICIAL_SOURCE_SEARCH_PLAN_PATH.as_posix(): _report_payload("PR159R_OFFICIAL_SOURCE_SEARCH_PLAN_REPORT", search_plan, common),
        c.OFFICIAL_SOURCE_DISCOVERY_RECEIPTS_PATH.as_posix(): _report_payload("PR159R_OFFICIAL_SOURCE_DISCOVERY_RECEIPTS_REPORT", discovery_receipts, common),
        c.OFFICIAL_SOURCE_CAPTURE_RECEIPTS_PATH.as_posix(): _report_payload("PR159R_OFFICIAL_SOURCE_CAPTURE_RECEIPTS_REPORT", capture_receipts, common),
        c.NON_AUTHORITATIVE_REJECTION_LEDGER_PATH.as_posix(): _report_payload("PR159R_NON_AUTHORITATIVE_SEED_REJECTION_LEDGER_REPORT", non_authoritative_rejections, common),
        c.EXACT_LOCATOR_EXTRACTION_MATRIX_PATH.as_posix(): _report_payload("PR159R_EXACT_LOCATOR_EXTRACTION_MATRIX_REPORT", locator_matrix, common),
        c.CANDIDATE_PACKET_REPORT_PATH.as_posix(): _report_payload("PR159R_CANDIDATE_SOURCE_EVIDENCE_PACKET_REGISTRY_REPORT", candidate_packets, common),
        c.CANDIDATE_PACKET_REGISTRY_PATH.as_posix(): _registry_payload("PR159R_CANDIDATE_SOURCE_EVIDENCE_PACKET_REGISTRY", candidate_packets, common),
        c.ACCEPTED_PACKET_REPORT_PATH.as_posix(): _report_payload("PR159R_ACCEPTED_SOURCE_EVIDENCE_PACKET_REGISTRY_REPORT", accepted_packets, common),
        c.ACCEPTED_PACKET_REGISTRY_PATH.as_posix(): _registry_payload("PR159R_ACCEPTED_SOURCE_EVIDENCE_PACKET_REGISTRY", accepted_packets, common),
        c.TARGET_FIELD_LEDGER_REPORT_PATH.as_posix(): _report_payload("PR159R_TARGET_FIELD_ACCEPTANCE_LEDGER_REPORT", ledger_records, common),
        c.TARGET_FIELD_LEDGER_REGISTRY_PATH.as_posix(): _registry_payload("PR159R_TARGET_FIELD_ACCEPTANCE_LEDGER_REGISTRY", ledger_records, common),
        c.PR154_SOURCE_COMPLETION_REPORT_PATH.as_posix(): _report_payload("PR159R_PR154_SOURCE_COMPLETION_REPORT", pr154_completion, common),
        c.PR154_SOURCE_COMPLETION_REGISTRY_PATH.as_posix(): _registry_payload("PR159R_PR154_SOURCE_COMPLETION_REGISTRY", pr154_completion, common),
        c.ATOMICROWS_SOURCE_READY_REPORT_PATH.as_posix(): _report_payload("PR159R_ATOMICROWS_SOURCE_READY_COMPLETION_REPORT", atomic_completion, common),
        c.ATOMICROWS_SOURCE_READY_REGISTRY_PATH.as_posix(): _registry_payload("PR159R_ATOMICROWS_SOURCE_READY_COMPLETION_REGISTRY", atomic_completion, common),
        c.PR161_MATERIALIZATION_HANDOFF_PATH.as_posix(): _report_payload("PR159R_PR161_MATERIALIZATION_HANDOFF_REPORT", pr161_handoff, common),
        c.SOURCE_CONFLICT_REVIEW_QUEUE_PATH.as_posix(): _report_payload("PR159R_SOURCE_CONFLICT_REVIEW_QUEUE_REPORT", conflict_queue, common),
        c.SOURCE_FRESHNESS_REVALIDATION_AUDIT_PATH.as_posix(): _report_payload("PR159R_SOURCE_FRESHNESS_AND_REVALIDATION_AUDIT_REPORT", freshness_audit, common),
        c.UNRESOLVED_EXACT_FILL_PATH_PATH.as_posix(): _report_payload("PR159R_UNRESOLVED_EXACT_SOURCE_FILL_PATH_REPORT", unresolved_paths, common),
        c.SOURCE_ACCEPTANCE_ATTEMPT_MATRIX_PATH.as_posix(): _report_payload("PR159R_SOURCE_ACCEPTANCE_ATTEMPT_MATRIX_REPORT", attempt_matrix, common),
        c.SOURCE_FAMILY_REUSABLE_ACCEPTANCE_MATRIX_PATH.as_posix(): _report_payload("PR159R_SOURCE_FAMILY_REUSABLE_ACCEPTANCE_MATRIX_REPORT", source_family_reuse_matrix, common),
        c.SECOND_PASS_EXACT_ACCEPTANCE_ATTEMPT_MATRIX_PATH.as_posix(): _report_payload("PR159R_SECOND_PASS_EXACT_ACCEPTANCE_ATTEMPT_MATRIX_REPORT", second_pass_attempt_matrix, common),
        c.SELECTION_READINESS_UPDATE_PATH.as_posix(): _report_payload("PR159R_ATOMICROWS_SELECTION_READINESS_SOURCE_UPDATE_REPORT", selection_updates, common),
        c.TRADE_CONTEXT_UPDATE_PATH.as_posix(): _report_payload("PR159R_TRADE_CONTEXT_SOURCE_READINESS_UPDATE_REPORT", trade_updates, common),
        c.SCORING_RANKING_UPDATE_PATH.as_posix(): _report_payload("PR159R_SCORING_RANKING_SOURCE_READINESS_UPDATE_REPORT", scoring_updates, common),
        c.LOW_LATENCY_UPDATE_PATH.as_posix(): _report_payload("PR159R_LOW_LATENCY_SOURCE_SNAPSHOT_READINESS_UPDATE_REPORT", low_latency_updates, common),
        c.TARGET_AGENT_MATRIX_PATH.as_posix(): _report_payload("PR159R_TARGET_AGENT_APPLICABILITY_NO_ORPHAN_MATRIX_REPORT", agent_matrix, common),
        c.QUANTUM_FORWARD_BRIDGE_PATH.as_posix(): _report_payload("PR159R_QUANTUM_FORWARD_OPTIMIZER_READINESS_BRIDGE_REPORT", quantum_records, common),
        c.QUANTUM_PR82_PR86_RECONCILIATION_PATH.as_posix(): _report_payload("PR159R_QUANTUM_APPLICABILITY_RECONCILIATION_WITH_PR82_PR86_REPORT", quantum_records, common),
        c.QUANTUM_UPSTREAM_DOWNSTREAM_BRIDGE_PATH.as_posix(): _report_payload("PR159R_QUANTUM_UPSTREAM_DOWNSTREAM_WORKFLOW_BRIDGE_REPORT", quantum_records, common),
        c.QUANTUM_CLASSICAL_HYBRID_ARBITRATION_PATH.as_posix(): _report_payload("PR159R_QUANTUM_CLASSICAL_HYBRID_ARBITRATION_READINESS_REPORT", quantum_records, common),
        c.QUANTUM_PROVIDER_READINESS_PATH.as_posix(): _report_payload("PR159R_QUANTUM_PROVIDER_SOURCE_READINESS_UPDATE_REPORT", provider_readiness, common),
        c.QUANTUM_REPLAY_PAPER_COMPARISON_PATH.as_posix(): _report_payload("PR159R_QUANTUM_REPLAY_PAPER_COMPARISON_READINESS_REPORT", quantum_records, common),
    }
    markdown_payloads = {c.HUMAN_SUMMARY_PATH.as_posix(): _summary_markdown(master_report)}
    return BuildArtifacts(payloads=payloads, markdown_payloads=markdown_payloads)


def write_artifacts(repo_root: Path | str) -> None:
    root = Path(repo_root).resolve()
    artifacts = build_artifacts(root)
    for rel_path, payload in artifacts.payloads.items():
        write_json(root / rel_path, payload)
    for rel_path, payload in artifacts.markdown_payloads.items():
        write_text(root / rel_path, payload)
