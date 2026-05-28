from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from tools.build_master_plan_section_coverage_report import load_yaml_subset
from tools.ci_branch_context import BranchContext
from tools.validate_master_plan_section_coverage import validate_json_schema_subset

from src.qtt.stage1_prediction_markets.atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate import (
    builder as pr142_builder,
    constants as c,
    report as pr142_report,
)
from src.qtt.stage1_prediction_markets.pr160_split_reclassification_route_closure import (
    constants as pr160_constants,
)
from src.qtt.stage1_prediction_markets.atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.report import (
    _is_allowed_pr142_changed_path,
    _is_allowed_pr142_changed_path_for_branch,
    _is_pr138_mainline_context_repair_changed_path_for_branch,
    _is_pr146_generated_report_nonmutating_validation_repair_changed_path_for_branch,
    build_json_schema,
    build_report,
    validate_payload,
    validate_repository_artifacts,
)
from tools import run_validation_gates as runner
from tools import (
    validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate
    as pr142_cli,
)


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


def test_cli_default_validation_does_not_rewrite_tracked_report(capsys) -> None:
    report_path = REPO_ROOT / c.REPORT_PATH
    before = report_path.read_bytes()

    assert pr142_cli.main(["--repo-root", str(REPO_ROOT)]) == 0

    assert report_path.read_bytes() == before
    assert c.SUCCESS_MARKER in capsys.readouterr().out


def test_cli_write_artifacts_mode_is_explicit_opt_in(monkeypatch, capsys) -> None:
    calls: list[Path] = []
    repo_root = REPO_ROOT / ".tmp" / "pr142_write_artifacts_opt_in_unit"

    def fake_write_all_artifacts(repo_root: Path) -> dict:
        calls.append(repo_root)
        return {}

    monkeypatch.setattr(pr142_cli, "write_all_artifacts", fake_write_all_artifacts)
    monkeypatch.setattr(pr142_cli, "validate_repository_artifacts", lambda repo_root: [])

    assert pr142_cli.main(["--repo-root", str(repo_root), "--write-artifacts"]) == 0

    assert calls == [repo_root.resolve()]
    assert c.SUCCESS_MARKER in capsys.readouterr().out


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


def test_schema_rejects_missing_required_identity() -> None:
    payload = _report()
    payload.pop("authority_class")
    failures = validate_json_schema_subset(payload, _schema())
    assert any("missing required field authority_class" in failure for failure in failures)


def test_constants_schema_report_alignment_is_centralized() -> None:
    schema = _schema()
    report = _report()
    assert report["artifact_stem"] == c.ARTIFACT_STEM
    assert report["authority_class"] == c.AUTHORITY_CLASS
    assert report["validation_marker"] == c.SUCCESS_MARKER
    assert (
        schema["properties"]["authority_class"]["enum"]
        == list(c.AUTHORITY_CLASS_VALUES)
    )
    reason_enum = schema["properties"]["static_handoff_readiness_contract"][
        "properties"
    ]["blocked_reason_codes"]["items"]["enum"]
    assert reason_enum == list(c.BLOCK_REASON_CODES)
    assert (
        report["static_handoff_readiness_contract"]["blocked_reason_codes"]
        == list(c.BLOCK_REASON_CODES)
    )


def test_pr136_alias_resolution_uses_canonical_without_creating_alias() -> None:
    report = _report()
    alias_resolution = report["pr136_orchestration_preflight"]["alias_resolution"]
    assert alias_resolution == {
        "requested_alias": c.CROSSWALK_REQUESTED_ALIAS.as_posix(),
        "alias_exists": False,
        "canonical_crosswalk_used": c.CROSSWALK_CANONICAL.as_posix(),
        "created_missing_alias": False,
        "conflict_detected": False,
    }
    assert not (REPO_ROOT / c.CROSSWALK_REQUESTED_ALIAS).exists()


def test_required_pr136_and_atomicrows_evidence_lists_are_non_empty_and_exact() -> None:
    report = _report()
    assert report["pr136_orchestration_preflight"]["consumed_files"] == [
        path.as_posix() for path in c.PR136_EVIDENCE_PATHS
    ]
    assert report["upstream_atomicrows_evidence"]["consumed_files"] == [
        path.as_posix() for path in c.ATOMICROWS_EVIDENCE_PATHS
    ]
    assert report["pr136_orchestration_preflight"]["pr136_planning_authority_only"] is True
    assert (
        report["pr136_orchestration_preflight"][
            "pr136_does_not_authorize_materialization"
        ]
        is True
    )


def test_missing_evidence_fails_closed() -> None:
    _evidence, failures = pr142_builder.load_static_evidence(REPO_ROOT / ".tmp" / "missing")
    assert any("PR142_REQUIRED_EVIDENCE_MISSING" in failure for failure in failures)


