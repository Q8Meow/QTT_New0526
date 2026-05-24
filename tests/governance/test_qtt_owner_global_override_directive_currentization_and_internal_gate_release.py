from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from tools.build_master_plan_section_coverage_report import load_yaml_subset
from tools.ci_branch_context import BranchContext
from tools.validate_master_plan_section_coverage import validate_json_schema_subset

from src.qtt.stage1_prediction_markets.qtt_owner_global_override_directive_currentization_and_internal_gate_release import (
    builder as pr143_builder,
    constants as c,
    report as pr143_report,
)
from src.qtt.stage1_prediction_markets.qtt_owner_global_override_directive_currentization_and_internal_gate_release.report import (
    _is_allowed_pr143_changed_path,
    _is_allowed_pr143_changed_path_for_branch,
    _is_pr138_mainline_context_repair_changed_path_for_branch,
    _is_pr142_changed_path_guard_compatibility_repair_changed_path_for_branch,
    build_json_schema,
    build_report,
    validate_payload,
    validate_repository_artifacts,
)
from tools import run_validation_gates as runner


REPO_ROOT = Path(__file__).resolve().parents[2]
_CACHE: dict[str, dict] | None = None


def _outputs() -> dict[str, dict]:
    global _CACHE
    if _CACHE is None:
        _CACHE = {
            "schema": build_json_schema(REPO_ROOT),
            "report": build_report(REPO_ROOT),
            "yaml": load_yaml_subset(REPO_ROOT / c.YAML_PATH),
            "fixture": json.loads((REPO_ROOT / c.FIXTURE_PATH).read_text(encoding="utf-8")),
        }
    return _CACHE


def _schema() -> dict:
    return deepcopy(_outputs()["schema"])


def _report() -> dict:
    return deepcopy(_outputs()["report"])


def _yaml() -> dict:
    return deepcopy(_outputs()["yaml"])


def _fixture() -> dict:
    return deepcopy(_outputs()["fixture"])


def _payload_failures(mutator) -> set[str]:
    payload = _report()
    mutator(payload)
    return set(validate_payload(payload, _schema()))


def _walk_strings(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, str):
        yield value


def test_schema_accepts_yaml_report_and_fixture() -> None:
    schema = _schema()
    for payload in (_yaml(), _report(), _fixture()):
        assert validate_json_schema_subset(payload, schema) == []
        assert validate_payload(payload, schema) == []
    assert _fixture()["execution"] == "DISABLED"
    assert _fixture()["mode"] == "SOURCE_REQUIRED"


def test_schema_rejects_missing_owner_override_declaration() -> None:
    payload = _report()
    payload["owner_global_override_directive"].pop("owner_global_override_declared")
    failures = validate_json_schema_subset(payload, _schema())
    assert any(
        "missing required field owner_global_override_declared" in failure
        for failure in failures
    )


def test_constants_schema_report_alignment_is_centralized() -> None:
    schema = _schema()
    report = _report()
    assert report["artifact_stem"] == c.ARTIFACT_STEM
    assert report["authority_class"] == c.AUTHORITY_CLASS
    assert report["validation_marker"] == c.SUCCESS_MARKER
    assert schema["properties"]["authority_class"]["enum"] == list(
        c.AUTHORITY_CLASS_VALUES
    )
    release_enum = schema["properties"]["internal_gate_release_contract"][
        "properties"
    ]["released_internal_gate_classes"]["items"]["enum"]
    assert release_enum == list(c.RELEASED_INTERNAL_GATE_CLASSES)
    preserved_enum = schema["properties"]["non_owner_evidence_boundary"][
        "properties"
    ]["preserved_non_owner_evidence_classes"]["items"]["enum"]
    assert preserved_enum == list(c.NON_OWNER_EVIDENCE_CLASSES_PRESERVED)
    assert report["internal_gate_release_contract"]["released_internal_gate_classes"] == list(
        c.RELEASED_INTERNAL_GATE_CLASSES
    )


def test_pr136_alias_resolution_uses_canonical_without_creating_alias() -> None:
    alias_resolution = _report()["pr136_orchestration_preflight"]["alias_resolution"]
    assert alias_resolution == {
        "requested_alias": c.CROSSWALK_REQUESTED_ALIAS.as_posix(),
        "alias_exists": False,
        "canonical_crosswalk_used": c.CROSSWALK_CANONICAL.as_posix(),
        "created_missing_alias": False,
        "conflict_detected": False,
    }
    assert not (REPO_ROOT / c.CROSSWALK_REQUESTED_ALIAS).exists()


