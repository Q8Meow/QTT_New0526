from __future__ import annotations

import json
from pathlib import Path

from src.qtt.service import pr169_svc1_resolvers as resolvers
from tools import build_pr169_svc1 as builder
from tools import validate_pr169_svc1 as validator


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "docs/master_plan/generated/pr169_svc1"


def _jsonl(name: str) -> list[dict]:
    with (ARTIFACT_DIR / name).open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _json(name: str) -> dict:
    return json.loads((ARTIFACT_DIR / name).read_text(encoding="utf-8"))


def _assert_false(rows: list[dict], *fields: str) -> None:
    for row in rows:
        for field in fields:
            if field in row:
                assert row[field] is False, f"{field} widened in {row.get('registry_row_id')}"


def test_pr169_svc1_registry_projection_integrity():
    validator.validate(REPO_ROOT, ARTIFACT_DIR)
    registry = _jsonl("service_registry.jsonl")
    manifest = _json("service_manifest.json")
    assert registry
    assert manifest["canonical_registry_ref"] == builder.REGISTRY_REF
    assert manifest["baseline_consumed"]["PR268_PRETRADE1_commit"] == "fc0f72088aeb70f7a3aa835dd5e86561a5a89d02"
    assert any(
        row["current_equivalent_path_or_absent"] == builder.PRETRADE_EXEC_LADDER_EQUIVALENT_REF
        for row in manifest["phase0_mapping"]
    )
    assert not (ARTIFACT_DIR / "pretrade_execution_ladder_handoff.generated.jsonl").exists()
    assert all(row["generated_from"] == builder.REGISTRY_REF for row in registry)
    assert all(row["manual_edit_allowed"] is False for row in registry)
    assert all(row["orphan_status"] in {"NOT_ORPHAN", "SCOPED_GAP_ROUTED"} for row in registry)
    assert all(row["lifecycle_state"] for row in registry)
    assert all(row["timing_state"] for row in registry)
    assert all(row["provider_state"] for row in registry)
    assert all(row["freshness_state"] for row in registry)
    assert all(row["authority_state"] for row in registry)

    registry_ids = {row["registry_row_id"] for row in registry}
    for artifact in builder.JSONL_ARTIFACTS:
        rows = _jsonl(artifact)
        assert rows, artifact
        assert "_hint" not in artifact
        assert "future" not in artifact.lower()
        for row in rows:
            assert row["registry_row_id"] in registry_ids
            assert row["source_registry_row_id"] in registry_ids
            assert row["generated_from"] == builder.REGISTRY_REF


def test_pr169_svc1_action_event_receipt_authority_boundaries():
    actions = _jsonl("owner_action_requests.generated.jsonl")
    next_steps = _jsonl("owner_next_step_routes.generated.jsonl")
    events = _jsonl("event_stream_contracts.generated.jsonl")
    receipts = _jsonl("owner_action_receipts.generated.jsonl")
    assert set(builder.ACTION_REQUEST_CLASSES) <= {row["action_code"] for row in actions}
    assert set(builder.EVENT_CLASSES) <= {row["event_class"] for row in events}
    assert any(row["next_step_route_id"] == "LIVE_ORDER_SUBMIT_DISABLED" for row in next_steps)
    for row in actions:
        assert row["owner_trading_command_authority_allowed"] is True
        assert row["action_request_natural_key"]
        assert row["dedupe_policy_ref_or_gap"]
        assert row["required_confirmation_class"]
        assert row["risk_class"]
        if row["eligible_state"].startswith("ELIGIBLE"):
            assert row["eligibility_proof_ref_or_gap"]
        else:
            assert row["denied_reason_ref_or_gap"]
        assert row["what_will_not_happen_now"]
    assert all(row["event_sample_state"] == "CONTRACT_SAMPLE_NOT_RUNTIME_EVENT" for row in events)
    assert all(row["receipt_contract_only"] is True for row in receipts)
    _assert_false(
        actions + next_steps + events + receipts,
        "direct_venue_submit_authority_created",
        "execution_router_release_authority_created",
        "order_submission_created",
        "replay_execution_created",
        "paper_execution_created",
        "shadow_execution_created",
        "live_execution_created",
        "connector_read_created",
        "private_cash_account_read_created",
        "runtime_llm_call_created",
        "runtime_agent_execution_created",
        "fake_receipt_created",
        "profit_claim_created",
        "qtt_sha_authority_created",
        "atomicrows_hash_authority_created",
    )


