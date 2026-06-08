from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from tools.build_master_plan_section_coverage_report import load_yaml_subset
from tools.ci_branch_context import BranchContext
from tools.validate_master_plan_section_coverage import validate_json_schema_subset

from src.qtt.stage1_prediction_markets.atomicrows_semantic_value_materialization_owner_authorization_gate import (
    constants as c,
    report as pr141_report,
)
from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import (
    constants as pr160_constants,
)
from src.qtt.stage1_prediction_markets.atomicrows_semantic_value_materialization_owner_authorization_gate.report import (
    _is_allowed_pr141_changed_path,
    _is_ignored_pr141_changed_path,
    _is_pr138_mainline_context_repair_changed_path_for_branch,
    _is_pr140_guard_repair_changed_path_for_branch,
    _is_pr142_handoff_changed_path_for_branch,
    _is_pr143_owner_override_currentization_changed_path_for_branch,
    build_gate,
    build_json_schema,
    build_report,
    validate_gate_payload,
    validate_repository_artifacts,
)
from tools import run_validation_gates as runner


REPO_ROOT = Path(__file__).resolve().parents[2]
_CACHE: dict | None = None


def _outputs() -> dict:
    global _CACHE
    if _CACHE is None:
        _CACHE = {
            "schema": build_json_schema(REPO_ROOT),
            "gate": build_gate(REPO_ROOT),
            "report": build_report(REPO_ROOT),
        }
    return _CACHE


def _schema() -> dict:
    return deepcopy(_outputs()["schema"])


def _gate() -> dict:
    return deepcopy(_outputs()["gate"])


def _report() -> dict:
    return deepcopy(_outputs()["report"])


def _inventory() -> dict:
    return json.loads((REPO_ROOT / c.PR138_INVENTORY_PATH).read_text(encoding="utf-8"))


def _pr139_manifest() -> dict:
    return load_yaml_subset(REPO_ROOT / c.PR139_MANIFEST_PATH)


def _pr140_plan() -> dict:
    return load_yaml_subset(REPO_ROOT / c.PR140_PLAN_PATH)


def _agent_map() -> dict:
    return json.loads((REPO_ROOT / c.PR136_EVIDENCE_PATHS[5]).read_text(encoding="utf-8"))


def _gate_failures(mutator) -> set[str]:
    gate = _gate()
    mutator(gate)
    return set(
        validate_gate_payload(
            gate,
            _schema(),
            inventory=_inventory(),
            pr139_manifest=_pr139_manifest(),
            pr140_plan=_pr140_plan(),
            agent_map=_agent_map(),
        )
    )


def _walk_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def test_schema_accepts_canonical_fixture() -> None:
    fixture = json.loads((REPO_ROOT / c.FIXTURE_PATH).read_text(encoding="utf-8"))
    assert validate_json_schema_subset(fixture, _schema()) == []
    assert fixture["mode"] == "SOURCE_REQUIRED"
    assert fixture["execution"] == "DISABLED"


def test_schema_rejects_missing_required_top_level_fields() -> None:
    gate = _gate()
    gate.pop("authority_class")
    failures = validate_json_schema_subset(gate, _schema())
    assert any("missing required field authority_class" in failure for failure in failures)


def test_schema_rejects_malformed_authority_boundary_values() -> None:
    failures = _gate_failures(
        lambda gate: gate["authority_boundaries"].update(
            materialization_permission_created=True
        )
    )
    assert any("AUTHORITY_BOUNDARY" in failure or "SCHEMA_VALIDATION" in failure for failure in failures)


def test_schema_rejects_missing_downstream_quantum_and_latency_sections() -> None:
    for key in (
        "downstream_handoff_contract",
        "quantum_forward_authorization_boundary",
        "latency_hot_path_authorization_boundary",
    ):
        gate = _gate()
        gate.pop(key)
        failures = validate_json_schema_subset(gate, _schema())
        assert any(f"missing required field {key}" in failure for failure in failures)


