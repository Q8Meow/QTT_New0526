from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from tools import run_validation_gates
from tools import validate_agent_consumable_parameter_default_registry as pr155_cli

from src.qtt.stage1_prediction_markets.agent_consumable_parameter_default_registry import (
    constants as c,
)
from src.qtt.stage1_prediction_markets.agent_consumable_parameter_default_registry import (
    input_discovery,
    orchestration_preflight,
    report as report_builder,
    schema_projection,
    validator,
)
from src.qtt.stage1_prediction_markets.agent_consumable_parameter_default_registry.builder import (
    build_outputs,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
_TRACKED_GENERATED_SIDE_EFFECT_PATHS = (
    "docs/master_plan/generated/QttActiveNonShaDay1GateStateRegistry.report.json",
    "docs/master_plan/generated/QttFinalReadinessDependencyPolicy.report.json",
    "docs/master_plan/generated/QttPrIdentityRoster.report.json",
)
_TRACKED_GENERATED_SIDE_EFFECT_BASELINES = {
    path: (REPO_ROOT / path).read_bytes()
    for path in _TRACKED_GENERATED_SIDE_EFFECT_PATHS
    if (REPO_ROOT / path).is_file()
}


def _restore_tracked_generated_side_effects() -> None:
    for path, content in _TRACKED_GENERATED_SIDE_EFFECT_BASELINES.items():
        target = REPO_ROOT / path
        if not target.exists() or target.read_bytes() != content:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)


def _outputs():
    return build_outputs(REPO_ROOT)


def _registry() -> dict:
    return dict(_outputs().registry)


def _report() -> dict:
    return dict(_outputs().report)


def _records() -> list[dict]:
    return list(_registry()["records"])


def _blocked_records() -> list[dict]:
    return list(_registry()["blocked_records"])


def test_pr155_discovers_pr154_canonical_input_and_preserves_checkpoint_counts():
    discovery = input_discovery.discover_pr154_input(REPO_ROOT)
    report = _report()

    assert discovery.failures == ()
    assert discovery.input_path == c.PR154_INPUT_REPORT_PATH
    assert report["input_pr154_total_records"] == 342
    assert report["agent_consumable_default_ready_count"] == 230
    assert report["non_consumable_blocked_count"] == 112
    assert report["official_source_materialized_default_count"] == 92
    assert report["owner_internal_control_plane_default_count"] == 138
    assert report["live_order_ready_count"] == 0
    assert report["runtime_ready_count"] == 0
    assert report["connector_semantic_bound_count"] == 0
    assert report["replay_tested_count"] == 0
    assert report["paper_approved_count"] == 0
    assert report["quantum_execution_evidence_count"] == 0
    assert report["profit_evidence_count"] == 0


def test_registry_ready_defaults_are_nonlive_and_pending_direct_agent_binding():
    ready = [
        record
        for record in _records()
        if record["agent_consumable_default_ready_flag"] is True
    ]

    assert len(ready) == 230
    assert all(
        record["registry_consumption_state"]
        == c.REGISTRY_READY_NONLIVE_AGENT_ASSIGNMENT_PENDING
        for record in ready
    )
    assert all(record["agent_assignment_state"] == c.AGENT_ASSIGNMENT_PENDING for record in ready)
    assert all(record["direct_agent_assignment_ready_flag"] is False for record in ready)
    assert all(record["eligible_agent_ids"] == [] for record in ready)
    assert all(record["eligible_agent_basis"] == c.ELIGIBLE_AGENT_BASIS_PENDING for record in ready)
    assert all(record["forbidden_agent_ids"] == [] for record in ready)
    assert all(
        record["forbidden_agent_basis"] == c.FORBIDDEN_AGENT_BASIS_UNDECLARED
        for record in ready
    )
    for record in ready:
        for field in c.RECORD_ALWAYS_FALSE_FIELDS:
            assert record[field] is False


