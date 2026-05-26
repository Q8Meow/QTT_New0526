from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess

from tools.build_master_plan_section_coverage_report import load_yaml_subset
from tools.ci_branch_context import BranchContext
from tools.validate_master_plan_section_coverage import validate_json_schema_subset

from src.qtt.stage1_prediction_markets.atomicrows_semantic_field_coverage_enrichment_plan import (
    constants as c,
    report as pr140_report,
)
from src.qtt.stage1_prediction_markets.atomicrows_semantic_field_coverage_enrichment_plan.report import (
    _is_allowed_pr140_changed_path,
    _is_ignored_pr140_changed_path,
    _is_pr141_downstream_changed_path_for_branch,
    _is_pr142_downstream_changed_path_for_branch,
    _is_pr143_owner_override_currentization_changed_path_for_branch,
    build_json_schema,
    build_plan,
    build_report,
    validate_plan_payload,
    validate_report_payload,
    validate_repository_artifacts,
)
from tools import run_validation_gates as runner


REPO_ROOT = Path(__file__).resolve().parents[2]
_CACHE: dict | None = None


def _tracked_atomicrows_generated_paths() -> tuple[str, ...]:
    completed = subprocess.run(
        ["git", "ls-files", "docs/master_plan/generated"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return ()
    return tuple(
        sorted(
            path.strip().replace("\\", "/")
            for path in completed.stdout.splitlines()
            if path.strip().startswith("docs/master_plan/generated/AtomicRows")
            and path.strip().replace("\\", "/") not in c.ALLOWED_PR140_CHANGED_PATHS
        )
    )


_TRACKED_GENERATED_SIDE_EFFECT_BASELINES = {
    path: (REPO_ROOT / path).read_bytes()
    for path in _tracked_atomicrows_generated_paths()
    if (REPO_ROOT / path).is_file()
}


def _restore_tracked_generated_side_effects() -> None:
    for path, content in _TRACKED_GENERATED_SIDE_EFFECT_BASELINES.items():
        target = REPO_ROOT / path
        if not target.exists() or target.read_bytes() != content:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)


def _outputs() -> dict:
    global _CACHE
    if _CACHE is None:
        _CACHE = {
            "schema": build_json_schema(REPO_ROOT),
            "plan": build_plan(REPO_ROOT),
            "report": build_report(REPO_ROOT),
        }
    return _CACHE


def _schema() -> dict:
    return deepcopy(_outputs()["schema"])


def _plan() -> dict:
    return deepcopy(_outputs()["plan"])


def _report() -> dict:
    return deepcopy(_outputs()["report"])


def _inventory() -> dict:
    return json.loads((REPO_ROOT / c.PR138_INVENTORY_PATH).read_text(encoding="utf-8"))


def _pr139_manifest() -> dict:
    return load_yaml_subset(REPO_ROOT / c.PR139_MANIFEST_PATH)


def _plan_failures(mutator) -> set[str]:
    plan = _plan()
    mutator(plan)
    return set(
        validate_plan_payload(
            plan,
            _schema(),
            inventory=_inventory(),
            pr139_manifest=_pr139_manifest(),
        )
    )


def test_schema_accepts_canonical_fixture() -> None:
    fixture = json.loads((REPO_ROOT / c.FIXTURE_PATH).read_text(encoding="utf-8"))
    assert validate_json_schema_subset(fixture, _schema()) == []


def test_schema_rejects_missing_required_top_level_fields() -> None:
    plan = _plan()
    plan.pop("authority_class")
    failures = validate_json_schema_subset(plan, _schema())
    assert any("missing required field authority_class" in failure for failure in failures)


def test_schema_rejects_malformed_authority_boundary_values() -> None:
    failures = _plan_failures(
        lambda plan: plan["authority_boundaries"].update(
            bundle_mutation_allowed_flag=True
        )
    )
    assert any("AUTHORITY_BOUNDARY" in failure or "SCHEMA_VALIDATION" in failure for failure in failures)


def test_schema_rejects_missing_quantum_latency_and_downstream_sections() -> None:
    for key in (
        "quantum_forward_metadata_plan",
        "latency_hot_path_exclusion_matrix",
        "downstream_handoff_contract",
    ):
        plan = _plan()
        plan.pop(key)
        failures = validate_json_schema_subset(plan, _schema())
        assert any(f"missing required field {key}" in failure for failure in failures)


def test_every_pr138_field_is_covered_exactly_once() -> None:
    plan = _plan()
    inventory = _inventory()
    expected = [field["field_id"] for field in inventory["fields"]]
    actual = [field["field_id"] for field in plan["field_coverage"]]
    assert actual == expected
    assert len(actual) == 59
    assert len(set(actual)) == 59


def test_duplicate_field_coverage_fails_closed() -> None:
    failures = _plan_failures(
        lambda plan: plan["field_coverage"].append(deepcopy(plan["field_coverage"][0]))
    )
    assert "PR140_DUPLICATE_FIELD_COVERAGE" in failures


def test_unknown_field_id_fails_closed() -> None:
    failures = _plan_failures(
        lambda plan: plan["field_coverage"][0].update(field_id="unknown_pr138_field")
    )
    assert any("PR140_UNKNOWN_FIELD_ID" in failure for failure in failures)


def test_all_eight_field_groups_are_represented_and_counts_match() -> None:
    plan = _plan()
    inventory = _inventory()
    expected_groups = {group["field_group_id"] for group in inventory["field_groups"]}
    actual_groups = {group["field_group_id"] for group in plan["field_group_coverage"]}
    assert actual_groups == expected_groups
    for group in plan["field_group_coverage"]:
        assert group["coverage_plan_complete"] is True
        assert group["required_field_count"] == len(group["required_field_ids"])
        assert group["covered_field_count"] == len(group["required_field_ids"])
        assert group["semantic_values_materialized"] is False


def test_row_id_is_only_present_existing_field_and_58_fields_remain_planned() -> None:
    plan = _plan()
    present = [
        field["field_id"]
        for field in plan["field_coverage"]
        if field["coverage_status"] == "PRESENT_EXISTING_ID_ONLY"
    ]
    assert present == ["row_id"]
    assert plan["existing_supported_field_ids"] == ["row_id"]
    assert plan["missing_or_planned_field_count"] == 58


def test_all_15_row_family_sources_are_represented() -> None:
    plan = _plan()
    manifest = _pr139_manifest()
    expected_paths = {
        entry["source_file_path"]
        for entry in manifest["row_family_source_manifest"]["row_family_entries"]
    }
    actual_paths = {
        entry["row_family_source_file_path"]
        for entry in plan["row_family_source_coverage"]
    }
    assert len(actual_paths) == 15
    assert actual_paths == expected_paths


def test_unknown_row_family_source_file_fails_closed() -> None:
    failures = _plan_failures(
        lambda plan: plan["row_family_source_coverage"][0].update(
            row_family_source_file_path=(
                "docs/master_plan/atomic_rows/pr98_row_family_sources/999_unknown.source.jsonl"
            )
        )
    )
    assert "PR140_UNKNOWN_OR_MISSING_ROW_FAMILY_SOURCE" in failures


def test_row_family_source_mutation_or_materialization_flags_fail_closed() -> None:
    mutation_failures = _plan_failures(
        lambda plan: plan["row_family_source_coverage"][0].update(
            mutation_allowed_by_pr140=True
        )
    )
    materialized_failures = _plan_failures(
        lambda plan: plan["row_family_source_coverage"][0].update(
            semantic_values_materialized_by_pr140=True
        )
    )
    assert any("PR140_SOURCE_MUTATION_ALLOWED" in failure for failure in mutation_failures)
    assert any(
        "PR140_SOURCE_VALUES_MATERIALIZED" in failure
        for failure in materialized_failures
    )


def test_authority_boundaries_remain_false_in_plan_and_report() -> None:
    plan = _plan()
    report = _report()
    assert plan["authority_boundaries"] == c.AUTHORITY_BOUNDARIES
    assert report["authority_boundaries"] == c.AUTHORITY_BOUNDARIES
    assert report["authority_class"] == c.AUTHORITY_CLASS
    assert report["final_ready"] is False
    assert report["day1_launch_ready"] is False
    assert report["semantic_values_materialized"] is False
    assert report["row_family_sources_mutated"] is False
    assert report["atomicrows_bundle_mutated"] is False
    assert report["master_plan_mutated"] is False


def test_live_order_profit_source_connector_replay_paper_quantum_authority_is_false() -> None:
    boundaries = _report()["authority_boundaries"]
    for key in (
        "source_acceptance_created",
        "connector_semantic_binding_created",
        "replay_execution_created",
        "paper_execution_created",
        "replay_result_created",
        "paper_result_created",
        "runtime_live_order_authority_created",
        "order_execution_created",
        "fill_receipt_created",
        "profit_evidence_created",
        "alpha_evidence_created",
        "latency_superiority_claimed",
        "execution_superiority_claimed",
        "quantum_optimizer_input_created",
        "quantum_optimizer_output_created",
        "quantum_backend_execution_created",
        "quantum_simulator_execution_created",
        "quantum_advantage_claimed",
        "qtt_integrity_authority_created",
    ):
        assert boundaries[key] is False


def test_qtt_integrity_authority_and_bundle_sidecar_references_fail_closed() -> None:
    integrity_failures = _plan_failures(
        lambda plan: plan.update(qtt_generated_integrity_authority=True)
    )
    sidecar_failures = _plan_failures(
        lambda plan: plan["field_coverage"][0].update(
            rationale="forbidden AtomicRows.bundle.sha sidecar reference"
        )
    )
    assert any("INTEGRITY_AUTHORITY_FORBIDDEN" in failure for failure in integrity_failures)
    assert any("BUNDLE_SIDECAR_REFERENCE_FORBIDDEN" in failure for failure in sidecar_failures)


def test_changed_path_guard_allows_only_narrow_repair_paths() -> None:
    allowed_pr138_repairs = {
        "src/qtt/stage1_prediction_markets/atomicrows_semantic_contract/validator.py",
        "tests/atomicrows/test_pr138_atomicrows_semantic_row_contract.py",
    }
    allowed_pr139_ordering_repair = (
        "tests/atomicrows/test_atomicrows_row_family_source_manifest_currentization.py"
    )
    allowed_linux_determinism_repairs = {
        "src/qtt/stage1_prediction_markets/orderbook_event_state_snapshot/validator.py",
        "tools/build_master_plan_section_coverage_report.py",
    }
    forbidden_pr138_artifacts = {
        "docs/master_plan/generated/PR138_AtomicRowsSemanticFieldInventory.json",
        "docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.index.json",
        "docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json",
        "schemas/atomicrows/atomicrows_semantic_row_contract.schema.json",
        (
            "tests/fixtures/atomicrows/pr138_semantic_row_contract/"
            "semantic_contract_fixtures.v1.fixture.json"
        ),
    }
    forbidden_broad_test_paths = {
        "tests/atomicrows",
        "tests/atomicrows/",
        "tests/atomicrows/**",
    }

    assert allowed_pr138_repairs.issubset(c.ALLOWED_PR140_CHANGED_PATHS)
    assert allowed_pr139_ordering_repair in c.ALLOWED_PR140_CHANGED_PATHS
    assert allowed_linux_determinism_repairs.issubset(c.ALLOWED_PR140_CHANGED_PATHS)
    assert c.ALLOWED_PR140_CHANGED_PATHS.isdisjoint(forbidden_pr138_artifacts)
    assert c.ALLOWED_PR140_CHANGED_PATHS.isdisjoint(forbidden_broad_test_paths)
    assert c.ALLOWED_PR140_CHANGED_PATHS.isdisjoint(
        c.PR141_DOWNSTREAM_AUTHORIZATION_GATE_CHANGED_PATHS
    )
    assert c.ALLOWED_PR140_CHANGED_PATHS.isdisjoint(
        c.PR142_DOWNSTREAM_HANDOFF_READINESS_GATE_CHANGED_PATHS
    )
    assert c.IGNORED_PR140_CHANGED_PATH_PATTERNS == (".tmp/", ".tmp/**")
    assert c.ALLOWED_PR140_CHANGED_PATHS.isdisjoint(c.IGNORED_PR140_CHANGED_PATH_PATTERNS)


def test_changed_path_guard_allows_exact_pr141_downstream_handoff_files_only(monkeypatch) -> None:
    assert c.PR141_DOWNSTREAM_ALLOWANCE_REASON_CODE == (
        "PR141_DOWNSTREAM_AUTHORIZATION_GATE_CONSUMES_PR140_HANDOFF"
    )
    downstream_branch = (
        "pr141-atomicrows-semantic-value-materialization-owner-authorization-gate"
    )
    for path in c.PR141_DOWNSTREAM_AUTHORIZATION_GATE_CHANGED_PATHS:
        assert _is_pr141_downstream_changed_path_for_branch(
            path,
            downstream_branch,
        )
        assert _is_pr141_downstream_changed_path_for_branch(
            path,
            "pr142-future-roadmap-branch",
        )
        assert not _is_pr141_downstream_changed_path_for_branch(
            path,
            c.BRANCH,
        )
        assert not _is_pr141_downstream_changed_path_for_branch(path, "main")
        assert not _is_pr141_downstream_changed_path_for_branch(path, "")

    monkeypatch.setattr(
        pr140_report,
        "current_branch_context",
        lambda repo_root: BranchContext(branch=downstream_branch, source="unit-test"),
    )
    for path in c.PR141_DOWNSTREAM_AUTHORIZATION_GATE_CHANGED_PATHS:
        assert _is_allowed_pr140_changed_path(path, REPO_ROOT)


def test_changed_path_guard_allows_exact_pr142_downstream_handoff_files_only(monkeypatch) -> None:
    downstream_branch = (
        "pr142-atomicrows-semantic-value-materialization-authorization-handoff-gate"
    )
    for path in c.PR142_DOWNSTREAM_HANDOFF_READINESS_GATE_CHANGED_PATHS:
        assert _is_pr142_downstream_changed_path_for_branch(path, downstream_branch)
        assert _is_pr142_downstream_changed_path_for_branch(
            path,
            "pr143k-future-roadmap-branch",
        )
        assert not _is_pr142_downstream_changed_path_for_branch(path, c.BRANCH)
        assert not _is_pr142_downstream_changed_path_for_branch(path, "main")
        assert not _is_pr142_downstream_changed_path_for_branch(path, "")

    monkeypatch.setattr(
        pr140_report,
        "current_branch_context",
        lambda repo_root: BranchContext(branch=downstream_branch, source="unit-test"),
    )
    for path in c.PR142_DOWNSTREAM_HANDOFF_READINESS_GATE_CHANGED_PATHS:
        assert _is_allowed_pr140_changed_path(path, REPO_ROOT)


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
        pr140_report,
        "current_branch_context",
        lambda repo_root: BranchContext(branch=downstream_branch, source="unit-test"),
    )
    for path in c.PR143_OWNER_GLOBAL_OVERRIDE_CURRENTIZATION_CHANGED_PATHS:
        assert _is_allowed_pr140_changed_path(path, REPO_ROOT)


