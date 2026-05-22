"""Deterministic PR138 fixture collection builder."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import constants as c
from .schema import json_dump


def _fixture(
    fixture_id: str,
    *,
    payload_type: str,
    mutation: dict[str, Any] | None,
    expected_reason_codes: list[str] | None = None,
    polarity: str = "INVALID_NEGATIVE_EXPECTED_FAIL",
) -> dict[str, Any]:
    return {
        "expected_reason_codes": expected_reason_codes or [],
        "fixture_id": fixture_id,
        "fixture_polarity": polarity,
        "mutation": mutation or {},
        "payload_type": payload_type,
    }


def build_fixture_collection() -> dict[str, Any]:
    fixtures = [
        _fixture(
            "valid_minimal_semantic_contract_inventory",
            payload_type="contract",
            mutation=None,
            polarity="VALID_POSITIVE",
        ),
        _fixture(
            "valid_report_no_claim_boundary",
            payload_type="report",
            mutation=None,
            polarity="VALID_POSITIVE",
        ),
        _fixture(
            "invalid_missing_required_field",
            payload_type="contract",
            mutation={"operation": "remove_field", "field_id": "row_id"},
            expected_reason_codes=[c.PR138_REASON_REQUIRED_FIELD_MISSING],
        ),
        _fixture(
            "invalid_missing_field_group",
            payload_type="contract",
            mutation={"operation": "remove_field_group", "field_group_id": "IDENTITY"},
            expected_reason_codes=[c.PR138_REASON_REQUIRED_FIELD_GROUP_MISSING],
        ),
        _fixture(
            "invalid_duplicate_field",
            payload_type="contract",
            mutation={"operation": "duplicate_field", "field_id": "row_id"},
            expected_reason_codes=[c.PR138_REASON_FIELD_DUPLICATE],
        ),
        _fixture(
            "invalid_duplicate_field_group",
            payload_type="contract",
            mutation={"operation": "duplicate_field_group", "field_group_id": "IDENTITY"},
            expected_reason_codes=[c.PR138_REASON_FIELD_GROUP_DUPLICATE],
        ),
        _fixture(
            "invalid_forbidden_venue_alias_as_accepted_value",
            payload_type="contract",
            mutation={
                "operation": "append_accepted_market_scope",
                "accepted_value": "FORECASTX",
                "field_id": "venue_scope",
            },
            expected_reason_codes=[c.PR138_REASON_FORBIDDEN_VENUE_ALIAS],
        ),
        _fixture(
            "invalid_live_use_allowed_flag_true",
            payload_type="report",
            mutation={"operation": "set_default_flag", "field": "live_use_allowed_flag", "value": True},
            expected_reason_codes=[c.PR138_REASON_LIVE_USE_FLAG_TRUE_FORBIDDEN],
        ),
        _fixture(
            "invalid_order_authority_created_flag_true",
            payload_type="report",
            mutation={
                "operation": "set_default_flag",
                "field": "order_authority_created_flag",
                "value": True,
            },
            expected_reason_codes=[c.PR138_REASON_ORDER_AUTHORITY_FLAG_TRUE_FORBIDDEN],
        ),
        _fixture(
            "invalid_profit_evidence_created_flag_true",
            payload_type="report",
            mutation={
                "operation": "set_default_flag",
                "field": "profit_evidence_created_flag",
                "value": True,
            },
            expected_reason_codes=[c.PR138_REASON_PROFIT_EVIDENCE_FLAG_TRUE_FORBIDDEN],
        ),
        _fixture(
            "invalid_quantum_backend_execution_allowed_flag_true",
            payload_type="report",
            mutation={
                "operation": "set_default_flag",
                "field": "quantum_backend_execution_allowed_flag",
                "value": True,
            },
            expected_reason_codes=[c.PR138_REASON_QUANTUM_BACKEND_EXECUTION_FLAG_TRUE_FORBIDDEN],
        ),
        _fixture(
            "invalid_external_fact_authority_flag_true",
            payload_type="report",
            mutation={
                "operation": "set_default_flag",
                "field": "external_fact_authority_flag",
                "value": True,
            },
            expected_reason_codes=[
                c.PR138_REASON_EXTERNAL_FACT_AUTHORITY_TRUE_FORBIDDEN_WITHOUT_ACCEPTED_SOURCE_PACKET
            ],
        ),
        _fixture(
            "invalid_scattered_reason_code_not_present_in_centralized_constants",
            payload_type="contract",
            mutation={
                "operation": "append_reason_code",
                "field_id": "row_id",
                "reason_code": "PR138_REASON_SCATTERED_NOT_CENTRALIZED",
            },
            expected_reason_codes=[c.PR138_REASON_REASON_CODE_NOT_CENTRALIZED],
        ),
        _fixture(
            "invalid_missing_authority_boundary_metadata",
            payload_type="contract",
            mutation={"operation": "remove_field_key", "field_id": "row_id", "key": "authority_boundary"},
            expected_reason_codes=[c.PR138_REASON_FIELD_WITHOUT_AUTHORITY_BOUNDARY],
        ),
        _fixture(
            "invalid_missing_future_pr_phase_metadata",
            payload_type="contract",
            mutation={"operation": "remove_field_key", "field_id": "row_id", "key": "future_enrichment_phase"},
            expected_reason_codes=[c.PR138_REASON_FUTURE_PHASE_MISSING],
        ),
        _fixture(
            "invalid_missing_crosswalk_trace_metadata_if_required",
            payload_type="contract",
            mutation={
                "operation": "set_trace_state",
                "field_id": "row_id",
                "trace_key": "full_master_plan_section_crosswalk_trace",
                "trace_state": "TRACE_BLOCKED",
            },
            expected_reason_codes=[c.PR138_REASON_FIELD_WITHOUT_CROSSWALK_TRACE],
        ),
        _fixture(
            "invalid_final_readiness_claim",
            payload_type="report",
            mutation={"operation": "set_report_flag", "field": "final_readiness_claimed_by_pr138", "value": True},
            expected_reason_codes=[c.PR138_REASON_FINAL_READINESS_NOT_CREATED],
        ),
        _fixture(
            "invalid_day1_live_readiness_claim",
            payload_type="report",
            mutation={"operation": "set_report_flag", "field": "day1_live_readiness_claimed_by_pr138", "value": True},
            expected_reason_codes=[c.PR138_REASON_DAY1_LIVE_READINESS_NOT_CREATED],
        ),
        _fixture(
            "invalid_latency_superiority_claim",
            payload_type="report",
            mutation={"operation": "set_report_flag", "field": "latency_superiority_claimed_by_pr138", "value": True},
            expected_reason_codes=[c.PR138_REASON_REPORT_CLAIM_FORBIDDEN],
        ),
        _fixture(
            "invalid_execution_superiority_claim",
            payload_type="report",
            mutation={"operation": "set_report_flag", "field": "execution_superiority_claimed_by_pr138", "value": True},
            expected_reason_codes=[c.PR138_REASON_REPORT_CLAIM_FORBIDDEN],
        ),
        _fixture(
            "invalid_quantum_advantage_claim",
            payload_type="report",
            mutation={"operation": "set_report_flag", "field": "quantum_advantage_claimed_by_pr138", "value": True},
            expected_reason_codes=[c.PR138_REASON_QUANTUM_ADVANTAGE_CLAIM_FORBIDDEN],
        ),
        _fixture(
            "invalid_quantum_simulator_execution_claim",
            payload_type="report",
            mutation={"operation": "set_report_flag", "field": "quantum_simulator_execution_created_by_pr138", "value": True},
            expected_reason_codes=[c.PR138_REASON_QUANTUM_SIMULATOR_EXECUTION_FORBIDDEN],
        ),
        _fixture(
            "invalid_quantum_optimizer_input_claim",
            payload_type="report",
            mutation={"operation": "set_report_flag", "field": "quantum_optimizer_input_created_by_pr138", "value": True},
            expected_reason_codes=[c.PR138_REASON_QUANTUM_OPTIMIZER_INPUT_FORBIDDEN],
        ),
        _fixture(
            "invalid_quantum_optimizer_output_claim",
            payload_type="report",
            mutation={"operation": "set_report_flag", "field": "quantum_optimizer_output_created_by_pr138", "value": True},
            expected_reason_codes=[c.PR138_REASON_QUANTUM_OPTIMIZER_INPUT_FORBIDDEN],
        ),
        _fixture(
            "invalid_atomicrows_bundle_mutation_detection",
            payload_type="protected_diff",
            mutation={
                "operation": "simulate_changed_path",
                "path": c.ATOMICROWS_BUNDLE_PATH.as_posix(),
            },
            expected_reason_codes=[c.PR138_REASON_BUNDLE_MUTATION_FORBIDDEN],
        ),
        _fixture(
            "invalid_row_family_mutation_detection",
            payload_type="protected_diff",
            mutation={
                "operation": "simulate_changed_path",
                "path": "docs/master_plan/atomic_rows/pr98_row_family_sources/001_signal_features.source.jsonl",
            },
            expected_reason_codes=[c.PR138_REASON_ROW_FAMILY_SOURCE_MUTATION_FORBIDDEN],
        ),
        _fixture(
            "invalid_bundle_builder_mutation_detection",
            payload_type="protected_diff",
            mutation={"operation": "simulate_changed_path", "path": "tools/build_atomicrows_bundle.py"},
            expected_reason_codes=[c.PR138_REASON_BUILDER_MUTATION_FORBIDDEN],
        ),
        _fixture(
            "invalid_new_atomicrows_bundle_sidecar_reference_in_pr138_artifact_or_diff_scope",
            payload_type="protected_diff",
            mutation={
                "operation": "simulate_forbidden_sidecar_reference",
                "introduced_reference_class": "ATOMICROWS_BUNDLE_FORBIDDEN_SIDECAR_REFERENCE",
            },
            expected_reason_codes=[
                c.PR138_REASON_NEW_ATOMICROWS_BUNDLE_SHA_SIDECAR_REFERENCE_FORBIDDEN
            ],
        ),
        _fixture(
            "invalid_qtt_generated_cryptographic_authority_field",
            payload_type="report",
            mutation={
                "operation": "add_report_key",
                "key": "qtt_generated_cryptographic_authority_field",
                "value": True,
            },
            expected_reason_codes=[c.PR138_REASON_QTT_GENERATED_CRYPTOGRAPHIC_AUTHORITY_FORBIDDEN],
        ),
        _fixture(
            "invalid_older_unresolved_baseline_checkpoint_reference",
            payload_type="report",
            mutation={
                "operation": "set_report_flag",
                "field": "baseline_checkpoint",
                "value": "STALE_NON_D1BCE40_BASELINE_PLACEHOLDER",
            },
            expected_reason_codes=[
                c.PR138_REASON_OLDER_BASELINE_CHECKPOINT_REFERENCE_FORBIDDEN
            ],
        ),
    ]
    return {
        "execution": "DISABLED",
        "fixture_collection_id": "PR138_ATOMICROWS_SEMANTIC_ROW_CONTRACT_FIXTURES",
        "fixture_version": "v1",
        "fixtures": fixtures,
        "mode": "SOURCE_REQUIRED",
        "pr_id": c.PR_ID,
    }


def write_fixture_file(repo_root: Path | str) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    fixture = build_fixture_collection()
    path = root / c.FIXTURE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json_dump(fixture), encoding="utf-8", newline="\n")
    return fixture