def test_blocked_records_preserve_exact_pr154_completion_paths():
    blocked = _blocked_records()

    assert len(blocked) == 112
    for record in blocked:
        completion = record["blocked_completion_path_if_any"]
        assert record["agent_consumable_default_ready_flag"] is False
        assert record["direct_agent_assignment_ready_flag"] is False
        assert not record["registry_consumption_state"].startswith("REGISTRY_DEFAULT_READY")
        for field in c.COMPLETION_PATH_FIELDS:
            assert field in completion
            assert completion[field]


def test_authority_boundary_forbids_runtime_live_connector_replay_paper_quantum_profit_and_hash_authority():
    report = _report()
    registry = _registry()

    for field in c.REPORT_FALSE_AUTHORITY_FIELDS:
        assert report[field] is False
    assert all(value is False for value in report["non_authority_boundary"].values())
    assert all(value is False for value in registry["non_authority_boundary"].values())
    for record in _records():
        for field in c.RECORD_ALWAYS_FALSE_FIELDS:
            assert record[field] is False
        assert record["authority_boundary"]["registry_default_is_not_live_order_ready"] is True
        assert record["authority_boundary"]["registry_default_is_not_quantum_execution_evidence"] is True


def test_orchestration_preflight_consumes_required_artifacts_and_records_alias_fallback():
    preflight = _report()["control_plane_preflight"]

    assert preflight["pr_identity_roster_consumed"] is True
    assert preflight["roadmap_execution_state_consumed"] is True
    assert preflight["launch_readiness_policy_consumed"] is True
    assert preflight["route_triage_consumed"] is True
    assert preflight["section_crosswalk_or_successor_consumed"] is True
    assert preflight["market_specific_index_consumed"] is True
    assert preflight["command_action_matrix_consumed"] is True
    assert preflight["atomicrows_reconciliation_consumed"] is True
    assert preflight["atomicrows_semantic_contract_consumed"] is True
    assert preflight["pr155_allowed_to_continue"] is True
    assert preflight["alias_resolution_applied"]["alias_exists"] is False
    assert preflight["alias_resolution_applied"]["successor_used"] is True
    assert (
        c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix()
        in preflight["missing_control_plane_artifacts"]
    )


def test_atomicrows_and_quantum_forward_metadata_are_traceable_not_execution():
    report = _report()
    registry = _registry()

    assert report["control_plane_preflight"]["atomicrows_reconciliation_consumed"] is True
    assert report["control_plane_preflight"]["atomicrows_semantic_contract_consumed"] is True
    assert report["atomicrows_bundle_created"] is False
    assert report["atomicrows_bundle_sha_or_hash_authority_created"] is False
    assert report["quantum_forward_compatibility_summary"]["quantum_execution_created"] is False
    assert (
        report["quantum_forward_compatibility_summary"]["optimizer_backend_execution_created"]
        is False
    )
    for record in registry["records"]:
        assert record["atomicrows_compatibility_state"] in c.ATOMICROWS_COMPATIBILITY_STATES
        assert (
            record["quantum_forward_compatibility_state"]
            in c.QUANTUM_FORWARD_COMPATIBILITY_STATES
        )
        assert record["optimizer_readiness_hint"] in c.OPTIMIZER_READINESS_HINTS
        assert record["quantum_strategy_compatibility_tags"] == []


def test_deterministic_output_and_forbidden_artifact_reference_absence():
    first = build_outputs(REPO_ROOT)
    second = build_outputs(REPO_ROOT)
    serialized = report_builder.json_dump(first.registry) + report_builder.json_dump(first.report)
    forbidden_data = "AtomicRows.bundle." + "jsonl"
    forbidden_hash = "AtomicRows.bundle." + "sha" + "256"

    assert report_builder.json_dump(first.registry) == report_builder.json_dump(second.registry)
    assert report_builder.json_dump(first.report) == report_builder.json_dump(second.report)
    assert forbidden_data not in serialized
    assert forbidden_hash not in serialized
    assert "pr155-agent-consumable-parameter-default-registry" not in serialized
    assert "C:\\Users\\" not in serialized
    assert "generated_at" not in serialized


