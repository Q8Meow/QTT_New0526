import json
from pathlib import Path

from tools import validate_qtt_trade_context_packet as validator


ROOT = Path(".")


def _schema() -> dict:
    return validator.load_json(validator.DEFAULT_SCHEMA)


def _production() -> dict:
    return validator.load_yaml(validator.DEFAULT_PRODUCTION_PACKET)


def _fixture() -> dict:
    return validator.load_json(validator.DEFAULT_FIXTURE)


def _case(case_id: str) -> dict:
    cases = {case["case_id"]: case for case in _fixture()["fixture_cases"]}
    return cases[case_id]


def _case_packet(case_id: str) -> dict:
    return validator.case_packet_from_fixture(_fixture(), _case(case_id))


def _schema_failures(packet: dict) -> list[str]:
    return validator.schema_subset_failures(packet, _schema(), "packet")


def test_production_packet_validates_and_report_is_deterministic():
    result = validator.validate(
        repo_root=ROOT,
        schema_path=validator.DEFAULT_SCHEMA,
        production_packet_path=validator.DEFAULT_PRODUCTION_PACKET,
        fixture_path=validator.DEFAULT_FIXTURE,
        output_path=validator.DEFAULT_REPORT,
    )

    assert result.ok, result.failures
    assert result.report is not None
    assert result.report["validation_marker"] == validator.SUCCESS_MARKER
    report_text = validator.DEFAULT_REPORT.read_text(encoding="utf-8")
    assert report_text == json.dumps(json.loads(report_text), indent=2, sort_keys=True) + "\n"
    assert "QTT_TRADE_CONTEXT_PACKET_SCHEMA_OK" in report_text


def test_pr77_pr73_pr74_pr75_and_repair_pr76_dependencies_are_valid():
    edge_schema, edge_packet, pr77_failures = validator.validate_pr77_dependency(ROOT)

    assert not validator.validate_pr73_dependency(ROOT)
    assert not validator.validate_pr74_dependency(ROOT)
    assert not validator.validate_pr75_dependency(ROOT)
    assert not pr77_failures
    assert not validator.validate_repair_pr76_dependency(ROOT)
    assert edge_schema["properties"]["packet_id"]["const"] == "EDGE_PARAMETER_STACK_SELECTION_PACKET"
    assert edge_packet["depends_on_parameter_stack_role_taxonomy"]["validation_marker"] == (
        "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_OK"
    )
    assert edge_packet["depends_on_parameter_stack_completeness_gate"]["validation_marker"] == (
        "ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE_OK"
    )
    assert edge_packet["depends_on_parameter_stack_compatibility_gate"]["validation_marker"] == (
        "ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE_OK"
    )


def test_all_minimum_trade_context_fields_are_required_and_present():
    schema = _schema()
    production = _production()
    schema_required = set(schema["required"])

    for field in validator.MINIMUM_REQUIRED_PACKET_FIELDS:
        assert field in production
        assert field in schema_required
    assert production["minimum_required_packet_fields"] == list(
        validator.MINIMUM_REQUIRED_PACKET_FIELDS
    )
    assert "trade_context_id" in schema_required
    assert "platform" in schema_required
    assert "market_type" in schema_required
    assert "venue_scope" in schema_required
    assert "strategy_class" in schema_required
    assert "edge_type" in schema_required
    assert "order_intent_type" in schema_required
    assert "latency_sensitivity_class" in schema_required
    assert "capital_intensity_class" in schema_required
    assert "risk_mode" in schema_required
    assert "liquidity_context" in schema_required
    assert "time_horizon" in schema_required
    assert "owner_override_basis" in schema_required
    assert "quantum_priority_mode" in schema_required


def test_shared_fields_align_with_edge_packet_fields():
    schema = _schema()
    production = _production()
    edge_schema, edge_packet, failures = validator.validate_pr77_dependency(ROOT)

    assert not failures
    assert not validator.validate_shared_edge_alignment(
        schema=schema,
        production_packet=production,
        edge_schema=edge_schema,
        edge_packet=edge_packet,
    )
    assert production["shared_fields_aligned_with_edge_packet"] == list(
        validator.SHARED_EDGE_FIELDS
    )


def test_missing_required_fields_fail_closed():
    for case_id, missing_field in (
        ("TRADE_CONTEXT_BLOCKED_MISSING_TRADE_CONTEXT_ID", "trade_context_id"),
        ("TRADE_CONTEXT_BLOCKED_MISSING_PLATFORM", "platform"),
        ("TRADE_CONTEXT_BLOCKED_MISSING_MARKET_TYPE", "market_type"),
        ("TRADE_CONTEXT_BLOCKED_MISSING_ORDER_INTENT_TYPE", "order_intent_type"),
        ("TRADE_CONTEXT_BLOCKED_MISSING_QUANTUM_PRIORITY_MODE", "quantum_priority_mode"),
    ):
        assert any(missing_field in failure for failure in _schema_failures(_case_packet(case_id)))


def test_static_trade_context_does_not_route_select_score_rank_arbitrate_or_execute():
    production = _production()
    context = production["context_static_policy"]
    future = production["future_consumer_contract"]
    readiness = production["production_readiness"]

    assert context["trade_context_is_static_schema_only"] is True
    assert context["trade_context_routes_selection_universe"] is False
    assert context["trade_context_selects_stack"] is False
    assert context["trade_context_scores_stack"] is False
    assert context["trade_context_ranks_stack"] is False
    assert context["trade_context_arbitrates_optimizer"] is False
    assert context["trade_context_executes_replay_or_paper"] is False
    assert context["trade_context_executes_runtime_or_live"] is False
    assert all(future[field] is False for field in validator.FUTURE_CONSUMER_FALSE_FIELDS)
    assert readiness == validator.PRODUCTION_READINESS_EXPECTED