def test_pr169_svc1_institutional_quantum_agent_llm_routes():
    ranking = _jsonl("execution_adjusted_ranking_views.generated.jsonl")
    tca = _jsonl("tca_decomposition_views.generated.jsonl")
    memory = _jsonl("regime_memory_prior_views.generated.jsonl")
    quantum = _jsonl("quantum_structural_readiness_views.generated.jsonl")
    qku = _jsonl("qku_formula_compute_route_views.generated.jsonl")
    agent_ops = _jsonl("agent_operations_views.generated.jsonl")
    team = _jsonl("team_workflow_queue_views.generated.jsonl")
    assert ranking and tca and memory and quantum and qku and agent_ops and team
    assert all(row["ranking_is_view_only"] is True for row in ranking)
    assert all(row["ranking_recomputed_by_svc1"] is False for row in ranking)
    assert all(row["tca_is_explicit_not_vague_score"] is True for row in tca)
    assert all(row["memory_is_prior_not_proof"] is True for row in memory)
    for row in quantum:
        assert row["objective_function_route_ref_or_gap"]
        assert row["variable_encoding_route_ref_or_gap"]
        assert row["constraint_route_ref_or_gap"]
        assert row["penalty_scaling_route_ref_or_gap"]
        assert row["classical_exact_or_heuristic_comparator_ref_or_gap"]
        assert row["fallback_route_ref_or_gap"]
    for row in qku + agent_ops + team:
        assert row["responsible_agent_role_refs"]
        assert row["agent_roster_discovery_audit_ref_or_gap"]
        assert row["agent_duty_source_crosswalk_ref_or_gap"]
        assert row["llm_grounding_route_ref_or_gap"]
    _assert_false(quantum + qku + agent_ops + team, "quantum_backend_execution_created", "quantum_advantage_claim_created", "runtime_llm_call_created", "runtime_agent_execution_created", "order_authority_created")


def test_pr169_svc1_surface_chat_mobile_expansion_contracts():
    intents = _jsonl("owner_plain_english_intent_routes.generated.jsonl")
    surface = _jsonl("cross_surface_state_contract.generated.jsonl")
    mobile = _jsonl("mobile_app_shell_contract_views.generated.jsonl")
    expansion = _jsonl("market_venue_expansion_socket_routes.generated.jsonl")
    ladder = _jsonl("execution_ladder_stage_views.generated.jsonl")
    charts = _jsonl("professional_provider_pending_frames.generated.jsonl")
    required_intents = {intent for intent, _request in builder.PLAIN_ENGLISH_INTENT_ROUTES}
    assert required_intents <= {row["intent_class"] for row in intents}
    assert all(row["parser_contract_ref"].startswith("NaturalLanguageOwnerIntentParserContractV1") for row in intents)
    assert all(row["source_truth_created"] is False for row in intents)
    for row in surface + mobile:
        assert row["shared_state_id_state"]
        assert row["shared_action_id_state"]
        assert row["shared_widget_id_state"]
        assert row["shared_chart_id_state"]
        assert row["shared_chat_id_state"]
        assert row["shared_receipt_id_state"]
        assert row["no_mobile_only_fork_proof"]
        assert row["no_telegram_second_governance_plane_proof"]
    assert all(row["fake_pnl_cash_fill_live_position_data_created"] is False for row in charts)
    assert all(row["no_scattered_market_logic_proof"] for row in expansion)
    assert all(row["upstream_current_equivalent_ref"] == builder.PRETRADE_EXEC_LADDER_EQUIVALENT_REF for row in ladder)
    _assert_false(surface + mobile + expansion + ladder, "service_worker_runtime_created", "push_notification_runtime_created", "native_mobile_runtime_created", "connector_read_created", "order_execution_created")


def test_pr169_svc1_resolver_contracts():
    api = resolvers.OwnerDashboardAPI(ARTIFACT_DIR)
    manifest = api.load_service_manifest()
    snapshots = api.list_read_model_snapshots()
    candidate_id = snapshots[0]["candidate_id"]
    assert manifest["canonical_registry_ref"] == builder.REGISTRY_REF
    assert api.get_snapshot(snapshots[0]["snapshot_id"])["snapshot_id"] == snapshots[0]["snapshot_id"]
    assert api.list_event_contracts()
    assert api.list_action_requests()
    assert api.get_action_eligibility("REQUEST_PRETRADE_RECHECK")["action_code"] == "REQUEST_PRETRADE_RECHECK"
    assert api.get_action_denied_reason("REQUEST_EXECUTION_ROUTER_SUBMIT_REVIEW")["denied_reason_ref_or_gap"] == "LIVE_ORDER_SUBMIT_DISABLED"
    assert api.get_pretrade_view(candidate_id)["candidate_id"] == candidate_id
    assert api.get_tca_view(candidate_id)["tca_is_explicit_not_vague_score"] is True
    assert api.get_quantum_readiness_view(candidate_id)["quantum_backend_execution_created"] is False
    assert api.get_agent_operations_view()
    assert api.get_team_workflow_queue()
    assert api.get_owner_next_step_route("REQUEST_PRETRADE_RECHECK")["runtime_side_effect_allowed"] is False
    assert api.get_trade_workbench_route(candidate_id)["execution_router_boundary_route_ref_or_gap"]
    assert api.get_execution_ladder(candidate_id)["upstream_current_equivalent_ref"] == builder.PRETRADE_EXEC_LADDER_EQUIVALENT_REF
    parsed = api.parse_owner_plain_english_intent_preview("Why did no-trade win here?")
    assert parsed["intent_class"] == "NO_TRADE_EXPLANATION_REQUEST"
    assert parsed["parser_runtime"] == "DETERMINISTIC_ROUTE_PREVIEW_NO_LLM_CALL"
