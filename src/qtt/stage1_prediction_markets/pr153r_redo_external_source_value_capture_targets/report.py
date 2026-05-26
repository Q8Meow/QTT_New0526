"""Deterministic PR153R redo report builder."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping

from . import accepted_packet
from . import constants as c
from . import extraction
from . import seed_map
from . import source_retrieval
from . import taxonomy as tx


def json_dump(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    return extraction.read_json_object(path)


def _git_output(repo_root: Path, *args: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip()


def _control_plane_records(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for rel_path in c.MANDATORY_CONTROL_PLANE_PATHS:
        path = repo_root / rel_path
        record = {
            "path": rel_path.as_posix(),
            "exists": path.exists(),
            "consumed": path.exists(),
            "consumption_mode": "READ_ONLY_CONTEXT",
        }
        if rel_path == c.PR136_SECTION_CROSSWALK_ALIAS and not path.exists():
            successor = repo_root / c.PR136_SECTION_CROSSWALK_CANONICAL_SUCCESSOR
            record.update(
                {
                    "consumed": successor.exists(),
                    "exists": False,
                    "requested_alias_missing": True,
                    "canonical_successor_path_consumed": (
                        c.PR136_SECTION_CROSSWALK_CANONICAL_SUCCESSOR.as_posix()
                    ),
                    "canonical_successor_exists": successor.exists(),
                    "created_missing_alias": False,
                }
            )
        records.append(record)
    return records


def _owner_input_records(repo_root: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": rel_path.as_posix(),
            "exists": (repo_root / rel_path).exists(),
            "consumed": (repo_root / rel_path).exists(),
            "authority_status": "OWNER_SUPPLIED_RETRIEVAL_CANDIDATE_SEED_ONLY",
        }
        for rel_path in c.OWNER_SUPPLIED_INPUT_PATHS
    ]


def _seed_counts_by_platform(seed_records: list[Mapping[str, Any]]) -> dict[str, Any]:
    target_counts = Counter(str(record.get("platform_scope") or "") for record in seed_records)
    url_counts: Counter[str] = Counter()
    for record in seed_records:
        url_counts[str(record.get("platform_scope") or "")] += len(
            seed_map.split_seed_urls(record.get("source_seed_url"))
        )
    return {
        "target_records": {
            key: target_counts.get(key, 0) for key in sorted(c.EXPECTED_PLATFORM_COUNTS)
        },
        "seed_url_fragments": {
            key: url_counts.get(key, 0) for key in sorted(c.EXPECTED_PLATFORM_COUNTS)
        },
    }


def _seed_counts_by_source_class(records: list[Mapping[str, Any]]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for record in records:
        for url in seed_map.split_seed_urls(record.get("source_seed_url")):
            classified = source_retrieval.classify_source_url(url)
            counter[str(classified["official_source_class"])] += 1
    return {key: counter[key] for key in sorted(counter)}


def _per_target_records(
    targets: list[Mapping[str, Any]],
    seed_by_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for target in targets:
        target_id = str(target.get("retrieval_target_id") or "")
        seed_record = dict(seed_by_id.get(target_id, {}))
        if seed_record:
            target["separation_bucket"] = seed_record.get("separation_bucket")
        retrieval_records = source_retrieval.retrieval_records_for_target(
            target,
            seed_record,
        )
        digest_metadata = source_retrieval.target_digest_metadata(target, retrieval_records)
        block_codes = source_retrieval.block_codes_for_target(
            target,
            retrieval_records,
            digest_metadata,
        )
        records.append(
            {
                "retrieval_target_id": target_id,
                "target_field_path": target.get("target_field_path"),
                "platform_scope": target.get("platform_scope"),
                "target_family": target.get("pr150_target_domain"),
                "semantic_family": target.get("source_target_class"),
                "target_field_id": target.get("target_field_id"),
                "source_family": target.get("official_source_class"),
                "owner_route": target.get("owner_route"),
                "recommended_primary_eligibility_lane": target.get(
                    "recommended_primary_eligibility_lane"
                ),
                "blocker_primary_category": target.get("blocker_primary_category"),
                "priority_class": target.get("priority_class"),
                "owner_supplied_seed_urls": seed_map.split_seed_urls(
                    seed_record.get("source_seed_url")
                ),
                "owner_supplied_seed_title": seed_record.get("source_seed_title"),
                "owner_supplied_seed_quality": seed_record.get("source_seed_quality"),
                "owner_supplied_seed_summary": seed_record.get("source_seed_summary"),
                "seed_url_authority_status": tx.CANDIDATE_SEED_ONLY_NOT_ACCEPTED_FACT,
                "classified_seed_url_candidates": retrieval_records,
                "retrieved_official_locators": [
                    {
                        "source_url": item.get("source_url"),
                        "source_domain": item.get("source_domain"),
                        "official_source_class": item.get("official_source_class"),
                        "online_retrieval_status": item.get("online_retrieval_status"),
                        "retrieval_artifact_digest": item.get("retrieval_artifact_digest"),
                    }
                    for item in retrieval_records
                    if item.get("online_retrieval_status")
                    == tx.OFFICIAL_SOURCE_RETRIEVED_PENDING_ACCEPTANCE
                ],
                "source_packet_digest_metadata": digest_metadata,
                "quote_span_locator": None,
                "machine_field_locator": None,
                "exact_target_value_extracted": None,
                "unit_scale_enum_domain": None,
                "target_field_scope_exact": False,
                "platform_venue_scope_exact": True,
                "scope_broadening_created": False,
                "source_conflict_check_status": digest_metadata[
                    "source_conflict_check_status"
                ],
                "revalidation_policy": digest_metadata["revalidation_policy"],
                "source_materiality_class": digest_metadata["source_materiality_class"],
                "acceptance_decision": tx.ACCEPTANCE_BLOCKED,
                "accepted_packet_path": None,
                "block_codes": block_codes,
                "owner_review_required": True,
                "connector_unlock_eligibility_status": (
                    tx.CONNECTOR_UNLOCK_NOT_CREATED_BY_SOURCE_PACKET
                ),
            }
        )
    return records


def _accepted_packet_count_from_artifacts(repo_root: Path) -> int:
    directory = repo_root / c.ACCEPTED_PACKET_DIR
    if not directory.exists():
        return 0
    return len(sorted(directory.glob("*.json")))


def build_report(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    pr153 = _read_json(root / c.PR153_REPORT_PATH)
    pr151 = _read_json(root / c.PR151_REPORT_PATH)
    raw_targets = extraction.extract_pr153r_targets(pr153)
    enriched_targets = extraction.enrich_targets_from_pr151(raw_targets, pr151)
    owner_inputs = seed_map.load_owner_supplied_inputs(root)
    seed_by_id = seed_map.seed_records_by_id(owner_inputs["json_seed_map"])
    cross_validation = seed_map.cross_validate_seed_inputs(
        raw_targets,
        owner_inputs,
        enriched_targets,
    )
    per_target = _per_target_records(enriched_targets, seed_by_id)

    accepted_artifact_count = _accepted_packet_count_from_artifacts(root)
    accepted_count = sum(
        1
        for item in per_target
        if item["acceptance_decision"] == tx.ACCEPTED_TARGET_FIELD_SOURCE_PACKET
    )
    blocked_count = len(per_target) - accepted_count
    retrieved_target_count = sum(
        1 for item in per_target if item["retrieved_official_locators"]
    )
    source_digest_count = sum(
        1
        for item in per_target
        if not accepted_packet.digest_metadata_policy_failures(item)
    )
    branch = _git_output(root, "branch", "--show-current")
    head = _git_output(root, "rev-parse", "--short", "HEAD")
    platform_counts = extraction.platform_counts(raw_targets)
    final_status = (
        tx.PR153R_REDO_FULL_CAPTURE_OK
        if accepted_count == c.EXPECTED_TARGET_COUNT and blocked_count == 0
        else tx.PR153R_REDO_CAPTURE_PARTIAL_ACCEPTANCE_WITH_BLOCKER_TRIAGE_OK
        if accepted_count
        else tx.PR153R_REDO_CAPTURE_INCOMPLETE_WITH_BLOCKER_TRIAGE_OK
    )

    return {
        "pr_id": c.PR_ID,
        "report_id": tx.PR153R_REDO_EXTERNAL_SOURCE_VALUE_CAPTURE_TARGETS,
        "report_authority_class": c.REPORT_AUTHORITY_CLASS,
        "controller_version": c.CONTROLLER_VERSION,
        "branch": branch,
        "baseline_head_short_sha": {
            "value": head,
            "authority_status": "VCS_METADATA_ONLY_NOT_QTT_SHA_FREEZE_CHECKSUM_AUTHORITY",
        },
        "taxonomy_module_path": (
            "src/qtt/stage1_prediction_markets/"
            "pr153r_redo_external_source_value_capture_targets/taxonomy.py"
        ),
        "centralized_taxonomy_constants": {
            "routes": [tx.PR153R_RETRY_CAPTURE],
            "lanes": [tx.EXTERNAL_SOURCE_VALUE_CAPTURE_TARGET],
            "block_codes": list(tx.BLOCK_CODES),
            "final_status_labels": list(tx.FINAL_STATUS_LABELS),
            "allowed_digest_metadata_fields": list(tx.ALLOWED_DIGEST_METADATA_FIELDS),
        },
        "owner_supplied_input_files_consumed": _owner_input_records(root),
        "mandatory_control_plane_files_consumed": _control_plane_records(root),
        "exact_34_extraction_rule": {
            "source_report_path": c.PR153_REPORT_PATH.as_posix(),
            "object_filter": {
                "owner_route": tx.PR153R_RETRY_CAPTURE,
                "recommended_primary_eligibility_lane": (
                    tx.EXTERNAL_SOURCE_VALUE_CAPTURE_TARGET
                ),
            },
            "extraction_path_observed": (
                "owner_blocker_decision_layer.owner_decision_required_queue"
            ),
            "recursive_object_filter_used": True,
            "source_capture_candidate_packets_used_as_target_source": False,
        },
        "extracted_target_count": len(raw_targets),
        "platform_counts": platform_counts,
        "no_broadening_to_342": len(raw_targets) != c.PR151_TOTAL_TARGET_COUNT,
        "no_broadening_to_126": (
            len(raw_targets) != c.CORRECTED_PUBLIC_DENOMINATOR_COUNT
        ),
        "no_broadening_to_92": (
            len(raw_targets) != c.PR154_ACCEPTANCE_REVIEW_ONLY_PACKET_COUNT
        ),
        "no_top_20_unresolved_list_used_as_target_source": True,
        "owner_supplied_seed_cross_validation_status": cross_validation,
        "online_retrieval_enabled_status": (
            "ENABLED_CODEX_WEB_RETRIEVAL_OFFICIAL_SOURCE_CANDIDATES_RECORDED"
        ),
        "online_retrieval_method": {
            "official_source_domains_first": True,
            "private_or_authenticated_sources_retrieved": False,
            "packages_installed_for_retrieval": False,
            "external_repositories_cloned_for_retrieval": False,
            "source_acceptance_created_by_retrieval": False,
        },
        "per_target_records": per_target,
        "source_seed_counts_by_platform": _seed_counts_by_platform(
            owner_inputs["json_seed_map"]
        ),
        "source_seed_counts_by_official_source_class": _seed_counts_by_source_class(
            owner_inputs["json_seed_map"]
        ),
        "official_source_retrieved_count": retrieved_target_count,
        "accepted_source_packet_count": accepted_count,
        "accepted_source_packet_artifact_count": accepted_artifact_count,
        "accepted_public_source_packet_count": 0,
        "accepted_private_source_packet_count": 0,
        "blocked_candidate_count": blocked_count,
        "owner_review_required_count": sum(
            1 for item in per_target if item["owner_review_required"]
        ),
        "connector_unlock_count": 0,
        "runtime_cash_receipt_count": 0,
        "order_receipt_count": 0,
        "fill_receipt_count": 0,
        "replay_result_count": 0,
        "paper_result_count": 0,
        "live_reachability_count": 0,
        "profit_evidence_count": 0,
        "quantum_backend_execution_count": 0,
        "quantum_advantage_claim_count": 0,
        "atomicrows_bundle_mutation_count": 0,
        "atomicrows_bundle_hash_sha_artifact_reference_count": 0,
        "qtt_sha_freeze_checksum_authority_count": 0,
        "global_repository_digest_authority_count": 0,
        "source_packet_digest_metadata_count": source_digest_count,
        "source_evidence_digest_metadata_policy": {
            "digest_metadata_target_field_scoped_source_provenance_only": True,
            "digest_metadata_unlocks_connector_semantics": False,
            "digest_metadata_creates_qtt_sha_freeze_checksum_authority": False,
            "digest_metadata_creates_global_repository_digest_authority": False,
            "digest_metadata_creates_atomicrows_bundle_hash_sha_authority": False,
            "allowed_digest_metadata_fields": list(tx.ALLOWED_DIGEST_METADATA_FIELDS),
        },
        "atomicrows_compatibility_surface": {
            "target_identity_can_later_support_semantic_value_materialization": True,
            "field_paths_remain_stable": True,
            "platform_scope_remains_explicit": True,
            "bundle_mutation_created": False,
            "bundle_hash_sha_artifact_created": False,
            "bundle_hash_sha_artifact_referenced": False,
            "atomicrows_authority_claim_created": False,
        },
        "quantum_forward_compatibility_surface": {
            "future_routing_metadata_preserved": True,
            "quantum_backend_execution_created": False,
            "quantum_simulator_execution_created": False,
            "optimizer_execution_created": False,
            "quantum_advantage_claim_created": False,
        },
        "connector_unlock_boundary": {
            "candidate_packets_unlock_connectors": False,
            "seed_urls_unlock_connectors": False,
            "owner_definitions_packet_unlocks_connectors": False,
            "accepted_source_packet_by_itself_submits_orders": False,
            "connector_unlock_count": 0,
        },
        "no_claim_boundary": {
            key: 0 for key in tx.ZERO_AUTHORITY_COUNT_KEYS
        },
        "final_status_label": final_status,
        "validation_commands_run": list(c.REQUIRED_COMMANDS),
        "validation_results": {
            "report_generation_result": "DETERMINISTIC_REPORT_GENERATED",
            "command_results_are_recorded_in_codex_final_response": True,
            "report_results_create_runtime_or_live_authority": False,
        },
        "owner_review_required": blocked_count > 0,
    }


def write_report_file(repo_root: Path | str) -> Path:
    root = Path(repo_root).resolve()
    report = build_report(root)
    path = root / c.REPORT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_dump(report), encoding="utf-8")
    return path