def test_every_pr138_field_is_covered_exactly_once_and_maps_to_pr140() -> None:
    gate = _gate()
    inventory = _inventory()
    pr140_by_id = {
        field["field_id"]: field
        for field in _pr140_plan()["field_coverage"]
    }
    expected = [field["field_id"] for field in inventory["fields"]]
    actual = [field["field_id"] for field in gate["field_authorization_readiness_ledger"]]
    assert actual == expected
    assert len(actual) == 59
    assert len(set(actual)) == 59
    for entry in gate["field_authorization_readiness_ledger"]:
        upstream = pr140_by_id[entry["field_id"]]
        assert entry["pr140_coverage_status"] == upstream["coverage_status"]
        assert entry["pr140_dependency_class"] == upstream["dependency_class"]
        assert entry["pr140_future_pr_dependency_class"] == upstream["future_pr_dependency_class"]


def test_duplicate_and_unknown_field_authorization_fail_closed() -> None:
    duplicate_failures = _gate_failures(
        lambda gate: gate["field_authorization_readiness_ledger"].append(
            deepcopy(gate["field_authorization_readiness_ledger"][0])
        )
    )
    unknown_failures = _gate_failures(
        lambda gate: gate["field_authorization_readiness_ledger"][0].update(
            field_id="unknown_pr138_field"
        )
    )
    assert "PR141_DUPLICATE_FIELD_AUTHORIZATION" in duplicate_failures
    assert any("PR141_UNKNOWN_FIELD_ID" in failure for failure in unknown_failures)


def test_row_id_is_existing_supported_only() -> None:
    row_id = next(
        entry
        for entry in _gate()["field_authorization_readiness_ledger"]
        if entry["field_id"] == "row_id"
    )
    assert row_id["owner_authorization_readiness_state"] == "EXISTING_ROW_ID_ONLY_NO_AUTHORIZATION_NEEDED"
    assert row_id["materialization_eligibility_state"] == "EXISTING_FIELD_ALREADY_SUPPORTED"
    assert row_id["downstream_dependency_class"] == "EXISTING_ROW_ID_ONLY"
    assert row_id["eligibility_to_request_owner_authorization"] is False
    assert row_id["owner_approval_granted_by_pr141"] is False
    assert row_id["materialization_permitted_now"] is False


def test_forced_false_source_and_quantum_boundary_fields_remain_closed() -> None:
    ledger = {
        entry["field_id"]: entry
        for entry in _gate()["field_authorization_readiness_ledger"]
    }
    for field_id in c.FORCED_FALSE_FIELD_IDS:
        entry = ledger[field_id]
        assert entry["forced_false_no_authority_boundary"] is True
        assert entry["owner_approval_granted_by_pr141"] is False
        assert entry["materialization_permitted_now"] is False
    assert ledger["quantum_backend_execution_allowed_flag"]["quantum_backend_execution_allowed"] is False
    assert ledger["quantum_backend_execution_allowed_flag"]["materialization_eligibility_state"] == (
        "BLOCKED_BY_QUANTUM_BACKEND_EXECUTION_BOUNDARY"
    )
    assert ledger["external_fact_authority_flag"]["materialization_eligibility_state"] == (
        "BLOCKED_BY_AUTHORITY_BOUNDARY"
    )
    assert _gate()["authority_boundaries"]["accepted_source_packet_created"] is False


def test_owner_approval_and_materialization_are_false_for_every_field() -> None:
    for entry in _gate()["field_authorization_readiness_ledger"]:
        assert entry["owner_approval_granted_by_pr141"] is False
        assert entry["materialization_permitted_now"] is False
        assert entry["semantic_value_materialized_by_pr141"] is False
        assert entry["bundle_mutation_allowed_by_pr141"] is False
        assert entry["row_family_source_mutation_allowed_by_pr141"] is False


def test_all_field_groups_and_row_family_sources_are_represented_without_mutation() -> None:
    gate = _gate()
    inventory = _inventory()
    expected_groups = {group["field_group_id"] for group in inventory["field_groups"]}
    actual_groups = {
        group["field_group_id"]
        for group in gate["field_group_authorization_summary"]
    }
    assert actual_groups == expected_groups
    assert len(actual_groups) == 8
    for group in gate["field_group_authorization_summary"]:
        assert group["no_authority_created"] is True
        assert group["semantic_values_materialized"] is False

    manifest = _pr139_manifest()
    expected_paths = {
        entry["source_file_path"]
        for entry in manifest["row_family_source_manifest"]["row_family_entries"]
    }
    actual_paths = {
        entry["row_family_source_file_path"]
        for entry in gate["row_family_source_authorization_summary"]
    }
    assert len(actual_paths) == 15
    assert actual_paths == expected_paths
    for source in gate["row_family_source_authorization_summary"]:
        assert source["mutation_allowed_by_pr141"] is False
        assert source["semantic_values_materialized_by_pr141"] is False


