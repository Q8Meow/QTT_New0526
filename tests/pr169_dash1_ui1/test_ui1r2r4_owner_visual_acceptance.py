from __future__ import annotations

from pathlib import Path

from tests.pr169_dash1_ui1.conftest import boot_data, ui_doc, ui_text, walk
from tools.build_pr169_dash1_owner_dashboard_ui import OWNER_SETTINGS_STORAGE_KEY


def r2r4_bundle() -> dict:
    return ui_doc("ui1r2r4_owner_semantic_bundle.generated.json")


def central_manifest() -> dict:
    return ui_doc("../ui1_r2_r4/centralization_manifest.generated.json")


def field_map() -> dict[str, dict]:
    return {row["field_id"]: row for row in r2r4_bundle()["field_semantics"]}


def education_map() -> dict[str, dict]:
    return {row["education_id"]: row for row in r2r4_bundle()["education_catalog"]}


def test_ui1r2r4_visual_acceptance_controls_inputs_and_settings() -> None:
    bundle = r2r4_bundle()
    text = ui_text()
    states = {row["state_id"] for row in bundle["interaction_states"]}
    assert {"input_required", "review_required", "optional_input", "provider_pending", "high_confirmation", "success"} <= states
    assert "data-field-initial-state" in text
    assert "updateWorkbenchFieldStates" in text
    assert "input_required" in text and "review_required" in text
    assert "data-settings-other-field" in text
    assert "width: 20px" in text and "min-height: 44px" in text
    fields = field_map()
    assert fields["plain_english_detail"]["interaction_state"] == "input_required"
    assert fields["max_budget"]["interaction_state"] in {"input_required", "optional_input"}
    for field_id in ("custom_market_family", "custom_event_category", "custom_event", "custom_venue", "custom_source_family", "custom_route_type"):
        row = fields[field_id]
        assert row["source_category"] == "candidate_owner_custom"
        assert row["authority"] == "local_preview_guardrail"
        assert row["source_truth"] is False
        assert row["connector_semantics"] is False
        assert row["replay_paper_evidence"] is False
        assert row["live_readiness"] is False
        assert row["order_authority"] is False


def test_ui1r2r4_qtt_guide_chat_and_plain_english_intents() -> None:
    bundle = r2r4_bundle()
    text = ui_text()
    intents = {row["intent_id"]: row for row in bundle["chat_qtt_guide_intents"]}
    for intent in (
        "trade_check",
        "research_link",
        "formula_qku_search",
        "agent_disagreement_risk",
        "no_trade_explanation",
        "replay_paper_preview",
        "workbench_prefill",
        "evidence_missing",
        "agent_operations_status",
        "workflow_queue_status",
        "online_research_provider_pending",
        "source_candidate_extraction_preview",
        "formula_qku_extraction_preview",
        "unknown_clarification",
    ):
        assert intent in intents
        assert intents[intent]["runtime_side_effect_allowed"] is False
    for phrase in (
        "Can QTT check this market and find the best trade?",
        "Research this article and tell me if it creates a prediction-market edge.",
        "Ask the QKU agents to compare the best formula stacks for this event.",
        "Why did no-trade win here?",
        "What variables would make this trade pass replay and paper?",
        "Show me which agent disagrees and why.",
    ):
        assert phrase in "\n".join(str(value) for value in walk(bundle))
    assert 'data-qtt-guide-composer="shared-chat-action-state"' in text
    assert 'data-qtt-guide-send="shared-chat-submit"' in text
    assert "localIntentResponse" in text
    assert "UNKNOWN_OWNER_REQUEST_NEEDS_CLARIFICATION" in text
    assert "No online search, live LLM, real agent task, connector read, replay, paper, live execution, venue submit, or Execution Router release happened." in text


def test_ui1r2r4_centralized_education_distinct_actions_and_disabled_policy() -> None:
    bundle = r2r4_bundle()
    text = ui_text()
    education = education_map()
    required = {
        "education.explain",
        "education.learn",
        "education.why",
        "education.qku_formula_routes",
        "education.tca_cost",
        "education.chart_drilldown",
        "education.disabled_action",
        "education.workbench_field_help",
        "education.workflow_queue",
        "education.receipts",
        "education.risk_quantum",
    }
    assert required <= set(education)
    summaries = {education[row]["plain_english_summary"] for row in required}
    assert len(summaries) == len(required)
    assert "centralEducationEntry" in text
    assert "data-central-education-id" in text
    assert "data-action-applicability" in text
    assert "data-disabled-action-education" in text
    assert "Technical Details" in text
    assert bundle["thin_module_import_graph"]["renderer_imports_thin_feature_modules"] is False