def test_pr141_handoff_forbids_materialization_and_owner_approval_receipts() -> None:
    handoff = _report()["pr141_downstream_handoff_consumption"][
        "downstream_handoff_contract"
    ]
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
    assert (
        "PR142_PR141_FORBIDDEN_HANDOFF_TRUE: pr141_authorizes_materialization"
        in _payload_failures(
            lambda payload: payload["pr141_downstream_handoff_consumption"][
                "downstream_handoff_contract"
            ].update(pr141_authorizes_materialization=True)
        )
    )


def test_owner_approval_receipt_bundle_and_source_mutation_boundaries_fail_closed() -> None:
    approval_failures = _payload_failures(
        lambda payload: payload["no_claim_boundary"].update(
            owner_approval_receipt_created=True
        )
    )
    assert any("owner_approval_receipt_created" in failure for failure in approval_failures)

    bundle_failures = _payload_failures(
        lambda payload: payload["forbidden_authority_output_boundary"].update(
            atomicrows_bundle_mutation_created=True
        )
    )
    assert any("atomicrows_bundle_mutation_created" in failure for failure in bundle_failures)

    source_failures = _payload_failures(
        lambda payload: payload["forbidden_authority_output_boundary"].update(
            row_family_source_mutation_created=True
        )
    )
    assert any("row_family_source_mutation_created" in failure for failure in source_failures)


def test_quantum_and_optimizer_boundaries_are_metadata_only() -> None:
    quantum = _report()["quantum_forward_compatibility"]
    for key in c.QUANTUM_EXECUTION_FALSE_FIELDS:
        assert quantum[key] is False
    assert quantum["optimizer_parameter_value_source_status"] == (
        "NOT_MATERIALIZED_OR_NOT_ACCEPTED"
    )
    assert quantum["compatible_future_problem_forms"] == "UNKNOWN_PENDING_EVIDENCE"
    assert quantum["missing_optimizer_default_policy_route"] == (
        "BLOCK_UNTIL_ACCEPTED_EVIDENCE_OR_OWNER_POLICY"
    )
    assert set(quantum["metadata_only_fields"]) == set(c.QUANTUM_FORWARD_METADATA_ONLY_FIELDS)
    assert any(
        "qaoa_execution_created" in failure
        for failure in _payload_failures(
            lambda payload: payload["quantum_forward_compatibility"].update(
                qaoa_execution_created=True
            )
        )
    )


def test_classical_optimizer_forward_compatibility_does_not_execute() -> None:
    classical = _report()["classical_optimizer_forward_compatibility"]
    for key in c.CLASSICAL_OPTIMIZER_FALSE_FIELDS:
        assert classical[key] is False
    for key in c.CLASSICAL_OPTIMIZER_METADATA_ONLY_FIELDS:
        assert classical[key] is True
    assert set(classical["metadata_only_fields"]) == set(
        c.CLASSICAL_OPTIMIZER_METADATA_ONLY_FIELDS
    )


def test_source_evidence_packet_is_policy_not_external_fact_authority() -> None:
    source = _report()["source_evidence_boundary"]
    assert source["source_evidence_packet_repo_path_present"] is True
    assert source["owner_policy_may_authorize_retrieval_scope"] is True
    assert source["owner_policy_may_authorize_external_fact_value"] is False
    assert source["source_acceptance_created"] is False
    assert source["connector_semantic_binding_created"] is False
    assert source["runtime_cash_receipt_created"] is False
    assert source["missing_accepted_source_packets_block_runtime_use"] is True


def test_report_paths_are_os_stable_and_no_forbidden_bundle_reference_is_emitted() -> None:
    report = _report()
    for text in _walk_strings(report):
        assert "C:\\" not in text
        assert "\\\\" not in text
    serialized = json.dumps(report, sort_keys=True)
    assert c.forbidden_bundle_reference_text() not in serialized
    assert "AtomicRows.bundle.jsonl" not in serialized


def test_no_qtt_generated_integrity_authority_fields_except_vcs_metadata() -> None:
    report = _report()
    allowed = set(c.ALLOWED_VCS_METADATA_FIELD_NAMES)
    for key, _item in pr142_report._walk(report):
        lowered = key.lower()
        if key in allowed:
            continue
        assert not any(fragment in lowered for fragment in ("sha", "digest", "hash", "checksum"))


def test_changed_path_guard_uses_explicit_branch_context_simulation(monkeypatch) -> None:
    allowed_path = c.REPORT_PATH.as_posix()
    assert _is_allowed_pr142_changed_path_for_branch(allowed_path, c.BRANCH)
    assert _is_allowed_pr142_changed_path_for_branch(allowed_path, "pr143k-future")
    assert not _is_allowed_pr142_changed_path_for_branch(allowed_path, "main")
    assert not _is_allowed_pr142_changed_path_for_branch(allowed_path, "")

    monkeypatch.setattr(
        pr142_report,
        "current_branch_context",
        lambda repo_root: BranchContext(branch=c.BRANCH, source="unit-test"),
    )
    assert _is_allowed_pr142_changed_path(allowed_path, REPO_ROOT)


