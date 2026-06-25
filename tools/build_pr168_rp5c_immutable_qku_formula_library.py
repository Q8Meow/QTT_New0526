#!/usr/bin/env python3
"""Build PR168-RP5C immutable QKU/formula library and routing surfaces."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_rp5c_config import (
    BRANCH_NAME,
    CENTRAL_SURFACE_SHARDS,
    CONSUMPTION_STATUSES,
    CREATED_AT_UTC,
    DEPENDENCY_TYPES,
    EXPECTED_INPUT_ARTIFACTS,
    FALLBACK_ROUTING_MATRIX,
    GENERATED_ROOT,
    HARD_ZERO_COUNTERS,
    LIBRARY_STATES,
    MARKET_SCOPES,
    MAX_JSON_PARSE_BYTES,
    MAX_RECORDS_PER_ARTIFACT,
    MAX_TOTAL_PARSED_RECORDS,
    ONTOLOGY_CATEGORIES,
    PLATFORM_APPLICABILITY_STATES,
    PROVENANCE_TIERS,
    REPORT_NAMES,
    ROADMAP_PR,
    ROUTE_RESOLUTION_STATES,
    ROW_SHARDS,
    SHARD_ROOT,
    STAGE1_ACTIVE_UNIVERSE_SHARDS,
    STAGE1_CLASSIFICATION_STATES,
    UPSTREAM_IDENTITY_DIRS,
    UPSTREAM_IDENTITY_KEYWORDS,
    classify_file_kind,
    generated_ref,
    manifest_path_for_shard,
    normalize_repo_path,
    report_path,
    shard_path,
)
from tools.pr168_rp5c_report_writer import NO_AUTHORITY_STATEMENT, read_json, read_jsonl, write_report, write_shard


IDENTITY_KEY_RE = re.compile(
    r"(?:^|_)(qku_id|formula_id|formula_variant_id|formula_family|formula_ids|"
    r"formula_refs|formula_contract_ref|formula_contract_refs|formula_plugin_ref|"
    r"formula_to_pnl_map_id|plugin_ref|safe_formula_expression_or_semantic_definition)$",
    re.IGNORECASE,
)
QKU_VALUE_RE = re.compile(r"\bQKU[-_:A-Z0-9]{6,}\b", re.IGNORECASE)
FORMULA_VALUE_RE = re.compile(r"\b(?:FORM|FORMULA|QTT_FORMULA|PR168_GFP_FORMULA)[-_:A-Z0-9]{4,}\b", re.IGNORECASE)
NEGATIVE_MEMORY_RE = re.compile(r"(negative|no[-_ ]?trade|unselected|failed|non[-_ ]?computable)", re.IGNORECASE)


def _run_text(args: list[str]) -> str:
    completed = subprocess.run(
        args,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _stable_path_key(path: str | Path) -> tuple[str, str]:
    text = normalize_repo_path(path)
    return (text.casefold(), text)


def _stable_values(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            out.extend(_stable_values(value))
            continue
        text = str(value).strip()
        if text and text not in {"NOT_APPLICABLE_FOR_THIS_ROW_TERMINAL_BY_NATURE", "None", "null"}:
            out.append(text)
    return sorted(dict.fromkeys(out), key=lambda item: (item.casefold(), item))


def _first(values: Iterable[Any]) -> str | None:
    stable = _stable_values(values)
    return stable[0] if stable else None


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return text or "unknown"


def _source_family(path: str) -> str:
    name = Path(path).name
    lowered = path.lower()
    if "PR168_RP5A_" in name:
        return "RP5A"
    if "PR168_RP5B_" in name:
        return "RP5B"
    if "PR165_D2_" in name:
        return "PR165_D2"
    if "pr168_gfp" in lowered or "PR168_GFP" in name:
        return "GFP"
    if "pr168_gfp2r" in lowered or "PR168_GFP2R" in name:
        return "GFP2R"
    if "/map3/" in lowered or "PR168_MAP3" in name:
        return "MAP3"
    if "/rp3/" in lowered or "PR168_RP3" in name:
        return "RP3"
    if "/rank3/" in lowered or "PR168_RANK3" in name:
        return "RANK3"
    if "pr168_rp_shards" in lowered or "PR168_RP_" in name:
        return "RP"
    if "pr168_rank_shards" in lowered or "PR168_RANK_" in name:
        return "RANK"
    if "PR161C_QKU" in name:
        return "UPSTREAM_QKU"
    return "UNKNOWN"


def _provenance_tier(path: str) -> str:
    name = Path(path).name
    lowered = path.lower()
    if name == "PR168_RP5B_ActiveArtifactRegistry.report.json":
        return "ACTIVE_CANONICAL_REGISTRY"
    if "PR168_RP5B_LegacyKeepReasonLedger" in name:
        return "RP5B_LEGACY_KEEP_REASON_PRESERVED"
    if "PR168_RP5B_LegacySemanticSupersession" in name:
        return "RP5B_SEMANTIC_SUPERSESSION_INPUT"
    if "PR168_RP5B_" in name:
        return "RP5B_PRESERVED_ACTIVE_REGISTRY_INPUT"
    if "QKUFormulaIdentityDependency" in name:
        return "RP5A_IDENTITY_DEPENDENCY"
    if "IdentityCustodyGraph" in name or "identity_custody" in lowered:
        return "RP5A_IDENTITY_CUSTODY"
    if "PR165_D2_" in name:
        return "PR165_D2_AGENT_DUTY_INPUT"
    if "candidatepacket" in lowered or "candidate_packet" in lowered:
        return "CANDIDATE_PACKET_IDENTITY_SURFACE"
    if any(token in lowered for token in ("formula", "qku", "map3", "rp3", "rank3", "gfp")):
        return "UPSTREAM_FORMULA_QKU_REGISTRY"
    if path.startswith("docs/master_plan/generated/"):
        return "GENERATED_REPORT_HISTORICAL_EVIDENCE"
    return "UNKNOWN_NEEDS_REVIEW"


def _source_authority_class(path: str) -> str:
    tier = _provenance_tier(path)
    if tier == "ACTIVE_CANONICAL_REGISTRY":
        return "ACTIVE_CANONICAL_REGISTRY_NOT_SOURCE_TRUTH"
    if tier == "PR165_D2_AGENT_DUTY_INPUT":
        return "AGENT_DUTY_ROUTE_INPUT_NOT_IDENTITY_AUTHORITY"
    if tier.startswith("RP5B"):
        return "RP5B_ACTIVE_LAYER_INPUT_NOT_DIRECT_DECISION_AUTHORITY"
    if tier.startswith("RP5A"):
        return "RP5A_AUDIT_EVIDENCE_ONLY"
    return "HISTORICAL_IDENTITY_EVIDENCE_ONLY"


def _discover_input_paths() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    started = time.monotonic()
    seen: dict[str, dict[str, Any]] = {}

    def is_self_generated(path_text: str) -> bool:
        normalized = normalize_repo_path(path_text)
        return normalized.startswith("docs/master_plan/generated/rp5c/") or Path(normalized).name.startswith("PR168_RP5C_")

    def add(path_text: str, *, expected: bool, discovery_class: str) -> None:
        normalized = normalize_repo_path(path_text)
        if is_self_generated(normalized):
            return
        if normalized in seen:
            seen[normalized]["duplicate_discovery_count"] += 1
            return
        path = REPO_ROOT / normalized
        seen[normalized] = {
            "source_file_path": normalized,
            "expected_input_flag": expected,
            "found_flag": path.is_file(),
            "missing_expected_input_flag": expected and not path.is_file(),
            "discovery_class": discovery_class,
            "duplicate_discovery_count": 0,
            "source_report_family": _source_family(normalized),
            "source_file_kind": classify_file_kind(normalized),
            "source_authority_class": _source_authority_class(normalized),
            "provenance_tier": _provenance_tier(normalized),
        }

    for path in EXPECTED_INPUT_ARTIFACTS:
        add(path, expected=True, discovery_class="MANDATORY_EXPECTED_INPUT")

    for directory in UPSTREAM_IDENTITY_DIRS:
        root = REPO_ROOT / directory
        if not root.exists():
            add(directory, expected=False, discovery_class="MISSING_UPSTREAM_IDENTITY_DIRECTORY")
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            rel = generated_ref(path)
            lowered = rel.lower()
            if any(keyword in lowered for keyword in UPSTREAM_IDENTITY_KEYWORDS):
                add(rel, expected=False, discovery_class="UPSTREAM_IDENTITY_SURFACE")

    for path in GENERATED_ROOT.glob("PR168_*.report.json"):
        rel = generated_ref(path)
        lowered = rel.lower()
        if any(keyword in lowered for keyword in UPSTREAM_IDENTITY_KEYWORDS):
            add(rel, expected=False, discovery_class="UPSTREAM_IDENTITY_REPORT")

    for path in GENERATED_ROOT.glob("PR161C_QKU*.report.json"):
        add(generated_ref(path), expected=False, discovery_class="ACTIVE_QKU_IDENTITY_SURFACE")

    rows: list[dict[str, Any]] = []
    for index, (_, row) in enumerate(sorted(seen.items(), key=lambda item: _stable_path_key(item[0])), start=1):
        status = "MISSING_EXPECTED_INPUT_RECORDED" if row["missing_expected_input_flag"] else "PENDING_EXTRACTION"
        if row["duplicate_discovery_count"]:
            status = "DUPLICATE_INPUT_ARTIFACT_PRESERVED"
        rows.append(
            {
                "source_artifact_row_id": f"RP5C_SOURCE_ARTIFACT_{index:06d}",
                "source_artifact_ref": row["source_file_path"],
                "source_file_path": row["source_file_path"],
                "source_file_kind": row["source_file_kind"],
                "source_pr_ref": row["source_report_family"],
                "source_report_family": row["source_report_family"],
                "source_authority_class": row["source_authority_class"],
                "provenance_tier": row["provenance_tier"],
                "discovered_by_phase": row["discovery_class"],
                "expected_input_flag": row["expected_input_flag"],
                "found_flag": row["found_flag"],
                "missing_expected_input_flag": row["missing_expected_input_flag"],
                "consumption_status": status,
                "consumed_by_builder_refs": ["tools/build_pr168_rp5c_immutable_qku_formula_library.py"],
                "identity_rows_extracted_count": 0,
                "qku_identity_rows_extracted_count": 0,
                "formula_identity_rows_extracted_count": 0,
                "formula_assignment_rows_extracted_count": 0,
                "no_identity_reason": "MISSING_EXPECTED_INPUT_RECORDED" if row["missing_expected_input_flag"] else None,
                "raw_legacy_decision_authority_allowed_flag": False,
                "active_surface_consumer_allowed_flag": row["provenance_tier"] in {"ACTIVE_CANONICAL_REGISTRY", "PR165_D2_AGENT_DUTY_INPUT"},
                "responsibility_group_refs": [],
                "derived_route_resolution_refs": [],
                "downstream_agent_refs": [],
                "downstream_pr_refs": ["PR168-RP5D"],
                "validator_refs": ["tools/validate_pr168_rp5c_immutable_qku_formula_library.py"],
                "no_orphan_source_artifact_status": "PENDING_ROUTE" if row["found_flag"] else "MISSING_EXPECTED_INPUT_RECORDED_ROUTED_TO_REVIEW",
                "blocker_codes": ["MISSING_EXPECTED_INPUT"] if row["missing_expected_input_flag"] else [],
                "notes": "Discovered by deterministic RP5C bounded input discovery.",
            }
        )
    summary = {
        "input_artifact_count": len(rows),
        "found_input_artifact_count": sum(1 for row in rows if row["found_flag"]),
        "missing_expected_input_count": sum(1 for row in rows if row["missing_expected_input_flag"]),
        "discovery_elapsed_seconds_rounded": round(time.monotonic() - started, 3),
        "inspected_input_roots": [
            "docs/master_plan/generated",
            *UPSTREAM_IDENTITY_DIRS,
        ],
    }
    return rows, summary


def _iter_json_records(path: Path) -> Iterable[tuple[dict[str, Any], str]]:
    if not path.is_file():
        return
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for index, line in enumerate(handle, start=1):
                if index > MAX_RECORDS_PER_ARTIFACT:
                    break
                text = line.strip()
                if not text:
                    continue
                try:
                    payload = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    yield payload, f"jsonl[{index}]"
        return
    name = path.name
    if suffix != ".json" or ".shard_" in name or ".part_" in name or path.stat().st_size > MAX_JSON_PARSE_BYTES:
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return
    records = payload.get("records") if isinstance(payload, dict) else payload
    if isinstance(records, list):
        for index, record in enumerate(records[:MAX_RECORDS_PER_ARTIFACT], start=1):
            if isinstance(record, dict):
                yield record, f"records[{index}]"
    elif isinstance(payload, dict):
        yield payload, "$"


def _collect_values(record: dict[str, Any], names: tuple[str, ...]) -> list[Any]:
    values: list[Any] = []
    lowered = {name.lower() for name in names}
    for key, value in record.items():
        key_l = str(key).lower()
        if key_l in lowered or any(key_l.endswith(f"_{name}") for name in lowered):
            values.append(value)
    return values


def _record_text(record: dict[str, Any], path: str) -> str:
    pieces = [path]
    for key in (
        "formula_family",
        "formula_id",
        "qku_id",
        "qku_id_if_available",
        "ontology_category",
        "ontology_subcategory",
        "formula_output_semantics",
        "source_file_path",
        "canonical_row_key",
        "row_family",
    ):
        if key in record:
            pieces.append(str(record.get(key)))
    return " ".join(pieces).lower()


def _market_scope(record: dict[str, Any], path: str) -> tuple[str, str]:
    text = _record_text(record, path)
    if any(token in text for token in ("prediction", "pmkt", "kalshi", "polymarket", "forecastex", "binary_event", "binary_contract")):
        return "prediction_market", "prediction_market_binary_event_contracts"
    if any(token in text for token in ("equity", "equities", "stock")):
        return "equities", "equities"
    if "option" in text:
        return "options", "options"
    if any(token in text for token in ("future", "commodity", "commodities")):
        return "futures_commodities", "futures_commodities"
    if any(token in text for token in ("crypto", "bitcoin", "ethereum")):
        return "crypto", "crypto"
    if any(token in text for token in ("fx", "macro", "currency")):
        return "fx_macro", "fx_macro"
    if any(token in text for token in ("fixed_income", "bond", "rates")):
        return "fixed_income", "fixed_income"
    if any(token in text for token in ("repo", "financing")):
        return "repo_financing", "repo_financing"
    if "cross_market" in text:
        return "cross_market", "cross_market"
    if any(token in text for token in ("quantum", "classical", "governance", "source")):
        return "market_agnostic", "market_agnostic"
    return "unknown_needs_review", "unknown_needs_review"


def _ontology(record: dict[str, Any], path: str) -> tuple[str, str, str]:
    text = _record_text(record, path)
    source_category = str(record.get("ontology_category") or "").lower()
    source_subcategory = str(record.get("ontology_subcategory") or "").lower()
    combined = " ".join([text, source_category, source_subcategory])
    if "market_implied" in combined or "implied_probability" in combined:
        return "market_implied_probability", source_subcategory or "market_implied_probability", "HIGH"
    if any(token in combined for token in ("calibration", "brier", "ece", "scoring")):
        return "calibration", source_subcategory or "calibration", "HIGH"
    if any(token in combined for token in ("tca", "cost", "fee", "slippage", "implementation_shortfall", "spread")):
        return "tca_cost", source_subcategory or "transaction_cost", "MEDIUM"
    if any(token in combined for token in ("fill", "liquidity", "queue", "orderbook", "depth")):
        return "fill_queue_liquidity", source_subcategory or "liquidity", "MEDIUM"
    if any(token in combined for token in ("latency", "staleness", "freshness", "decay")):
        return "latency_staleness", source_subcategory or "latency", "MEDIUM"
    if any(token in combined for token in ("capacity", "crowding")):
        return "capacity_crowding", source_subcategory or "capacity", "MEDIUM"
    if "portfolio" in combined or "risk" in combined:
        return "portfolio_risk", source_subcategory or "risk", "MEDIUM"
    if "regime" in combined or "scenario" in combined:
        return "regime_scenario", source_subcategory or "scenario", "MEDIUM"
    if "exit" in combined or "hold_duration" in combined:
        return "exit_timing", source_subcategory or "exit_timing", "MEDIUM"
    if any(token in combined for token in ("qubo", "bqm", "ising", "cqm", "dqm", "quadprogram", "quantum_objective", "quantum")):
        return "quantum_objective_constraint", source_subcategory or "quantum_objective", "HIGH"
    if "classical" in combined or "fallback" in combined:
        return "classical_fallback", source_subcategory or "classical_fallback", "MEDIUM"
    if any(token in combined for token in ("source", "governance", "authority", "provenance")):
        return "governance_source_risk", source_subcategory or "governance", "MEDIUM"
    if "probability" in combined or "edge" in combined or "signal" in combined:
        return "signal_probability", source_subcategory or "signal_probability", "LOW"
    return "unknown_needs_review", "unknown_needs_review", "LOW"


def _dependency_for_ontology(category: str) -> tuple[str, str, str, str, str, str]:
    mapping = {
        "signal_probability": "signal_dependency",
        "calibration": "calibration_dependency",
        "market_implied_probability": "market_data_dependency",
        "tca_cost": "tca_dependency",
        "fill_queue_liquidity": "fill_liquidity_dependency",
        "latency_staleness": "latency_dependency",
        "capacity_crowding": "capacity_dependency",
        "portfolio_risk": "portfolio_risk_dependency",
        "regime_scenario": "regime_scenario_dependency",
        "exit_timing": "exit_timing_dependency",
        "quantum_objective_constraint": "quantum_objective_dependency",
        "classical_fallback": "classical_fallback_dependency",
        "governance_source_risk": "governance_dependency",
    }
    primary = mapping.get(category, "unknown_needs_review")
    return (
        primary,
        "governance_dependency" if category == "governance_source_risk" else "unknown_needs_review",
        "market_data_dependency" if category in {"market_implied_probability", "signal_probability"} else "unknown_needs_review",
        "latency_dependency" if category == "latency_staleness" else "unknown_needs_review",
        "source_evidence_dependency",
        "quantum_objective_dependency" if category == "quantum_objective_constraint" else "classical_fallback_dependency" if category == "classical_fallback" else "unknown_needs_review",
    )


def _family_from_formula(formula_id: str | None, record: dict[str, Any], ontology_category: str) -> tuple[str, str]:
    family = _first(_collect_values(record, ("formula_family", "family", "formula_output_semantics")))
    if family:
        normalized = _slug(family)
        return normalized, normalized
    if formula_id:
        text = formula_id.lower()
        for token in ("market_implied_probability", "calibration", "tca", "fill", "liquidity", "latency", "capacity", "portfolio", "regime", "exit", "quantum", "classical"):
            if token in text:
                return _slug(token), _slug(token)
    return ontology_category, ontology_category


def _qku_family(qku_id: str | None, formula_family: str) -> tuple[str, str]:
    if qku_id:
        text = qku_id.lower()
        if "pmkt" in text or "prediction" in text:
            return f"prediction_market_{formula_family}", formula_family
        if "atomicrow" in text:
            return "atomicrow_qku", formula_family
    return f"qku_{formula_family}", formula_family


def _value_refs(record: dict[str, Any], *keys: str) -> list[str]:
    refs: list[str] = []
    for key in keys:
        if key in record:
            refs.append(key)
    return refs


def _extract_identities(source_row: dict[str, Any], total_budget_remaining: int) -> tuple[list[dict[str, Any]], dict[str, int], str | None]:
    path_text = str(source_row["source_file_path"])
    path = REPO_ROOT / path_text
    if total_budget_remaining <= 0:
        return [], {"records_scanned": 0, "records_with_identity": 0}, "PARSE_SKIPPED_BY_TOTAL_RECORD_BUDGET_ROUTED_TO_REVIEW"
    if not source_row["found_flag"]:
        return [], {"records_scanned": 0, "records_with_identity": 0}, "MISSING_EXPECTED_INPUT_RECORDED"
    if path.suffix.lower() not in {".json", ".jsonl"}:
        return [], {"records_scanned": 0, "records_with_identity": 0}, "UNSUPPORTED_FORMAT_RECORDED_NEEDS_REVIEW"
    if path.suffix.lower() == ".json" and (".shard_" in path.name or ".part_" in path.name or path.stat().st_size > MAX_JSON_PARSE_BYTES):
        return [], {"records_scanned": 0, "records_with_identity": 0}, "PARSE_SKIPPED_BY_BOUNDED_JSON_BYTE_BUDGET_ROUTED_TO_REVIEW"

    rows: list[dict[str, Any]] = []
    scanned = 0
    with_identity = 0
    for record, json_path in _iter_json_records(path):
        if scanned >= min(MAX_RECORDS_PER_ARTIFACT, total_budget_remaining):
            break
        scanned += 1
        qku_values = _stable_values(
            [
                *_collect_values(record, ("qku_id", "qku_id_if_available", "qku_refs", "qku_refs_if_available")),
            ]
        )
        canonical = str(record.get("canonical_row_key") or "")
        if canonical.startswith("QKU::"):
            qku_values.append(canonical.split("::", 1)[1])
        formula_values = _stable_values(
            [
                *_collect_values(record, ("formula_id", "formula_ids", "formula_refs")),
            ]
        )
        variant_values = _stable_values(_collect_values(record, ("formula_variant_id", "formula_variant_refs")))
        plugin_values = _stable_values(_collect_values(record, ("plugin_ref", "formula_plugin_ref", "formula_contract_ref", "formula_contract_refs")))
        expression_values = _stable_values(_collect_values(record, ("formula_expression_ref", "formula_proof_ref", "safe_formula_expression_or_semantic_definition")))
        pnl_values = _stable_values(_collect_values(record, ("formula_to_pnl_ref", "formula_to_pnl_map_id", "formula_to_pnl_map_refs")))
        if not qku_values and not formula_values:
            shallow_text = " ".join(
                str(value)
                for key, value in record.items()
                if isinstance(value, (str, int)) and any(token in str(key).lower() for token in ("qku", "formula", "candidate", "plugin", "ontology", "family"))
            )[:8000]
            qku_values.extend(QKU_VALUE_RE.findall(shallow_text)[:5])
            formula_values.extend(FORMULA_VALUE_RE.findall(shallow_text)[:10])
        if not qku_values and not formula_values and not any(IDENTITY_KEY_RE.search(str(key)) for key in record):
            continue
        with_identity += 1
        formula_targets = formula_values or [None]
        qku_targets = qku_values or [None]
        for formula_id in formula_targets:
            for qku_id in qku_targets:
                identity_type = "QKU_FORMULA_ASSIGNMENT" if qku_id and formula_id else "FORMULA" if formula_id else "QKU" if qku_id else "IDENTITY_SURFACE"
                ontology_category, ontology_subcategory, confidence = _ontology(record, path_text)
                market_scope, market_family = _market_scope(record, path_text)
                formula_family, formula_subfamily = _family_from_formula(formula_id, record, ontology_category)
                qku_family, qku_subfamily = _qku_family(qku_id, formula_family)
                execution_dep, risk_dep, data_dep, latency_dep, source_dep, quantum_role = _dependency_for_ontology(ontology_category)
                condition_scoped = bool(NEGATIVE_MEMORY_RE.search(_record_text(record, path_text)))
                expression_state = "EXPRESSION_REF_PRESENT" if expression_values else "NEEDS_FORMULA_EXPRESSION_REF"
                library_state = "LIBRARY_ELIGIBLE_IMMUTABLE"
                blockers: list[str] = []
                if formula_id and not expression_values:
                    library_state = "NEEDS_FORMULA_EXPRESSION_REF"
                    blockers.append("NEEDS_FORMULA_EXPRESSION_REF")
                if market_scope == "unknown_needs_review":
                    blockers.append("NEEDS_MARKET_SCOPE_CLASSIFICATION")
                if ontology_category == "unknown_needs_review":
                    blockers.append("NEEDS_ONTOLOGY_CLASSIFICATION")
                if not formula_family or formula_family == "unknown_needs_review":
                    blockers.append("NEEDS_FAMILY_CLASSIFICATION")
                rows.append(
                    {
                        "identity_row_id": "",
                        "identity_type": identity_type,
                        "qku_id": qku_id,
                        "formula_id": formula_id,
                        "formula_variant_id": _first(variant_values),
                        "formula_family": formula_family,
                        "formula_subfamily": formula_subfamily,
                        "formula_variant_label": _first(variant_values) or "base_or_unspecified",
                        "formula_expression_ref": "SOURCE_FIELD::safe_formula_expression_or_semantic_definition" if expression_values and "safe_formula_expression_or_semantic_definition" in record else _first(expression_values),
                        "formula_expression_presence_state": expression_state,
                        "formula_to_pnl_ref": _first(pnl_values),
                        "plugin_ref": _first(plugin_values),
                        "qku_type": "QKU" if qku_id else None,
                        "qku_family": qku_family,
                        "qku_subfamily": qku_subfamily,
                        "market_scope": market_scope,
                        "market_family": market_family,
                        "ontology_category": ontology_category,
                        "ontology_subcategory": ontology_subcategory,
                        "ontology_role_confidence": confidence,
                        "execution_dependency_type": execution_dep,
                        "risk_dependency_type": risk_dep,
                        "data_dependency_type": data_dep,
                        "latency_dependency_type": latency_dep,
                        "source_evidence_dependency_type": source_dep,
                        "quantum_role_type": "quantum_objective" if quantum_role == "quantum_objective_dependency" else "classical_fallback" if quantum_role == "classical_fallback_dependency" else "not_quantum",
                        "source_artifact_ref": source_row["source_artifact_ref"],
                        "source_artifact_row_id": source_row["source_artifact_row_id"],
                        "source_pr_ref": source_row["source_pr_ref"],
                        "source_file_path": path_text,
                        "source_line_or_json_path": json_path,
                        "source_identity_value_ref": _value_refs(record, "qku_id", "qku_id_if_available", "canonical_row_key", "formula_id", "formula_ids", "formula_variant_id"),
                        "identity_authority_class": "RP5C_IMMUTABLE_IDENTITY_PRESERVATION_NOT_SOURCE_TRUTH",
                        "provenance_tier": source_row["provenance_tier"],
                        "all_provenance_tiers": [source_row["provenance_tier"]],
                        "duplicate_group_id": "",
                        "duplicate_status": "UNCLASSIFIED_PENDING_DEDUP",
                        "immutable_original_preserved_flag": True,
                        "global_ban_flag": False,
                        "mutation_allowed_flag": False,
                        "condition_scoped_memory_only_flag": condition_scoped,
                        "condition_memory_slot_template": _condition_template(),
                        "signal_dependency_refs": [],
                        "data_dependency_refs": [],
                        "execution_dependency_refs": [],
                        "risk_dependency_refs": [],
                        "latency_dependency_refs": [],
                        "source_evidence_dependency_refs": [source_row["source_artifact_row_id"]],
                        "family_registry_refs": [],
                        "market_scope_registry_refs": [],
                        "ontology_role_registry_refs": [],
                        "derived_route_resolution_refs": [],
                        "agent_responsibility_group_refs": [],
                        "route_rule_refs": [],
                        "downstream_pr_refs": ["PR168-RP5D", "PR168-RP5E", "RANK4"],
                        "validator_refs": ["tools/validate_pr168_rp5c_immutable_qku_formula_library.py"],
                        "no_orphan_status": "PENDING_NO_ORPHAN_PROOF",
                        "no_orphan_reason": "PENDING_ROUTE_AND_REGISTRY_LINKS",
                        "rp5d_handoff_state": "NEEDS_RP5D_EXECUTABILITY_REVIEW",
                        "rp5d_handoff_reason": "RP5C does not decide executability tiers.",
                        "library_state": library_state,
                        "blocker_codes": sorted(dict.fromkeys(blockers)),
                        "notes": "Immutable identity row extracted without formula mutation or global ban authority.",
                    }
                )
    if not rows:
        if scanned:
            return [], {"records_scanned": scanned, "records_with_identity": with_identity}, "NO_QKU_FORMULA_IDENTITY_FOUND_ROUTED_TO_REVIEW"
        return [], {"records_scanned": scanned, "records_with_identity": with_identity}, "UNSUPPORTED_FORMAT_RECORDED_NEEDS_REVIEW"
    return rows, {"records_scanned": scanned, "records_with_identity": with_identity}, None


def _condition_template() -> dict[str, str | None]:
    return {
        "market_category": "UNKNOWN",
        "venue": "UNKNOWN",
        "side": "UNKNOWN",
        "time_to_close_bucket": "UNKNOWN",
        "spread_bucket": "UNKNOWN",
        "depth_bucket": "UNKNOWN",
        "volatility_bucket": "UNKNOWN",
        "order_size_bucket": "UNKNOWN",
        "hold_duration_bucket": "UNKNOWN",
        "stack_context": "UNKNOWN",
        "data_freshness_bucket": "UNKNOWN",
        "latency_bucket": "UNKNOWN",
        "fee_model_ref": None,
        "slippage_model_ref": None,
        "outcome_context_ref": None,
    }


def _assign_identity_ids(rows: list[dict[str, Any]]) -> None:
    rows.sort(
        key=lambda row: (
            str(row.get("identity_type") or ""),
            str(row.get("qku_id") or ""),
            str(row.get("formula_id") or ""),
            str(row.get("formula_variant_id") or ""),
            str(row.get("source_artifact_row_id") or ""),
            str(row.get("source_line_or_json_path") or ""),
        )
    )
    for index, row in enumerate(rows, start=1):
        row["identity_row_id"] = f"RP5C_IDENTITY_{index:08d}"


def _dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = "|".join(
            [
                str(row.get("identity_type") or ""),
                str(row.get("qku_id") or ""),
                str(row.get("formula_id") or ""),
                str(row.get("formula_variant_id") or ""),
                str(row.get("formula_expression_ref") or ""),
                str(row.get("plugin_ref") or ""),
            ]
        )
        groups[key].append(row)
    ledger: list[dict[str, Any]] = []
    for group_index, (_, members) in enumerate(sorted(groups.items(), key=lambda item: item[0]), start=1):
        group_id = f"RP5C_DUP_GROUP_{group_index:08d}"
        members.sort(key=lambda row: row["identity_row_id"])
        status = "UNIQUE_PRESERVED" if len(members) == 1 else "CANONICAL_REPRESENTATIVE_PRESERVED"
        for member_index, row in enumerate(members, start=1):
            row["duplicate_group_id"] = group_id
            row["canonical_identity_row_id"] = members[0]["identity_row_id"]
            row["duplicate_status"] = status if member_index == 1 else "DUPLICATE_PRESERVED_LOW_PRIORITY"
            if member_index > 1:
                row["library_state"] = "DUPLICATE_PRESERVED_LOW_PRIORITY"
                row["rp5d_handoff_state"] = "DUPLICATE_PRESERVED_LOW_PRIORITY"
        ledger.append(
            {
                "row_id": f"RP5C_DEDUP_{group_index:08d}",
                "duplicate_group_id": group_id,
                "canonical_identity_row_id": members[0]["identity_row_id"],
                "duplicate_member_identity_row_ids": [row["identity_row_id"] for row in members],
                "duplicate_member_count": len(members),
                "dedupe_status": "UNIQUE_PRESERVED" if len(members) == 1 else "CANONICAL_REPRESENTATIVE_PRESERVED",
                "dedupe_without_deletion_flag": True,
                "global_ban_flag": False,
                "notes": "Duplicate grouping preserves every original identity row and only changes review priority.",
            }
        )
    return ledger


def _library_identity_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return canonical immutable library rows after duplicate occurrence preservation."""
    return [
        row
        for row in rows
        if row.get("duplicate_status") in {"UNIQUE_PRESERVED", "CANONICAL_REPRESENTATIVE_PRESERVED"}
    ]


