from __future__ import annotations

import re

import pytest

from tools.pr168_rp5c_config import (
    HARD_ZERO_COUNTERS,
    MASTER_PLAN_MARKET_FAMILIES,
    STAGE1_ENABLED_PLATFORMS,
    STAGE1_PROFILE_ID,
)
from tools.pr168_rp5c_library_reader import (
    LibraryVersionMismatchError,
    get_formula,
    get_qku,
    list_formulas,
    list_qkus,
    load_library,
    load_rows as reader_load_rows,
    query_ids,
    resolve_stage_agent_universe,
)

from ._helpers import final_summary, load_report, load_rows


def _matrix_by_identity() -> dict[str, dict]:
    return {row["identity_row_id"]: row for row in load_rows("qku_market_applicability_matrix")}


def test_rp5c_reader_loads_central_surfaces_without_raw_rp5a_rp5b_legacy_inputs() -> None:
    library = load_library()

    assert library["immutable_qku_formula_library"]
    assert library["qku_market_applicability_matrix"]
    assert library["raw_legacy_surface_paths_read"] == []
    assert all(path.startswith("docs/master_plan/generated/rp5c/") for path in library["loaded_surface_paths"])
    assert not any("PR168_RP5A" in path or "PR168_RP5B" in path for path in library["loaded_surface_paths"])


def test_rp5c_reader_gets_qkus_and_formulas_by_id() -> None:
    library = load_library()
    qku = list_qkus(library)[0]
    formula = list_formulas(library)[0]

    assert get_qku(qku["qku_id"], library)["identity_row_id"] == qku["identity_row_id"]
    assert get_formula(formula["formula_id"], library)["identity_row_id"] == formula["identity_row_id"]
    assert reader_load_rows([qku["identity_row_id"], formula["identity_row_id"]], library)


def test_rp5c_query_filters_stage1_by_exact_prediction_market_family() -> None:
    library = load_library()
    matrix = _matrix_by_identity()
    result = query_ids(
        STAGE1_PROFILE_ID,
        "research_agent",
        "KALSHI",
        access_mode="DEFAULT_COMPUTE",
        library=library,
    )

    assert result
    assert all("PREDICTION_MARKETS" in matrix[identity_id]["market_family_refs"] for identity_id in result)
    assert all(matrix[identity_id]["applicability_mode"] == "MARKET_SPECIFIC" for identity_id in result)
    assert all("KALSHI" in matrix[identity_id]["platform_refs"] for identity_id in result)
    assert set(MASTER_PLAN_MARKET_FAMILIES).issuperset(
        family for identity_id in result for family in matrix[identity_id]["market_family_refs"]
    )


def test_rp5c_repo_financing_family_requires_repo_specific_evidence() -> None:
    matrix = _matrix_by_identity()
    identities = {row["identity_row_id"]: row for row in load_rows("immutable_qku_formula_library")}
    repo_rows = [row for row in matrix.values() if "SECURITIES_FINANCING_AND_REPO" in row["market_family_refs"]]
    stage_profiles = load_rows("market_stage_activation_profile_registry")
    profile_market_families = {
        family for row in stage_profiles for family in row.get("enabled_market_family_refs", [])
    }
    repo_financing_evidence = re.compile(
        r"\b("
        r"securities[_ -]?financing|"
        r"secured[_ -]?financing|"
        r"repo[_ -]?(financing|rate|market|trade|haircut|special|gc|collateral)|"
        r"repurchase[_ -]?agreement|"
        r"general[_ -]?collateral"
        r")\b",
        flags=re.IGNORECASE,
    )

    assert "SECURITIES_FINANCING_AND_REPO" in profile_market_families
    for row in repo_rows:
        identity = identities[row["identity_row_id"]]
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
        assert repo_financing_evidence.search(evidence)


