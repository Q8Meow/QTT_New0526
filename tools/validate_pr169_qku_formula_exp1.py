#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.catalog import EXPECTED_FAMILY_COUNTS
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.objects import CORE_OBJECTS, DISTINCT_OBJECTS, INTEGRATED_OBJECTS
from src.qtt.stage1_prediction_markets.pr169_qku_formula_exp1.policy import GENERIC_TOOL_OPERATIONS, PERMANENT_QTT_LAWS, SHORT_HORIZON_FIELDS, STABLE_VALIDATOR_RULE_IDS, STRATEGY_TEMPLATES
from tools.build_pr169_qku_formula_exp1 import build


EXPECTED_FILES = {
    "manifest.json", "acceptance.report.json", "policy.json", "requirements.jsonl",
    "objects.jsonl", "bindings.jsonl", "integration.jsonl", "strategies.jsonl",
    "validator_rules.jsonl", "tool_manifest.jsonl", "reading.jsonl", "sources.jsonl",
    "family_j_receipts.jsonl",
}


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _import_callable(ref: str) -> Any:
    module, name = ref.split(":", 1)
    return getattr(importlib.import_module(module), name)


def validate_stable_rules(rows: list[dict[str, Any]], failures: list[str]) -> None:
    actual = {row.get("rule_id") for row in rows}
    if actual != set(STABLE_VALIDATOR_RULE_IDS): failures.append("stable validator rule IDs are incomplete")
    for row in rows:
        if row.get("pass_fail_state") != "PASS" or not row.get("validator_function_ref") or not row.get("test_ref"):
            failures.append(f"validator rule is not executable: {row.get('rule_id')}")


