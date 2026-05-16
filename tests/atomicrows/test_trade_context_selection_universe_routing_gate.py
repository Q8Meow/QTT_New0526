from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from tools import validate_trade_context_selection_universe_routing_gate as validator


ROOT = Path(".")


def _schema() -> dict:
    return validator.load_json(validator.DEFAULT_SCHEMA)


def _production_gate() -> dict:
    return validator.load_yaml(validator.DEFAULT_PRODUCTION_GATE)


def _fixture() -> dict:
    return validator.load_json(validator.DEFAULT_FIXTURE)


def _dependencies() -> tuple[dict, dict]:
    _trade_schema, _trade_packet, registry, consumer_access_gate, failures = (
        validator.validate_dependencies(ROOT)
    )
    assert not failures
    return registry, consumer_access_gate


def _case(case_id: str) -> dict:
    return {case["case_id"]: case for case in _fixture()["fixture_cases"]}[case_id]


def _case_report(case_id: str) -> dict:
    registry, consumer_access_gate = _dependencies()
    _gate, _registry, _consumer_gate, report = validator._case_gate_registry_consumer_report(
        _fixture(),
        _case(case_id),
        registry,
        consumer_access_gate,
        ROOT,
    )
    return report


def _case_failures(case_id: str) -> tuple[dict, list[str]]:
    registry, consumer_access_gate = _dependencies()
    gate, case_registry, _consumer_gate, report = validator._case_gate_registry_consumer_report(
        _fixture(),
        _case(case_id),
        registry,
        consumer_access_gate,
        ROOT,
    )
    failures: list[str] = []
    failures.extend(
        validator.validate_routing_request(
            validator._mapping(gate.get("routing_request_contract")),
            f"fixture_case.{case_id}",
        )
    )
    failures.extend(validator.validate_required_universes(case_registry, f"{case_id}.registry"))
    failures.extend(validator.validate_policy_sections(gate, f"fixture_case.{case_id}"))
    failures.extend(validator.validate_report(report, f"fixture_case.{case_id}.report"))
    return report, failures


def _all_report_codes(report: dict) -> list[str]:
    codes: list[str] = []
    for candidate in report["route_candidates"]:
        codes.extend(candidate["reason_codes"])
    for blocked in report["blocked_universes"]:
        codes.extend(blocked["blocked_reason_codes"])
    return codes


def test_validator_emits_marker_and_report_is_byte_stable(capsys):
    first = validator.validate(
        repo_root=ROOT,
        schema_path=validator.DEFAULT_SCHEMA,
        production_gate_path=validator.DEFAULT_PRODUCTION_GATE,
        fixture_path=validator.DEFAULT_FIXTURE,
        output_path=validator.DEFAULT_REPORT,
    )
    second = validator.validate(
        repo_root=ROOT,
        schema_path=validator.DEFAULT_SCHEMA,
        production_gate_path=validator.DEFAULT_PRODUCTION_GATE,
        fixture_path=validator.DEFAULT_FIXTURE,
        output_path=validator.DEFAULT_REPORT,
    )
    report_text = validator.DEFAULT_REPORT.read_text(encoding="utf-8")

    assert first.failures == second.failures == ()
    assert first.report == second.report == json.loads(report_text)
    assert report_text == json.dumps(json.loads(report_text), indent=2, sort_keys=True) + "\n"
    assert json.loads(report_text)["validation_marker"] == validator.SUCCESS_MARKER
    assert validator.main([]) == 0
    assert capsys.readouterr().out.strip() == validator.SUCCESS_MARKER


def test_pr73_through_pr80_dependencies_are_consumed_and_marked_valid():
    registry, consumer_access_gate = _dependencies()
    report = json.loads(validator.PR80_REPORT.read_text(encoding="utf-8"))

    assert registry["required_selection_universe_ids"] == list(
        validator.REQUIRED_SELECTION_UNIVERSE_IDS
    )
    assert report["validation_marker"] == validator.PR80_SUCCESS_MARKER
    assert consumer_access_gate["required_selection_universe_ids"] == list(
        validator.REQUIRED_SELECTION_UNIVERSE_IDS
    )
    assert not validator.consumer_gate.validate_repair_pr76_dependency(ROOT)


@pytest.mark.parametrize(
    ("case_id", "expected_universe"),
    [
        ("ROUTING_PASS_KALSHI_BINARY_SHORT_HORIZON", "KALSHI_BINARY_SHORT_HORIZON"),
        (
            "ROUTING_PASS_POLYMARKET_EVENT_MARKET_MOMENTUM",
            "POLYMARKET_EVENT_MARKET_MOMENTUM",
        ),
        (
            "ROUTING_PASS_FORECASTEX_IBKR_EVENT_RISK_HEDGE",
            "FORECASTEX_IBKR_EVENT_RISK_HEDGE",
        ),
    ],
)
def test_explicit_static_trade_contexts_route_to_matching_universe(case_id, expected_universe):
    report = _case_report(case_id)

    assert validator.validate_report(report) == []
    assert report["eligible_universe_ids"] == [expected_universe]
    assert report["final_route_eligible_universe_ids"] == [expected_universe]
    assert report["owner_override_applied"] is False
    assert "ROUTE_ALLOWED_EXPLICIT_MATCH" in _all_report_codes(report)