def test_rp5c_market_scope_quality_audit_records_repair_distribution() -> None:
    report = load_report("PR168_RP5C_MarketScopeClassificationQualityAudit.report.json")
    matrix_rows = load_rows("qku_market_applicability_matrix")
    counts = {}
    for row in matrix_rows:
        counts[row["applicability_mode"]] = counts.get(row["applicability_mode"], 0) + 1

    assert report["prior_suspicious_repo_financing_assignment_count"] == 9382
    assert report["prior_unknown_needs_review_count"] == 267
    assert report["repo_financing_default_used_without_repo_specific_evidence_count"] == 0
    assert report["generic_future_market_scope_row_count"] == 0
    assert report["valid_cross_market_support_unavailable_to_stage1_count"] == 0
    assert report["stage1_default_full_universe_compute_route_count"] == 0
    assert report["repaired_cross_market_shared_count"] == counts["CROSS_MARKET_SHARED"] == 1471
    assert report["repaired_market_specific_count"] == counts["MARKET_SPECIFIC"] == 530
    assert report["repaired_unknown_needs_review_count"] == counts["UNKNOWN_NEEDS_REVIEW"] == 8188
    assert report["qku_identity_deleted_count"] == 0
    assert report["formula_identity_deleted_count"] == 0
    assert report["global_qku_ban_count"] == 0
    assert report["global_formula_ban_count"] == 0


def test_rp5c_market_family_reclassification_ledger_records_evidence_rules() -> None:
    rows = load_rows("market_family_reclassification_ledger")
    row_types = {row["ledger_row_type"] for row in rows}

    assert {
        "PRIOR_SUSPICIOUS_DISTRIBUTION",
        "REPO_FINANCING_BROAD_DEFAULT_REMOVED",
        "REUSABLE_SUPPORT_TO_CROSS_MARKET_SHARED",
        "PREDICTION_MARKET_SPECIFIC_PRESERVED",
        "UNRESOLVED_TO_UNKNOWN_NEEDS_REVIEW",
    }.issubset(row_types)
    repo_rule = next(row for row in rows if row["ledger_row_type"] == "REPO_FINANCING_BROAD_DEFAULT_REMOVED")
    assert repo_rule["before_repo_financing_assignment_count"] == 9382
    assert repo_rule["after_unsupported_repo_financing_assignment_count"] == 0


def test_rp5c_compact_market_pool_views_match_applicability_matrix() -> None:
    matrix_rows = load_rows("qku_market_applicability_matrix")
    shared_rows = [row for row in matrix_rows if row["applicability_mode"] == "CROSS_MARKET_SHARED"]
    specific_rows = [row for row in matrix_rows if row["applicability_mode"] == "MARKET_SPECIFIC"]
    shared_pool = load_rows("shared_cross_market_support_pool")
    market_specific_pools = load_rows("market_specific_qku_pool_registry")

    assert len(shared_pool) == 1
    assert shared_pool[0]["identity_row_count"] == len(shared_rows) == 1471
    assert shared_pool[0]["full_library_copy_flag"] is False
    assert shared_pool[0]["contains_canonical_formula_objects_flag"] is False
    assert shared_pool[0]["contains_canonical_qku_objects_flag"] is False
    assert set(shared_pool[0]["identity_refs"]) == {row["identity_row_id"] for row in shared_rows}
    assert len(market_specific_pools) == len(MASTER_PLAN_MARKET_FAMILIES)
    assert sum(row["identity_row_count"] for row in market_specific_pools) == len(specific_rows) == 530
    assert all(row["full_library_copy_flag"] is False for row in market_specific_pools)
    assert all(row["contains_canonical_formula_objects_flag"] is False for row in market_specific_pools)
    assert all(row["contains_canonical_qku_objects_flag"] is False for row in market_specific_pools)


def test_rp5c_market_agnostic_shared_support_is_not_specific_market_family_assignment() -> None:
    matrix_rows = load_rows("qku_market_applicability_matrix")
    shared_rows = [row for row in matrix_rows if row["applicability_mode"] == "CROSS_MARKET_SHARED"]

    assert shared_rows
    assert all(row["shared_cross_market_support_flag"] is True for row in shared_rows)
    assert all(row["specific_market_family_refs"] == [] for row in shared_rows)
    assert all("SECURITIES_FINANCING_AND_REPO" not in row["market_family_refs"] for row in shared_rows)