def test_missing_evidence_fails_closed() -> None:
    _evidence, failures = pr143_builder.load_static_evidence(REPO_ROOT / ".tmp" / "missing")
    assert any("PR143_REQUIRED_EVIDENCE_MISSING" in failure for failure in failures)


def test_existing_owner_global_override_authority_is_consumed() -> None:
    consumed = _report()["existing_owner_global_override_authority_consumption"]
    assert consumed["tool_path"] == c.OWNER_GLOBAL_OVERRIDE_AUTHORITY_TOOL_PATH.as_posix()
    assert consumed["report_path"] == c.OWNER_GLOBAL_OVERRIDE_AUTHORITY_REPORT_PATH.as_posix()
    assert consumed["tool_consumed"] is True
    assert consumed["report_present"] is True
    assert consumed["report_type"] == "QTT_OWNER_GLOBAL_OVERRIDE_AUTHORITY_REPORT"
    assert consumed["owner_global_override_authority"] is True
    assert consumed["owner_override_satisfies_all_qtt_internal_requirements"] is True


def test_pr142_readiness_owner_blockers_are_consumed_and_released() -> None:
    handoff = _report()["pr142_handoff_consumption"]
    assert handoff["ready_to_request_owner_review"] is True
    assert handoff["ready_to_prepare_future_materialization_plan"] is True
    assert handoff["required_future_owner_action"] == (
        "EXPLICIT_OWNER_APPROVAL_PACKET_REQUIRED_BEFORE_MATERIALIZATION"
    )
    assert handoff["owner_gate_codes_released_by_pr143"] == list(
        c.OWNER_GATE_CODES_RELEASED_BY_PR143
    )
    assert set(c.OWNER_GATE_CODES_RELEASED_BY_PR143).issubset(
        handoff["blocked_reason_codes_before_pr143"]
    )
    assert handoff["readiness_state_after_pr143"] == c.READINESS_STATE_AFTER_PR143
    assert handoff["materialization_permission_for_planning_released"] is True
    assert handoff["materialization_permission_for_actual_value_writes_created"] is False


def test_owner_global_override_recorded_and_future_prompts_must_not_ask_again() -> None:
    directive = _report()["owner_global_override_directive"]
    assert directive["owner_global_override_declared"] is True
    assert directive["owner_statement_recorded_normalized"] == (
        c.OWNER_GLOBAL_OVERRIDE_CANONICAL_NORMALIZED_TEXT
    )
    assert directive["owner_says_do_not_ask_again"] is True
    for field in c.FUTURE_PROMPT_CONSUMPTION_REQUIREMENTS:
        assert directive[field] is True
    assert directive["owner_override_satisfies_internal_owner_approval"] is True
    assert directive["owner_override_satisfies_internal_owner_approval_receipt"] is True
    assert directive["owner_override_satisfies_internal_owner_permission"] is True
    assert directive["owner_override_satisfies_internal_owner_action_required"] is True


def test_internal_owner_gate_classes_released_globally_with_no_active_owner_blockers() -> None:
    release = _report()["internal_gate_release_contract"]
    assert release["released_internal_gate_classes"] == list(c.RELEASED_INTERNAL_GATE_CLASSES)
    assert release["active_owner_approval_blockers_after_pr143"] == []
    assert release["internal_owner_permission_state_after_pr143"] == (
        c.INTERNAL_OWNER_PERMISSION_STATE_AFTER_PR143
    )
    failures = _payload_failures(
        lambda payload: payload["internal_gate_release_contract"][
            "active_owner_approval_blockers_after_pr143"
        ].append("MISSING_OWNER_APPROVAL")
    )
    assert "PR143_OWNER_APPROVAL_BLOCKERS_STILL_ACTIVE" in failures


