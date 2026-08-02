from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess

from tools import run_validation_gates as runner
from tools import (
    validate_source_backed_classical_quantum_parameter_default_target_matrix
    as pr150_cli,
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
    constants as pr149_constants,
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
from src.qtt.stage1_prediction_markets.source_backed_classical_quantum_parameter_default_target_matrix import (
    constants as c,
    report as pr150_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
_TRANSIENT_INPUT_COPY_PATTERNS = (
    "__pycache__",
    ".pytest_cache",
    "*.pyc",
    "*.pyo",
)
_TRANSIENT_INPUT_COPY_IGNORE = shutil.ignore_patterns(
    *_TRANSIENT_INPUT_COPY_PATTERNS
)


def _report() -> dict:
    return pr150_report.build_report(REPO_ROOT)


def _items(report: dict | None = None) -> list[dict]:
    payload = report if report is not None else _report()
    return payload["parameter_default_target_matrix"]["parameter_target_items"]


def _item_by_authority(authority_class: str) -> dict:
    for item in _items():
        if item["value_authority_class"] == authority_class:
            return deepcopy(item)
    raise AssertionError(authority_class)


def _copy_input_directory(source: Path, target: Path) -> None:
    shutil.copytree(source, target, ignore=_TRANSIENT_INPUT_COPY_IGNORE)


def _copy_inputs(tmp_path: Path) -> Path:
    for rel_path in (*c.REQUIRED_UPSTREAM_ARTIFACTS, *c.OPTIONAL_CONTEXT_ARTIFACTS):
        source = REPO_ROOT / rel_path
        if not source.exists():
            continue
        target = tmp_path / rel_path
        if source.is_dir():
            _copy_input_directory(source, target)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    return tmp_path


def test_pr150_consumes_required_upstream_chain_and_alias() -> None:
    report = _report()
    consumed = {
        row["artifact_path"]
        for row in report["upstream_artifact_inputs"]
        if row["consumed"]
    }
    for rel_path in c.REQUIRED_UPSTREAM_ARTIFACTS:
        assert rel_path.as_posix() in consumed
    assert report["pr136_alignment_summary"]["route_receipt_type"] == (
        "PR136_ROUTE_TRIAGE_RECEIPT"
    )
    assert report["pr136_alignment_summary"]["market_scope_count"] == 4
    assert report["pr136_alignment_summary"]["command_action_count"] >= 1
    alias = report["orchestration_preflight_receipt"]["alias_resolution"]
    assert alias["requested_alias"] == c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix()
    assert alias["canonical_successor_used"] is True
    assert alias["created_missing_alias"] is False
    assert not (REPO_ROOT / c.PR136_SECTION_CROSSWALK_ALIAS_PATH).exists()


def test_pr150_consumes_pr137r_pr138_pr149_and_source_policy_boundaries() -> None:
    report = _report()
    assert report["pr137r_alignment_summary"]["row_count_proven"] is True
    assert report["pr138_semantic_contract_summary"]["field_count"] == 59
    assert report["pr149_bridge_consumption_summary"]["report_id"] == (
        "QTT_PR149_ATOMICROWS_SEMANTIC_VALUE_MATERIALIZATION_IMPLEMENTATION_BRIDGE_REPORT"
    )
    assert report["pr149_bridge_consumption_summary"]["semantic_item_count"] == 59
    assert report["source_evidence_boundary_summary"]["owner_source_policy_packet_present"] is True
    assert report["source_evidence_boundary_summary"]["policy_context_only"] is True
    assert report["source_evidence_boundary_summary"]["external_fact_value_created"] is False


def test_target_matrix_covers_required_classical_scoring_risk_and_execution_domains() -> None:
    report = _report()
    assert len(report["classical_parameter_targets"]) == 12
    assert len(report["scoring_formula_input_targets"]) == 14
    assert len(report["risk_capital_control_targets"]) == 14
    assert len(report["execution_latency_parameter_targets"]) == 13
    item_domains = {item["target_domain"] for item in _items(report)}
    for domain in c.PARAMETER_DOMAIN_VALUES:
        assert domain in item_domains
    for item in _items(report):
        assert item["default_value"] is None
        assert item["allowed_range"] is None


def test_venue_optimizer_quantum_atomicrows_and_replay_paper_surfaces() -> None:
    report = _report()
    venue_rows = report["market_specific_parameter_targets"]
    assert {row["market_scope"] for row in venue_rows} == set(c.VENUE_SCOPES)
    assert len(report["venue_source_required_targets"]) == len(c.VENUE_SCOPES) * 16
    assert len(report["optimizer_parameter_targets"]) == 12
    assert len(report["quantum_parameter_targets"]) == 18
    assert len(report["atomicrows_parameter_targets"]) == 7
    assert len(report["replay_paper_calibration_targets"]) == 8
    quantum_items = [
        item
        for item in _items(report)
        if item["target_family_id"] == "QUANTUM_PARAMETER"
    ]
    assert {
        "QUANTUM_METADATA_ONLY_VALUE",
        "QUANTUM_EXECUTION_EVIDENCE_REQUIRED_VALUE",
        "REPLAY_PAPER_CALIBRATION_REQUIRED_VALUE",
    }.issubset({item["value_authority_class"] for item in quantum_items})
    assert report["atomicrows_compatibility_summary"]["atomicrows_bundle_mutated"] is False


def test_target_family_catalog_and_items_are_deterministic() -> None:
    first = pr150_report.build_report(REPO_ROOT)
    second = pr150_report.build_report(REPO_ROOT)
    assert first == second
    assert pr150_report.json_dump(first) == pr150_report.json_dump(second)
    assert [row["target_family_id"] for row in first["target_family_catalog"]] == list(
        c.TARGET_FAMILY_VALUES
    )
    item_ids = [item["target_id"] for item in _items(first)]
    assert item_ids == sorted(item_ids)
    assert len(item_ids) == len(set(item_ids))
    assert first["centralized_reason_codes"] == list(c.REASON_CODES)


def test_validation_default_output_and_write_modes(capsys, tmp_path) -> None:
    report_path = REPO_ROOT / c.REPORT_PATH
    before_report = report_path.read_bytes()
    before_diff = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    ).stdout
    output_path = tmp_path / "pr150.report.json"

    assert pr150_cli.main(["--repo-root", REPO_ROOT.as_posix()]) == 0
    assert report_path.read_bytes() == before_report

    assert pr150_cli.main(
        ["--repo-root", REPO_ROOT.as_posix(), "--output", output_path.as_posix()]
    ) == 0
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == _report()
    assert sorted(
        path.relative_to(tmp_path).as_posix()
        for path in tmp_path.rglob("*")
        if path.is_file()
    ) == ["pr150.report.json"]
    assert report_path.read_bytes() == before_report

    assert pr150_cli.main(["--repo-root", REPO_ROOT.as_posix(), "--write-report"]) == 0
    after_diff = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    ).stdout
    assert report_path.read_bytes() == before_report
    assert after_diff == before_diff
    assert c.SUCCESS_MARKER in capsys.readouterr().out