def test_changed_path_guard_allows_exact_pr138_mainline_context_repair_files_only(
    monkeypatch,
) -> None:
    assert c.PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_ALLOWANCE_REASON_CODE == (
        "PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_REQUIRED_FOR_PR144_DOWNSTREAM_VALIDATION"
    )
    for path in c.PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_CHANGED_PATHS:
        assert path not in c.ALLOWED_PR142_CHANGED_PATHS
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
            "pr142-atomicrows-semantic-value-materialization-authorization-handoff-gate",
        )
        assert not _is_pr138_mainline_context_repair_changed_path_for_branch(
            path,
            "pr138-atomicrows-semantic-row-contract",
        )
        assert not _is_pr138_mainline_context_repair_changed_path_for_branch(path, "main")
        assert not _is_pr138_mainline_context_repair_changed_path_for_branch(path, "")

    monkeypatch.setattr(
        pr142_report,
        "current_branch_context",
        lambda repo_root: BranchContext(
            branch="pr146-generated-report-nonmutating-validation-mode-audit",
            source="unit-test",
        ),
    )
    for path in c.PR138_MAINLINE_BRANCH_CONTEXT_REPAIR_CHANGED_PATHS:
        assert _is_allowed_pr142_changed_path(path, REPO_ROOT)


def test_changed_path_guard_allows_pr143_owner_override_currentization_files() -> None:
    pr143_paths = {
        "docs/master_plan/governance/QTTOwnerGlobalOverrideDirectiveCurrentizationAndInternalGateRelease.yaml",
        (
            "docs/master_plan/generated/"
            "QTTOwnerGlobalOverrideDirectiveCurrentizationAndInternalGateRelease.report.json"
        ),
        (
            "schemas/governance/"
            "qtt_owner_global_override_directive_currentization_and_internal_gate_release.schema.json"
        ),
        (
            "src/qtt/stage1_prediction_markets/"
            "qtt_owner_global_override_directive_currentization_and_internal_gate_release/constants.py"
        ),
        (
            "tools/"
            "validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py"
        ),
        (
            "tests/governance/"
            "test_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py"
        ),
    }
    assert pr143_paths.issubset(c.ALLOWED_PR142_CHANGED_PATHS)
    for path in pr143_paths:
        assert _is_allowed_pr142_changed_path_for_branch(path, "pr143-future")
        assert _is_allowed_pr142_changed_path_for_branch(path, "pr143k-future")
        assert not _is_allowed_pr142_changed_path_for_branch(path, "main")


def test_changed_path_guard_allows_exact_pr146_tooling_hygiene_files_only() -> None:
    assert c.PR146_GENERATED_REPORT_NONMUTATING_VALIDATION_REPAIR_ALLOWANCE_REASON_CODE == (
        "PR146_GENERATED_REPORT_NONMUTATING_VALIDATION_REPAIR_REQUIRED"
    )
    for path in c.PR146_GENERATED_REPORT_NONMUTATING_VALIDATION_REPAIR_CHANGED_PATHS:
        assert _is_pr146_generated_report_nonmutating_validation_repair_changed_path_for_branch(
            path,
            "pr146-generated-report-nonmutating-validation-mode-audit",
        )
        assert not _is_pr146_generated_report_nonmutating_validation_repair_changed_path_for_branch(
            path,
            c.BRANCH,
        )
        assert not _is_pr146_generated_report_nonmutating_validation_repair_changed_path_for_branch(
            path,
            "main",
        )
        assert not _is_pr146_generated_report_nonmutating_validation_repair_changed_path_for_branch(
            path,
            "",
        )


def test_changed_path_guard_rejects_protected_atomicrows_paths() -> None:
    disallowed_paths = {
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl",
        "docs/master_plan/atomic_rows/pr98_row_family_sources/001_signal_features.source.jsonl",
        "docs/master_plan/generated/PR136RouteTriage.report.json",
    }
    for path in disallowed_paths:
        assert path not in c.ALLOWED_PR142_CHANGED_PATHS
        assert not _is_pr138_mainline_context_repair_changed_path_for_branch(
            path,
            "pr144-pr138-mainline-branch-context-normalization",
        )
        assert not _is_allowed_pr142_changed_path_for_branch(path, c.BRANCH)


def test_repository_artifacts_validate_with_monkeypatched_branch_context(monkeypatch) -> None:
    monkeypatch.setattr(
        pr142_report,
        "current_branch_context",
        lambda repo_root: BranchContext(
            branch=pr160_constants.EXPECTED_BRANCH,
            source="unit-test",
        ),
    )
    assert validate_repository_artifacts(REPO_ROOT) == []
    assert build_report(REPO_ROOT) == build_report(REPO_ROOT)


def test_validation_gate_sequence_includes_pr142_after_pr141(monkeypatch) -> None:
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)
    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    assert command_names.index(
        "validate_atomicrows_semantic_value_materialization_owner_authorization_gate.py"
    ) < command_names.index(
        "validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py"
    ) < command_names.index("validate_qtt_owner_global_override_authority.py")
    pr142_command = commands[
        command_names.index(
            "validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py"
        )
    ]
    assert pr142_command == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py"
        ),
        "--repo-root",
        ".",
    ]
    assert "--write-artifacts" not in pr142_command