def test_market_scopes_and_agent_domains_are_static_metadata_only() -> None:
    gate = _gate()
    scopes = gate["market_scope_authorization_summary"]
    assert {scope["scope_id"] for scope in scopes} == set(c.MARKET_SCOPE_IDS)
    for scope in scopes:
        assert scope["owner_authorization_required_before_materialization"] is True
        assert scope["external_fact_authority_created"] is False
        assert scope["connector_binding_created"] is False
        assert scope["live_use_allowed_created"] is False

    agent_domains = gate["agent_orchestration_authorization_summary"]
    assert len(agent_domains) == 19
    for domain in agent_domains:
        assert domain["may_consume_pr141_gate_as_static_metadata"] is True
        assert domain["may_materialize_values_by_pr141"] is False
        assert domain["final_order_submission_authority_created"] is False
        assert domain["live_order_authority_allowed"] is False
        assert domain["latency_hot_path_allowed"] is False


def test_authority_boundaries_remain_false_in_gate_and_report() -> None:
    gate = _gate()
    report = _report()
    assert gate["authority_boundaries"] == c.AUTHORITY_BOUNDARIES
    assert report["authority_boundaries"] == c.AUTHORITY_BOUNDARIES
    assert report["authority_class"] == c.AUTHORITY_CLASS
    for payload in (gate, report):
        assert payload["final_ready"] is False
        assert payload["day1_launch_ready"] is False
        assert payload["semantic_values_materialized"] is False
        assert payload["materialization_permission_created"] is False
        assert payload["owner_approval_receipt_created"] is False
        assert payload["authority_boundaries"]["row_family_sources_mutated"] is False
        assert payload["authority_boundaries"]["atomicrows_bundle_mutated"] is False
        for key, value in payload["authority_boundaries"].items():
            assert value is False, key


def test_quantum_and_latency_boundaries_create_no_execution_or_claims() -> None:
    gate = _gate()
    quantum = gate["quantum_forward_authorization_boundary"]
    for key in (
        "no_quantum_execution_flag",
        "no_quantum_signal_creation_flag",
        "no_quantum_optimizer_input_flag",
        "no_quantum_optimizer_output_flag",
        "no_quantum_backend_execution_flag",
        "no_quantum_simulator_execution_flag",
        "no_quantum_advantage_claim_flag",
        "quantum_backend_execution_allowed_flag_forced_false",
    ):
        assert quantum[key] is True
    latency = gate["latency_hot_path_authorization_boundary"]
    assert latency == c.LATENCY_HOT_PATH_AUTHORIZATION_BOUNDARY
    assert latency["future_live_path_consumption_mode"] == (
        "PRECOMPUTED_SNAPSHOT_ONLY_AFTER_FUTURE_AUTHORIZED_PR"
    )


def test_downstream_handoff_honors_pr140_and_does_not_authorize_pr142() -> None:
    handoff = _gate()["downstream_handoff_contract"]
    assert handoff["pr141_consumes_downstream_input_from"] == ["PR140"]
    assert handoff["pr141_creates_downstream_input_for"] == ["PR142"]
    assert handoff["pr141_authorizes_materialization"] is False
    assert handoff["pr141_authorizes_bundle_mutation"] is False
    assert handoff["pr141_authorizes_row_family_source_mutation"] is False
    assert handoff["pr141_authorizes_source_acceptance"] is False
    assert handoff["pr141_authorizes_connector_binding"] is False
    assert handoff["pr141_authorizes_replay_execution"] is False
    assert handoff["pr141_authorizes_paper_execution"] is False
    assert handoff["pr141_authorizes_live_order_authority"] is False
    assert handoff["pr141_authorizes_quantum_backend_execution"] is False
    assert handoff["pr141_authorizes_final_readiness"] is False
    assert handoff["future_owner_authorization_required_for_actual_materialization"] is True
    assert handoff["future_owner_authorization_packet_required"] is True
    assert handoff["no_same_number_identity_inference"] is True