def test_explicit_tracked_write_guard_allows_only_pr150_report_on_main(monkeypatch) -> None:
    report_path = c.REPORT_PATH.as_posix()
    unrelated_path = "docs/master_plan/generated/PR150_unrelated.report.json"
    expected_report_failure = f"PR150_CHANGED_PATH_OUT_OF_SCOPE: {report_path}"
    expected_unrelated_failure = f"PR150_CHANGED_PATH_OUT_OF_SCOPE: {unrelated_path}"

    monkeypatch.setattr(
        pr150_report,
        "current_branch_context",
        lambda repo_root: BranchContext(branch="main", source="unit-test"),
    )
    monkeypatch.setattr(pr150_report, "_changed_paths", lambda repo_root: [report_path])

    assert pr150_report.validate_repository_artifacts(REPO_ROOT) == [
        expected_report_failure
    ]
    assert (
        pr150_report.validate_repository_artifacts(
            REPO_ROOT,
            tracked_report_write_allowed=True,
        )
        == []
    )

    monkeypatch.setattr(
        pr150_report,
        "_changed_paths",
        lambda repo_root: [report_path, unrelated_path],
    )
    assert pr150_report.validate_repository_artifacts(
        REPO_ROOT,
        tracked_report_write_allowed=True,
    ) == [expected_unrelated_failure]