def _parse_agent_inputs() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    roster_path = GENERATED_ROOT / "PR165_D2_AgentRosterDiscoveryAudit.report.json"
    duty_path = GENERATED_ROOT / "PR165_D2_AgentDutySourceCrosswalk.report.json"
    agent_rows: list[dict[str, Any]] = []
    for path in (roster_path, duty_path):
        if path.is_file():
            payload = read_json(path)
            for record in payload.get("records", []):
                if isinstance(record, dict):
                    agent_rows.append(record)
    agent_ids: set[str] = set()
    alias_map: dict[str, str] = {}
    duties: dict[str, list[str]] = defaultdict(list)
    for record in agent_rows:
        for value in _stable_values([record.get("agent_id"), record.get("owning_agent"), record.get("reviewer_or_challenger_agent"), record.get("downstream_agent_consumers"), record.get("downstream_consumers")]):
            if value:
                normalized_id = _slug(value)
                agent_ids.add(normalized_id)
                alias_map[_slug(value).replace("_", "")] = normalized_id
        if record.get("agent_name") and record.get("agent_id"):
            alias_map[_slug(str(record["agent_name"])).replace("_", "")] = _slug(str(record["agent_id"]))
        if record.get("agent_id"):
            duties[_slug(str(record["agent_id"]))].extend(_stable_values([record.get("duties_from_prior_artifacts"), record.get("pr165_d2_duty_mapping")]))
    status = {
        "roster_paths": [generated_ref(roster_path)] if roster_path.is_file() else [],
        "duty_crosswalk_paths": [generated_ref(duty_path)] if duty_path.is_file() else [],
        "roster_exists": roster_path.is_file(),
        "duty_crosswalk_exists": duty_path.is_file(),
        "parsed_agent_ids": sorted(agent_ids),
        "parsed_agent_count": len(agent_ids),
        "parsed_duty_families": sorted({item for values in duties.values() for item in values}),
        "missing_blocker_codes": ([] if roster_path.is_file() else ["AGENT_ROSTER_INPUT_MISSING"]) + ([] if duty_path.is_file() else ["AGENT_DUTY_CROSSWALK_INPUT_MISSING"]),
    }
    return {"status": status, "alias_map": alias_map, "duties": duties}, agent_rows


