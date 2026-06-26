from __future__ import annotations

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