def test_orchestration_evidence_consumption_and_crosswalk_alias_resolution_are_recorded() -> None:
    report = _report()
    assert report["crosswalk_alias_resolution"] == {
        "requested_alias": c.CROSSWALK_REQUESTED_ALIAS.as_posix(),
        "alias_exists": False,
        "canonical_crosswalk_used": c.CROSSWALK_CANONICAL.as_posix(),
        "created_missing_alias": False,
    }
    for required_path in (
        "docs/master_plan/generated/PR136RouteTriage.report.json",
        "docs/master_plan/generated/PR136CommandActionMatrix.report.json",
        "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json",
        "docs/master_plan/generated/PR136AgentLaunchOrchestrationMap.report.json",
        "docs/master_plan/generated/PR136LaunchReadinessDependencyGraph.report.json",
        "docs/master_plan/generated/PR136QuantumAtomicRowsOptimizationReadinessMap.report.json",
    ):
        assert required_path in report["pr136_evidence_consumed"]
    assert c.PR140_REPORT_PATH.as_posix() in report["pr140_evidence_consumed"]
    assert c.PR140_PLAN_PATH.as_posix() in report["pr140_evidence_consumed"]


def test_no_forbidden_property_names_or_bundle_reference_are_emitted() -> None:
    for payload in (_gate(), _report(), _schema()):
        lowered_keys = [key.lower() for key in _walk_keys(payload)]
        for key in lowered_keys:
            assert not any(fragment in key for fragment in c.FORBIDDEN_PROPERTY_NAME_FRAGMENTS)
        serialized = json.dumps(payload, sort_keys=True)
        assert c.forbidden_bundle_reference_text() not in serialized


def test_changed_path_guard_ignores_only_runtime_tmp_directory() -> None:
    assert _is_ignored_pr141_changed_path(".tmp/")
    assert _is_ignored_pr141_changed_path(".tmp/pr141_deterministic_report_test")
    assert _is_ignored_pr141_changed_path(".tmp/nested/output.json")
    assert not _is_ignored_pr141_changed_path(".tmpfile")
    assert not _is_ignored_pr141_changed_path("tmp/")


def test_changed_path_guard_allows_exact_pr138_mainline_context_repair_files_only(
    monkeypatch,
) -> None:
    assert c.PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_ALLOWANCE_REASON_CODE == (
        "PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_REQUIRED_FOR_PR144_DOWNSTREAM_VALIDATION"
    )
    for path in c.PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_CHANGED_PATHS:
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
            "pr143-qtt-owner-global-override-directive-currentization-internal-gate-release",
        )
        assert not _is_pr138_mainline_context_repair_changed_path_for_branch(
            path,
            "pr138-atomicrows-semantic-row-contract",
        )
        assert not _is_pr138_mainline_context_repair_changed_path_for_branch(
            path,
            c.BRANCH,
        )
        assert not _is_pr138_mainline_context_repair_changed_path_for_branch(path, "main")
        assert not _is_pr138_mainline_context_repair_changed_path_for_branch(path, "")

    monkeypatch.setattr(
        pr141_report,
        "current_branch_context",
        lambda repo_root: BranchContext(
            branch="pr146-generated-report-nonmutating-validation-mode-audit",
            source="unit-test",
        ),
    )
    for path in c.PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_CHANGED_PATHS:
        assert _is_allowed_pr141_changed_path(path, REPO_ROOT)


def test_changed_path_guard_allows_exact_pr140_guard_repair_files_only(monkeypatch) -> None:
    assert c.PR140_GUARD_REPAIR_ALLOWANCE_REASON_CODE == (
        "PR140_GUARD_REPAIR_REQUIRED_FOR_PR141_DOWNSTREAM_HANDOFF"
    )
    for path in c.PR140_GUARD_REPAIR_CHANGED_PATHS:
        assert _is_pr140_guard_repair_changed_path_for_branch(
            path,
            c.BRANCH,
        )
        assert _is_pr140_guard_repair_changed_path_for_branch(
            path,
            "pr142-future-roadmap-branch",
        )
        assert not _is_pr140_guard_repair_changed_path_for_branch(
            path,
            "pr140-atomicrows-semantic-field-coverage-enrichment-plan",
        )
        assert not _is_pr140_guard_repair_changed_path_for_branch(path, "main")
        assert not _is_pr140_guard_repair_changed_path_for_branch(path, "")

    monkeypatch.setattr(
        pr141_report,
        "current_branch_context",
        lambda repo_root: BranchContext(branch=c.BRANCH, source="unit-test"),
    )
    for path in c.PR140_GUARD_REPAIR_CHANGED_PATHS:
        assert _is_allowed_pr141_changed_path(path, REPO_ROOT)