def test_changed_path_guard_rejects_pr141_downstream_handoff_files_on_main_and_detached_context(
    monkeypatch,
) -> None:
    for branch in ("main", ""):
        monkeypatch.setattr(
            pr140_report,
            "current_branch_context",
            lambda repo_root, branch=branch: BranchContext(
                branch=branch,
                source="unit-test",
            ),
        )
        for path in c.PR141_DOWNSTREAM_AUTHORIZATION_GATE_CHANGED_PATHS:
            assert not _is_allowed_pr140_changed_path(path, REPO_ROOT)
        for path in c.PR142_DOWNSTREAM_HANDOFF_READINESS_GATE_CHANGED_PATHS:
            assert not _is_allowed_pr140_changed_path(path, REPO_ROOT)


def test_changed_path_guard_rejects_broad_pr141_like_directories() -> None:
    broad_paths = {
        "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_owner_authorization_gate/",
        "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_owner_authorization_gate",
        "tests/fixtures/atomicrows/",
        "docs/master_plan/atomic_rows/",
    }
    assert c.PR141_DOWNSTREAM_AUTHORIZATION_GATE_CHANGED_PATHS.isdisjoint(broad_paths)
    assert c.PR142_DOWNSTREAM_HANDOFF_READINESS_GATE_CHANGED_PATHS.isdisjoint(broad_paths)
    for path in broad_paths:
        assert not _is_pr141_downstream_changed_path_for_branch(
            path,
            "pr141-atomicrows-semantic-value-materialization-owner-authorization-gate",
        )
        assert not _is_pr142_downstream_changed_path_for_branch(
            path,
            "pr142-atomicrows-semantic-value-materialization-authorization-handoff-gate",
        )