def test_quantum_forward_route_is_static_and_evidence_neutral():
    report = _case_report("ROUTING_PASS_QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION_STATIC_ONLY")
    quantum = report["quantum_forward_metadata"]

    assert validator.validate_report(report) == []
    assert report["eligible_universe_ids"] == ["QUANTUM_OPTIMIZED_PORTFOLIO_SELECTION"]
    assert report["route_is_selection"] is False
    assert report["stack_selection_created"] is False
    assert report["score_breakdown_created"] is False
    assert report["optimizer_arbitration_created"] is False
    assert report["quantum_backend_execution_created"] is False
    assert report["quantum_advantage_claim_created"] is False
    assert quantum["quantum_forward_metadata_preserved_flag"] is True
    assert quantum["future_quantum_applicability_registry_required"] is True
    assert quantum["future_owner_quantum_priority_policy_required"] is True
    assert quantum["optimizer_arbitration_created"] is False
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_advantage_claim_created"] is False


def test_owner_override_allows_internal_route_only_for_existing_universe():
    report = _case_report("ROUTING_PASS_OWNER_OVERRIDE_INTERNAL_ONLY")

    assert validator.validate_report(report) == []
    assert report["eligible_universe_ids"] == []
    assert report["owner_override_eligible_universe_ids"] == [
        "POLYMARKET_EVENT_MARKET_MOMENTUM"
    ]
    assert report["final_route_eligible_universe_ids"] == [
        "POLYMARKET_EVENT_MARKET_MOMENTUM"
    ]
    assert report["owner_override_applied"] is True
    assert report["owner_override_basis"] == "OWNER_GLOBAL_OVERRIDE"
    assert report["owner_override_external_fact_fabrication_created"] is False
    assert report["source_acceptance_created"] is False
    assert report["connector_semantic_binding_created"] is False
    assert report["quantum_backend_execution_created"] is False
    assert report["profit_evidence_created"] is False
    assert "ROUTE_ALLOWED_OWNER_OVERRIDE_INTERNAL_ONLY" in _all_report_codes(report)


@pytest.mark.parametrize(
    ("case_id", "expected_fragment"),
    [
        ("ROUTING_BLOCK_UNKNOWN_PLATFORM", "ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_VALUE"),
        ("ROUTING_BLOCK_UNKNOWN_MARKET_TYPE", "ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_VALUE"),
        ("ROUTING_BLOCK_UNKNOWN_VENUE_SCOPE", "ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_VALUE"),
        ("ROUTING_BLOCK_UNKNOWN_STRATEGY_CLASS", "ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_VALUE"),
        ("ROUTING_BLOCK_UNKNOWN_EDGE_TYPE", "ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_VALUE"),
        (
            "ROUTING_BLOCK_UNKNOWN_LATENCY_SENSITIVITY_CLASS",
            "ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_VALUE",
        ),
        (
            "ROUTING_BLOCK_UNKNOWN_CAPITAL_INTENSITY_CLASS",
            "ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_VALUE",
        ),
        ("ROUTING_BLOCK_UNKNOWN_RISK_MODE", "ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_VALUE"),
        (
            "ROUTING_BLOCK_UNKNOWN_LIQUIDITY_CONTEXT",
            "ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_VALUE",
        ),
        ("ROUTING_BLOCK_UNKNOWN_TIME_HORIZON", "ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_VALUE"),
        (
            "ROUTING_BLOCK_UNKNOWN_QUANTUM_PRIORITY_MODE",
            "ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_VALUE",
        ),
        (
            "ROUTING_BLOCK_UNKNOWN_OWNER_OVERRIDE_BASIS",
            "ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_VALUE",
        ),
        (
            "ROUTING_BLOCK_UNKNOWN_TRADE_CONTEXT_FIELD",
            "ROUTE_BLOCKED_UNKNOWN_TRADE_CONTEXT_FIELD",
        ),
        ("ROUTING_BLOCK_UNKNOWN_UNIVERSE_ID", "ROUTE_BLOCKED_UNKNOWN_UNIVERSE"),
        ("ROUTING_BLOCK_MISSING_REQUIRED_UNIVERSE_ID", "missing required universe"),
        ("ROUTING_BLOCK_DUPLICATE_UNIVERSE_ID", "duplicate universe_id"),
        ("ROUTING_BLOCK_MISSING_CONSUMER_ACCESS", "ROUTE_BLOCKED_CONSUMER_ACCESS_MISSING"),
        ("ROUTING_BLOCK_CONSUMER_ACCESS_DENIED", "ROUTE_BLOCKED_CONSUMER_ACCESS_DENIED"),
        ("ROUTING_BLOCK_RANDOM_ROUTING_ATTEMPT", "random_selection_used"),
        ("ROUTING_BLOCK_SELECTED_STACK_ID_AUTHORITY", "selected_stack_id"),
        ("ROUTING_BLOCK_SCORE_BREAKDOWN", "score_breakdown"),
        ("ROUTING_BLOCK_RANKING_FIELDS", "ranking_fields"),
        ("ROUTING_BLOCK_OPTIMIZER_ARBITRATION", "optimizer_arbitration"),
        ("ROUTING_BLOCK_RUNTIME_LIVE_ORDER_AUTHORITY", "runtime_authority_created"),
        ("ROUTING_BLOCK_SOURCE_RETRIEVAL_OR_ACCEPTANCE", "source_retrieval_created"),
        ("ROUTING_BLOCK_CONNECTOR_SEMANTIC_BINDING", "connector_semantic_binding_created"),
        ("ROUTING_BLOCK_QUANTUM_BACKEND_EXECUTION", "quantum_backend_execution_created"),
        ("ROUTING_BLOCK_QUANTUM_ADVANTAGE_CLAIM", "quantum_advantage_claim_created"),
        ("ROUTING_BLOCK_PROFIT_EVIDENCE", "profit_evidence_created"),
        (
            "ROUTING_BLOCK_OWNER_OVERRIDE_EXTERNAL_FACT_ATTEMPT",
            "ROUTE_BLOCKED_OWNER_OVERRIDE_EXTERNAL_FACT_ATTEMPT",
        ),
        (
            "ROUTING_BLOCK_OWNER_OVERRIDE_MISSING_UNIVERSE",
            "ROUTE_BLOCKED_OWNER_OVERRIDE_MISSING_UNIVERSE",
        ),
        ("ROUTING_BLOCK_ATOMICROWS_BUNDLE_SHA256_CREATED", "atomicrows_bundle_sha256_exists"),
    ],
)
def test_fail_closed_block_cases_observe_expected_failure(case_id, expected_fragment):
    report, failures = _case_failures(case_id)
    observed_text = "\n".join([*failures, *_all_report_codes(report)])

    assert expected_fragment in observed_text


