from __future__ import annotations

import json
from pathlib import Path

from src.qtt.stage1_prediction_markets.pr153r_redo_external_source_value_capture_targets import (
    accepted_packet,
    constants as c,
    extraction,
    report as report_builder,
    seed_map,
    taxonomy as tx,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _pr153_extracted_targets():
    pr153 = _read_json(REPO_ROOT / c.PR153_REPORT_PATH)
    return extraction.extract_pr153r_targets(pr153)


def _report():
    return _read_json(REPO_ROOT / c.REPORT_PATH)


def test_exact_34_extraction_from_pr153_report():
    targets = _pr153_extracted_targets()

    assert len(targets) == 34
    assert extraction.platform_counts(targets) == {
        "FORECASTEX_IBKR": 16,
        "KALSHI": 10,
        "POLYMARKET": 8,
    }
    assert {
        target["owner_route"] for target in targets
    } == {tx.PR153R_RETRY_CAPTURE}
    assert {
        target["recommended_primary_eligibility_lane"] for target in targets
    } == {tx.EXTERNAL_SOURCE_VALUE_CAPTURE_TARGET}


def test_owner_supplied_seed_files_have_exact_34_and_match_pr153_extraction():
    owner_inputs = seed_map.load_owner_supplied_inputs(REPO_ROOT)
    extracted = _pr153_extracted_targets()
    expected_ids = {target["retrieval_target_id"] for target in extracted}

    assert {name: len(records) for name, records in owner_inputs.items()} == {
        "json_seed_map": 34,
        "csv_seed_map": 34,
        "extracted_lane_json": 34,
    }
    for records in owner_inputs.values():
        assert {record["retrieval_target_id"] for record in records} == expected_ids


def test_owner_supplied_seed_cross_validation_passes():
    owner_inputs = seed_map.load_owner_supplied_inputs(REPO_ROOT)
    pr151 = _read_json(REPO_ROOT / c.PR151_REPORT_PATH)
    extracted = _pr153_extracted_targets()
    enriched = extraction.enrich_targets_from_pr151(extracted, pr151)

    result = seed_map.cross_validate_seed_inputs(extracted, owner_inputs, enriched)

    assert result["status"] == "PASSED"
    assert result["target_count"] == 34
    assert result["platform_counts"] == c.EXPECTED_PLATFORM_COUNTS
    assert result["no_duplicate_target_ids"] is True
    assert result["no_duplicate_field_paths_unless_platform_separated"] is True


def test_no_broadening_to_pr151_public_denominator_pr154_or_top20():
    report = _report()
    pr151 = _read_json(REPO_ROOT / c.PR151_REPORT_PATH)
    pr153 = _read_json(REPO_ROOT / c.PR153_REPORT_PATH)

    assert len(pr151["official_source_retrieval_target_queue"]) == 342
    assert report["no_broadening_to_342"] is True
    assert report["no_broadening_to_126"] is True
    assert report["no_broadening_to_92"] is True
    assert report["no_top_20_unresolved_list_used_as_target_source"] is True
    top20 = pr153["capture_blocker_category_summary"]["top_20_unresolved_p0_p1_targets"]
    assert len(top20) == 20
    assert len(report["per_target_records"]) == 34
    assert {
        target["retrieval_target_id"] for target in report["per_target_records"]
    } != {target["retrieval_target_id"] for target in top20}


def test_seed_urls_are_candidate_hints_only_not_accepted_facts():
    report = _report()

    assert report["accepted_source_packet_count"] == 0
    assert report["blocked_candidate_count"] == 34
    for record in report["per_target_records"]:
        assert record["seed_url_authority_status"] == (
            tx.CANDIDATE_SEED_ONLY_NOT_ACCEPTED_FACT
        )
        assert record["acceptance_decision"] == tx.ACCEPTANCE_BLOCKED
        assert record["accepted_packet_path"] is None
        assert tx.BLOCK_OWNER_REVIEW_REQUIRED in record["block_codes"]


def test_accepted_packets_require_exact_source_scope_and_revalidation_fields():
    failures = accepted_packet.validate_accepted_packet(
        {
            "retrieval_target_id": "target",
            "target_field_path": "path.a",
            "platform_scope": "KALSHI",
            "official_source_class": "OFFICIAL_API_DOCS",
            "official_source_locator": "https://docs.kalshi.com/example",
            "target_value": "value",
            "unit_scale_enum_domain": "exact",
            "target_field_scope": "path.a",
            "platform_venue_scope": "KALSHI",
            "conflict_check_status": "CLEAR",
            "revalidation_policy": "P1D",
            "source_materiality_class": "CONNECTOR_BLOCKING",
            "source_packet_integrity_digest": "abc123",
        }
    )

    assert tx.BLOCK_MISSING_QUOTE_SPAN_OR_MACHINE_FIELD_LOCATOR in failures


def test_digest_metadata_is_target_field_scoped_source_provenance_only():
    report = _report()
    for record in report["per_target_records"]:
        assert accepted_packet.digest_metadata_policy_failures(record) == []
        metadata = record["source_packet_digest_metadata"]
        assert metadata["scope_type"] == "TARGET_FIELD_SOURCE_PROVENANCE"
        assert metadata["digest_authority_class"] == (
            "SOURCE_PROVENANCE_ONLY_NOT_QTT_NOT_GLOBAL_NOT_ATOMICROWS"
        )

    malformed = {
        "source_packet_digest_metadata": {
            "scope_type": "GLOBAL_REPOSITORY",
            "digest_authority_class": "GLOBAL_REPOSITORY_DIGEST_AUTHORITY",
            "source_packet_integrity_digest": "digest",
        }
    }
    assert accepted_packet.digest_metadata_policy_failures(malformed)


def test_no_qtt_global_atomicrows_connector_runtime_profit_or_quantum_authority():
    report = _report()

    for key in tx.ZERO_AUTHORITY_COUNT_KEYS:
        assert report[key] == 0
    assert report["connector_unlock_count"] == 0
    assert report["accepted_source_packet_count"] == 0
    assert report["accepted_private_source_packet_count"] == 0
    assert report["atomicrows_compatibility_surface"]["bundle_mutation_created"] is False
    assert (
        report["atomicrows_compatibility_surface"][
            "bundle_hash_sha_artifact_referenced"
        ]
        is False
    )
    assert (
        report["source_evidence_digest_metadata_policy"][
            "digest_metadata_creates_qtt_sha_freeze_checksum_authority"
        ]
        is False
    )
    assert (
        report["source_evidence_digest_metadata_policy"][
            "digest_metadata_creates_global_repository_digest_authority"
        ]
        is False
    )
    assert (
        report["quantum_forward_compatibility_surface"][
            "quantum_backend_execution_created"
        ]
        is False
    )


def test_taxonomy_constants_are_centralized_and_report_uses_known_block_codes():
    report = _report()

    assert tx.PR153R_REDO_EXTERNAL_SOURCE_VALUE_CAPTURE_TARGETS
    assert tx.PR153R_RETRY_CAPTURE
    assert tx.EXTERNAL_SOURCE_VALUE_CAPTURE_TARGET
    assert report["taxonomy_module_path"].endswith("/taxonomy.py")
    assert set(report["centralized_taxonomy_constants"]["block_codes"]) == set(
        tx.BLOCK_CODES
    )
    for record in report["per_target_records"]:
        assert set(record["block_codes"]).issubset(set(tx.BLOCK_CODES))


def test_report_generation_is_deterministic_across_repeated_runs():
    first = report_builder.json_dump(report_builder.build_report(REPO_ROOT))
    second = report_builder.json_dump(report_builder.build_report(REPO_ROOT))
    tracked = (REPO_ROOT / c.REPORT_PATH).read_text(encoding="utf-8")

    assert first == second
    assert first == tracked


def test_validation_gate_integration_includes_pr153r_redo_if_touched():
    from tools import run_validation_gates

    commands = run_validation_gates.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    assert "validate_pr153r_redo_external_source_value_capture_targets.py" in command_names