def test_changed_path_guard_keeps_generated_evidence_and_protected_paths_disallowed() -> None:
    disallowed_paths = {
        "docs/master_plan/generated/AtomicRowsUnexpectedSideEffect.report.json",
        "docs/master_plan/generated/PR138_AtomicRowsSemanticFieldInventory.json",
        "docs/master_plan/generated/PR138_AtomicRowsSemanticRowContract.report.json",
        "docs/master_plan/generated/AtomicRowsRowFamilySourceManifestCurrentization.report.json",
        "docs/master_plan/generated/AtomicRowsSemanticFieldCoverageEnrichmentPlan.report.json.unexpected",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
        "docs/master_plan/atomic_rows/pr98_row_family_sources/001_signal_features.source.jsonl",
        "src/qtt/stage1_prediction_markets/connector_semantic_binding/validator.py",
        "src/qtt/stage1_prediction_markets/runtime_resolver/validator.py",
        "src/qtt/stage1_prediction_markets/replay_paper/validator.py",
        "src/qtt/stage1_prediction_markets/atomicrows_semantic_value_materialization_owner_authorization_gate/extra.py",
        "requirements.txt",
    }
    for path in disallowed_paths:
        assert path not in c.ALLOWED_PR140_CHANGED_PATHS
        assert not _is_pr141_downstream_changed_path_for_branch(
            path,
            "pr141-atomicrows-semantic-value-materialization-owner-authorization-gate",
        )


