#!/usr/bin/env python3
"""Validator for PR168-RP5C immutable QKU/formula library reclaim artifacts."""

from __future__ import annotations

from typing import Any

from tools.pr168_rp5c_config import (
    CENTRAL_SURFACE_SHARDS,
    HARD_ZERO_COUNTERS,
    MARKET_SCOPES,
    ONTOLOGY_CATEGORIES,
    PLATFORM_APPLICABILITY_STATES,
    REPORT_NAMES,
    ROW_SHARDS,
    STAGE1_ACTIVE_UNIVERSE_SHARDS,
    generated_ref,
    manifest_path_for_shard,
    report_path,
    shard_path,
)
from tools.pr168_rp5c_report_writer import read_json, read_jsonl


def _failures() -> list[str]:
    failures: list[str] = []
    for name in REPORT_NAMES:
        if not report_path(name).is_file():
            failures.append(f"MISSING_REPORT:{name}")
    for key in ROW_SHARDS:
        path = shard_path(key)
        manifest = manifest_path_for_shard(path)
        if not path.is_file():
            failures.append(f"MISSING_SHARD:{generated_ref(path)}")
        if not manifest.is_file():
            failures.append(f"MISSING_MANIFEST:{generated_ref(manifest)}")
        if path.is_file() and manifest.is_file():
            rows = read_jsonl(path)
            payload = read_json(manifest)
            if payload.get("row_count") != len(rows):
                failures.append(f"MANIFEST_ROW_COUNT_MISMATCH:{generated_ref(path)}")
            if payload.get("schema_version_name") in {None, ""}:
                failures.append(f"MANIFEST_SCHEMA_MISSING:{generated_ref(manifest)}")
            if payload.get("generated_surface_authority_class") in {None, ""}:
                failures.append(f"MANIFEST_AUTHORITY_CLASS_MISSING:{generated_ref(manifest)}")
            if payload.get("row_count_within_bound_flag") is not True:
                failures.append(f"MANIFEST_ROW_BOUND_EXCEEDED:{generated_ref(path)}")
    if failures:
        return failures

    final_summary = read_json(report_path("PR168_RP5C_FinalSummary.report.json"))
    for field, expected in HARD_ZERO_COUNTERS.items():
        if final_summary.get(field) != expected:
            failures.append(f"HARD_ZERO_NONZERO:{field}:{final_summary.get(field)}")
    if not final_summary.get("all_hard_zero_counters_zero_flag"):
        failures.append("FINAL_HARD_ZERO_FLAG_FALSE")

    input_report = read_json(report_path("PR168_RP5C_Input.report.json"))
    if input_report.get("branch_name") != "pr168-rp5c-immutable-qku-formula-library":
        failures.append("INPUT_BRANCH_MISMATCH")
    source_rows = read_jsonl(shard_path("source_artifact_consumption_ledger"))
    coverage_rows = read_jsonl(shard_path("input_artifact_to_identity_coverage"))
    if len(source_rows) != len(coverage_rows):
        failures.append("SOURCE_COVERAGE_ROW_COUNT_MISMATCH")
    if not source_rows:
        failures.append("SOURCE_LEDGER_EMPTY")
    for row in source_rows:
        if not row.get("source_artifact_row_id"):
            failures.append("SOURCE_ROW_MISSING_ID")
        if not row.get("consumption_status"):
            failures.append(f"SOURCE_ROW_MISSING_STATUS:{row.get('source_file_path')}")
        if row.get("raw_legacy_decision_authority_allowed_flag") is not False:
            failures.append(f"RAW_LEGACY_AUTHORITY_ALLOWED:{row.get('source_file_path')}")
        if not row.get("derived_route_resolution_refs"):
            failures.append(f"SOURCE_ROW_MISSING_ROUTE:{row.get('source_file_path')}")
        if not row.get("validator_refs"):
            failures.append(f"SOURCE_ROW_MISSING_VALIDATOR:{row.get('source_file_path')}")

    identities = read_jsonl(shard_path("immutable_qku_formula_library"))
    qku_rows = read_jsonl(shard_path("immutable_qku_library"))
    formula_rows = read_jsonl(shard_path("immutable_formula_library"))
    if not identities or not qku_rows or not formula_rows:
        failures.append("IMMUTABLE_LIBRARY_EMPTY")
    source_ids = {row["source_artifact_row_id"] for row in source_rows}
    route_refs_seen: set[str] = set()
    for row in identities:
        if row.get("source_artifact_row_id") not in source_ids:
            failures.append(f"IDENTITY_SOURCE_ROW_MISSING:{row.get('identity_row_id')}")
        if row.get("global_ban_flag") is not False:
            failures.append(f"IDENTITY_GLOBAL_BAN_TRUE:{row.get('identity_row_id')}")
        if row.get("mutation_allowed_flag") is not False:
            failures.append(f"IDENTITY_MUTATION_ALLOWED_TRUE:{row.get('identity_row_id')}")
        if row.get("immutable_original_preserved_flag") is not True:
            failures.append(f"IDENTITY_NOT_IMMUTABLE_PRESERVED:{row.get('identity_row_id')}")
        for field in ("family_registry_refs", "market_scope_registry_refs", "ontology_role_registry_refs", "derived_route_resolution_refs", "downstream_pr_refs", "validator_refs"):
            if not row.get(field):
                failures.append(f"IDENTITY_MISSING_{field.upper()}:{row.get('identity_row_id')}")
        if not row.get("rp5d_handoff_state"):
            failures.append(f"IDENTITY_MISSING_RP5D_HANDOFF:{row.get('identity_row_id')}")
        route_refs_seen.update(row.get("derived_route_resolution_refs", []))

    family_rows = read_jsonl(shard_path("qku_formula_family_registry"))
    market_rows = read_jsonl(shard_path("market_scope_family_registry"))
    ontology_rows = read_jsonl(shard_path("ontology_role_registry"))
    if not family_rows:
        failures.append("FAMILY_REGISTRY_EMPTY")
    if {row.get("market_scope") for row in market_rows} != set(MARKET_SCOPES):
        failures.append("MARKET_SCOPE_REGISTRY_INCOMPLETE")
    if {row.get("ontology_category") for row in ontology_rows} != set(ONTOLOGY_CATEGORIES):
        failures.append("ONTOLOGY_REGISTRY_INCOMPLETE")

    groups = read_jsonl(shard_path("agent_responsibility_group_registry"))
    rules = read_jsonl(shard_path("agent_duty_routing_rulebook"))
    routes = read_jsonl(shard_path("derived_agent_route_resolution_ledger"))
    if len(groups) < len(ONTOLOGY_CATEGORIES):
        failures.append("RESPONSIBILITY_GROUPS_INCOMPLETE")
    if len(rules) < len(ONTOLOGY_CATEGORIES):
        failures.append("ROUTING_RULEBOOK_INCOMPLETE")
    for rule in rules:
        if rule.get("manual_per_qku_override_allowed_flag") is not False:
            failures.append(f"MANUAL_PER_QKU_OVERRIDE_ALLOWED:{rule.get('route_rule_id')}")
        if not rule.get("responsibility_group_refs"):
            failures.append(f"RULE_MISSING_GROUP:{rule.get('route_rule_id')}")
    route_ids = {row["route_resolution_id"] for row in routes}
    if route_refs_seen - route_ids:
        failures.append(f"IDENTITY_ROUTE_REF_MISSING:{sorted(route_refs_seen - route_ids)[:5]}")
    if len(routes) != len(identities):
        failures.append("ROUTE_IDENTITY_COUNT_MISMATCH")
    for route in routes:
        if not route.get("route_rule_refs"):
            failures.append(f"ROUTE_MISSING_RULE:{route.get('route_resolution_id')}")
        if not route.get("primary_responsibility_group_refs"):
            failures.append(f"ROUTE_MISSING_GROUP:{route.get('route_resolution_id')}")

    file_crosswalk = read_jsonl(shard_path("file_to_derived_route_crosswalk"))
    if len(file_crosswalk) != len(source_rows):
        failures.append("FILE_CROSSWALK_SOURCE_COUNT_MISMATCH")
    for row in file_crosswalk:
        if not row.get("responsibility_group_refs"):
            failures.append(f"FILE_CROSSWALK_MISSING_GROUP:{row.get('source_file_path')}")
        if not row.get("validator_refs"):
            failures.append(f"FILE_CROSSWALK_MISSING_VALIDATOR:{row.get('source_file_path')}")

    dedupe_rows = read_jsonl(shard_path("identity_deduplication_ledger"))
    extracted_occurrence_count = int(final_summary.get("library_row_counts", {}).get("extracted_identity_occurrence_count", len(identities)))
    if sum(int(row.get("duplicate_member_count", 0)) for row in dedupe_rows) != extracted_occurrence_count:
        failures.append("DEDUP_MEMBER_COUNT_DOES_NOT_COVER_EXTRACTED_OCCURRENCES")
    if any(row.get("global_ban_flag") for row in dedupe_rows):
        failures.append("DEDUP_GLOBAL_BAN_TRUE")

    no_global = read_json(report_path("PR168_RP5C_NoGlobalBanProof.report.json"))
    if no_global.get("global_formula_ban_count") != 0 or no_global.get("global_qku_ban_count") != 0:
        failures.append("NO_GLOBAL_BAN_REPORT_NONZERO")
    no_orphan_identity = read_json(report_path("PR168_RP5C_NoOrphanIdentityProof.report.json"))
    no_orphan_source = read_json(report_path("PR168_RP5C_NoOrphanSourceArtifactProof.report.json"))
    no_orphan_generated = read_json(report_path("PR168_RP5C_NoOrphanGeneratedSurfaceProof.report.json"))
    if no_orphan_identity.get("orphan_identity_count") != 0:
        failures.append("ORPHAN_IDENTITY_NONZERO")
    if no_orphan_source.get("orphan_source_artifact_count") != 0 or no_orphan_source.get("orphan_input_report_count") != 0:
        failures.append("ORPHAN_SOURCE_NONZERO")
    if no_orphan_generated.get("orphan_generated_shard_count") != 0:
        failures.append("ORPHAN_GENERATED_NONZERO")

    handoff_rows = read_jsonl(shard_path("rp5d_executability_handoff"))
    if len(handoff_rows) != len(identities):
        failures.append("RP5D_HANDOFF_IDENTITY_COUNT_MISMATCH")
    if any(row.get("no_executability_tier_decided_flag") is not True for row in handoff_rows):
        failures.append("RP5D_HANDOFF_DECIDES_EXECUTABILITY")

    central = read_json(report_path("PR168_RP5C_CentralSurfaceManifest.report.json"))
    listed = set(central.get("canonical_active_surfaces", []))
    required = {generated_ref(shard_path(key)) for key in CENTRAL_SURFACE_SHARDS}
    if not required.issubset(listed):
        failures.append("CENTRAL_SURFACE_MANIFEST_MISSING_REQUIRED_SURFACE")
    stage1_required = {generated_ref(shard_path(key)) for key in STAGE1_ACTIVE_UNIVERSE_SHARDS}
    if not stage1_required.issubset(listed):
        failures.append("CENTRAL_SURFACE_MANIFEST_MISSING_STAGE1_SURFACE")
    if central.get("stage1_agent_computation_universe_seed_is_default_stage1_seed") is not True:
        failures.append("CENTRAL_SURFACE_MANIFEST_STAGE1_SEED_NOT_DEFAULT")
    if central.get("stage1_agents_must_not_default_compute_full_universe") is not True:
        failures.append("CENTRAL_SURFACE_MANIFEST_FULL_UNIVERSE_DEFAULT_ALLOWED")

    activation_rows = read_jsonl(shard_path("stage1_prediction_market_qku_activation_view"))
    platform_rows = read_jsonl(shard_path("platform_applicability_registry"))
    dormant_rows = read_jsonl(shard_path("dormant_future_market_qku_ledger"))
    seed_rows = read_jsonl(shard_path("stage1_agent_computation_universe_seed"))
    if len(activation_rows) != len(identities):
        failures.append("STAGE1_ACTIVATION_IDENTITY_COUNT_MISMATCH")
    if not seed_rows:
        failures.append("STAGE1_SEED_EMPTY")
    if not dormant_rows:
        failures.append("DORMANT_FUTURE_MARKET_LEDGER_EMPTY")
    activation_ids = {row["stage1_activation_row_id"] for row in activation_rows}
    seed_activation_refs = {ref for row in seed_rows for ref in row.get("stage1_activation_view_refs", [])}
    dormant_activation_refs = {ref for row in dormant_rows for ref in row.get("stage1_activation_view_refs", [])}
    if not seed_activation_refs.issubset(activation_ids):
        failures.append("STAGE1_SEED_NOT_DERIVED_FROM_ACTIVATION_VIEW")
    if not dormant_activation_refs.issubset(activation_ids):
        failures.append("DORMANT_LEDGER_NOT_DERIVED_FROM_ACTIVATION_VIEW")
    if any(row.get("default_compute_from_universal_library_flag") is not False for row in seed_rows):
        failures.append("STAGE1_SEED_DEFAULTS_TO_FULL_UNIVERSE")
    if any(row.get("derived_from_classification_and_routing_surfaces_flag") is not True for row in seed_rows):
        failures.append("STAGE1_SEED_NOT_DERIVED_FROM_CLASSIFICATION_ROUTING")
    for row in seed_rows:
        state = row.get("stage1_classification_state")
        scope = row.get("market_scope")
        if state == "STAGE1_PREDICTION_MARKET_ACTIVE_CANDIDATE" and scope != "prediction_market":
            failures.append(f"STAGE1_ACTIVE_NON_PREDICTION_MARKET:{row.get('identity_row_id')}")
        if state == "STAGE1_PREDICTION_MARKET_SUPPORTING_MARKET_AGNOSTIC" and scope != "market_agnostic":
            failures.append(f"STAGE1_SUPPORTING_NOT_MARKET_AGNOSTIC:{row.get('identity_row_id')}")
        if state not in {"STAGE1_PREDICTION_MARKET_ACTIVE_CANDIDATE", "STAGE1_PREDICTION_MARKET_SUPPORTING_MARKET_AGNOSTIC"}:
            failures.append(f"STAGE1_SEED_INVALID_CLASSIFICATION:{row.get('identity_row_id')}")
    if any(row.get("deleted_flag") is not False for row in dormant_rows):
        failures.append("DORMANT_QKU_DELETED")
    if any(row.get("global_ban_flag") is not False for row in dormant_rows):
        failures.append("DORMANT_QKU_GLOBAL_BANNED")
    if any(row.get("preserved_in_universal_library_flag") is not True for row in dormant_rows):
        failures.append("DORMANT_QKU_NOT_PRESERVED_IN_UNIVERSAL_LIBRARY")
    platform_states = {row.get("platform_applicability_state") for row in platform_rows}
    if set(PLATFORM_APPLICABILITY_STATES) - platform_states:
        failures.append("PLATFORM_APPLICABILITY_REGISTRY_INCOMPLETE")
    required_platform_states = {"KALSHI_APPLICABLE", "POLYMARKET_APPLICABLE", "FORECASTEX_IBKR_APPLICABLE"}
    if not required_platform_states.issubset(platform_states):
        failures.append("PLATFORM_APPLICABILITY_REGISTRY_MISSING_STAGE1_PLATFORMS")

    portability = read_json(report_path("PR168_RP5C_CrossOSPathPortabilityAudit.report.json"))
    for field in ("generated_path_case_collision_count", "absolute_local_path_leak_count", "backslash_only_path_leak_count"):
        if portability.get(field) != 0:
            failures.append(f"PORTABILITY_COUNTER_NONZERO:{field}:{portability.get(field)}")
    path_audit = read_json(report_path("PR168_RP5C_PathAudit.report.json"))
    if path_audit.get("no_deletion_proof", {}).get("deleted_file_count") != 0:
        failures.append("PATH_AUDIT_DELETION_NONZERO")
    return failures


def run_validation() -> dict[str, Any]:
    failures = _failures()
    if failures:
        raise AssertionError("\n".join(failures))
    return {
        "validation": "PR168_RP5C_IMMUTABLE_QKU_FORMULA_LIBRARY_OK",
        "reports_checked": len(REPORT_NAMES),
        "row_shards_checked": len(ROW_SHARDS),
    }
