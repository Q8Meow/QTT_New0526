from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from tools import run_validation_gates
from tools import validate_agent_default_binding_universal_intake_gate as pr156_cli

from src.qtt.stage1_prediction_markets.agent_default_binding_universal_intake_gate import (
    agent_binding,
    constants as c,
    input_discovery,
    orchestration_preflight,
    report as report_builder,
    schema_projection,
    validator,
)
from src.qtt.stage1_prediction_markets.agent_default_binding_universal_intake_gate.builder import (
    build_outputs,
)
from src.qtt.stage1_prediction_markets.agent_default_binding_universal_intake_gate.models import (
    OptionalArtifactSet,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def _outputs():
    return build_outputs(REPO_ROOT)


def _registry() -> dict:
    return dict(_outputs().registry)


def _report() -> dict:
    return dict(_outputs().report)


def _records() -> list[dict]:
    return list(_registry()["records"])


def test_preflight_consumes_required_orchestration_and_alias_successor():
    preflight = _report()["control_plane_preflight"]

    assert preflight["pr_identity_roster_consumed"] is True
    assert preflight["roadmap_execution_state_consumed"] is True
    assert preflight["launch_readiness_roadmap_consumed"] is True
    assert preflight["launch_readiness_policy_consumed"] is True
    assert preflight["route_triage_consumed"] is True
    assert preflight["section_crosswalk_or_successor_consumed"] is True
    assert preflight["market_specific_index_consumed"] is True
    assert preflight["command_action_matrix_consumed"] is True
    assert preflight["atomicrows_reconciliation_consumed"] is True
    assert preflight["atomicrows_semantic_contract_consumed"] is True
    assert preflight["alias_resolution_applied"]["alias_exists"] is False
    assert preflight["alias_resolution_applied"]["successor_used"] is True
    assert (
        c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix()
        in preflight["missing_control_plane_artifacts"]
    )


def test_missing_crosswalk_and_successor_fail_closed(tmp_path):
    result = orchestration_preflight.load_control_plane_preflight(tmp_path)

    assert c.PR156_ORCHESTRATION_CROSSWALK_MISSING in result.failures
    assert result.preflight["section_crosswalk_or_successor_consumed"] is False
    assert result.preflight["pr156_allowed_to_continue"] is False


def test_pr155_and_pr154_inputs_consumed_without_modifying_pr155_artifacts():
    before_registry = (REPO_ROOT / c.PR155_REGISTRY_PATH).read_bytes()
    before_report = (REPO_ROOT / c.PR155_REPORT_PATH).read_bytes()
    report = _report()

    assert input_discovery.discover_pr155_registry(REPO_ROOT).input_path == c.PR155_REGISTRY_PATH
    assert input_discovery.discover_pr155_report(REPO_ROOT).input_path == c.PR155_REPORT_PATH
    assert input_discovery.discover_pr154_report(REPO_ROOT).input_path == c.PR154_REPORT_PATH
    assert report["input_pr155_total_records"] == 342
    assert report["input_pr155_ready_default_count"] == 230
    assert report["input_pr155_blocked_count"] == 112
    assert (REPO_ROOT / c.PR155_REGISTRY_PATH).read_bytes() == before_registry
    assert (REPO_ROOT / c.PR155_REPORT_PATH).read_bytes() == before_report


def test_pr155_ready_defaults_remain_pending_without_exact_binding_maps():
    registry = _registry()
    ready = registry["agent_binding_records"]

    assert len(ready) == 230
    assert all(
        record["agent_binding_state"] == c.BINDING_PENDING_EXPLICIT_AGENT_MAP_MISSING
        for record in ready
    )
    assert all(record["bound_agent_ids"] == [] for record in ready)
    assert all(record["bound_agent_roles"] == [] for record in ready)
    assert all(record["bound_consumer_classes"] == [] for record in ready)
    assert _report()["binding_pending_count"] == 230
    assert _report()["explicit_agent_bound_count"] == 0


def test_exact_synthetic_agent_role_consumer_bindings_are_consumed_without_inference():
    optional = OptionalArtifactSet(
        artifacts={
            "qtt_agent_algorithm_binding_report": {
                "agent_binding_records": [
                    {
                        "pr155_registry_record_id": "PR155_RECORD_X",
                        "agent_ids": ["agent-a"],
                    },
                    {
                        "pr155_registry_record_id": "PR155_RECORD_Y",
                        "agent_roles": ["role-y"],
                    },
                    {
                        "pr155_registry_record_id": "PR155_RECORD_Z",
                        "consumer_classes": ["consumer-z"],
                    },
                ]
            }
        },
        consumed_artifacts=(
            {
                "artifact_key": "qtt_agent_algorithm_binding_report",
                "artifact_path": "synthetic.json",
                "consumed": True,
            },
        ),
        missing_artifacts=(),
        failures=(),
    )
    context = agent_binding.load_agent_binding_context(optional)

    assert agent_binding.binding_for_pr155_record("PR155_RECORD_X", context)[
        "agent_binding_state"
    ] == c.AGENT_BOUND_NONLIVE_EXPLICIT
    assert agent_binding.binding_for_pr155_record("PR155_RECORD_Y", context)[
        "agent_binding_state"
    ] == c.ROLE_BOUND_NONLIVE_EXPLICIT
    assert agent_binding.binding_for_pr155_record("PR155_RECORD_Z", context)[
        "agent_binding_state"
    ] == c.CONSUMER_CLASS_BOUND_NONLIVE_EXPLICIT
    assert agent_binding.binding_for_pr155_record("PR155_RECORD_MISSING", context)[
        "agent_binding_state"
    ] == c.BINDING_PENDING_EXPLICIT_AGENT_MAP_MISSING


def test_blocked_records_preserve_completion_paths_and_do_not_bind():
    blocked = _registry()["blocked_records"]

    assert len(blocked) == 112
    for record in blocked:
        assert record["population_lane"] == c.PR154_BLOCKED_COMPLETION_INGESTION_LANE
        assert record["agent_binding_state"] == c.BINDING_PENDING_PR154_COMPLETION
        assert record["bound_agent_ids"] == []
        completion = record["blocked_completion_path_ref_or_inline"]
        for field in c.COMPLETION_PATH_FIELDS:
            assert field in completion
            assert completion[field]


def test_atomicrows_universe_uses_confirmed_4183_aggregate_without_bundle_authority():
    report = _report()
    summary = report["atomicrows_ingestion_summary"]

    assert report["atomicrows_universe_confirmed_count"] == 4183
    assert report["atomicrows_universe_count_state"] == c.ATOMICROWS_UNIVERSE_COUNT_CONFIRMED
    assert summary["atomicrows_bundle_created"] is False
    assert summary["atomicrows_bundle_hash_authority_created"] is False
    assert summary["atomicrows_rows_materialized_by_pr156"] == 0
    assert _registry()["atomicrows_universe_ingestion_summary"]["record_kind"] == (
        c.ATOMICROWS_UNIVERSE_INGESTION_SUMMARY_RECORD
    )


def test_universal_templates_cover_classical_quantum_hybrid_and_are_not_candidates():
    templates = _registry()["universal_intake_templates"]
    template_types = {record["template_type"] for record in templates}

    assert set(c.UNIVERSAL_INTAKE_TEMPLATE_TYPE_VALUES) == template_types
    assert _report()["future_classical_intake_template_count"] == len(
        c.CLASSICAL_TEMPLATE_TYPES
    )
    assert _report()["future_quantum_intake_template_count"] == len(
        c.QUANTUM_TEMPLATE_TYPES
    )
    assert _report()["future_hybrid_intake_template_count"] == len(c.HYBRID_TEMPLATE_TYPES)
    for required in (
        c.QUBO_COMPATIBLE_TEMPLATE,
        c.ISING_COMPATIBLE_TEMPLATE,
        c.QAOA_COMPATIBLE_TEMPLATE,
        c.VQE_COMPATIBLE_TEMPLATE,
        c.ANNEALING_COMPATIBLE_TEMPLATE,
        c.QUANTUM_PORTFOLIO_OPTIMIZATION_TEMPLATE,
    ):
        assert required in template_types
    assert all(
        record["candidate_instance_state"] == c.TEMPLATE_ONLY_NO_CANDIDATE_INSTANCE
        for record in templates
    )
    assert all(record["bound_agent_ids"] == [] for record in templates)


def test_classical_quantum_strategy_priority_states_are_represented_without_execution():
    templates = _registry()["universal_intake_templates"]
    by_type = {record["template_type"]: record for record in templates}

    assert by_type[c.CLASSICAL_TRADING_FORMULA_TEMPLATE][
        "owner_strategy_priority_state"
    ] == c.OWNER_CLASSICAL_ALLOWED
    assert by_type[c.QUANTUM_INSPIRED_OPTIMIZER_TEMPLATE][
        "owner_strategy_priority_state"
    ] == c.OWNER_QUANTUM_ALLOWED
    assert by_type[c.HYBRID_CLASSICAL_QUANTUM_ALGORITHM_TEMPLATE][
        "owner_strategy_priority_state"
    ] == c.OWNER_HYBRID_COMPARE_ALLOWED
    assert all(record["optimizer_executed_flag"] is False for record in _records())
    assert all(record["quantum_backend_executed_flag"] is False for record in _records())


def test_static_scoring_optimizer_replay_paper_foundations_are_referenced_only():
    report = _report()
    scoring = report["scoring_ranking_future_routing_summary"]
    optimizer = report["optimizer_replay_paper_future_routing_summary"]

    assert c.OPTIONAL_INPUT_ARTIFACT_PATHS[
        "parameter_algorithm_scoring_policy_registry"
    ].as_posix() in scoring["static_foundation_artifacts_consumed"]
    assert c.OPTIONAL_INPUT_ARTIFACT_PATHS[
        "quantum_classical_optimizer_arbitration_gate"
    ].as_posix() in optimizer["static_foundation_artifacts_consumed"]
    assert scoring["scoring_ranking_executed_as_trade_selection"] is False
    assert optimizer["optimizer_executed"] is False
    assert optimizer["replay_executed"] is False
    assert optimizer["paper_executed"] is False


def test_no_authority_counts_and_false_flags_hold_everywhere():
    report = _report()

    for field in c.REPORT_ZERO_COUNT_FIELDS:
        assert report[field] == 0
    for field in c.REPORT_FALSE_AUTHORITY_FIELDS:
        assert report[field] is False
    for record in _records():
        for field in c.RECORD_ALWAYS_FALSE_FIELDS:
            assert record["non_authority_boundary"][field] is False
        assert record["authority_boundary"]["profit_evidence_created"] is False
        assert record["authority_boundary"]["quantum_advantage_claim_created"] is False


def test_determinism_and_branch_token_scan_allows_domainmap_but_blocks_ref(monkeypatch):
    first = _outputs()
    second = _outputs()

    assert report_builder.json_dump(first.registry) == report_builder.json_dump(
        second.registry
    )
    assert report_builder.json_dump(first.report) == report_builder.json_dump(second.report)
    serialized = report_builder.json_dump(first.registry) + report_builder.json_dump(
        first.report
    )
    assert c.BRANCH not in serialized
    assert "C:\\Users\\" not in serialized
    assert "generated_at" not in serialized

    monkeypatch.setattr(validator, "_git_stdout", lambda _repo_root, _args: (0, "main\n", ""))
    assert validator.validate_payloads(_registry(), _report(), repo_root=REPO_ROOT) == []

    poisoned = deepcopy(_registry())
    poisoned["determinism_metadata_without_runtime_git_volatility"] = {
        "branch_probe": c.BRANCH_TOKEN_SENTINEL_BLOCKED_REF_PREFIX + "main",
        "allowed_probe": c.BRANCH_TOKEN_SENTINEL_ALLOWED_DOMAINMAP,
    }
    assert c.PR156_RECORD_SCHEMA_INVALID in validator.validate_payloads(
        poisoned,
        _report(),
        repo_root=REPO_ROOT,
    )


def test_input_discovery_missing_and_ambiguous_fail_closed(tmp_path):
    assert input_discovery.discover_pr155_registry(tmp_path).failures == (
        c.PR156_REQUIRED_INPUT_MISSING,
    )
    assert input_discovery.discover_pr154_report(tmp_path).failures == (
        c.PR156_REQUIRED_INPUT_MISSING,
    )

    generated = tmp_path / "docs" / "master_plan" / "generated"
    generated.mkdir(parents=True)
    payload = {
        "registry_type": c.PR155_REGISTRY_TYPE,
        "pr_id": "PR155",
        "records": [],
    }
    for name in (
        "PR155_AgentConsumableParameterDefaultRegistry_A.registry.json",
        "PR155_AgentConsumableParameterDefaultRegistry_B.registry.json",
    ):
        (generated / name).write_text(
            json.dumps(payload, sort_keys=True),
            encoding="utf-8",
        )

    ambiguous = input_discovery.discover_pr155_registry(tmp_path)
    assert ambiguous.failures == (c.PR156_REQUIRED_INPUT_AMBIGUOUS,)
    assert len(ambiguous.candidate_paths) == 2


def test_schema_projection_and_validator_use_central_constants():
    schema = schema_projection.registry_record_schema_projection()

    assert schema["properties"]["population_lane"]["enum"] == list(
        c.POPULATION_LANE_VALUES
    )
    assert schema["properties"]["agent_binding_state"]["enum"] == list(
        c.AGENT_BINDING_STATE_VALUES
    )
    assert schema["properties"]["atomicrows_ingestion_state"]["enum"] == list(
        c.ATOMICROWS_INGESTION_STATE_VALUES
    )
    assert validator.validate_payloads(_registry(), _report(), repo_root=REPO_ROOT) == []


def test_cli_check_only_accepts_tracked_artifacts(capsys):
    assert pr156_cli.main(["--repo-root", REPO_ROOT.as_posix(), "--check-only"]) == 0
    assert c.SUCCESS_MARKER in capsys.readouterr().out


def test_validation_gate_sequence_includes_pr156_after_pr155_without_tracked_write():
    commands = run_validation_gates.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands if len(command) > 1]
    pr155_index = command_names.index(
        "validate_agent_consumable_parameter_default_registry.py"
    )
    pr156_index = command_names.index(
        "validate_agent_default_binding_universal_intake_gate.py"
    )
    next_index = command_names.index("validate_qtt_agent_role_operating_charter_registry.py")

    assert pr155_index < pr156_index < next_index
    assert commands[pr156_index] == [
        run_validation_gates.sys.executable,
        str(Path("tools") / "validate_agent_default_binding_universal_intake_gate.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr156_index]