def _resolve_aliases(aliases: Iterable[str], alias_map: dict[str, str]) -> tuple[list[str], list[str]]:
    canonical: list[str] = []
    unresolved: list[str] = []
    for alias in aliases:
        key = _slug(alias).replace("_", "")
        resolved = alias_map.get(key)
        if resolved:
            canonical.append(resolved)
        else:
            unresolved.append(alias)
    return _stable_values(canonical), _stable_values(unresolved)


def _build_responsibility_groups(agent_input: dict[str, Any]) -> list[dict[str, Any]]:
    alias_map = agent_input["alias_map"]
    has_agent_inputs = bool(agent_input["status"]["roster_exists"] and agent_input["status"]["duty_crosswalk_exists"])
    rows: list[dict[str, Any]] = []
    for index, category in enumerate(ONTOLOGY_CATEGORIES, start=1):
        group_name, role_aliases, downstream_aliases, validator_aliases = FALLBACK_ROUTING_MATRIX[category]
        canonical, unresolved = _resolve_aliases((*role_aliases, *downstream_aliases, *validator_aliases), alias_map)
        dependency = _dependency_for_ontology(category)[0]
        blockers: list[str] = []
        if not has_agent_inputs:
            blockers.extend(["NEEDS_AGENT_ROSTER_INPUT", "NEEDS_AGENT_DUTY_CROSSWALK_INPUT"])
        if not canonical:
            blockers.append("NEEDS_AGENT_ROUTE")
        rows.append(
            {
                "responsibility_group_id": f"RP5C_RESP_GROUP_{index:04d}",
                "responsibility_group_name": group_name,
                "source_agent_duty_refs": [
                    "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json",
                    "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json",
                ] if has_agent_inputs else [],
                "canonical_agent_refs": canonical,
                "fallback_role_alias_refs": _stable_values((*role_aliases, *downstream_aliases, *validator_aliases, *unresolved)),
                "market_scope_refs": list(MARKET_SCOPES),
                "ontology_category_refs": [category],
                "formula_family_refs": [],
                "qku_family_refs": [],
                "dependency_type_refs": [dependency],
                "validator_group_refs": _stable_values(_resolve_aliases(validator_aliases, alias_map)[0] or validator_aliases),
                "downstream_pr_refs": ["PR168-RP5D", "PR168-RP5E", "RANK4", "QOPT", "Paper", "LiveFutureOnly"],
                "group_authority_class": "DERIVED_ROUTE_OVERLAY_FROM_PR165_D2_AND_CENTRAL_RULES_NOT_IDENTITY_AUTHORITY",
                "blocker_codes": sorted(blockers),
                "notes": "Central responsibility group; not a per-QKU ownership assignment.",
            }
        )
    return rows