def test_ui1r2r4_agent_operations_workflow_queue_and_receipt_preview() -> None:
    bundle = r2r4_bundle()
    text = ui_text()
    assert bundle["agent_operations_projection"]
    assert bundle["workflow_queue_projection"]
    assert bundle["receipt_preview_projection"]
    for row in bundle["agent_operations_projection"]:
        assert row["agent_status"] == "provider-pending, not running"
        assert row["started_at"] == "provider-pending"
        assert row["trust_score"] == "provider-pending"
        assert row["runtime_side_effect_allowed"] is False
    for row in bundle["workflow_queue_projection"]:
        assert row["responsible_agent"]
        assert row["current_stage"]
        assert row["latest_receipt"] == "provider-pending"
        assert row["runtime_side_effect_allowed"] is False
    receipt_classes = {row["receipt_class"] for row in bundle["receipt_preview_projection"]}
    assert {
        "RuntimeTaskReceiptV1",
        "AgentDecisionReceiptV1",
        "MemoryUpdateReceiptV1",
        "PaperOrderIntentV1",
        "PaperFillSimulationReceiptV1",
        "NoTradeDecisionReceiptV1",
        "RiskGateReceiptV1",
        "TCAMetricReceiptV1",
        "OwnerActionReceiptV1",
    } <= receipt_classes
    assert 'data-agent-operations-shell="OwnerAgentOperationsProjectionV1"' in text
    assert 'data-workflow-queue-shell="OwnerWorkflowQueueStateV1"' in text
    assert 'data-receipt-preview-shell="OwnerReceiptPreviewStateV1"' in text
    assert "No fake timestamps" in text


def test_ui1r2r4_online_search_provider_pending_and_source_candidate_boundaries() -> None:
    bundle = r2r4_bundle()
    previews = bundle["online_research_provider_pending_preview"]
    assert previews
    for row in previews:
        assert row["candidate_lane"] in {"research/provisional", "formula_qku/provisional"}
        assert row["later_provider_stage"] in {"LLM2_PROVIDER_PENDING", "LLM2_FORMULA_QKU_EXTRACTION_PROVIDER_PENDING"}
        assert "online search" in row["will_not_happen_now"]
        assert row["source_truth_created"] is False
        assert row["order_authority_created"] is False
    text = "\n".join(str(value) for value in walk(bundle))
    assert "fake URLs" in text
    assert "candidate/provisional" in text


def test_ui1r2r4_owner_command_authority_without_execution_router_bypass() -> None:
    bundle = r2r4_bundle()
    actions = {row["preview_action_family"]: row for row in bundle["owner_command_preview_actions"]}
    for action in (
        "OwnerTradeIntentPreview",
        "OwnerTradeCheckRequestPreview",
        "OwnerReplayPaperRequestPreview",
        "OwnerLiveCanaryReviewRequestPreview",
        "OwnerExecutionRouterSubmitRequestPreview",
        "OwnerKillSwitchRequestPreview",
        "OwnerRollbackRequestPreview",
        "OwnerPauseNewTradesRequestPreview",
        "OwnerVetoRouteRequestPreview",
        "OwnerResearchSubmissionPreview",
    ):
        assert action in actions
        assert actions[action]["routes_through"] == "OwnerActionRegistry + OwnerNextStepRouter"
        assert actions[action]["runtime_side_effect_allowed"] is False
        assert actions[action]["order_authority_created"] is False
    all_text = "\n".join(str(value) for value in walk(bundle))
    assert "no direct venue submit" in all_text
    assert "No direct order authority" in all_text


def test_ui1r2r4_qku_formula_agent_route_gap_no_orphan_projection() -> None:
    bundle = r2r4_bundle()
    rows = bundle["qku_formula_agent_route_gap_projection"]
    assert rows
    for row in rows:
        assert row["owner_visible_id"]
        assert row["upstream_ref"]
        assert row["downstream_consumer_ref"]
        assert row["qku_refs_or_gap"]
        assert row["formula_refs_or_gap"]
        assert row["responsible_agent_refs_or_PR165_D2_gap"]
        assert row["runtime_side_effect_allowed"] is False
        assert row["source_truth_created"] is False
        assert row["order_authority_created"] is False
    assert "TradePlanCandidateV1" in "\n".join(str(value) for value in walk(bundle))
    assert "QKUs/formulas remain immutable" in "\n".join(str(value) for value in walk(bundle))