def test_non_owner_evidence_is_preserved_as_pending_evidence_not_owner_approval() -> None:
    boundary = _report()["non_owner_evidence_boundary"]
    assert boundary["preserved_non_owner_evidence_classes"] == list(
        c.NON_OWNER_EVIDENCE_CLASSES_PRESERVED
    )
    assert boundary["non_owner_evidence_state_label"] == c.NON_OWNER_EVIDENCE_STATE_LABEL
    for field in c.FORBIDDEN_AUTHORITY_OUTPUT_FIELDS:
        assert boundary[field] is True
    assert "MISSING_ACCEPTED_SOURCE_PACKETS" in _report()["pr142_handoff_consumption"][
        "non_owner_evidence_codes_preserved_by_pr143"
    ]


def test_quantum_planning_is_released_without_quantum_execution_or_advantage_claims() -> None:
    quantum = _report()["quantum_forward_compatibility"]
    assert quantum["owner_internal_permission_for_quantum_planning_satisfied"] is True
    assert quantum[
        "owner_internal_permission_for_quantum_optimization_architecture_satisfied"
    ] is True
    assert quantum[
        "owner_internal_permission_for_true_quantum_backend_integration_planning_satisfied"
    ] is True
    assert quantum["quantum_planning_state"] == c.QUANTUM_PLANNING_STATE
    for field in c.QUANTUM_PLANNING_ALLOWED_FIELDS:
        assert quantum[field] is True
    for field in (
        "true_quantum_backend_execution_created",
        "quantum_simulator_execution_created",
        "qaoa_execution_created",
        "vqe_execution_created",
        "annealing_execution_created",
        "qubo_solving_created",
        "ising_solving_created",
        "quantum_optimizer_input_output_created",
        "quantum_advantage_claim_created",
        "parameter_ranges_invented",
        "optimizer_defaults_invented",
    ):
        assert quantum[field] is False
    assert quantum["quantum_backend_result_status"] == c.NON_OWNER_EVIDENCE_STATE_LABEL
    assert quantum["quantum_simulator_result_status"] == c.NON_OWNER_EVIDENCE_STATE_LABEL


def test_classical_optimizer_planning_released_without_optimizer_execution() -> None:
    classical = _report()["classical_optimizer_forward_compatibility"]
    assert classical["owner_internal_permission_for_optimizer_planning_satisfied"] is True
    assert classical["deterministic_field_identity_ready"] is True
    assert classical["external_fact_evidence_pending_not_owner_approval"] is True
    assert classical["replay_paper_results_pending_not_owner_approval"] is True
    assert classical["runtime_cash_receipt_pending_not_owner_approval"] is True
    for field in (
        "classical_optimizer_execution_created",
        "scoring_execution_created",
        "ranking_execution_created",
        "arbitration_execution_created",
        "strategy_selection_created",
    ):
        assert classical[field] is False


def test_materialization_bundle_source_connector_replay_paper_live_profit_are_forbidden() -> None:
    no_claim = _report()["no_claim_boundary"]
    for field in c.NO_CLAIM_FALSE_FIELDS:
        assert no_claim[field] is False
    for field in (
        "semantic_values_materialized",
        "materialization_permission_for_actual_value_writes_created",
        "source_acceptance_created",
        "connector_binding_created",
        "replay_execution_created",
        "paper_execution_created",
        "live_reachability_created",
        "order_authority_created",
        "profit_evidence_created",
        "final_readiness_created",
        "day1_launch_created",
        "qtt_generated_integrity_authority_created",
        "atomicrows_bundle_sha_path_reference_created",
    ):
        assert no_claim[field] is False


def test_source_evidence_packet_is_policy_not_external_fact_authority() -> None:
    source = _report()["source_evidence_boundary"]
    assert source["source_evidence_packet_consumed_if_present"] is True
    assert source["owner_policy_may_authorize_retrieval_scope"] is True
    assert source["owner_policy_may_authorize_external_fact_value"] is False
    assert source["source_acceptance_created"] is False
    assert source["connector_semantic_binding_created"] is False
    assert source["runtime_cash_receipt_created"] is False
    assert source[
        "missing_accepted_source_packets_are_evidence_pending_not_owner_approval"
    ] is True


def test_pr143k_remains_downstream_and_not_replaced() -> None:
    handoff = _report()["pr143k_forward_handoff"]
    for field in c.DOWNSTREAM_PR143_COMPATIBILITY_FIELDS:
        assert handoff[field] is True
    assert _report()["pr_identity_resolution"]["does_not_replace_pr143k"] is True
    assert _report()["pr_identity_resolution"][
        "pr143k_pr143p_pr143f_remain_downstream_evidence_lanes"
    ] is True


