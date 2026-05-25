from __future__ import annotations

import json
from pathlib import Path

from tools import run_validation_gates as runner
from tools import (
    validate_atomicrows_semantic_value_materialization_implementation_bridge
    as pr149_cli,
)
from tools.ci_branch_context import BranchContext

from src.qtt.stage1_prediction_markets.atomicrows_semantic_field_coverage_enrichment_plan import (
    constants as pr140_constants,
    report as pr140_report,
)
from src.qtt.stage1_prediction_markets.atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate import (
    constants as pr142_constants,
    report as pr142_report,
)
from src.qtt.stage1_prediction_markets.atomicrows_semantic_value_materialization_implementation_bridge import (
    constants as c,
    report as pr149_report,
)
from src.qtt.stage1_prediction_markets.atomicrows_semantic_value_materialization_owner_authorization_gate import (
    constants as pr141_constants,
    report as pr141_report,
)
from src.qtt.stage1_prediction_markets.qtt_owner_global_override_directive_currentization_and_internal_gate_release import (
    constants as pr143_constants,
    report as pr143_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _report() -> dict:
    return pr149_report.build_report(REPO_ROOT)


def _serialized_report() -> str:
    return json.dumps(_report(), sort_keys=True)


def _copy_inputs(tmp_path: Path) -> Path:
    for rel_path in (*c.ALLOWED_INPUT_ARTIFACT_PATHS, *c.OPTIONAL_CONTEXT_ARTIFACT_PATHS):
        source = REPO_ROOT / rel_path
        if source.exists():
            target = tmp_path / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
    return tmp_path


def test_pr149_consumes_required_upstream_chain_and_alias() -> None:
    report = _report()
    consumed = {
        row["artifact_path"]
        for row in report["upstream_artifact_inputs"]
        if row["consumed"]
    }
    for rel_path in c.ALLOWED_INPUT_ARTIFACT_PATHS:
        assert rel_path.as_posix() in consumed
    alias = report["orchestration_preflight_receipt"]["alias_resolution"]
    assert alias["requested_alias"] == c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix()
    assert alias["canonical_successor_used"] is True
    assert alias["created_missing_alias"] is False
    assert not (REPO_ROOT / c.PR136_SECTION_CROSSWALK_ALIAS_PATH).exists()


def test_pr149_aligns_pr136_through_pr142_surfaces() -> None:
    report = _report()
    assert report["pr136_alignment_summary"]["route_receipt_type"] == (
        "PR136_ROUTE_TRIAGE_RECEIPT"
    )
    assert report["pr136_alignment_summary"]["market_scope_count"] == 4
    assert report["pr136_alignment_summary"]["command_action_count"] >= 1
    assert report["pr137r_alignment_summary"]["row_count_proven"] is True
    assert report["pr138_semantic_contract_summary"]["field_count"] == 59
    assert report["pr140_field_coverage_summary"]["validation_marker"] == (
        "QTT_ATOMICROWS_SEMANTIC_FIELD_COVERAGE_ENRICHMENT_PLAN_OK"
    )
    assert report["pr141_owner_authorization_summary"]["validation_marker"] == (
        "QTT_ATOMICROWS_SEMANTIC_VALUE_MATERIALIZATION_OWNER_AUTHORIZATION_GATE_OK"
    )
    assert report["pr142_handoff_readiness_summary"]["validation_marker"] == (
        "QTT_ATOMICROWS_SEMANTIC_VALUE_MATERIALIZATION_AUTHORIZATION_HANDOFF_"
        "READINESS_GATE_OK"
    )


def test_report_is_deterministic_and_uses_centralized_constants() -> None:
    first = pr149_report.build_report(REPO_ROOT)
    second = pr149_report.build_report(REPO_ROOT)
    assert first == second
    assert pr149_report.json_dump(first) == pr149_report.json_dump(second)
    assert first["report_id"] == c.REPORT_ID
    assert first["authority_class"] == c.AUTHORITY_CLASS
    assert first["readiness_class"] == c.READINESS_CLASS
    assert first["centralized_reason_codes"] == list(c.REASON_CODES)
    assert first["centralized_state_enums"]["materialization_state"] == list(
        c.MATERIALIZATION_STATE_VALUES
    )


def test_validation_default_does_not_mutate_tracked_report(capsys) -> None:
    report_path = REPO_ROOT / c.REPORT_PATH
    before = report_path.read_bytes()

    assert pr149_cli.main(["--repo-root", REPO_ROOT.as_posix()]) == 0

    assert report_path.read_bytes() == before
    assert c.SUCCESS_MARKER in capsys.readouterr().out


def test_output_path_and_tracked_write_modes_are_explicit(capsys, tmp_path) -> None:
    report_path = REPO_ROOT / c.REPORT_PATH
    before = report_path.read_bytes()
    output_path = tmp_path / "pr149.report.json"

    assert pr149_cli.main(["--repo-root", REPO_ROOT.as_posix(), "--output", output_path.as_posix()]) == 0
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == _report()
    assert sorted(
        path.relative_to(tmp_path).as_posix()
        for path in tmp_path.rglob("*")
        if path.is_file()
    ) == ["pr149.report.json"]
    assert report_path.read_bytes() == before

    assert pr149_cli.main(["--repo-root", REPO_ROOT.as_posix(), "--write-report"]) == 0
    assert report_path.read_bytes() == before
    assert c.SUCCESS_MARKER in capsys.readouterr().out


def test_explicit_tracked_write_guard_allows_only_pr149_report_on_main(monkeypatch) -> None:
    report_path = c.REPORT_PATH.as_posix()
    unrelated_path = "docs/master_plan/generated/PR149_unrelated.report.json"
    expected_report_failure = f"PR149_CHANGED_PATH_OUT_OF_SCOPE: {report_path}"
    expected_unrelated_failure = f"PR149_CHANGED_PATH_OUT_OF_SCOPE: {unrelated_path}"

    monkeypatch.setattr(
        pr149_report,
        "current_branch_context",
        lambda repo_root: BranchContext(branch="main", source="unit-test"),
    )
    monkeypatch.setattr(pr149_report, "_changed_paths", lambda repo_root: [report_path])

    assert pr149_report.validate_repository_artifacts(REPO_ROOT) == [
        expected_report_failure
    ]
    assert (
        pr149_report.validate_repository_artifacts(
            REPO_ROOT,
            tracked_report_write_allowed=True,
        )
        == []
    )

    monkeypatch.setattr(
        pr149_report,
        "_changed_paths",
        lambda repo_root: [report_path, unrelated_path],
    )

    assert pr149_report.validate_repository_artifacts(
        REPO_ROOT,
        tracked_report_write_allowed=True,
    ) == [expected_unrelated_failure]


def test_missing_and_malformed_upstream_fail_closed(tmp_path) -> None:
    _evidence, missing_failures = pr149_report.load_static_evidence(tmp_path / "empty")
    assert any(failure.startswith("PR149_UPSTREAM_REPORT_MISSING") for failure in missing_failures)

    copied_root = _copy_inputs(tmp_path / "malformed")
    bad_path = copied_root / c.PR138_REPORT_PATH
    bad_path.write_text("{", encoding="utf-8")
    _evidence, parse_failures = pr149_report.load_static_evidence(copied_root)
    assert any(
        failure.startswith("PR149_UPSTREAM_REPORT_PARSE_ERROR")
        for failure in parse_failures
    )


def test_atomicrows_bundle_and_sidecar_boundaries_are_not_crossed() -> None:
    bundle_path = REPO_ROOT / c.ATOMICROWS_BUNDLE_PATH
    before = bundle_path.read_bytes()

    report = _report()

    assert bundle_path.read_bytes() == before
    assert report["atomicrows_compatibility_surface"]["bundle_mutation_created"] is False
    assert report["atomicrows_compatibility_surface"]["qtt_integrity_authority_created"] is False
    serialized = _serialized_report()
    assert "AtomicRows.bundle." not in serialized
    assert ("AtomicRows.bundle." + "sha" + "256") not in serialized


def test_no_claim_flags_cover_runtime_market_quantum_and_readiness_boundaries() -> None:
    report = _report()
    flags = report["centralized_no_claim_flags"]
    assert flags == c.NO_CLAIM_FLAGS
    assert all(value is False for value in flags.values())
    for item in report["semantic_value_materialization_packet"]["materialization_items"]:
        assert item["no_claim_flags"] == c.NO_CLAIM_FLAGS
        assert item["evidence_boundary"]["materialized_value_created"] is False


def test_materialization_items_are_typed_without_invented_values() -> None:
    report = _report()
    items = report["semantic_value_materialization_packet"]["materialization_items"]
    assert len(items) == 59
    assert [item["semantic_item_id"] for item in items] == sorted(
        item["semantic_item_id"] for item in items
    )
    states = {item["materialization_state"] for item in items}
    value_classes = {item["value_source_class"] for item in items}
    assert "IMPLEMENTATION_BRIDGE_READY" in states
    assert "CONFIGURATION_READY_WITH_TYPED_LIMITS" in states
    assert "METADATA_ONLY_READY" in states
    assert "BLOCKED_EXTERNAL_FACT_REQUIRED" in states
    assert "BLOCKED_RUNTIME_RECEIPT_REQUIRED" in states
    assert "SOURCE_EVIDENCE_REQUIRED_EXTERNAL_FACT_VALUE" in value_classes
    assert "RUNTIME_RECEIPT_REQUIRED_VALUE" in value_classes
    assert "QUANTUM_FORWARD_METADATA_VALUE" in value_classes
    assert all("materialized_value" not in item for item in items)


def test_downstream_agent_surface_remains_static_configuration_only() -> None:
    report = _report()
    surfaces = report["downstream_agent_configuration_surface"]
    assert surfaces
    assert {
        surface["downstream_agent_surface_class"]
        for surface in surfaces
    }.issubset(set(c.DOWNSTREAM_AGENT_SURFACE_CLASS_VALUES))
    for surface in surfaces:
        assert surface["may_consume_pr149_static_metadata"] is True
        assert all(value is False for value in surface["surface_authority"].values())
        assert surface["no_claim_flags"] == c.NO_CLAIM_FLAGS


def test_market_and_source_surfaces_remain_evidence_pending() -> None:
    report = _report()
    assert {row["canonical_venue_id"] for row in report["market_specific_surface"]} == {
        "FORECASTEX_IBKR",
        "KALSHI",
        "POLYMARKET",
        "PREDICTION_MARKETS_GENERAL",
    }
    for row in report["market_specific_surface"]:
        assert row["materialization_state"] == "BLOCKED_EXTERNAL_FACT_REQUIRED"
        assert row["venue_specific_value_created"] is False
        assert row["reason_codes"] == ["PR149_EXTERNAL_FACT_EVIDENCE_REQUIRED"]
    source = report["source_evidence_boundary_surface"]
    assert source["owner_source_policy_packet_present"] is True
    assert source["policy_context_only"] is True
    assert source["accepted_source_packet_created"] is False
    assert source["connector_semantic_authority_created"] is False
    assert source["runtime_cash_receipt_created"] is False


def test_quantum_surface_is_metadata_only() -> None:
    quantum = _report()["quantum_forward_compatibility_surface"]
    assert quantum["quantum_forward_state"] == c.QUANTUM_FORWARD_STATE
    assert quantum["quantum_applicability_metadata_only"] is True
    assert quantum["qaoa_compatible_metadata_only"] is True
    assert quantum["vqe_compatible_metadata_only"] is True
    assert quantum["annealing_compatible_metadata_only"] is True
    assert quantum["qubo_compatible_metadata_only"] is True
    assert quantum["ising_compatible_metadata_only"] is True
    assert quantum["quantum_optimizer_candidate_metadata_only"] is True
    assert quantum["strongest_classical_comparator_required_metadata_only"] is True
    assert quantum["quantum_execution_evidence_pending"] is True
    assert quantum["quantum_live_hot_path_excluded"] is True
    assert _report()["centralized_no_claim_flags"]["quantum_backend_execution_created"] is False
    assert _report()["centralized_no_claim_flags"]["quantum_simulator_execution_created"] is False
    assert _report()["centralized_no_claim_flags"]["quantum_advantage_evidence_created"] is False


def test_hidden_default_and_institutional_value_guards() -> None:
    guard = _report()["hidden_default_guard"]
    assert guard["hidden_default_created"] is False
    assert guard["institutional_parameter_value_invented"] is False
    assert guard["venue_fact_value_created"] is False
    assert guard["optimizer_parameter_value_invented"] is False
    assert guard["external_fact_value_created"] is False


def test_changed_path_allowances_are_exact_and_pr148_remains_narrow() -> None:
    pr149_path = c.REPORT_PATH.as_posix()
    assert pr149_path in c.CHANGED_PATH_EXACT_ALLOWANCE_CANDIDATES
    assert "docs/master_plan/generated/" not in c.CHANGED_PATH_EXACT_ALLOWANCE_CANDIDATES
    assert pr140_constants.PR148_POST_PR147_VALIDATION_STABLE_CHECKPOINT_CURRENTIZATION_CHANGED_PATHS == {
        "docs/master_plan/generated/QttPrIdentityRoster.report.json",
        "docs/roadmap/QTT_PR_Identity_Roster_v1_0.json",
        "docs/roadmap/QTT_Roadmap_Execution_State_Controller_v1_0.json",
    }
    for constants_module in (
        pr140_constants,
        pr141_constants,
        pr142_constants,
        pr143_constants,
    ):
        assert set(constants_module.PR149_IMPLEMENTATION_BRIDGE_CHANGED_PATHS) == set(
            c.CHANGED_PATH_EXACT_ALLOWANCE_CANDIDATES
        )
    assert pr140_report._is_pr149_implementation_bridge_changed_path_for_branch(
        pr149_path,
        c.BRANCH,
    )
    assert pr141_report._is_pr149_implementation_bridge_changed_path_for_branch(
        pr149_path,
        c.BRANCH,
    )
    assert pr142_report._is_pr149_implementation_bridge_changed_path_for_branch(
        pr149_path,
        c.BRANCH,
    )
    assert pr143_report._is_pr149_implementation_bridge_changed_path_for_branch(
        pr149_path,
        c.BRANCH,
    )


def test_validation_gate_sequence_includes_pr149_without_tracked_write() -> None:
    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr143_index = command_names.index(
        "validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py"
    )
    pr149_index = command_names.index(
        "validate_atomicrows_semantic_value_materialization_implementation_bridge.py"
    )
    agent_index = command_names.index("validate_qtt_agent_role_operating_charter_registry.py")
    assert pr143_index < pr149_index < agent_index
    assert commands[pr149_index] == [
        runner.sys.executable,
        str(Path("tools") / "validate_atomicrows_semantic_value_materialization_implementation_bridge.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr149_index]


def test_report_validator_rejects_forbidden_claim_mutations() -> None:
    report = _report()
    report["centralized_no_claim_flags"]["order_execution_created"] = True
    failures = pr149_report.validate_report_payload(report)
    assert any("order_execution_created" in failure for failure in failures)

    report = _report()
    report["hidden_default_guard"]["hidden_default_created"] = True
    failures = pr149_report.validate_report_payload(report)
    assert any("PR149_NO_HIDDEN_DEFAULTS" in failure for failure in failures)


def test_report_validator_rejects_forbidden_bundle_authority_payload() -> None:
    report = _report()
    report["atomicrows_compatibility_surface"]["bundle_mutation_created"] = True
    failures = pr149_report.validate_report_payload(report)
    assert "PR149_NO_BUNDLE_MUTATION_AUTHORITY" in failures

    report = _report()
    report["validation_summary"]["tracked_report_path"] = c.ATOMICROWS_BUNDLE_PATH.with_suffix(
        "." + "sha" + "256"
    ).as_posix()
    failures = pr149_report.validate_report_payload(report)
    assert "PR149_NO_BUNDLE_MUTATION_AUTHORITY" in failures


def test_valid_no_mutation_boundary_metadata_does_not_fail() -> None:
    report = _report()
    report["canonical_boundary_metadata"] = {
        "bundle_boundary_ref": c.ATOMICROWS_BUNDLE_PATH.as_posix(),
        "no_mutation_boundary": {
            "atomicrows_bundle_mutated": False,
            "bundle_mutation_created": False,
        },
    }
    failures = pr149_report.validate_report_payload(report)
    assert "PR149_NO_BUNDLE_MUTATION_AUTHORITY" not in failures


def test_no_repair_or_test_bypass_markers_in_pr149_files() -> None:
    marker_a = "allow_repair=" + "True"
    marker_b = "raise SystemExit(" + "0)"
    marker_c = "x" + "fail"
    marker_d = "s" + "kip"
    files = [
        REPO_ROOT
        / "tools"
        / "validate_atomicrows_semantic_value_materialization_implementation_bridge.py",
        REPO_ROOT
        / "src"
        / "qtt"
        / "stage1_prediction_markets"
        / "atomicrows_semantic_value_materialization_implementation_bridge"
        / "report.py",
        REPO_ROOT
        / "tests"
        / "atomicrows"
        / "test_atomicrows_semantic_value_materialization_implementation_bridge.py",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    for marker in (marker_a, marker_b, marker_c, marker_d):
        assert marker not in combined