def test_ui1r2r4_ultra_centralized_semantic_bundle_no_scatter() -> None:
    bundle = r2r4_bundle()
    assert bundle["central_bundle_id"] == "OwnerUXSemanticBundleV1"
    assert bundle["source_of_truth_precedence"] == [
        "canonical dashboard surface registry/current equivalent",
        "OwnerDashboardStateV1/current equivalent",
        "OwnerActionRegistry/current equivalent",
        "central owner UX semantic bundle/current equivalent",
        "generated projections under owned prefix",
        "renderers / tests / Playwright",
    ]
    anti_scatter = bundle["anti_scatter_discovery_policy"]
    for key, value in anti_scatter.items():
        if key.startswith("component_local_"):
            assert value is False
    assert bundle["thin_module_import_graph"]["renderer_consumes"] == "central generated OwnerDashboardStateV1 + ui1r2r4 semantic bundle projection only"


def test_ui1r2r4_owned_prefix_currentization_and_stable_artifacts() -> None:
    bundle = r2r4_bundle()
    assert bundle["owned_generated_prefix"] == "docs/master_plan/generated/pr169_dash1/ui1_r2_r4/"
    assert central_manifest()["manifest_id"] == "UI1R2R4_CENTRALIZATION_MANIFEST"
    for path in (
        Path("docs/master_plan/generated/pr169_dash1/ui/ui1r2r4_owner_semantic_bundle.generated.json"),
        Path("docs/master_plan/generated/pr169_dash1/ui1_r2_r4/centralization_manifest.generated.json"),
    ):
        assert path.exists()
        assert "future" not in path.name
        assert not path.name.endswith("_hint.jsonl")
    all_paths = [str(path) for path in Path("docs/master_plan/generated/pr169_dash1").rglob("*") if path.is_file()]
    assert not any("AtomicRows.bundle.sha256" in path for path in all_paths)
    assert not any("freeze" in path.lower() or "global_digest" in path.lower() for path in all_paths)


def test_ui1r2r4_no_runtime_authority_and_no_test_sprawl() -> None:
    boundary = r2r4_bundle()["no_runtime_authority"]
    for key, value in boundary.items():
        assert value is True
    all_values = "\n".join(str(value) for value in walk(boot_data()))
    assert "guaranteed positive profit" not in all_values
    assert "POST /orders" not in ui_text()
    assert "fetch(" not in ui_text()


def test_ui1r2r4_current_equivalent_mapping_and_single_storage_key() -> None:
    bundle = r2r4_bundle()
    concepts = {row["conceptual_system"] for row in bundle["phase0_current_equivalent_mapping"]}
    assert len(concepts) >= 20
    assert "central owner UX semantic bundle" in concepts
    assert bundle["single_settings_key"] == OWNER_SETTINGS_STORAGE_KEY
    assert OWNER_SETTINGS_STORAGE_KEY in ui_text()
    assert "localStorage.setItem(THEME_STORAGE_KEY" in ui_text()
    assert bundle["legacy_preference_key_migration_only"]["no_new_component_local_keys"] is True


def test_ui1r2r4_thin_module_imports_and_antiscatter_discovery() -> None:
    bundle = r2r4_bundle()
    graph = bundle["thin_module_import_graph"]
    assert graph["thin_modules_added"] is False
    assert graph["renderer_imports_thin_feature_modules"] is False
    policy = bundle["anti_scatter_discovery_policy"]
    assert policy["allowed_central_files"]
    for key, value in policy.items():
        if key.startswith("component_local_"):
            assert value is False


def test_ui1r2r4_generated_subprefix_or_shared_artifact_justification() -> None:
    bundle = r2r4_bundle()
    manifest_groups = central_manifest()["semantic_groups"]
    assert {row["semantic_group"] for row in manifest_groups}
    for row in manifest_groups:
        assert row["central_owner_file_or_current_equivalent"]
        assert row["builder_consumer"] == "tools/build_pr169_dash1_owner_dashboard_ui.py"
        assert row["validator_consumer"] == "tools/validate_pr169_dash1_owner_dashboard_ui.py"
        assert row["runtime_side_effect_allowed"] is False
    shared = bundle["broad_pr169_ui_generated_artifact_justification"]
    assert shared
    assert all(row["central_builder_owns_it"] == "tools/build_pr169_dash1_owner_dashboard_ui.py" for row in shared)