def validate(repo_root: Path, artifact_dir: Path) -> list[str]:
    failures: list[str] = []
    if not artifact_dir.is_dir(): return [f"missing artifact directory: {artifact_dir}"]
    actual_files = {path.name for path in artifact_dir.iterdir() if path.is_file()}
    if actual_files != EXPECTED_FILES: failures.append(f"owned generated file set differs: {sorted(actual_files ^ EXPECTED_FILES)}")
    manifest=_json(artifact_dir/"manifest.json"); acceptance=_json(artifact_dir/"acceptance.report.json"); policy=_json(artifact_dir/"policy.json")
    requirements=_jsonl(artifact_dir/"requirements.jsonl"); objects=_jsonl(artifact_dir/"objects.jsonl"); bindings=_jsonl(artifact_dir/"bindings.jsonl"); integration=_jsonl(artifact_dir/"integration.jsonl")
    strategies=_jsonl(artifact_dir/"strategies.jsonl"); rules=_jsonl(artifact_dir/"validator_rules.jsonl"); tools=_jsonl(artifact_dir/"tool_manifest.jsonl"); j_receipts=_jsonl(artifact_dir/"family_j_receipts.jsonl")
    if len(requirements)!=213 or len({row["card_id"] for row in requirements})!=213: failures.append("213 unique formula cards required")
    family_counts={family:sum(row["formula_family"]==family for row in requirements) for family in EXPECTED_FAMILY_COUNTS}
    if family_counts!=EXPECTED_FAMILY_COUNTS: failures.append(f"formula family counts differ: {family_counts}")
    if len(objects)!=233 or {row["object_name"] for row in objects}!=set(DISTINCT_OBJECTS): failures.append("233 object dispositions required")
    if len(CORE_OBJECTS)!=59 or len(INTEGRATED_OBJECTS)!=191 or len(set(CORE_OBJECTS)&set(INTEGRATED_OBJECTS))!=17: failures.append("object inventory cardinalities differ")
    if len(bindings)!=213 or len(integration)!=213: failures.append("every formula requires binding and integration edge")
    if len(strategies)!=len(STRATEGY_TEMPLATES)!=38: failures.append("38 strategy templates required")
    if any(not row.get("formula_DAG_refs") or not row.get("no_trade_comparator_ref") or not row.get("PR165_D2_responsible_agent_route") for row in strategies): failures.append("strategy formula DAG/agent/no-trade route missing")
    validate_stable_rules(rules,failures)
    if tuple(policy.get("permanent_laws",()))!=PERMANENT_QTT_LAWS: failures.append("permanent QTT law block differs")
    if tuple(policy.get("short_horizon_fields",()))!=SHORT_HORIZON_FIELDS or len(SHORT_HORIZON_FIELDS)!=47: failures.append("47 short-horizon fields required")
    if {row["operation_id"] for row in tools}!=set(GENERIC_TOOL_OPERATIONS) or len(tools)!=5: failures.append("five generic formula/QKU operations required")
    for row in requirements:
        try: callable_obj=_import_callable(row["callable_ref"])
        except Exception as exc: failures.append(f"callable import failed for {row['card_id']}: {exc}"); continue
        if not callable(callable_obj): failures.append(f"callable ref is not callable: {row['card_id']}")
        if not row.get("no_order_authority") or not row.get("no_connector_read"): failures.append(f"authority boundary missing: {row['card_id']}")
    if len(j_receipts)!=8 or {row["family_j_card_id"] for row in j_receipts}!={f"J{i:02d}" for i in range(1,9)}: failures.append("all eight Family-J receipts required")
    for row in j_receipts:
        if row.get("terminal_state")!="VALIDATED_ROUTED_UNACKNOWLEDGED" or not row.get("method_specific_output_ref") or not row.get("qku_binding_ids") or not row.get("AGENT_ORCH_task_ref"): failures.append(f"Family-J closure missing: {row.get('family_j_card_id')}")
    zero_keys=(
        "J_family_unresolved_count","J_family_metadata_only_count","J_family_route_only_count","J_family_method_inapplicable_count",
        "formula_unresolved_applicable_count","duplicate_canonical_formula_id_count","duplicate_semantic_identity_count","parallel_callable_authority_count",
        "READINESS_missing_count","PRETRADE_missing_binding_count","AGENT_ORCH_missing_applicable_route_count","SVC_missing_applicable_projection_count",
        "false_delivery_claim_count","orphan_formula_count","orphan_QKU_count","orphan_artifact_count","orphan_value_count","orphan_agent_task_count","orphan_projection_count","orphan_handoff_count",
        "external_conversation_attachment_dependency_count","preparation_only_local_path_dependency_count","raw_JSONL_agent_scan_count","full_library_default_agent_access_count",
        "formula_callable_connector_read_count","shadow_or_live_candidate_authority_count","implicit_unit_or_basis_conversion_count","formula_dependency_DAG_cycle_count",
        "shared_generated_unrelated_churn_count","shared_generated_format_or_order_only_churn_count","proactive_branch_allowlist_change_count",
        "advanced_assurance_procedure_method_inapplicable_count","advanced_assurance_procedure_metadata_only_count","advanced_assurance_procedure_route_only_count","advanced_assurance_procedure_unresolved_count",
        "live_order_authority_count","quantum_backend_execution_count",
    )
    for key in zero_keys:
        if acceptance.get(key)!=0: failures.append(f"acceptance zero invariant failed: {key}={acceptance.get(key)!r}")
    if acceptance.get("formula_card_total_required_count")!=213 or acceptance.get("J_family_executable_count")!=8: failures.append("acceptance formula counts differ")
    if manifest.get("manual_generated_edit_count")!=0 or manifest.get("parallel_registry_count")!=0: failures.append("manual edit or parallel registry invariant failed")
    if any(row.get("delivery_state")=="DELIVERED_TO_DESTINATION" and not row.get("destination_ack_ref") for row in integration): failures.append("false destination delivery claim")
    with tempfile.TemporaryDirectory(prefix="pr169_formula_exp1_") as temporary:
        compare=Path(temporary); build(repo_root,compare)
        for filename in EXPECTED_FILES:
            if (artifact_dir/filename).read_bytes()!=(compare/filename).read_bytes(): failures.append(f"generated artifact is not deterministic: {filename}")
    return failures


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--repo-root",default="."); parser.add_argument("--artifact-dir",default="docs/master_plan/generated/pr169_qku_formula_exp1"); parser.add_argument("--timeout-ms",default="3600000")
    args=parser.parse_args(); root=Path(args.repo_root).resolve(); artifacts=Path(args.artifact_dir); artifacts=artifacts if artifacts.is_absolute() else root/artifacts
    failures=validate(root,artifacts)
    print(json.dumps({"status":"FAIL" if failures else "PASS","failure_count":len(failures),"failures":failures},sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__": raise SystemExit(main())