def test_pr141_downstream_allowance_is_handoff_not_materialization() -> None:
    plan = _plan()
    handoff = plan["downstream_handoff_contract"]
    assert handoff["pr140_creates_downstream_input_for"] == ["PR141", "PR142"]
    assert handoff["downstream_owner_authorization_required_for_materialization"] is True
    assert plan["semantic_values_materialized"] is False
    assert plan["authority_boundaries"]["semantic_values_materialized"] is False
    assert plan["authority_boundaries"]["bundle_mutation_allowed_flag"] is False
    assert plan["authority_boundaries"]["source_acceptance_created"] is False
    assert plan["authority_boundaries"]["connector_semantic_binding_created"] is False
    assert plan["authority_boundaries"]["runtime_live_order_authority_created"] is False
    assert plan["authority_boundaries"]["quantum_backend_execution_created"] is False
    assert plan["final_ready"] is False


def test_changed_path_guard_ignores_only_runtime_tmp_directory() -> None:
    assert _is_ignored_pr140_changed_path(".tmp/")
    assert _is_ignored_pr140_changed_path(".tmp/pr133_deterministic_report_test")
    assert _is_ignored_pr140_changed_path(".tmp/nested/output.json")
    assert not _is_ignored_pr140_changed_path(".tmpfile")
    assert not _is_ignored_pr140_changed_path("tmp/")
    assert not _is_ignored_pr140_changed_path(
        "docs/master_plan/generated/MasterPlanSectionCoverageReport.json"
    )