def test_route_output_ordering_reason_codes_and_static_boundaries_are_deterministic():
    report = _case_report("ROUTING_DETERMINISM_BYTE_STABLE_REPORT")
    text = validator.serialize_report(report)

    assert report == json.loads(text)
    assert report["eligible_universe_ids"] == sorted(report["eligible_universe_ids"])
    assert [item["universe_id"] for item in report["blocked_universes"]] == sorted(
        item["universe_id"] for item in report["blocked_universes"]
    )
    for item in report["route_candidates"]:
        assert item["reason_codes"] == validator._sort_reason_codes(item["reason_codes"])
    assert not validator.validate_report_deterministic_content(report)
    assert not validator.validate_validator_source_static(ROOT)


def test_forbidden_sha_artifact_paths_fail_closed_without_creating_repo_bundle_sha():
    temp_root = ROOT / ".tmp" / "pr81_bundle_artifact_test"
    if temp_root.exists():
        shutil.rmtree(temp_root)
    bundle_dir = temp_root / "docs" / "master_plan" / "atomic_rows"
    bundle_dir.mkdir(parents=True)
    try:
        (bundle_dir / "AtomicRows.bundle.jsonl").write_text("", encoding="utf-8")
        (bundle_dir / "AtomicRows.bundle.sha256").write_text("", encoding="utf-8")

        failures = validator.validate_no_forbidden_artifacts(temp_root)

        assert "ATOMICROWS_BUNDLE_FORBIDDEN_ARTIFACT_BLOCK" not in failures
        assert "ATOMICROWS_BUNDLE_SHA_FORBIDDEN_ARTIFACT_BLOCK" in failures
        assert (ROOT / validator.CANONICAL_BUNDLE_JSONL).exists()
        assert not (ROOT / validator.CANONICAL_BUNDLE_SHA256).exists()
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def test_production_contract_preserves_no_runtime_source_connector_profit_or_quantum_backend():
    gate = _production_gate()
    report = json.loads(validator.DEFAULT_REPORT.read_text(encoding="utf-8"))

    assert validator.validate_policy_sections(gate) == []
    assert report["route_is_selection"] is False
    assert report["selected_stack_id"] is None
    assert report["score_breakdown_created"] is False
    assert report["optimizer_arbitration_created"] is False
    assert report["runtime_authority_created"] is False
    assert report["live_authority_created"] is False
    assert report["order_authority_created"] is False
    assert report["source_retrieval_created"] is False
    assert report["source_acceptance_created"] is False
    assert report["connector_semantic_binding_created"] is False
    assert report["quantum_backend_execution_created"] is False
    assert report["quantum_advantage_claim_created"] is False
    assert report["profit_evidence_created"] is False
    assert report["random_selection_used"] is False
    assert not (ROOT / validator.PR76_OLD_LONG_TEST).exists()
    assert (ROOT / validator.PR76_SHORT_TEST).exists()