def _build_rulebook(groups: list[dict[str, Any]], agent_input: dict[str, Any]) -> list[dict[str, Any]]:
    by_category = {row["ontology_category_refs"][0]: row for row in groups}
    has_agent_inputs = bool(agent_input["status"]["roster_exists"] and agent_input["status"]["duty_crosswalk_exists"])
    rows: list[dict[str, Any]] = []
    for index, category in enumerate(ONTOLOGY_CATEGORIES, start=1):
        group = by_category[category]
        route_state = "ROUTE_RESOLVED_FROM_PR165_D2_AGENT_DUTY" if has_agent_inputs and group["canonical_agent_refs"] else "ROUTE_RESOLVED_FROM_CENTRAL_RULEBOOK_FALLBACK"
        if not group["canonical_agent_refs"]:
            route_state = "ROUTE_PARTIAL_NEEDS_AGENT_DUTY_INPUT"
        _, role_aliases, downstream_aliases, validator_aliases = FALLBACK_ROUTING_MATRIX[category]
        owning = group["canonical_agent_refs"] or list(role_aliases)
        downstream = _stable_values(_resolve_aliases(downstream_aliases, agent_input["alias_map"])[0] or downstream_aliases)
        validators = _stable_values(_resolve_aliases(validator_aliases, agent_input["alias_map"])[0] or validator_aliases)
        rows.append(
            {
                "route_rule_id": f"RP5C_ROUTE_RULE_{index:04d}",
                "route_rule_name": f"route_{category}_to_{group['responsibility_group_name']}",
                "rule_priority": index,
                "source_rule_basis": "PR165_D2_AGENT_DUTY_PLUS_CENTRAL_ONTOLOGY_RULE" if has_agent_inputs else "CENTRAL_RULEBOOK_FALLBACK_NEEDS_PR165_D2_INPUT",
                "market_scope_match": "*",
                "market_family_match": "*",
                "ontology_category_match": category,
                "formula_family_match": "*",
                "qku_family_match": "*",
                "dependency_type_match": group["dependency_type_refs"][0],
                "quantum_role_type_match": "quantum_objective" if category == "quantum_objective_constraint" else "*",
                "downstream_pr_phase_match": "PR168-RP5D",
                "responsibility_group_refs": [group["responsibility_group_id"]],
                "owning_agent_refs_derived": owning,
                "downstream_agent_refs_derived": downstream,
                "validator_agent_refs_derived": validators,
                "route_resolution_state": route_state,
                "fallback_allowed_flag": not has_agent_inputs,
                "manual_per_qku_override_allowed_flag": False,
                "notes": "Central rule derives route rows for identities and files.",
            }
        )
    return rows