def test_changed_path_guard_allows_exact_pr142_handoff_files_only(monkeypatch) -> None:
    downstream_branch = (
        "pr142-atomicrows-semantic-value-materialization-authorization-handoff-gate"
    )
    for path in c.PR142_HANDOFF_READINESS_GATE_CHANGED_PATHS:
        assert _is_pr142_handoff_changed_path_for_branch(path, downstream_branch)
        assert _is_pr142_handoff_changed_path_for_branch(
            path,
            "pr143k-future-roadmap-branch",
        )
        assert not _is_pr142_handoff_changed_path_for_branch(path, c.BRANCH)
        assert not _is_pr142_handoff_changed_path_for_branch(path, "main")
        assert not _is_pr142_handoff_changed_path_for_branch(path, "")

    monkeypatch.setattr(
        pr141_report,
        "current_branch_context",
        lambda repo_root: BranchContext(branch=downstream_branch, source="unit-test"),
    )
    for path in c.PR142_HANDOFF_READINESS_GATE_CHANGED_PATHS:
        assert _is_allowed_pr141_changed_path(path, REPO_ROOT)


def test_changed_path_guard_allows_exact_pr143_owner_override_files_only(monkeypatch) -> None:
    downstream_branch = (
        "pr143-qtt-owner-global-override-directive-currentization-internal-gate-release"
    )
    for path in c.PR143_OWNER_GLOBAL_OVERRIDE_CURRENTIZATION_CHANGED_PATHS:
        assert _is_pr143_owner_override_currentization_changed_path_for_branch(
            path,
            downstream_branch,
        )
        assert _is_pr143_owner_override_currentization_changed_path_for_branch(
            path,
            "pr143k-future-roadmap-branch",
        )
        assert _is_pr143_owner_override_currentization_changed_path_for_branch(
            path,
            "pr144-future-roadmap-branch",
        )
        assert not _is_pr143_owner_override_currentization_changed_path_for_branch(
            path,
            c.BRANCH,
        )
        assert not _is_pr143_owner_override_currentization_changed_path_for_branch(path, "main")
        assert not _is_pr143_owner_override_currentization_changed_path_for_branch(path, "")

    monkeypatch.setattr(
        pr141_report,
        "current_branch_context",
        lambda repo_root: BranchContext(branch=downstream_branch, source="unit-test"),
    )
    for path in c.PR143_OWNER_GLOBAL_OVERRIDE_CURRENTIZATION_CHANGED_PATHS:
        assert _is_allowed_pr141_changed_path(path, REPO_ROOT)


def test_changed_path_guard_rejects_pr140_guard_repair_files_on_main_and_detached_context(
    monkeypatch,
) -> None:
    for branch in ("main", ""):
        monkeypatch.setattr(
            pr141_report,
            "current_branch_context",
            lambda repo_root, branch=branch: BranchContext(
                branch=branch,
                source="unit-test",
            ),
        )
        for path in c.PR140_GUARD_REPAIR_CHANGED_PATHS:
            assert not _is_allowed_pr141_changed_path(path, REPO_ROOT)
        for path in c.PR142_HANDOFF_READINESS_GATE_CHANGED_PATHS:
            assert not _is_allowed_pr141_changed_path(path, REPO_ROOT)