def test_rp5c_stage_profile_registry_has_disabled_templates_for_all_canonical_market_families() -> None:
    profiles = load_rows("market_stage_activation_profile_registry")
    represented = {
        row["enabled_market_family_refs"][0]
        for row in profiles
        if row.get("enabled_market_family_refs")
    }
    disabled_templates = [row for row in profiles if row.get("profile_state") == "DISABLED_TEMPLATE_NEEDS_OWNER_STAGE_ASSIGNMENT"]

    assert set(MASTER_PLAN_MARKET_FAMILIES).issubset(represented)
    assert disabled_templates
    assert all(row["no_owner_approved_stage_number_claimed_flag"] is True for row in disabled_templates)


def test_rp5c_cross_market_shared_is_available_to_stage1_but_not_default_computed() -> None:
    matrix = _matrix_by_identity()
    cross_shared_ids = {identity_id for identity_id, row in matrix.items() if row["applicability_mode"] == "CROSS_MARKET_SHARED"}
    stage_views = load_rows("stage_computation_universe_view")

    assert cross_shared_ids
    for view in stage_views:
        default_ids = set(view["default_compute_identity_refs"])
        on_demand_ids = set(view["available_on_demand_identity_refs"])
        assert cross_shared_ids.issubset(on_demand_ids)
        assert default_ids.isdisjoint(cross_shared_ids)
        assert len(default_ids) < len(matrix)


def test_rp5c_stage1_resolves_prediction_markets_plus_cross_market_shared_ids() -> None:
    matrix = _matrix_by_identity()
    stage_views = load_rows("stage_computation_universe_view")

    for view in stage_views:
        platform_id = view["platform_id"]
        expected = {
            identity_id
            for identity_id, row in matrix.items()
            if platform_id in row["platform_refs"]
            and (
                row["applicability_mode"] == "CROSS_MARKET_SHARED"
                or ("PREDICTION_MARKETS" in row["market_family_refs"] and row["applicability_mode"] == "MARKET_SPECIFIC")
            )
        }
        resolved = set(view["default_compute_identity_refs"]) | set(view["available_on_demand_identity_refs"])
        assert resolved == expected


def test_rp5c_stage1_platform_filtering_works_for_all_enabled_platforms() -> None:
    library = load_library()
    matrix = _matrix_by_identity()

    for platform_id in STAGE1_ENABLED_PLATFORMS:
        result = query_ids(STAGE1_PROFILE_ID, "research_agent", platform_id, library=library)
        assert result
        assert all(platform_id in matrix[identity_id]["platform_refs"] for identity_id in result)


def test_rp5c_agent_access_is_pr165_d2_policy_derived_and_not_per_qku_ownership() -> None:
    policies = load_rows("agent_qku_access_policy_registry")

    assert policies
    for policy in policies:
        assert policy["mutable_per_qku_ownership_authority_flag"] is False
        assert policy["default_full_universe_access_flag"] is False
        assert "docs/master_plan/generated/PR165_D2_AgentRosterDiscoveryAudit.report.json" in policy["source_duty_refs"]
        assert "docs/master_plan/generated/PR165_D2_AgentDutySourceCrosswalk.report.json" in policy["source_duty_refs"]


def test_rp5c_agent_policy_category_coverage_matches_central_duties() -> None:
    policies = {row["agent_id"]: row for row in load_rows("agent_qku_access_policy_registry")}

    assert {"signal_probability", "calibration", "market_implied_probability", "regime_scenario"}.issubset(
        set(policies["research_agent"]["allowed_ontology_categories"])
    )
    assert {"tca_cost", "fill_queue_liquidity", "latency_staleness", "exit_timing"}.issubset(
        set(policies["connector_venue_readiness_future_consumer"]["allowed_ontology_categories"])
    )
    assert {"portfolio_risk", "capacity_crowding", "regime_scenario", "governance_source_risk"}.issubset(
        set(policies["risk_manager_agent"]["allowed_ontology_categories"])
    )
    assert {"quantum_objective_constraint", "classical_fallback"}.issubset(
        set(policies["quantum_optimizer_agent"]["allowed_ontology_categories"])
    )
    assert set(policies["governance_agent"]["allowed_ontology_categories"]) == {
        "signal_probability",
        "calibration",
        "market_implied_probability",
        "tca_cost",
        "fill_queue_liquidity",
        "latency_staleness",
        "capacity_crowding",
        "portfolio_risk",
        "regime_scenario",
        "exit_timing",
        "quantum_objective_constraint",
        "classical_fallback",
        "governance_source_risk",
        "unknown_needs_review",
    }