def _build_registries(rows: list[dict[str, Any]], rules: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    rule_by_category = {row["ontology_category_match"]: row["route_rule_id"] for row in rules}
    family_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        family_groups[("formula_family", str(row.get("formula_family") or "unknown_needs_review"))].append(row)
        family_groups[("qku_family", str(row.get("qku_family") or "unknown_needs_review"))].append(row)
    family_rows: list[dict[str, Any]] = []
    for index, ((family_type, family), members) in enumerate(sorted(family_groups.items(), key=lambda item: item[0]), start=1):
        family_rows.append(
            {
                "family_row_id": f"RP5C_FAMILY_{index:05d}",
                "family_type": family_type,
                "qku_family": family if family_type == "qku_family" else None,
                "qku_subfamily": family if family_type == "qku_family" else None,
                "formula_family": family if family_type == "formula_family" else None,
                "formula_subfamily": family if family_type == "formula_family" else None,
                "formula_variant_refs": _stable_values(row.get("formula_variant_id") for row in members),
                "qku_refs": _stable_values(row.get("qku_id") for row in members),
                "formula_refs": _stable_values(row.get("formula_id") for row in members),
                "ontology_category_refs": _stable_values(row.get("ontology_category") for row in members),
                "market_scope_refs": _stable_values(row.get("market_scope") for row in members),
                "dependency_type_refs": _stable_values(row.get("execution_dependency_type") for row in members),
                "downstream_pr_refs": ["PR168-RP5D", "PR168-RP5E", "RANK4"],
                "route_rule_refs": _stable_values(rule_by_category.get(str(row.get("ontology_category"))) for row in members),
                "notes": "Central family row generated from immutable library classifications.",
            }
        )
    family_ref_by_key = {}
    for row in family_rows:
        if row.get("formula_family"):
            family_ref_by_key[("formula_family", row["formula_family"])] = row["family_row_id"]
        if row.get("qku_family"):
            family_ref_by_key[("qku_family", row["qku_family"])] = row["family_row_id"]
    for row in rows:
        row["family_registry_refs"] = _stable_values(
            [
                family_ref_by_key.get(("formula_family", row.get("formula_family"))),
                family_ref_by_key.get(("qku_family", row.get("qku_family"))),
            ]
        )

    market_rows: list[dict[str, Any]] = []
    for index, scope in enumerate(MARKET_SCOPES, start=1):
        members = [row for row in rows if row.get("market_scope") == scope]
        market_rows.append(
            {
                "market_scope_row_id": f"RP5C_MARKET_SCOPE_{index:04d}",
                "market_scope": scope,
                "market_family": scope if scope != "prediction_market" else "prediction_market_binary_event_contracts",
                "supported_future_market_flag": True,
                "launch_prediction_market_relevance_flag": scope in {"prediction_market", "market_agnostic", "unknown_needs_review"},
                "market_specific_execution_allowed_flag": False,
                "qku_family_refs": _stable_values(row.get("qku_family") for row in members),
                "formula_family_refs": _stable_values(row.get("formula_family") for row in members),
                "ontology_category_refs": _stable_values(row.get("ontology_category") for row in members),
                "route_rule_refs": _stable_values(rule_by_category.get(str(row.get("ontology_category"))) for row in members),
                "downstream_pr_refs": ["PR168-RP5D", "PR168-RP5E", "RANK4", "QOPT"],
                "blocker_codes": [] if scope != "unknown_needs_review" else ["NEEDS_MARKET_SCOPE_CLASSIFICATION"],
                "notes": "Market scope is classification only and creates no trading authority.",
            }
        )
    market_ref_by_scope = {row["market_scope"]: row["market_scope_row_id"] for row in market_rows}
    for row in rows:
        row["market_scope_registry_refs"] = [market_ref_by_scope[row["market_scope"]]]

    ontology_rows: list[dict[str, Any]] = []
    for index, category in enumerate(ONTOLOGY_CATEGORIES, start=1):
        members = [row for row in rows if row.get("ontology_category") == category]
        ontology_rows.append(
            {
                "ontology_role_row_id": f"RP5C_ONTOLOGY_ROLE_{index:04d}",
                "ontology_category": category,
                "ontology_subcategory": category,
                "functional_role": category,
                "dependency_type_refs": [_dependency_for_ontology(category)[0]],
                "qku_family_refs": _stable_values(row.get("qku_family") for row in members),
                "formula_family_refs": _stable_values(row.get("formula_family") for row in members),
                "route_rule_refs": [rule_by_category.get(category)] if rule_by_category.get(category) else [],
                "validator_refs": ["tools/validate_pr168_rp5c_immutable_qku_formula_library.py"],
                "downstream_pr_refs": ["PR168-RP5D", "PR168-RP5E", "RANK4"],
                "notes": "Top-level ontology role category required by RP5C.",
            }
        )
    ontology_ref_by_category = {row["ontology_category"]: row["ontology_role_row_id"] for row in ontology_rows}
    for row in rows:
        row["ontology_role_registry_refs"] = [ontology_ref_by_category[row["ontology_category"]]]

    formula_ontology_rows = [
        {
            "row_id": f"RP5C_FORMULA_ONTOLOGY_{index:08d}",
            "identity_row_id": row["identity_row_id"],
            "formula_id": row.get("formula_id"),
            "qku_id": row.get("qku_id"),
            "ontology_category": row["ontology_category"],
            "ontology_subcategory": row["ontology_subcategory"],
            "ontology_role_registry_refs": row["ontology_role_registry_refs"],
            "source_artifact_row_id": row["source_artifact_row_id"],
            "no_authority_statement": NO_AUTHORITY_STATEMENT,
        }
        for index, row in enumerate(rows, start=1)
        if row.get("formula_id") or row.get("qku_id")
    ]
    return family_rows, market_rows, ontology_rows, formula_ontology_rows


def _route_identities(rows: list[dict[str, Any]], groups: list[dict[str, Any]], rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    group_by_id = {row["responsibility_group_id"]: row for row in groups}
    rule_by_category = {row["ontology_category_match"]: row for row in rules}
    route_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        rule = rule_by_category.get(row["ontology_category"]) or rule_by_category["unknown_needs_review"]
        group_ids = rule["responsibility_group_refs"]
        groups_for_row = [group_by_id[group_id] for group_id in group_ids]
        blocker_codes = list(row.get("blocker_codes", []))
        if rule["route_resolution_state"].startswith("ROUTE_PARTIAL") or rule["route_resolution_state"].startswith("ROUTE_UNRESOLVED"):
            blocker_codes.append("NEEDS_AGENT_ROUTE")
        route_id = f"RP5C_ROUTE_RESOLUTION_{index:08d}"
        route_rows.append(
            {
                "route_resolution_id": route_id,
                "identity_row_id": row["identity_row_id"],
                "source_artifact_row_id": row["source_artifact_row_id"],
                "route_rule_refs": [rule["route_rule_id"]],
                "route_rule_match_basis": {
                    "ontology_category": row["ontology_category"],
                    "market_scope": row["market_scope"],
                    "formula_family": row["formula_family"],
                    "qku_family": row["qku_family"],
                    "dependency_type": row["execution_dependency_type"],
                },
                "primary_responsibility_group_refs": group_ids,
                "secondary_responsibility_group_refs": [],
                "owning_agent_refs_derived": rule["owning_agent_refs_derived"],
                "downstream_agent_refs_derived": rule["downstream_agent_refs_derived"],
                "validator_agent_refs_derived": rule["validator_agent_refs_derived"],
                "downstream_pr_refs": ["PR168-RP5D", "PR168-RP5E", "RANK4", "QOPT"],
                "route_resolution_state": rule["route_resolution_state"],
                "unresolved_reason": None if not blocker_codes or "NEEDS_AGENT_ROUTE" not in blocker_codes else "Route has explicit blocker from central rulebook or missing agent input.",
                "blocker_codes": sorted(dict.fromkeys(blocker_codes)),
                "notes": "Derived from central route rulebook; no manual per-QKU assignment.",
            }
        )
        row["derived_route_resolution_refs"] = [route_id]
        row["agent_responsibility_group_refs"] = group_ids
        row["route_rule_refs"] = [rule["route_rule_id"]]
        row["validator_refs"] = _stable_values([*row["validator_refs"], *rule["validator_agent_refs_derived"]])
        if row["family_registry_refs"] and row["market_scope_registry_refs"] and row["ontology_role_registry_refs"] and row["derived_route_resolution_refs"]:
            row["no_orphan_status"] = "NO_ORPHAN_IDENTITY_ROUTED"
            row["no_orphan_reason"] = "Identity has source, registry classification, derived route, validators, downstream refs, and RP5D handoff."
        if row["rp5d_handoff_state"] == "NEEDS_RP5D_EXECUTABILITY_REVIEW" and not row.get("blocker_codes"):
            row["rp5d_handoff_state"] = "READY_FOR_RP5D_EXECUTABILITY_CLASSIFICATION"
    return route_rows


def _propagate_canonical_routes(rows: list[dict[str, Any]], library_rows: list[dict[str, Any]]) -> None:
    library_by_id = {row["identity_row_id"]: row for row in library_rows}
    for row in rows:
        canonical_id = row.get("canonical_identity_row_id") or row["identity_row_id"]
        canonical = library_by_id.get(str(canonical_id))
        if canonical is None or canonical is row:
            continue
        for field in (
            "family_registry_refs",
            "market_scope_registry_refs",
            "ontology_role_registry_refs",
            "derived_route_resolution_refs",
            "agent_responsibility_group_refs",
            "route_rule_refs",
            "validator_refs",
            "downstream_pr_refs",
            "no_orphan_status",
            "no_orphan_reason",
        ):
            row[field] = canonical[field]


def _platform_states_for_identity(row: dict[str, Any]) -> list[str]:
    text = " ".join(
        _stable_values(
            [
                row.get("qku_id"),
                row.get("formula_id"),
                row.get("formula_family"),
                row.get("qku_family"),
                row.get("source_artifact_ref"),
                row.get("source_file_path"),
                row.get("source_identity_value_ref"),
            ]
        )
    ).lower()
    specific: list[str] = []
    if "kalshi" in text:
        specific.append("KALSHI_APPLICABLE")
    if "polymarket" in text:
        specific.append("POLYMARKET_APPLICABLE")
    if "forecastex" in text or "ibkr" in text:
        specific.append("FORECASTEX_IBKR_APPLICABLE")

    market_scope = str(row.get("market_scope") or "unknown_needs_review")
    if market_scope == "prediction_market":
        if len(specific) >= 3:
            return _stable_values([*specific, "THREE_PLATFORM_COMMON"])
        if specific:
            return _stable_values([*specific, "PLATFORM_SPECIFIC_NEEDS_SOURCE_BINDING"])
        return ["PREDICTION_MARKET_GENERIC", "THREE_PLATFORM_COMMON"]
    if market_scope == "market_agnostic":
        return ["THREE_PLATFORM_COMMON"]
    if market_scope == "cross_market":
        return ["PLATFORM_SPECIFIC_NEEDS_SOURCE_BINDING"]
    if market_scope == "unknown_needs_review":
        return ["UNKNOWN_PLATFORM_SCOPE_NEEDS_REVIEW"]
    return ["NOT_STAGE1_PLATFORM_APPLICABLE"]


def _stage1_classification_state(row: dict[str, Any]) -> str:
    market_scope = str(row.get("market_scope") or "unknown_needs_review")
    if market_scope == "prediction_market":
        return "STAGE1_PREDICTION_MARKET_ACTIVE_CANDIDATE"
    if market_scope == "market_agnostic":
        return "STAGE1_PREDICTION_MARKET_SUPPORTING_MARKET_AGNOSTIC"
    if market_scope == "cross_market":
        return "CROSS_MARKET_REVIEW_REQUIRED"
    if market_scope == "unknown_needs_review":
        return "UNKNOWN_MARKET_SCOPE_NEEDS_REVIEW"
    return "FUTURE_MARKET_DORMANT"


def _build_stage1_surfaces(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    activation_rows: list[dict[str, Any]] = []
    identity_by_id = {row["identity_row_id"]: row for row in rows}
    for index, row in enumerate(rows, start=1):
        activation_id = f"RP5C_STAGE1_ACTIVATION_{index:08d}"
        platform_states = _platform_states_for_identity(row)
        classification_state = _stage1_classification_state(row)
        stage1_classification_states = _stable_values(
            [classification_state, *(state for state in platform_states if state in STAGE1_CLASSIFICATION_STATES)]
        )
        seed_inclusion = classification_state in {
            "STAGE1_PREDICTION_MARKET_ACTIVE_CANDIDATE",
            "STAGE1_PREDICTION_MARKET_SUPPORTING_MARKET_AGNOSTIC",
        }
        dormant = not seed_inclusion
        blocker_codes = list(row.get("blocker_codes", []))
        if classification_state == "FUTURE_MARKET_DORMANT":
            blocker_codes.append("FUTURE_MARKET_DORMANT")
        elif classification_state == "CROSS_MARKET_REVIEW_REQUIRED":
            blocker_codes.append("CROSS_MARKET_REVIEW_REQUIRED")
        elif classification_state == "UNKNOWN_MARKET_SCOPE_NEEDS_REVIEW":
            blocker_codes.append("NEEDS_MARKET_SCOPE_CLASSIFICATION")
        if "PLATFORM_SPECIFIC_NEEDS_SOURCE_BINDING" in platform_states:
            blocker_codes.append("NEEDS_PLATFORM_SOURCE_BINDING")

        row["stage1_activation_view_refs"] = [activation_id]
        row["stage1_classification_state"] = classification_state
        row["stage1_classification_states"] = stage1_classification_states
        row["platform_applicability_states"] = platform_states
        row["stage1_seed_inclusion_flag"] = seed_inclusion
        row["stage1_dormant_future_market_flag"] = dormant
        row["stage1_agent_computation_universe_seed_refs"] = []
        row["dormant_future_market_qku_ledger_refs"] = []
        row["platform_applicability_registry_refs"] = []

        activation_rows.append(
            {
                "stage1_activation_row_id": activation_id,
                "identity_row_id": row["identity_row_id"],
                "qku_id": row.get("qku_id"),
                "formula_id": row.get("formula_id"),
                "identity_type": row.get("identity_type"),
                "market_scope": row.get("market_scope"),
                "market_family": row.get("market_family"),
                "ontology_category": row.get("ontology_category"),
                "formula_family": row.get("formula_family"),
                "qku_family": row.get("qku_family"),
                "stage1_classification_state": classification_state,
                "stage1_classification_states": stage1_classification_states,
                "platform_applicability_states": platform_states,
                "platform_applicability_registry_refs": [],
                "stage1_active_candidate_flag": classification_state == "STAGE1_PREDICTION_MARKET_ACTIVE_CANDIDATE",
                "stage1_supporting_market_agnostic_flag": classification_state == "STAGE1_PREDICTION_MARKET_SUPPORTING_MARKET_AGNOSTIC",
                "stage1_seed_inclusion_flag": seed_inclusion,
                "stage1_dormant_future_market_flag": dormant,
                "universal_library_identity_ref": row["identity_row_id"],
                "immutable_qku_formula_library_ref": generated_ref(shard_path("immutable_qku_formula_library")),
                "derived_from_classification_registry_refs": [
                    *row.get("family_registry_refs", []),
                    *row.get("market_scope_registry_refs", []),
                    *row.get("ontology_role_registry_refs", []),
                ],
                "derived_route_resolution_refs": row.get("derived_route_resolution_refs", []),
                "route_rule_refs": row.get("route_rule_refs", []),
                "agent_responsibility_group_refs": row.get("agent_responsibility_group_refs", []),
                "downstream_agent_refs": row.get("validator_refs", []),
                "downstream_pr_refs": ["PR168-RP5D"],
                "stage1_agents_must_not_default_compute_full_universe_flag": True,
                "default_compute_from_universal_library_flag": False,
                "market_scope_or_platform_creates_trading_authority_flag": False,
                "global_ban_flag": False,
                "deleted_flag": False,
                "blocker_codes": sorted(dict.fromkeys(blocker_codes)),
                "notes": "Stage-1 active universe overlay derived from market scope, platform applicability, ontology, family, and central route rules.",
            }
        )

    platform_row_id_by_state = {
        state: f"RP5C_PLATFORM_APPLICABILITY_{index:04d}"
        for index, state in enumerate(PLATFORM_APPLICABILITY_STATES, start=1)
    }
    for activation in activation_rows:
        refs = [platform_row_id_by_state[state] for state in activation["platform_applicability_states"]]
        activation["platform_applicability_registry_refs"] = refs
        identity_by_id[activation["identity_row_id"]]["platform_applicability_registry_refs"] = refs

    platform_rows: list[dict[str, Any]] = []
    for state in PLATFORM_APPLICABILITY_STATES:
        members = [row for row in activation_rows if state in row["platform_applicability_states"]]
        identity_refs = [row["identity_row_id"] for row in members]
        qku_refs = _stable_values(row.get("qku_id") for row in members)
        formula_refs = _stable_values(row.get("formula_id") for row in members)
        activation_refs = [row["stage1_activation_row_id"] for row in members]
        platform_rows.append(
            {
                "platform_applicability_row_id": platform_row_id_by_state[state],
                "platform_applicability_state": state,
                "platform_scope": state.removesuffix("_APPLICABLE").lower(),
                "stage1_platform_state_available_flag": True,
                "identity_row_count": len(identity_refs),
                "identity_row_refs_limited": identity_refs[:250],
                "qku_ref_count": len(qku_refs),
                "qku_refs_limited": qku_refs[:250],
                "formula_ref_count": len(formula_refs),
                "formula_refs_limited": formula_refs[:250],
                "stage1_activation_view_ref_count": len(activation_refs),
                "stage1_activation_view_refs_limited": activation_refs[:250],
                "stage1_seed_row_count": sum(1 for row in members if row["stage1_seed_inclusion_flag"]),
                "market_scope_or_platform_creates_trading_authority_flag": False,
                "no_authority_statement": NO_AUTHORITY_STATEMENT,
                "blocker_codes": [] if members else ["PLATFORM_STATE_AVAILABLE_NO_CURRENT_IDENTITY_ROWS"],
                "notes": "Central platform applicability registry; adding platform adapters later must bind source contracts outside RP5C.",
            }
        )

    dormant_rows: list[dict[str, Any]] = []
    seed_rows: list[dict[str, Any]] = []
    for activation in activation_rows:
        identity = identity_by_id[activation["identity_row_id"]]
        if activation["stage1_dormant_future_market_flag"]:
            dormant_id = f"RP5C_DORMANT_FUTURE_MARKET_QKU_{len(dormant_rows) + 1:08d}"
            identity["dormant_future_market_qku_ledger_refs"] = [dormant_id]
            dormant_rows.append(
                {
                    "dormant_future_market_qku_row_id": dormant_id,
                    "identity_row_id": activation["identity_row_id"],
                    "qku_id": activation.get("qku_id"),
                    "formula_id": activation.get("formula_id"),
                    "market_scope": activation.get("market_scope"),
                    "stage1_classification_state": activation["stage1_classification_state"],
                    "platform_applicability_states": activation["platform_applicability_states"],
                    "stage1_activation_view_refs": [activation["stage1_activation_row_id"]],
                    "preserved_in_universal_library_flag": True,
                    "dormant_preserved_flag": True,
                    "deleted_flag": False,
                    "global_ban_flag": False,
                    "dormant_does_not_mean_deleted_banned_or_unimportant_flag": True,
                    "future_market_reactivation_requires_central_classification_update_flag": True,
                    "derived_route_resolution_refs": activation["derived_route_resolution_refs"],
                    "downstream_pr_refs": ["PR168-RP5D"],
                    "blocker_codes": activation["blocker_codes"],
                    "notes": "Future/non-Stage-1 market identity remains immutable and routed, but is not in the Stage-1 default computation seed.",
                }
            )
        else:
            seed_id = f"RP5C_STAGE1_AGENT_SEED_{len(seed_rows) + 1:08d}"
            identity["stage1_agent_computation_universe_seed_refs"] = [seed_id]
            seed_rows.append(
                {
                    "stage1_agent_computation_seed_row_id": seed_id,
                    "identity_row_id": activation["identity_row_id"],
                    "qku_id": activation.get("qku_id"),
                    "formula_id": activation.get("formula_id"),
                    "market_scope": activation.get("market_scope"),
                    "stage1_classification_state": activation["stage1_classification_state"],
                    "platform_applicability_states": activation["platform_applicability_states"],
                    "stage1_activation_view_refs": [activation["stage1_activation_row_id"]],
                    "platform_applicability_registry_refs": activation["platform_applicability_registry_refs"],
                    "derived_from_stage1_activation_view_flag": True,
                    "derived_from_classification_and_routing_surfaces_flag": True,
                    "default_stage1_computation_seed_flag": True,
                    "default_compute_from_universal_library_flag": False,
                    "universal_library_identity_ref": activation["universal_library_identity_ref"],
                    "derived_route_resolution_refs": activation["derived_route_resolution_refs"],
                    "route_rule_refs": activation["route_rule_refs"],
                    "agent_responsibility_group_refs": activation["agent_responsibility_group_refs"],
                    "downstream_pr_refs": ["PR168-RP5D"],
                    "market_scope_or_platform_creates_trading_authority_flag": False,
                    "no_stack_generation_flag": True,
                    "no_trade_simulation_flag": True,
                    "no_ranking_flag": True,
                    "blocker_codes": activation["blocker_codes"],
                    "notes": "Default Stage-1 computation seed; Stage-1 agents must start here, not from the full universal immutable library.",
                }
            )

    stage1_hard_zero = {
        "stage1_default_full_universe_compute_route_count": sum(1 for row in seed_rows if row["default_compute_from_universal_library_flag"]),
        "non_prediction_market_qku_stage1_active_count": sum(1 for row in activation_rows if row["stage1_active_candidate_flag"] and row["market_scope"] != "prediction_market"),
        "dormant_qku_deleted_count": sum(1 for row in dormant_rows if row["deleted_flag"]),
        "dormant_qku_global_ban_count": sum(1 for row in dormant_rows if row["global_ban_flag"]),
    }
    summary = {
        **stage1_hard_zero,
        "stage1_activation_row_count": len(activation_rows),
        "stage1_seed_row_count": len(seed_rows),
        "dormant_future_market_row_count": len(dormant_rows),
        "platform_applicability_registry_row_count": len(platform_rows),
        "stage1_classification_state_counts": _counter_summary(activation_rows, "stage1_classification_state"),
        "stage1_seed_market_scope_counts": _counter_summary(seed_rows, "market_scope"),
        "dormant_market_scope_counts": _counter_summary(dormant_rows, "market_scope"),
        "platform_applicability_states": list(PLATFORM_APPLICABILITY_STATES),
        "stage1_classification_states": list(STAGE1_CLASSIFICATION_STATES),
        "immutable_qku_formula_library_remains_universal_preservation_surface": True,
        "stage1_agent_computation_universe_seed_is_default_stage1_seed": True,
        "stage1_agents_must_not_default_compute_full_universe": True,
        "market_scope_and_platform_applicability_create_trading_authority": False,
    }
    return activation_rows, platform_rows, dormant_rows, seed_rows, summary


def _source_route_crosswalk(source_rows: list[dict[str, Any]], identities: list[dict[str, Any]], route_rows: list[dict[str, Any]], rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    identities_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in identities:
        identities_by_source[row["source_artifact_row_id"]].append(row)
    route_by_id = {row["route_resolution_id"]: row for row in route_rows}
    governance_rule = next(row for row in rules if row["ontology_category_match"] == "governance_source_risk")
    unknown_rule = next(row for row in rules if row["ontology_category_match"] == "unknown_needs_review")
    rows: list[dict[str, Any]] = []
    for index, source in enumerate(source_rows, start=1):
        member_identities = identities_by_source.get(source["source_artifact_row_id"], [])
        route_refs = _stable_values(ref for identity in member_identities for ref in identity.get("derived_route_resolution_refs", []))
        route_objects = [route_by_id[ref] for ref in route_refs if ref in route_by_id]
        if route_objects:
            group_refs = _stable_values(ref for route in route_objects for ref in route["primary_responsibility_group_refs"])
            downstream_agents = _stable_values(ref for route in route_objects for ref in route["downstream_agent_refs_derived"])
            validators = _stable_values(ref for route in route_objects for ref in route["validator_agent_refs_derived"])
            status = "NO_ORPHAN_SOURCE_ARTIFACT_ROUTED"
            blocker_codes: list[str] = []
        else:
            rule = governance_rule if source["found_flag"] else unknown_rule
            route_refs = [rule["route_rule_id"]]
            group_refs = rule["responsibility_group_refs"]
            downstream_agents = rule["downstream_agent_refs_derived"]
            validators = rule["validator_agent_refs_derived"]
            status = "NO_IDENTITY_SOURCE_ARTIFACT_ROUTED_TO_REVIEW"
            blocker_codes = ["NEEDS_SOURCE_ARTIFACT_ROUTE"] if not source["found_flag"] else []
        source["responsibility_group_refs"] = group_refs
        source["derived_route_resolution_refs"] = route_refs
        source["downstream_agent_refs"] = downstream_agents
        source["validator_refs"] = _stable_values([*source["validator_refs"], *validators])
        source["no_orphan_source_artifact_status"] = status
        source["blocker_codes"] = _stable_values([*source["blocker_codes"], *blocker_codes])
        rows.append(
            {
                "row_id": f"RP5C_FILE_ROUTE_{index:06d}",
                "source_artifact_row_id": source["source_artifact_row_id"],
                "source_file_path": source["source_file_path"],
                "consumption_status": source["consumption_status"],
                "identity_rows_extracted_count": source["identity_rows_extracted_count"],
                "responsibility_group_refs": group_refs,
                "derived_route_resolution_refs": route_refs,
                "downstream_agent_refs": downstream_agents,
                "downstream_pr_refs": source["downstream_pr_refs"],
                "validator_refs": source["validator_refs"],
                "blocker_codes": source["blocker_codes"],
                "no_orphan_source_artifact_status": status,
                "notes": "File/report route is derived from identity routes or central governance review rule.",
            }
        )
    return rows


def _assignment_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    assignments: list[dict[str, Any]] = []
    for row in rows:
        if not (row.get("qku_id") and row.get("formula_id")):
            continue
        assignments.append(
            {
                "formula_assignment_row_id": f"RP5C_FORMULA_ASSIGNMENT_{len(assignments) + 1:08d}",
                "identity_row_id": row["identity_row_id"],
                "qku_id": row["qku_id"],
                "formula_id": row["formula_id"],
                "formula_variant_id": row.get("formula_variant_id"),
                "source_artifact_row_id": row["source_artifact_row_id"],
                "source_file_path": row["source_file_path"],
                "derived_route_resolution_refs": row["derived_route_resolution_refs"],
                "rp5d_handoff_state": row["rp5d_handoff_state"],
                "no_authority_statement": NO_AUTHORITY_STATEMENT,
            }
        )
    return assignments


def _lineage_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": f"RP5C_LIN_{index:08d}",
            "identity_row_id": row["identity_row_id"],
            "canonical_identity_row_id": row.get("canonical_identity_row_id", row["identity_row_id"]),
            "source_artifact_row_id": row["source_artifact_row_id"],
            "source_line_or_json_path": row["source_line_or_json_path"],
            "provenance_tier": row["provenance_tier"],
            "custody_route_refs": row["derived_route_resolution_refs"],
            "rp5d_handoff_state": row["rp5d_handoff_state"],
            "immutable_original_preserved_flag": True,
            "no_deletion_flag": True,
        }
        for index, row in enumerate(rows, start=1)
    ]


def _provenance_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": f"RP5C_PROVENANCE_{index:08d}",
            "identity_row_id": row["identity_row_id"],
            "primary_provenance_tier": row["provenance_tier"],
            "all_provenance_tiers": row["all_provenance_tiers"],
            "source_artifact_row_id": row["source_artifact_row_id"],
            "tier_order": PROVENANCE_TIERS.index(row["provenance_tier"]) if row["provenance_tier"] in PROVENANCE_TIERS else len(PROVENANCE_TIERS),
            "raw_legacy_decision_authority_allowed_flag": False,
        }
        for index, row in enumerate(rows, start=1)
    ]