def test_missing_and_malformed_upstream_fail_closed(tmp_path) -> None:
    _evidence, missing_failures = pr150_report.load_static_evidence(tmp_path / "empty")
    assert any(failure.startswith("PR150_UPSTREAM_REPORT_MISSING") for failure in missing_failures)

    copied_root = _copy_inputs(tmp_path / "malformed")
    bad_path = copied_root / c.PR138_REPORT_PATH
    bad_path.write_text("{", encoding="utf-8")
    _evidence, parse_failures = pr150_report.load_static_evidence(copied_root)
    assert any(
        failure.startswith("PR150_UPSTREAM_REPORT_PARSE_ERROR")
        for failure in parse_failures
    )

    synthetic_source = tmp_path / "synthetic-source"
    (synthetic_source / "__pycache__").mkdir(parents=True)
    (synthetic_source / ".pytest_cache").mkdir()
    (synthetic_source / "kept.py").write_text("KEPT = True\n", encoding="utf-8")
    (synthetic_source / "__pycache__" / "ignored.cpython-test.pyc").write_bytes(
        b"ignored"
    )
    (synthetic_source / ".pytest_cache" / "ignored").write_text(
        "ignored", encoding="utf-8"
    )
    (synthetic_source / "ignored.pyo").write_bytes(b"ignored")
    synthetic_target = tmp_path / "synthetic-target"
    _copy_input_directory(synthetic_source, synthetic_target)

    assert (synthetic_target / "kept.py").is_file()
    assert not (synthetic_target / "__pycache__").exists()
    assert not (synthetic_target / ".pytest_cache").exists()
    assert not tuple(synthetic_target.rglob("*.pyc"))
    assert not tuple(synthetic_target.rglob("*.pyo"))


def test_validator_rejects_unauthorized_values_and_authority_misuse() -> None:
    report = _report()
    item = next(
        row
        for row in report["parameter_default_target_matrix"]["parameter_target_items"]
        if row["value_authority_class"] == "SOURCE_EVIDENCE_REQUIRED_VALUE"
    )
    item["default_value"] = "unauthorized"
    failures = pr150_report.validate_report_payload(report)
    assert any("PR150_UNAUTHORIZED_DEFAULT_VALUE_FILLED" in failure for failure in failures)

    report = _report()
    item = _item_by_authority("SOURCE_EVIDENCE_REQUIRED_VALUE")
    item["value_authority_class"] = "ACCEPTED_SOURCE_EVIDENCE_VALUE"
    item["source_artifact_ref"] = "docs/master_plan/source_evidence/candidate_packet.json"
    item["default_value"] = "candidate_value"
    report["parameter_default_target_matrix"]["parameter_target_items"].append(item)
    failures = pr150_report.validate_report_payload(report)
    assert any("PR150_ACCEPTED_SOURCE_FIELD_SCOPE_REQUIRED" in failure for failure in failures)

    report = _report()
    item = _items(report)[0]
    item["value_authority_class"] = "OWNER_POLICY_VALUE"
    item["source_target_field_class"] = "official_source:KALSHI:fee_rules"
    item["default_value"] = "owner_policy_cannot_fill_external_fact"
    failures = pr150_report.validate_report_payload(report)
    assert any("PR150_OWNER_POLICY_EXTERNAL_FACT_MISUSE" in failure for failure in failures)


def test_missing_evidence_routes_remain_pending_and_null() -> None:
    report = _report()
    source_item = _item_by_authority("SOURCE_EVIDENCE_REQUIRED_VALUE")
    runtime_item = _item_by_authority("RUNTIME_RECEIPT_REQUIRED_VALUE")
    replay_item = _item_by_authority("REPLAY_PAPER_CALIBRATION_REQUIRED_VALUE")
    quantum_item = _item_by_authority("QUANTUM_EXECUTION_EVIDENCE_REQUIRED_VALUE")

    assert source_item["default_target_state"] == "TARGET_DEFINED_VALUE_PENDING_SOURCE_EVIDENCE"
    assert runtime_item["default_target_state"] == "TARGET_DEFINED_VALUE_PENDING_RUNTIME_RECEIPT"
    assert replay_item["default_target_state"] == (
        "TARGET_DEFINED_VALUE_PENDING_REPLAY_PAPER_CALIBRATION"
    )
    assert quantum_item["default_target_state"] == (
        "TARGET_DEFINED_VALUE_PENDING_QUANTUM_EXECUTION_EVIDENCE"
    )
    for item in (source_item, runtime_item, replay_item, quantum_item):
        assert item["default_value"] is None
        assert item["allowed_range"] is None


def test_no_claim_boundaries_and_order_use() -> None:
    report = _report()
    assert report["no_claim_boundary"] == c.NO_CLAIM_FLAGS
    assert all(value is False for value in report["no_claim_boundary"].values())
    assert report["order_use_eligibility_summary"]["order_usable_target_count"] == 0
    for item in _items(report):
        assert item["no_claim_flags"] == c.NO_CLAIM_FLAGS
        assert item["order_use_eligibility"] in c.ORDER_USE_ELIGIBILITY_VALUES
        assert item["order_use_eligibility"] != "ORDER_USABLE"