def test_pr136_crosswalk_alias_resolution_and_evidence_consumption_are_recorded() -> None:
    report = _report()
    assert report["crosswalk_alias_resolution"] == {
        "requested_alias": c.CROSSWALK_REQUESTED_ALIAS.as_posix(),
        "alias_exists": False,
        "canonical_crosswalk_used": c.CROSSWALK_CANONICAL.as_posix(),
        "created_missing_alias": False,
    }
    assert "docs/master_plan/generated/PR136RouteTriage.report.json" in report["pr136_evidence_consumed"]
    assert "docs/master_plan/generated/PR136CommandActionMatrix.report.json" in report["pr136_evidence_consumed"]
    assert "docs/master_plan/generated/PR136MarketSpecificLaunchReadinessIndex.report.json" in report["pr136_evidence_consumed"]
    assert "docs/master_plan/generated/PR136AgentLaunchOrchestrationMap.report.json" in report["pr136_evidence_consumed"]
    assert "docs/master_plan/generated/PR136LaunchReadinessDependencyGraph.report.json" in report["pr136_evidence_consumed"]
    assert "docs/master_plan/generated/PR136QuantumAtomicRowsOptimizationReadinessMap.report.json" in report["pr136_evidence_consumed"]


def test_downstream_handoff_contract_does_not_authorize_pr141_or_pr142_work() -> None:
    handoff = _report()["downstream_handoff_contract"]
    assert handoff["pr140_creates_downstream_input_for"] == ["PR141", "PR142"]
    assert handoff["downstream_owner_authorization_required_for_materialization"] is True
    assert handoff["no_same_number_identity_inference"] is True
    assert "semantic_value_materialization" in handoff["downstream_scope_not_authorized_by_pr140"]
    assert "final_readiness" in handoff["downstream_scope_not_authorized_by_pr140"]


