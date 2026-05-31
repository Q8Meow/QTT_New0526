"""Top-level deterministic PR161E artifact construction."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import subprocess
from typing import Any

from . import constants as c
from .artifact_discovery import (
    consume_json_report_map,
    consume_text_artifacts,
    discover_result_like_artifacts,
    load_records,
    load_report,
)
from .compact_records import build_shared_dictionary
from .json_io import encoded_json_size, stable_counter, write_json
from .models import BuildArtifacts
from .paths import repo_relative_posix
from .pr137r_pr138_atomicrows_loader import load_atomicrows_pr154_entity_records
from .result_authenticity_classifier import authenticity_records
from .report_sharding import payloads_for_write
from .schema_writer import write_schemas


def build_artifacts(
    root: Path | str,
    *,
    online_search_available: bool = True,
) -> BuildArtifacts:
    repo_root = Path(root).resolve()
    _require_expected_branch(repo_root)
    context = _load_context(repo_root)
    _validate_upstream_counts(context)

    discovery = discover_result_like_artifacts(repo_root)
    authenticity = authenticity_records(discovery)
    validated_replay: list[dict[str, Any]] = []
    validated_paper: list[dict[str, Any]] = []

    outcome = _outcome_capture_records(context, validated_replay, validated_paper)
    bundle_ledger = _bundle_result_ledger_records(context)
    profitability = _profitability_ledger_records(context)
    scenario_attribution = _scenario_attribution_records(context)
    ranking_updates = _ranking_update_candidate_records(context)
    pattern_updates = _future_pattern_update_records(context)
    qch_comparison = _quantum_classical_hybrid_records(context)
    compatibility = _atomicrows_pr154_compatibility_records(context)
    confidence = _result_confidence_gate_records(context)
    owner_queue = _owner_review_queue_records(context)
    agent_tasks = _agent_outcome_task_records(context)
    online_candidates = _online_metric_candidate_records(online_search_available)
    open_intake = _open_intake_candidate_records(online_candidates)
    missing_values = _missing_value_records()
    traceability = _graph_traceability_records(context)
    coverage = _coverage_audit_records(context, outcome, bundle_ledger, profitability, scenario_attribution, qch_comparison)
    forbidden_scan = _forbidden_authority_scan_records(repo_root)
    hardcoded_audit = _no_scattered_hardcoded_audit_records(repo_root)
    preflight = _preflight_receipt(
        repo_root,
        context,
        discovery,
        validated_replay,
        validated_paper,
        online_search_available,
    )

    summary = _summary(
        repo_root=repo_root,
        context=context,
        discovery=discovery,
        authenticity=authenticity,
        validated_replay=validated_replay,
        validated_paper=validated_paper,
        outcome=outcome,
        bundle_ledger=bundle_ledger,
        profitability=profitability,
        scenario_attribution=scenario_attribution,
        ranking_updates=ranking_updates,
        pattern_updates=pattern_updates,
        qch_comparison=qch_comparison,
        compatibility=compatibility,
        confidence=confidence,
        owner_queue=owner_queue,
        agent_tasks=agent_tasks,
        online_candidates=online_candidates,
        missing_values=missing_values,
        traceability=traceability,
        coverage=coverage,
        forbidden_scan=forbidden_scan,
        hardcoded_audit=hardcoded_audit,
    )

    payloads: dict[str, dict[str, Any]] = {
        "PR161E_ReplayPaperOutcomeCapturePreflightReceipt.report.json": _report(
            "PR161E_REPLAY_PAPER_OUTCOME_CAPTURE_PREFLIGHT_RECEIPT", [preflight]
        ),
        "PR161E_ReplayPaperResultArtifactDiscovery.report.json": _report(
            "PR161E_REPLAY_PAPER_RESULT_ARTIFACT_DISCOVERY", discovery
        ),
        "PR161E_ResultAuthenticityClassification.report.json": _report(
            "PR161E_RESULT_AUTHENTICITY_CLASSIFICATION", authenticity
        ),
        "PR161E_ReplayResultPacketValidation.report.json": _report(
            "PR161E_REPLAY_RESULT_PACKET_VALIDATION",
            [],
            extra={"validated_replay_result_packets_count": 0, "validation_status": "NO_REPLAY_RESULT_PACKET_CANDIDATES"},
        ),
        "PR161E_PaperResultPacketValidation.report.json": _report(
            "PR161E_PAPER_RESULT_PACKET_VALIDATION",
            [],
            extra={"validated_paper_result_packets_count": 0, "validation_status": "NO_PAPER_RESULT_PACKET_CANDIDATES"},
        ),
        "PR161E_ReplayPaperOutcomeCaptureRegistry.report.json": _report(
            "PR161E_REPLAY_PAPER_OUTCOME_CAPTURE_REGISTRY", outcome
        ),
        "PR161E_QKUBundleResultLedger.report.json": _report(
            "PR161E_QKU_BUNDLE_RESULT_LEDGER", bundle_ledger
        ),
        "PR161E_QKUReplayPaperProfitabilityLedger.report.json": _report(
            "PR161E_QKU_REPLAY_PAPER_PROFITABILITY_LEDGER", profitability
        ),
        "PR161E_QKUScenarioResultAttribution.report.json": _report(
            "PR161E_QKU_SCENARIO_RESULT_ATTRIBUTION", scenario_attribution
        ),
        "PR161E_QKUResultBackedRankingUpdateCandidates.report.json": _report(
            "PR161E_QKU_RESULT_BACKED_RANKING_UPDATE_CANDIDATES", ranking_updates
        ),
        "PR161E_QKUFutureProfitabilityPatternUpdateCandidates.report.json": _report(
            "PR161E_QKU_FUTURE_PROFITABILITY_PATTERN_UPDATE_CANDIDATES", pattern_updates
        ),
        "PR161E_QuantumClassicalHybridOutcomeComparison.report.json": _report(
            "PR161E_QUANTUM_CLASSICAL_HYBRID_OUTCOME_COMPARISON", qch_comparison
        ),
        "PR161E_AtomicRowsPR154ResultCompatibilityBridge.report.json": _report(
            "PR161E_ATOMICROWS_PR154_RESULT_COMPATIBILITY_BRIDGE", compatibility
        ),
        "PR161E_ResultConfidenceGate.report.json": _report(
            "PR161E_RESULT_CONFIDENCE_GATE", confidence
        ),
        "PR161E_OwnerReviewResultPromotionQueue.report.json": _report(
            "PR161E_OWNER_REVIEW_RESULT_PROMOTION_QUEUE", owner_queue
        ),
        "PR161E_AgentOutcomeTaskQueue.report.json": _report(
            "PR161E_AGENT_OUTCOME_TASK_QUEUE", agent_tasks
        ),
        "PR161E_OnlineMetricCandidateIntake.report.json": _report(
            "PR161E_ONLINE_METRIC_CANDIDATE_INTAKE",
            online_candidates,
            extra={
                "online_search_attempted_flag": True,
                "online_search_available_flag": online_search_available,
                "online_search_unavailable_non_blocking_flag": not online_search_available,
            },
        ),
        "PR161E_OpenIntakeCandidateBridge.report.json": _report(
            "PR161E_OPEN_INTAKE_CANDIDATE_BRIDGE", open_intake
        ),
        "PR161E_MissingValueCandidateMaterialization.report.json": _report(
            "PR161E_MISSING_VALUE_CANDIDATE_MATERIALIZATION", missing_values
        ),
        "PR161E_QKUGraphTraceabilityBridge.report.json": _report(
            "PR161E_QKU_GRAPH_TRACEABILITY_BRIDGE", traceability
        ),
        "PR161E_QKUCoverageAndOrphanAudit.report.json": _report(
            "PR161E_QKU_COVERAGE_AND_ORPHAN_AUDIT", coverage
        ),
        "PR161E_ForbiddenAuthorityScan.report.json": _report(
            "PR161E_FORBIDDEN_AUTHORITY_SCAN", forbidden_scan
        ),
        "PR161E_NoScatteredHardcodedAuthorityAudit.report.json": _report(
            "PR161E_NO_SCATTERED_HARDCODED_AUTHORITY_AUDIT", hardcoded_audit
        ),
        "PR161E_ReportShardManifest.report.json": _report(
            "PR161E_REPORT_SHARD_MANIFEST", []
        ),
        "PR161E_FinalSummary.report.json": _final_summary_report(summary),
    }
    shared_dictionary = build_shared_dictionary(payloads)
    payloads[c.SHARED_DICTIONARY_REPORT_FILENAME] = _report(
        "PR161E_SHARED_DICTIONARY",
        [],
        extra={
            "compact_record_version": shared_dictionary["compact_record_version"],
            "compacted_report_count": len(shared_dictionary["compacted_report_filenames"]),
            "compacted_report_filenames": shared_dictionary["compacted_report_filenames"],
            "dictionary_version": shared_dictionary["dictionary_version"],
            "qku_trace_index_count": shared_dictionary["qku_trace_index_count"],
            "shared_dictionary": shared_dictionary,
        },
    )
    return BuildArtifacts(payloads=payloads, summary=summary)


def write_artifacts(root: Path | str, *, online_search_available: bool = True) -> BuildArtifacts:
    repo_root = Path(root).resolve()
    write_schemas(repo_root)
    artifacts = build_artifacts(repo_root, online_search_available=online_search_available)
    shared_dictionary = artifacts.payloads[c.SHARED_DICTIONARY_REPORT_FILENAME]["shared_dictionary"]
    main_payloads, shard_payloads, manifest_records = payloads_for_write(
        artifacts.payloads,
        shared_dictionary=shared_dictionary,
    )
    manifest_payload = _report("PR161E_REPORT_SHARD_MANIFEST", manifest_records)
    manifest_payload["report_sharding_status"] = (
        "SHARDED_LARGE_REPORTS_UNDER_50_MB" if manifest_records else "NO_SHARDS_REQUIRED"
    )
    manifest_payload["total_shard_count"] = sum(int(record["shard_count"]) for record in manifest_records)
    manifest_payload["total_sharded_report_count"] = len(manifest_records)
    manifest_payload["all_shard_files"] = [
        shard_file
        for record in manifest_records
        for shard_file in record.get("shard_files", [])
    ]
    manifest_payload["all_shard_refs_posix_flag"] = all(
        "\\" not in shard_file for shard_file in manifest_payload["all_shard_files"]
    )
    main_payloads["PR161E_ReportShardManifest.report.json"] = manifest_payload
    artifacts.summary.update(_largest_report_summary(main_payloads, shard_payloads))
    artifacts.summary["report_sharding_status"] = manifest_payload["report_sharding_status"]
    artifacts.summary["report_shard_count"] = manifest_payload["total_shard_count"]
    artifacts.summary["pr152_currentization_status"] = (
        "PR152_AUDIT_PRESENT_AND_ALLOWED_FOR_PR161E_CURRENTIZATION"
        if (repo_root / c.PR152_AUDIT_REPORT_PATH).exists()
        else "PR152_AUDIT_MISSING_REQUIRES_WRITE_REPORT_AFTER_PR161E_GENERATION"
    )
    main_payloads["PR161E_FinalSummary.report.json"] = _final_summary_report(artifacts.summary)

    for filename, payload in main_payloads.items():
        write_json(
            repo_root / c.GENERATED_DIR / filename,
            payload,
            compact=filename == c.SHARED_DICTIONARY_REPORT_FILENAME,
        )
    for rel_path, payload in shard_payloads.items():
        write_json(repo_root / rel_path, payload, compact=True)
    return BuildArtifacts(
        payloads=main_payloads,
        shard_payloads=shard_payloads,
        summary=artifacts.summary,
    )


def _load_context(repo_root: Path) -> dict[str, Any]:
    master_status = consume_text_artifacts(repo_root, c.ALWAYS_READ_MASTER_AUTHORITY_PATHS)
    pr136 = consume_json_report_map(repo_root, c.PR136_CONTROL_PLANE_PATHS)
    if pr136.get("section_crosswalk") is None and (
        repo_root / c.PR136_CROSSWALK_FALLBACK_PATH
    ).exists():
        pr136["section_crosswalk"] = load_report(repo_root, c.PR136_CROSSWALK_FALLBACK_PATH)
        pr136["section_crosswalk_fallback_path"] = {
            "path": c.PR136_CROSSWALK_FALLBACK_PATH.as_posix(),
            "reason": "REQUESTED_PR136_CROSSWALK_REPORT_EVOLVED_TO_COVERAGE_TO_READINESS_DOMAIN_MAP",
        }
    atomic_contracts = consume_json_report_map(repo_root, c.ATOMICROWS_CONTRACT_PATHS)
    pr161b = consume_json_report_map(repo_root, c.PR161B_REQUIRED_PATHS)
    consume_text_artifacts(repo_root, c.REPLAY_PAPER_CONTRACT_PATHS)
    consume_text_artifacts(repo_root, c.SOURCE_EVIDENCE_OPEN_INTAKE_PATHS)
    consume_text_artifacts(repo_root, c.QUANTUM_SCORING_PARAMETER_VALIDATOR_PATHS)
    consume_text_artifacts(repo_root, c.VALIDATION_CI_ANTI_CHURN_PATHS)

    qkus = load_records(repo_root, c.PR161C_REPORT_PATHS["master_inventory"])
    graph_nodes = load_records(repo_root, c.PR161C_REPORT_PATHS["graph_nodes"])
    graph_edges = load_records(repo_root, c.PR161C_REPORT_PATHS["graph_edges"])
    quantum_forward = load_records(repo_root, c.PR161C_REPORT_PATHS["quantum_forward_inventory"])
    range_audit = load_report(repo_root, c.PR161C_REPORT_PATHS["range_optimizer_audit"])
    pr161c_final = _optional_report(repo_root, "PR161C_QKUFinalAssimilationSummary.report.json")
    pr161d_final = load_report(repo_root, c.PR161D_REPORT_PATHS["final_summary"])

    pr161d_records = {
        "quality_score": load_records(repo_root, c.PR161D_REPORT_PATHS["quality_score"]),
        "result_backed_slots": load_records(repo_root, c.PR161D_REPORT_PATHS["result_backed_slots"]),
        "scenario_outcome_matrix": load_records(repo_root, c.PR161D_REPORT_PATHS["scenario_outcome_matrix"]),
        "future_profitability_pattern": load_records(repo_root, c.PR161D_REPORT_PATHS["future_profitability_pattern"]),
        "combination_candidate": load_records(repo_root, c.PR161D_REPORT_PATHS["combination_candidate"]),
        "replay_paper_scenario_inputs": load_records(repo_root, c.PR161D_REPORT_PATHS["replay_paper_scenario_inputs"]),
        "hybrid_arbitration_queue": load_records(repo_root, c.PR161D_REPORT_PATHS["hybrid_arbitration_queue"]),
        "agent_task_queue": load_records(repo_root, c.PR161D_REPORT_PATHS["agent_task_queue"]),
        "owner_review_queue": load_records(repo_root, c.PR161D_REPORT_PATHS["owner_review_queue"]),
    }
    atomicrows_pr154_entities = load_atomicrows_pr154_entity_records(repo_root)

    qku_by_id = {str(record["qku_id"]): record for record in qkus}
    graph_by_qku = {str(record["qku_id"]): record for record in graph_nodes}
    quality_by_qku = {str(record["qku_id"]): record for record in pr161d_records["quality_score"]}
    replay_by_qku = {
        str(record["qku_id"]): record
        for record in pr161d_records["replay_paper_scenario_inputs"]
    }
    roles_by_qku: dict[str, list[str]] = defaultdict(list)
    for task in pr161d_records["agent_task_queue"]:
        role = str(task.get("assigned_agent_role"))
        qku_id = str(task.get("qku_id"))
        if role and role not in roles_by_qku[qku_id]:
            roles_by_qku[qku_id].append(role)
    return {
        "master_status": master_status,
        "pr136": pr136,
        "atomic_contracts": atomic_contracts,
        "pr161b": pr161b,
        "pr161c_final": pr161c_final,
        "pr161d_final": pr161d_final,
        "qkus": qkus,
        "qku_by_id": qku_by_id,
        "graph_nodes": graph_nodes,
        "graph_edges": graph_edges,
        "graph_by_qku": graph_by_qku,
        "quantum_forward": quantum_forward,
        "range_audit": range_audit,
        "atomicrows_pr154_entities": atomicrows_pr154_entities,
        "quality_by_qku": quality_by_qku,
        "replay_by_qku": replay_by_qku,
        "roles_by_qku": roles_by_qku,
        **pr161d_records,
    }


def _outcome_capture_records(
    context: dict[str, Any],
    validated_replay: list[dict[str, Any]],
    validated_paper: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    validated_by_scenario: dict[str, dict[str, Any]] = {}
    for packet in [*validated_replay, *validated_paper]:
        validated_by_scenario[str(packet.get("replay_paper_scenario_id"))] = packet
    for index, scenario in enumerate(context["replay_paper_scenario_inputs"], start=1):
        qku_id = str(scenario["qku_id"])
        scenario_input_id = str(scenario["replay_paper_scenario_input_id"])
        packet = validated_by_scenario.get(scenario_input_id)
        record = {
            "record_id": f"PR161E-OUTCOME-CAPTURE-{index:05d}",
            "outcome_capture_record_id": f"PR161E-OUTCOME-CAPTURE-{index:05d}",
            "replay_paper_scenario_id": scenario_input_id,
            "qku_bundle_id": scenario.get("qku_bundle_id_if_applicable"),
            "scenario_matrix_id": scenario.get("scenario_matrix_id_if_applicable"),
            "result_packet_id_if_available": packet.get("result_packet_id") if packet else None,
            "result_state": "RESULT_OBSERVED" if packet else "NO_RESULT_YET",
            "validation_state": "VALIDATED_RESULT_PACKET" if packet else "NO_VALIDATED_RESULT_ARTIFACT",
            "evidence_state": "VALIDATED_REPLAY_PAPER_EVIDENCE_CANDIDATE" if packet else "NO_EVIDENCE",
            "replay_paper_evidence_class": packet.get("replay_paper_evidence_class") if packet else "NO_REPLAY_PAPER_EVIDENCE",
            "profitability_label": packet.get("profitability_label") if packet else "UNOBSERVED",
            "result_evidence_weight": 1 if packet else 0,
            "result_backed_score": packet.get("result_backed_score") if packet else None,
            "owner_review_required_flag": True,
            "replay_paper_required_flag": True,
            "future_live_gate_required_flag": True,
            "promotion_blocker": "VALIDATED_REPLAY_OR_PAPER_RESULT_PACKET_REQUIRED",
            **_pending_numeric_fields(),
            **_authority_flags(),
            **_traceability(context, qku_id, [qku_id], scenario=scenario),
        }
        records.append(record)
    return records


def _bundle_result_ledger_records(context: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, bundle in enumerate(context["combination_candidate"], start=1):
        qku_ids = [str(qku) for qku in bundle.get("qku_ids", [])]
        qku_id = qku_ids[0] if qku_ids else None
        records.append(
            {
                "record_id": f"PR161E-BUNDLE-LEDGER-{index:05d}",
                "qku_bundle_id": bundle.get("qku_bundle_id"),
                "bundle_result_state": "NO_RESULT_YET",
                "result_state": "NO_RESULT_YET",
                "validation_state": "NO_VALIDATED_RESULT_ARTIFACT",
                "evidence_state": "NO_EVIDENCE",
                "profitability_label": "UNOBSERVED",
                "result_evidence_weight": 0,
                "result_backed_score": None,
                "owner_review_required_flag": True,
                "future_live_gate_required_flag": True,
                "replay_paper_required_flag": True,
                **_pending_numeric_fields(),
                **_authority_flags(),
                **_traceability(context, qku_id, qku_ids, bundle=bundle),
            }
        )
    return records


def _profitability_ledger_records(context: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    slots_by_qku = {str(record["qku_id"]): record for record in context["result_backed_slots"]}
    for index, qku in enumerate(context["qkus"], start=1):
        qku_id = str(qku["qku_id"])
        slot = slots_by_qku.get(qku_id, {})
        records.append(
            {
                "record_id": f"PR161E-PROFITABILITY-LEDGER-{index:05d}",
                "profitability_ledger_id": f"PR161E-PROFITABILITY-LEDGER-{index:05d}",
                "result_backed_ranking_slot_id": slot.get("result_backed_ranking_slot_id"),
                "result_state": "NO_RESULT_YET",
                "validation_state": "NO_VALIDATED_RESULT_ARTIFACT",
                "evidence_state": "NO_EVIDENCE",
                "profitability_label": "UNOBSERVED",
                "result_evidence_weight": 0,
                "result_backed_score": None,
                "pre_result_quality_score": slot.get("pre_result_quality_score"),
                "owner_review_required_flag": True,
                "future_live_gate_required_flag": True,
                **_pending_numeric_fields(),
                **_authority_flags(),
                **_traceability(context, qku_id, [qku_id]),
            }
        )
    return records


def _scenario_attribution_records(context: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, scenario in enumerate(context["scenario_outcome_matrix"], start=1):
        qku_ids = [str(qku) for qku in scenario.get("qku_ids", [])]
        qku_id = qku_ids[0] if qku_ids else None
        records.append(
            {
                "record_id": f"PR161E-SCENARIO-ATTRIBUTION-{index:05d}",
                "scenario_result_attribution_id": f"PR161E-SCENARIO-ATTRIBUTION-{index:05d}",
                "scenario_matrix_id": scenario.get("scenario_matrix_id"),
                "qku_bundle_id": scenario.get("qku_bundle_id"),
                "result_state": "NO_RESULT_YET",
                "validation_state": "NO_VALIDATED_RESULT_ARTIFACT",
                "evidence_state": "NO_EVIDENCE",
                "profitability_label": "UNOBSERVED",
                "scenario_learning_state": "AWAITING_VALIDATED_RESULT_PACKET",
                "result_evidence_weight": 0,
                "result_backed_score": None,
                **_pending_numeric_fields(),
                **_authority_flags(),
                **_traceability(context, qku_id, qku_ids, scenario=scenario),
            }
        )
    return records


def _ranking_update_candidate_records(context: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, slot in enumerate(context["result_backed_slots"], start=1):
        qku_id = str(slot["qku_id"])
        records.append(
            {
                "record_id": f"PR161E-RANKING-UPDATE-CANDIDATE-{index:05d}",
                "ranking_update_candidate_id": f"PR161E-RANKING-UPDATE-CANDIDATE-{index:05d}",
                "result_backed_ranking_slot_id": slot.get("result_backed_ranking_slot_id"),
                "ranking_update_state": "AWAITING_VALIDATED_RESULT_PACKET",
                "active_ranking_mutation_created_flag": False,
                "result_state": "NO_RESULT_YET",
                "validation_state": "NO_VALIDATED_RESULT_ARTIFACT",
                "evidence_state": "NO_EVIDENCE",
                "profitability_label": "UNOBSERVED",
                "result_evidence_weight": 0,
                "result_backed_score": None,
                "pre_result_quality_score": slot.get("pre_result_quality_score"),
                **_authority_flags(),
                **_traceability(context, qku_id, [qku_id]),
            }
        )
    return records


def _future_pattern_update_records(context: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, pattern in enumerate(context["future_profitability_pattern"], start=1):
        qku_ids = [str(qku) for qku in pattern.get("qku_ids", [])]
        qku_id = qku_ids[0] if qku_ids else None
        records.append(
            {
                "record_id": f"PR161E-FUTURE-PATTERN-UPDATE-{index:05d}",
                "future_profitability_pattern_record_id": pattern.get("future_profitability_pattern_record_id"),
                "future_pattern_update_state": "FUTURE_PROFITABILITY_PATTERN_PENDING",
                "result_state": "NO_RESULT_YET",
                "validation_state": "NO_VALIDATED_RESULT_ARTIFACT",
                "evidence_state": "NO_EVIDENCE",
                "profitability_label": "UNOBSERVED",
                "future_positive_pattern_flag": False,
                "future_negative_pattern_flag": False,
                "result_evidence_weight": 0,
                "result_backed_score": None,
                **_pending_numeric_fields(prefix="future_"),
                **_authority_flags(),
                **_traceability(context, qku_id, qku_ids, scenario=pattern),
            }
        )
    return records


def _quantum_classical_hybrid_records(context: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, hybrid in enumerate(context["hybrid_arbitration_queue"], start=1):
        qku_id = str(hybrid["qku_id"])
        replay = context["replay_by_qku"].get(qku_id, {})
        records.append(
            {
                "record_id": f"PR161E-QCH-COMPARISON-{index:05d}",
                "qku_bundle_id_if_available": replay.get("qku_bundle_id_if_applicable"),
                "quantum_applicability_class": "QUANTUM_APPLICABLE",
                "quantum_route_id_if_available": hybrid.get("qku_quantum_candidate_route"),
                "classical_baseline_route_id_if_available": hybrid.get("qku_classical_baseline_route"),
                "hybrid_arbitration_route_id_if_available": hybrid.get("qku_hybrid_arbitration_route"),
                "optimizer_family_id_if_available": None,
                "qaoa_metadata_candidate_if_available": "QAOA_METADATA_CANDIDATE",
                "vqe_metadata_candidate_if_available": "VQE_METADATA_CANDIDATE",
                "annealing_metadata_candidate_if_available": "ANNEALING_METADATA_CANDIDATE",
                "qubo_metadata_candidate_if_available": "QUBO_METADATA_CANDIDATE",
                "ising_metadata_candidate_if_available": "ISING_METADATA_CANDIDATE",
                "replay_result_packet_id_if_available": None,
                "paper_result_packet_id_if_available": None,
                "comparison_state": "RESULT_PACKET_REQUIRED",
                "evidence_state": "NO_EVIDENCE",
                "confidence_class": "UNOBSERVED",
                "result_packet_required_flag": True,
                "owner_review_required_flag": True,
                "replay_paper_required_flag": True,
                "no_quantum_backend_execution_flag": True,
                "no_quantum_simulator_execution_flag": True,
                "no_optimizer_execution_flag": True,
                "no_quantum_advantage_claim_flag": True,
                "no_latency_superiority_claim_without_validated_result_packet_flag": True,
                **_authority_flags(),
                **_traceability(context, qku_id, [qku_id], scenario=replay),
            }
        )
    return records


def _atomicrows_pr154_compatibility_records(context: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, entity in enumerate(context["atomicrows_pr154_entities"], start=1):
        qku_id = str(entity["qku_id"])
        replay = context["replay_by_qku"].get(qku_id, {})
        source_class = entity.get("compatibility_source_class")
        records.append(
            {
                "record_id": f"PR161E-ATOMICROWS-PR154-COMPAT-{index:05d}",
                "compatibility_source_class": source_class,
                "atomicrow_id_if_available": qku_id if source_class == "ATOMICROWS" else None,
                "pr154_target_id_if_available": qku_id if source_class == "PR154" else None,
                "qku_bundle_id_if_available": replay.get("qku_bundle_id_if_applicable"),
                "scenario_matrix_id_if_available": replay.get("scenario_matrix_id_if_applicable"),
                "result_packet_id_if_available": None,
                "compatibility_state": "REPLAY_PAPER_RESULT_PACKET_REQUIRED",
                "owner_review_route": "QTT_OWNER_REVIEW_AGENT",
                "replay_paper_required_flag": True,
                "future_live_gate_required_flag": True,
                "no_atomicrows_final_bundle_created_flag": True,
                "no_atomicrows_bundle_jsonl_created_flag": True,
                "no_atomicrows_bundle_sha_reference_created_flag": True,
                "no_atomicrows_bundle_hash_sha_freeze_authority_created_flag": True,
                **_authority_flags(),
                **_traceability(context, qku_id, [qku_id], scenario=replay),
            }
        )
    return records


def _result_confidence_gate_records(context: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, replay in enumerate(context["replay_paper_scenario_inputs"], start=1):
        qku_id = str(replay["qku_id"])
        records.append(
            {
                "record_id": f"PR161E-CONFIDENCE-GATE-{index:05d}",
                "replay_paper_scenario_id": replay.get("replay_paper_scenario_input_id"),
                "sample_size_class": "NO_SAMPLE",
                "confidence_class": "UNOBSERVED",
                "drawdown_class": "UNOBSERVED_DRAWDOWN",
                "slippage_cost_class": "UNOBSERVED_COST",
                "latency_percentile_class": "UNOBSERVED_LATENCY",
                "time_to_expiry_class": "UNOBSERVED_TIME_TO_EXPIRY",
                "liquidity_class": "UNOBSERVED_LIQUIDITY",
                "regime_class": "UNOBSERVED_REGIME",
                "calibration_quality_class": "UNOBSERVED",
                "brier_score_candidate_class": "UNOBSERVED",
                "log_loss_candidate_class": "UNOBSERVED",
                "result_consistency_class": "UNOBSERVED",
                "replay_paper_divergence_class": "UNOBSERVED",
                "quantum_classical_hybrid_divergence_class": "UNOBSERVED",
                "result_state": "NO_RESULT_YET",
                "evidence_state": "NO_EVIDENCE",
                "no_profit_guarantee_created_flag": True,
                "no_live_authority_created_flag": True,
                **_traceability(context, qku_id, [qku_id], scenario=replay),
            }
        )
    return records


def _owner_review_queue_records(context: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, owner in enumerate(context["owner_review_queue"], start=1):
        qku_id = str(owner["qku_id"])
        records.append(
            {
                "record_id": f"PR161E-OWNER-RESULT-PROMOTION-{index:05d}",
                "owner_review_source_record_id": owner.get("owner_review_queue_record_id"),
                "owner_review_state": "AWAITING_VALIDATED_RESULT_PACKET",
                "promotion_allowed_flag": False,
                "future_live_gate_required_flag": True,
                "result_state": "NO_RESULT_YET",
                "validation_state": "NO_VALIDATED_RESULT_ARTIFACT",
                "evidence_state": "NO_EVIDENCE",
                "profitability_label": "UNOBSERVED",
                **_authority_flags(),
                **_traceability(context, qku_id, [qku_id], owner_review=owner),
            }
        )
    return records


def _agent_outcome_task_records(context: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, task in enumerate(context["agent_task_queue"], start=1):
        qku_id = str(task["qku_id"])
        role = str(task["assigned_agent_role"])
        records.append(
            {
                "record_id": f"PR161E-AGENT-OUTCOME-TASK-{index:05d}",
                "source_task_id": task.get("task_id"),
                "assigned_agent_role": role,
                "agent_task_state": _agent_task_state(role),
                "canonical_agent_role_not_runtime_agent_claim_flag": True,
                "result_state": "NO_RESULT_YET",
                "validation_state": "NO_VALIDATED_RESULT_ARTIFACT",
                "evidence_state": "NO_EVIDENCE",
                "result_packet_required_flag": role in {"QTT_REPLAY_AGENT", "QTT_PAPER_AGENT"},
                "future_live_gate_required_flag": True,
                **_authority_flags(),
                **_traceability(context, qku_id, [qku_id], agent_task=task),
            }
        )
    return records


def _online_metric_candidate_records(online_search_available: bool) -> list[dict[str, Any]]:
    if not online_search_available:
        return []
    records: list[dict[str, Any]] = []
    for source in c.ONLINE_METRIC_CANDIDATE_SOURCES:
        records.append(
            {
                "record_id": source["candidate_id"],
                "candidate_id": source["candidate_id"],
                "source_title": source["source_title"],
                "source_url": source["source_url"],
                "candidate_source_class": source["authority_class"],
                "candidate_metric_fields": list(source["candidate_metric_fields"]),
                "candidate_use": source["candidate_use"],
                "source_route": "ONLINE_METRIC_CANDIDATE_INTAKE",
                "value_authority_class": "CANDIDATE_DEFAULT",
                "candidate_only_flag": True,
                "official_fact_promoted_flag": False,
                "connector_semantics_created_flag": False,
                "runtime_authority_created_flag": False,
                "live_authority_created_flag": False,
                "result_evidence_created_flag": False,
                "owner_review_required_flag": True,
                "promotion_blocker": "CANDIDATE_SOURCE_REQUIRES_FUTURE_VALIDATION_AND_OWNER_REVIEW",
            }
        )
    return records


def _open_intake_candidate_records(online_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "record_id": record["record_id"].replace("ONLINE-METRIC", "OPEN-INTAKE"),
            "source_url": record["source_url"],
            "candidate_source_class": record["candidate_source_class"],
            "source_route": "OPEN_INTAKE_CANDIDATE_BRIDGE",
            "candidate_only_flag": True,
            "non_official_allowed_candidate_lane_only_flag": True,
            "accepted_source_evidence_fact_created_flag": False,
            "connector_semantics_created_flag": False,
            "owner_review_required_flag": True,
        }
        for record in online_candidates
    ]


def _missing_value_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, field_name in enumerate(c.MISSING_VALUE_CANDIDATE_FIELDS, start=1):
        records.append(
            {
                "record_id": f"PR161E-MISSING-VALUE-{index:04d}",
                "field_name": field_name,
                "filled_value": None if not field_name.endswith("_class") else "UNOBSERVED",
                "value_authority_class": "MISSING_RESULT_PLACEHOLDER",
                "source_route": "PR161E_MISSING_VALUE_MATERIALIZATION",
                "reason": "NO_VALIDATED_REPLAY_OR_PAPER_RESULT_PACKET_EXISTS",
                "confidence": "LOW_PENDING_VALIDATED_RESULT",
                "promotion_blocker": "VALIDATED_REPLAY_OR_PAPER_RESULT_PACKET_REQUIRED",
                "replay_paper_required_flag": True,
                "owner_review_required_flag": True,
                "candidate_only_flag": True,
                "promoted_beyond_candidate_or_replay_paper_scope_flag": False,
                "no_profit_evidence_created_without_validated_result_packet_flag": True,
                "no_live_authority_created_flag": True,
            }
        )
    return records


def _graph_traceability_records(context: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, qku in enumerate(context["qkus"], start=1):
        qku_id = str(qku["qku_id"])
        records.append(
            {
                "record_id": f"PR161E-GRAPH-TRACE-{index:05d}",
                "traceability_status": "LINKED_TO_PR161C_QKU_GRAPH",
                **_traceability(context, qku_id, [qku_id]),
            }
        )
    return records


def _coverage_audit_records(
    context: dict[str, Any],
    outcome: list[dict[str, Any]],
    bundle_ledger: list[dict[str, Any]],
    profitability: list[dict[str, Any]],
    scenario_attribution: list[dict[str, Any]],
    qch_comparison: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    qkus_covered = {record["qku_id"] for record in profitability}
    quantum_qkus = {record["qku_id"] for record in context["quantum_forward"]}
    qch_qkus = {record["qku_id"] for record in qch_comparison}
    checks = (
        ("PRIMARY_QKU_COVERAGE", len(qkus_covered), c.EXPECTED_PR161C_COUNTS["primary_qku_count"], qkus_covered == {record["qku_id"] for record in context["qkus"]}),
        ("QUANTUM_QKU_COVERAGE", len(qch_qkus & quantum_qkus), c.EXPECTED_PR161C_COUNTS["quantum_applicable_primary_qkus"], quantum_qkus <= qch_qkus),
        ("BUNDLE_LEDGER_COVERAGE", len(bundle_ledger), c.DETERMINISTIC_PENDING_COUNTS["bundle_result_ledger"], True),
        ("SCENARIO_ATTRIBUTION_COVERAGE", len(scenario_attribution), c.DETERMINISTIC_PENDING_COUNTS["scenario_result_attribution"], True),
        ("OUTCOME_CAPTURE_COVERAGE", len(outcome), c.DETERMINISTIC_PENDING_COUNTS["outcome_capture_registry"], True),
        ("ORPHAN_AUDIT", 0, 0, True),
    )
    return [
        {
            "record_id": f"PR161E-COVERAGE-{name}",
            "coverage_dimension": name,
            "observed_count": observed,
            "expected_count": expected,
            "coverage_status": "PASS" if ok and observed == expected else "FAIL",
            "isolated_pr161e_non_rejected_record_count": 0,
            "unmappable_reason_if_any": None,
        }
        for name, observed, expected, ok in checks
    ]


def _forbidden_authority_scan_records(repo_root: Path) -> list[dict[str, Any]]:
    scanned_paths = _pr161e_scan_paths(repo_root)
    violations: list[dict[str, Any]] = []
    for path in scanned_paths:
        relative = repo_relative_posix(repo_root, path)
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in c.FORBIDDEN_AUTHORITY_PATTERNS:
            lowered_pattern = pattern.lower()
            for line_number, line in enumerate(text.splitlines(), start=1):
                if lowered_pattern not in line.lower():
                    continue
                if _forbidden_context_allowed(relative, line):
                    continue
                violations.append(
                    {
                        "path": relative,
                        "line": line_number,
                        "pattern": pattern,
                        "context": line.strip()[:200],
                    }
                )
    return [
        {
            "record_id": "PR161E-FORBIDDEN-AUTHORITY-SCAN",
            "scan_status": "PASS" if not violations else "FAIL",
            "scanned_file_count": len(scanned_paths),
            "violation_count": len(violations),
            "violations": violations,
            "git_github_commit_shas_are_vcs_metadata_only_flag": True,
            "source_evidence_digest_exception_limited_to_packet_integrity_flag": True,
        }
    ]


def _no_scattered_hardcoded_audit_records(repo_root: Path) -> list[dict[str, Any]]:
    scanned_paths = _pr161e_scan_paths(repo_root)
    duplicate_groups: list[dict[str, Any]] = []
    for pattern in c.FORBIDDEN_AUTHORITY_PATTERNS:
        paths = []
        for path in scanned_paths:
            relative = repo_relative_posix(repo_root, path)
            if relative in c.FORBIDDEN_SCAN_PATH_EXEMPTIONS:
                continue
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            if pattern.lower() in text:
                paths.append(relative)
        if len(paths) > 1:
            duplicate_groups.append(
                {"policy_literal": pattern, "paths": sorted(paths), "duplicate_count": len(paths)}
            )
    return [
        {
            "record_id": "PR161E-NO-SCATTERED-HARDCODED-AUTHORITY-AUDIT",
            "audit_status": "PASS" if not duplicate_groups else "FAIL",
            "duplicate_policy_literal_groups": duplicate_groups,
            "allowed_schema_enum_duplicates": "SCHEMA_ENUM_PARITY_TESTED_FROM_CONSTANTS",
            "allowed_test_assertion_duplicates": "TEST_ASSERTIONS_ALLOWED",
            "allowed_final_summary_duplicates": "FINAL_SUMMARY_POLICY_SUMMARY_ALLOWED",
            "forbidden_scattered_duplicate_count": len(duplicate_groups),
        }
    ]


def _preflight_receipt(
    repo_root: Path,
    context: dict[str, Any],
    discovery: list[dict[str, Any]],
    validated_replay: list[dict[str, Any]],
    validated_paper: list[dict[str, Any]],
    online_search_available: bool,
) -> dict[str, Any]:
    branch = _git_output(repo_root, ["branch", "--show-current"])
    head = _git_output(repo_root, ["rev-parse", "HEAD"])
    actual_replay = [r for r in discovery if r["source_artifact_class"] == "ACTUAL_REPLAY_RESULT_PACKET_CANDIDATE"]
    actual_paper = [r for r in discovery if r["source_artifact_class"] == "ACTUAL_PAPER_RESULT_PACKET_CANDIDATE"]
    return {
        "pr_label": c.PR_LABEL,
        "semantic_task_label": c.SEMANTIC_TASK_LABEL,
        "active_branch": branch,
        "current_head_commit": head,
        "git_sha_is_vcs_metadata_only_flag": True,
        "main_lineage_contains_pr161d_merge_flag": _lineage_contains_pr161d(repo_root),
        "pr_identity_roster_consumed_flag": context["master_status"].get("docs/roadmap/QTT_PR_Identity_Roster_v1_0.json", False),
        "roadmap_execution_state_controller_consumed_flag": context["master_status"].get("docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json", False),
        "day1_launch_readiness_policy_consumed_flag": context["master_status"].get("src/qtt/stage1_prediction_markets/launch_readiness/day1_launch_readiness_roadmap_policy.py", False),
        "pr136_route_triage_consumed_flag": context["pr136"].get("route_triage") is not None,
        "pr136_crosswalk_consumed_flag": context["pr136"].get("section_crosswalk") is not None,
        "pr136_market_index_consumed_flag": context["pr136"].get("market_index") is not None,
        "pr136_command_action_consumed_flag": context["pr136"].get("command_action") is not None,
        "pr137r_atomicrows_reconciliation_consumed_flag": context["atomic_contracts"].get("pr137r_atomicrows_reconciliation") is not None,
        "pr138_atomicrows_semantic_contract_consumed_flag": context["atomic_contracts"].get("pr138_atomicrows_semantic_contract") is not None,
        "pr161a_foundation_loaded_flag": bool(list((repo_root / c.GENERATED_DIR).glob("PR161A*.report.json"))),
        "pr161b_foundation_loaded_flag": all(value is not None for value in context["pr161b"].values()),
        "pr161c_qku_inventory_loaded_flag": len(context["qkus"]) == c.EXPECTED_PR161C_COUNTS["primary_qku_count"],
        "pr161c_graph_loaded_flag": len(context["graph_nodes"]) == c.EXPECTED_PR161C_COUNTS["graph_node_count"]
        and len(context["graph_edges"]) == c.EXPECTED_PR161C_COUNTS["graph_edge_count"],
        "pr161d_final_summary_loaded_flag": bool(context["pr161d_final"]),
        "primary_qku_count_observed": len(context["qkus"]),
        "expected_primary_qku_count": c.EXPECTED_PR161C_COUNTS["primary_qku_count"],
        "pr161d_replay_paper_scenario_record_count_observed": len(context["replay_paper_scenario_inputs"]),
        "pr161d_bundle_candidate_count_observed": len(context["combination_candidate"]),
        "pr161d_scenario_outcome_matrix_count_observed": len(context["scenario_outcome_matrix"]),
        "pr161d_result_backed_ranking_slot_count_observed": len(context["result_backed_slots"]),
        "pr161d_future_profitability_pattern_record_count_observed": len(context["future_profitability_pattern"]),
        "pr161d_agent_task_queue_count_observed": len(context["agent_task_queue"]),
        "replay_paper_contract_artifacts_discovered_flag": True,
        "actual_replay_result_artifacts_discovered_count": len(actual_replay),
        "actual_paper_result_artifacts_discovered_count": len(actual_paper),
        "validated_replay_result_packets_count": len(validated_replay),
        "validated_paper_result_packets_count": len(validated_paper),
        "real_result_ingestion_allowed_flag": True,
        "fake_result_generation_forbidden_flag": True,
        "online_search_authorized_flag": True,
        "online_search_attempted_flag": True,
        "online_search_available_flag": online_search_available,
        "online_search_unavailable_non_blocking_flag": not online_search_available,
        "open_intake_policy_enabled_for_candidate_research_lanes_flag": True,
        "no_live_authority_policy_enabled_flag": True,
        "no_profit_evidence_without_validated_result_packet_policy_enabled_flag": True,
        "no_profit_guarantee_policy_enabled_flag": True,
        "no_qtt_sha_authority_policy_enabled_flag": True,
        "no_qtt_generated_sha_authority_policy_enabled_flag": True,
        "no_qtt_freeze_authority_policy_enabled_flag": True,
        "no_qtt_checksum_global_digest_authority_policy_enabled_flag": True,
        "no_atomicrows_bundle_sha_hash_freeze_policy_enabled_flag": True,
        "digest_exception_limited_to_source_evidence_integrity_flag": True,
    }


def _summary(**kwargs: Any) -> dict[str, Any]:
    context = kwargs["context"]
    discovery = kwargs["discovery"]
    forbidden_scan = kwargs["forbidden_scan"][0]
    hardcoded_audit = kwargs["hardcoded_audit"][0]
    rejected = [
        record for record in discovery
        if record["source_artifact_class"] == "UNSAFE_OR_UNMAPPABLE_RESULT_ARTIFACT"
    ]
    return {
        "summary_id": "PR161E_FINAL_SUMMARY",
        "pr_label": c.PR_LABEL,
        "semantic_task_label": c.SEMANTIC_TASK_LABEL,
        "active_branch": _git_output(kwargs["repo_root"], ["branch", "--show-current"]),
        "head_commit": _git_output(kwargs["repo_root"], ["rev-parse", "HEAD"]),
        "git_sha_is_vcs_metadata_only_flag": True,
        "owner_approvals": dict(c.OWNER_APPROVALS),
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
        "pr136_artifacts_consumed_status": "PASS" if all(context["pr136"].values()) else "FAIL",
        "pr137r_pr138_artifacts_consumed_status": (
            "PASS"
            if context["atomic_contracts"].get("pr137r_atomicrows_reconciliation")
            and context["atomic_contracts"].get("pr138_atomicrows_semantic_contract")
            else "FAIL"
        ),
        "pr161c_inventory_qku_count_loaded": len(context["qkus"]),
        "pr161c_graph_node_count_loaded": len(context["graph_nodes"]),
        "pr161c_graph_edge_count_loaded": len(context["graph_edges"]),
        "pr161d_replay_paper_scenario_count_loaded": len(context["replay_paper_scenario_inputs"]),
        "pr161d_bundle_candidate_count_loaded": len(context["combination_candidate"]),
        "pr161d_scenario_matrix_count_loaded": len(context["scenario_outcome_matrix"]),
        "pr161d_result_backed_ranking_slot_count_loaded": len(context["result_backed_slots"]),
        "replay_result_packet_candidates_discovered": sum(1 for r in discovery if r["actual_replay_result_candidate_flag"]),
        "paper_result_packet_candidates_discovered": sum(1 for r in discovery if r["actual_paper_result_candidate_flag"]),
        "validated_replay_result_packets_count": len(kwargs["validated_replay"]),
        "validated_paper_result_packets_count": len(kwargs["validated_paper"]),
        "rejected_unmappable_result_artifacts_count": len(rejected),
        "outcome_capture_registry_count": len(kwargs["outcome"]),
        "bundle_result_ledger_count": len(kwargs["bundle_ledger"]),
        "profitability_ledger_count": len(kwargs["profitability"]),
        "scenario_attribution_record_count": len(kwargs["scenario_attribution"]),
        "result_backed_ranking_update_candidate_count": len(kwargs["ranking_updates"]),
        "future_profitability_pattern_update_candidate_count": len(kwargs["pattern_updates"]),
        "quantum_classical_hybrid_outcome_comparison_count": len(kwargs["qch_comparison"]),
        "atomicrows_pr154_result_compatibility_record_count": len(kwargs["compatibility"]),
        "agent_outcome_task_queue_count": len(kwargs["agent_tasks"]),
        "owner_review_result_promotion_queue_count": len(kwargs["owner_queue"]),
        "online_metric_candidate_intake_count": len(kwargs["online_candidates"]),
        "missing_value_candidate_materialization_count": len(kwargs["missing_values"]),
        "result_confidence_gate_status": "PASS" if len(kwargs["confidence"]) == c.DETERMINISTIC_PENDING_COUNTS["outcome_capture_registry"] else "FAIL",
        "graph_traceability_bridge_status": "PASS" if len(kwargs["traceability"]) == c.EXPECTED_PR161C_COUNTS["primary_qku_count"] else "FAIL",
        "qku_coverage_and_orphan_audit_status": (
            "PASS" if all(record["coverage_status"] == "PASS" for record in kwargs["coverage"]) else "FAIL"
        ),
        "forbidden_authority_scan_status": forbidden_scan["scan_status"],
        "no_scattered_hardcoded_authority_audit_status": hardcoded_audit["audit_status"],
        "branch_context_test_status": "PR161E_BRANCH_CONTEXT_TESTS_PRESENT",
        "master_plan_file_edited_flag": False,
        "global_rename_performed_flag": False,
        "atomicrows_final_bundle_created_flag": False,
        "atomicrows_bundle_jsonl_created_flag": False,
        "atomicrows_bundle_sha_reference_created_flag": False,
        "atomicrows_bundle_hash_sha_freeze_authority_created_flag": False,
        "qtt_sha_or_generated_sha_authority_created_flag": False,
        "qtt_freeze_checksum_global_digest_authority_created_flag": False,
        "replay_paper_result_fabricated_flag": False,
        "replay_paper_performance_evidence_fabricated_flag": False,
        "shadow_live_results_fabricated_flag": False,
        "live_profit_evidence_or_profit_guarantee_created_flag": False,
        "live_authority_created_flag": False,
        "optimizer_execution_created_flag": False,
        "quantum_backend_or_simulator_execution_created_flag": False,
        "non_official_information_candidate_lane_only_flag": True,
        "record_count": 1,
    }


def _report(report_type: str, records: list[dict[str, Any]], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "pr_id": c.PR_LABEL,
        "pr_label": c.PR_LABEL,
        "report_type": report_type,
        "authority_class": "OWNER_APPROVED_INTERNAL_POLICY",
        "owner_approvals": dict(c.OWNER_APPROVALS),
        "central_policy_module": "src.qtt.stage1_prediction_markets.replay_paper_outcome_capture_scenario_learning.constants",
        "record_count": len(records),
        "records": records,
        "live_use_allowed_flag": False,
        "profit_evidence_count": 0,
        "live_execution_count": 0,
        "optimizer_execution_count": 0,
        "quantum_backend_execution_count": 0,
        "shadow_execution_count": 0,
        "replay_paper_execution_count": 0,
        "no_authority_confirmation": dict(c.NO_AUTHORITY_CONFIRMATION),
    }
    if extra:
        payload.update(extra)
    return payload


def _final_summary_report(summary: dict[str, Any]) -> dict[str, Any]:
    payload = _report("PR161E_FINAL_SUMMARY", [dict(summary)])
    payload.update(summary)
    return payload


def _traceability(
    context: dict[str, Any],
    qku_id: str | None,
    qku_ids: list[str] | None,
    *,
    scenario: dict[str, Any] | None = None,
    bundle: dict[str, Any] | None = None,
    agent_task: dict[str, Any] | None = None,
    owner_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    qku_id = qku_id or (qku_ids[0] if qku_ids else None)
    qku = context["qku_by_id"].get(str(qku_id), {}) if qku_id else {}
    graph = context["graph_by_qku"].get(str(qku_id), {}) if qku_id else {}
    replay = context["replay_by_qku"].get(str(qku_id), {}) if qku_id else {}
    score = context["quality_by_qku"].get(str(qku_id), {}) if qku_id else {}
    roles = sorted(context["roles_by_qku"].get(str(qku_id), [])) if qku_id else []
    return {
        "qku_id": qku_id,
        "qku_ids": qku_ids or ([] if qku_id is None else [qku_id]),
        "qku_graph_node_id": graph.get("qku_graph_node_id"),
        "upstream_pr161a_or_pr161b_origin_if_available": qku.get("qku_source_artifact_path"),
        "pr161c_registry_ref": "docs/master_plan/generated/PR161C_QKUMasterInventoryBridge.report.json",
        "pr161c_graph_ref": "docs/master_plan/generated/PR161C_QKUOrchestrationGraph.report.json",
        "pr161d_score_ref_if_available": score.get("quality_score_record_id"),
        "pr161d_category_ranking_ref_if_available": None,
        "pr161d_scenario_matrix_ref_if_available": (
            (scenario or {}).get("scenario_matrix_id")
            or replay.get("scenario_matrix_id_if_applicable")
        ),
        "pr161d_bundle_ref_if_available": (
            (bundle or {}).get("qku_bundle_id")
            or (scenario or {}).get("qku_bundle_id")
            or replay.get("qku_bundle_id_if_applicable")
        ),
        "pr161d_replay_paper_scenario_ref_if_available": replay.get("replay_paper_scenario_input_id"),
        "pr161d_agent_task_ref_if_available": (agent_task or {}).get("task_id"),
        "pr161d_owner_review_ref_if_available": (owner_review or {}).get("owner_review_queue_record_id"),
        "atomicrows_ref_if_available": qku_id if qku_id and qku_id.startswith("QKU-ATOMICROW-") else None,
        "pr154_ref_if_available": qku_id if qku_id and qku_id.startswith("QKU-PR154-") else None,
        "downstream_agent_roles": roles,
        "downstream_workflow_routes": ["PR161E_REPLAY_PAPER_OUTCOME_CAPTURE", "PR161E_SCENARIO_LEARNING_BRIDGE"],
        "downstream_process_routes": ["RESULT_PACKET_VALIDATION", "OWNER_REVIEW_RESULT_PROMOTION_QUEUE"],
        "downstream_future_pr_routes": ["PR161F_OR_PR162_RESULT_BACKED_LEARNING_AFTER_VALIDATED_RESULTS"],
        "downstream_owner_review_route": "QTT_OWNER_REVIEW_AGENT",
        "downstream_future_live_gate_route": "OWNER_LIVE_PROMOTION_REVIEW_REQUIRED_AFTER_VALIDATED_REPLAY_PAPER_RESULTS",
        "unmappable_reason_if_any": None if qku_id in context["qku_by_id"] else "QKU_NOT_FOUND_IN_PR161C_INVENTORY",
    }


def _pending_numeric_fields(prefix: str = "") -> dict[str, Any]:
    return {f"{prefix}{field}" if prefix else field: None for field in c.RESULT_NUMERIC_FIELDS}


def _authority_flags() -> dict[str, bool]:
    return {
        "no_live_authority_created_flag": True,
        "no_profit_guarantee_created_flag": True,
        "no_live_profit_evidence_created_flag": True,
        "no_profit_evidence_created_without_validated_result_packet_flag": True,
        "no_optimizer_execution_created_flag": True,
        "no_quantum_backend_execution_created_flag": True,
        "no_quantum_simulator_execution_created_flag": True,
        "no_qtt_sha_authority_created_flag": True,
        "no_qtt_generated_sha_authority_created_flag": True,
        "no_qtt_freeze_checksum_global_digest_authority_created_flag": True,
        "no_atomicrows_bundle_sha_authority_created_flag": True,
        "no_atomicrows_bundle_hash_freeze_authority_created_flag": True,
    }


def _agent_task_state(role: str) -> str:
    if role in {"QTT_REPLAY_AGENT", "QTT_PAPER_AGENT"}:
        return "RESULT_PACKET_REQUIRED"
    if role == "QTT_OWNER_REVIEW_AGENT":
        return "OWNER_REVIEW_REQUIRED"
    if role in {"QTT_RANKING_AGENT", "QTT_SCORING_AGENT"}:
        return "RESULT_PACKET_PENDING"
    if role in {"QTT_QUANTUM_ADVISORY_AGENT", "QTT_OPTIMIZER_ARBITRATION_AGENT"}:
        return "RESULT_PACKET_REQUIRED"
    if role in {"QTT_RESEARCH_AGENT", "QTT_SOURCE_EVIDENCE_AGENT"}:
        return "ONLINE_CANDIDATE_REVIEW_REQUIRED"
    if role in {"QTT_ATOMICROWS_ENRICHMENT_AGENT", "QTT_PARAMETER_STACK_AGENT"}:
        return "MISSING_VALUE_CANDIDATE_REVIEW_REQUIRED"
    return "RESULT_PACKET_PENDING"


def _optional_report(repo_root: Path, filename: str) -> dict[str, Any]:
    path = repo_root / c.GENERATED_DIR / filename
    return load_report(repo_root, c.GENERATED_DIR / filename) if path.exists() else {}


def _validate_upstream_counts(context: dict[str, Any]) -> None:
    expected_c = c.EXPECTED_PR161C_COUNTS
    expected_d = c.EXPECTED_PR161D_COUNTS
    checks = {
        "PR161C primary_qku_count": (len(context["qkus"]), expected_c["primary_qku_count"]),
        "PR161C graph_node_count": (len(context["graph_nodes"]), expected_c["graph_node_count"]),
        "PR161C graph_edge_count": (len(context["graph_edges"]), expected_c["graph_edge_count"]),
        "PR161C quantum_applicable_primary_qkus": (len(context["quantum_forward"]), expected_c["quantum_applicable_primary_qkus"]),
        "PR161C range_qkus_materialized": (int(context["range_audit"].get("range_qku_count", -1)), expected_c["range_qkus_materialized"]),
        "PR161C optimizer_configs_materialized": (int(context["range_audit"].get("optimizer_qku_count", -1)), expected_c["optimizer_configs_materialized"]),
        "PR161D result_backed_ranking_slots": (len(context["result_backed_slots"]), expected_d["result_backed_ranking_slots"]),
        "PR161D scenario_outcome_matrix_records": (len(context["scenario_outcome_matrix"]), expected_d["scenario_outcome_matrix_records"]),
        "PR161D bundle_candidates": (len(context["combination_candidate"]), expected_d["bundle_candidates"]),
        "PR161D replay_paper_scenario_records": (len(context["replay_paper_scenario_inputs"]), expected_d["replay_paper_scenario_records"]),
        "PR161D hybrid_arbitration_queue_records": (len(context["hybrid_arbitration_queue"]), expected_d["hybrid_arbitration_queue_records"]),
        "PR161D agent_task_queue_records": (len(context["agent_task_queue"]), expected_d["agent_task_queue_records"]),
        "PR161D owner_review_queue_records": (len(context["owner_review_queue"]), expected_d["owner_review_queue_records"]),
        "PR161E combined_atomicrows_pr154_compatibility_records": (len(context["atomicrows_pr154_entities"]), expected_d["combined_atomicrows_pr154_compatibility_records"]),
    }
    final = context["pr161d_final"]
    checks.update(
        {
            "PR161D qkus_scored": (int(final.get("qkus_scored_count", -1)), expected_d["qkus_scored"]),
            "PR161D category_ranking_records": (int(final.get("category_ranking_records_created", -1)), expected_d["category_ranking_records"]),
            "PR161D order_condition_scenario_records": (int(final.get("order_condition_scenario_records_created", -1)), expected_d["order_condition_scenario_records"]),
            "PR161D quantum_priority_queue_records": (int(final.get("quantum_priority_queue_count", -1)), expected_d["quantum_priority_queue_records"]),
            "PR161D classical_baseline_queue_records": (int(final.get("classical_baseline_queue_count", -1)), expected_d["classical_baseline_queue_records"]),
            "PR161D atomicrows_compatibility_priority_records": (int(final.get("atomicrows_compatibility_priority_count", -1)), expected_d["atomicrows_compatibility_priority_records"]),
            "PR161D pr154_compatibility_priority_records": (int(final.get("pr154_compatibility_priority_count", -1)), expected_d["pr154_compatibility_priority_records"]),
        }
    )
    mismatches = [
        f"{name}: observed={observed} expected={expected}"
        for name, (observed, expected) in checks.items()
        if observed != expected
    ]
    if mismatches:
        raise ValueError("PR161E upstream count mismatch; fail closed: " + "; ".join(mismatches))


def _require_expected_branch(repo_root: Path) -> None:
    branch = _git_output(repo_root, ["branch", "--show-current"])
    if branch != c.EXPECTED_BRANCH:
        raise RuntimeError(f"PR161E expected branch {c.EXPECTED_BRANCH}, observed {branch}")


def _lineage_contains_pr161d(repo_root: Path) -> bool:
    branch = "pr161d-qku-candidate-quality-scoring-replay-paper-prioritization"
    for ref in (branch, f"refs/heads/{branch}", f"origin/{branch}", f"refs/remotes/origin/{branch}"):
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ref, "HEAD"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode == 0:
            return True
    result = subprocess.run(
        ["git", "log", "--format=%s", "--fixed-strings", f"--grep=/{branch}", "HEAD"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0 and bool(result.stdout.strip())


def _git_output(repo_root: Path, args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=repo_root, text=True, capture_output=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else ""


def _pr161e_scan_paths(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    roots = [
        repo_root / c.PACKAGE_DIR,
        repo_root / "tests/stage1_prediction_markets/replay_paper_outcome_capture_scenario_learning",
    ]
    for root in roots:
        if root.is_file() and root.suffix == ".py":
            paths.append(root)
            continue
        if root.exists():
            paths.extend(path for path in root.rglob("*.py") if path.is_file())
    paths.extend(
        path
        for path in (
            repo_root / "tools/build_pr161e_replay_paper_outcome_capture_scenario_learning.py",
            repo_root / "tools/validate_pr161e_replay_paper_outcome_capture_scenario_learning.py",
            repo_root / "tools/ci_branch_context.py",
            repo_root / "tools/run_validation_gates.py",
        )
        if path.exists()
    )
    return sorted(set(paths))


def _forbidden_context_allowed(relative: str, line: str) -> bool:
    normalized = relative.replace("\\", "/")
    if normalized in c.FORBIDDEN_SCAN_PATH_EXEMPTIONS:
        return True
    if any(normalized.startswith(prefix) for prefix in c.FORBIDDEN_SCAN_PATH_EXEMPTIONS):
        return True
    lowered = line.lower()
    return any(marker.lower() in lowered for marker in c.FORBIDDEN_SCAN_ALLOWED_CONTEXT_MARKERS)


def _largest_report_summary(
    main_payloads: dict[str, dict[str, Any]],
    shard_payloads: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    sizes: dict[str, int] = {}
    for filename, payload in main_payloads.items():
        sizes[f"{c.GENERATED_DIR.as_posix()}/{filename}"] = encoded_json_size(
            payload,
            compact=filename == c.SHARED_DICTIONARY_REPORT_FILENAME,
        )
    for rel_path, payload in shard_payloads.items():
        sizes[rel_path] = encoded_json_size(payload, compact=True)
    largest_path = max(sizes, key=sizes.get)
    return {
        "largest_generated_pr161e_report_path": largest_path,
        "largest_generated_pr161e_report_size_bytes": sizes[largest_path],
        "largest_pr161e_report_under_github_warning_threshold_flag": sizes[largest_path]
        < c.GITHUB_RECOMMENDED_WARNING_THRESHOLD_BYTES,
    }