def test_no_bundle_sidecar_local_path_or_integrity_authority() -> None:
    report = _report()
    serialized = pr150_report.json_dump(report)
    assert "AtomicRows.bundle." not in serialized
    assert ("AtomicRows.bundle." + "sha" + "256") not in serialized
    assert "C:\\Users\\" not in serialized

    mutated = _report()
    mutated["validation_summary"]["tracked_report_path"] = (
        c.ATOMICROWS_BUNDLE_PATH.with_suffix("." + "sha" + "256").as_posix()
    )
    failures = pr150_report.validate_report_payload(mutated)
    assert "PR150_NO_BUNDLE_MUTATION_AUTHORITY" in failures

    mutated = _report()
    mutated["no_claim_boundary"]["qtt_integrity_authority_created"] = True
    failures = pr150_report.validate_report_payload(mutated)
    assert any("PR150_FORBIDDEN_FLAG_TRUE" in failure for failure in failures)


def test_reason_codes_centralized_and_no_bypass_markers_in_pr150_files() -> None:
    report = _report()
    item_reason_codes = {
        reason
        for item in _items(report)
        for reason in item["reason_codes"]
    }
    assert item_reason_codes.issubset(set(c.REASON_CODES))

    marker_a = "allow_repair=" + "True"
    marker_b = "raise SystemExit(" + "0)"
    marker_c = "x" + "fail"
    marker_d = "s" + "ki" + "p"
    files = [
        REPO_ROOT
        / "tools"
        / "validate_source_backed_classical_quantum_parameter_default_target_matrix.py",
        REPO_ROOT
        / "src"
        / "qtt"
        / "stage1_prediction_markets"
        / "source_backed_classical_quantum_parameter_default_target_matrix"
        / "report.py",
        REPO_ROOT
        / "tests"
        / "atomicrows"
        / "test_source_backed_classical_quantum_parameter_default_target_matrix.py",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    for marker in (marker_a, marker_b, marker_c, marker_d):
        assert marker not in combined


def test_validation_gate_sequence_includes_pr150_without_tracked_write() -> None:
    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands if len(command) > 1]
    pr149_index = command_names.index(
        "validate_atomicrows_semantic_value_materialization_implementation_bridge.py"
    )
    pr150_index = command_names.index(
        "validate_source_backed_classical_quantum_parameter_default_target_matrix.py"
    )
    agent_index = command_names.index("validate_qtt_agent_role_operating_charter_registry.py")
    assert pr149_index < pr150_index < agent_index
    assert commands[pr150_index] == [
        runner.sys.executable,
        str(Path("tools") / "validate_source_backed_classical_quantum_parameter_default_target_matrix.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr150_index]
    assert "--output" not in commands[pr150_index]


def test_changed_path_allowances_are_exact_for_pr150() -> None:
    assert set(pr140_constants.PR150_TARGET_MATRIX_CHANGED_PATHS) == set(
        c.EXACT_CHANGED_PATH_CANDIDATES
    )
    assert set(pr141_constants.PR150_TARGET_MATRIX_CHANGED_PATHS) == set(
        c.EXACT_CHANGED_PATH_CANDIDATES
    )
    assert set(pr142_constants.PR150_TARGET_MATRIX_CHANGED_PATHS) == set(
        c.EXACT_CHANGED_PATH_CANDIDATES
    )
    assert set(pr143_constants.PR150_TARGET_MATRIX_CHANGED_PATHS) == set(
        c.EXACT_CHANGED_PATH_CANDIDATES
    )
    assert set(pr149_constants.PR150_TARGET_MATRIX_CHANGED_PATHS) == set(
        c.EXACT_CHANGED_PATH_CANDIDATES
    )
    assert "docs/master_plan/generated/" not in c.EXACT_CHANGED_PATH_CANDIDATES
    path = c.REPORT_PATH.as_posix()
    branch = c.BRANCH
    assert pr140_report._is_pr150_target_matrix_changed_path_for_branch(path, branch)
    assert pr141_report._is_pr150_target_matrix_changed_path_for_branch(path, branch)
    assert pr142_report._is_pr150_target_matrix_changed_path_for_branch(path, branch)
    assert pr143_report._is_pr150_target_matrix_changed_path_for_branch(path, branch)
    assert pr149_report._is_pr150_target_matrix_changed_path_for_branch(path, branch)
