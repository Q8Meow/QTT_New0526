from __future__ import annotations

from tools.pr168_rp5c_config import STAGE1_ACTIVE_UNIVERSE_SHARDS, generated_ref, shard_path

from ._helpers import final_summary, load_report, load_rows


def test_rp5c_stage1_agent_computation_universe_seed_exists_and_is_not_full_universe_default() -> None:
    identities = load_rows("immutable_qku_formula_library")
    activation = load_rows("stage1_prediction_market_qku_activation_view")
    seed = load_rows("stage1_agent_computation_universe_seed")

    assert seed
    assert len(activation) == len(identities)
    assert len(seed) < len(identities)
    assert all(row["derived_from_stage1_activation_view_flag"] is True for row in seed)
    assert all(row["derived_from_classification_and_routing_surfaces_flag"] is True for row in seed)
    assert all(row["default_stage1_computation_seed_flag"] is True for row in seed)
    assert all(row["default_compute_from_universal_library_flag"] is False for row in seed)


def test_rp5c_stage1_seed_contains_only_prediction_market_or_market_agnostic_supporting_rows() -> None:
    seed = load_rows("stage1_agent_computation_universe_seed")

    for row in seed:
        if row["stage1_classification_state"] == "STAGE1_PREDICTION_MARKET_ACTIVE_CANDIDATE":
            assert row["market_scope"] == "prediction_market"
        elif row["stage1_classification_state"] == "STAGE1_PREDICTION_MARKET_SUPPORTING_MARKET_AGNOSTIC":
            assert row["market_scope"] == "market_agnostic"
        else:
            raise AssertionError(row["stage1_classification_state"])


def test_rp5c_future_market_qkus_are_preserved_dormant_not_deleted_or_banned() -> None:
    dormant = load_rows("dormant_future_market_qku_ledger")

    assert dormant
    assert all(row["preserved_in_universal_library_flag"] is True for row in dormant)
    assert all(row["dormant_preserved_flag"] is True for row in dormant)
    assert all(row["deleted_flag"] is False for row in dormant)
    assert all(row["global_ban_flag"] is False for row in dormant)
    assert all(row["dormant_does_not_mean_deleted_banned_or_unimportant_flag"] is True for row in dormant)


def test_rp5c_platform_applicability_registry_declares_stage1_platform_states() -> None:
    platform_rows = load_rows("platform_applicability_registry")
    states = {row["platform_applicability_state"] for row in platform_rows}

    assert {"KALSHI_APPLICABLE", "POLYMARKET_APPLICABLE", "FORECASTEX_IBKR_APPLICABLE"}.issubset(states)
    assert "THREE_PLATFORM_COMMON" in states
    assert all(row["market_scope_or_platform_creates_trading_authority_flag"] is False for row in platform_rows)


def test_rp5c_central_manifest_lists_stage1_active_universe_surfaces() -> None:
    report = load_report("PR168_RP5C_CentralSurfaceManifest.report.json")
    listed = set(report["canonical_active_surfaces"])
    required = {generated_ref(shard_path(key)) for key in STAGE1_ACTIVE_UNIVERSE_SHARDS}

    assert required.issubset(listed)
    assert set(report["stage1_active_universe_surfaces"]) == required
    assert report["immutable_qku_formula_library_remains_universal_preservation_surface"] is True
    assert report["stage1_agent_computation_universe_seed_is_default_stage1_seed"] is True
    assert report["stage1_agents_must_not_default_compute_full_universe"] is True


def test_rp5c_stage1_hard_zero_counters_remain_zero() -> None:
    summary = final_summary()

    assert summary["stage1_default_full_universe_compute_route_count"] == 0
    assert summary["non_prediction_market_qku_stage1_active_count"] == 0
    assert summary["dormant_qku_deleted_count"] == 0
    assert summary["dormant_qku_global_ban_count"] == 0
    assert summary["stage1_active_universe_summary"]["stage1_agents_must_not_default_compute_full_universe"] is True