def test_latency_hot_path_boundary_is_control_plane_only() -> None:
    latency = _report()["latency_hot_path_boundary"]
    assert latency == c.LATENCY_HOT_PATH_BOUNDARY
    assert latency["control_plane_only"] is True
    assert latency["no_quantum_backend_call_in_live_path"] is True
    assert latency["owner_global_override_validation_not_live_hot_path_dependency"] is True


def test_report_paths_are_os_stable_and_no_forbidden_bundle_sha_path_is_emitted() -> None:
    report = _report()
    for text in _walk_strings(report):
        assert "C:\\" not in text
        assert "\\\\" not in text
    serialized = json.dumps(report, sort_keys=True)
    assert c.forbidden_bundle_reference_text() not in serialized
    assert "AtomicRows.bundle.jsonl" not in serialized


def test_no_generated_integrity_authority_fields_except_allowed_false_no_claims() -> None:
    allowed = set(c.ALLOWED_INTEGRITY_FIELD_NAMES)
    report = _report()
    for key, item in pr143_report._walk(report):
        lowered = key.lower()
        if key in allowed:
            if key != "main_head_short_sha_as_vcs_metadata_only":
                assert item is False
            continue
        assert not any(fragment in lowered for fragment in ("sha", "digest", "hash", "checksum"))


def test_changed_path_guard_uses_explicit_branch_context_simulation(monkeypatch) -> None:
    allowed_path = c.REPORT_PATH.as_posix()
    assert _is_allowed_pr143_changed_path_for_branch(allowed_path, c.BRANCH)
    assert _is_allowed_pr143_changed_path_for_branch(allowed_path, "pr143k-future")
    assert _is_allowed_pr143_changed_path_for_branch(allowed_path, "pr144-future")
    assert not _is_allowed_pr143_changed_path_for_branch(allowed_path, "main")
    assert not _is_allowed_pr143_changed_path_for_branch(allowed_path, "")

    monkeypatch.setattr(
        pr143_report,
        "current_branch_context",
        lambda repo_root: BranchContext(branch=c.BRANCH, source="unit-test"),
    )
    assert _is_allowed_pr143_changed_path(allowed_path, REPO_ROOT)


def test_changed_path_guard_allows_exact_pr138_mainline_context_repair_files_only(
    monkeypatch,
) -> None:
    assert c.PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_ALLOWANCE_REASON_CODE == (
        "PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_REQUIRED_FOR_PR144_DOWNSTREAM_VALIDATION"
    )
    for path in c.PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_CHANGED_PATHS:
        assert path not in c.ALLOWED_PR143_CHANGED_PATHS
        assert _is_pr138_mainline_context_repair_changed_path_for_branch(
            path,
            "pr144-pr138-mainline-branch-context-normalization",
        )
        assert _is_pr138_mainline_context_repair_changed_path_for_branch(
            path,
            "pr145-future-roadmap-branch",
        )
        assert not _is_pr138_mainline_context_repair_changed_path_for_branch(
            path,
            c.BRANCH,
        )
        assert not _is_pr138_mainline_context_repair_changed_path_for_branch(
            path,
            "pr143-qtt-owner-global-override-directive-currentization-internal-gate-release",
        )
        assert not _is_pr138_mainline_context_repair_changed_path_for_branch(
            path,
            "pr138-atomicrows-semantic-row-contract",
        )
        assert not _is_pr138_mainline_context_repair_changed_path_for_branch(path, "main")
        assert not _is_pr138_mainline_context_repair_changed_path_for_branch(path, "")

    monkeypatch.setattr(
        pr143_report,
        "current_branch_context",
        lambda repo_root: BranchContext(
            branch="pr144-pr138-mainline-branch-context-normalization",
            source="unit-test",
        ),
    )
    for path in c.PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_CHANGED_PATHS:
        assert _is_allowed_pr143_changed_path(path, REPO_ROOT)