def test_order_intent_owner_override_and_quantum_boundaries():
    production = _production()
    order = production["order_intent_boundary_policy"]
    owner = production["owner_override_policy"]
    quantum = production["quantum_priority_boundary_policy"]
    owner_case = _case_packet("OWNER_OVERRIDE_SATISFIED_INTERNAL_TRADE_CONTEXT_READINESS_ONLY")

    assert order["order_intent_type_is_static_context_only"] is True
    assert order["order_intent_type_creates_order_authority"] is False
    assert order["order_intent_type_creates_order_receipt"] is False
    assert order["order_intent_type_creates_fill_receipt"] is False
    assert _schema_failures(_case_packet("TRADE_CONTEXT_BLOCKED_ORDER_AUTHORITY_ATTEMPT"))

    assert owner["owner_override_satisfies_internal_trade_context_readiness_only"] is True
    for field in validator.OWNER_OVERRIDE_POLICY_FALSE_FIELDS:
        assert owner[field] is False
        assert owner_case["owner_override_policy"][field] is False
        assert owner_case["owner_override_basis"][field] is False
    assert owner_case["owner_override_basis"]["owner_override_token"] == "OWNER_GLOBAL_OVERRIDE"

    assert production["quantum_priority_mode"] in validator.QUANTUM_PRIORITY_MODE_VALUES
    assert quantum["quantum_priority_mode_static_context_only"] is True
    assert quantum["future_owner_quantum_priority_policy_required_before_quantum_priority_selection"] is True
    assert quantum["quantum_selection_created"] is False
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert _schema_failures(_case_packet("TRADE_CONTEXT_BLOCKED_QUANTUM_SELECTION_ATTEMPT"))
    assert _schema_failures(_case_packet("TRADE_CONTEXT_BLOCKED_QUANTUM_BACKEND_ATTEMPT"))
    assert _schema_failures(_case_packet("TRADE_CONTEXT_BLOCKED_QUANTUM_ADVANTAGE_CLAIM"))


def test_source_connector_runtime_live_order_profit_boundaries():
    production = _production()
    source = production["source_evidence_boundary_policy"]
    connector = production["connector_semantic_boundary_policy"]
    runtime = production["runtime_live_order_boundary_policy"]
    flags = production["explicit_no_claim_flags"]

    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert source["market_data_fact_requires_accepted_source_packet"] is True
    assert source["liquidity_fact_requires_accepted_source_packet"] is True
    assert flags["market_data_fact_created"] is False
    assert flags["liquidity_fact_created"] is False
    assert connector["connector_semantic_binding_created"] is False
    assert runtime["runtime_artifacts_created"] is False
    assert runtime["runtime_live_use_created"] is False
    assert runtime["order_authority_created"] is False
    assert runtime["profit_evidence_created"] is False
    assert _schema_failures(
        _case_packet("TRADE_CONTEXT_BLOCKED_LIQUIDITY_FACT_WITHOUT_ACCEPTED_SOURCE_PACKET")
    )
    assert _schema_failures(_case_packet("TRADE_CONTEXT_BLOCKED_EXTERNAL_FACT_AUTHORITY_ATTEMPT"))
    assert _schema_failures(_case_packet("TRADE_CONTEXT_BLOCKED_CONNECTOR_SEMANTIC_ATTEMPT"))
    assert _schema_failures(_case_packet("TRADE_CONTEXT_BLOCKED_RUNTIME_LIVE_ORDER_ATTEMPT"))


def test_forbidden_output_fields_and_no_claim_flags():
    production = _production()
    schema_properties = _schema()["properties"]

    for field in validator.FORBIDDEN_OUTPUT_FIELDS:
        assert field not in production
        assert field not in schema_properties
    assert _schema_failures(_case_packet("TRADE_CONTEXT_BLOCKED_SELECTED_STACK_ID_FIELD"))
    assert _schema_failures(_case_packet("TRADE_CONTEXT_BLOCKED_SELECTION_UNIVERSE_OUTPUT_FIELD"))
    assert _schema_failures(_case_packet("TRADE_CONTEXT_BLOCKED_SCORE_BREAKDOWN_FIELD"))
    assert production["forbidden_output_fields_policy"][
        "selected_stack_id_forbidden_in_trade_context"
    ] is True
    assert production["forbidden_output_fields_policy"][
        "selection_universe_ids_forbidden_as_output_in_this_pr"
    ] is True
    assert production["forbidden_output_fields_policy"][
        "score_breakdown_forbidden_in_this_pr"
    ] is True
    assert all(
        production["explicit_no_claim_flags"][field] is False
        for field in validator.EXPLICIT_NO_CLAIM_FALSE_FIELDS
    )


def test_forbidden_artifacts_master_plan_and_repair_pr76_state():
    completed = validator.subprocess.run(
        ["git", "diff", "--quiet", "--", str(validator.MASTER_PLAN_CURRENT)],
        stdout=validator.subprocess.PIPE,
        stderr=validator.subprocess.PIPE,
        text=True,
    )

    assert completed.returncode == 0
    assert not (ROOT / validator.CANONICAL_BUNDLE_JSONL).exists()
    assert not (ROOT / validator.CANONICAL_BUNDLE_SHA256).exists()
    assert (ROOT / validator.PR76_SHORT_TEST).exists()
    assert not (ROOT / validator.PR76_OLD_LONG_TEST).exists()