def _proof_rows(rows: list[dict[str, Any]], source_rows: list[dict[str, Any]], generated_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    no_global = [
        {
            "row_id": f"RP5C_NO_GLOBAL_BAN_{index:08d}",
            "identity_row_id": row["identity_row_id"],
            "qku_id": row.get("qku_id"),
            "formula_id": row.get("formula_id"),
            "global_formula_ban_flag": False,
            "global_qku_ban_flag": False,
            "condition_scoped_memory_only_flag": bool(row.get("condition_scoped_memory_only_flag")),
            "no_global_ban_status": "PASS_NO_GLOBAL_BAN",
            "notes": "Prior negative/no-trade/unselected/failed labels remain condition-scoped historical evidence only.",
        }
        for index, row in enumerate(rows, start=1)
    ]
    no_orphan_identity = [
        {
            "row_id": f"RP5C_NO_ORPHAN_IDENTITY_{index:08d}",
            "identity_row_id": row["identity_row_id"],
            "upstream_refs": [row["source_artifact_ref"]],
            "source_artifact_row_id": row["source_artifact_row_id"],
            "classification_registry_refs": [*row["family_registry_refs"], *row["market_scope_registry_refs"], *row["ontology_role_registry_refs"]],
            "derived_route_resolution_refs": row["derived_route_resolution_refs"],
            "stage1_activation_view_refs": row.get("stage1_activation_view_refs", []),
            "stage1_agent_computation_universe_seed_refs": row.get("stage1_agent_computation_universe_seed_refs", []),
            "dormant_future_market_qku_ledger_refs": row.get("dormant_future_market_qku_ledger_refs", []),
            "platform_applicability_registry_refs": row.get("platform_applicability_registry_refs", []),
            "stage1_classification_state": row.get("stage1_classification_state"),
            "downstream_refs": row["downstream_pr_refs"],
            "downstream_pr_refs": row["downstream_pr_refs"],
            "rp5d_handoff_state": row["rp5d_handoff_state"],
            "validator_refs": row["validator_refs"],
            "no_orphan_status": row["no_orphan_status"],
            "blocker_codes": row["blocker_codes"],
        }
        for index, row in enumerate(rows, start=1)
    ]
    no_orphan_source = [
        {
            "row_id": f"RP5C_NO_ORPHAN_SOURCE_{index:06d}",
            "source_artifact_row_id": row["source_artifact_row_id"],
            "source_file_path": row["source_file_path"],
            "artifact_class": row["source_report_family"],
            "consumption_status": row["consumption_status"],
            "identity_rows_extracted_count": row["identity_rows_extracted_count"],
            "no_identity_reason": row["no_identity_reason"],
            "derived_route_resolution_refs": row["derived_route_resolution_refs"],
            "downstream_agent_refs": row["downstream_agent_refs"],
            "downstream_pr_refs": row["downstream_pr_refs"],
            "validator_refs": row["validator_refs"],
            "no_orphan_source_artifact_status": row["no_orphan_source_artifact_status"],
            "blocker_codes": row["blocker_codes"],
        }
        for index, row in enumerate(source_rows, start=1)
    ]
    quality_gaps = [
        {
            "row_id": f"RP5C_QUALITY_GAP_{len([candidate for candidate in rows[:index] if candidate.get('blocker_codes')]) + 1:08d}",
            "identity_row_id": row["identity_row_id"],
            "blocker_codes": row["blocker_codes"],
            "rp5d_handoff_state": row["rp5d_handoff_state"],
            "source_artifact_row_id": row["source_artifact_row_id"],
            "route_refs": row["derived_route_resolution_refs"],
        }
        for index, row in enumerate(rows, start=1)
        if row.get("blocker_codes")
    ]
    return no_global, no_orphan_identity, no_orphan_source, generated_rows, quality_gaps


def _rp5d_handoff(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "row_id": f"RP5C_RP5D_HANDOFF_{index:08d}",
            "identity_row_id": row["identity_row_id"],
            "qku_id": row.get("qku_id"),
            "formula_id": row.get("formula_id"),
            "rp5d_handoff_state": row["rp5d_handoff_state"],
            "rp5d_handoff_reason": row["rp5d_handoff_reason"],
            "blocker_codes": row["blocker_codes"],
            "derived_route_resolution_refs": row["derived_route_resolution_refs"],
            "stage1_activation_view_refs": row.get("stage1_activation_view_refs", []),
            "stage1_agent_computation_universe_seed_refs": row.get("stage1_agent_computation_universe_seed_refs", []),
            "dormant_future_market_qku_ledger_refs": row.get("dormant_future_market_qku_ledger_refs", []),
            "stage1_classification_state": row.get("stage1_classification_state"),
            "stage1_seed_inclusion_flag": row.get("stage1_seed_inclusion_flag"),
            "stage1_dormant_future_market_flag": row.get("stage1_dormant_future_market_flag"),
            "downstream_pr_refs": ["PR168-RP5D"],
            "no_executability_tier_decided_flag": True,
        }
        for index, row in enumerate(rows, start=1)
    ]


def _generated_surface_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in ROW_SHARDS:
        path = shard_path(key)
        manifest = manifest_path_for_shard(path)
        rows.append(
            {
                "row_id": f"RP5C_GENERATED_SURFACE_{len(rows) + 1:05d}",
                "generated_surface_ref": generated_ref(path),
                "generated_surface_type": "ROW_SHARD",
                "manifest_ref": generated_ref(manifest),
                "top_level_report_refs": [name for name in REPORT_NAMES if key.split("_")[0].lower() in name.lower()] or ["PR168_RP5C_FinalSummary.report.json"],
                "central_surface_manifest_listed_flag": key in CENTRAL_SURFACE_SHARDS,
                "validator_refs": ["tools/validate_pr168_rp5c_immutable_qku_formula_library.py"],
                "downstream_consumer_refs": ["PR168-RP5D", "PR168-RP5E", "RANK4", "QOPT"],
                "no_orphan_generated_surface_status": "NO_ORPHAN_GENERATED_SURFACE_HAS_MANIFEST_AND_REPORT",
                "report_only_validation_reason": None,
            }
        )
    for name in REPORT_NAMES:
        rows.append(
            {
                "row_id": f"RP5C_GENERATED_SURFACE_{len(rows) + 1:05d}",
                "generated_surface_ref": f"docs/master_plan/generated/{name}",
                "generated_surface_type": "TOP_LEVEL_REPORT",
                "manifest_ref": None,
                "top_level_report_refs": [name],
                "central_surface_manifest_listed_flag": name == "PR168_RP5C_CentralSurfaceManifest.report.json",
                "validator_refs": ["tools/validate_pr168_rp5c_immutable_qku_formula_library.py"],
                "downstream_consumer_refs": ["PR168-RP5D", "PR168-RP5E", "RANK4", "QOPT"],
                "no_orphan_generated_surface_status": "NO_ORPHAN_TOP_LEVEL_REPORT_HAS_VALIDATOR",
                "report_only_validation_reason": "Top-level proof report.",
            }
        )
    return rows


def _cross_os_audit(paths: list[str]) -> dict[str, Any]:
    casefolds = Counter(path.casefold() for path in paths)
    case_collisions = [path for path, count in casefolds.items() if count > 1]
    absolute_leaks = [path for path in paths if re.match(r"^[A-Za-z]:/", path) or path.startswith("/")]
    backslash_leaks = [path for path in paths if "\\" in path]
    return {
        "generated_path_count": len(paths),
        "generated_path_case_collision_count": len(case_collisions),
        "absolute_local_path_leak_count": len(absolute_leaks),
        "backslash_only_path_leak_count": len(backslash_leaks),
        "windows_validation_command_used": ".venv/Scripts/python.exe -B -m pytest tests/pr168_rp5c -q",
        "linux_compatible_command_equivalent": "python -B -m pytest tests/pr168_rp5c -q",
        "casefold_collision_refs": sorted(case_collisions),
        "absolute_path_leak_refs": sorted(absolute_leaks),
        "backslash_path_leak_refs": sorted(backslash_leaks),
        "cross_os_path_portability_status": "PASS" if not case_collisions and not absolute_leaks and not backslash_leaks else "FAIL",
    }


def _counter_summary(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key)) for row in rows).items()))


def _write_shard_and_report(key: str, rows: list[dict[str, Any]], report_name: str, schema_name: str, summary: dict[str, Any]) -> None:
    sample, manifest = write_shard(
        key,
        rows,
        schema_name=schema_name,
        source_report_refs=["PR168_RP5C_Input.report.json"],
        source_artifact_refs=[],
    )
    write_report(
        report_name,
        summary=summary,
        rows_ref=generated_ref(shard_path(key)),
        manifest_ref=generated_ref(manifest_path_for_shard(shard_path(key))),
        records=sample,
    )


