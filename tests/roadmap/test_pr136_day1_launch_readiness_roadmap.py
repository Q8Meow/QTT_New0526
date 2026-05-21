from __future__ import annotations

import json
from pathlib import Path

from src.qtt.stage1_prediction_markets.launch_readiness import (
    day1_launch_readiness_roadmap_policy as policy,
)
from tools import validate_pr136_day1_launch_readiness_roadmap as validator
from tools import validate_pr136_roadmap_policy_literal_drift as drift


ROOT = Path(__file__).resolve().parents[2]


def _report(name: str) -> dict:
    return json.loads((ROOT / "docs" / "master_plan" / "generated" / name).read_text())


def _roadmap_generated(name: str) -> dict:
    return json.loads((ROOT / "docs" / "roadmap" / "generated" / name).read_text())


def _domain_map() -> dict:
    return _report("PR136MasterPlanCoverageToReadinessDomainMap.report.json")


def _taxonomy() -> dict:
    return _report("PR136ReadinessDomainTaxonomy.report.json")


def _sequence() -> dict:
    return _report("PR136PostPR135RoadmapSequence.report.json")


def _classification_records() -> list[dict]:
    return _report("PR136ProvisionalPR137ToPR164Classification.report.json")[
        "classification_records"
    ]


def _json_key_paths(value, path: str = "$") -> list[tuple[str, str]]:
    paths: list[tuple[str, str]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            next_path = f"{path}.{key}"
            paths.append((key, next_path))
            paths.extend(_json_key_paths(item, next_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            paths.extend(_json_key_paths(item, f"{path}[{index}]"))
    return paths


def _pr136_text_artifact_paths() -> tuple[str, ...]:
    return (
        "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md",
    )


def _pr136_json_artifact_paths() -> tuple[str, ...]:
    return (
        *policy.PR136_REPORT_PATHS,
        *policy.PR136_ROADMAP_RECEIPT_PATHS,
        *policy.PR136_SCHEMA_PATHS,
        "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_Index_v1_0.json",
    )


def test_pr136_validator_emits_marker(capsys):
    assert validator.main(["--repo-root", str(ROOT)]) == 0
    assert capsys.readouterr().out.strip() == policy.VALIDATOR_MARKER


def test_pr135_currentization_required():
    receipt = _report("PR135GitHubAuditCurrentization.report.json")
    assert receipt["currentized_in_identity_roster"] is True
    assert validator._validate_pr135_currentization(ROOT) == []


def test_owner_verified_pr135_fields_required():
    receipt = _report("PR135GitHubAuditCurrentization.report.json")
    assert receipt["mergeCommit_full"] == "c0aa723a5c46d86ba93a007d5b50d7f64438b03d"
    assert receipt["mergedAt"] == "2026-05-21T04:31:43Z"
    assert receipt["repo_pr_url"].endswith("/pull/135")


def test_same_number_inference_forbidden():
    assert _report("PR136RouteTriage.report.json")["same_number_inference_used"] is False
    assert _report("PR136Day1LaunchReadinessRoadmap.report.json")[
        "planning_authority_only"
    ] is True


def test_read_receipt_required_files_present():
    receipt = _report("PR136ReadReceipt.report.json")
    assert receipt["missing_files"] == []
    assert receipt["read_before_editing_confirmed"] is True


def test_path_decision_present():
    assert _report("PR136PathDecision.report.json")["safe_canonical_path_inferred"] is True


def test_policy_manifest_present():
    manifest = _report("PR136PolicyManifest.report.json")
    assert manifest["validator_marker"] == policy.VALIDATOR_MARKER
    assert manifest["centralized_block_code_doctrine"] is True


def test_policy_schema_defs_match_policy_module():
    schema = json.loads((ROOT / policy.POLICY_SCHEMA_DEFS_PATH).read_text())
    defs = schema["$defs"]
    assert defs["classification_label"]["enum"] == list(policy.CLASSIFICATION_LABELS)
    assert defs["block_code_ref"]["enum"] == list(policy.BLOCK_CODE_REFS)


def test_policy_literal_drift_blocks(tmp_path):
    duplicate = tmp_path / "bad_pr136_policy.py"
    duplicate.write_text(
        'VALUES = ["CONFIRMED", "SPLIT_OR_REPLACED"]\n',
        encoding="utf-8",
    )
    failures = drift.validate_policy_literal_drift(
        repo_root=ROOT, extra_paths=(duplicate,), write_report=False
    )
    assert failures


def test_no_scattered_classification_or_block_code_definitions():
    assert drift.validate_policy_literal_drift(repo_root=ROOT, write_report=False) == []


def test_master_plan_coverage_report_consumed_with_structural_evidence():
    domain_map = _domain_map()
    coverage = json.loads(
        (ROOT / "docs/master_plan/generated/MasterPlanSectionCoverageReport.json").read_text()
    )
    assert "coverage_report_digest_sha256" not in domain_map
    assert domain_map["coverage_report_ref"].endswith("MasterPlanSectionCoverageReport.json")
    assert domain_map["report_type"] == coverage["report_type"]
    assert domain_map["report_version"] == coverage["report_version"]
    assert domain_map["deterministic_output"] is True
    assert domain_map["generated_by"] == coverage["generated_by"]
    assert domain_map["generated_at_utc"] == coverage["generated_at_utc"]
    assert domain_map["registry_entry_count"] == coverage["registry"]["entry_count"]
    assert domain_map["parser_visible_section_count"] == coverage["coverage_summary"][
        "parser_visible_section_count"
    ]
    assert all(domain_map["required_structural_keys_present"].values())
    assert domain_map["required_structural_keys_missing"] == []


def test_master_plan_coverage_values_not_guessed():
    domain_map = _domain_map()
    coverage = json.loads(
        (ROOT / "docs/master_plan/generated/MasterPlanSectionCoverageReport.json").read_text()
    )
    assert domain_map["master_plan_section_count"] == len(coverage["section_coverage"])
    assert domain_map["coverage_entry_count"] == len(coverage["coverage_entries"])


def test_pr136_read_receipts_use_sizes_not_digests():
    for receipt in (
        _report("PR136ReadReceipt.report.json"),
        _roadmap_generated("CODEX_PR136_MANDATORY_READ_RECEIPT.json"),
    ):
        assert "file_digests_or_sizes" not in receipt
        assert "coverage_report_digest_sha256" not in receipt
        assert receipt["file_sizes_and_line_counts"]
        assert all(
            "sha256" not in metadata
            for metadata in receipt["file_sizes_and_line_counts"].values()
        )
        assert receipt["coverage_entry_count"] == _domain_map()["coverage_entry_count"]


def test_no_pr136_sha_digest_authority_fields_are_generated():
    required_forbidden_terms = {
        "AtomicRows.bundle.sha256",
        "atomicrows_bundle_sha_path",
        "ATOMICROWS_BUNDLE_SHA_PATH",
        "sha256",
    }
    assert required_forbidden_terms.issubset(
        validator.FORBIDDEN_PR136_DIGEST_AUTHORITY_TEXT
    )
    failures: list[str] = []
    for rel_path in _pr136_json_artifact_paths():
        payload = json.loads((ROOT / rel_path).read_text())
        failures.extend(
            f"{rel_path}:{field_path}"
            for field_path in validator._scan_forbidden_pr136_digest_authority_keys(payload)
        )
    for rel_path in _pr136_text_artifact_paths():
        text = (ROOT / rel_path).read_text()
        for forbidden in validator.FORBIDDEN_PR136_DIGEST_AUTHORITY_TEXT:
            if forbidden in text:
                failures.append(f"{rel_path}:{forbidden}")
    assert failures == []


def test_readiness_domain_taxonomy_is_coverage_derived():
    taxonomy = _taxonomy()
    assert "coverage entries" in taxonomy["domain_derivation_method"]
    assert taxonomy["taxonomy_authority_class"].startswith("COVERAGE_DERIVED")


def test_readiness_domain_count_is_not_hardcoded():
    domain_map = _domain_map()
    assert domain_map["readiness_domain_count"] == len(domain_map["domain_records"])
    assert domain_map["readiness_domain_count"] != 13


def test_no_arbitrary_domain_count_forced():
    assert _domain_map()["arbitrary_domain_count_forced"] is False


def test_fixed_13_domain_model_is_forbidden():
    assert _domain_map()["fixed_13_domain_model_used"] is False
    assert _taxonomy()["fixed_13_domain_model_used"] is False


def test_each_readiness_domain_has_evidence_basis():
    assert all(record["evidence_basis"] for record in _domain_map()["domain_records"])


def test_parent_domains_and_subdomains_are_traceable():
    taxonomy = _taxonomy()
    parent_ids = {row["parent_domain_id"] for row in taxonomy["parent_domains"]}
    assert parent_ids
    assert all(record["parent_domain_id"] in parent_ids for record in taxonomy["subdomains"])


def test_master_plan_coverage_entries_all_mapped_or_deferred_with_evidence():
    domain_map = _domain_map()
    assert domain_map["domain_map_complete"] is True
    assert domain_map["unmapped_entries"] == []


def test_domain_map_has_no_missing_domain():
    assert _domain_map()["readiness_domain_count"] > 0


def test_provisional_pr137_pr164_all_classified():
    assert {row["provisional_pr_number"] for row in _classification_records()} == set(
        range(137, 165)
    )


def test_provisional_skeleton_marked_non_authoritative():
    report = _report("PR136ProvisionalPR137ToPR164Classification.report.json")
    assert report["provisional_pr137_pr164_skeleton_used_as"] == (
        "NON_AUTHORITATIVE_PLANNING_INPUT_ONLY"
    )


def test_each_classification_has_evidence_basis():
    assert all(row["evidence_basis"] for row in _classification_records())


def test_sequence_can_confirm_split_replace_merge_insert_defer_or_require_owner_authorization():
    seen = {row["classification"] for row in _classification_records()}
    assert {"CONFIRMED", "SPLIT_OR_REPLACED", "NEW_INSERTION_REQUIRED_BEFORE_THIS_PR", "DEFERRED_AFTER_DAY1", "OWNER_AUTHORIZATION_REQUIRED"}.issubset(seen)


def test_final_sequence_has_no_duplicate_pr_numbers():
    ids = [row["final_sequence_pr_number_or_placeholder"] for row in _sequence()["sequence_entries"]]
    assert len(ids) == len(set(ids))


def test_final_sequence_is_planning_authority_not_execution_authority():
    assert _sequence()["sequence_authority_class"] == policy.SEQUENCE_AUTHORITY
    assert all(row["current_authority_created"] is False for row in _sequence()["sequence_entries"])


def test_future_pr_cards_have_definition_of_done():
    cards = _report("PR136FuturePRCardRegistry.report.json")["cards"]
    assert cards
    assert all(card["definition_of_done"] for card in cards)


def test_dependency_graph_is_acyclic():
    graph = _report("PR136LaunchReadinessDependencyGraph.report.json")
    assert graph["acyclic"] is True
    assert validator._graph_has_cycle(
        [node["node_id"] for node in graph["nodes"]], graph["edges"]
    ) is False


def test_dependency_graph_includes_all_derived_domains():
    graph_nodes = {node["node_id"] for node in _report("PR136LaunchReadinessDependencyGraph.report.json")["nodes"]}
    assert {row["domain_id"] for row in _domain_map()["domain_records"]}.issubset(graph_nodes)


def test_market_specific_index_has_all_four_scopes():
    scopes = [row["canonical_venue_id"] for row in _report("PR136MarketSpecificLaunchReadinessIndex.report.json")["market_scopes"]]
    assert tuple(scopes) == policy.CANONICAL_VENUES


def test_forecastex_ibkr_canonical_identity_preserved():
    scopes = [row["canonical_venue_id"] for row in _report("PR136MarketSpecificLaunchReadinessIndex.report.json")["market_scopes"]]
    assert "FORECASTEX_IBKR" in scopes
    assert "FORECASTX" not in scopes


def test_atomicrows_materialization_remains_blocked():
    qmap = _report("PR136QuantumAtomicRowsOptimizationReadinessMap.report.json")
    assert qmap["atomicrows_materialization_authority_created_flag"] is False
    assert qmap["future_owner_authorization_required_for_materialization_flag"] is True


def test_atomicrows_bundle_sha_paths_not_created_or_edited():
    qmap = _report("PR136QuantumAtomicRowsOptimizationReadinessMap.report.json")
    assert qmap["atomicrows_bundle_created_flag"] is False
    assert qmap["atomicrows_bundle_integrity_authority_status"] == (
        "OWNER_DISABLED_NO_QTT_SHA"
    )
    assert "atomicrows_bundle_sha_path" not in qmap
    assert "atomicrows_sha_created_flag" not in qmap
    assert "AtomicRows.bundle.sha256" not in json.dumps(qmap)


def test_quantum_readiness_is_metadata_only():
    assert _report("PR136QuantumAtomicRowsOptimizationReadinessMap.report.json")[
        "quantum_evidence_status"
    ] == "METADATA_ONLY_NO_EXECUTION"


def test_quantum_parameter_refs_are_future_refs_only():
    qmap = _report("PR136QuantumAtomicRowsOptimizationReadinessMap.report.json")
    assert qmap["future_qaoa_depth_p_refs"][0].startswith("FUTURE_")
    assert qmap["future_qubo_penalty_scale_refs"][0].startswith("FUTURE_")


def test_no_quantum_execution_or_advantage_claim():
    qmap = _report("PR136QuantumAtomicRowsOptimizationReadinessMap.report.json")
    assert qmap["no_quantum_execution_flag"] is True
    assert qmap["no_quantum_advantage_claim_flag"] is True


def test_source_evidence_required_before_connector_binding():
    graph = _report("PR136LaunchReadinessDependencyGraph.report.json")
    assert "ORDER_AUTHORITY_BLOCKED_UNTIL_SOURCE_CONNECTOR_CASH_RISK_GATES" in graph[
        "blocked_execution_edges"
    ]


def test_connector_binding_not_created():
    assert policy.NO_AUTHORITY_FLAGS["creates_connector_binding"] is False
    assert _report("PR136CommandActionMatrix.report.json")["actions"][0][
        "creates_connector_binding"
    ] is False


def test_runtime_cash_private_state_not_created():
    flags = _report("PR136Day1LaunchReadinessRoadmap.report.json")["no_authority_flags"]
    assert flags["creates_runtime_cash_authority"] is False
    assert flags["creates_private_state_fetch"] is False


def test_replay_paper_execution_not_created():
    flags = _report("PR136Day1LaunchReadinessRoadmap.report.json")["no_authority_flags"]
    assert flags["creates_replay_execution"] is False
    assert flags["creates_paper_execution"] is False


def test_order_authority_not_created():
    assert _report("PR136Day1LaunchReadinessRoadmap.report.json")["no_authority_flags"][
        "creates_order_authority"
    ] is False


def test_profit_evidence_not_created():
    assert _report("PR136Day1LaunchReadinessRoadmap.report.json")["no_authority_flags"][
        "creates_profit_evidence"
    ] is False


def test_day1_launch_not_created():
    assert _report("PR136Day1LaunchReadinessRoadmap.report.json")["no_authority_flags"][
        "creates_day1_live_launch"
    ] is False


def test_day1_launch_ready_is_owner_command_required_not_started():
    terminal = _report("PR136LaunchReadinessDependencyGraph.report.json")["terminal_nodes"]
    assert "DAY1_LAUNCH_READY_OWNER_COMMAND_REQUIRED" in terminal
    assert "OFFICIAL_DAY1_LIVE_TRADING_STARTED_OWNER_AUTHORIZED_ONLY" in terminal


def test_agent_orchestration_map_grants_no_live_authority():
    agents = _report("PR136AgentLaunchOrchestrationMap.report.json")["agent_domains"]
    assert all(agent["live_order_authority_allowed"] is False for agent in agents)


def test_latency_map_blocks_control_plane_calls_from_live_hot_path():
    latency = _report("PR136LatencyControlPlaneVsLivePathMap.report.json")
    assert "LLM reasoning" in latency["live_hot_path_forbidden_current_and_future_runtime_calls"]
    assert "quantum backend call" in latency["live_hot_path_forbidden_current_and_future_runtime_calls"]


def test_owner_authorization_required_for_live_or_materialization_nodes():
    sequence = _sequence()["sequence_entries"]
    assert any(row["final_sequence_pr_number_or_placeholder"] == "PR164" and row["owner_authorization_required"] for row in sequence)
    assert any(row["final_sequence_pr_number_or_placeholder"] == "PR141" and row["owner_authorization_required"] for row in sequence)


def test_versioned_candidate_set_snapshot_lock_wording_preserved():
    text = (ROOT / "tests/fixtures/replay_paper/historical_dataset_digest_and_loader.fixture.json").read_text()
    assert "versioned_candidate_set_snapshot_lock" in text.lower()


def test_no_global_permanent_candidate_freeze_language():
    doc = (ROOT / "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md").read_text()
    assert "global permanent candidate freeze" not in doc.lower()


def test_additive_roadmap_doc_does_not_delete_existing_roadmap_content():
    doc = (ROOT / "docs/roadmap/QTT_PostPR135_Day1_Launch_Readiness_Roadmap_v1_0.md").read_text()
    assert "additive currentization" in doc
    assert (ROOT / "docs/roadmap/QTT_PRs_Roadmap_Index_v1_0.json").exists()


def test_validator_marker_only_on_full_pass():
    assert validator.marker_for_failures([]) == policy.VALIDATOR_MARKER
    fake_failure = validator.ValidationFailure("X", "bad", "artifact")
    assert validator.marker_for_failures([fake_failure]) == ""


def test_roadmap_generated_receipts_present():
    assert _roadmap_generated("CODEX_PR136_ROUTE_TRIAGE_RECEIPT.json")[
        "same_number_inference_used"
    ] is False
    assert _roadmap_generated("CODEX_PR136_MANDATORY_READ_RECEIPT.json")[
        "missing_files"
    ] == []