def test_changed_path_guard_allows_exact_pr142_guard_compatibility_files_only(
    monkeypatch,
) -> None:
    assert c.PR142_CHANGED_PATH_GUARD_COMPATIBILITY_REPAIR_ALLOWANCE_REASON_CODE == (
        "PR142_CHANGED_PATH_GUARD_COMPATIBILITY_REQUIRED_FOR_PR144_DOWNSTREAM_VALIDATION"
    )
    for path in c.PR142_CHANGED_PATH_GUARD_COMPATIBILITY_REPAIR_CHANGED_PATHS:
        assert path not in c.ALLOWED_PR143_CHANGED_PATHS
        assert _is_pr142_changed_path_guard_compatibility_repair_changed_path_for_branch(
            path,
            "pr144-pr138-mainline-branch-context-normalization",
        )
        assert _is_pr142_changed_path_guard_compatibility_repair_changed_path_for_branch(
            path,
            "pr145-future-roadmap-branch",
        )
        assert not _is_pr142_changed_path_guard_compatibility_repair_changed_path_for_branch(
            path,
            c.BRANCH,
        )
        assert not _is_pr142_changed_path_guard_compatibility_repair_changed_path_for_branch(
            path,
            "pr142-atomicrows-semantic-value-materialization-authorization-handoff-gate",
        )
        assert not _is_pr142_changed_path_guard_compatibility_repair_changed_path_for_branch(
            path,
            "main",
        )
        assert not _is_pr142_changed_path_guard_compatibility_repair_changed_path_for_branch(
            path,
            "",
        )

    monkeypatch.setattr(
        pr143_report,
        "current_branch_context",
        lambda repo_root: BranchContext(
            branch="pr144-pr138-mainline-branch-context-normalization",
            source="unit-test",
        ),
    )
    for path in c.PR142_CHANGED_PATH_GUARD_COMPATIBILITY_REPAIR_CHANGED_PATHS:
        assert _is_allowed_pr143_changed_path(path, REPO_ROOT)


def test_changed_path_guard_rejects_protected_atomicrows_paths() -> None:
    disallowed_paths = {
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
        "docs/master_plan/atomic_rows/pr98_row_family_sources/001_signal_features.source.jsonl",
        "docs/master_plan/generated/PR136RouteTriage.report.json",
    }
    for path in disallowed_paths:
        assert path not in c.ALLOWED_PR143_CHANGED_PATHS
        assert path not in c.PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_CHANGED_PATHS
        assert (
            path
            not in c.PR142_CHANGED_PATH_GUARD_COMPATIBILITY_REPAIR_CHANGED_PATHS
        )
        assert not _is_allowed_pr143_changed_path_for_branch(path, c.BRANCH)


def test_repository_artifacts_validate_with_monkeypatched_branch_context(monkeypatch) -> None:
    monkeypatch.setattr(
        pr143_report,
        "_changed_paths",
        lambda repo_root: [
            c.REPORT_PATH.as_posix(),
            c.YAML_PATH.as_posix(),
            c.SCHEMA_PATH.as_posix(),
            c.FIXTURE_PATH.as_posix(),
        ],
    )
    monkeypatch.setattr(
        pr143_report,
        "current_branch_context",
        lambda repo_root: BranchContext(branch=c.BRANCH, source="unit-test"),
    )
    assert validate_repository_artifacts(REPO_ROOT) == []
    assert build_report(REPO_ROOT) == build_report(REPO_ROOT)


def test_repository_artifacts_validate_pr144_repair_branch_changed_paths(monkeypatch) -> None:
    monkeypatch.setattr(
        pr143_report,
        "_changed_paths",
        lambda repo_root: [
            *sorted(c.PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_CHANGED_PATHS),
            *sorted(c.PR142_CHANGED_PATH_GUARD_COMPATIBILITY_REPAIR_CHANGED_PATHS),
            "src/qtt/stage1_prediction_markets/"
            "atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate/"
            "constants.py",
            "tests/atomicrows/"
            "test_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py",
        ],
    )
    monkeypatch.setattr(
        pr143_report,
        "current_branch_context",
        lambda repo_root: BranchContext(
            branch="pr144-pr138-mainline-branch-context-normalization",
            source="unit-test",
        ),
    )
    assert validate_repository_artifacts(REPO_ROOT) == []


def test_validation_gate_sequence_includes_pr143_after_owner_global_override(monkeypatch) -> None:
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)
    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]
    assert command_names.index(
        "validate_qtt_owner_global_override_authority.py"
    ) < command_names.index(
        "validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py"
    ) < command_names.index("validate_qtt_agent_role_operating_charter_registry.py")