def test_input_discovery_missing_and_ambiguous_fail_closed(tmp_path):
    missing = input_discovery.discover_pr154_input(tmp_path / "missing")
    assert missing.failures == (c.PR155_PR154_INPUT_MISSING,)

    generated = tmp_path / "docs" / "master_plan" / "generated"
    generated.mkdir(parents=True)
    payload = {
        "report_id": c.PR154_INPUT_REPORT_ID,
        "semantic_pr_label": "PR154",
        "per_target_materialization_records": [],
    }
    for name in (
        "PR154_A_MaterializationGate.report.json",
        "PR154_B_MaterializationGate.report.json",
    ):
        (generated / name).write_text(
            json.dumps(payload, sort_keys=True),
            encoding="utf-8",
        )

    ambiguous = input_discovery.discover_pr154_input(tmp_path)
    assert ambiguous.failures == (c.PR155_PR154_INPUT_AMBIGUOUS,)
    assert len(ambiguous.candidate_paths) == 2


def test_missing_crosswalk_and_successor_fail_closed(tmp_path):
    result = orchestration_preflight.load_control_plane_preflight(tmp_path)

    assert c.PR155_ORCHESTRATION_CROSSWALK_MISSING in result.failures
    assert result.preflight["section_crosswalk_or_successor_consumed"] is False
    assert result.preflight["pr155_allowed_to_continue"] is False


def test_schema_projection_and_validator_use_central_constants():
    schema = schema_projection.registry_record_schema_projection()

    assert schema["properties"]["registry_consumption_state"]["enum"] == list(
        c.REGISTRY_CONSUMPTION_STATES
    )
    assert schema["properties"]["agent_assignment_state"]["enum"] == list(
        c.AGENT_ASSIGNMENT_STATES
    )
    assert schema["properties"]["atomicrows_compatibility_state"]["enum"] == list(
        c.ATOMICROWS_COMPATIBILITY_STATES
    )
    assert validator.validate_payloads(_registry(), _report()) == []


def test_branch_volatility_check_ignores_main_substrings_but_blocks_branch_tokens(monkeypatch):
    monkeypatch.setattr(
        validator,
        "_git_stdout",
        lambda _repo_root, _args: (0, "main\n", ""),
    )

    registry = _registry()
    report = _report()
    assert validator.validate_payloads(registry, report) == []

    poisoned = deepcopy(registry)
    poisoned["determinism_metadata_without_runtime_git_volatility"] = {
        "branch_probe": "refs/heads/main"
    }
    assert c.PR155_RECORD_SCHEMA_INVALID in validator.validate_payloads(poisoned, report)


def test_cli_check_only_accepts_tracked_artifacts_after_generation(capsys):
    _restore_tracked_generated_side_effects()
    assert pr155_cli.main(["--repo-root", REPO_ROOT.as_posix(), "--check-only"]) == 0
    assert c.SUCCESS_MARKER in capsys.readouterr().out


def test_validation_gate_sequence_includes_pr155_without_tracked_write():
    commands = run_validation_gates.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands if len(command) > 1]
    pr154_index = command_names.index(
        "validate_atomicrows_parameter_default_value_materialization_gate.py"
    )
    pr155_index = command_names.index(
        "validate_agent_consumable_parameter_default_registry.py"
    )
    pr156_index = command_names.index(
        "validate_agent_default_binding_universal_intake_gate.py"
    )
    next_index = command_names.index("validate_qtt_agent_role_operating_charter_registry.py")

    assert pr154_index < pr155_index < pr156_index < next_index
    assert commands[pr155_index] == [
        run_validation_gates.sys.executable,
        str(Path("tools") / "validate_agent_consumable_parameter_default_registry.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr155_index]
