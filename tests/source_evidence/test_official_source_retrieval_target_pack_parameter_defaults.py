from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess

from tools import run_validation_gates as runner
from tools import (
    validate_official_source_retrieval_target_pack_parameter_defaults as pr151_cli,
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
from src.qtt.stage1_prediction_markets.official_source_retrieval_target_pack_parameter_defaults import (
    constants as c,
    report as pr151_report,
)
from src.qtt.stage1_prediction_markets.qtt_owner_global_override_directive_currentization_and_internal_gate_release import (
    constants as pr143_constants,
    report as pr143_report,
)
from src.qtt.stage1_prediction_markets.source_backed_classical_quantum_parameter_default_target_matrix import (
    constants as pr150_constants,
    report as pr150_report,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _report() -> dict:
    return pr151_report.build_report(REPO_ROOT)


def _queue(report: dict | None = None) -> list[dict]:
    payload = report if report is not None else _report()
    return payload["official_source_retrieval_target_queue"]


def _copy_inputs(tmp_path: Path) -> Path:
    for rel_path in (*c.REQUIRED_UPSTREAM_ARTIFACTS, *c.OPTIONAL_CONTEXT_ARTIFACTS):
        source = REPO_ROOT / rel_path
        if not source.exists():
            continue
        target = tmp_path / rel_path
        if source.is_dir():
            shutil.copytree(source, target)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    return tmp_path


def test_pr151_consumes_required_upstream_chain_and_owner_packet() -> None:
    report = _report()
    consumed = {
        row["artifact_path"]
        for row in report["upstream_artifact_inputs"]
        if row["consumed"]
    }
    for rel_path in c.REQUIRED_UPSTREAM_ARTIFACTS:
        assert rel_path.as_posix() in consumed
    alias = report["orchestration_preflight_receipt"]["alias_resolution"]
    assert alias["requested_alias"] == c.PR136_SECTION_CROSSWALK_ALIAS_PATH.as_posix()
    assert alias["canonical_successor_used"] is True
    assert alias["created_missing_alias"] is False
    assert report["pr136_alignment_summary"]["route_receipt_type"] == (
        "PR136_ROUTE_TRIAGE_RECEIPT"
    )
    assert report["pr136_alignment_summary"]["market_scope_count"] == 4
    assert report["pr136_alignment_summary"]["command_action_count"] >= 1
    assert report["pr137r_alignment_summary"]["row_count_proven"] is True
    assert report["pr138_semantic_contract_summary"]["field_count"] == 59
    assert report["pr149_bridge_consumption_summary"]["report_id"] is not None
    assert report["pr150_parameter_target_matrix_consumption_summary"]["report_id"] == (
        "QTT_PR150_SOURCE_BACKED_CLASSICAL_QUANTUM_PARAMETER_DEFAULT_TARGET_MATRIX_REPORT"
    )
    assert report["orchestration_preflight_receipt"]["owner_source_packet_consumed"] is True


def test_source_class_extraction_and_catalog_match_owner_packet() -> None:
    report = _report()
    receipt = report["source_class_extraction_receipt"]
    assert receipt["extracted_from_owner_packet"] is True
    assert receipt["matches_constant_surface"] is True
    assert receipt["extracted_official_source_classes"] == sorted(c.OFFICIAL_SOURCE_CLASS_VALUES)
    assert report["owner_source_evidence_packet_summary"]["non_authoritative_source_classes"] == sorted(
        c.NON_AUTHORITATIVE_SOURCE_CLASS_VALUES
    )
    catalog_classes = {
        row["source_target_class"]
        for row in report["source_retrieval_target_class_catalog"]
    }
    assert "VENUE_API_SOURCE_TARGET" in catalog_classes
    assert "MARKET_DATA_SOURCE_TARGET" in catalog_classes
    assert "RISK_CAPITAL_SOURCE_TARGET" in catalog_classes
    assert "OPTIMIZER_PROVIDER_DOC_SOURCE_TARGET" in catalog_classes
    assert "QUANTUM_PROVIDER_DOC_SOURCE_TARGET" in catalog_classes
    assert "ATOMICROWS_COMPATIBILITY_SOURCE_TARGET" in catalog_classes


def test_pr151_derives_queue_from_pr150_and_covers_every_eligible_target() -> None:
    report = _report()
    coverage = report["pr150_source_target_coverage_summary"]
    queue = _queue(report)
    assert coverage["eligible_pr150_target_count"] == 146
    assert coverage["queue_item_count"] == 342
    assert coverage["typed_exclusion_count"] == 0
    assert set(coverage["eligible_pr150_target_ids"]) == set(
        coverage["covered_pr150_target_ids"]
    )
    assert {row["target_platform_scope"] for row in queue} == set(c.VENUE_SCOPES)
    assert coverage["queue_item_count_by_platform"] == {
        "FORECASTEX_IBKR": 114,
        "KALSHI": 114,
        "POLYMARKET": 114,
    }
    general_target = next(
        row
        for row in queue
        if row["pr150_target_id"].endswith("PREDICTION_MARKETS_GENERAL")
    )
    sibling_platforms = {
        row["target_platform_scope"]
        for row in queue
        if row["pr150_target_id"] == general_target["pr150_target_id"]
    }
    assert sibling_platforms == set(c.VENUE_SCOPES)


def test_queue_items_are_target_only_and_symbolic() -> None:
    for row in _queue():
        assert row["owner_approved_domain_route"] is None
        assert row["owner_domain_route_state"] == "DOMAIN_ROUTE_PENDING_OWNER_APPROVAL"
        assert row["official_source_domain_slot"].startswith("PR151_DOMAIN_SLOT__")
        assert row["value_capture_state"] == "BLOCKED_PENDING_DOMAIN_ROUTE"
        assert row["accepted_value_state"] == "NOT_ACCEPTED_TARGET_ONLY"
        assert row["order_use_eligibility"] == "NOT_ORDER_USABLE_RETRIEVAL_TARGET_ONLY"
        assert row["no_claim_flags"] == c.NO_CLAIM_FLAGS
        assert "PR151_DOMAIN_ROUTE_PENDING_OWNER_APPROVAL" in row["reason_codes"]
        serialized = json.dumps(row, sort_keys=True)
        assert "://" not in serialized
        assert "www." not in serialized
        assert ".com" not in serialized


def test_surface_coverage_for_venue_market_risk_optimizer_quantum_and_atomicrows() -> None:
    queue = _queue()
    classes = {row["source_target_class"] for row in queue}
    assert {
        "VENUE_API_SOURCE_TARGET",
        "ORDER_FIELD_SOURCE_TARGET",
        "FEE_RULE_SOURCE_TARGET",
        "TICK_RULE_SOURCE_TARGET",
        "SDK_BEHAVIOR_SOURCE_TARGET",
        "RATE_LIMIT_SOURCE_TARGET",
        "MARKET_DATA_SOURCE_TARGET",
        "ACCOUNT_PRIVATE_STATE_SOURCE_TARGET",
        "EXECUTION_LIFECYCLE_SOURCE_TARGET",
        "FILL_INTEGRITY_SOURCE_TARGET",
        "RECONCILIATION_SOURCE_TARGET",
        "CROSS_VENUE_NORMALIZATION_SOURCE_TARGET",
        "RISK_CAPITAL_SOURCE_TARGET",
        "OPTIMIZER_PROVIDER_DOC_SOURCE_TARGET",
        "QUANTUM_PROVIDER_DOC_SOURCE_TARGET",
        "ATOMICROWS_COMPATIBILITY_SOURCE_TARGET",
    }.issubset(classes)
    quantum_rows = [
        row for row in queue if row["source_target_class"] == "QUANTUM_PROVIDER_DOC_SOURCE_TARGET"
    ]
    assert quantum_rows
    assert {
        row["quantum_forward_dependency"]
        for row in quantum_rows
    } == {c.QUANTUM_FORWARD_STATE}
    optimizer_rows = [
        row
        for row in queue
        if row["source_target_class"] == "OPTIMIZER_PROVIDER_DOC_SOURCE_TARGET"
    ]
    assert optimizer_rows
    assert all(row["official_source_class"] == "OFFICIAL_PROVIDER_DOCS" for row in optimizer_rows)


def test_report_is_deterministic_and_has_no_local_paths() -> None:
    first = pr151_report.build_report(REPO_ROOT)
    second = pr151_report.build_report(REPO_ROOT)
    assert first == second
    assert pr151_report.json_dump(first) == pr151_report.json_dump(second)
    ids = [row["retrieval_target_id"] for row in _queue(first)]
    assert ids == sorted(ids)
    assert len(ids) == len(set(ids))
    serialized = pr151_report.json_dump(first)
    assert "C:\\Users\\" not in serialized
    assert "AtomicRows.bundle." not in serialized
    assert ("AtomicRows.bundle." + "sha" + "256") not in serialized


def test_validation_default_output_and_write_modes(capsys, monkeypatch, tmp_path) -> None:
    report_path = REPO_ROOT / c.REPORT_PATH
    before_report = report_path.read_bytes()
    before_diff = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    ).stdout
    output_path = tmp_path / "pr151.report.json"
    current_pr151_paths = [
        path
        for path in pr151_report._changed_paths(REPO_ROOT)
        if path in c.EXACT_CHANGED_PATH_CANDIDATES
        or path.startswith(
            "src/qtt/stage1_prediction_markets/"
            "official_source_retrieval_target_pack_parameter_defaults/"
        )
    ]
    monkeypatch.setattr(pr151_report, "_changed_paths", lambda repo_root: current_pr151_paths)

    assert pr151_cli.main(["--repo-root", REPO_ROOT.as_posix()]) == 0
    assert report_path.read_bytes() == before_report

    assert pr151_cli.main(
        ["--repo-root", REPO_ROOT.as_posix(), "--output", output_path.as_posix()]
    ) == 0
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == _report()
    assert sorted(
        path.relative_to(tmp_path).as_posix()
        for path in tmp_path.rglob("*")
        if path.is_file()
    ) == ["pr151.report.json"]
    assert report_path.read_bytes() == before_report

    assert pr151_cli.main(["--repo-root", REPO_ROOT.as_posix(), "--write-report"]) == 0
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


def test_explicit_tracked_write_guard_allows_only_pr151_report_on_main(monkeypatch) -> None:
    report_path = c.REPORT_PATH.as_posix()
    unrelated_path = "docs/master_plan/generated/PR151_unrelated.report.json"
    expected_report_failure = f"PR151_CHANGED_PATH_OUT_OF_SCOPE: {report_path}"
    expected_unrelated_failure = f"PR151_CHANGED_PATH_OUT_OF_SCOPE: {unrelated_path}"

    monkeypatch.setattr(
        pr151_report,
        "current_branch_context",
        lambda repo_root: BranchContext(branch="main", source="unit-test"),
    )
    monkeypatch.setattr(pr151_report, "_changed_paths", lambda repo_root: [report_path])

    assert pr151_report.validate_repository_artifacts(REPO_ROOT) == [
        expected_report_failure
    ]
    assert (
        pr151_report.validate_repository_artifacts(
            REPO_ROOT,
            tracked_report_write_allowed=True,
        )
        == []
    )

    monkeypatch.setattr(
        pr151_report,
        "_changed_paths",
        lambda repo_root: [report_path, unrelated_path],
    )
    assert pr151_report.validate_repository_artifacts(
        REPO_ROOT,
        tracked_report_write_allowed=True,
    ) == [expected_unrelated_failure]


def test_missing_and_malformed_upstream_fail_closed(tmp_path) -> None:
    _evidence, missing_failures = pr151_report.load_static_evidence(tmp_path / "empty")
    assert any(failure.startswith("PR151_UPSTREAM_REPORT_MISSING") for failure in missing_failures)

    copied_root = _copy_inputs(tmp_path / "malformed")
    bad_path = copied_root / c.PR150_REPORT_PATH
    bad_path.write_text("{", encoding="utf-8")
    _evidence, parse_failures = pr151_report.load_static_evidence(copied_root)
    assert any(
        failure.startswith("PR151_UPSTREAM_REPORT_PARSE_ERROR")
        for failure in parse_failures
    )


def test_synthetic_missing_queue_or_exclusion_fails_closed() -> None:
    report = _report()
    target_id = report["pr150_source_target_coverage_summary"]["eligible_pr150_target_ids"][0]
    report["official_source_retrieval_target_queue"] = [
        row for row in _queue(report) if row["pr150_target_id"] != target_id
    ]
    report["pr150_source_target_coverage_summary"]["queue_item_count"] = len(
        report["official_source_retrieval_target_queue"]
    )
    failures = pr151_report.validate_report_payload(report)
    assert any("PR151_PR150_SOURCE_TARGET_COVERAGE_REQUIRED" in failure for failure in failures)


def test_synthetic_non_authoritative_domain_value_and_state_failures() -> None:
    report = _report()
    report["official_source_retrieval_target_queue"][0]["official_source_class"] = "BLOG"
    failures = pr151_report.validate_report_payload(report)
    assert "PR151_NON_AUTHORITATIVE_SOURCE_CLASS_BLOCKED" in failures

    report = _report()
    report["official_source_retrieval_target_queue"][0][
        "owner_approved_domain_route"
    ] = "INVENTED_ROUTE_TOKEN"
    failures = pr151_report.validate_report_payload(report)
    assert "PR151_DOMAIN_ROUTE_INVENTED" in failures

    value_keys = {
        "captured_value": "PR151_CAPTURED_VALUE_CREATED",
        "accepted_value": "PR151_ACCEPTED_VALUE_CREATED",
        "connector_semantic_value": "PR151_CONNECTOR_VALUE_CREATED",
        "runtime_receipt_value": "PR151_RUNTIME_RECEIPT_VALUE_CREATED",
        "replay_paper_result_value": "PR151_REPLAY_PAPER_RESULT_VALUE_CREATED",
        "quantum_output_value": "PR151_QUANTUM_OUTPUT_VALUE_CREATED",
    }
    for key, failure_code in value_keys.items():
        mutated = _report()
        mutated["official_source_retrieval_target_queue"][0][key] = "synthetic"
        assert failure_code in pr151_report.validate_report_payload(mutated)

    report = _report()
    report["official_source_retrieval_target_queue"][0]["order_use_eligibility"] = (
        "ORDER_USABLE"
    )
    failures = pr151_report.validate_report_payload(report)
    assert "PR151_ORDER_USABLE_CREATED" in failures


def test_no_claim_flags_and_authority_boundaries_are_false() -> None:
    report = _report()
    assert report["no_claim_boundary"] == c.NO_CLAIM_FLAGS
    assert all(value is False for value in report["no_claim_boundary"].values())
    for key in (
        "source_fact_acceptance_created",
        "connector_semantic_value_created",
        "runtime_cash_receipt_created",
        "replay_execution_created",
        "paper_execution_created",
        "order_execution_created",
        "live_reachability_created",
        "profit_proof_created",
        "latency_superiority_proof_created",
        "quantum_backend_call_created",
        "quantum_simulator_call_created",
        "quantum_optimizer_output_created",
        "quantum_superiority_proof_created",
        "launch_readiness_created",
        "final_readiness_created",
        "atomicrows_bundle_mutated",
        "qtt_integrity_authority_created",
    ):
        assert report["no_claim_boundary"][key] is False
    assert report["atomicrows_compatibility_surface"]["bundle_mutation_required"] is False
    assert report["quantum_forward_source_target_surface"]["quantum_output_created"] is False


def test_network_surface_and_bypass_markers_absent() -> None:
    assert pr151_report._network_surface_failures(REPO_ROOT) == []
    marker_a = "allow_repair=" + "True"
    marker_b = "raise SystemExit(" + "0)"
    marker_c = "x" + "fail"
    marker_d = "s" + "ki" + "p"
    files = [
        REPO_ROOT
        / "tools"
        / "validate_official_source_retrieval_target_pack_parameter_defaults.py",
        REPO_ROOT
        / "src"
        / "qtt"
        / "stage1_prediction_markets"
        / "official_source_retrieval_target_pack_parameter_defaults"
        / "report.py",
        REPO_ROOT
        / "tests"
        / "source_evidence"
        / "test_official_source_retrieval_target_pack_parameter_defaults.py",
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    for marker in (marker_a, marker_b, marker_c, marker_d):
        assert marker not in combined


def test_validation_gate_sequence_includes_pr151_without_tracked_write() -> None:
    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands if len(command) > 1]
    pr150_index = command_names.index(
        "validate_source_backed_classical_quantum_parameter_default_target_matrix.py"
    )
    pr151_index = command_names.index(
        "validate_official_source_retrieval_target_pack_parameter_defaults.py"
    )
    agent_index = command_names.index("validate_qtt_agent_role_operating_charter_registry.py")
    assert pr150_index < pr151_index < agent_index
    assert commands[pr151_index] == [
        runner.sys.executable,
        str(Path("tools") / "validate_official_source_retrieval_target_pack_parameter_defaults.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr151_index]
    assert "--output" not in commands[pr151_index]


def test_changed_path_allowances_are_exact_for_pr151() -> None:
    expected_paths = set(c.EXACT_CHANGED_PATH_CANDIDATES)
    assert set(pr140_constants.PR151_RETRIEVAL_TARGET_PACK_CHANGED_PATHS) == expected_paths
    assert set(pr141_constants.PR151_RETRIEVAL_TARGET_PACK_CHANGED_PATHS) == expected_paths
    assert set(pr142_constants.PR151_RETRIEVAL_TARGET_PACK_CHANGED_PATHS) == expected_paths
    assert set(pr143_constants.PR151_RETRIEVAL_TARGET_PACK_CHANGED_PATHS) == expected_paths
    assert set(pr149_constants.PR151_RETRIEVAL_TARGET_PACK_CHANGED_PATHS) == expected_paths
    assert set(pr150_constants.PR151_RETRIEVAL_TARGET_PACK_CHANGED_PATHS) == expected_paths
    assert "docs/master_plan/generated/" not in c.EXACT_CHANGED_PATH_CANDIDATES
    branch = c.BRANCH
    path = c.REPORT_PATH.as_posix()
    assert pr140_report._is_pr151_retrieval_target_pack_changed_path_for_branch(path, branch)
    assert pr141_report._is_pr151_retrieval_target_pack_changed_path_for_branch(path, branch)
    assert pr142_report._is_pr151_retrieval_target_pack_changed_path_for_branch(path, branch)
    assert pr143_report._is_pr151_retrieval_target_pack_changed_path_for_branch(path, branch)
    assert pr149_report._is_pr151_retrieval_target_pack_changed_path_for_branch(path, branch)
    assert pr150_report._is_pr151_retrieval_target_pack_changed_path_for_branch(path, branch)