def test_rp5c_execution_like_agent_does_not_receive_unrelated_research_only_families() -> None:
    library = load_library()
    identities = {row["identity_row_id"]: row for row in load_rows("immutable_qku_formula_library")}
    connector_policy = next(row for row in load_rows("agent_qku_access_policy_registry") if row["agent_id"] == "connector_venue_readiness_future_consumer")
    result = query_ids(STAGE1_PROFILE_ID, connector_policy["agent_id"], "KALSHI", library=library)

    assert "signal_probability" not in connector_policy["allowed_ontology_categories"]
    assert "regime_scenario" not in connector_policy["allowed_ontology_categories"]
    assert result
    assert all(identities[identity_id]["ontology_category"] not in {"signal_probability", "regime_scenario"} for identity_id in result)


def test_rp5c_no_agent_receives_full_universal_library_by_default() -> None:
    library = load_library()
    universal_count = len(library["immutable_qku_formula_library"])

    for policy in library["agent_qku_access_policy_registry"]:
        for platform_id in STAGE1_ENABLED_PLATFORMS:
            receipt = resolve_stage_agent_universe(STAGE1_PROFILE_ID, policy["agent_id"], platform_id, library)
            assert receipt["resolved_identity_count"] < universal_count
            assert receipt["default_compute_count"] < universal_count


def test_rp5c_reader_queries_precomputed_views_not_universal_scan() -> None:
    library = load_library()
    baseline = query_ids(STAGE1_PROFILE_ID, "research_agent", "KALSHI", library=library)

    assert baseline
    library["immutable_qku_formula_library"] = []
    assert query_ids(STAGE1_PROFILE_ID, "research_agent", "KALSHI", library=library) == baseline
    assert reader_load_rows(baseline[:3], library)


def test_rp5c_derived_views_are_id_views_not_canonical_object_copies() -> None:
    for view in [*load_rows("stage_computation_universe_view"), *load_rows("agent_computation_universe_view")]:
        assert view["contains_canonical_formula_objects_flag"] is False
        assert view["contains_canonical_qku_objects_flag"] is False
        assert "qku_id" not in view
        assert "formula_id" not in view
        assert "formula_expression_ref" not in view


def test_rp5c_reader_version_mismatch_fails_closed() -> None:
    with pytest.raises(LibraryVersionMismatchError):
        load_library(expected_versions={"library_version": "not-the-rp5c-library-version"})


def test_rp5c_unknown_rows_are_not_silently_classified_cross_market_shared() -> None:
    matrix_rows = load_rows("qku_market_applicability_matrix")
    unknown_rows = [row for row in matrix_rows if row["applicability_mode"] == "UNKNOWN_NEEDS_REVIEW"]

    assert unknown_rows
    assert all(row["applicability_mode"] != "CROSS_MARKET_SHARED" for row in unknown_rows)
    assert all("NEEDS_MARKET_FAMILY_CLASSIFICATION" in row["blocker_codes"] or row["blocker_codes"] for row in unknown_rows)


def test_rp5c_machine_access_preserves_no_delete_no_mutate_no_global_ban_and_hard_zeros() -> None:
    summary = final_summary()
    no_global = load_report("PR168_RP5C_NoGlobalBanProof.report.json")
    identities = load_rows("immutable_qku_formula_library")

    assert all(row["global_ban_flag"] is False for row in identities)
    assert all(row["mutation_allowed_flag"] is False for row in identities)
    assert all(row["immutable_original_preserved_flag"] is True for row in identities)
    assert no_global["global_formula_ban_count"] == 0
    assert no_global["global_qku_ban_count"] == 0
    for field, expected in HARD_ZERO_COUNTERS.items():
        assert summary[field] == expected
