#!/usr/bin/env python3
"""Validator for PR168-RP5C immutable QKU/formula library reclaim artifacts."""

from __future__ import annotations

import re
from typing import Any

from tools.pr168_rp5c_config import (
    AGENT_ACCESS_POLICY_VERSION,
    APPLICABILITY_MATRIX_VERSION,
    AUTHORITATIVE_CENTRAL_LAYER_SHARDS,
    CENTRAL_SURFACE_SHARDS,
    HARD_ZERO_COUNTERS,
    LIBRARY_VERSION,
    MARKET_APPLICABILITY_MODES,
    MARKET_SCOPES,
    MASTER_PLAN_MARKET_FAMILIES,
    ONTOLOGY_CATEGORIES,
    PLATFORM_APPLICABILITY_STATES,
    REPORT_NAMES,
    ROW_SHARDS,
    STAGE1_ACTIVE_UNIVERSE_SHARDS,
    STAGE1_ENABLED_MARKET_FAMILIES,
    STAGE1_ENABLED_PLATFORMS,
    STAGE1_PROFILE_ID,
    STAGE_ACCESS_MODES,
    STAGE_PROFILE_VERSION,
    generated_ref,
    manifest_path_for_shard,
    report_path,
    shard_path,
)
from tools.pr168_rp5c_library_reader import LibraryVersionMismatchError, load_library, query_ids, resolve_stage_agent_universe
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
    identity_by_id = {row["identity_row_id"]: row for row in identities}
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
    authoritative_refs = {generated_ref(shard_path(key)) for key in AUTHORITATIVE_CENTRAL_LAYER_SHARDS}
    if set(central.get("authoritative_central_layer_surfaces", [])) != authoritative_refs:
        failures.append("CENTRAL_SURFACE_MANIFEST_AUTHORITATIVE_LAYER_MISMATCH")
    if central.get("authoritative_central_layer_count") != 4 or central.get("only_four_authoritative_central_layers_flag") is not True:
        failures.append("CENTRAL_SURFACE_MANIFEST_NOT_EXACTLY_FOUR_AUTHORITATIVE_LAYERS")
    if central.get("independent_full_library_copy_count") != 0:
        failures.append("CENTRAL_SURFACE_MANIFEST_HAS_FULL_LIBRARY_COPY")
    authoritative_record_refs = {
        row.get("surface_ref")
        for row in central.get("records", [])
        if row.get("authoritative_configuration_data_layer_flag") is True
    }
    if authoritative_record_refs != authoritative_refs:
        failures.append("CENTRAL_SURFACE_RECORD_AUTHORITATIVE_LAYER_MISMATCH")
    stage1_required = {generated_ref(shard_path(key)) for key in STAGE1_ACTIVE_UNIVERSE_SHARDS}
    if not stage1_required.issubset(listed):
        failures.append("CENTRAL_SURFACE_MANIFEST_MISSING_STAGE1_SURFACE")
    if central.get("stage1_agent_computation_universe_seed_is_default_stage1_seed") is not True:
        failures.append("CENTRAL_SURFACE_MANIFEST_STAGE1_SEED_NOT_DEFAULT")
    if central.get("stage1_agents_must_not_default_compute_full_universe") is not True:
        failures.append("CENTRAL_SURFACE_MANIFEST_FULL_UNIVERSE_DEFAULT_ALLOWED")

    matrix_rows = read_jsonl(shard_path("qku_market_applicability_matrix"))
    stage_profiles = read_jsonl(shard_path("market_stage_activation_profile_registry"))
    access_policies = read_jsonl(shard_path("agent_qku_access_policy_registry"))
    stage_views = read_jsonl(shard_path("stage_computation_universe_view"))
    agent_views = read_jsonl(shard_path("agent_computation_universe_view"))
    resolver_rows = read_jsonl(shard_path("stage_agent_qku_universe_resolver"))
    receipt_rows = read_jsonl(shard_path("library_query_receipts"))
    if len(matrix_rows) != len(identities):
        failures.append("MARKET_APPLICABILITY_MATRIX_IDENTITY_COUNT_MISMATCH")
    valid_market_families = set(MASTER_PLAN_MARKET_FAMILIES)
    for row in matrix_rows:
        if row.get("applicability_mode") not in set(MARKET_APPLICABILITY_MODES):
            failures.append(f"MARKET_APPLICABILITY_INVALID_MODE:{row.get('identity_row_id')}")
        if set(row.get("market_family_refs", [])) - valid_market_families:
            failures.append(f"MARKET_APPLICABILITY_INVALID_FAMILY:{row.get('identity_row_id')}")
        if row.get("applicability_mode") == "CROSS_MARKET_SHARED":
            if row.get("shared_cross_market_support_flag") is not True:
                failures.append(f"CROSS_MARKET_SHARED_FLAG_FALSE:{row.get('identity_row_id')}")
            if row.get("specific_market_family_refs"):
                failures.append(f"CROSS_MARKET_SHARED_HAS_SPECIFIC_MARKET_REFS:{row.get('identity_row_id')}")
        if row.get("applicability_mode") == "UNKNOWN_NEEDS_REVIEW" and "CROSS_MARKET_SHARED" in row.get("market_family_refs", []):
            failures.append(f"UNKNOWN_ROW_SILENTLY_CROSS_MARKET:{row.get('identity_row_id')}")
        if row.get("applicability_mode") == "CROSS_MARKET_SHARED" and row.get("stage_access_mode_by_profile", {}).get(STAGE1_PROFILE_ID) == "DEFAULT_COMPUTE":
            failures.append(f"CROSS_MARKET_SHARED_DEFAULT_COMPUTE:{row.get('identity_row_id')}")
        if "SECURITIES_FINANCING_AND_REPO" in row.get("market_family_refs", []):
            identity = identity_by_id.get(row["identity_row_id"], {})
            evidence = " ".join(
                str(value)
                for value in [
                    identity.get("qku_id"),
                    identity.get("formula_id"),
                    identity.get("formula_family"),
                    identity.get("qku_family"),
                    identity.get("source_file_path"),
                    *identity.get("blocker_codes", []),
                ]
            )
            repo_financing_evidence = re.search(
                r"\b("
                r"securities[_ -]?financing|"
                r"secured[_ -]?financing|"
                r"repo[_ -]?(financing|rate|market|trade|haircut|special|gc|collateral)|"
                r"repurchase[_ -]?agreement|"
                r"general[_ -]?collateral"
                r")\b",
                evidence,
                flags=re.IGNORECASE,
            )
            if not repo_financing_evidence:
                failures.append(f"REPO_FINANCING_WITHOUT_REPO_EVIDENCE:{row.get('identity_row_id')}")
        if row.get("market_scope_or_platform_creates_trading_authority_flag") is not False:
            failures.append(f"MARKET_APPLICABILITY_TRADING_AUTHORITY:{row.get('identity_row_id')}")
    if not any(row.get("applicability_mode") == "CROSS_MARKET_SHARED" for row in matrix_rows):
        failures.append("MARKET_APPLICABILITY_NO_CROSS_MARKET_SHARED_ROWS")
    if not any("PREDICTION_MARKETS" in row.get("market_family_refs", []) for row in matrix_rows):
        failures.append("MARKET_APPLICABILITY_NO_PREDICTION_MARKET_ROWS")

    stage_profile = next((row for row in stage_profiles if row.get("profile_id") == STAGE1_PROFILE_ID), None)
    if stage_profile is None:
        failures.append("STAGE_PROFILE_STAGE1_MISSING")
    else:
        if stage_profile.get("enabled_market_family_refs") != list(STAGE1_ENABLED_MARKET_FAMILIES):
            failures.append("STAGE_PROFILE_MARKET_FAMILIES_MISMATCH")
        if stage_profile.get("enabled_platform_refs") != list(STAGE1_ENABLED_PLATFORMS):
            failures.append("STAGE_PROFILE_PLATFORM_REFS_MISMATCH")
        if stage_profile.get("include_cross_market_shared") is not True:
            failures.append("STAGE_PROFILE_DOES_NOT_INCLUDE_CROSS_MARKET_SHARED")
        if stage_profile.get("include_shared_cross_market_support") is not True:
            failures.append("STAGE_PROFILE_SHARED_SUPPORT_ALIAS_MISSING")
        if set(stage_profile.get("access_modes", [])) != set(STAGE_ACCESS_MODES):
            failures.append("STAGE_PROFILE_ACCESS_MODES_MISMATCH")
        if stage_profile.get("stage_profile_version") != STAGE_PROFILE_VERSION:
            failures.append("STAGE_PROFILE_VERSION_MISMATCH")
    represented_profile_families = {
        row.get("enabled_market_family_refs", [None])[0]
        for row in stage_profiles
        if row.get("enabled_market_family_refs")
    }
    if set(MASTER_PLAN_MARKET_FAMILIES) - represented_profile_families:
        failures.append("STAGE_PROFILE_MARKET_FAMILY_TEMPLATES_INCOMPLETE")
    for row in stage_profiles:
        if row.get("profile_id") != STAGE1_PROFILE_ID and row.get("profile_state") != "DISABLED_TEMPLATE_NEEDS_OWNER_STAGE_ASSIGNMENT":
            failures.append(f"FUTURE_STAGE_PROFILE_NOT_DISABLED_TEMPLATE:{row.get('profile_id')}")

    if not access_policies:
        failures.append("AGENT_ACCESS_POLICY_EMPTY")
    policies_by_agent = {row.get("agent_id"): row for row in access_policies}
    for row in access_policies:
        if row.get("agent_access_policy_version") != AGENT_ACCESS_POLICY_VERSION:
            failures.append(f"AGENT_ACCESS_POLICY_VERSION_MISMATCH:{row.get('agent_id')}")
        if row.get("mutable_per_qku_ownership_authority_flag") is not False:
            failures.append(f"AGENT_ACCESS_POLICY_MUTABLE_OWNERSHIP:{row.get('agent_id')}")
        if row.get("default_full_universe_access_flag") is not False:
            failures.append(f"AGENT_ACCESS_POLICY_FULL_UNIVERSE:{row.get('agent_id')}")
        for field in ("allowed_ontology_categories", "allowed_formula_family_refs", "allowed_qku_family_refs", "allowed_market_family_refs", "allowed_platform_refs", "allowed_access_modes", "source_duty_refs"):
            if not row.get(field):
                failures.append(f"AGENT_ACCESS_POLICY_MISSING_{field.upper()}:{row.get('agent_id')}")
        if not {"docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json", "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json"}.issubset(set(row.get("source_duty_refs", []))):
            failures.append(f"AGENT_ACCESS_POLICY_MISSING_PR165_D2_SOURCE:{row.get('agent_id')}")
    expected_agent_categories = {
        "research_agent": {"signal_probability", "calibration", "market_implied_probability", "regime_scenario"},
        "connector_venue_readiness_future_consumer": {"tca_cost", "fill_queue_liquidity", "latency_staleness", "exit_timing"},
        "risk_manager_agent": {"portfolio_risk", "capacity_crowding", "regime_scenario", "governance_source_risk"},
        "quantum_optimizer_agent": {"quantum_objective_constraint", "classical_fallback"},
    }
    for agent_id, expected_categories in expected_agent_categories.items():
        actual_categories = set(policies_by_agent.get(agent_id, {}).get("allowed_ontology_categories", []))
        if not expected_categories.issubset(actual_categories):
            failures.append(f"AGENT_ACCESS_POLICY_CATEGORY_GAP:{agent_id}")

    if {row.get("platform_id") for row in stage_views} != set(STAGE1_ENABLED_PLATFORMS):
        failures.append("STAGE_COMPUTATION_VIEW_PLATFORM_MISMATCH")
    cross_shared_ids = {row["identity_row_id"] for row in matrix_rows if row.get("applicability_mode") == "CROSS_MARKET_SHARED"}
    prediction_ids = {row["identity_row_id"] for row in matrix_rows if "PREDICTION_MARKETS" in row.get("market_family_refs", []) and row.get("applicability_mode") == "MARKET_SPECIFIC"}
    for row in stage_views:
        if row.get("library_version") != LIBRARY_VERSION or row.get("applicability_matrix_version") != APPLICABILITY_MATRIX_VERSION or row.get("stage_profile_version") != STAGE_PROFILE_VERSION or row.get("agent_access_policy_version") != AGENT_ACCESS_POLICY_VERSION:
            failures.append(f"STAGE_VIEW_VERSION_MISMATCH:{row.get('stage_computation_universe_view_id')}")
        if row.get("contains_canonical_formula_objects_flag") is not False or row.get("contains_canonical_qku_objects_flag") is not False:
            failures.append(f"STAGE_VIEW_DUPLICATES_CANONICAL_OBJECTS:{row.get('stage_computation_universe_view_id')}")
        default_refs = set(row.get("default_compute_identity_refs", []))
        on_demand_refs = set(row.get("available_on_demand_identity_refs", []))
        if not default_refs.issubset(prediction_ids):
            failures.append(f"STAGE_VIEW_DEFAULT_NOT_PREDICTION_ONLY:{row.get('platform_id')}")
        if not cross_shared_ids.issubset(on_demand_refs):
            failures.append(f"STAGE_VIEW_MISSING_CROSS_MARKET_SHARED_ON_DEMAND:{row.get('platform_id')}")
        if cross_shared_ids & default_refs:
            failures.append(f"STAGE_VIEW_CROSS_MARKET_SHARED_DEFAULT_COMPUTE:{row.get('platform_id')}")
    for row in agent_views:
        if row.get("contains_canonical_formula_objects_flag") is not False or row.get("contains_canonical_qku_objects_flag") is not False:
            failures.append(f"AGENT_VIEW_DUPLICATES_CANONICAL_OBJECTS:{row.get('agent_computation_universe_view_id')}")
        if len(row.get("identity_refs", [])) >= len(identities):
            failures.append(f"AGENT_VIEW_FULL_UNIVERSE_DEFAULT:{row.get('agent_id')}:{row.get('platform_id')}")
    if len(resolver_rows) != len(access_policies) * len(STAGE1_ENABLED_PLATFORMS):
        failures.append("STAGE_AGENT_RESOLVER_POLICY_PLATFORM_COUNT_MISMATCH")
    for row in resolver_rows:
        if row.get("library_version") != LIBRARY_VERSION or row.get("applicability_matrix_version") != APPLICABILITY_MATRIX_VERSION or row.get("stage_profile_version") != STAGE_PROFILE_VERSION or row.get("agent_access_policy_version") != AGENT_ACCESS_POLICY_VERSION:
            failures.append(f"STAGE_AGENT_RESOLVER_VERSION_MISMATCH:{row.get('stage_agent_resolver_row_id')}")
        if row.get("contains_canonical_formula_objects_flag") is not False or row.get("contains_canonical_qku_objects_flag") is not False:
            failures.append(f"STAGE_AGENT_RESOLVER_DUPLICATES_CANONICAL_OBJECTS:{row.get('stage_agent_resolver_row_id')}")
        if len(row.get("resolved_identity_refs", [])) >= len(identities):
            failures.append(f"STAGE_AGENT_RESOLVER_FULL_UNIVERSE:{row.get('agent_id')}:{row.get('platform_id')}")
    if not receipt_rows:
        failures.append("LIBRARY_QUERY_RECEIPTS_EMPTY")
    for row in receipt_rows:
        if not row.get("query_receipt_id") or "result_identity_refs" not in row:
            failures.append(f"LIBRARY_QUERY_RECEIPT_INCOMPLETE:{row.get('query_receipt_id')}")

    machine_report = read_json(report_path("PR168_RP5C_MachineConsumableLibraryAccess.report.json"))
    if machine_report.get("machine_library_reader_ref") != "tools/pr168_rp5c_library_reader.py":
        failures.append("MACHINE_ACCESS_REPORT_MISSING_READER")
    if machine_report.get("authoritative_central_layer_count") != 4:
        failures.append("MACHINE_ACCESS_REPORT_AUTHORITATIVE_LAYER_COUNT_MISMATCH")
    agent_contract = read_json(report_path("PR168_RP5C_AgentQKUAccessContract.report.json"))
    if agent_contract.get("mutable_per_qku_ownership_in_identity_rows_flag") is not False:
        failures.append("AGENT_ACCESS_CONTRACT_MUTABLE_PER_QKU_OWNERSHIP")
    resolver_report = read_json(report_path("PR168_RP5C_StageAgentUniverseResolutionProof.report.json"))
    if resolver_report.get("version_mismatch_fail_closed_flag") is not True:
        failures.append("RESOLVER_REPORT_VERSION_MISMATCH_NOT_FAIL_CLOSED")
    vs1_report = read_json(report_path("PR168_RP5C_ToVS1TradingIntelligenceHandoff.report.json"))
    if vs1_report.get("no_trade_simulation_or_live_authority_flag") is not True or vs1_report.get("no_source_truth_authority_flag") is not True:
        failures.append("VS1_HANDOFF_FORBIDDEN_AUTHORITY")
    reader_source = (report_path("PR168_RP5C_FinalSummary.report.json").parents[3] / "tools" / "pr168_rp5c_library_reader.py").read_text(encoding="utf-8")
    if 'for identity in sorted(data["immutable_qku_formula_library"]' in reader_source:
        failures.append("LIBRARY_READER_QUERY_SCANS_FULL_UNIVERSE")

    reader_library = load_library()
    if reader_library.get("raw_legacy_surface_paths_read"):
        failures.append("LIBRARY_READER_READS_RAW_LEGACY_SURFACES")
    try:
        load_library(expected_versions={"library_version": "WRONG_VERSION"})
    except LibraryVersionMismatchError:
        pass
    else:
        failures.append("LIBRARY_READER_VERSION_MISMATCH_DID_NOT_FAIL_CLOSED")
    first_policy = access_policies[0]["agent_id"] if access_policies else None
    if first_policy:
        reader_resolution = resolve_stage_agent_universe(STAGE1_PROFILE_ID, first_policy, STAGE1_ENABLED_PLATFORMS[0], reader_library)
        if reader_resolution["resolved_identity_count"] >= len(identities):
            failures.append("LIBRARY_READER_RESOLVES_FULL_UNIVERSE")
        queried_default = query_ids(STAGE1_PROFILE_ID, first_policy, STAGE1_ENABLED_PLATFORMS[0], access_mode="DEFAULT_COMPUTE", library=reader_library)
        if len(queried_default) >= len(identities):
            failures.append("LIBRARY_READER_QUERY_DEFAULT_FULL_UNIVERSE")

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