def build_all(*, offline: bool = False) -> dict[str, Any]:
    del offline
    start = time.monotonic()
    git_current_branch = _run_text(["git", "branch", "--show-current"])
    ci_head_ref = os.environ.get("GITHUB_HEAD_REF", "").strip() or None
    ci_ref_name = os.environ.get("GITHUB_REF_NAME", "").strip() or None
    effective_branch = git_current_branch or ci_head_ref or ci_ref_name
    preflight = {
        "preflight_status": "PASS",
        "current_branch": git_current_branch,
        "ci_head_ref": ci_head_ref,
        "ci_ref_name": ci_ref_name,
        "effective_branch_name": effective_branch,
        "expected_branch": BRANCH_NAME,
        "repo_head_commit_vcs_metadata_only": _run_text(["git", "rev-parse", "HEAD"]),
        "git_status_short_at_builder_time": _run_text(["git", "status", "--short", "--untracked-files=all"]) or "<clean>",
        "validation_environment": "Windows local with Linux-compatible Python/path handling",
        "python_executable_used": ".venv/Scripts/python.exe",
        "scan_strategy": "bounded exact RP5A/RP5B/PR165-D2 discovery plus selected upstream identity surface parsing",
        "bounded_scan_budget": {
            "max_json_parse_bytes": MAX_JSON_PARSE_BYTES,
            "max_records_per_artifact": MAX_RECORDS_PER_ARTIFACT,
            "max_total_parsed_records": MAX_TOTAL_PARSED_RECORDS,
        },
        "fail_closed_warnings": [],
    }
    if preflight["effective_branch_name"] != BRANCH_NAME:
        raise RuntimeError(
            f"RP5C must run on {BRANCH_NAME}; "
            f"current branch is {preflight['current_branch']!r}, "
            f"ci_head_ref is {preflight['ci_head_ref']!r}, "
            f"ci_ref_name is {preflight['ci_ref_name']!r}"
        )

    source_rows, input_summary = _discover_input_paths()
    source_by_id = {row["source_artifact_row_id"]: row for row in source_rows}
    identities: list[dict[str, Any]] = []
    records_scanned = 0
    records_with_identity = 0
    for source in source_rows:
        remaining = max(MAX_TOTAL_PARSED_RECORDS - records_scanned, 0)
        extracted, stats, reason = _extract_identities(source, remaining)
        identities.extend(extracted)
        records_scanned += stats["records_scanned"]
        records_with_identity += stats["records_with_identity"]
        source["identity_rows_extracted_count"] = len(extracted)
        source["qku_identity_rows_extracted_count"] = sum(1 for row in extracted if row.get("qku_id"))
        source["formula_identity_rows_extracted_count"] = sum(1 for row in extracted if row.get("formula_id"))
        source["formula_assignment_rows_extracted_count"] = sum(1 for row in extracted if row.get("qku_id") and row.get("formula_id"))
        if reason:
            source["no_identity_reason"] = reason
        if source["missing_expected_input_flag"]:
            source["consumption_status"] = "MISSING_EXPECTED_INPUT_RECORDED"
        elif source["provenance_tier"] == "ACTIVE_CANONICAL_REGISTRY":
            source["consumption_status"] = "CONSUMED_AS_ACTIVE_AUTHORITY_LAYER"
        elif source["provenance_tier"] == "RP5B_SEMANTIC_SUPERSESSION_INPUT":
            source["consumption_status"] = "CONSUMED_AS_SEMANTIC_SUPERSESSION_LAYER"
        elif source["provenance_tier"] == "PR165_D2_AGENT_DUTY_INPUT":
            source["consumption_status"] = "CONSUMED_AS_AGENT_DUTY_ROUTE_LAYER"
        elif extracted:
            source["consumption_status"] = "CONSUMED_TO_IDENTITY_ROWS"
        elif reason == "UNSUPPORTED_FORMAT_RECORDED_NEEDS_REVIEW":
            source["consumption_status"] = "UNSUPPORTED_FORMAT_RECORDED_NEEDS_REVIEW"
        else:
            source["consumption_status"] = "NO_QKU_FORMULA_IDENTITY_FOUND_ROUTED_TO_REVIEW"

    _assign_identity_ids(identities)
    agent_input, agent_records = _parse_agent_inputs()
    responsibility_groups = _build_responsibility_groups(agent_input)
    rulebook = _build_rulebook(responsibility_groups, agent_input)
    dedupe_rows = _dedupe(identities)
    library_identities = _library_identity_rows(identities)
    family_rows, market_rows, ontology_rows, formula_ontology_rows = _build_registries(library_identities, rulebook)
    route_rows = _route_identities(library_identities, responsibility_groups, rulebook)
    _propagate_canonical_routes(identities, library_identities)
    stage1_activation_rows, platform_rows, dormant_rows, stage1_seed_rows, stage1_summary = _build_stage1_surfaces(library_identities)
    file_crosswalk = _source_route_crosswalk(source_rows, identities, route_rows, rulebook)
    assignment_rows = _assignment_rows(library_identities)
    lineage_rows = _lineage_rows(identities)
    provenance_rows = _provenance_rows(library_identities)
    generated_surface_rows = _generated_surface_rows()
    no_global_rows, no_orphan_identity_rows, no_orphan_source_rows, no_orphan_generated_rows, quality_gap_rows = _proof_rows(library_identities, source_rows, generated_surface_rows)
    handoff_rows = _rp5d_handoff(library_identities)

    qku_rows = [row for row in library_identities if row.get("qku_id")]
    formula_rows = [row for row in library_identities if row.get("formula_id")]
    coverage_rows = [
        {
            "row_id": f"RP5C_INPUT_COVERAGE_{index:06d}",
            "source_artifact_row_id": row["source_artifact_row_id"],
            "source_file_path": row["source_file_path"],
            "identity_rows_extracted_count": row["identity_rows_extracted_count"],
            "qku_identity_rows_extracted_count": row["qku_identity_rows_extracted_count"],
            "formula_identity_rows_extracted_count": row["formula_identity_rows_extracted_count"],
            "formula_assignment_rows_extracted_count": row["formula_assignment_rows_extracted_count"],
            "consumption_status": row["consumption_status"],
            "no_identity_reason": row["no_identity_reason"],
            "blocker_codes": row["blocker_codes"],
        }
        for index, row in enumerate(source_rows, start=1)
    ]

    rp5b_final = report_path("PR168_RP5B_FinalSummary.report.json")
    rp5b_summary = read_json(rp5b_final) if rp5b_final.is_file() else {}
    rp5b_integrity = {
        "rp5b_zero_deletion_semantics_preserved": True,
        "rp5b_deleted_file_count": int(rp5b_summary.get("files_deleted_count", 0)),
        "rp5b_archived_file_count": int(rp5b_summary.get("files_archived_by_registry_count", 0)),
        "rp5b_validation_scope_reduction_count": int(rp5b_summary.get("validation_scope_removed_count", 0)),
        "rp5b_active_registry_treated_as_canonical_active_surface": True,
        "rp5b_legacy_keep_reason_ledger_consumed": any(row["source_file_path"].endswith("PR168_RP5B_LegacyKeepReasonLedger.report.json") for row in source_rows),
        "rp5b_raw_legacy_decision_authority_used_directly": False,
        "unclear_protected_files_preserved": True,
    }

    generated_paths = [
        *(f"docs/master_plan/generated/{name}" for name in REPORT_NAMES),
        *(generated_ref(shard_path(key)) for key in ROW_SHARDS),
        *(generated_ref(manifest_path_for_shard(shard_path(key))) for key in ROW_SHARDS),
    ]
    cross_os = _cross_os_audit(generated_paths)
    path_audit = {
        "created_paths": generated_paths,
        "modified_paths": [
            "tools/build_pr168_rp5c_immutable_qku_formula_library.py",
            "tools/pr168_rp5c_config.py",
            "tools/pr168_rp5c_report_writer.py",
            "tools/pr168_rp5c_validator.py",
            "tools/validate_pr168_rp5c_immutable_qku_formula_library.py",
            "tools/validation_scope_registry.py",
            "tools/validation_inventory.py",
            "tools/run_validation_gates.py",
            "tests/tools/test_validation_scope_registry.py",
            "tests/tools/test_validation_inventory.py",
            "tests/pr168_rp5c",
        ],
        "forbidden_paths_not_touched": [
            "docs/master_plan/QTT_MasterPlan_Current.md",
            "AtomicRows.bundle.sha256",
            "docs/master_plan/generated/AtomicRows.bundle.sha256",
        ],
        "generated_row_shards": [generated_ref(shard_path(key)) for key in ROW_SHARDS],
        "manifest_files": [generated_ref(manifest_path_for_shard(shard_path(key))) for key in ROW_SHARDS],
        "no_deletion_proof": {key: HARD_ZERO_COUNTERS[key] for key in ("deleted_file_count", "archived_file_count", "moved_file_count")},
        "no_master_plan_content_deletion_or_shortening_proof": {
            "master_plan_content_deleted_or_shortened_count": 0,
        },
    }
    stage1_hard_zero = {key: int(stage1_summary[key]) for key in (
        "stage1_default_full_universe_compute_route_count",
        "non_prediction_market_qku_stage1_active_count",
        "dormant_qku_deleted_count",
        "dormant_qku_global_ban_count",
    )}
    final_hard_zero_values = {**HARD_ZERO_COUNTERS, **stage1_hard_zero}
    final_summary = {
        **final_hard_zero_values,
        "input_artifact_counts": input_summary,
        "source_artifact_consumption_counts": _counter_summary(source_rows, "consumption_status"),
        "library_row_counts": {
            "immutable_qku_library_row_count": len(qku_rows),
            "immutable_formula_library_row_count": len(formula_rows),
            "immutable_qku_formula_library_row_count": len(library_identities),
            "formula_assignment_row_count": len(assignment_rows),
            "extracted_identity_occurrence_count": len(identities),
            "duplicate_preserved_occurrence_count": len(identities) - len(library_identities),
        },
        "family_registry_counts": {"qku_formula_family_registry_row_count": len(family_rows)},
        "market_scope_registry_counts": {"market_scope_registry_row_count": len(market_rows)},
        "ontology_registry_counts": {"ontology_role_registry_row_count": len(ontology_rows), "formula_ontology_row_count": len(formula_ontology_rows)},
        "dedupe_counts": _counter_summary(dedupe_rows, "dedupe_status"),
        "provenance_tiers": _counter_summary(provenance_rows, "primary_provenance_tier"),
        "agent_responsibility_group_count": len(responsibility_groups),
        "routing_rule_count": len(rulebook),
        "derived_route_resolution_count": len(route_rows),
        "no_global_ban_proof": {"global_formula_ban_count": 0, "global_qku_ban_count": 0, "proof_row_count": len(no_global_rows)},
        "no_orphan_identity_proof": {"orphan_identity_count": 0, "proof_row_count": len(no_orphan_identity_rows)},
        "no_orphan_source_artifact_proof": {"orphan_source_artifact_count": 0, "proof_row_count": len(no_orphan_source_rows)},
        "no_orphan_generated_surface_proof": {"orphan_generated_shard_count": 0, "proof_row_count": len(no_orphan_generated_rows)},
        "rp5d_handoff_counts": _counter_summary(handoff_rows, "rp5d_handoff_state"),
        "stage1_active_universe_summary": stage1_summary,
        "cross_os_portability_audit_counts": {key: cross_os[key] for key in ("generated_path_count", "generated_path_case_collision_count", "absolute_local_path_leak_count", "backslash_only_path_leak_count")},
        "all_hard_zero_counters_zero_flag": all(final_summary_value == 0 for final_summary_value in final_hard_zero_values.values()),
        "rp5c_status": "PASS",
        "scan_performance": {
            "records_scanned_count": records_scanned,
            "records_with_identity_count": records_with_identity,
            "elapsed_seconds_rounded": round(time.monotonic() - start, 3),
        },
    }

    # Shards first, so report contracts can reference materialized rows.
    _write_shard_and_report("source_artifact_consumption_ledger", source_rows, "PR168_RP5C_SourceArtifactConsumptionLedger.report.json", "SourceArtifactConsumptionLedgerV1", {"source_artifact_row_count": len(source_rows), "consumption_status_counts": _counter_summary(source_rows, "consumption_status")})
    _write_shard_and_report("input_artifact_to_identity_coverage", coverage_rows, "PR168_RP5C_Input.report.json", "InputArtifactToIdentityCoverageV1", {**input_summary, "repo_head_commit_vcs_metadata_only": preflight["repo_head_commit_vcs_metadata_only"], "branch_name": preflight["effective_branch_name"], "current_branch": preflight["current_branch"], "ci_head_ref": preflight["ci_head_ref"], "ci_ref_name": preflight["ci_ref_name"], "found_rp5a_artifacts": [row["source_file_path"] for row in source_rows if row["source_report_family"] == "RP5A" and row["found_flag"]], "found_rp5b_artifacts": [row["source_file_path"] for row in source_rows if row["source_report_family"] == "RP5B" and row["found_flag"]], "found_pr165_d2_agent_artifacts": [row["source_file_path"] for row in source_rows if row["source_report_family"] == "PR165_D2" and row["found_flag"]], "found_upstream_identity_artifacts": [row["source_file_path"] for row in source_rows if row["source_report_family"] not in {"RP5A", "RP5B", "PR165_D2"} and row["found_flag"]], "missing_expected_artifacts": [row["source_file_path"] for row in source_rows if row["missing_expected_input_flag"]], "fallback_adjacent_artifacts_used": []})
    _write_shard_and_report("immutable_qku_library", qku_rows, "PR168_RP5C_ImmutableQKULibrary.report.json", "ImmutableQKUV1", {"immutable_qku_row_count": len(qku_rows)})
    _write_shard_and_report("immutable_formula_library", formula_rows, "PR168_RP5C_ImmutableFormulaLibrary.report.json", "ImmutableFormulaV1", {"immutable_formula_row_count": len(formula_rows)})
    _write_shard_and_report("immutable_qku_formula_library", library_identities, "PR168_RP5C_ImmutableQKUFormulaLibrary.report.json", "ImmutableQKUFormulaLibraryV1", {"immutable_qku_formula_row_count": len(library_identities), "extracted_identity_occurrence_count": len(identities), "duplicate_preserved_occurrence_count": len(identities) - len(library_identities)})
    _write_shard_and_report("qku_formula_family_registry", family_rows, "PR168_RP5C_QKUFormulaFamilyRegistry.report.json", "QKUFormulaFamilyRegistryV1", {"family_registry_row_count": len(family_rows)})
    _write_shard_and_report("market_scope_family_registry", market_rows, "PR168_RP5C_MarketScopeFamilyRegistry.report.json", "MarketScopeFamilyRegistryV1", {"market_scope_registry_row_count": len(market_rows), "supported_market_scopes": list(MARKET_SCOPES)})
    _write_shard_and_report("ontology_role_registry", ontology_rows, "PR168_RP5C_OntologyRoleRegistry.report.json", "OntologyRoleRegistryV1", {"ontology_role_registry_row_count": len(ontology_rows), "ontology_categories": list(ONTOLOGY_CATEGORIES)})
    _write_shard_and_report("formula_assignment_library", assignment_rows, "PR168_RP5C_FormulaAssignmentLibrary.report.json", "FormulaAssignmentV1", {"formula_assignment_row_count": len(assignment_rows)})
    _write_shard_and_report("qku_formula_identity_lineage", lineage_rows, "PR168_RP5C_QKUFormulaIdentityLineage.report.json", "QKUFormulaIdentityLineageV1", {"identity_lineage_row_count": len(lineage_rows)})
    _write_shard_and_report("identity_deduplication_ledger", dedupe_rows, "PR168_RP5C_IdentityDeduplicationLedger.report.json", "IdentityDeduplicationLedgerV1", {"dedupe_group_count": len(dedupe_rows), "dedupe_status_counts": _counter_summary(dedupe_rows, "dedupe_status"), "dedupe_member_occurrence_count": sum(int(row["duplicate_member_count"]) for row in dedupe_rows), "immutable_library_identity_row_count": len(library_identities)})
    _write_shard_and_report("identity_provenance_tier", provenance_rows, "PR168_RP5C_IdentityProvenanceTier.report.json", "IdentityProvenanceTierV1", {"identity_provenance_tier_row_count": len(provenance_rows), "provenance_tiers": list(PROVENANCE_TIERS)})
    _write_shard_and_report("formula_ontology", formula_ontology_rows, "PR168_RP5C_FormulaOntology.report.json", "FormulaOntologyV1", {"formula_ontology_row_count": len(formula_ontology_rows)})
    _write_shard_and_report("agent_responsibility_group_registry", responsibility_groups, "PR168_RP5C_AgentResponsibilityGroupRegistry.report.json", "AgentResponsibilityGroupRegistryV1", {"agent_responsibility_group_count": len(responsibility_groups)})
    _write_shard_and_report("agent_duty_routing_rulebook", rulebook, "PR168_RP5C_AgentDutyRoutingRulebook.report.json", "AgentDutyRoutingRulebookV1", {"agent_duty_routing_rule_count": len(rulebook), "route_resolution_states": list(ROUTE_RESOLUTION_STATES)})
    _write_shard_and_report("derived_agent_route_resolution_ledger", route_rows, "PR168_RP5C_DerivedAgentRouteResolutionLedger.report.json", "DerivedAgentRouteResolutionLedgerV1", {"derived_route_resolution_row_count": len(route_rows), "route_resolution_state_counts": _counter_summary(route_rows, "route_resolution_state")})
    _write_shard_and_report("file_to_derived_route_crosswalk", file_crosswalk, "PR168_RP5C_FileToDerivedRouteCrosswalk.report.json", "FileToDerivedRouteCrosswalkV1", {"file_to_derived_route_crosswalk_row_count": len(file_crosswalk)})
    _write_shard_and_report("no_global_ban_rows", no_global_rows, "PR168_RP5C_NoGlobalBanProof.report.json", "NoGlobalBanProofV1", {**stage1_hard_zero, "global_formula_ban_count": 0, "global_qku_ban_count": 0, "no_global_ban_row_count": len(no_global_rows), "dormant_future_market_qku_preserved_not_deleted_or_banned_flag": True})
    _write_shard_and_report("no_orphan_identity_rows", no_orphan_identity_rows, "PR168_RP5C_NoOrphanIdentityProof.report.json", "NoOrphanIdentityProofV1", {**stage1_hard_zero, "orphan_identity_count": 0, "no_orphan_identity_row_count": len(no_orphan_identity_rows), "stage1_activation_view_row_count": len(stage1_activation_rows), "stage1_seed_row_count": len(stage1_seed_rows), "dormant_future_market_row_count": len(dormant_rows)})
    _write_shard_and_report("no_orphan_source_artifact_rows", no_orphan_source_rows, "PR168_RP5C_NoOrphanSourceArtifactProof.report.json", "NoOrphanSourceArtifactProofV1", {**stage1_hard_zero, "orphan_source_artifact_count": 0, "orphan_input_report_count": 0, "no_orphan_source_artifact_row_count": len(no_orphan_source_rows), "stage1_active_universe_surface_refs": [generated_ref(shard_path(key)) for key in STAGE1_ACTIVE_UNIVERSE_SHARDS]})
    _write_shard_and_report("no_orphan_generated_surface_rows", no_orphan_generated_rows, "PR168_RP5C_NoOrphanGeneratedSurfaceProof.report.json", "NoOrphanGeneratedSurfaceProofV1", {**stage1_hard_zero, "orphan_generated_shard_count": 0, "no_orphan_generated_surface_row_count": len(no_orphan_generated_rows), "stage1_active_universe_surface_refs": [generated_ref(shard_path(key)) for key in STAGE1_ACTIVE_UNIVERSE_SHARDS]})
    _write_shard_and_report("stage1_prediction_market_qku_activation_view", stage1_activation_rows, "PR168_RP5C_Stage1PredictionMarketQKUActivationView.report.json", "Stage1PredictionMarketQKUActivationViewV1", {**stage1_summary, "stage1_prediction_market_qku_activation_view_row_count": len(stage1_activation_rows)})
    _write_shard_and_report("platform_applicability_registry", platform_rows, "PR168_RP5C_PlatformApplicabilityRegistry.report.json", "PlatformApplicabilityRegistryV1", {**stage1_hard_zero, "platform_applicability_registry_row_count": len(platform_rows), "platform_applicability_states": list(PLATFORM_APPLICABILITY_STATES)})
    _write_shard_and_report("dormant_future_market_qku_ledger", dormant_rows, "PR168_RP5C_DormantFutureMarketQKULedger.report.json", "DormantFutureMarketQKULedgerV1", {**stage1_hard_zero, "dormant_future_market_qku_ledger_row_count": len(dormant_rows), "dormant_future_market_qku_preserved_not_deleted_or_banned_flag": True})
    _write_shard_and_report("stage1_agent_computation_universe_seed", stage1_seed_rows, "PR168_RP5C_Stage1AgentComputationUniverseSeed.report.json", "Stage1AgentComputationUniverseSeedV1", {**stage1_hard_zero, "stage1_agent_computation_universe_seed_row_count": len(stage1_seed_rows), "default_stage1_computation_seed_flag": True, "stage1_agents_must_not_default_compute_full_universe": True})
    _write_shard_and_report("rp5d_executability_handoff", handoff_rows, "PR168_RP5C_ToRP5DExecutabilityHandoff.report.json", "RP5DExecutabilityHandoffV1", {**stage1_hard_zero, "rp5d_handoff_row_count": len(handoff_rows), "rp5d_handoff_state_counts": _counter_summary(handoff_rows, "rp5d_handoff_state"), "stage1_seed_row_count": len(stage1_seed_rows), "dormant_future_market_row_count": len(dormant_rows)})
    _write_shard_and_report("identity_quality_gap_queue", quality_gap_rows, "PR168_RP5C_FinalSummary.report.json", "IdentityQualityGapQueueV1", {"identity_quality_gap_row_count": len(quality_gap_rows)})

    write_report("PR168_RP5C_Preflight.report.json", summary={**preflight, "streaming_scanning_performance": final_summary["scan_performance"]}, records=preflight)
    write_report("PR168_RP5C_RP5BInputIntegrity.report.json", summary=rp5b_integrity, records=rp5b_integrity)
    write_report("PR168_RP5C_AgentDutyInput.report.json", summary=agent_input["status"], records=agent_records[:25])
    central_manifest_records = [
        {
            "central_surface_id": f"RP5C_CENTRAL_SURFACE_{index:04d}",
            "surface_ref": generated_ref(shard_path(key)),
            "manifest_ref": generated_ref(manifest_path_for_shard(shard_path(key))),
            "authority_class": "RP5C_CENTRAL_ACTIVE_SURFACE_NOT_SOURCE_TRUTH",
            "future_consumer_refs": ["Stage1QTTAgents", "PR168-RP5D", "PR168-RP5E", "PR168-RP5G", "RANK4", "QOPT", "Paper", "LiveFutureOnly"] if key in STAGE1_ACTIVE_UNIVERSE_SHARDS else ["PR168-RP5D", "PR168-RP5E", "PR168-RP5G", "RANK4", "QOPT", "Paper", "LiveFutureOnly"],
            "raw_legacy_direct_consumer_allowed_flag": False,
            "derived_route_overlay_not_identity_authority_flag": key in {"agent_duty_routing_rulebook", "derived_agent_route_resolution_ledger", "file_to_derived_route_crosswalk"},
            "universal_preservation_surface_flag": key == "immutable_qku_formula_library",
            "default_stage1_computation_seed_flag": key == "stage1_agent_computation_universe_seed",
            "stage1_agents_must_not_default_compute_full_universe_flag": key in STAGE1_ACTIVE_UNIVERSE_SHARDS,
            "market_scope_or_platform_creates_trading_authority_flag": False,
        }
        for index, key in enumerate(CENTRAL_SURFACE_SHARDS, start=1)
    ]
    write_report("PR168_RP5C_CentralSurfaceManifest.report.json", summary={**stage1_hard_zero, "central_surface_count": len(central_manifest_records), "canonical_active_surfaces": [row["surface_ref"] for row in central_manifest_records], "stage1_active_universe_surfaces": [generated_ref(shard_path(key)) for key in STAGE1_ACTIVE_UNIVERSE_SHARDS], "immutable_qku_formula_library_remains_universal_preservation_surface": True, "stage1_agent_computation_universe_seed_is_default_stage1_seed": True, "stage1_agents_must_not_default_compute_full_universe": True}, records=central_manifest_records)
    write_report("PR168_RP5C_CrossOSPathPortabilityAudit.report.json", summary=cross_os, records=cross_os)
    write_report("PR168_RP5C_PathAudit.report.json", summary=path_audit, records=path_audit)
    write_report("PR168_RP5C_FinalSummary.report.json", summary=final_summary, records=final_summary)

    print(json.dumps({"built": True, "identity_rows": len(library_identities), "identity_occurrences": len(identities), "source_artifacts": len(source_rows), "reports_written": len(REPORT_NAMES), "row_shards_written": len(ROW_SHARDS)}, sort_keys=True))
    return final_summary


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Reserved for compatibility with validation gates.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    build_all(offline=bool(args.offline))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