def test_market_scope_coverage_contains_four_canonical_scopes_without_authority() -> None:
    scopes = _report()["market_scope_coverage"]["market_scopes"]
    assert {scope["scope_id"] for scope in scopes} == set(c.MARKET_SCOPE_IDS)
    for scope in scopes:
        assert scope["external_fact_authority_created"] is False
        assert scope["connector_binding_created"] is False
        assert scope["live_use_allowed_created"] is False
        assert scope["future_source_packet_dependency_class"] == (
            "ACCEPTED_SOURCE_PACKET_DEPENDENT"
        )


def test_agent_orchestration_coverage_is_static_metadata_only() -> None:
    coverage = _report()["agent_orchestration_coverage"]
    assert coverage["agent_domain_count"] == 19
    for domain in coverage["agent_domains"]:
        assert domain["may_consume_pr140_plan_as_static_metadata"] is True
        assert domain["live_order_authority_allowed"] is False
        assert domain["latency_hot_path_allowed"] is False
        assert domain["final_order_submission_authority_created"] is False


def test_latency_hot_path_exclusion_matrix_blocks_forbidden_work() -> None:
    matrix = _report()["latency_hot_path_exclusion_matrix"]
    for key, expected in c.LATENCY_HOT_PATH_EXCLUSION_MATRIX.items():
        assert matrix[key] == expected
    assert matrix["future_live_path_consumption_mode"] == "PRECOMPUTED_SNAPSHOT_ONLY"


def test_quantum_forward_metadata_plan_has_references_without_execution_or_advantage() -> None:
    quantum = _report()["quantum_forward_metadata_plan"]
    for key in (
        "future_qaoa_depth_p_ref",
        "future_qaoa_qubo_constraint_ref",
        "future_qubo_penalty_scale_ref",
        "future_ising_model_ref",
        "future_vqe_ansatz_ref",
        "future_annealing_schedule_ref",
        "future_shot_budget_ref",
        "future_seed_control_ref",
        "future_backend_provider_class_ref",
        "future_classical_comparator_ref",
    ):
        assert quantum[key].startswith("FUTURE_")
    assert quantum["no_quantum_execution_flag"] is True
    assert quantum["no_quantum_advantage_claim_flag"] is True
    assert quantum["no_quantum_signal_creation_flag"] is True
    assert quantum["quantum_metadata_only"] is True
    assert quantum["quantum_backend_execution_allowed_flag_forced_false"] is True


def test_repository_artifacts_validate_and_report_is_deterministic(monkeypatch) -> None:
    _outputs()
    _restore_tracked_generated_side_effects()
    monkeypatch.setattr(
        pr140_report,
        "current_branch_context",
        lambda repo_root: BranchContext(
            branch="repair-pr153r-redo-report-determinism",
            source="unit-test",
        ),
    )
    assert validate_repository_artifacts(REPO_ROOT) == []
    assert build_report(REPO_ROOT) == build_report(REPO_ROOT)
    assert validate_report_payload(_report(), build_report(REPO_ROOT)) == []


def test_validation_gate_sequence_includes_pr140_after_pr139_and_before_pytest(monkeypatch) -> None:
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)
    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]

    assert command_names.index("validate_atomicrows_row_family_source_manifest_currentization.py") < command_names.index(
        "validate_atomicrows_semantic_field_coverage_enrichment_plan.py"
    ) < command_names.index("run_pytest_fresh_basetemp.py")