def test_changed_path_guard_rejects_broad_pr140_package_directories() -> None:
    broad_paths = {
        "src/qtt/stage1_prediction_markets/atomicrows_semantic_field_coverage_enrichment_plan/",
        "src/qtt/stage1_prediction_markets/atomicrows_semantic_field_coverage_enrichment_plan",
        "tests/atomicrows/",
        "tests/atomicrows",
    }
    assert c.PR140_GUARD_REPAIR_CHANGED_PATHS.isdisjoint(broad_paths)
    assert c.PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_CHANGED_PATHS.isdisjoint(broad_paths)
    assert c.PR142_HANDOFF_READINESS_GATE_CHANGED_PATHS.isdisjoint(broad_paths)
    for path in broad_paths:
        assert not _is_pr138_mainline_context_repair_changed_path_for_branch(
            path,
            "pr144-pr138-mainline-branch-context-normalization",
        )
        assert not _is_pr140_guard_repair_changed_path_for_branch(path, c.BRANCH)
        assert not _is_pr142_handoff_changed_path_for_branch(
            path,
            "pr142-atomicrows-semantic-value-materialization-authorization-handoff-gate",
        )


def test_changed_path_guard_keeps_pr140_generated_and_protected_paths_disallowed() -> None:
    disallowed_paths = {
        c.PR140_REPORT_PATH.as_posix(),
        c.PR140_PLAN_PATH.as_posix(),
        c.PR140_SCHEMA_PATH.as_posix(),
        "docs/master_plan/generated/AtomicRowsUnexpectedSideEffect.report.json",
        "docs/master_plan/generated/PR136RouteTriage.report.json",
        "docs/master_plan/generated/PR137R_AtomicRowsBundleReconciliation.report.json",
        "docs/master_plan/generated/PR138_AtomicRowsSemanticFieldInventory.json",
        "docs/master_plan/generated/AtomicRowsRowFamilySourceManifestCurrentization.report.json",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
        "docs/master_plan/atomic_rows/pr98_row_family_sources/001_signal_features.source.jsonl",
        "src/qtt/stage1_prediction_markets/connector_semantic_binding/validator.py",
        "src/qtt/stage1_prediction_markets/runtime_resolver/validator.py",
        "src/qtt/stage1_prediction_markets/replay_paper/validator.py",
        "requirements.txt",
    }
    for path in disallowed_paths:
        assert path not in c.ALLOWED_PR141_CHANGED_PATHS
        assert not _is_pr138_mainline_context_repair_changed_path_for_branch(
            path,
            "pr144-pr138-mainline-branch-context-normalization",
        )
        assert not _is_pr140_guard_repair_changed_path_for_branch(path, c.BRANCH)
        assert not _is_pr142_handoff_changed_path_for_branch(
            path,
            "pr142-atomicrows-semantic-value-materialization-authorization-handoff-gate",
        )


def test_pr140_guard_repair_allowance_is_integration_support_not_materialization() -> None:
    gate = _gate()
    assert gate["downstream_handoff_contract"]["pr141_consumes_downstream_input_from"] == [
        "PR140"
    ]
    assert gate["semantic_values_materialized"] is False
    assert gate["materialization_permission_created"] is False
    assert gate["owner_approval_receipt_created"] is False
    assert gate["authority_boundaries"]["semantic_values_materialized"] is False
    assert gate["authority_boundaries"]["atomicrows_bundle_mutated"] is False
    assert gate["authority_boundaries"]["source_acceptance_created"] is False
    assert gate["authority_boundaries"]["connector_semantic_binding_created"] is False
    assert gate["authority_boundaries"]["runtime_live_order_authority_created"] is False
    assert gate["authority_boundaries"]["quantum_backend_execution_created"] is False
    assert gate["final_ready"] is False


def test_repository_artifacts_validate_and_report_is_deterministic(monkeypatch) -> None:
    monkeypatch.setattr(
            pr141_report,
            "current_branch_context",
            lambda repo_root: BranchContext(
                branch="pr-ci-fastfail-validation-context-preflight",
                source="unit-test",
            ),
        )
    assert validate_repository_artifacts(REPO_ROOT) == []
    assert build_report(REPO_ROOT) == build_report(REPO_ROOT)


def test_validation_gate_sequence_includes_pr141_after_pr140_and_before_pytest(monkeypatch) -> None:
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)
    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]

    assert command_names.index("validate_atomicrows_semantic_field_coverage_enrichment_plan.py") < command_names.index(
        "validate_atomicrows_semantic_value_materialization_owner_authorization_gate.py"
    ) < command_names.index("run_pytest_fresh_basetemp.py")
