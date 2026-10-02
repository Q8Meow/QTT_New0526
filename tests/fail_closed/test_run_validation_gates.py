import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools import ci_branch_context
from tools import (
    validate_atomicrows_research_provenance_evidence_tier_classification as research_provenance_gate,
)
from tools import (
    validate_atomicrows_owner_submitted_research_source_intake_registry as owner_intake_gate,
)
from tools import (
    validate_atomicrows_research_source_to_candidate_family_gate as candidate_family_gate,
)
from tools import (
    validate_atomicrows_parameter_stack_role_taxonomy as parameter_stack_role_gate,
)
from tools import (
    validate_atomicrows_parameter_stack_completeness_gate as parameter_stack_completeness_gate,
)
from tools import (
    validate_atomicrows_parameter_stack_compatibility_gate as parameter_stack_compatibility_gate,
)
from tools import validate_edge_parameter_stack_selection_packet as edge_packet_gate
from tools import validate_qtt_trade_context_packet as trade_context_gate
from tools import (
    validate_atomicrows_parameter_selection_universe_registry as selection_universe_gate,
)
from tools import (
    validate_atomicrows_parameter_selection_universe_consumer_gate as selection_universe_consumer_gate,
)
from tools import (
    validate_trade_context_selection_universe_routing_gate as trade_context_routing_gate,
)
from tools import (
    validate_quantum_applicability_classification_registry as quantum_applicability_gate,
)
from tools import (
    validate_owner_quantum_priority_policy_registry as owner_quantum_priority_gate,
)
from tools import (
    validate_parameter_algorithm_scoring_policy_registry as scoring_policy_gate,
)
from tools import (
    validate_parameter_stack_scoring_and_ranking_gate as stack_scoring_gate,
)
from tools import (
    validate_quantum_classical_optimizer_arbitration_gate as optimizer_arbitration_gate,
)
from tools import (
    validate_candidate_parameter_stack_generation_gate as candidate_generation_gate,
)
from tools import (
    validate_trade_context_parameter_stack_selection_gate as trade_context_stack_selection_gate,
)
from tools import (
    validate_selected_parameter_stack_handoff_packet as selected_stack_handoff_gate,
)
from tools import (
    validate_replay_paper_candidate_stack_competition_gate as replay_paper_competition_gate,
)
from tools import (
    validate_dual_result_review_for_parameter_stacks as dual_result_review_gate,
)
from tools import (
    validate_owner_live_promotion_review_for_parameter_stacks as owner_live_promotion_review_gate,
)
from tools import (
    validate_owner_approval_request_queue_registry as owner_approval_request_queue_gate,
)
from tools import (
    validate_owner_override_receipt_authoring_gate as owner_override_receipt_authoring_gate,
)
from tools import (
    validate_owner_dashboard_approval_menu_schema as owner_dashboard_approval_menu_schema_gate,
)
from tools import (
    validate_owner_dashboard_approval_static_screen_contract
    as owner_dashboard_approval_static_screen_contract_gate,
)
from tools import (
    validate_atomicrows_full_bundle_row_expansion_plan
    as atomicrows_full_bundle_row_expansion_plan_gate,
)
from tools import (
    validate_atomicrows_bundle_row_family_source_files
    as atomicrows_bundle_row_family_source_files_gate,
)
from tools import (
    validate_atomicrows_bundle_builder_deterministic_assembly_gate
    as atomicrows_bundle_builder_deterministic_assembly_gate,
)
from tools import (
    validate_atomicrows_sha_system_dormancy_state_contract
    as atomicrows_sha_system_dormancy_state_contract,
)
from tools import (
    validate_qtt_final_readiness_dependency_policy_contract
    as qtt_final_readiness_dependency_policy_contract,
)
from tools import (
    validate_qtt_active_non_sha_day1_gate_state_registry_contract
    as qtt_active_non_sha_day1_gate_state_registry_contract,
)
from tools import validate_qtt_pr_identity_roster as qtt_pr_identity_roster
from tools import (
    validate_qtt_roadmap_execution_state_controller
    as qtt_roadmap_execution_state_controller,
)
from tools import (
    validate_atomicrows_bundle_sha_freeze_authority_gate
    as atomicrows_bundle_sha_freeze_authority_gate,
)
from tools import (
    validate_atomicrows_exact_row_authority_classifier_bridge
    as atomicrows_exact_row_authority_classifier_bridge,
)
from tools import (
    validate_atomicrows_owner_approved_exact_15_family_count_distribution
    as atomicrows_owner_approved_exact_15_family_count_distribution,
)
from tools import (
    validate_atomicrows_exact_row_expansion_manifest
    as atomicrows_exact_row_expansion_manifest,
)
from tools import (
    validate_atomicrows_exact_row_generator_dry_run_manifest
    as atomicrows_exact_row_generator_dry_run_manifest,
)
from tools import (
    validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest
    as atomicrows_repair_chain_grand_debug_logic_audit_manifest,
)
from tools import (
    validate_atomicrows_exact_row_source_materialization_manifest
    as atomicrows_exact_row_source_materialization_manifest,
)
from tools import (
    validate_atomicrows_exact_row_agent_family_eligibility_matrix
    as atomicrows_exact_row_agent_family_eligibility_matrix,
)
from tools import (
    validate_atomicrows_bundle_materialization_manifest
    as atomicrows_bundle_materialization_manifest,
)
from tools import (
    validate_atomicrows_bundle_boundary_state_contract
    as atomicrows_bundle_boundary_state_contract,
)
from tools import (
    validate_atomicrows_sha_freeze_final_readiness_state_contract
    as atomicrows_sha_freeze_final_readiness_state_contract,
)
from tools import validate_qtt_agent_algorithm_command_matrix as command_matrix_gate
from tools import (
    validate_pr137_generated_integrity_authority_boundary as pr137_integrity_boundary_gate,
)
from tools import (
    validate_pr137_launch_readiness_dependency_controller as pr137_dependency_controller_gate,
)
from tools import run_validation_gates as runner
from tools import validation_reliability as reliability


REPO_ROOT = Path(__file__).resolve().parents[2]
PR153R_REPAIR_BRANCH = "repair-pr153r-redo-report-determinism"
PR153S_REPAIR_BRANCH = "repair/pr153s-source-value-capture-closure-classifier"
PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH = (
    ci_branch_context.PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH
)
BRANCH_CONTEXT_ENV = (
    "GITHUB_ACTIONS",
    "GITHUB_EVENT_NAME",
    "GITHUB_REF",
    "GITHUB_REF_NAME",
    "GITHUB_HEAD_REF",
)
_PRODUCTION_RUN_COMMANDS = runner.run_commands
_PRODUCTION_TEXT_INTEGRITY_PREFLIGHT = (
    runner._validation_text_integrity_preflight
)


def _clear_branch_context_env(monkeypatch):
    for env_name in BRANCH_CONTEXT_ENV:
        monkeypatch.delenv(env_name, raising=False)


def _synthetic_candidate_custody_v1(root, plan, *, observed_paths, effects, index_path=None,
                                    deadline_ns=None, nested_evidence_limits=None):
    """Finite pytest-owned surfaces; not real campaign acceptance."""
    nested_evidence_limits = {} if nested_evidence_limits is None else nested_evidence_limits
    custody = runner._ValidationCandidateCustodyV1(repo_root=root, plan=plan,
        observe_paths=observed_paths, check_exclusive=lambda: None, index_path=index_path,
        effects_by_occurrence={index: tuple(effects) for index in range(1, len(plan) + 1)}, ignored_paths=(),
        entry_limit=100 + sum(v["entry_limit"] for v in nested_evidence_limits.values()),
        snapshot_byte_limit=1_000_000 + sum(v["retained_byte_limit"] for v in nested_evidence_limits.values()),
        read_byte_limit=100_000_000 + sum(v["read_byte_limit"] for v in nested_evidence_limits.values()),
        deadline_ns=deadline_ns or runner.time.monotonic_ns() + 60_000_000_000,
        nested_evidence_limits=nested_evidence_limits,
        operation_checks={index: (lambda **kwargs: None) for index in range(1, len(plan) + 1)})

    def simulated_startup(index, entry, *, environment, run_paths):
        argv = tuple(entry.argv if type(entry) is reliability.CommandEvidencePlanEntry else entry.execution_argv)
        custody._preflight_launch = (argv, dict(environment))
        return environment, None
    custody.prepare_preflight = simulated_startup
    return custody


def _exercise_candidate_custody_failures_v1(tmp_path, monkeypatch):
    """Synthetic finite custody faults, with independently retained byte answers."""
    plan = runner._prepare_execution_plan([["python", "tools/example_gate.py"]])
    def case(name):
        root = tmp_path / name
        root.mkdir()
        (root / "source.py").write_bytes(b"owner source\n")
        (root / "output.json").write_bytes(b"candidate report\n")
        index = root / "synthetic-index"
        index.write_bytes(b"staged state\n")
        candidate = _synthetic_candidate_custody_v1(root, plan,
            observed_paths=lambda: ("source.py", "output.json"),
            effects=("output.json",), index_path=index)
        return root, index, candidate
    def begin(candidate):
        candidate.begin_occurrence(1, plan[0], environment={}, timeout_seconds=1,
                                   scratch_roots=())

    root, index, candidate = case("raw-index-change")
    begin(candidate)
    index.write_bytes(b"unexpected staged change\n")
    with pytest.raises(RuntimeError, match="INDEX_CHANGED"):
        candidate.end_occurrence(1, plan[0])
    assert candidate.state == "CLEANUP_REJECTED"
    assert index.read_bytes() == b"unexpected staged change\n"
    assert (root / "source.py").read_bytes() == b"owner source\n"

    root, index, candidate = case("mixed-permitted-and-owner-change")
    begin(candidate)
    (root / "output.json").write_bytes(b"permitted output\n")
    (root / "source.py").write_bytes(b"unexplained owner change\n")
    with pytest.raises(RuntimeError, match="UNADMITTED_EFFECT"):
        candidate.end_occurrence(1, plan[0])
    latched = candidate.failure
    with pytest.raises(RuntimeError, match="terminal candidate failure") as denied:
        candidate.restore()
    assert latched is not None and denied.value.__cause__ is latched
    assert candidate.failure is latched
    assert (root / "source.py").read_bytes() == b"unexplained owner change\n"
    assert (root / "output.json").read_bytes() == b"permitted output\n"
    assert candidate.completed_actions == []
    assert index.read_bytes() == b"staged state\n"

    root, index, candidate = case("change-before-child")
    (root / "output.json").write_bytes(b"later owner report\n")
    with pytest.raises(RuntimeError, match="BETWEEN_OCCURRENCES"):
        begin(candidate)
    assert candidate.active_occurrence is None
    assert (root / "output.json").read_bytes() == b"later owner report\n"

    root, index, candidate = case("change-after-child")
    begin(candidate)
    (root / "output.json").write_bytes(b"permitted output\n")
    candidate.end_occurrence(1, plan[0])
    (root / "output.json").write_bytes(b"later owner report\n")
    with pytest.raises(RuntimeError, match="BEFORE_RESTORATION"):
        candidate.restore()
    assert candidate.completed_actions == []
    assert (root / "output.json").read_bytes() == b"later owner report\n"

    root, index, candidate = case("partial-restore-write")
    begin(candidate)
    (root / "output.json").write_bytes(b"permitted output\n")
    candidate.end_occurrence(1, plan[0])
    original_write = runner.os.write
    calls = []
    failure = OSError("synthetic second write failure")
    def short_then_fail(descriptor, value):
        calls.append(len(value))
        if len(calls) == 1:
            return original_write(descriptor, value[:1])
        raise failure
    with monkeypatch.context() as scoped:
        scoped.setattr(runner.os, "write", short_then_fail)
        with pytest.raises(OSError) as caught:
            candidate.restore()
    assert caught.value is failure
    assert candidate.state == "CLEANUP_INCOMPLETE"
    assert (root / "output.json").read_bytes() == b"c"
    assert len(calls) == 2
    latched = candidate.failure
    with pytest.raises(RuntimeError, match="terminal candidate failure") as denied:
        candidate.restore()
    assert latched is not None and denied.value.__cause__ is latched
    assert candidate.failure is latched
    assert index.read_bytes() == b"staged state\n"

    root, index, candidate = case("readback-fault")
    begin(candidate)
    (root / "output.json").write_bytes(b"permitted output\n")
    candidate.end_occurrence(1, plan[0])
    original_snapshot = candidate._snapshot
    def corrupted_readback(paths, **kwargs):
        if candidate.state == "APPLYING" and candidate.completed_actions:
            (root / "output.json").write_bytes(b"readback corruption\n")
        return original_snapshot(paths, **kwargs)
    candidate._snapshot = corrupted_readback
    with pytest.raises(RuntimeError, match="RESTORATION_READBACK"):
        candidate.restore()
    assert candidate.state == "CLEANUP_INCOMPLETE"
    assert len(candidate.completed_actions) == 1
    assert (root / "output.json").read_bytes() == b"readback corruption\n"
    assert (root / "source.py").read_bytes() == b"owner source\n"
    assert index.read_bytes() == b"staged state\n"


@pytest.fixture(autouse=True)
def _central_supervision_test_adapter(monkeypatch, tmp_path):
    def make_paths(label: str):
        process_root = tmp_path / f"process-root-{label}"
        validation_root = process_root / reliability.VALIDATION_OUTPUT_DIR_NAME
        pytest_root = process_root / reliability.PYTEST_BASETEMP_DIR_NAME
        evidence_root = tmp_path / f"evidence-{label}"
        validation_root.mkdir(parents=True, exist_ok=True)
        pytest_root.mkdir(parents=True, exist_ok=True)
        evidence_root.mkdir(parents=True, exist_ok=True)
        return SimpleNamespace(
            run_id=f"run_test_supervision_{label}",
            repo_root=runner.REPO_ROOT,
            process_root=process_root,
            validation_output_root=validation_root,
            pytest_basetemp_root=pytest_root,
            evidence_root=evidence_root,
            cleanup_target=process_root,
        )

    paths = make_paths("active")
    resolve_count = 0

    def fake_resolve(repo_root, **_kwargs):
        nonlocal resolve_count
        resolve_count += 1
        resolved_paths = make_paths(str(resolve_count))
        resolved_paths.repo_root = Path(repo_root)
        return resolved_paths, SimpleNamespace(failure_operation=None)

    def fake_supervise(command, **kwargs):
        started = runner.time.perf_counter()
        timeout_seconds = kwargs.get("timeout_seconds")
        required_markers = tuple(kwargs.get("required_markers", ()))
        try:
            if timeout_seconds is None:
                completed = runner.subprocess.run(list(command))
            else:
                completed = runner.subprocess.run(
                    list(command),
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                )
        except subprocess.TimeoutExpired:
            return SimpleNamespace(
                command_index=kwargs["command_index"],
                elapsed_monotonic_seconds=runner.time.perf_counter() - started,
                native_exit_code=124,
                failure_class="ENGVR_PROCESS_TIMEOUT",
                stdout_marker_state="NOT_EVALUATED_TIMEOUT",
                pid=4321,
            )
        stdout = str(getattr(completed, "stdout", "") or "")
        stderr = str(getattr(completed, "stderr", "") or "")
        if stdout:
            print(stdout, end="", flush=True)
        if stderr:
            print(stderr, end="", file=sys.stderr, flush=True)
        missing = runner._st12h_missing_terminal_markers(
            stdout,
            required_markers,
        )
        native_exit = int(completed.returncode)
        failure_class = (
            "ENGVR_NATIVE_EXIT_NONZERO"
            if native_exit != 0
            else "ENGVR_REQUIRED_MARKER_MISSING"
            if missing
            else None
        )
        return SimpleNamespace(
            command_index=kwargs["command_index"],
            elapsed_monotonic_seconds=runner.time.perf_counter() - started,
            native_exit_code=native_exit,
            failure_class=failure_class,
            stdout_marker_state=(
                "NOT_REQUIRED"
                if not required_markers
                else "PASS"
                if not missing
                else "MISSING:" + ",".join(missing)
            ),
            pid=4321,
        )

    def typed_fake_supervise(command, **kwargs):
        # Preserve the existing substituted child outcomes, with complete receipt
        # identity. A namespace is deliberately no longer a terminal receipt.
        observed = fake_supervise(command, **kwargs)
        timed_out = observed.failure_class == "ENGVR_PROCESS_TIMEOUT"
        timeout = kwargs.get("timeout_seconds")
        evidence = Path(kwargs["evidence_root"])
        return reliability.CommandExecutionReceiptV1(
            schema_version=1, run_id=kwargs["run_id"], phase=kwargs["phase"],
            command_index=kwargs["command_index"], argv=tuple(command),
            cwd=str(Path(kwargs["cwd"]).resolve()), pid=observed.pid, platform=os.name,
            start_time_utc="2026-08-24T00:00:00Z", end_time_utc="2026-08-24T00:00:01Z",
            elapsed_monotonic_seconds=observed.elapsed_monotonic_seconds,
            native_exit_code=observed.native_exit_code, start_failure_class=None,
            timeout_seconds_or_null=timeout,
            timeout_state="TRIGGERED" if timed_out else "NOT_CONFIGURED" if timeout is None else "NOT_TRIGGERED",
            termination_state=("TASKKILL_T:0;TERMINAL:PROVEN" if os.name == "nt"
                               else "SIGTERM:0;TERMINAL:PROVEN") if timed_out else "NOT_REQUIRED",
            stdout_path=str(evidence / f"command-{kwargs['command_index']}.stdout.bin"),
            stderr_path=str(evidence / f"command-{kwargs['command_index']}.stderr.bin"),
            stdout_byte_count=0, stderr_byte_count=0,
            stdout_required_markers=tuple(kwargs.get("required_markers", ())),
            stdout_marker_state=observed.stdout_marker_state, stderr_was_nonempty=False,
            failure_class=observed.failure_class,
        )

    monkeypatch.setattr(runner, "_RUN_COMMANDS_SUPERVISION", None)
    monkeypatch.setattr(runner, "resolve_validation_run_paths", fake_resolve)
    monkeypatch.setattr(runner, "_RUN_COMMANDS_ACTIVE_PATHS", paths)
    monkeypatch.setattr(runner, "_ACTIVE_SEMANTIC_CHANGED_PATHS", None)
    monkeypatch.setattr(runner, "_ACTIVE_CLASSIFIED_CHANGED_PATHS", None)
    monkeypatch.setattr(runner, "write_run_provenance", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        runner,
        "_validation_text_integrity_preflight",
        lambda _repo_root: ((), (), None),
    )
    monkeypatch.setattr(
        runner,
        "cleanup_validation_run",
        lambda _paths: "PASS_REMOVED_EXACT_RUN_ROOT",
    )
    monkeypatch.setattr(runner, "atomic_write_json", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        runner,
        "validate_complete_run_evidence",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        runner,
        "validate_published_completion_receipt",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(runner, "_execute_supervised_command", typed_fake_supervise)

    # The existing orchestration probes already replace the process owner.
    # Their no-effect stub is never used by the explicit candidate-custody cases.
    original_prepare = runner._prepare_validation_candidate_v1
    original_restore = runner._restore_tracked_gate_side_effects
    class SyntheticNoEffectCustody:
        def prepare_preflight(self, *args, environment, **kwargs):
            return environment, None
        def begin_occurrence(self, *args, **kwargs):
            pass
        def end_occurrence(self, *args, **kwargs):
            pass
        def restore(self):
            return ()
    def prepare_fixture(root, plan, original):
        if original is not None:
            return original_prepare(root, plan, original)
        return None if root is None else SyntheticNoEffectCustody()
    def restore_fixture(root, original):
        if type(original) is SyntheticNoEffectCustody:
            return original.restore()
        return original_restore(root, original)
    monkeypatch.setattr(runner, "_prepare_validation_candidate_v1", prepare_fixture)
    monkeypatch.setattr(runner, "_restore_tracked_gate_side_effects", restore_fixture)

    def activate_synthetic_scan(*, scan_source=None, resolve_paths=True, mock_commands=False, deadline_ns=None, patcher=None):
        patcher = monkeypatch if patcher is None else patcher
        # Opt-in support for the existing mocked full-plan tests only. The real
        # capacity guard and native frame owner stay in the exercised call chain.
        # This grants no real RP5A scan, source acceptance or campaign capacity.
        from tools import pr168_rp5a_git_grep_scanner as scan_owner

        issued_inputs = []
        reader_inputs = []

        def resolve_scan_fixture(repo_root, **_kwargs):
            return reliability.resolve_validation_run_paths(
                Path(repo_root), explicit_process_root=tmp_path / "s",
                projected_relative_paths=("command-1.json",),
            )

        def synthetic_capacity(original_paths, phase, expected_plan):
            root = original_paths.repo_root
            assert root.is_relative_to(tmp_path) and root != REPO_ROOT
            selected = tuple(row for row in expected_plan
                             if runner._scan_full_builder_argv(row.argv))
            assert len(selected) == 1
            entry = selected[0]
            assert entry.cwd == str(root) and entry.run_id == original_paths.run_id
            source = root / "scan-fixture.py"
            source_bytes = b"# deterministic fixture-owned scan input\n"
            if source.exists():
                assert source.read_bytes() == source_bytes
            else:
                source.write_bytes(source_bytes)
            surface = reliability._ScanCandidateSurface(
                source.name, "FILE", source.stat().st_mode & 0o7777, source_bytes, (),
            )
            limits = reliability._ScanRunReadLimits(100_000, 1_000, 16, 1)
            deadline = runner.time.monotonic_ns() + 60_000_000_000
            scratch = original_paths.process_root / "i"
            scratch.mkdir()
            fence = reliability._ScanCandidateFence(
                root, (surface,), limits=limits, candidate_read_bytes=100_000,
                deadline_ns=deadline,
            )
            executable = shutil.which("git")
            assert executable is not None
            executable = str(Path(executable).resolve())
            profile = reliability._Rp5aScanProfile(
                original_paths.run_id, entry.command_index, str(root), str(scratch),
                (source.name,), 1, len(source.name.encode("utf-8")) + 1,
                ((source.name, len(source_bytes)),), executable, executable, "git",
                tuple(scan_owner._scan_child_environment(os.environ).items()),
                100_000, 100_000, 4096, 100_000, deadline, 3,
            )
            identity = reliability._ScanLaunchIdentity(
                original_paths.run_id, phase, entry.command_index,
                len(expected_plan), entry.argv, str(root),
            )
            original_input = reliability._ScanLaunchInput(
                identity, (surface,), limits=limits, candidate_read_bytes=100_000,
                deadline_ns=deadline, scratch_root=scratch, scratch_bytes=100_000,
                parent_frame_reread_bytes=100_000, check_candidate=fence,
            )
            issued_inputs.append(original_input)
            return _extend_synthetic_reader_launch_v1(
                reliability._prepare_scan_launch(
                original_paths, phase=phase, plan=expected_plan,
                profiles={entry.command_index: profile}, read_limits=limits,
                deadline_ns=deadline,
                launch_inputs={entry.command_index: original_input},
            ), issued_inputs, reader_inputs)

        def supervise_scan_fixture(command, **kwargs):
            original_input = kwargs.get("launch_input")
            if original_input is None:
                return typed_fake_supervise(command, **kwargs)
            if original_input not in reader_inputs:
                assert any(original_input is value for value in issued_inputs)
            stream = original_input._claim(
                run_id=kwargs["run_id"], phase=kwargs["phase"],
                command_index=kwargs["command_index"], argv=tuple(command),
                cwd=kwargs["cwd"],
            )
            # The existing subprocess port is mocked. Only its labeled lifecycle
            # is simulated; the original frame I/O and context cleanup are real.
            process = SimpleNamespace(pid=4321, returncode=None)
            process.poll = lambda: process.returncode
            original_input._attached(process)
            frame = stream.read(original_input.extent + 1)
            assert len(frame) == original_input.extent
            receipt = typed_fake_supervise(command, **kwargs)
            process.returncode = receipt.native_exit_code
            original_input._finished(process, receipt.native_exit_code)
            assert original_input.state == "CONSUMED"
            return receipt

        state = {}
        supplied_scan = synthetic_capacity if scan_source is None else scan_source
        def bind_run(paths, phase, plan):
            if state:
                assert state["paths"] is paths and state["plan"] is plan
                assert state["phase"] == phase
                return
            assert paths.repo_root.is_relative_to(tmp_path) and paths.repo_root != REPO_ROOT
            custody_deadline = deadline_ns or runner.time.monotonic_ns() + 60_000_000_000
            state.update(paths=paths, phase=phase, plan=plan, deadline=custody_deadline,
                         child=custody_deadline - 15_000_000_000,
                         parent=custody_deadline - 10_000_000_000, calls=[], nested={})

        def scan_supplier(paths, phase, plan):
            bind_run(paths, phase, plan)
            assert "scan" not in state["calls"]
            state["calls"].append("scan")
            launch = supplied_scan(paths, phase, plan)
            assert launch.paths is paths and launch.plan is plan and launch.phase == phase
            return launch

        def mapper_supplier(paths, phase, plan):
            bind_run(paths, phase, plan)
            assert "mapper" not in state["calls"]
            state["calls"].append("mapper")
            root = paths.repo_root
            selected = [(row, reliability._mapper_original_position_v1(row.argv, root)) for row in plan]
            selected = [(row, position) for row, position in selected if position is not None]
            assert selected, "do not attach this supplier to an unselected plan"
            assert {position for row, position in selected} in ({66, 67, 68}, {66, 67, 68, 429, 430, 431, 432, 433, 434})
            target = root / "mapper-fixture.json"
            raw = b"{}\n"  # Independent transport bytes, never authentic application acceptance.
            if target.exists():
                assert target.read_bytes() == raw
            else:
                target.write_bytes(raw)
            reference = paths.process_root / "mapper-basis.bin"
            with reference.open("xb") as stream:
                stream.write(raw)
            with target.open("rb") as stream:
                target_fd = reliability._mapper_stamp_v1(os.fstat(stream.fileno()))
            with reference.open("rb") as stream:
                reference_fd = reliability._mapper_stamp_v1(os.fstat(stream.fileno()))
            root_chain = reliability._mapper_chain_v1(root)
            basis_chain = reliability._mapper_chain_v1(reference.parent)
            r, b, p = len(root_chain), len(basis_chain), len(root_chain)
            metadata = 2*(r+b)+4 + 6*(r+b)+3*p+11
            # Existing finite sibling reader/header limits, with exact byte and
            # metadata demand for this one three-byte acquisition per route.
            read_limits = dict(byte_limit=1_048_576, node_limit=10_000, depth_limit=32,
                               profile_limit=len(selected) + 4)
            bindings = {}
            for row, position in selected:
                assert row is plan[row.command_index - 1]
                assert row.run_id == paths.run_id and row.phase == phase and row.cwd == str(root)
                child = (None if position in (66, 67, 68) else list(
                    reliability._mapper_child_command_v1(row.argv, root, paths.process_root)))
                basis = dict(kind="MAPPER_DISK_BASIS_V1", position=position,
                    generation="synthetic-three-byte-transport", root=str(root), root_chain=root_chain,
                    basis=str(reference), basis_chain=basis_chain,
                    basis_lstat=reliability._mapper_stamp_v1(reference.lstat()), basis_fstat=reference_fd,
                    entries=[dict(path=target.name, offset=0, length=3, attempt_limit=1,
                        lstat=reliability._mapper_stamp_v1(target.lstat()), fstat=target_fd,
                        parent_chain=root_chain)], limits=dict(attempts=1, target_bytes=4, basis_bytes=3,
                        metadata_calls=metadata, single_target_buffer=4), chunk_bytes=3,
                    deadline_ns=state["child"])
                binding = dict(kind="MAPPER_NATIVE_READ_BINDING_V2", run_id=paths.run_id,
                    phase=phase, command_index=row.command_index, command_count=len(plan),
                    original_position=position, repo_root=str(root), process_root=str(paths.process_root),
                    evidence_root=str(paths.evidence_root), parent_argv=list(row.argv), child_argv=child,
                    run_read_limits=read_limits, basis=basis,
                    activation_limits=dict(target_bytes=4, basis_bytes=3,
                        metadata_calls=metadata + 3*r + 2*b + 3*p + 6,
                        record_bytes=100_000, evidence_deadline_ns=state["deadline"]))
                bindings[str(row.command_index)] = reliability._mapper_binding_v1(binding)
                if child is not None:
                    # Finite evidence roster and six retained files per nested
                    # route. Every possible original barrier/final recheck is
                    # reserved before dispatch, not enlarged after a failure.
                    state["nested"][row.command_index] = dict(
                        entry_limit=3*len(plan)+2*len(selected)+4,
                        file_byte_limit=100_000, retained_byte_limit=1_000_000,
                        read_byte_limit=(2*len(plan)+16)*6*100_000,
                        child_execution_deadline_ns=state["child"],
                        execution_deadline_ns=state["parent"], deadline_ns=state["deadline"])
            state["bindings"] = bindings
            return bindings

        def candidate_supplier(root, plan):
            assert state["paths"].repo_root == root and state["plan"] is plan
            names = tuple(sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()))
            return _synthetic_candidate_custody_v1(root, plan, observed_paths=lambda: names,
                effects=(), deadline_ns=state["deadline"], nested_evidence_limits=state["nested"])

        previous_provenance = getattr(runner.write_run_provenance, "_fixture_original", runner.write_run_provenance)
        previous_atomic = getattr(runner.atomic_write_json, "_fixture_original", runner.atomic_write_json)
        def write_fixture_provenance(*args, **kwargs):
            previous_provenance(*args, **kwargs)
            if previous_provenance is not reliability.write_run_provenance:
                reliability.write_run_provenance(*args, **kwargs)
        def write_fixture_atomic(path, payload):
            previous_atomic(path, payload)
            if previous_atomic is not reliability.atomic_write_json:
                reliability.atomic_write_json(path, payload)
        write_fixture_provenance._fixture_original = previous_provenance
        write_fixture_atomic._fixture_original = previous_atomic
        patcher.setattr(runner, "write_run_provenance", write_fixture_provenance)
        patcher.setattr(runner, "atomic_write_json", write_fixture_atomic)
        patcher.setattr(runner, "_prepare_validation_candidate_v1", original_prepare)
        if mock_commands:
            # These root/uniqueness tests previously substituted the whole
            # run_commands port. Only their synthetic process outcomes move
            # through the real admission/finalizer path; no application runs.
            patcher.setattr(runner.subprocess, "run", lambda command, **kwargs:
                SimpleNamespace(returncode=0, stdout=_st12h_mock_terminal_output(command), stderr=""))
        original_port = runner._execute_supervised_command
        if resolve_paths:
            patcher.setattr(runner, "resolve_validation_run_paths", resolve_scan_fixture)
            original_port = supervise_scan_fixture

        def supervise_bound_fixture(command, **kwargs):
            if "execution_deadline_ns" in kwargs:
                # Match the existing native supervisor's launch-time clamp.
                # The earlier planner timeout cannot widen the armed gate.
                remaining = (kwargs["execution_deadline_ns"] - runner.time.monotonic_ns()) / 1e9
                assert remaining > 0
                prior = kwargs.get("timeout_seconds")
                kwargs["timeout_seconds"] = remaining if prior is None else min(prior, remaining)
            receipt = original_port(command, **kwargs)
            position = reliability._mapper_original_position_v1(tuple(command), Path(kwargs["cwd"]))
            if position is None:
                return receipt
            paths = state["paths"]
            assert kwargs["run_id"] == paths.run_id and kwargs["phase"] == state["phase"]
            row = state["plan"][kwargs["command_index"] - 1]
            assert row.argv == tuple(command)
            _, live = reliability._mapper_read_profile_for_process_v1(paths.repo_root,
                environment=kwargs["environment"], actual_argv=tuple(command), role="PARENT")
            assert live["original_position"] == position
            with reliability._mapper_bound_reads_v1(live) as reader:
                assert reader.read_json("mapper-fixture.json", json.loads) == {}
                assert reader.counters["attempts"] == 1
            controls = reliability._mapper_read_controls_v1(state["bindings"][str(row.command_index)])
            controls += ((reliability._MAPPER_ACTIVATION_ENV_V1,
                          kwargs["environment"][reliability._MAPPER_ACTIVATION_ENV_V1]),)
            if live["child_argv"] is not None:
                gate = runner._RUN_COMMANDS_SUPERVISION["nested_evidence"][row.command_index]
                assert gate.planned is row and gate.paths is paths
                controls = gate.parent_controls
                from tools.run_pytest_fresh_basetemp import _allocate_nested_evidence_root
                child_root = _allocate_nested_evidence_root(paths.evidence_root, pid=receipt.pid)
                child = replace(receipt, phase="nested-pytest", command_index=1,
                    argv=gate.child_argv, pid=receipt.pid+1,
                    timeout_seconds_or_null=(state["child"]-runner.time.monotonic_ns())/1e9,
                    timeout_state="NOT_TRIGGERED", stdout_required_markers=(),
                    stdout_marker_state="NOT_REQUIRED", stdout_path=str(child_root/"command-1.stdout.bin"),
                    stderr_path=str(child_root/"command-1.stderr.bin"), **gate.child_projection)
                Path(child.stdout_path).write_bytes(b"")
                Path(child.stderr_path).write_bytes(b"")
                reliability.atomic_write_json(child_root/"command-1.json", child)
            receipt = replace(receipt, fixed_environment_controls=controls)
            Path(receipt.stdout_path).write_bytes(b"")
            Path(receipt.stderr_path).write_bytes(b"")
            reliability.atomic_write_json(paths.evidence_root/f"command-{row.command_index}.json", receipt)
            return receipt
        patcher.setattr(runner, "_execute_supervised_command", supervise_bound_fixture)
        return dict(scan_capacity_source=scan_supplier, mapper_read_source=mapper_supplier,
                    candidate_source=candidate_supplier)

    return activate_synthetic_scan



def _extend_synthetic_reader_launch_v1(legacy, issued_inputs, reader_inputs):
    """Extend only the existing finite mocked orchestration fixture."""
    from dataclasses import replace
    root = legacy.paths.repo_root
    assert root != REPO_ROOT
    roles = {entry.command_index: reliability._rp5a_consumer_role_v1(entry.argv, root)
             for entry in legacy.plan}
    selected = {index for index, role in roles.items() if role is not None}
    limits = replace(legacy.read_limits, profile_limit=len(legacy.profiles) + len(selected))
    scanners, readers, bases, inputs = {}, {}, {}, {}
    original_profile = next(iter(legacy.profiles.values()))
    original_input = next(iter(legacy.launch_inputs.values()))
    read_allowance = (4 * (limits.byte_limit + 4) + 9) * sum(
        len(row.content) + sum(len(name.encode("utf-8")) for name in row.children)
        for row in original_input.candidate_files) * len(selected)
    reader_fence = reliability._ScanCandidateFence(root, original_input.candidate_files,
        limits=limits, candidate_read_bytes=read_allowance, deadline_ns=legacy.deadline_ns)
    basis = reliability._Rp5aReadBasisV1("1" * 40, b"# synthetic historical data\n",
        4096, 10, 256, 4096, 1000, 100, 1000)
    for index in sorted(selected):
        reader_root = legacy.paths.process_root / ("reader-" + str(index))
        reader_root.mkdir()
        readers[index] = replace(original_profile, command_index=index, scratch_root=str(reader_root))
        bases[index] = basis
        if index in legacy.profiles:
            scanner_root = legacy.paths.process_root / ("scanner-" + str(index))
            scanner_root.mkdir()
            scanners[index] = replace(legacy.profiles[index], scratch_root=str(scanner_root))
            frame_root = original_input.scratch_root
        else:
            frame_root = legacy.paths.process_root / ("input-" + str(index))
            frame_root.mkdir()
        identity = reliability._ScanLaunchIdentity(legacy.paths.run_id, legacy.phase,
            index, len(legacy.plan), legacy.plan[index - 1].argv, str(root))
        input_owner = reliability._ScanLaunchInput(identity, original_input.candidate_files,
            limits=limits, candidate_read_bytes=read_allowance,
            deadline_ns=legacy.deadline_ns, scratch_root=frame_root,
            scratch_bytes=original_input.scratch_bytes, parent_frame_reread_bytes=original_input.remaining_reread,
            check_candidate=reader_fence, rp5a_read_basis=basis)
        inputs[index] = input_owner
        if index in legacy.profiles:
            issued_inputs[issued_inputs.index(original_input)] = input_owner
        else:
            reader_inputs.append(input_owner)
    return reliability._prepare_scan_launch(legacy.paths, phase=legacy.phase, plan=legacy.plan,
        profiles=scanners, reader_profiles=readers, reader_bases=bases, launch_inputs=inputs,
        read_limits=limits, deadline_ns=legacy.deadline_ns)


def _st12h_mock_terminal_output(command: list[str]) -> str:
    contract = runner._st12h_command_contract(command)
    if contract is None:
        return ""
    _timeout, markers = contract
    return "" if not markers else "\n".join(markers) + "\n"


def _record_fake_aggregate_success_receipts(commands) -> None:
    runner._LAST_PLANNED_COMMAND_COUNT = len(commands)
    runner._LAST_COMMAND_RECEIPTS = tuple(
        reliability.CommandExecutionReceiptV1(
            schema_version=1, run_id=runner._RUN_COMMANDS_ACTIVE_PATHS.run_id,
            phase=runner.ALL_PHASE, argv=tuple(_command), cwd=str(REPO_ROOT),
            platform=os.name, start_time_utc="2026-08-24T00:00:00Z",
            end_time_utc="2026-08-24T00:00:01Z", elapsed_monotonic_seconds=1.0,
            start_failure_class=None, timeout_seconds_or_null=None,
            timeout_state="NOT_CONFIGURED", termination_state="NOT_REQUIRED",
            stdout_path=str(runner._RUN_COMMANDS_ACTIVE_PATHS.evidence_root / f"command-{index}.stdout.bin"),
            stderr_path=str(runner._RUN_COMMANDS_ACTIVE_PATHS.evidence_root / f"command-{index}.stderr.bin"),
            stdout_byte_count=0, stderr_byte_count=0, stdout_required_markers=(),
            stderr_was_nonempty=False,
            command_index=index,
            pid=4321,
            native_exit_code=0,
            failure_class=None,
            stdout_marker_state="PASS",
        )
        for index, _command in enumerate(commands, start=1)
    )


def _assert_generic_text_preflight_and_scope_matrix(monkeypatch) -> None:
    from tools import changed_area_validation_router as router
    from tools import validation_scope_registry as scope_registry

    registered_path = (
        "src/qtt/stage1_prediction_markets/"
        "pr168_gfp_real_computation/pnl.py"
    )
    semantic_record = reliability.classify_byte_surfaces(
        path=registered_path,
        baseline_bytes=b"old\n",
        index_bytes=b"new\n",
        worktree_bytes=b"new\n",
        authorized=False,
    )
    representation_record = reliability.classify_byte_surfaces(
        path="representation.py",
        baseline_bytes=b"same\n",
        index_bytes=b"same\n",
        worktree_bytes=b"same\r\n",
        authorized=False,
    )
    with monkeypatch.context() as preflight_patch:
        preflight_patch.setattr(
            runner,
            "classify_repository_changes",
            lambda _root: (semantic_record,),
        )
        records, failures, candidates = _PRODUCTION_TEXT_INTEGRITY_PREFLIGHT(
            REPO_ROOT
        )
    assert records == (semantic_record,)
    assert failures == ()
    assert candidates == (registered_path,)
    assert semantic_record.semantic_scope_member is False

    with monkeypatch.context() as representation_patch:
        representation_patch.setattr(
            runner,
            "classify_repository_changes",
            lambda _root: (representation_record,),
        )
        _records, representation_failures, representation_candidates = (
            _PRODUCTION_TEXT_INTEGRITY_PREFLIGHT(REPO_ROOT)
        )
    assert representation_candidates == ()
    assert any(
        failure.startswith("ENGVR_UNRELATED_TEXT_REPRESENTATION_DRIFT")
        for failure in representation_failures
    )

    assert registered_path not in ci_branch_context.ENGVR_CHANGED_PATHS
    assert scope_registry.is_pr_scoped_changed_path_allowed(
        scope_registry.PR168_GFP_BRANCH,
        registered_path,
    )
    registered_route = router.build_router_result(
        router.RouterInput(
            repo_root=REPO_ROOT,
            changed_files=(registered_path,),
            current_branch=scope_registry.PR168_GFP_BRANCH,
            workflow_event_name="pull_request",
            is_pull_request=True,
        )
    )
    assert registered_route.unknown_files == ()
    assert registered_route.fail_closed_reasons == ()

    unregistered_path = "unregistered/semantic.py"
    assert not scope_registry.is_pr_scoped_changed_path_allowed(
        "feature/unregistered",
        unregistered_path,
    )
    unregistered_route = router.build_router_result(
        router.RouterInput(
            repo_root=REPO_ROOT,
            changed_files=(unregistered_path,),
            current_branch="feature/unregistered",
            workflow_event_name="pull_request",
            is_pull_request=True,
        )
    )
    assert unregistered_route.unknown_files == (unregistered_path,)
    assert unregistered_route.full_validation_required is True

    assert all(
        scope_registry.is_pr_scoped_changed_path_allowed(
            ci_branch_context.ENGVR_IMPLEMENTATION_BRANCH,
            path,
        )
        for path in ci_branch_context.ENGVR_CHANGED_PATHS
    )
    assert not scope_registry.is_pr_scoped_changed_path_allowed(
        ci_branch_context.ENGVR_IMPLEMENTATION_BRANCH,
        registered_path,
    )
    runner_source = Path(runner.__file__).read_text(encoding="utf-8")
    assert "ENGVR_CHANGED_PATHS as ENGVR_AUTHORIZED_PATHS" not in runner_source
    assert "ENGVR_AUTHORIZED_PATHS" not in runner_source
    assert "semantic_candidate_paths(records)" in runner_source
    assert "include_authority_boundary=False" in runner_source


def _assert_actual_runner_receipt_integration(
    external_parent: Path,
    monkeypatch,
) -> None:
    REPO_ROOT = (external_parent.parent / "receipt-fixture-repo").resolve()
    REPO_ROOT.mkdir(parents=True, exist_ok=False)
    marker = "ENGVR_ACTUAL_RECEIPT_INTEGRATION_OK"
    command = (sys.executable, "-c", f'print("{marker}")')
    before_evidence = set(external_parent.glob("*.evidence"))
    started = time.monotonic()
    with monkeypatch.context() as production_path:
        production_path.setattr(
            runner,
            "resolve_validation_run_paths",
            reliability.resolve_validation_run_paths,
        )
        production_path.setattr(
            runner,
            "write_run_provenance",
            reliability.write_run_provenance,
        )
        production_path.setattr(
            runner,
            "_execute_supervised_command",
            reliability.supervise_command,
        )
        production_path.setattr(
            runner,
            "cleanup_validation_run",
            reliability.cleanup_validation_run,
        )
        production_path.setattr(
            runner,
            "atomic_write_json",
            reliability.atomic_write_json,
        )
        production_path.setattr(
            runner,
            "validate_complete_run_evidence",
            reliability.validate_complete_run_evidence,
        )
        production_path.setattr(
            runner,
            "validate_published_completion_receipt",
            reliability.validate_published_completion_receipt,
        )
        assert runner.resolve_validation_run_paths is (
            reliability.resolve_validation_run_paths
        )
        assert runner.write_run_provenance is reliability.write_run_provenance
        assert runner._execute_supervised_command is reliability.supervise_command
        assert runner.cleanup_validation_run is reliability.cleanup_validation_run
        assert runner.atomic_write_json is reliability.atomic_write_json
        assert runner.validate_complete_run_evidence is (
            reliability.validate_complete_run_evidence
        )
        assert runner.validate_published_completion_receipt is (
            reliability.validate_published_completion_receipt
        )
        run_paths, probe = runner.resolve_validation_run_paths(
            REPO_ROOT,
            explicit_process_root=external_parent,
            projected_relative_paths=("command-1.stdout.bin",),
        )
        runner.write_run_provenance(
            run_paths,
            probe,
            phase=runner.FAST_PREFLIGHT_PHASE,
            command_count=1,
            text_integrity_preflight_state="PASS",
        )
        receipt = runner._execute_supervised_command(
            command,
            cwd=REPO_ROOT,
            run_id=run_paths.run_id,
            phase=runner.FAST_PREFLIGHT_PHASE,
            command_index=1,
            evidence_root=run_paths.evidence_root,
            required_markers=(marker,),
            timeout_seconds=180,
            environment=os.environ,
        )
        result, cleanup_state, completion = runner._finalize_validation_run(
            run_paths=run_paths,
            probe=probe,
            phase=runner.FAST_PREFLIGHT_PHASE,
            planned_count=1,
            expected_plan=reliability.build_command_evidence_plan(
                run_id=run_paths.run_id,
                phase=runner.FAST_PREFLIGHT_PHASE,
                commands=(command,),
                cwd=REPO_ROOT,
            ),
            receipts=(receipt,),
            result=0,
            text_state="PASS",
        )
    elapsed = time.monotonic() - started
    assert result == 0
    assert elapsed < 180
    print(f"ENGVR_ACTUAL_RECEIPT_INTEGRATION_ELAPSED_SECONDS={elapsed:.6f}")
    created_evidence = set(external_parent.glob("*.evidence")) - before_evidence
    assert len(created_evidence) == 1
    evidence_root = created_evidence.pop()
    run_payload = json.loads(
        (evidence_root / "run.json").read_text(encoding="utf-8")
    )
    completion_payload = json.loads(
        (evidence_root / "completion.json").read_text(encoding="utf-8")
    )
    cleanup_payload = json.loads(
        (evidence_root / "cleanup.json").read_text(encoding="utf-8")
    )
    command_payload = json.loads(
        (evidence_root / "command-1.json").read_text(encoding="utf-8")
    )
    assert run_payload["command_count"] == 1
    assert run_payload["filesystem_probe"]["failure_operation"] is None
    assert completion_payload["command_count_planned"] == 1
    assert completion_payload["command_count_started"] == 1
    assert completion_payload["command_count_completed"] == 1
    assert completion_payload["required_marker_state"] == "PASS"
    assert completion_payload["evidence_root_state"] == "PRESENT"
    assert command_payload["argv"] == list(command)
    assert command_payload["pid"] == receipt.pid
    assert command_payload["pid"] > 0
    assert command_payload["native_exit_code"] == 0
    assert command_payload["stdout_required_markers"] == [marker]
    assert command_payload["stdout_marker_state"] == "PASS"
    assert marker.encode("utf-8") in (
        evidence_root / "command-1.stdout.bin"
    ).read_bytes()
    assert completion_payload["final_state"] == "PASS"
    assert completion_payload["text_integrity_preflight_state"] == "PASS"
    assert cleanup_payload["cleanup_state"].startswith("PASS")
    assert cleanup_state.startswith("PASS")
    assert completion.final_state == "PASS"
    assert not Path(cleanup_payload["cleanup_target"]).exists()
    assert run_paths.evidence_root.is_dir()
    assert reliability.command_receipt_file_indexes(evidence_root) == (1,)
    assert len(list(evidence_root.glob("command-*.stdout.bin"))) == 1
    assert len(list(evidence_root.glob("command-*.stderr.bin"))) == 1
    assert {
        path.name for path in evidence_root.iterdir() if path.is_file()
    } == {
        "run.json",
        "command-1.stdout.bin",
        "command-1.stderr.bin",
        "command-1.json",
        "cleanup.json",
        "completion.json",
    }


def _assert_exact_stat_command_boundary(monkeypatch, tmp_path: Path) -> None:
    stat_only = reliability.classify_byte_surfaces(
        path="exact-stat.py",
        baseline_bytes=b"same\n",
        index_bytes=b"same\n",
        worktree_bytes=b"same\n",
        git_status_state="DIRTY",
        authorized=True,
    )
    semantic = reliability.classify_byte_surfaces(
        path="semantic.py",
        baseline_bytes=b"old\n",
        index_bytes=b"new\n",
        worktree_bytes=b"new\n",
        git_status_state="DIRTY",
        authorized=True,
    )
    exact_paths = tuple(
        record.path
        for record in (stat_only, semantic)
        if record.change_class == "STAT_CACHE_ONLY_CHANGE"
    )
    assert exact_paths == ("exact-stat.py",)
    refresh_calls = []
    with monkeypatch.context() as refresh_patch:
        refresh_patch.setattr(
            reliability.subprocess,
            "run",
            lambda command, **kwargs: refresh_calls.append((tuple(command), kwargs))
            or subprocess.CompletedProcess(command, 0),
        )
        assert reliability._run_exact_stat_refresh(
            tmp_path.resolve(),
            exact_paths,
            stronger=False,
        ) == 0
        assert reliability._run_exact_stat_refresh(
            tmp_path.resolve(),
            exact_paths,
            stronger=True,
        ) == 0
    assert refresh_calls[0][0] == (
        "git",
        "update-index",
        "--refresh",
        "--",
        "exact-stat.py",
    )
    assert refresh_calls[1][0] == (
        "git",
        "update-index",
        "--really-refresh",
        "--",
        "exact-stat.py",
    )


def _env_without_pythonpath() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    return env


def _owner_gate_git_metadata_responses(branch: str):
    def fake_git_stdout(repo_root, args):
        command = tuple(args)
        if command == ("branch", "--show-current"):
            return 0, branch, ""
        if command == ("rev-parse", "--short", "HEAD"):
            return 0, "abcdef0", ""
        if (
            len(command) == 3
            and command[:2] == ("cat-file", "-e")
            and command[2].endswith("^{commit}")
        ):
            return 0, "", ""
        if (
            len(command) == 4
            and command[:2] == ("merge-base", "--is-ancestor")
            and command[3] == "HEAD"
        ):
            return 0, "", ""
        raise AssertionError(f"unexpected git command: {command!r}")

    return fake_git_stdout


def _default_temp_generated_report(filename: str) -> str:
    return str(
        runner._validation_generated_output(
            runner._default_validation_dir(),
            f"docs/master_plan/generated/{filename}",
        )
    )


def test_runner_uses_github_head_ref_for_detached_pr_merge_checkout(monkeypatch):
    _clear_branch_context_env(monkeypatch)

    class Completed:
        returncode = 0
        stdout = "\n"

    monkeypatch.setenv("GITHUB_HEAD_REF", runner.PR168_RP5G_BRANCH)
    monkeypatch.setattr(runner.subprocess, "run", lambda *args, **kwargs: Completed())

    assert runner._current_git_branch(REPO_ROOT) == runner.PR168_RP5G_BRANCH


def test_runner_pr169_dash1_branch_scope_keeps_only_dash1_deterministic_commands(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        runner,
        "_current_git_branch",
        lambda _repo_root: runner.PR169_DASH1_BRANCH,
    )
    assert runner._pr169_dash1_local_branch_scope_active(
        repo_root=REPO_ROOT,
        phase=runner.DETERMINISTIC_VALIDATORS_PHASE,
        validation_mode="auto",
        changed_files=(),
        force_full=False,
        manual_mode="",
    )

    commands = runner.build_phase_commands(
        runner.DETERMINISTIC_VALIDATORS_PHASE,
        tmp_path / "validation",
        tmp_path / "pytest",
    )
    kept = runner._filter_commands_for_pr169_dash1_local_branch_scope(commands)

    assert [Path(command[1]).name for command in kept] == [
        "build_pr169_dash1_owner_dashboard.py",
        "validate_pr169_dash1_owner_dashboard.py",
    ]
    assert all(
        str(tmp_path / "validation" / "master_plan_generated" / "pr169_dash1")
        in command
        for command in kept
    )


def test_runner_pr169_readiness1_branch_scope_keeps_only_readiness1_deterministic_commands(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        runner,
        "_current_git_branch",
        lambda _repo_root: runner.PR169_READINESS1_BRANCH,
    )
    assert runner._pr169_readiness1_local_branch_scope_active(
        repo_root=REPO_ROOT,
        phase=runner.DETERMINISTIC_VALIDATORS_PHASE,
        validation_mode="auto",
        changed_files=(),
        force_full=False,
        manual_mode="",
    )

    commands = runner.build_phase_commands(
        runner.DETERMINISTIC_VALIDATORS_PHASE,
        tmp_path / "validation",
        tmp_path / "pytest",
    )
    kept = runner._filter_commands_for_pr169_readiness1_local_branch_scope(commands)

    assert [Path(command[1]).name for command in kept] == [
        "build_pr169_readiness1.py",
        "validate_pr169_readiness1.py",
    ]
    assert all(
        any("pr169_readiness1" in part for part in command)
        for command in kept
    )


def test_owner_authorized_validation_branch_keeps_all_non_guarded_commands(
    capsys,
):
    branches = (
        "agent/st12a-contract-envelope",
        "repair/no-runtime-custody-and-ci-dependency-boundary",
    )
    commands = [
        ["python", "tools/build_pr168_rp5c_immutable_qku_formula_library.py"],
        ["python", "tools/build_qku_computation_control_plane.py"],
        [
            "python",
            "tools/build_pr169_readiness1.py",
            "--out-dir",
            ".tmp/pr169_readiness1",
        ],
        [
            "python",
            "tools/build_pr169_svc1.py",
            "--out-dir",
            "docs/master_plan/generated",
        ],
        ["python", "tools/validate_pr168_rp5c_immutable_qku_formula_library.py"],
        ["python", "tools/run_pr168_vs1_trading_intelligence_slice.py"],
    ]

    for branch in branches:
        kept = runner._filter_foreign_branch_guarded_builders_for_owner_validation(
            commands,
            branch=branch,
        )
        kept_names = [runner._command_script_name(command) for command in kept]

        assert kept_names == [
            "build_qku_computation_control_plane.py",
            "build_pr169_readiness1.py",
            "build_pr169_svc1.py",
            "validate_pr168_rp5c_immutable_qku_formula_library.py",
            "run_pr168_vs1_trading_intelligence_slice.py",
        ]
        assert len(commands) - len(kept) == 1
        assert kept_names.count(
            "build_pr168_rp5c_immutable_qku_formula_library.py"
        ) == 0
        assert kept_names.count(
            "validate_pr168_rp5c_immutable_qku_formula_library.py"
        ) == 1
        assert all(
            runner._command_script_name(command) in kept_names
            for command in commands
            if runner._command_script_name(command).startswith("validate_")
        )
        assert all(
            runner._command_script_name(command) in kept_names
            for command in commands
            if runner._command_script_name(command).startswith("build_")
            and runner._command_script_name(command)
            not in runner.OWNER_VALIDATION_READ_ONLY_UPSTREAM_BUILDER_SCRIPT_NAMES
        )

    output = capsys.readouterr().out
    assert output.count(
        "QTT_OWNER_AUTHORIZED_VALIDATION_UPSTREAM_BUILDERS_READ_ONLY"
    ) == len(branches)
    assert output.count("build_pr168_rp5c_immutable_qku_formula_library.py") == len(
        branches
    )
    for branch in branches:
        assert f"branch={branch}" in output

    unclassified_branches = ["feature/unrelated", "main"]
    for branch in branches:
        unclassified_branches.extend((f"{branch}-copy", branch.upper()))
    for unclassified_branch in unclassified_branches:
        assert runner._filter_foreign_branch_guarded_builders_for_owner_validation(
            commands,
            branch=unclassified_branch,
        ) == commands


def test_st12_architecture_oracle_prerequisite_filters_only_rp5c_builder(capsys):
    commands = [
        ["python", "tools/build_pr168_rp5c_immutable_qku_formula_library.py"],
        ["python", "tools/validate_pr168_rp5c_immutable_qku_formula_library.py"],
        ["python", "tools/validate_validation_inventory.py"],
    ]

    kept = runner._filter_foreign_branch_guarded_builders_for_owner_validation(
        commands,
        branch=(
            ci_branch_context.ST12_ARCHITECTURE_ORACLE_PREREQUISITE_REPAIR_BRANCH
        ),
    )
    kept_names = [runner._command_script_name(command) for command in kept]

    assert kept_names.count(
        "build_pr168_rp5c_immutable_qku_formula_library.py"
    ) == 0
    assert kept_names.count(
        "validate_pr168_rp5c_immutable_qku_formula_library.py"
    ) == 1
    assert kept_names.count("validate_validation_inventory.py") == 1
    assert len(kept) == 2
    output = capsys.readouterr().out
    assert output.count(
        "QTT_OWNER_AUTHORIZED_VALIDATION_UPSTREAM_BUILDERS_READ_ONLY"
    ) == 1
    assert (
        "branch="
        + ci_branch_context.ST12_ARCHITECTURE_ORACLE_PREREQUISITE_REPAIR_BRANCH
    ) in output


def test_owner_authorized_validation_phase_omits_no_validator(tmp_path):
    validation_root = tmp_path / "validation"
    commands = runner.build_phase_commands(
        "deterministic-validators-c",
        validation_root,
        tmp_path / "pytest",
    )
    original_names = [runner._command_script_name(command) for command in commands]
    original_validator_names = {
        runner._command_script_name(command)
        for command in commands
        if runner._command_script_name(command).startswith("validate_")
    }
    assert original_names.count(
        "build_pr168_rp5c_immutable_qku_formula_library.py"
    ) == 1
    assert original_names.count(
        "validate_pr168_rp5c_immutable_qku_formula_library.py"
    ) == 1

    for branch in (
        "agent/st12a-contract-envelope",
        "repair/no-runtime-custody-and-ci-dependency-boundary",
    ):
        kept = runner._filter_foreign_branch_guarded_builders_for_owner_validation(
            commands,
            branch=branch,
        )
        kept_names = [runner._command_script_name(command) for command in kept]
        kept_name_set = set(kept_names)

        assert original_validator_names <= kept_name_set
        assert len(commands) - len(kept) == 1
        assert kept_names.count(
            "build_pr168_rp5c_immutable_qku_formula_library.py"
        ) == 0
        assert kept_names.count(
            "validate_pr168_rp5c_immutable_qku_formula_library.py"
        ) == 1
        assert "build_pr169_readiness1.py" in kept_name_set
        assert "validate_pr169_readiness1.py" in kept_name_set


def test_run_validation_gates_direct_script_imports_router_without_pythonpath(
    monkeypatch,
    tmp_path,
):
    fixture_repo = (tmp_path / "r").resolve()
    fixture_hooks = (tmp_path / "h").resolve()
    external_parent = (tmp_path / "p").resolve()
    for directory in (fixture_repo, fixture_hooks, external_parent):
        directory.mkdir()
        assert directory.is_dir() and not directory.is_symlink()
        assert not getattr(directory.lstat(), "st_file_attributes", 0) & 0x400
    assert not tuple(fixture_hooks.iterdir())

    source_paths = (
        "tools/run_validation_gates.py",
        "tools/validation_reliability.py",
        "tools/validation_scope_registry.py",
        "tools/ci_branch_context.py",
        "tools/changed_area_validation_router.py",
        "tools/validation_inventory.py",
        "tools/repo_path_refs.py",
    )
    copied_sources = {}
    for relative_path in source_paths:
        content = (REPO_ROOT / relative_path).read_bytes()
        destination = fixture_repo / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        assert destination.read_bytes() == content
        copied_sources[relative_path] = content
    (fixture_repo / ".gitattributes").write_bytes(b"*.py text eol=lf\n")
    (fixture_repo / ".gitignore").write_bytes(b"__pycache__/\n")

    environment = _env_without_pythonpath()
    for env_name in tuple(environment):
        if env_name.upper().startswith("GIT_"):
            environment.pop(env_name)
    environment.update(
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_TERMINAL_PROMPT="0",
        GIT_NO_REPLACE_OBJECTS="1",
        GIT_NO_LAZY_FETCH="1",
        GIT_ALLOW_PROTOCOL="",
        PYTHONDONTWRITEBYTECODE="1",
    )
    environment[reliability.PROCESS_ROOT_ENV] = str(external_parent)
    for env_name in (
        reliability.RUN_ID_ENV,
        reliability.EVIDENCE_ROOT_ENV,
        runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV,
        runner.PR152_BUILD_REPORT_CACHE_ENV,
        "QTT_FORCE_FULL_VALIDATION",
        *BRANCH_CONTEXT_ENV,
    ):
        environment.pop(env_name, None)

    def fixture_git(*arguments):
        result = subprocess.run(
            [
                "git",
                "-c", "user.name=QTT test fixture",
                "-c", "user.email=qtt-fixture@example.invalid",
                "-c", "commit.gpgsign=false",
                "-c", "core.autocrlf=false",
                "-c", f"core.hooksPath={fixture_hooks}",
                *arguments,
            ],
            cwd=fixture_repo,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
        assert result.returncode == 0, result.stderr.decode("utf-8")
        return result.stdout

    fixture_git("init", "--initial-branch=main")
    fixture_git("add", "--", ".gitattributes", ".gitignore", *source_paths)
    fixture_git("commit", "-m", "Direct runner test fixture")
    fixture_git("update-ref", "refs/remotes/origin/main", "HEAD")
    assert fixture_git("status", "--porcelain=v1", "-z", "--untracked-files=all") == b""
    fixture_head = fixture_git("rev-parse", "HEAD")
    fixture_index = fixture_git("ls-files", "--stage", "-z")
    fixture_entries = [entry for entry in fixture_index.split(b"\0") if entry]
    assert len(fixture_entries) == len(source_paths) + 2
    assert all(entry.split(b"\t", 1)[0].split()[2] == b"0" for entry in fixture_entries)

    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(Path("tools") / "run_validation_gates.py"),
            "--phase",
            "fast-preflight",
            "--validation-mode",
            "reduced",
            "--changed-file",
            "docs/master_plan/generated/UnownedGeneratedReport.report.json",
        ],
        cwd=fixture_repo,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )

    combined_output = completed.stdout + completed.stderr
    assert completed.returncode == 2
    assert "GENERATED_REPORT_OWNER_MISSING" in combined_output
    assert "ModuleNotFoundError" not in combined_output
    assert "No module named 'tools'" not in combined_output
    assert "QTT_VALIDATION_TEXT_INTEGRITY_PREFLIGHT_OK" in combined_output
    assert runner.SUCCESS_MARKER not in combined_output
    assert fixture_git("status", "--porcelain=v1", "-z", "--untracked-files=all") == b""
    fixture_head_unchanged = fixture_git("rev-parse", "HEAD") == fixture_head
    fixture_index_unchanged = fixture_git("ls-files", "--stage", "-z") == fixture_index
    assert fixture_head_unchanged
    assert fixture_index_unchanged
    for relative_path, content in copied_sources.items():
        assert (fixture_repo / relative_path).read_bytes() == content
    assert not (fixture_repo / "docs").exists()
    assert not tuple(fixture_hooks.iterdir())

    evidence_roots = tuple(external_parent.glob("*.evidence"))
    assert len(evidence_roots) == 1
    evidence_root = evidence_roots[0]
    assert evidence_root.is_dir()
    run_payload = json.loads((evidence_root / "run.json").read_bytes().decode("utf-8"))
    completion_payload = json.loads(
        (evidence_root / "completion.json").read_bytes().decode("utf-8")
    )
    cleanup_payload = json.loads(
        (evidence_root / "cleanup.json").read_bytes().decode("utf-8")
    )
    assert Path(run_payload["paths"]["repo_root"]).resolve() == fixture_repo
    assert run_payload["phase"] == runner.FAST_PREFLIGHT_PHASE
    assert run_payload["command_count"] == 0
    assert run_payload["text_integrity_preflight_state"] == "PASS"
    assert run_payload["paths"]["filesystem_probe_state"] == "PASS"
    probe = run_payload["filesystem_probe"]
    assert probe["created_directory"] is True
    assert probe["written_bytes"] > 0
    assert probe["readback_equal"] is True
    assert probe["rename_equal"] is True
    assert probe["unlink_success"] is True
    assert probe["directory_cleanup_success"] is True
    assert probe["failure_operation"] is None
    assert probe["native_error_class"] is None
    assert completion_payload["final_state"] == "FAIL"
    assert completion_payload["text_integrity_preflight_state"] == "PASS"
    assert completion_payload["command_count_planned"] == 0
    assert completion_payload["command_count_started"] == 0
    assert completion_payload["command_count_completed"] == 0
    assert completion_payload["required_marker_state"] == "NOT_RUN"
    assert completion_payload["evidence_root_state"] == "PRESENT"
    assert completion_payload["run_id"] == run_payload["run_id"]
    assert cleanup_payload["run_id"] == run_payload["run_id"]
    assert cleanup_payload["cleanup_state"].startswith("PASS")
    assert completion_payload["process_root_cleanup_state"] == cleanup_payload["cleanup_state"]
    assert cleanup_payload["parent_preserved"] is True
    cleanup_target = Path(cleanup_payload["cleanup_target"])
    assert cleanup_target == Path(run_payload["paths"]["cleanup_target"])
    assert cleanup_target.parent == external_parent
    assert not cleanup_target.exists()
    assert evidence_root.is_dir()
    assert reliability.command_receipt_file_indexes(evidence_root) == ()
    assert not tuple(evidence_root.glob("command-*.json"))
    assert not tuple(evidence_root.glob("command-*.stdout.bin"))
    assert not tuple(evidence_root.glob("command-*.stderr.bin"))
    _assert_generic_text_preflight_and_scope_matrix(monkeypatch)
    _assert_actual_runner_receipt_integration(external_parent, monkeypatch)


def test_validate_validation_inventory_direct_script_imports_pr208_modules_without_pythonpath():
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(Path("tools") / "validate_validation_inventory.py"),
        ],
        cwd=REPO_ROOT,
        env=_env_without_pythonpath(),
        capture_output=True,
        text=True,
        timeout=60,
    )

    combined_output = completed.stdout + completed.stderr
    assert completed.returncode == 0, combined_output
    assert "VALIDATION_INVENTORY_OK" in completed.stdout
    assert "ModuleNotFoundError" not in combined_output
    assert "No module named 'tools'" not in combined_output


def _expected_commands(
    python_executable: str,
    pytest_basetemp: Path | None = None,
) -> list[list[str]]:
    validation_dir = runner._default_validation_dir()
    if pytest_basetemp is None:
        pytest_basetemp = runner._default_pytest_basetemp()
    section_manifest = validation_dir / "SectionManifest.json"
    traceability_report = validation_dir / "TraceabilityReport.json"
    first_pr_scope_report = validation_dir / "FirstPrScopeReport.json"
    row_family_currentization_report = (
        validation_dir / "AtomicRowsRowFamilySourceManifestCurrentization.report.json"
    )
    master_plan = Path("docs") / "master_plan" / "QTT_MasterPlan_Current.md"

    commands = [
        [
            python_executable,
            str(Path("tools") / "master_plan_ingest.py"),
            "--input",
            str(master_plan),
            "--section-manifest-out",
            str(section_manifest),
            "--traceability-out",
            str(traceability_report),
            "--scope-report-out",
            str(first_pr_scope_report),
        ],
        [
            python_executable,
            str(Path("tools") / "master_plan_traceability_check.py"),
            "--master-plan",
            str(master_plan),
            "--section-manifest",
            str(section_manifest),
            "--traceability-report",
            str(traceability_report),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_first_pr_scope.py"),
            "--repo-root",
            ".",
            "--scope-report",
            str(first_pr_scope_report),
            "--block-runtime",
            "--block-live",
            "--block-sha",
            "--block-companion-package",
            "--block-profit-claims",
            "--block-source-retrieval",
            "--block-source-acceptance",
            "--block-connector-binding",
            "--block-private-state-fetch",
            "--block-order-execution",
            "--block-neural-training",
            "--block-neural-inference",
            "--block-external-repo-clone",
            "--block-package-install-scripts",
        ],
        [
            python_executable,
            "-c",
            runner.PR138_NON_MUTATING_VALIDATION_SCRIPT,
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_row_family_source_manifest_currentization.py"
            ),
            "--repo-root",
            ".",
            "--out",
            str(row_family_currentization_report),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_semantic_field_coverage_enrichment_plan.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_idempotence_runtime_containment.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_semantic_value_materialization_owner_authorization_gate.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_owner_global_override_authority.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "QTTOwnerGlobalOverrideAuthority.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_semantic_value_materialization_implementation_bridge.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_source_backed_classical_quantum_parameter_default_target_matrix.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_official_source_retrieval_target_pack_parameter_defaults.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_grand_global_debug_logical_consistency_audit.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_controlled_official_source_capture_candidate_packets.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr153r_redo_external_source_value_capture_targets.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr153s_source_value_capture_closure_classifier.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_parameter_default_value_materialization_gate.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_agent_consumable_parameter_default_registry.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_agent_default_binding_universal_intake_gate.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr157_pr154_atomicrows_completion_materialization_bridge.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr158_owner_response_selection_readiness_bridge.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr159_official_source_completion_bridge.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr160_split_reclassification_route_closure.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr159r_source_locator_value_capture.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr159s_open_intake_completion.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr161a_atomicrows_pr154_value_state_materialization.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr161b_master_plan_residual_candidate_coverage.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr161c_qku_residual_candidate_assimilation.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr161d_qku_candidate_quality_replay_paper_prioritization.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr161e_replay_paper_outcome_capture_scenario_learning.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr161f_replay_paper_executor_input_run_artifact_generation.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr162b_qku_formula_algorithm_solver_market_scope_materialization.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr162d_aggressive_qku_candidate_materialization_agent_routing.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr162r_a_replay_paper_executability_classification_audit.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr162d_r2a_real_formulations.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr162r_generic_replay_paper_adapter_rerun.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr162r_b_replay_paper_data_binding_completion.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr163_generic_paper_adapter_capture_framework.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr163_b_paired_replay_paper_concurrent_executor.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr164_review_provenance_qku_canonical_coverage_audit.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr163_c_pretrade_infrastructure_rejection_remediation.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr165_evidence_backed_scoring_ranking.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr165_b_condition_scoped_negative_memory.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr165_c_replay_paper_memory_consumer_integration.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr165_d_scenario_qku_combination_selection.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr166_s_replay_paper_scenario_retest_execution.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr166_sm_score_memory_refresh_from_pr166_s_results.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr166_sf_repair_materialization_before_retest.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr166_s2_replay_paper_retest_loop_v2.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr166_sm2_score_memory_refresh_v2.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr166_sf_r2_targeted_conversion_repair_retest.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr166_sm3_score_memory_refresh_v3.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr166_q_quantum_classical_hybrid_comparator.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr166_qb_bounded_quantum_benchmark.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr166_qc_quantum_selected_replay_paper_retest.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr162e_q_quantum_automapper.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr167_open_trade_simulator_integration.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr162e_plugin_framework.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr162e_negative_repair_factory.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr162e_no_orphan_lineage.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "build_pr168_gfp_global_formula_discovery_real_computation.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_baseline_count_reconcile.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr168_gfp_no_fake_positive_negative_labels.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_formula_assignment_coverage.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_real_formula_computation.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_formula_registry_integrity.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr168_gfp_atomicrows_computation_coverage.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_qku_computation_coverage.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr168_gfp_candidate_packet_v1_coverage.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr168_gfp_quantum_objective_coefficients.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr168_gfp_metadata_placeholder_demotions.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_truth_overlay_required.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_report_compactness.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_formula_source_arbitration.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr168_gfp_master_plan_formula_catalog_diff.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr168_gfp_minimum_tradability_formula_set.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr168_gfp_forbidden_bundle_terminology.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_no_orphan_lineage.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp_authority_boundaries.py"),
        ],
        *[
            [
                python_executable,
                str(Path("tools") / script_name),
            ]
            for script_name in (
                "build_pr168_rp_formula_based_replay_paper_recompute.py",
                "validate_qtt_authority_reason_code_registry.py",
                "validate_pr168_rp_formula_execution.py",
                "validate_pr168_rp_replay_paper_results.py",
                "validate_pr168_rp_no_fake_computed_labels.py",
                "validate_pr168_rp_tca_pnl_math.py",
                "validate_pr168_rp_microstructure_fill_model.py",
                "validate_pr168_rp_pretrade_simulation_kernel.py",
                "validate_pr168_rp_order_policy_candidate_ranking.py",
                "validate_pr168_rp_no_trade_candidate.py",
                "validate_pr168_rp_scenario_ladder.py",
                "validate_pr168_rp_latency_budget.py",
                "validate_pr168_rp_live_candidate_handoff_no_order_authority.py",
                "validate_pr168_rp_probability_calibration.py",
                "validate_pr168_rp_overfit_fdr.py",
                "validate_pr168_rp_quantum_objective_recompute.py",
                "validate_pr168_rp_quantum_structural_readiness.py",
                "validate_pr168_rp_portfolio_marginal_utility.py",
                "validate_pr168_rp_capacity_crowding.py",
                "validate_pr168_rp_regime_memory.py",
                "validate_pr168_rp_champion_challenger.py",
                "validate_pr168_rp_combination_selection.py",
                "validate_pr168_rp_negative_recovery.py",
                "validate_pr168_rp_edge_attribution.py",
                "validate_pr168_rp_agent_duty_orchestration.py",
                "validate_pr168_rp_connector_candidate_routing.py",
                "validate_pr168_rp_strict_input_consumption.py",
                "validate_pr168_rp_no_orphan_lineage.py",
                "validate_pr168_rp_artifact_information_value_dag.py",
                "validate_pr168_rp_authority_boundaries.py",
                "validate_pr168_rp_report_compactness.py",
                "validate_pr168_rp_validation_scope_registry_integration.py",
                "validate_pr168_rp_windows_linux_compatibility.py",
                "validate_pr168_rp_no_metadata_only_pass.py",
                "validate_pr168_rp_no_forced_negative_to_positive.py",
                "validate_pr168_rp_no_scattered_authority_wording.py",
            )
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rank_evidence_backed_ranking.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_data1_public_market_data_snapshots.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_data1a_focused_audit.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_gfp2r_data1a_gated_candidate_recompute.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp2_map2.py"),
            "--offline",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp2_map2.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_map3.py"),
            "--offline",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_map3.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp3.py"),
            "--offline",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp3.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rank3.py"),
            "--offline",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rank3.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp5a_legacy_semantic_audit.py"),
            "--offline",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp5a_legacy_semantic_audit.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp5b_active_registry_safe_cleanup.py"),
            "--dry-run",
            "--offline",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp5b_active_registry_safe_cleanup.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp5c_immutable_qku_formula_library.py"),
            "--offline",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp5c_immutable_qku_formula_library.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "run_pr168_vs1_trading_intelligence_slice.py"),
            "--fixture",
            "all",
            "--top-k",
            "10",
            "--max-identities",
            "50",
            "--max-stacks-per-fixture",
            "20",
            "--dump-temp",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_vs1_trading_intelligence_slice.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp5d_replay_paper_executability_tiers.py"),
            "--offline",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp5d_replay_paper_executability_tiers.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp5e_stack_gen.py"),
            "--offline",
            "--fixture",
            "sample",
            "--max-stacks",
            "1000",
            "--dump-temp",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp5e_stack_gen.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp5d_r1_exec_now_unlock.py"),
            "--offline",
            "--fixture",
            "sample",
            "--target-min",
            "5",
            "--target-max",
            "15",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp5d_r1_exec_now_unlock.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp5f_dynamic_targets.py"),
            "--offline",
            "--fixture",
            "sample",
            "--max-targets",
            "25",
            "--max-seeds",
            "500",
            "--dump-temp",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp5f_dynamic_targets.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rp5g_trade_plan_sim.py"),
            "--offline",
            "--fixture",
            "sample",
            "--max-candidates",
            "10",
            "--out",
            "docs/master_plan/generated/pr168_rp5g",
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rp5g_trade_plan_sim.py"),
            "--generated",
            "docs/master_plan/generated/pr168_rp5g",
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_rank4_advisory_ranking.py"),
            "--repo-root",
            ".",
            "--out-dir",
            "docs/master_plan/generated/pr168_rank4",
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_rank4_advisory_ranking.py"),
            "--repo-root",
            ".",
            "--artifact-dir",
            "docs/master_plan/generated/pr168_rank4",
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_qopt1_batch_optimization.py"),
            "--repo-root",
            ".",
            "--out-dir",
            "docs/master_plan/generated/pr168_qopt1",
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_qopt1_batch_optimization.py"),
            "--repo-root",
            ".",
            "--artifact-dir",
            "docs/master_plan/generated/pr168_qopt1",
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_vs2_paper_intent_candidates.py"),
            "--repo-root",
            ".",
            "--out-dir",
            "docs/master_plan/generated/pr168_vs2",
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_vs2_paper_intent_candidates.py"),
            "--repo-root",
            ".",
            "--artifact-dir",
            "docs/master_plan/generated/pr168_vs2",
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr168_mem1_condition_scoped_memory.py"),
            "--repo-root",
            ".",
            "--out-dir",
            str(validation_dir / "master_plan_generated" / "pr168_mem1"),
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr168_mem1_condition_scoped_memory.py"),
            "--repo-root",
            ".",
            "--artifact-dir",
            str(validation_dir / "master_plan_generated" / "pr168_mem1"),
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr169_readiness1.py"),
            "--repo-root",
            ".",
            "--out-dir",
            str(validation_dir / "master_plan_generated" / "pr169_readiness1"),
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr169_readiness1.py"),
            "--repo-root",
            ".",
            "--artifact-dir",
            str(validation_dir / "master_plan_generated" / "pr169_readiness1"),
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr169_pretrade1.py"),
            "--repo-root",
            ".",
            "--out-dir",
            str(validation_dir / "master_plan_generated" / "pr169_pretrade1"),
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr169_pretrade1.py"),
            "--repo-root",
            ".",
            "--artifact-dir",
            str(validation_dir / "master_plan_generated" / "pr169_pretrade1"),
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr169_agent_orch1.py"),
            "--repo-root",
            ".",
            "--out-dir",
            str(validation_dir / "master_plan_generated" / "pr169_agent_orch1"),
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr169_agent_orch1.py"),
            "--repo-root",
            ".",
            "--artifact-dir",
            str(validation_dir / "master_plan_generated" / "pr169_agent_orch1"),
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr169_svc1.py"),
            "--repo-root",
            ".",
            "--out-dir",
            str(validation_dir / "master_plan_generated" / "pr169_svc1"),
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr169_svc1.py"),
            "--repo-root",
            ".",
            "--artifact-dir",
            str(validation_dir / "master_plan_generated" / "pr169_svc1"),
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr169_dash1_owner_dashboard.py"),
            "--repo-root",
            ".",
            "--out",
            str(validation_dir / "master_plan_generated" / "pr169_dash1"),
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "build_pr169_dash1_owner_dashboard_ui.py"),
            "--repo-root",
            ".",
            "--base",
            str(validation_dir / "master_plan_generated" / "pr169_dash1"),
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr169_dash1_owner_dashboard.py"),
            "--repo-root",
            ".",
            "--base",
            str(validation_dir / "master_plan_generated" / "pr169_dash1"),
            "--timeout-ms",
            "3600000",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr169_dash1_owner_dashboard_ui.py"),
            "--repo-root",
            ".",
            "--base",
            str(validation_dir / "master_plan_generated" / "pr169_dash1"),
            "--timeout-ms",
            "3600000",
        ],
        *[
            [
                python_executable,
                str(Path("tools") / f"validate_pr168_rank_{name}.py"),
            ]
            for name in (
                "input_consumption",
                "no_fake_ranking",
                "score_math",
                "binary_prediction_market_pnl",
                "candidate_stack_generation",
                "mode_policy_matrix",
                "pretrade_order_simulation",
                "order_decision_tournament",
                "tca_decomposition",
                "champion_challenger",
                "no_trade_dominance",
                "overfit_fdr",
                "regime_ranking",
                "portfolio_ranking",
                "capacity_crowding",
                "quantum_structural_ranking",
                "quantum_combinatorial_selection",
                "latency_hot_path_seed",
                "agent_work_orders",
                "downstream_orchestration",
                "dag_orchestration",
                "no_orphan",
                "authority_boundaries",
                "validation_scope_registry_integration",
                "centralized_systems_coverage",
                "edge_capture_attribution",
                "negative_recovery_tournament",
                "threshold_surfaces",
                "maker_taker_tradeoff",
                "size_price_time_sensitivity",
                "scenario_stress_surface",
                "materialized_artifacts_not_blueprints",
                "scalar_value_no_orphan",
                "terminal_artifact_lifecycle",
                "connector_candidate_routing",
                "two_speed_decision_surface",
                "future_expansion_registries",
                "market_adapter_registry_seed",
                "venue_cost_model_registry_seed",
                "contract_payoff_model_registry_seed",
                "formula_algorithm_plugin_registry_seed",
                "quantum_objective_registry_seed",
                "order_policy_registry_seed",
                "agent_capability_registry_seed",
                "connector_readiness_registry_seed",
                "runtime_allowlist_seed_registry",
                "hot_path_decision_surface_registry",
                "registry_seed_no_orphan",
                "registry_anti_scatter",
            )
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr165_d2_score_refreshed_scenario_selection_v2.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_pr165_d3_quantum_aware_scenario_selection_v3.py"
            ),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_agent_role_operating_charter_registry.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "QTTAgentRoleOperatingCharterReport.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_algorithm_formula_family_registry.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "QTTAlgorithmFormulaFamilyReport.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_agent_algorithm_binding_registry.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "QTTAgentAlgorithmBindingReport.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_agent_algorithm_consumer_gate.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "QTTAgentAlgorithmConsumerGate.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_agent_algorithm_cumulative_readiness_gate.py"),
            "--mode",
            "dev",
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "QTTAgentAlgorithmCumulativeReadinessGate.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_agent_algorithm_command_matrix.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_source_evidence_static.py"),
            "--schema",
            str(Path("schemas") / "source_evidence" / "source_evidence.schema.json"),
            "--owner-packet",
            str(
                Path("docs")
                / "master_plan"
                / "source_evidence"
                / "QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"
            ),
            "--registry-fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "synthetic_acceptance_registry.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_source_evidence_gate_confirmation_static.py"),
            "--repo-root",
            ".",
            "--schema",
            str(
                Path("schemas")
                / "source_evidence"
                / "source_evidence_gate_confirmation.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "synthetic_source_evidence_gate_confirmation_blocked.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_source_evidence_retrieval_executor.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_source_evidence_acceptance.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_accepted_source_to_connector_semantic_binding.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_source_revalidation_scheduler.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_connector_semantic_binding_implementation_gate.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_per_venue_execution_lifecycle_model.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_cross_venue_execution_normalization_binding.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "runtime_cash_component_field_map_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "private_state_read_receipt_gate_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "credential_alias_secret_no_capture_readiness_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "venue_market_data_ingest_adapters_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "orderbook_event_state_snapshot_builder_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "runtime_resolver_snapshot_executor_validate.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_historical_dataset_policy_literal_drift.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_historical_dataset_digest_and_loader.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr136_roadmap_policy_literal_drift.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr136_day1_launch_readiness_roadmap.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr137_generated_integrity_authority_boundary.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr137_launch_readiness_dependency_controller.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_connector_capability_static.py"),
            "--schema",
            str(
                Path("schemas")
                / "connectors"
                / "connector_capability_registry.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "connectors"
                / "synthetic_connector_capability_registry.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_runtime_orchestration_static.py"),
            "--schema",
            str(
                Path("schemas")
                / "runtime_orchestration"
                / "runtime_orchestration_skeleton.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "runtime_orchestration"
                / "synthetic_runtime_orchestration_skeleton.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_replay_paper_execution_graph_static.py"),
            "--schema",
            str(
                Path("schemas")
                / "replay_paper_review"
                / "replay_paper_execution_graph.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "replay_paper_review"
                / "synthetic_replay_paper_execution_graph.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_venue_abstraction_layer_static.py"),
            "--schema",
            str(Path("schemas") / "connectors" / "venue_abstraction_layer.schema.json"),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "connectors"
                / "synthetic_venue_abstraction_layer.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_order_intent_execution_router_static.py"),
            "--schema",
            str(
                Path("schemas")
                / "connectors"
                / "order_intent_execution_router_scaffolding.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "connectors"
                / "synthetic_order_intent_execution_router_scaffolding.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_readiness_static.py"),
            "--repo-root",
            ".",
            "--schema",
            str(Path("schemas") / "atomicrows" / "atomicrows_readiness_audit.schema.json"),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "atomicrows"
                / "synthetic_atomicrows_readiness_blocked.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_unblocking_requirements_static.py"),
            "--repo-root",
            ".",
            "--schema",
            str(
                Path("schemas")
                / "atomicrows"
                / "atomicrows_unblocking_requirements_audit.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "atomicrows"
                / "synthetic_atomicrows_unblocking_requirements_required.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_canonical_row_specification_static.py"
            ),
            "--repo-root",
            ".",
            "--schema",
            str(
                Path("schemas")
                / "atomicrows"
                / "atomicrows_canonical_row_specification_audit.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "atomicrows"
                / "synthetic_atomicrows_canonical_row_specification_required.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_bundle_schema_checker_static.py"),
            "--repo-root",
            ".",
            "--row-schema",
            str(Path("schemas") / "atomicrows" / "atomic_parameter_row.schema.json"),
            "--bundle-schema",
            str(Path("schemas") / "atomicrows" / "atomic_row_bundle.schema.json"),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "atomicrows"
                / "synthetic_atomicrows_bundle_bootstrap_absent.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "build_atomicrows_parameter_lifecycle_report.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_parameter_lifecycle.py"),
            "--mode",
            "dev",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_lifecycle_consumer_gate.py"),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsLifecycleConsumerGate.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_lifecycle_promotion_receipt_gate.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsLifecyclePromotionReceiptGate.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_lifecycle_registry_mutation_guard.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsLifecycleRegistryMutationGuard.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_lifecycle_cumulative_readiness_gate.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsLifecycleCumulativeReadinessGate.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_lifecycle_gate_command_matrix.py"),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsLifecycleGateCommandMatrix.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_agent_binding_registry.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsParameterAgentBindingReport.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_agent_binding_consumer_gate.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsParameterAgentBindingConsumerGate.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_agent_binding_cumulative_readiness_gate.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsParameterAgentBindingCumulativeReadinessGate.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_agent_binding_command_matrix.py"
            ),
            "--mode",
            "dev",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "AtomicRowsParameterAgentBindingCommandMatrix.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_research_provenance_evidence_tier_classification.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_research_source_to_candidate_family_gate.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_parameter_stack_role_taxonomy.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_stack_completeness_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_stack_compatibility_gate.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_edge_parameter_stack_selection_packet.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_trade_context_packet.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_selection_universe_registry.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_parameter_selection_universe_consumer_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_trade_context_selection_universe_routing_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_quantum_applicability_classification_registry.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_owner_quantum_priority_policy_registry.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_parameter_algorithm_scoring_policy_registry.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_parameter_stack_scoring_and_ranking_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_quantum_classical_optimizer_arbitration_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_candidate_parameter_stack_generation_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_trade_context_parameter_stack_selection_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_selected_parameter_stack_handoff_packet.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_replay_paper_candidate_stack_competition_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_dual_result_review_for_parameter_stacks.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_owner_live_promotion_review_for_parameter_stacks.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_owner_approval_request_queue_registry.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_owner_override_receipt_authoring_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_owner_dashboard_approval_menu_schema.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_owner_dashboard_approval_static_screen_contract.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_full_bundle_row_expansion_plan.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_bundle_row_family_source_files.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_bundle_builder_deterministic_assembly_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_sha_system_dormancy_state_contract.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_qtt_final_readiness_dependency_policy_contract.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_qtt_active_non_sha_day1_gate_state_registry_contract.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_pr_identity_roster.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_qtt_roadmap_execution_state_controller.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_bundle_sha_freeze_authority_gate.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_exact_row_authority_classifier_bridge.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_exact_row_expansion_manifest.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_owner_approved_exact_15_family_count_distribution.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_exact_row_generator_dry_run_manifest.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_exact_row_source_materialization_manifest.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_exact_row_agent_family_eligibility_matrix.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_bundle_materialization_manifest.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_atomicrows_bundle_boundary_state_contract.py"),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_atomicrows_sha_freeze_final_readiness_state_contract.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_generated_derivative_bootstrap_gate_static.py"),
            "--repo-root",
            ".",
            "--schema",
            str(
                Path("schemas")
                / "master_plan"
                / "generated_derivative_bootstrap_gate.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "master_plan"
                / "synthetic_generated_derivative_bootstrap_gate.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_stage1_packet_schema_gate_static.py"),
            "--repo-root",
            ".",
            "--schema-dir",
            str(Path("schemas") / "stage1_prediction_markets"),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "stage1_prediction_markets"
                / "synthetic_stage1_packet_schema_gate_blocked.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_venue_neutral_prediction_adapter_gate_static.py"
            ),
            "--repo-root",
            ".",
            "--schema-dir",
            str(Path("schemas") / "venue_neutral_prediction_adapter"),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "venue_neutral_prediction_adapter"
                / "synthetic_venue_neutral_prediction_adapter_gate_blocked.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_connector_scaffold_source_required_gate_static.py"
            ),
            "--repo-root",
            ".",
            "--schema",
            str(
                Path("schemas")
                / "connectors"
                / "connector_scaffold_source_required_gate.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "connectors"
                / "synthetic_connector_scaffold_source_required_blocked.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_stage1_runtime_scaffold_gate_static.py"),
            "--repo-root",
            ".",
            "--schema",
            str(
                Path("schemas")
                / "runtime_orchestration"
                / "stage1_runtime_scaffold_gate.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "runtime_orchestration"
                / "synthetic_stage1_runtime_scaffold_gate_blocked.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_source_fact_binding_connector_semantic_readiness_static.py"
            ),
            "--repo-root",
            ".",
            "--source-to-connector-schema",
            str(
                Path("schemas")
                / "source_fact_binding_readiness"
                / "stage1_source_to_connector_field_binding_matrix.schema.json"
            ),
            "--source-to-connector-fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_fact_binding_readiness"
                / "synthetic_stage1_source_to_connector_field_binding_matrix.v1.fixture.json"
            ),
            "--connector-target-schema",
            str(
                Path("schemas")
                / "source_fact_binding_readiness"
                / "stage1_connector_semantic_target_field_matrix.schema.json"
            ),
            "--connector-target-fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_fact_binding_readiness"
                / "synthetic_stage1_connector_semantic_target_field_matrix.v1.fixture.json"
            ),
            "--gate-report-schema",
            str(
                Path("schemas")
                / "source_fact_binding_readiness"
                / "stage1_connector_semantic_readiness_gate_report.schema.json"
            ),
            "--gate-report-fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_fact_binding_readiness"
                / "synthetic_stage1_connector_semantic_readiness_gate_report.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "source_evidence_acceptance_consumer_contract_check.py"),
            "--repo-root",
            ".",
            "--consumer-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "source_evidence"
                / "acceptance"
                / "accepted_source_evidence_consumer_contract.schema.json"
            ),
            "--target-field-ledger-schema",
            str(
                Path("src")
                / "qtt"
                / "source_evidence"
                / "acceptance"
                / "stage1_target_field_acceptance_ledger_record.schema.json"
            ),
            "--export-record-schema",
            str(
                Path("src")
                / "qtt"
                / "source_evidence"
                / "acceptance"
                / "stage1_accepted_source_evidence_export_record.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "acceptance_consumer_contract"
                / "synthetic_accepted_source_evidence_consumer_contract_records.v1.fixture.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "stage1_connector_semantic_binding_ledger_check.py"),
            "--repo-root",
            ".",
            "--ledger-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "connector_semantic_binding"
                / "stage1_connector_semantic_binding_ledger_record.schema.json"
            ),
            "--canonicalization-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "connector_semantic_binding"
                / "stage1_connector_semantic_value_canonicalization.schema.json"
            ),
            "--consumer-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "connector_semantic_binding"
                / "stage1_connector_semantic_binding_consumer_contract.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "connector_semantic_binding"
                / "synthetic_stage1_connector_semantic_binding_contracts.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1ConnectorSemanticBindingLedgerCheck.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "stage1_runtime_resolver_snapshot_contract_check.py"),
            "--repo-root",
            ".",
            "--input-lock-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver"
                / "stage1_runtime_resolver_snapshot_input_lock.schema.json"
            ),
            "--manifest-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver"
                / "stage1_runtime_resolver_snapshot_manifest.schema.json"
            ),
            "--consumer-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver"
                / "stage1_runtime_resolver_consumer_contract.schema.json"
            ),
            "--gate-report-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver"
                / "stage1_runtime_resolver_snapshot_gate_report.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "runtime_resolver"
                / "synthetic_stage1_runtime_resolver_snapshot_contracts.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1RuntimeResolverSnapshotContractCheck.report.json"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "stage1_runtime_resolver_to_replay_paper_handoff_check.py"
            ),
            "--repo-root",
            ".",
            "--consumer-allowlist-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver_snapshot"
                / "stage1_runtime_resolver_snapshot_consumer_allowlist.schema.json"
            ),
            "--handoff-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver_snapshot"
                / "stage1_runtime_resolver_to_replay_paper_handoff_contract.schema.json"
            ),
            "--handoff-report-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "runtime_resolver_snapshot"
                / "stage1_runtime_resolver_to_replay_paper_handoff_report.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "runtime_resolver_snapshot"
                / "synthetic_stage1_runtime_resolver_to_replay_paper_handoff.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1RuntimeResolverToReplayPaperHandoff.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "stage1_concurrent_replay_paper_contract_check.py"),
            "--repo-root",
            ".",
            "--input-identity-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "replay_paper"
                / "concurrent_replay_paper_input_identity.schema.json"
            ),
            "--replay-lane-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "replay_paper"
                / "concurrent_replay_lane_contract.schema.json"
            ),
            "--paper-lane-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "replay_paper"
                / "concurrent_paper_lane_contract.schema.json"
            ),
            "--replay-result-boundary-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "replay_paper"
                / "replay_result_packet_boundary.schema.json"
            ),
            "--paper-result-boundary-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "replay_paper"
                / "paper_result_packet_boundary.schema.json"
            ),
            "--gate-report-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "replay_paper"
                / "concurrent_replay_paper_execution_gate_report.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "replay_paper"
                / "synthetic_concurrent_replay_paper_contracts.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1ConcurrentReplayPaperContractCheck.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "stage1_dual_result_review_contract_check.py"),
            "--repo-root",
            ".",
            "--input-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "dual_result_review"
                / "stage1_dual_result_review_input_contract.schema.json"
            ),
            "--comparison-matrix-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "dual_result_review"
                / "stage1_replay_paper_comparison_matrix.schema.json"
            ),
            "--gate-report-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "dual_result_review"
                / "stage1_dual_result_review_gate_report.schema.json"
            ),
            "--owner-handoff-block-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "dual_result_review"
                / "stage1_owner_live_promotion_handoff_block.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "dual_result_review"
                / "synthetic_stage1_dual_result_review_contracts.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1DualResultReviewContractCheck.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "stage1_owner_live_promotion_review_contract_check.py"),
            "--repo-root",
            ".",
            "--input-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "owner_live_promotion_review"
                / "stage1_owner_live_promotion_review_input_contract.schema.json"
            ),
            "--owner-approval-receipt-boundary-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "owner_live_promotion_review"
                / "stage1_owner_approval_receipt_boundary.schema.json"
            ),
            "--gate-report-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "owner_live_promotion_review"
                / "stage1_owner_live_promotion_review_gate_report.schema.json"
            ),
            "--handoff-block-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "owner_live_promotion_review"
                / "stage1_three_venue_canary_eligibility_handoff_block.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "owner_live_promotion_review"
                / "synthetic_stage1_owner_live_promotion_review_contracts.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1OwnerLivePromotionReviewContractCheck.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "stage1_three_venue_canary_eligibility_contract_check.py"),
            "--repo-root",
            ".",
            "--input-contract-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "three_venue_canary_eligibility"
                / "stage1_three_venue_canary_eligibility_input_contract.schema.json"
            ),
            "--readiness-matrix-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "three_venue_canary_eligibility"
                / "stage1_three_venue_platform_readiness_matrix.schema.json"
            ),
            "--handoff-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "three_venue_canary_eligibility"
                / "stage1_owner_review_to_canary_eligibility_handoff.schema.json"
            ),
            "--gate-report-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "three_venue_canary_eligibility"
                / "stage1_three_venue_canary_eligibility_gate_report.schema.json"
            ),
            "--execution-block-schema",
            str(
                Path("src")
                / "qtt"
                / "stage1_prediction_markets"
                / "three_venue_canary_eligibility"
                / "stage1_limited_live_canary_execution_block.schema.json"
            ),
            "--fixture",
            str(
                Path("tests")
                / "fixtures"
                / "source_evidence"
                / "three_venue_canary_eligibility"
                / "synthetic_stage1_three_venue_canary_eligibility_contracts.v1.fixture.json"
            ),
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "Stage1ThreeVenueCanaryEligibilityContractCheck.report.json"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "build_master_plan_section_coverage_report.py"),
        ],
        [
            python_executable,
            str(Path("tools") / "validate_master_plan_section_coverage.py"),
            "--mode",
            "dev",
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_qtt_master_plan_section_coverage_triage_routes.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_qtt_master_plan_section_roadmap_crosswalk.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "validate_qtt_master_plan_section_coverage_command_matrix.py"
            ),
        ],
        [
            python_executable,
            str(Path("tools") / "qtt_test_gate.py"),
            "--phase",
            "first-coding-runbook",
            "--repo-root",
            ".",
            "--strict-no-claim",
            "--out",
            str(Path("docs") / "master_plan" / "generated" / "QTTTestGate.report.json"),
        ],
        [
            python_executable,
            str(Path("tools") / "local_gate_command_matrix.py"),
            "--repo-root",
            ".",
            "--out",
            str(Path("docs") / "master_plan" / "generated" / "LocalGateCommandMatrix.json"),
        ],
        [
            python_executable,
            str(Path("tools") / "pr_handoff_check.py"),
            "--repo-root",
            ".",
            "--out",
            str(
                Path("docs")
                / "master_plan"
                / "generated"
                / "FirstCodingPRHandoff.packet.json"
            ),
        ],
        *[
            [
                python_executable,
                str(
                    Path("tools")
                    / "validate_qku_computation_control_plane.py"
                ),
                "--domain",
                domain,
            ]
            for domain in (
                "architecture",
                "quantum",
                "latency",
                "d",
                "agent",
                "model_risk",
                "g",
                "h",
            )
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "independent_validate_qku_computation_control_plane.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "independent_validate_qku_computation_control_plane_latency.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "independent_validate_qku_computation_control_plane_model_risk.py"
            ),
        ],
        [
            python_executable,
            str(
                Path("tools")
                / "independent_validate_qku_computation_control_plane_g.py"
            ),
        ],
        *[
            [python_executable, str(Path("tools") / script_name)]
            for script_name in (
                "independent_validate_qku_computation_control_plane_agent.py",
                "independent_validate_qku_computation_control_plane_d.py",
                "independent_validate_qku_computation_control_plane_quantum.py",
                "independent_validate_qku_computation_control_plane_architecture.py",
            )
        ],
        *[
            list(command)
            for command in runner.build_st12h_validation_commands(python_executable)
        ],
        [
            python_executable,
            str(Path("tools") / "validate_pr169_val1.py"),
            "--repo-root",
            ".",
        ],
        [
            python_executable,
            str(Path("tools") / "validate_no_runtime_artifacts.py"),
            "--repo-root",
            ".",
            "--forbid-source-retrieval",
            "--forbid-source-acceptance",
            "--forbid-connector-binding",
            "--forbid-private-state-fetch",
            "--forbid-order-execution",
            "--forbid-neural-training",
            "--forbid-neural-inference",
            "--forbid-external-repo-clone",
            "--forbid-package-install-scripts",
        ],
        [
            python_executable,
            str(Path("tools") / "run_pytest_fresh_basetemp.py"),
            str(
                Path("tests")
                / "source_evidence"
                / "test_controlled_official_source_capture_candidate_packets.py"
            ),
            "-q",
            runner.PYTEST_DURATIONS_ARG,
            "--basetemp",
            str(pytest_basetemp),
        ],
        [
            python_executable,
            str(Path("tools") / "run_pytest_fresh_basetemp.py"),
            "tests",
            "-q",
            "--ignore",
            str(
                Path("tests")
                / "source_evidence"
                / "test_controlled_official_source_capture_candidate_packets.py"
            ),
            runner.PYTEST_DURATIONS_ARG,
            "--basetemp",
            str(pytest_basetemp),
        ],
    ]
    return [
        runner._route_command_generated_outputs_to_temp(command, validation_dir)
        for command in commands
    ]


def _pytest_basetemp_from_commands(commands: list[list[str]]) -> Path:
    pytest_command = next(
        command for command in reversed(commands) if "--basetemp" in command
    )
    return Path(pytest_command[pytest_command.index("--basetemp") + 1])


def _validation_dir_from_commands(commands: list[list[str]]) -> Path:
    ingest_command = next(
        command
        for command in commands
        if len(command) > 1 and Path(command[1]).name == "master_plan_ingest.py"
    )
    return Path(ingest_command[ingest_command.index("--section-manifest-out") + 1]).parent


def test_runner_builds_expected_command_sequence(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    assert runner.build_validation_commands() == _expected_commands(python_executable)


def test_runner_registers_qku_primary_and_independent_systems():
    commands = runner.build_deterministic_validator_commands()
    qku_commands = [
        command
        for command in commands
        if any(
            "qku_computation_control_plane" in part and part.endswith(".py")
            for part in command
        )
    ]
    assert [command[-1] for command in qku_commands[:8]] == [
        "architecture",
        "quantum",
        "latency",
        "d",
        "agent",
        "model_risk",
        "g",
        "h",
    ]
    assert [Path(command[1]).name for command in qku_commands[8:16]] == [
        "independent_validate_qku_computation_control_plane.py",
        "independent_validate_qku_computation_control_plane_latency.py",
        "independent_validate_qku_computation_control_plane_model_risk.py",
        "independent_validate_qku_computation_control_plane_g.py",
        "independent_validate_qku_computation_control_plane_agent.py",
        "independent_validate_qku_computation_control_plane_d.py",
        "independent_validate_qku_computation_control_plane_quantum.py",
        "independent_validate_qku_computation_control_plane_architecture.py",
    ]
    assert tuple(tuple(command) for command in qku_commands[16:]) == tuple(
        runner.build_st12h_validation_commands(sys.executable)
    )


def test_runner_phase_manifest_covers_full_validation_plan(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)
    validation_dir = Path("validation-dir")
    pytest_basetemp = Path("pytest-basetemp")

    manifest = runner.build_phase_manifest(validation_dir, pytest_basetemp)
    manifest_commands = [
        command
        for phase_record in manifest
        for command in phase_record["commands"]
    ]

    assert [record["phase"] for record in manifest] == list(runner.ORDERED_PHASES)
    assert manifest_commands == runner.build_phase_commands(
        runner.ALL_PHASE,
        validation_dir,
        pytest_basetemp,
    )


    # Independent registered-vector evidence transcribed from unchanged R5
    # reference/ORDERED_COMMAND_PLAN_SOURCE.json, never from projector output.
    # REVIEW_PYTHON and /owned are synthetic operands, not execution grants.
    import ast
    from pathlib import PurePosixPath
    from types import SimpleNamespace
    expected_ordered = (
        ('fast-preflight', ('REVIEW_PYTHON', 'tools/validate_grand_global_debug_logical_consistency_audit.py', '--repo-root', '.')),
        ('fast-preflight', ('REVIEW_PYTHON', 'tools/validate_ci_branch_context_matrix.py', '--repo-root', '.')),
        ('fast-preflight', ('REVIEW_PYTHON', 'tools/validate_repair_pr_changed_file_scope.py', '--repo-root', '.')),
        ('fast-preflight', ('REVIEW_PYTHON', 'tools/validate_nested_validator_contracts.py', '--repo-root', '.')),
        ('fast-preflight', ('REVIEW_PYTHON', 'tools/validate_validation_inventory.py', '--repo-root', '.')),
        ('fast-preflight', ('REVIEW_PYTHON', 'tools/validate_validation_scope_registry.py')),
        ('fast-preflight', ('REVIEW_PYTHON', 'tools/changed_area_validation_router.py', '--repo-root', '.')),
        ('fast-preflight', ('REVIEW_PYTHON', 'tools/cross_platform_path_invariant.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/master_plan_ingest.py', '--input', 'docs/master_plan/QTT_MasterPlan_Current.md', '--section-manifest-out', '/owned/v/SectionManifest.json', '--traceability-out', '/owned/v/TraceabilityReport.json', '--scope-report-out', '/owned/v/FirstPrScopeReport.json')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/master_plan_traceability_check.py', '--master-plan', 'docs/master_plan/QTT_MasterPlan_Current.md', '--section-manifest', '/owned/v/SectionManifest.json', '--traceability-report', '/owned/v/TraceabilityReport.json')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_first_pr_scope.py', '--repo-root', '.', '--scope-report', '/owned/v/FirstPrScopeReport.json', '--block-runtime', '--block-live', '--block-sha', '--block-companion-package', '--block-profit-claims', '--block-source-retrieval', '--block-source-acceptance', '--block-connector-binding', '--block-private-state-fetch', '--block-order-execution', '--block-neural-training', '--block-neural-inference', '--block-external-repo-clone', '--block-package-install-scripts')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', '-c', "from pathlib import Path\nfrom src.qtt.stage1_prediction_markets.atomicrows_semantic_contract.report import build_report\nfrom src.qtt.stage1_prediction_markets.atomicrows_semantic_contract.validator import validate_report_payload, validate_repository_artifacts\nroot = Path('.').resolve()\nreport = build_report(root)\nfailures = list(validate_repository_artifacts(root))\noutcome = validate_report_payload(\n    report,\n    repo_root=root,\n    enforce_environment=True,\n    enforce_protected_diff=True,\n)\nfailures.extend(outcome.failures)\nunique_failures = tuple(sorted(set(failures)))\nif unique_failures:\n    print('\\n'.join(unique_failures))\n    raise SystemExit(1)\nfor receipt in outcome.receipts:\n    print(receipt)\n")),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_atomicrows_row_family_source_manifest_currentization.py', '--repo-root', '.', '--out', '/owned/v/AtomicRowsRowFamilySourceManifestCurrentization.report.json')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_atomicrows_semantic_field_coverage_enrichment_plan.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_idempotence_runtime_containment.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_atomicrows_semantic_value_materialization_owner_authorization_gate.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_qtt_owner_global_override_authority.py', '--mode', 'dev', '--repo-root', '.', '--out', '/owned/v/master_plan_generated/QTTOwnerGlobalOverrideAuthority.report.json')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_atomicrows_semantic_value_materialization_implementation_bridge.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_source_backed_classical_quantum_parameter_default_target_matrix.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_official_source_retrieval_target_pack_parameter_defaults.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_controlled_official_source_capture_candidate_packets.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr153r_redo_external_source_value_capture_targets.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr153s_source_value_capture_closure_classifier.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_atomicrows_parameter_default_value_materialization_gate.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_agent_consumable_parameter_default_registry.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_agent_default_binding_universal_intake_gate.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr157_pr154_atomicrows_completion_materialization_bridge.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr158_owner_response_selection_readiness_bridge.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr159_official_source_completion_bridge.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr160_split_reclassification_route_closure.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr159r_source_locator_value_capture.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr159s_open_intake_completion.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr161a_atomicrows_pr154_value_state_materialization.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr161b_master_plan_residual_candidate_coverage.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr161c_qku_residual_candidate_assimilation.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr161d_qku_candidate_quality_replay_paper_prioritization.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr161e_replay_paper_outcome_capture_scenario_learning.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr161f_replay_paper_executor_input_run_artifact_generation.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr162b_qku_formula_algorithm_solver_market_scope_materialization.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr162d_aggressive_qku_candidate_materialization_agent_routing.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr162r_a_replay_paper_executability_classification_audit.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr162d_r2a_real_formulations.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr162r_generic_replay_paper_adapter_rerun.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr162r_b_replay_paper_data_binding_completion.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr163_generic_paper_adapter_capture_framework.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr163_b_paired_replay_paper_concurrent_executor.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr164_review_provenance_qku_canonical_coverage_audit.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr163_c_pretrade_infrastructure_rejection_remediation.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr165_evidence_backed_scoring_ranking.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr165_b_condition_scoped_negative_memory.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr165_c_replay_paper_memory_consumer_integration.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr165_d_scenario_qku_combination_selection.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr166_s_replay_paper_scenario_retest_execution.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr166_sm_score_memory_refresh_from_pr166_s_results.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr166_sf_repair_materialization_before_retest.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr166_s2_replay_paper_retest_loop_v2.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr166_sm2_score_memory_refresh_v2.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr166_sf_r2_targeted_conversion_repair_retest.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr166_sm3_score_memory_refresh_v3.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr166_q_quantum_classical_hybrid_comparator.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr166_qb_bounded_quantum_benchmark.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr166_qc_quantum_selected_replay_paper_retest.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr162e_q_quantum_automapper.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr167_open_trade_simulator_integration.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr162e_plugin_framework.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr162e_negative_repair_factory.py', '--repo-root', '.')),
        ('deterministic-validators-a', ('REVIEW_PYTHON', 'tools/validate_pr162e_no_orphan_lineage.py', '--repo-root', '.')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/build_pr168_gfp_global_formula_discovery_real_computation.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp_baseline_count_reconcile.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp_no_fake_positive_negative_labels.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp_formula_assignment_coverage.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp_real_formula_computation.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp_formula_registry_integrity.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp_atomicrows_computation_coverage.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp_qku_computation_coverage.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp_candidate_packet_v1_coverage.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp_quantum_objective_coefficients.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp_metadata_placeholder_demotions.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp_truth_overlay_required.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp_report_compactness.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp_formula_source_arbitration.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp_master_plan_formula_catalog_diff.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp_minimum_tradability_formula_set.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp_forbidden_bundle_terminology.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp_no_orphan_lineage.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp_authority_boundaries.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/build_pr168_rp_formula_based_replay_paper_recompute.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_qtt_authority_reason_code_registry.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_formula_execution.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_replay_paper_results.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_no_fake_computed_labels.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_tca_pnl_math.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_microstructure_fill_model.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_pretrade_simulation_kernel.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_order_policy_candidate_ranking.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_no_trade_candidate.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_scenario_ladder.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_latency_budget.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_live_candidate_handoff_no_order_authority.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_probability_calibration.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_overfit_fdr.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_quantum_objective_recompute.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_quantum_structural_readiness.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_portfolio_marginal_utility.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_capacity_crowding.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_regime_memory.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_champion_challenger.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_combination_selection.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_negative_recovery.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_edge_attribution.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_agent_duty_orchestration.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_connector_candidate_routing.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_strict_input_consumption.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_no_orphan_lineage.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_artifact_information_value_dag.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_authority_boundaries.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_report_compactness.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_validation_scope_registry_integration.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_windows_linux_compatibility.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_no_metadata_only_pass.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_no_forced_negative_to_positive.py')),
        ('deterministic-validators-b', ('REVIEW_PYTHON', 'tools/validate_pr168_rp_no_scattered_authority_wording.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr168_rank_evidence_backed_ranking.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_data1_public_market_data_snapshots.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_data1a_focused_audit.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_gfp2r_data1a_gated_candidate_recompute.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr168_rp2_map2.py', '--offline')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rp2_map2.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr168_map3.py', '--offline')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_map3.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr168_rp3.py', '--offline')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rp3.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr168_rank3.py', '--offline')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank3.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr168_rp5a_legacy_semantic_audit.py', '--offline')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rp5a_legacy_semantic_audit.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr168_rp5b_active_registry_safe_cleanup.py', '--dry-run', '--offline')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rp5b_active_registry_safe_cleanup.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr168_rp5c_immutable_qku_formula_library.py', '--offline')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rp5c_immutable_qku_formula_library.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/run_pr168_vs1_trading_intelligence_slice.py', '--fixture', 'all', '--top-k', '10', '--max-identities', '50', '--max-stacks-per-fixture', '20', '--dump-temp')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_vs1_trading_intelligence_slice.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr168_rp5d_replay_paper_executability_tiers.py', '--offline')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rp5d_replay_paper_executability_tiers.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr168_rp5e_stack_gen.py', '--offline', '--fixture', 'sample', '--max-stacks', '1000', '--dump-temp')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rp5e_stack_gen.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr168_rp5d_r1_exec_now_unlock.py', '--offline', '--fixture', 'sample', '--target-min', '5', '--target-max', '15')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rp5d_r1_exec_now_unlock.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr168_rp5f_dynamic_targets.py', '--offline', '--fixture', 'sample', '--max-targets', '25', '--max-seeds', '500', '--dump-temp')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rp5f_dynamic_targets.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr168_rp5g_trade_plan_sim.py', '--offline', '--fixture', 'sample', '--max-candidates', '10', '--out', '/owned/v/master_plan_generated/pr168_rp5g', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rp5g_trade_plan_sim.py', '--generated', '/owned/v/master_plan_generated/pr168_rp5g', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr168_rank4_advisory_ranking.py', '--repo-root', '.', '--out-dir', '/owned/v/master_plan_generated/pr168_rank4', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank4_advisory_ranking.py', '--repo-root', '.', '--artifact-dir', '/owned/v/master_plan_generated/pr168_rank4', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr168_qopt1_batch_optimization.py', '--repo-root', '.', '--out-dir', '/owned/v/master_plan_generated/pr168_qopt1', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_qopt1_batch_optimization.py', '--repo-root', '.', '--artifact-dir', '/owned/v/master_plan_generated/pr168_qopt1', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr168_vs2_paper_intent_candidates.py', '--repo-root', '.', '--out-dir', '/owned/v/master_plan_generated/pr168_vs2', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_vs2_paper_intent_candidates.py', '--repo-root', '.', '--artifact-dir', '/owned/v/master_plan_generated/pr168_vs2', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr168_mem1_condition_scoped_memory.py', '--repo-root', '.', '--out-dir', '/owned/v/master_plan_generated/pr168_mem1', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_mem1_condition_scoped_memory.py', '--repo-root', '.', '--artifact-dir', '/owned/v/master_plan_generated/pr168_mem1', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr169_readiness1.py', '--repo-root', '.', '--out-dir', '/owned/v/master_plan_generated/pr169_readiness1', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr169_readiness1.py', '--repo-root', '.', '--artifact-dir', '/owned/v/master_plan_generated/pr169_readiness1', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr169_pretrade1.py', '--repo-root', '.', '--out-dir', '/owned/v/master_plan_generated/pr169_pretrade1', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr169_pretrade1.py', '--repo-root', '.', '--artifact-dir', '/owned/v/master_plan_generated/pr169_pretrade1', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr169_agent_orch1.py', '--repo-root', '.', '--out-dir', '/owned/v/master_plan_generated/pr169_agent_orch1', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr169_agent_orch1.py', '--repo-root', '.', '--artifact-dir', '/owned/v/master_plan_generated/pr169_agent_orch1', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr169_svc1.py', '--repo-root', '.', '--out-dir', '/owned/v/master_plan_generated/pr169_svc1', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr169_svc1.py', '--repo-root', '.', '--artifact-dir', '/owned/v/master_plan_generated/pr169_svc1', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr169_dash1_owner_dashboard.py', '--repo-root', '.', '--out', '/owned/v/master_plan_generated/pr169_dash1', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_pr169_dash1_owner_dashboard_ui.py', '--repo-root', '.', '--base', '/owned/v/master_plan_generated/pr169_dash1', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr169_dash1_owner_dashboard.py', '--repo-root', '.', '--base', '/owned/v/master_plan_generated/pr169_dash1', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr169_dash1_owner_dashboard_ui.py', '--repo-root', '.', '--base', '/owned/v/master_plan_generated/pr169_dash1', '--timeout-ms', '3600000')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_input_consumption.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_no_fake_ranking.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_score_math.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_binary_prediction_market_pnl.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_candidate_stack_generation.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_mode_policy_matrix.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_pretrade_order_simulation.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_order_decision_tournament.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_tca_decomposition.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_champion_challenger.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_no_trade_dominance.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_overfit_fdr.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_regime_ranking.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_portfolio_ranking.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_capacity_crowding.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_quantum_structural_ranking.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_quantum_combinatorial_selection.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_latency_hot_path_seed.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_agent_work_orders.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_downstream_orchestration.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_dag_orchestration.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_no_orphan.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_authority_boundaries.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_validation_scope_registry_integration.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_centralized_systems_coverage.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_edge_capture_attribution.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_negative_recovery_tournament.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_threshold_surfaces.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_maker_taker_tradeoff.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_size_price_time_sensitivity.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_scenario_stress_surface.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_materialized_artifacts_not_blueprints.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_scalar_value_no_orphan.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_terminal_artifact_lifecycle.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_connector_candidate_routing.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_two_speed_decision_surface.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_future_expansion_registries.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_market_adapter_registry_seed.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_venue_cost_model_registry_seed.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_contract_payoff_model_registry_seed.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_formula_algorithm_plugin_registry_seed.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_quantum_objective_registry_seed.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_order_policy_registry_seed.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_agent_capability_registry_seed.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_connector_readiness_registry_seed.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_runtime_allowlist_seed_registry.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_hot_path_decision_surface_registry.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_registry_seed_no_orphan.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr168_rank_registry_anti_scatter.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr165_d2_score_refreshed_scenario_selection_v2.py', '--repo-root', '.')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr165_d3_quantum_aware_scenario_selection_v3.py', '--repo-root', '.')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qtt_agent_role_operating_charter_registry.py', '--mode', 'dev', '--repo-root', '.', '--out', '/owned/v/master_plan_generated/QTTAgentRoleOperatingCharterReport.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qtt_algorithm_formula_family_registry.py', '--mode', 'dev', '--repo-root', '.', '--out', '/owned/v/master_plan_generated/QTTAlgorithmFormulaFamilyReport.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qtt_agent_algorithm_binding_registry.py', '--mode', 'dev', '--repo-root', '.', '--out', '/owned/v/master_plan_generated/QTTAgentAlgorithmBindingReport.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qtt_agent_algorithm_consumer_gate.py', '--mode', 'dev', '--repo-root', '.', '--out', '/owned/v/master_plan_generated/QTTAgentAlgorithmConsumerGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qtt_agent_algorithm_cumulative_readiness_gate.py', '--mode', 'dev', '--repo-root', '.', '--out', '/owned/v/master_plan_generated/QTTAgentAlgorithmCumulativeReadinessGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qtt_agent_algorithm_command_matrix.py', '--out', '/owned/v/master_plan_generated/QTTAgentAlgorithmCommandMatrix.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_source_evidence_static.py', '--schema', 'schemas/source_evidence/source_evidence.schema.json', '--owner-packet', 'docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md', '--registry-fixture', 'tests/fixtures/source_evidence/synthetic_acceptance_registry.v1.fixture.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_source_evidence_gate_confirmation_static.py', '--repo-root', '.', '--schema', 'schemas/source_evidence/source_evidence_gate_confirmation.schema.json', '--fixture', 'tests/fixtures/source_evidence/synthetic_source_evidence_gate_confirmation_blocked.v1.fixture.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_source_evidence_retrieval_executor.py', '--repo-root', '.', '--check-only')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_source_evidence_acceptance.py', '--repo-root', '.', '--check-only')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_accepted_source_to_connector_semantic_binding.py', '--repo-root', '.', '--out', '/owned/v/master_plan_generated/CODEX_PR124_ACCEPTED_SOURCE_TO_CONNECTOR_SEMANTIC_BINDING_CONSUMER_GATE_REPORT.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_source_revalidation_scheduler.py', '--repo-root', '.', '--check-only', '--out', '/owned/v/master_plan_generated/CODEX_PR125_SOURCE_REVALIDATION_SUPERSESSION_MATERIALITY_SCHEDULER_REPORT.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_connector_semantic_binding_implementation_gate.py', '--repo-root', '.', '--check-only')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_per_venue_execution_lifecycle_model.py', '--repo-root', '.', '--check-only')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_cross_venue_execution_normalization_binding.py', '--repo-root', '.', '--check-only')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/runtime_cash_component_field_map_validate.py', '--repo-root', '.', '--check-only')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/private_state_read_receipt_gate_validate.py', '--repo-root', '.', '--check-only')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/credential_alias_secret_no_capture_readiness_validate.py', '--repo-root', '.', '--check-only')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/venue_market_data_ingest_adapters_validate.py', '--repo-root', '.', '--check-only')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/orderbook_event_state_snapshot_builder_validate.py', '--repo-root', '.', '--check-only')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/runtime_resolver_snapshot_executor_validate.py', '--repo-root', '.', '--check-only')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_historical_dataset_policy_literal_drift.py', '--repo-root', '.')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_historical_dataset_digest_and_loader.py', '--repo-root', '.')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr136_roadmap_policy_literal_drift.py', '--repo-root', '.')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr136_day1_launch_readiness_roadmap.py', '--repo-root', '.')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr137_generated_integrity_authority_boundary.py', '--repo-root', '.')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr137_launch_readiness_dependency_controller.py', '--repo-root', '.')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_connector_capability_static.py', '--schema', 'schemas/connectors/connector_capability_registry.schema.json', '--fixture', 'tests/fixtures/connectors/synthetic_connector_capability_registry.v1.fixture.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_runtime_orchestration_static.py', '--schema', 'schemas/runtime_orchestration/runtime_orchestration_skeleton.schema.json', '--fixture', 'tests/fixtures/runtime_orchestration/synthetic_runtime_orchestration_skeleton.v1.fixture.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_replay_paper_execution_graph_static.py', '--schema', 'schemas/replay_paper_review/replay_paper_execution_graph.schema.json', '--fixture', 'tests/fixtures/replay_paper_review/synthetic_replay_paper_execution_graph.v1.fixture.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_venue_abstraction_layer_static.py', '--schema', 'schemas/connectors/venue_abstraction_layer.schema.json', '--fixture', 'tests/fixtures/connectors/synthetic_venue_abstraction_layer.v1.fixture.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_order_intent_execution_router_static.py', '--schema', 'schemas/connectors/order_intent_execution_router_scaffolding.schema.json', '--fixture', 'tests/fixtures/connectors/synthetic_order_intent_execution_router_scaffolding.v1.fixture.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_readiness_static.py', '--repo-root', '.', '--schema', 'schemas/atomicrows/atomicrows_readiness_audit.schema.json', '--fixture', 'tests/fixtures/atomicrows/synthetic_atomicrows_readiness_blocked.v1.fixture.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_unblocking_requirements_static.py', '--repo-root', '.', '--schema', 'schemas/atomicrows/atomicrows_unblocking_requirements_audit.schema.json', '--fixture', 'tests/fixtures/atomicrows/synthetic_atomicrows_unblocking_requirements_required.v1.fixture.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_canonical_row_specification_static.py', '--repo-root', '.', '--schema', 'schemas/atomicrows/atomicrows_canonical_row_specification_audit.schema.json', '--fixture', 'tests/fixtures/atomicrows/synthetic_atomicrows_canonical_row_specification_required.v1.fixture.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_bundle_schema_checker_static.py', '--repo-root', '.', '--row-schema', 'schemas/atomicrows/atomic_parameter_row.schema.json', '--bundle-schema', 'schemas/atomicrows/atomic_row_bundle.schema.json', '--fixture', 'tests/fixtures/atomicrows/synthetic_atomicrows_bundle_bootstrap_absent.v1.fixture.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_atomicrows_parameter_lifecycle_report.py', '--out', '/owned/v/master_plan_generated/AtomicRowsParameterLifecycleReport.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_parameter_lifecycle.py', '--mode', 'dev')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_lifecycle_consumer_gate.py', '--mode', 'dev', '--out', '/owned/v/master_plan_generated/AtomicRowsLifecycleConsumerGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_lifecycle_promotion_receipt_gate.py', '--mode', 'dev', '--out', '/owned/v/master_plan_generated/AtomicRowsLifecyclePromotionReceiptGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_lifecycle_registry_mutation_guard.py', '--mode', 'dev', '--out', '/owned/v/master_plan_generated/AtomicRowsLifecycleRegistryMutationGuard.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_lifecycle_cumulative_readiness_gate.py', '--mode', 'dev', '--out', '/owned/v/master_plan_generated/AtomicRowsLifecycleCumulativeReadinessGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_lifecycle_gate_command_matrix.py', '--mode', 'dev', '--out', '/owned/v/master_plan_generated/AtomicRowsLifecycleGateCommandMatrix.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_parameter_agent_binding_registry.py', '--mode', 'dev', '--out', '/owned/v/master_plan_generated/AtomicRowsParameterAgentBindingReport.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_parameter_agent_binding_consumer_gate.py', '--mode', 'dev', '--out', '/owned/v/master_plan_generated/AtomicRowsParameterAgentBindingConsumerGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_parameter_agent_binding_cumulative_readiness_gate.py', '--mode', 'dev', '--out', '/owned/v/master_plan_generated/AtomicRowsParameterAgentBindingCumulativeReadinessGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_parameter_agent_binding_command_matrix.py', '--mode', 'dev', '--out', '/owned/v/master_plan_generated/AtomicRowsParameterAgentBindingCommandMatrix.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_research_provenance_evidence_tier_classification.py', '--out', '/owned/v/master_plan_generated/AtomicRowsResearchProvenanceEvidenceTierClassification.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_owner_submitted_research_source_intake_registry.py', '--out', '/owned/v/master_plan_generated/AtomicRowsOwnerSubmittedResearchSourceIntakeRegistry.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_research_source_to_candidate_family_gate.py', '--out', '/owned/v/master_plan_generated/AtomicRowsResearchSourceToCandidateFamilyGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_parameter_stack_role_taxonomy.py', '--out', '/owned/v/master_plan_generated/AtomicRowsParameterStackRoleTaxonomy.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_parameter_stack_completeness_gate.py', '--out', '/owned/v/master_plan_generated/AtomicRowsParameterStackCompletenessGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_parameter_stack_compatibility_gate.py', '--out', '/owned/v/master_plan_generated/AtomicRowsParameterStackCompatibilityGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_edge_parameter_stack_selection_packet.py', '--out', '/owned/v/master_plan_generated/EDGEParameterStackSelectionPacket.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qtt_trade_context_packet.py', '--out', '/owned/v/master_plan_generated/QTTTradeContextPacket.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_parameter_selection_universe_registry.py', '--out', '/owned/v/master_plan_generated/AtomicRowsParameterSelectionUniverseRegistry.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_parameter_selection_universe_consumer_gate.py', '--out', '/owned/v/master_plan_generated/AtomicRowsParameterSelectionUniverseConsumerGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_trade_context_selection_universe_routing_gate.py', '--out', '/owned/v/master_plan_generated/AtomicRowsTradeContextSelectionUniverseRoutingGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_quantum_applicability_classification_registry.py', '--out', '/owned/v/master_plan_generated/QuantumApplicabilityClassificationRegistry.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_owner_quantum_priority_policy_registry.py', '--out', '/owned/v/master_plan_generated/OwnerQuantumPriorityPolicyRegistry.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_parameter_algorithm_scoring_policy_registry.py', '--out', '/owned/v/master_plan_generated/ParameterAlgorithmScoringPolicyRegistry.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_parameter_stack_scoring_and_ranking_gate.py', '--out', '/owned/v/master_plan_generated/ParameterStackScoringAndRankingGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_quantum_classical_optimizer_arbitration_gate.py', '--out', '/owned/v/master_plan_generated/QuantumClassicalOptimizerArbitrationGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_candidate_parameter_stack_generation_gate.py', '--out', '/owned/v/master_plan_generated/CandidateParameterStackGenerationGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_trade_context_parameter_stack_selection_gate.py', '--out', '/owned/v/master_plan_generated/TradeContextParameterStackSelectionGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_selected_parameter_stack_handoff_packet.py', '--out', '/owned/v/master_plan_generated/SelectedParameterStackHandoffPacket.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_replay_paper_candidate_stack_competition_gate.py', '--out', '/owned/v/master_plan_generated/ReplayPaperCandidateStackCompetitionGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_dual_result_review_for_parameter_stacks.py', '--out', '/owned/v/master_plan_generated/DualResultReviewForParameterStacks.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_owner_live_promotion_review_for_parameter_stacks.py', '--out', '/owned/v/master_plan_generated/OwnerLivePromotionReviewForParameterStacks.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_owner_approval_request_queue_registry.py', '--out', '/owned/v/master_plan_generated/OwnerApprovalRequestQueueRegistry.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_owner_override_receipt_authoring_gate.py', '--out', '/owned/v/master_plan_generated/OwnerOverrideReceiptAuthoringGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_owner_dashboard_approval_menu_schema.py', '--out', '/owned/v/master_plan_generated/OwnerDashboardApprovalMenuSchema.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_owner_dashboard_approval_static_screen_contract.py', '--out', '/owned/v/master_plan_generated/OwnerDashboardApprovalStaticScreenContract.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_full_bundle_row_expansion_plan.py', '--out', '/owned/v/master_plan_generated/AtomicRowsFullBundleRowExpansionPlan.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_bundle_row_family_source_files.py', '--out', '/owned/v/master_plan_generated/AtomicRowsBundleRowFamilySourceFiles.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_bundle_builder_deterministic_assembly_gate.py', '--out', '/owned/v/master_plan_generated/AtomicRowsBundleBuilderDeterministicAssemblyGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_sha_system_dormancy_state_contract.py', '--report-out', '/owned/v/master_plan_generated/AtomicRowsShaSystemDormancyStateContract.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qtt_final_readiness_dependency_policy_contract.py', '--report-out', '/owned/v/master_plan_generated/QttFinalReadinessDependencyPolicy.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qtt_active_non_sha_day1_gate_state_registry_contract.py', '--report-out', '/owned/v/master_plan_generated/QttActiveNonShaDay1GateStateRegistry.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qtt_pr_identity_roster.py', '--report-out', '/owned/v/master_plan_generated/QttPrIdentityRoster.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qtt_roadmap_execution_state_controller.py', '--report-out', '/owned/v/master_plan_generated/QttRoadmapExecutionStateController.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_bundle_sha_freeze_authority_gate.py', '--report-out', '/owned/v/master_plan_generated/AtomicRowsBundleShaFreezeAuthorityGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_exact_row_authority_classifier_bridge.py', '--report-out', '/owned/v/master_plan_generated/AtomicRowsExactRowAuthorityClassifierBridge.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_exact_row_expansion_manifest.py', '--report-out', '/owned/v/master_plan_generated/AtomicRowsExactRowExpansionManifest.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_owner_approved_exact_15_family_count_distribution.py', '--report-out', '/owned/v/master_plan_generated/AtomicRowsOwnerApprovedExact15FamilyCountDistribution.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_exact_row_generator_dry_run_manifest.py', '--report-out', '/owned/v/master_plan_generated/AtomicRowsExactRowGeneratorDryRun.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest.py', '--report-out', '/owned/v/master_plan_generated/AtomicRowsRepairChainGrandDebugLogicAudit.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_exact_row_source_materialization_manifest.py', '--report-out', '/owned/v/master_plan_generated/AtomicRowsExactRowSourceMaterialization.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_exact_row_agent_family_eligibility_matrix.py', '--report-out', '/owned/v/master_plan_generated/AtomicRowsExactRowAgentFamilyEligibilityMatrix.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_bundle_materialization_manifest.py', '--report-out', '/owned/v/master_plan_generated/AtomicRowsBundleMaterialization.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_bundle_boundary_state_contract.py', '--report-out', '/owned/v/master_plan_generated/AtomicRowsBundleBoundaryStateContract.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_atomicrows_sha_freeze_final_readiness_state_contract.py', '--report-out', '/owned/v/master_plan_generated/AtomicRowsShaFreezeFinalReadinessStateContract.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_generated_derivative_bootstrap_gate_static.py', '--repo-root', '.', '--schema', 'schemas/master_plan/generated_derivative_bootstrap_gate.schema.json', '--fixture', 'tests/fixtures/master_plan/synthetic_generated_derivative_bootstrap_gate.v1.fixture.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_stage1_packet_schema_gate_static.py', '--repo-root', '.', '--schema-dir', 'schemas/stage1_prediction_markets', '--fixture', 'tests/fixtures/stage1_prediction_markets/synthetic_stage1_packet_schema_gate_blocked.v1.fixture.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_venue_neutral_prediction_adapter_gate_static.py', '--repo-root', '.', '--schema-dir', 'schemas/venue_neutral_prediction_adapter', '--fixture', 'tests/fixtures/venue_neutral_prediction_adapter/synthetic_venue_neutral_prediction_adapter_gate_blocked.v1.fixture.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_connector_scaffold_source_required_gate_static.py', '--repo-root', '.', '--schema', 'schemas/connectors/connector_scaffold_source_required_gate.schema.json', '--fixture', 'tests/fixtures/connectors/synthetic_connector_scaffold_source_required_blocked.v1.fixture.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_stage1_runtime_scaffold_gate_static.py', '--repo-root', '.', '--schema', 'schemas/runtime_orchestration/stage1_runtime_scaffold_gate.schema.json', '--fixture', 'tests/fixtures/runtime_orchestration/synthetic_stage1_runtime_scaffold_gate_blocked.v1.fixture.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_source_fact_binding_connector_semantic_readiness_static.py', '--repo-root', '.', '--source-to-connector-schema', 'schemas/source_fact_binding_readiness/stage1_source_to_connector_field_binding_matrix.schema.json', '--source-to-connector-fixture', 'tests/fixtures/source_fact_binding_readiness/synthetic_stage1_source_to_connector_field_binding_matrix.v1.fixture.json', '--connector-target-schema', 'schemas/source_fact_binding_readiness/stage1_connector_semantic_target_field_matrix.schema.json', '--connector-target-fixture', 'tests/fixtures/source_fact_binding_readiness/synthetic_stage1_connector_semantic_target_field_matrix.v1.fixture.json', '--gate-report-schema', 'schemas/source_fact_binding_readiness/stage1_connector_semantic_readiness_gate_report.schema.json', '--gate-report-fixture', 'tests/fixtures/source_fact_binding_readiness/synthetic_stage1_connector_semantic_readiness_gate_report.v1.fixture.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/source_evidence_acceptance_consumer_contract_check.py', '--repo-root', '.', '--consumer-contract-schema', 'src/qtt/source_evidence/acceptance/accepted_source_evidence_consumer_contract.schema.json', '--target-field-ledger-schema', 'src/qtt/source_evidence/acceptance/stage1_target_field_acceptance_ledger_record.schema.json', '--export-record-schema', 'src/qtt/source_evidence/acceptance/stage1_accepted_source_evidence_export_record.schema.json', '--fixture', 'tests/fixtures/source_evidence/acceptance_consumer_contract/synthetic_accepted_source_evidence_consumer_contract_records.v1.fixture.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/stage1_connector_semantic_binding_ledger_check.py', '--repo-root', '.', '--ledger-schema', 'src/qtt/stage1_prediction_markets/connector_semantic_binding/stage1_connector_semantic_binding_ledger_record.schema.json', '--canonicalization-schema', 'src/qtt/stage1_prediction_markets/connector_semantic_binding/stage1_connector_semantic_value_canonicalization.schema.json', '--consumer-contract-schema', 'src/qtt/stage1_prediction_markets/connector_semantic_binding/stage1_connector_semantic_binding_consumer_contract.schema.json', '--fixture', 'tests/fixtures/source_evidence/connector_semantic_binding/synthetic_stage1_connector_semantic_binding_contracts.v1.fixture.json', '--out', '/owned/v/master_plan_generated/Stage1ConnectorSemanticBindingLedgerCheck.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/stage1_runtime_resolver_snapshot_contract_check.py', '--repo-root', '.', '--input-lock-schema', 'src/qtt/stage1_prediction_markets/runtime_resolver/stage1_runtime_resolver_snapshot_input_lock.schema.json', '--manifest-schema', 'src/qtt/stage1_prediction_markets/runtime_resolver/stage1_runtime_resolver_snapshot_manifest.schema.json', '--consumer-contract-schema', 'src/qtt/stage1_prediction_markets/runtime_resolver/stage1_runtime_resolver_consumer_contract.schema.json', '--gate-report-schema', 'src/qtt/stage1_prediction_markets/runtime_resolver/stage1_runtime_resolver_snapshot_gate_report.schema.json', '--fixture', 'tests/fixtures/source_evidence/runtime_resolver/synthetic_stage1_runtime_resolver_snapshot_contracts.v1.fixture.json', '--out', '/owned/v/master_plan_generated/Stage1RuntimeResolverSnapshotContractCheck.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/stage1_runtime_resolver_to_replay_paper_handoff_check.py', '--repo-root', '.', '--consumer-allowlist-schema', 'src/qtt/stage1_prediction_markets/runtime_resolver_snapshot/stage1_runtime_resolver_snapshot_consumer_allowlist.schema.json', '--handoff-contract-schema', 'src/qtt/stage1_prediction_markets/runtime_resolver_snapshot/stage1_runtime_resolver_to_replay_paper_handoff_contract.schema.json', '--handoff-report-schema', 'src/qtt/stage1_prediction_markets/runtime_resolver_snapshot/stage1_runtime_resolver_to_replay_paper_handoff_report.schema.json', '--fixture', 'tests/fixtures/source_evidence/runtime_resolver_snapshot/synthetic_stage1_runtime_resolver_to_replay_paper_handoff.v1.fixture.json', '--out', '/owned/v/master_plan_generated/Stage1RuntimeResolverToReplayPaperHandoff.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/stage1_concurrent_replay_paper_contract_check.py', '--repo-root', '.', '--input-identity-schema', 'src/qtt/stage1_prediction_markets/replay_paper/concurrent_replay_paper_input_identity.schema.json', '--replay-lane-schema', 'src/qtt/stage1_prediction_markets/replay_paper/concurrent_replay_lane_contract.schema.json', '--paper-lane-schema', 'src/qtt/stage1_prediction_markets/replay_paper/concurrent_paper_lane_contract.schema.json', '--replay-result-boundary-schema', 'src/qtt/stage1_prediction_markets/replay_paper/replay_result_packet_boundary.schema.json', '--paper-result-boundary-schema', 'src/qtt/stage1_prediction_markets/replay_paper/paper_result_packet_boundary.schema.json', '--gate-report-schema', 'src/qtt/stage1_prediction_markets/replay_paper/concurrent_replay_paper_execution_gate_report.schema.json', '--fixture', 'tests/fixtures/source_evidence/replay_paper/synthetic_concurrent_replay_paper_contracts.v1.fixture.json', '--out', '/owned/v/master_plan_generated/Stage1ConcurrentReplayPaperContractCheck.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/stage1_dual_result_review_contract_check.py', '--repo-root', '.', '--input-contract-schema', 'src/qtt/stage1_prediction_markets/dual_result_review/stage1_dual_result_review_input_contract.schema.json', '--comparison-matrix-schema', 'src/qtt/stage1_prediction_markets/dual_result_review/stage1_replay_paper_comparison_matrix.schema.json', '--gate-report-schema', 'src/qtt/stage1_prediction_markets/dual_result_review/stage1_dual_result_review_gate_report.schema.json', '--owner-handoff-block-schema', 'src/qtt/stage1_prediction_markets/dual_result_review/stage1_owner_live_promotion_handoff_block.schema.json', '--fixture', 'tests/fixtures/source_evidence/dual_result_review/synthetic_stage1_dual_result_review_contracts.v1.fixture.json', '--out', '/owned/v/master_plan_generated/Stage1DualResultReviewContractCheck.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/stage1_owner_live_promotion_review_contract_check.py', '--repo-root', '.', '--input-contract-schema', 'src/qtt/stage1_prediction_markets/owner_live_promotion_review/stage1_owner_live_promotion_review_input_contract.schema.json', '--owner-approval-receipt-boundary-schema', 'src/qtt/stage1_prediction_markets/owner_live_promotion_review/stage1_owner_approval_receipt_boundary.schema.json', '--gate-report-schema', 'src/qtt/stage1_prediction_markets/owner_live_promotion_review/stage1_owner_live_promotion_review_gate_report.schema.json', '--handoff-block-schema', 'src/qtt/stage1_prediction_markets/owner_live_promotion_review/stage1_three_venue_canary_eligibility_handoff_block.schema.json', '--fixture', 'tests/fixtures/source_evidence/owner_live_promotion_review/synthetic_stage1_owner_live_promotion_review_contracts.v1.fixture.json', '--out', '/owned/v/master_plan_generated/Stage1OwnerLivePromotionReviewContractCheck.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/stage1_three_venue_canary_eligibility_contract_check.py', '--repo-root', '.', '--input-contract-schema', 'src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/stage1_three_venue_canary_eligibility_input_contract.schema.json', '--readiness-matrix-schema', 'src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/stage1_three_venue_platform_readiness_matrix.schema.json', '--handoff-schema', 'src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/stage1_owner_review_to_canary_eligibility_handoff.schema.json', '--gate-report-schema', 'src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/stage1_three_venue_canary_eligibility_gate_report.schema.json', '--execution-block-schema', 'src/qtt/stage1_prediction_markets/three_venue_canary_eligibility/stage1_limited_live_canary_execution_block.schema.json', '--fixture', 'tests/fixtures/source_evidence/three_venue_canary_eligibility/synthetic_stage1_three_venue_canary_eligibility_contracts.v1.fixture.json', '--out', '/owned/v/master_plan_generated/Stage1ThreeVenueCanaryEligibilityContractCheck.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/build_master_plan_section_coverage_report.py', '--out', '/owned/v/master_plan_generated/MasterPlanSectionCoverageReport.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_master_plan_section_coverage.py', '--mode', 'dev')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qtt_master_plan_section_coverage_triage_routes.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qtt_master_plan_section_roadmap_crosswalk.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qtt_master_plan_section_coverage_command_matrix.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/qtt_test_gate.py', '--phase', 'first-coding-runbook', '--repo-root', '.', '--strict-no-claim', '--out', '/owned/v/master_plan_generated/QTTTestGate.report.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/local_gate_command_matrix.py', '--repo-root', '.', '--out', '/owned/v/master_plan_generated/LocalGateCommandMatrix.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/pr_handoff_check.py', '--repo-root', '.', '--out', '/owned/v/master_plan_generated/FirstCodingPRHandoff.packet.json')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qku_computation_control_plane.py', '--domain', 'architecture')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qku_computation_control_plane.py', '--domain', 'quantum')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qku_computation_control_plane.py', '--domain', 'latency')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qku_computation_control_plane.py', '--domain', 'd')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qku_computation_control_plane.py', '--domain', 'agent')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qku_computation_control_plane.py', '--domain', 'model_risk')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qku_computation_control_plane.py', '--domain', 'g')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qku_computation_control_plane.py', '--domain', 'h')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/independent_validate_qku_computation_control_plane.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/independent_validate_qku_computation_control_plane_latency.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/independent_validate_qku_computation_control_plane_model_risk.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/independent_validate_qku_computation_control_plane_g.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/independent_validate_qku_computation_control_plane_agent.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/independent_validate_qku_computation_control_plane_d.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/independent_validate_qku_computation_control_plane_quantum.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/independent_validate_qku_computation_control_plane_architecture.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/independent_validate_qku_computation_control_plane_accounting.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/independent_validate_qku_computation_control_plane_execution.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/independent_validate_qku_computation_control_plane_llm.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/independent_validate_qku_computation_control_plane_operations.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/independent_validate_qku_computation_control_plane_security.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/independent_validate_qku_computation_control_plane_source.py')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qku_computation_control_plane.py', '--domain', 'accounting')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qku_computation_control_plane.py', '--domain', 'execution')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qku_computation_control_plane.py', '--domain', 'llm')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qku_computation_control_plane.py', '--domain', 'operations')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qku_computation_control_plane.py', '--domain', 'security')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_qku_computation_control_plane.py', '--domain', 'source')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_pr169_val1.py', '--repo-root', '.')),
        ('deterministic-validators-c', ('REVIEW_PYTHON', 'tools/validate_no_runtime_artifacts.py', '--repo-root', '.', '--forbid-source-retrieval', '--forbid-source-acceptance', '--forbid-connector-binding', '--forbid-private-state-fetch', '--forbid-order-execution', '--forbid-neural-training', '--forbid-neural-inference', '--forbid-external-repo-clone', '--forbid-package-install-scripts')),
        ('pytest-shard-1', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/tools', 'tests/fail_closed', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/agent_consumable_parameter_default_registry', 'tests/stage1_prediction_markets/agent_default_binding_universal_intake_gate', 'tests/stage1_prediction_markets/aggressive_qku_candidate_materialization_agent_routing', 'tests/stage1_prediction_markets/atomicrows_bundle_reconciliation', 'tests/stage1_prediction_markets/atomicrows_pr154_value_state', 'tests/stage1_prediction_markets/latency_hot_path_snapshot_boundary', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr160_split_reclassification_route_closure', 'tests/stage1_prediction_markets/pr162d_r1_external_formula_data_quantum_acquisition_expansion', 'tests/stage1_prediction_markets/pr162d_r2a_real_formulations', 'tests/stage1_prediction_markets/pr162r_a_replay_paper_executability_classification_audit', 'tests/stage1_prediction_markets/pr162r_b_replay_paper_data_binding_completion', 'tests/stage1_prediction_markets/pr162r_generic_replay_paper_adapter_rerun', 'tests/stage1_prediction_markets/pr163_b_paired_replay_paper_concurrent_executor', 'tests/stage1_prediction_markets/pr163_c_pretrade_infrastructure_rejection_remediation', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/atomicrows', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_gfp', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_rp', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_rank', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_data1', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_data1a', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_gfp2r', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_rp2', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_map3', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_rp3', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_rank3', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_rp5a', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_rp5b', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_rp5c', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_vs1', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_rp5d', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_rp5e', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_rp5d_r1', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_rp5f', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_rp5g', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_rank4', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_qopt1', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_vs2', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr168_mem1', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr169_dash1', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr169_readiness1', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr169_pretrade1', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr169_svc1', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr169_agent_orch1', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-2', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr169_dash1_ui1', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-3', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/master_plan_residual_candidate_coverage', 'tests/stage1_prediction_markets/multisource_safe_nonlive_dataset_expansion_strict_qku_coverage', 'tests/stage1_prediction_markets/nonlive_replay_paper_data_adapter_quantum_forward_bridge', 'tests/stage1_prediction_markets/pr157_completion_materialization_bridge', 'tests/stage1_prediction_markets/pr158_owner_response_selection_readiness_bridge', 'tests/stage1_prediction_markets/pr159_official_source_completion_bridge', 'tests/stage1_prediction_markets/pr159r_source_locator_value_capture', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-3', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr163_generic_paper_adapter_capture_framework', 'tests/stage1_prediction_markets/pr164_review_provenance_qku_canonical_coverage_audit', 'tests/stage1_prediction_markets/pr165_b_condition_scoped_negative_memory', 'tests/stage1_prediction_markets/pr165_c_replay_paper_memory_consumer_integration', 'tests/stage1_prediction_markets/pr165_d_scenario_qku_combination_selection', 'tests/stage1_prediction_markets/pr165_d2_score_refreshed_scenario_selection_v2', 'tests/stage1_prediction_markets/pr165_evidence_backed_scoring_ranking', 'tests/stage1_prediction_markets/pr166_s_replay_paper_scenario_retest_execution', 'tests/stage1_prediction_markets/pr166_s2_replay_paper_retest_loop_v2', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-3', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/qku_candidate_quality_replay_paper_prioritization', 'tests/stage1_prediction_markets/qku_formula_algorithm_solver_market_scope_materialization', 'tests/stage1_prediction_markets/qku_residual_candidate_assimilation', 'tests/stage1_prediction_markets/replay_paper_executor_input_run_artifact_generation', 'tests/stage1_prediction_markets/replay_paper_outcome_capture_scenario_learning', 'tests/stage1_prediction_markets/safe_repo_local_nonlive_dataset_materialization_authority_gate', 'tests/stage1_prediction_markets/source_intelligence', 'tests/stage1_prediction_markets/test_validate_stage1_packet_schema_gate_static.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-4', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_sf_repair_materialization_before_retest', 'tests/stage1_prediction_markets/pr166_sm_score_memory_refresh_from_pr166_s_results', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-4', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_idempotence.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-5', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_ablation.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_agent_duty.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_agent_kpi.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_agent_task_queue.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_all_neg_conversion.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_alt_exec_memory.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_authority_boundaries.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_break_even_gap.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_build_outputs.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_calib_boost.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_calibration.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_candidate_family.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_capacity_crowding.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-5', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_champion_challenger.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_compact_names.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_condition_winners_losers.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_connector_ref_routing.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_conversion_agent_queue.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_conversion_math.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_convertible_queue.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_cost_cut.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_counterfactual.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_diversity.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_edge_decay.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_edge_uplift.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-5', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_evidence_depth.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_expansion_policy.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_external_dedupe.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_external_signal_registry.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_fill_boost.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_fragile_watchlist.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_handoff_intake.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_idempotence.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_input_consumption.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_lat_liq_impact.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_latent_edge.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_lcb_confidence.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-5', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_marginal_utility.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_memory_dag.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_memory_ledger.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_microstructure.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_no_bad_status_tokens.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_no_fill_memory.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_no_orphans.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_no_profit_evidence.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_orthogonal_edge.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_overfit_fdr.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_param_uplift.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_pos_seed_driver.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-5', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_positive_expansion.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_positive_negative_edge.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_pr152_pr208_routing_contract.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_pref_avoid_memory.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_provenance_supersession_drift.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_quantum_priority.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_rank_aggregation.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_rank_delta.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_rank_stability.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_regime_memory.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_repair_priority.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_result_intake.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-5', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_retest_boost_queue.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_route_crosswalk_cmd.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_row_count_reconciliation.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_score_explain.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_score_registry.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_selection_pressure.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_selection_ready_queue.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_settlement_adverse.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_shard_input_audit.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_shrinkage.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_status_enum_drift.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_tca_cost_roots.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_tt_risk.py', 'tests/stage1_prediction_markets/pr166_sm2_score_memory_refresh_v2/test_pr166_sm2_validator.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-6', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_agent_duty.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_agent_kpi.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_agent_task_queue.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_all_negative_intake.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_alt_exec_repair.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_authority_boundaries.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_before_after.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_break_even_gap.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_build_outputs.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_calib_uplift_proof.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_calibration.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_calibration_repair.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_capacity_crowding.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-6', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_champion_challenger.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_compact_names.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_computable_payload.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_connectivity.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_connector_routing.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_conversion_attribution.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_conversion_frontier.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_conversion_proof.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_cost_floor.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_cost_repair.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_downstream_handoffs.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_episode_plan.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-6', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_external_signals.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_fill_probability_model.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_fill_repair.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_fills_no_fills.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_formula_qku_repair.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_handoff_intake.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_holdout_replay.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-6', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_impl_shortfall.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_input_consumption.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_launch_candidate_filter.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_lcb_confidence.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-6', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_marginal_utility.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_microstructure.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_net_edge.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_no_bad_status_tokens.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_no_orphans.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_no_profit_evidence.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_order_intents.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_overfit_fdr.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_parameter_bound_audit.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_parameter_repair.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_positive_capacity.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_positive_conversion.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-6', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_pr152_pr208_routing_contract.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_quantum_handoff.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_quantum_objective_map.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_quantum_repair.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_rank_stability.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_regime_memory.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_repair_ablation.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_repair_failure.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_repair_feasibility.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_repair_frontier.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_repair_portfolio.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_repair_priority.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-6', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_repair_sensitivity.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_repair_universe.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_repaired_packet_registry.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_retest_policy.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_retest_universe.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_route_crosswalk_cmd.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_row_count_reconciliation.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_runtime_safety_handoff.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_shard_input_audit.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_status_enum_drift.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_still_negative.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_tca_cost_roots.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_terminal_rows.py', 'tests/stage1_prediction_markets/pr166_sf_r2_targeted_conversion_repair_retest/test_pr166_sf_r2_validator.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-7', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr165_d3_quantum_aware_scenario_selection_v3', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-7', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_sm3_score_memory_refresh_v3/test_pr166_sm3_idempotence.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-7', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_sm3_score_memory_refresh_v3', '-q', '--ignore', 'tests/stage1_prediction_markets/pr166_sm3_score_memory_refresh_v3/test_pr166_sm3_idempotence.py', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_q_quantum_classical_hybrid_comparator/test_pr166_q_idempotence.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_q_quantum_classical_hybrid_comparator', '-q', '--ignore', 'tests/stage1_prediction_markets/pr166_q_quantum_classical_hybrid_comparator/test_pr166_q_idempotence.py', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_qb_bounded_quantum_benchmark/test_pr166_qb_idempotence.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_qb_bounded_quantum_benchmark', '-q', '--ignore', 'tests/stage1_prediction_markets/pr166_qb_bounded_quantum_benchmark/test_pr166_qb_idempotence.py', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_qc_quantum_selected_replay_paper_retest/test_pr166_qc_idempotence.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr166_qc_quantum_selected_replay_paper_retest', '-q', '--ignore', 'tests/stage1_prediction_markets/pr166_qc_quantum_selected_replay_paper_retest/test_pr166_qc_idempotence.py', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr162e_q_quantum_automapper/test_pr162e_q_idempotence.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr162e_q_quantum_automapper', '-q', '--ignore', 'tests/stage1_prediction_markets/pr162e_q_quantum_automapper/test_pr162e_q_idempotence.py', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr167_open_trade_simulator_integration/test_pr167_idempotence.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/pr167_open_trade_simulator_integration', '-q', '--ignore', 'tests/stage1_prediction_markets/pr167_open_trade_simulator_integration/test_pr167_idempotence.py', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr162e/test_pr162e_idempotence_bounded.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/pr162e', '-q', '--ignore', 'tests/pr162e/test_pr162e_idempotence_bounded.py', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/source_evidence/test_controlled_official_source_capture_candidate_packets.py', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/agent_algorithm', 'tests/agents', 'tests/algorithms', 'tests/connectors', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/core', 'tests/dashboard', 'tests/edge', 'tests/external_repo', 'tests/governance', 'tests/launch', 'tests/master_plan', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/global_debug', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/neural_signal', 'tests/quantum', 'tests/replay_paper', 'tests/replay_paper_review', 'tests/research', 'tests/roadmap', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/runtime_cash', 'tests/runtime_orchestration', 'tests/runtime_resolver', 'tests/scoring', 'tests/selection', 'tests/venue_neutral_prediction_adapter', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/source_evidence', '-q', '--ignore', 'tests/source_evidence/test_controlled_official_source_capture_candidate_packets.py', '--durations=50', '--basetemp', '/owned/p')),
        ('pytest-shard-8', ('REVIEW_PYTHON', 'tools/run_pytest_fresh_basetemp.py', 'tests/stage1_prediction_markets/qku_computation_control_plane', '-q', '--durations=50', '--basetemp', '/owned/p')),
        ('post-validation', ('REVIEW_PYTHON', '-m', 'compileall', '-q', 'tools', 'tests', 'src')),
        ('post-validation', ('git', 'diff', '--check')),
        ('post-validation', ('git', 'diff', '--exit-code', '--', 'docs/master_plan/QTT_MasterPlan_Current.md')),
        ('post-validation', ('REVIEW_PYTHON', '-c', "import json\nfrom pathlib import Path\n\nbundle = Path('docs/master_plan/atomic_rows/AtomicRows.bundle.jsonl')\nsidecar = Path('docs/master_plan/atomic_rows') / ('AtomicRows' + '.bundle' + '.' + 'sha256')\nif not bundle.is_file():\n    raise SystemExit('AtomicRows bundle is missing')\nif sidecar.exists():\n    raise SystemExit('AtomicRows bundle SHA sidecar must be absent')\ndata = bundle.read_bytes()\nassert data, 'AtomicRows bundle is empty'\nassert not data.startswith(b'\\xef\\xbb\\xbf'), 'AtomicRows bundle has a UTF-8 BOM'\nassert b'\\r' not in data, 'AtomicRows bundle contains CR or CRLF line endings'\nassert data.endswith(b'\\n'), 'AtomicRows bundle must end with LF'\nlines = data.decode('utf-8').splitlines()\nassert len(lines) == 4183, f'expected 4183 AtomicRows rows, found {len(lines)}'\nassert all(line.strip() for line in lines), 'AtomicRows bundle contains blank rows'\nfor line_number, line in enumerate(lines, start=1):\n    json.loads(line)\n")),
    )
    runner_source = Path(runner.__file__).read_bytes()
    scope_source = (Path(runner.__file__).parent / "validation_scope_registry.py").read_bytes()
    # The retained diagnostic has POSIX path spelling. Keep that inspected
    # formatting profile explicit even when this group runs on admitted Windows;
    # this pure path facade neither performs I/O nor qualifies native execution.
    monkeypatch.setattr(runner, "pathlib", SimpleNamespace(
        Path=PurePosixPath, PurePath=PurePosixPath, PurePosixPath=PurePosixPath))
    node_count = sum(sum(1 for _ in ast.walk(ast.parse(source))) for source in (runner_source, scope_source))
    checks = []
    finite_before = {name for name in sys.modules if name.startswith("_qtt_v35_finite_manifest_")}
    options = dict(expected_runner_source=runner_source, expected_scope_source=scope_source,
        python_executable="REVIEW_PYTHON", validation_dir=PurePosixPath("/owned/v"), pytest_basetemp=PurePosixPath("/owned/p"),
        byte_limit=len(runner_source) + len(scope_source), node_limit=node_count,
        command_limit=450, argument_limit=2323, check_candidate=lambda: checks.append("original-candidate"))
    projected = runner._project_probability_validation_manifest_v1(runner_source, scope_source, **options)
    assert checks == ["original-candidate", "original-candidate"]
    assert len(projected) == 13
    assert tuple((phase["phase"], tuple(command)) for phase in projected for command in phase["commands"]) == expected_ordered
    assert [phase["command_count"] for phase in projected] == [8, 64, 55, 245, 1, 32, 3, 2, 6, 7, 3, 20, 4]
    assert sum(len(command) for phase in projected for command in phase["commands"]) == 2323
    assert {name for name in sys.modules if name.startswith("_qtt_v35_finite_manifest_")} == finite_before

    def replaced_declaration(source, name, replacement):
        decoded = source.decode("utf-8")
        nodes = [node for node in ast.parse(decoded).body if
                 (isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name) or
                 (isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets))]
        assert len(nodes) == 1
        lines = decoded.splitlines(keepends=True)
        node = nodes[0]
        return ("".join(lines[:node.lineno - 1]) + replacement + "\n" + "".join(lines[node.end_lineno:])).encode("utf-8")

    for bad_runner, bad_helper in ((runner_source + b"\n", scope_source), (runner_source, scope_source + b"\n")):
        with pytest.raises(ValueError, match="independent original byte basis"):
            runner._project_probability_validation_manifest_v1(bad_runner, bad_helper, **options)
    # Both bad bytes are independently supplied to reach the structural/effect
    # checks: source equality alone must not bless arbitrary selected declarations.
    phase_nodes = [node for node in ast.parse(runner_source).body if isinstance(node, ast.Assign) and
                   any(isinstance(target, ast.Name) and target.id == "ORDERED_PHASES" for target in node.targets)]
    assert len(phase_nodes) == 2
    phase_lines = runner_source.decode("utf-8").splitlines(keepends=True)
    first, second = phase_nodes
    altered_pair = ("".join(phase_lines[:first.lineno - 1]) + "ORDERED_PHASES = ()\n" +
                    "".join(phase_lines[first.end_lineno:])).encode("utf-8")
    reversed_pair = ("".join(phase_lines[:first.lineno - 1]) +
                     "".join(phase_lines[second.lineno - 1:second.end_lineno]) +
                     "".join(phase_lines[first.end_lineno:second.lineno - 1]) +
                     "".join(phase_lines[first.lineno - 1:first.end_lineno]) +
                     "".join(phase_lines[second.end_lineno:])).encode("utf-8")
    negative_sources = (
        (runner_source + b"\nORDERED_PHASES = ()\n", "ordered phase expansion profile"),
        (altered_pair, "ordered phase expansion profile"),
        (reversed_pair, "ordered phase expansion profile"),
        (runner_source + b"\nFAST_PREFLIGHT_PHASE = 'duplicate'\n", "duplicate manifest declaration"),
        (replaced_declaration(runner_source, "PYTEST_DURATIONS_ARG", "PYTEST_DURATIONS_ARG = _path('x')"), "unselected manifest initializer"),
        (replaced_declaration(runner_source, "PYTEST_DURATIONS_ARG", "PYTEST_DURATIONS_ARG = _pr166_sm2_pytest_paths(())"), "unselected manifest initializer"),
        (replaced_declaration(runner_source, "_pr166_sm2_pytest_paths", "def _pr166_sm2_pytest_paths(file_names: Sequence[str]) -> tuple[str, ...]:\n    return ()"), "path constructor profile"),
        (replaced_declaration(runner_source, "_pr166_sf_r2_pytest_paths", "def _pr166_sf_r2_pytest_paths(file_names: Sequence[str]) -> tuple[str, ...]:\n    return ()"), "path constructor profile"),
        (replaced_declaration(runner_source, "build_phase_manifest", "def build_phase_manifest(validation_dir=None, pytest_basetemp=None):\n    import os\n    return []"), "effectful declaration"),
        (replaced_declaration(runner_source, "build_phase_manifest", "def build_phase_manifest(validation_dir=None, pytest_basetemp=None):\n    return getattr(pathlib, 'Path')('.')"), "unselected manifest call"),
    )
    for bad, reason in negative_sources:
        with pytest.raises(ValueError, match=reason):
            runner._project_probability_validation_manifest_v1(bad, scope_source, **{**options,
                "expected_runner_source": bad, "byte_limit": len(bad) + len(scope_source),
                "node_limit": node_count + 1000})
        assert {name for name in sys.modules if name.startswith("_qtt_v35_finite_manifest_")} == finite_before
    for key, value in (("byte_limit", len(runner_source) + len(scope_source) - 1),
                       ("node_limit", node_count - 1), ("command_limit", 449), ("argument_limit", 2322)):
        with pytest.raises(ValueError):
            runner._project_probability_validation_manifest_v1(runner_source, scope_source, **{**options, key: value})
        assert {name for name in sys.modules if name.startswith("_qtt_v35_finite_manifest_")} == finite_before


def test_runner_assigns_canonical_non_pytest_commands_to_one_phase(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)
    validation_dir = Path("validation-dir")
    pytest_basetemp = Path("pytest-basetemp")

    canonical_commands = runner.build_validation_commands(validation_dir, pytest_basetemp)
    canonical_non_pytest = [
        command
        for command in canonical_commands
        if not runner._command_uses_pytest_helper(command)
    ]
    phase_non_pytest = runner.build_phase_commands(
        runner.FAST_PREFLIGHT_PHASE,
        validation_dir,
        pytest_basetemp,
    )
    for phase in runner.DETERMINISTIC_VALIDATOR_SHARD_PHASES:
        phase_non_pytest += runner.build_phase_commands(
            phase,
            validation_dir,
            pytest_basetemp,
        )

    for command in canonical_non_pytest:
        assert phase_non_pytest.count(command) == 1
    assert not any(
        runner._command_uses_pytest_helper(command) for command in phase_non_pytest
    )


def test_runner_deterministic_phase_moves_preflight_validator_out_of_long_phase():
    validation_dir = Path("validation-dir")
    pytest_basetemp = Path("pytest-basetemp")

    fast_names = [
        Path(command[1]).name
        for command in runner.build_phase_commands(
            runner.FAST_PREFLIGHT_PHASE,
            validation_dir,
            pytest_basetemp,
        )
    ]
    deterministic_names = [
        Path(command[1]).name
        for command in runner.build_phase_commands(
            runner.DETERMINISTIC_VALIDATORS_PHASE,
            validation_dir,
            pytest_basetemp,
        )
    ]

    assert set(fast_names) == runner.FAST_PREFLIGHT_SCRIPT_NAMES
    assert "validate_grand_global_debug_logical_consistency_audit.py" in fast_names
    assert "validate_grand_global_debug_logical_consistency_audit.py" not in deterministic_names


def test_runner_keeps_deterministic_alias_out_of_ordered_ci_phases():
    assert runner.DETERMINISTIC_VALIDATORS_PHASE in runner.VALIDATION_PHASES
    assert runner.DETERMINISTIC_VALIDATORS_PHASE not in runner.ORDERED_PHASES
    assert tuple(runner.DETERMINISTIC_VALIDATOR_SHARD_PHASES) == (
        "deterministic-validators-a",
        "deterministic-validators-b",
        "deterministic-validators-c",
    )


def test_runner_pytest_shards_cover_each_test_file_once():
    all_tests = set(runner.discover_pytest_files(REPO_ROOT))
    shard_manifest = runner.pytest_shard_manifest(REPO_ROOT)
    flattened = [
        path
        for shard_paths in shard_manifest.values()
        for path in shard_paths
    ]

    assert all_tests
    assert set(flattened) == all_tests
    assert flattened.count(runner.ST12H_TEST_MODULE) == 1
    assert len(flattened) == len(set(flattened))
    assert set(shard_manifest) == set(runner.PYTEST_SHARD_PHASES)
    assert (
        runner.ISOLATED_SOURCE_EVIDENCE_PYTEST
        in shard_manifest["pytest-shard-8"]
    )
    assert "tests/tools/test_ci_branch_context.py" in shard_manifest["pytest-shard-1"]
    assert (
        "tests/stage1_prediction_markets/pr159r_source_locator_value_capture/"
        "test_pr159r_branch_context_relaxation.py"
        in shard_manifest["pytest-shard-3"]
    )
    assert (
        "tests/global_debug/test_grand_global_debug_logical_consistency_audit.py"
        in shard_manifest["pytest-shard-8"]
    )
    assert (
        "tests/stage1_prediction_markets/pr165_d3_quantum_aware_scenario_selection_v3/"
        "test_pr165_d3_validator.py"
        in shard_manifest["pytest-shard-7"]
    )


def test_runner_pytest_runtime_budget_plan_is_complete_and_fail_closed():
    failures = runner.pytest_runtime_budget_failures(REPO_ROOT)
    plan = runner.pytest_runtime_budget_plan()

    assert failures == ()
    assert set(plan["pytest_shards"]) == set(runner.PYTEST_SHARD_PHASES)
    assert set(plan["shard_budgets"]) == set(runner.PYTEST_SHARD_PHASES)
    assert runner.RUNTIME_BUDGET_POLICY["pytest_shard_target_seconds"] == 20 * 60
    assert runner.RUNTIME_BUDGET_POLICY["pytest_shard_warning_seconds"] == 25 * 60
    assert runner.RUNTIME_BUDGET_POLICY["pytest_shard_hard_review_seconds"] == 30 * 60
    assert (
        runner.RUNTIME_BUDGET_POLICY["pytest_subprocess_group_target_seconds"]
        == 8 * 60
    )
    assert (
        runner.RUNTIME_BUDGET_POLICY["pytest_subprocess_group_warning_seconds"]
        == 10 * 60
    )
    assert runner.RUNTIME_BUDGET_POLICY["pytest_file_warning_seconds"] == 120
    assert runner.RUNTIME_BUDGET_POLICY["pytest_file_hard_review_seconds"] == 300
    assert runner.RUNTIME_BUDGET_POLICY["pytest_idempotence_warning_seconds"] == 120
    assert (
        runner.RUNTIME_BUDGET_POLICY["pytest_idempotence_hard_review_seconds"]
        == 180
    )
    assert runner.BOUNDED_DEFAULT_IDEMPOTENCE_TEST_PATHS == frozenset(
        {
            _pr166_sf_r2_idempotence_path(),
            _pr166_sm3_idempotence_path(),
            _pr166_q_idempotence_path(),
            _pr166_qb_idempotence_path(),
            _pr166_qc_idempotence_path(),
            _pr162e_q_idempotence_path(),
            _pr167_idempotence_path(),
            _pr162e_idempotence_path(),
        }
    )


def _pr166_sm2_group_paths() -> list[tuple[str, ...]]:
    return [
        tuple(
            f"{runner.PR166_SM2_TEST_ROOT}/{file_name}"
            for file_name in group
        )
        for group in runner.PR166_SM2_PYTEST_FILE_GROUPS
    ]


def _pr166_sf_r2_group_paths() -> list[tuple[str, ...]]:
    return [
        tuple(
            f"{runner.PR166_SF_R2_TEST_ROOT}/{file_name}"
            for file_name in group
        )
        for group in runner.PR166_SF_R2_PYTEST_FILE_GROUPS
    ]


def _pr166_sf_r2_idempotence_path() -> str:
    return (
        f"{runner.PR166_SF_R2_TEST_ROOT}/"
        f"{runner.PR166_SF_R2_IDEMPOTENCE_TEST_FILE}"
    )


def _pr166_sm3_idempotence_path() -> str:
    return (
        f"{runner.PR166_SM3_TEST_ROOT}/"
        f"{runner.PR166_SM3_IDEMPOTENCE_TEST_FILE}"
    )


def _pr166_q_idempotence_path() -> str:
    return (
        f"{runner.PR166_Q_TEST_ROOT}/"
        f"{runner.PR166_Q_IDEMPOTENCE_TEST_FILE}"
    )


def _pr166_qb_idempotence_path() -> str:
    return (
        f"{runner.PR166_QB_TEST_ROOT}/"
        f"{runner.PR166_QB_IDEMPOTENCE_TEST_FILE}"
    )


def _pr166_qc_idempotence_path() -> str:
    return (
        f"{runner.PR166_QC_TEST_ROOT}/"
        f"{runner.PR166_QC_IDEMPOTENCE_TEST_FILE}"
    )


def _pr162e_q_idempotence_path() -> str:
    return (
        f"{runner.PR162E_Q_TEST_ROOT}/"
        f"{runner.PR162E_Q_IDEMPOTENCE_TEST_FILE}"
    )


def _pr167_idempotence_path() -> str:
    return (
        f"{runner.PR167_TEST_ROOT}/"
        f"{runner.PR167_IDEMPOTENCE_TEST_FILE}"
    )


def _pr162e_idempotence_path() -> str:
    return (
        f"{runner.PR162E_TEST_ROOT}/"
        f"{runner.PR162E_IDEMPOTENCE_TEST_FILE}"
    )


def _pr166_sf_r2_non_idempotence_group_paths() -> list[tuple[str, ...]]:
    idempotence_group = (_pr166_sf_r2_idempotence_path(),)
    return [
        group_paths
        for group_paths in _pr166_sf_r2_group_paths()
        if group_paths != idempotence_group
    ]


def _pr166_sf_r2_split_command_placements():
    return [
        (phase, command.paths)
        for phase in runner.PYTEST_SHARD_PHASES
        for command in runner.PYTEST_SHARD_COMMANDS[phase]
        if any(
            path.startswith(f"{runner.PR166_SF_R2_TEST_ROOT}/")
            for path in command.paths
        )
    ]


def test_runner_splits_pytest_shard_2_longest_group_deterministically():
    commands = runner.PYTEST_SHARD_COMMANDS["pytest-shard-2"]

    assert [command.paths for command in commands] == [
        (
            "tests/stage1_prediction_markets/agent_consumable_parameter_default_registry",
            "tests/stage1_prediction_markets/agent_default_binding_universal_intake_gate",
            "tests/stage1_prediction_markets/aggressive_qku_candidate_materialization_agent_routing",
            "tests/stage1_prediction_markets/atomicrows_bundle_reconciliation",
            "tests/stage1_prediction_markets/atomicrows_pr154_value_state",
            "tests/stage1_prediction_markets/latency_hot_path_snapshot_boundary",
        ),
        (
            "tests/stage1_prediction_markets/pr160_split_reclassification_route_closure",
            "tests/stage1_prediction_markets/pr162d_r1_external_formula_data_quantum_acquisition_expansion",
            "tests/stage1_prediction_markets/pr162d_r2a_real_formulations",
            "tests/stage1_prediction_markets/pr162r_a_replay_paper_executability_classification_audit",
            "tests/stage1_prediction_markets/pr162r_b_replay_paper_data_binding_completion",
            "tests/stage1_prediction_markets/pr162r_generic_replay_paper_adapter_rerun",
            "tests/stage1_prediction_markets/pr163_b_paired_replay_paper_concurrent_executor",
            "tests/stage1_prediction_markets/pr163_c_pretrade_infrastructure_rejection_remediation",
        ),
        ("tests/atomicrows",),
        ("tests/pr168_gfp",),
        ("tests/pr168_rp",),
        ("tests/pr168_rank",),
        ("tests/pr168_data1",),
        ("tests/pr168_data1a",),
        ("tests/pr168_gfp2r",),
        ("tests/pr168_rp2",),
        ("tests/pr168_map3",),
        ("tests/pr168_rp3",),
        ("tests/pr168_rank3",),
        ("tests/pr168_rp5a",),
        ("tests/pr168_rp5b",),
        ("tests/pr168_rp5c",),
        ("tests/pr168_vs1",),
        ("tests/pr168_rp5d",),
        ("tests/pr168_rp5e",),
        ("tests/pr168_rp5d_r1",),
        ("tests/pr168_rp5f",),
        ("tests/pr168_rp5g",),
        ("tests/pr168_rank4",),
        ("tests/pr168_qopt1",),
        ("tests/pr168_vs2",),
        ("tests/pr168_mem1",),
        ("tests/pr169_dash1",),
        ("tests/pr169_readiness1",),
        ("tests/pr169_pretrade1",),
        ("tests/pr169_svc1",),
        ("tests/pr169_agent_orch1",),
        ("tests/pr169_dash1_ui1",),
    ]
    assert all(command.reason for command in commands)
    assert ("tests/stage1_prediction_markets",) not in [
        command.paths for command in commands
    ]

    expanded_paths = [
        path
        for command in commands
        for path in runner._pytest_files_for_command(command, REPO_ROOT)
    ]

    assert len(expanded_paths) == len(set(expanded_paths))
    assert set(expanded_paths) == set(
        runner.pytest_shard_manifest(REPO_ROOT)["pytest-shard-2"]
    )


def test_runner_pr166_sm2_split_groups_cover_each_test_file_once():
    expected = {
        path
        for path in runner.discover_pytest_files(REPO_ROOT)
        if path.startswith(f"{runner.PR166_SM2_TEST_ROOT}/")
    }
    grouped = [
        path
        for group in _pr166_sm2_group_paths()
        for path in group
    ]
    expanded = [
        path
        for command in runner.PYTEST_SHARD_COMMANDS["pytest-shard-5"]
        if any(path.startswith(f"{runner.PR166_SM2_TEST_ROOT}/") for path in command.paths)
        for path in runner._pytest_files_for_command(command, REPO_ROOT)
    ]

    assert len(runner.PR166_SM2_PYTEST_FILE_GROUPS) == 6
    assert all(0 < len(group) <= 14 for group in runner.PR166_SM2_PYTEST_FILE_GROUPS)
    assert grouped == sorted(grouped)
    assert len(grouped) == len(set(grouped))
    assert set(grouped) == expected
    assert expanded == grouped
    assert set(expanded).issubset(
        set(runner.pytest_shard_manifest(REPO_ROOT)["pytest-shard-5"])
    )


def test_runner_pr166_sf_r2_split_groups_cover_each_test_file_once():
    expected = {
        path
        for path in runner.discover_pytest_files(REPO_ROOT)
        if path.startswith(f"{runner.PR166_SF_R2_TEST_ROOT}/")
    }
    grouped = [
        path
        for group in _pr166_sf_r2_group_paths()
        for path in group
    ]
    expanded_by_phase = {
        phase: [
            path
            for command in runner.PYTEST_SHARD_COMMANDS[phase]
            if any(
                command_path.startswith(f"{runner.PR166_SF_R2_TEST_ROOT}/")
                for command_path in command.paths
            )
            for path in runner._pytest_files_for_command(command, REPO_ROOT)
        ]
        for phase in runner.PYTEST_SHARD_PHASES
    }
    expanded = [
        path
        for phase_paths in expanded_by_phase.values()
        for path in phase_paths
    ]
    idempotence_path = _pr166_sf_r2_idempotence_path()
    manifest_hits = [
        (phase, path)
        for phase, phase_paths in runner.pytest_shard_manifest(REPO_ROOT).items()
        for path in phase_paths
        if path == idempotence_path
    ]

    assert len(runner.PR166_SF_R2_PYTEST_FILE_GROUPS) == 8
    assert all(
        0 < len(group) <= 14 for group in runner.PR166_SF_R2_PYTEST_FILE_GROUPS
    )
    assert grouped == sorted(grouped)
    assert len(grouped) == len(set(grouped))
    assert set(grouped) == expected
    assert len(expanded) == len(set(expanded))
    assert sorted(expanded) == grouped
    assert expanded.count(idempotence_path) == 1
    assert idempotence_path not in expanded_by_phase["pytest-shard-2"]
    assert not expanded_by_phase["pytest-shard-2"]
    assert expanded_by_phase["pytest-shard-4"] == [idempotence_path]
    assert sorted(expanded_by_phase["pytest-shard-6"]) == sorted(
        path
        for group in _pr166_sf_r2_non_idempotence_group_paths()
        for path in group
    )
    assert manifest_hits == [("pytest-shard-4", idempotence_path)]


def test_runner_pr166_sf_r2_idempotence_is_own_early_shard4_subgroup():
    idempotence_path = _pr166_sf_r2_idempotence_path()
    placements = [
        (phase, paths)
        for phase, paths in _pr166_sf_r2_split_command_placements()
        if idempotence_path in paths
    ]
    manifest_hits = [
        (phase, path)
        for phase, phase_paths in runner.pytest_shard_manifest(REPO_ROOT).items()
        for path in phase_paths
        if path == idempotence_path
    ]

    assert placements == [("pytest-shard-4", (idempotence_path,))]
    idempotence_command = runner.PYTEST_SHARD_COMMANDS["pytest-shard-4"][1]
    assert idempotence_command.paths == (
        idempotence_path,
    )
    assert idempotence_command.bounded_idempotence is True
    assert manifest_hits == [("pytest-shard-4", idempotence_path)]


def test_runner_pr166_sm3_idempotence_is_bounded_shard7_subgroup():
    idempotence_path = _pr166_sm3_idempotence_path()
    placements = [
        (phase, command.paths)
        for phase in runner.PYTEST_SHARD_PHASES
        for command in runner.PYTEST_SHARD_COMMANDS[phase]
        if idempotence_path in runner._pytest_files_for_command(command, REPO_ROOT)
    ]
    manifest_hits = [
        (phase, path)
        for phase, phase_paths in runner.pytest_shard_manifest(REPO_ROOT).items()
        for path in phase_paths
        if path == idempotence_path
    ]

    assert placements == [("pytest-shard-7", (idempotence_path,))]
    idempotence_command = runner.PYTEST_SHARD_COMMANDS["pytest-shard-7"][1]
    assert idempotence_command.paths == (idempotence_path,)
    assert idempotence_command.bounded_idempotence is True
    assert manifest_hits == [("pytest-shard-7", idempotence_path)]


@pytest.mark.parametrize(
    "pr166_sm2_subgroup_index",
    range(len(runner.PR166_SM2_PYTEST_FILE_GROUPS)),
)
def test_runner_fails_closed_if_any_pr166_sm2_subgroup_fails(
    pr166_sm2_subgroup_index,
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = runner.build_pytest_shard_commands(
        "pytest-shard-5",
        Path(".tmp") / "pytest-basetemp",
    )
    pr166_commands = [
        command
        for command in commands
        if any(part.startswith(f"{runner.PR166_SM2_TEST_ROOT}/") for part in command)
    ]
    failing_command = pr166_commands[pr166_sm2_subgroup_index]
    failing_index = commands.index(failing_command)
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(73 if command == failing_command else 0)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands, phase="pytest-shard-5")

    assert exit_code == 73
    assert seen == commands[: failing_index + 1]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


@pytest.mark.parametrize(
    "pr166_sf_r2_subgroup_index",
    range(len(runner.PR166_SF_R2_PYTEST_FILE_GROUPS)),
)
def test_runner_fails_closed_if_any_pr166_sf_r2_subgroup_fails(
    pr166_sf_r2_subgroup_index,
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    expected_paths = _pr166_sf_r2_group_paths()[pr166_sf_r2_subgroup_index]
    placements = [
        (phase, paths)
        for phase, paths in _pr166_sf_r2_split_command_placements()
        if paths == expected_paths
    ]
    assert len(placements) == 1
    phase, failing_paths = placements[0]
    commands = runner.build_pytest_shard_commands(
        phase,
        Path(".tmp") / "pytest-basetemp",
    )
    failing_command = next(
        command
        for command in commands
        if tuple(command[2 : 2 + len(failing_paths)]) == failing_paths
    )
    failing_index = commands.index(failing_command)
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(83 if command == failing_command else 0)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands, phase=phase)

    assert exit_code == 83
    assert seen == commands[: failing_index + 1]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_rebalances_pytest_shard_3_with_stage1_legacy_group():
    commands = runner.PYTEST_SHARD_COMMANDS["pytest-shard-3"]

    assert [command.paths for command in commands] == [
        (
            "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage",
            "tests/stage1_prediction_markets/"
            "multisource_safe_nonlive_dataset_expansion_strict_qku_coverage",
            "tests/stage1_prediction_markets/"
            "nonlive_replay_paper_data_adapter_quantum_forward_bridge",
            "tests/stage1_prediction_markets/pr157_completion_materialization_bridge",
            "tests/stage1_prediction_markets/"
            "pr158_owner_response_selection_readiness_bridge",
            "tests/stage1_prediction_markets/"
            "pr159_official_source_completion_bridge",
            "tests/stage1_prediction_markets/pr159r_source_locator_value_capture",
        ),
        (
            "tests/stage1_prediction_markets/"
            "pr163_generic_paper_adapter_capture_framework",
            "tests/stage1_prediction_markets/"
            "pr164_review_provenance_qku_canonical_coverage_audit",
            "tests/stage1_prediction_markets/pr165_b_condition_scoped_negative_memory",
            "tests/stage1_prediction_markets/"
            "pr165_c_replay_paper_memory_consumer_integration",
            "tests/stage1_prediction_markets/"
            "pr165_d_scenario_qku_combination_selection",
            "tests/stage1_prediction_markets/"
            "pr165_d2_score_refreshed_scenario_selection_v2",
            "tests/stage1_prediction_markets/pr165_evidence_backed_scoring_ranking",
            "tests/stage1_prediction_markets/"
            "pr166_s_replay_paper_scenario_retest_execution",
            "tests/stage1_prediction_markets/pr166_s2_replay_paper_retest_loop_v2",
        ),
        (
            "tests/stage1_prediction_markets/qku_candidate_quality_replay_paper_prioritization",
            "tests/stage1_prediction_markets/qku_formula_algorithm_solver_market_scope_materialization",
            "tests/stage1_prediction_markets/qku_residual_candidate_assimilation",
            "tests/stage1_prediction_markets/replay_paper_executor_input_run_artifact_generation",
            "tests/stage1_prediction_markets/replay_paper_outcome_capture_scenario_learning",
            "tests/stage1_prediction_markets/safe_repo_local_nonlive_dataset_materialization_authority_gate",
            "tests/stage1_prediction_markets/source_intelligence",
            "tests/stage1_prediction_markets/test_validate_stage1_packet_schema_gate_static.py",
        ),
    ]
    assert all(command.reason for command in commands)

    expanded_paths = [
        path
        for command in commands
        for path in runner._pytest_files_for_command(command, REPO_ROOT)
    ]

    assert len(expanded_paths) == len(set(expanded_paths))
    assert set(expanded_paths) == set(
        runner.pytest_shard_manifest(REPO_ROOT)["pytest-shard-3"]
    )
    assert (
        "tests/stage1_prediction_markets/pr166_s2_replay_paper_retest_loop_v2/"
        "test_pr166_s2_exec_readiness.py"
        in runner._pytest_files_for_command(commands[1], REPO_ROOT)
    )


def test_runner_splits_pytest_shard_4_bounded_idempotence_deterministically():
    commands = runner.PYTEST_SHARD_COMMANDS["pytest-shard-4"]

    assert [command.paths for command in commands] == [
        (
            "tests/stage1_prediction_markets/pr166_sf_repair_materialization_before_retest",
            "tests/stage1_prediction_markets/pr166_sm_score_memory_refresh_from_pr166_s_results",
        ),
        (_pr166_sf_r2_idempotence_path(),),
    ]
    assert commands[1].bounded_idempotence is True
    assert all(command.reason for command in commands)

    expanded_paths = [
        path
        for command in commands
        for path in runner._pytest_files_for_command(command, REPO_ROOT)
    ]

    assert len(expanded_paths) == len(set(expanded_paths))
    assert set(expanded_paths) == set(
        runner.pytest_shard_manifest(REPO_ROOT)["pytest-shard-4"]
    )


def test_runner_splits_pytest_shard_7_current_pr_group_first():
    commands = runner.PYTEST_SHARD_COMMANDS["pytest-shard-7"]
    idempotence_path = _pr166_sm3_idempotence_path()

    assert [command.paths for command in commands] == [
        (
            "tests/stage1_prediction_markets/"
            "pr165_d3_quantum_aware_scenario_selection_v3",
        ),
        (idempotence_path,),
        (runner.PR166_SM3_TEST_ROOT,),
    ]
    assert commands[1].bounded_idempotence is True
    assert commands[2].ignores == (idempotence_path,)
    assert (
        "tests/stage1_prediction_markets/pr165_d3_quantum_aware_scenario_selection_v3/"
        "test_pr165_d3_validator.py"
        in runner._pytest_files_for_command(commands[0], REPO_ROOT)
    )
    assert idempotence_path in runner._pytest_files_for_command(
        commands[1],
        REPO_ROOT,
    )
    assert idempotence_path not in runner._pytest_files_for_command(
        commands[2],
        REPO_ROOT,
    )
    assert all(command.reason for command in commands)


def test_runner_splits_pytest_shard_8_residual_tests_deterministically():
    commands = runner.PYTEST_SHARD_COMMANDS["pytest-shard-8"]
    idempotence_path = _pr166_q_idempotence_path()
    qb_idempotence_path = _pr166_qb_idempotence_path()
    qc_idempotence_path = _pr166_qc_idempotence_path()
    pr162e_q_idempotence_path = _pr162e_q_idempotence_path()
    pr167_idempotence_path = _pr167_idempotence_path()
    pr162e_idempotence_path = _pr162e_idempotence_path()

    assert [command.paths for command in commands] == [
        (idempotence_path,),
        (runner.PR166_Q_TEST_ROOT,),
        (qb_idempotence_path,),
        (runner.PR166_QB_TEST_ROOT,),
        (qc_idempotence_path,),
        (runner.PR166_QC_TEST_ROOT,),
        (pr162e_q_idempotence_path,),
        (runner.PR162E_Q_TEST_ROOT,),
        (pr167_idempotence_path,),
        (runner.PR167_TEST_ROOT,),
        (pr162e_idempotence_path,),
        (runner.PR162E_TEST_ROOT,),
        (runner.ISOLATED_SOURCE_EVIDENCE_PYTEST,),
        (
            "tests/agent_algorithm",
            "tests/agents",
            "tests/algorithms",
            "tests/connectors",
        ),
        (
            "tests/core",
            "tests/dashboard",
            "tests/edge",
            "tests/external_repo",
            "tests/governance",
            "tests/launch",
            "tests/master_plan",
        ),
        ("tests/global_debug",),
        (
            "tests/neural_signal",
            "tests/quantum",
            "tests/replay_paper",
            "tests/replay_paper_review",
            "tests/research",
            "tests/roadmap",
        ),
        (
            "tests/runtime_cash",
            "tests/runtime_orchestration",
            "tests/runtime_resolver",
            "tests/scoring",
            "tests/selection",
            "tests/venue_neutral_prediction_adapter",
        ),
        ("tests/source_evidence",),
        (runner.ST12A_TEST_ROOT,),
    ]
    assert commands[0].bounded_idempotence is True
    assert commands[1].ignores == (idempotence_path,)
    assert commands[2].bounded_idempotence is True
    assert commands[3].ignores == (qb_idempotence_path,)
    assert commands[4].bounded_idempotence is True
    assert commands[5].ignores == (qc_idempotence_path,)
    assert commands[6].bounded_idempotence is True
    assert commands[7].ignores == (pr162e_q_idempotence_path,)
    assert commands[8].bounded_idempotence is True
    assert commands[9].ignores == (pr167_idempotence_path,)
    assert commands[10].bounded_idempotence is True
    assert commands[11].ignores == (pr162e_idempotence_path,)
    assert commands[-2].ignores == (runner.ISOLATED_SOURCE_EVIDENCE_PYTEST,)
    assert commands[-1].paths == (runner.ST12A_TEST_ROOT,)
    assert commands[-1].ignores == ()
    assert commands[-1].reason == "Complete QKU control-plane domain test root"
    assert "exact 42-file" not in commands[-1].reason
    assert all(command.reason for command in commands)
    assert ("tests",) not in [command.paths for command in commands]

    pytest_basetemp = Path(".tmp") / "pytest-basetemp"
    built_commands = [
        runner._build_pytest_command(
            command,
            pytest_basetemp,
        )
        for command in commands
    ]
    import_mode_flag = "--import-mode=importlib"
    legacy_registered_command = [
        sys.executable,
        runner._path("tools", runner.PYTEST_FRESH_BASETEMP_SCRIPT),
        runner.ST12A_TEST_ROOT,
        "-q",
        runner.PYTEST_DURATIONS_ARG,
        "--basetemp",
        str(pytest_basetemp),
    ]
    assert built_commands[-1] == legacy_registered_command
    assert all(
        not any(argument.startswith("--import-mode") for argument in built)
        for built in built_commands
    )
    assert sum(
        command.paths == (runner.ST12A_TEST_ROOT,) for command in commands
    ) == 1

    adapted = runner._execution_command_with_qku_root_importlib(
        built_commands[-1]
    )
    assert adapted.count(import_mode_flag) == 1
    import_mode_index = adapted.index(import_mode_flag)
    assert adapted[import_mode_index + 1] == "--basetemp"
    assert adapted[:import_mode_index] + adapted[import_mode_index + 1 :] == (
        built_commands[-1]
    )
    assert runner._execution_command_with_qku_root_importlib(adapted) == adapted
    with pytest.raises(
        RuntimeError,
        match="^QTT_QKU_ROOT_PYTEST_IMPORT_MODE_CONFLICT$",
    ):
        runner._execution_command_with_qku_root_importlib(
            [*built_commands[-1], "--import-mode=prepend"]
        )
    assert runner._execution_command_with_qku_root_importlib(
        built_commands[0]
    ) == built_commands[0]

    expanded_paths = [
        path
        for command in commands
        for path in runner._pytest_files_for_command(command, REPO_ROOT)
    ]

    assert expanded_paths.count(runner.ST12H_TEST_MODULE) == 1
    assert len(expanded_paths) == len(set(expanded_paths))
    assert set(expanded_paths) == set(
        runner.pytest_shard_manifest(REPO_ROOT)["pytest-shard-8"]
    )
    assert (
        "tests/global_debug/test_grand_global_debug_logical_consistency_audit.py"
        in runner._pytest_files_for_command(commands[15], REPO_ROOT)
    )


def test_runner_commands_use_sys_executable(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert commands
    assert all(command[0] == python_executable for command in commands)


def test_runner_includes_pr153_family_and_pr154_validators_after_pr152(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr152_index = command_names.index(
        "validate_grand_global_debug_logical_consistency_audit.py"
    )
    pr153_index = command_names.index(
        "validate_controlled_official_source_capture_candidate_packets.py"
    )
    pr153r_index = command_names.index(
        "validate_pr153r_redo_external_source_value_capture_targets.py"
    )
    pr153s_index = command_names.index(
        "validate_pr153s_source_value_capture_closure_classifier.py"
    )
    pr154_index = command_names.index(
        "validate_atomicrows_parameter_default_value_materialization_gate.py"
    )
    next_gate_index = command_names.index(
        "validate_qtt_agent_role_operating_charter_registry.py"
    )

    assert (
        command_names.count(
            "validate_controlled_official_source_capture_candidate_packets.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr153r_redo_external_source_value_capture_targets.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr153s_source_value_capture_closure_classifier.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_atomicrows_parameter_default_value_materialization_gate.py"
        )
        == 1
    )
    assert pr152_index < pr153_index < pr153r_index < pr153s_index < pr154_index
    assert pr154_index < next_gate_index
    assert commands[pr153_index] == [
        python_executable,
        str(Path("tools") / "validate_controlled_official_source_capture_candidate_packets.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr153r_index] == [
        python_executable,
        str(Path("tools") / "validate_pr153r_redo_external_source_value_capture_targets.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr153s_index] == [
        python_executable,
        str(Path("tools") / "validate_pr153s_source_value_capture_closure_classifier.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr154_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_parameter_default_value_materialization_gate.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr153_index]
    assert "--output" not in commands[pr153_index]
    assert "--write-report" not in commands[pr153r_index]
    assert "--output" not in commands[pr153r_index]
    assert "--write-report" not in commands[pr153s_index]
    assert "--output" not in commands[pr153s_index]
    assert "--write-report" not in commands[pr154_index]
    assert "--output" not in commands[pr154_index]


def test_runner_guidance_requires_pr152_finalization_before_validation_gates():
    guidance = runner.build_pre_validation_finalization_guidance()
    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands if len(command) > 1]

    assert guidance == [
        {
            "command_id": "pr152_currentize_after_generated_artifacts",
            "command": (
                ".\\.venv\\Scripts\\python.exe "
                "tools\\currentize_pr152_after_generated_artifacts.py"
            ),
            "when": "after final generated artifacts settle and before validation gates",
            "ci_tracked_report_mutation_allowed": False,
        }
    ]
    assert "currentize_pr152_after_generated_artifacts.py" not in command_names
    assert "validate_grand_global_debug_logical_consistency_audit.py" in command_names


def test_runner_includes_pr157_bridge_after_pr156_without_tracked_write(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr154_index = command_names.index(
        "validate_atomicrows_parameter_default_value_materialization_gate.py"
    )
    pr155_index = command_names.index(
        "validate_agent_consumable_parameter_default_registry.py"
    )
    pr156_index = command_names.index(
        "validate_agent_default_binding_universal_intake_gate.py"
    )
    pr157_index = command_names.index(
        "validate_pr157_pr154_atomicrows_completion_materialization_bridge.py"
    )
    pr158_index = command_names.index(
        "validate_pr158_owner_response_selection_readiness_bridge.py"
    )
    pr159_index = command_names.index(
        "validate_pr159_official_source_completion_bridge.py"
    )
    pr160_index = command_names.index(
        "validate_pr160_split_reclassification_route_closure.py"
    )
    pr159r_index = command_names.index(
        "validate_pr159r_source_locator_value_capture.py"
    )
    pr159s_index = command_names.index("validate_pr159s_open_intake_completion.py")
    pr161a_index = command_names.index(
        "validate_pr161a_atomicrows_pr154_value_state_materialization.py"
    )
    pr161b_index = command_names.index(
        "validate_pr161b_master_plan_residual_candidate_coverage.py"
    )
    pr161c_index = command_names.index(
        "validate_pr161c_qku_residual_candidate_assimilation.py"
    )
    pr161d_index = command_names.index(
        "validate_pr161d_qku_candidate_quality_replay_paper_prioritization.py"
    )
    pr161e_index = command_names.index(
        "validate_pr161e_replay_paper_outcome_capture_scenario_learning.py"
    )
    pr161f_index = command_names.index(
        "validate_pr161f_replay_paper_executor_input_run_artifact_generation.py"
    )
    pr162_index = command_names.index(
        "validate_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py"
    )
    pr162a_index = command_names.index(
        "validate_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py"
    )
    pr162b_index = command_names.index(
        "validate_pr162b_qku_formula_algorithm_solver_market_scope_materialization.py"
    )
    pr162c_index = command_names.index(
        "validate_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py"
    )
    pr162d_index = command_names.index(
        "validate_pr162d_aggressive_qku_candidate_materialization_agent_routing.py"
    )
    pr162r_a_index = command_names.index(
        "validate_pr162r_a_replay_paper_executability_classification_audit.py"
    )
    pr162d_r2a_index = command_names.index(
        "validate_pr162d_r2a_real_formulations.py"
    )
    pr162r_index = command_names.index(
        "validate_pr162r_generic_replay_paper_adapter_rerun.py"
    )
    pr162r_b_index = command_names.index(
        "validate_pr162r_b_replay_paper_data_binding_completion.py"
    )
    pr163_index = command_names.index(
        "validate_pr163_generic_paper_adapter_capture_framework.py"
    )
    pr163_b_index = command_names.index(
        "validate_pr163_b_paired_replay_paper_concurrent_executor.py"
    )
    pr164_index = command_names.index(
        "validate_pr164_review_provenance_qku_canonical_coverage_audit.py"
    )
    pr163_c_index = command_names.index(
        "validate_pr163_c_pretrade_infrastructure_rejection_remediation.py"
    )
    pr165_index = command_names.index(
        "validate_pr165_evidence_backed_scoring_ranking.py"
    )
    pr165_b_index = command_names.index(
        "validate_pr165_b_condition_scoped_negative_memory.py"
    )
    pr165_c_index = command_names.index(
        "validate_pr165_c_replay_paper_memory_consumer_integration.py"
    )
    pr165_d_index = command_names.index(
        "validate_pr165_d_scenario_qku_combination_selection.py"
    )
    pr166_s_index = command_names.index(
        "validate_pr166_s_replay_paper_scenario_retest_execution.py"
    )
    pr166_sm_index = command_names.index(
        "validate_pr166_sm_score_memory_refresh_from_pr166_s_results.py"
    )
    pr166_sf_index = command_names.index(
        "validate_pr166_sf_repair_materialization_before_retest.py"
    )
    pr166_s2_index = command_names.index(
        "validate_pr166_s2_replay_paper_retest_loop_v2.py"
    )
    pr166_sm2_index = command_names.index(
        "validate_pr166_sm2_score_memory_refresh_v2.py"
    )
    pr166_sf_r2_index = command_names.index(
        "validate_pr166_sf_r2_targeted_conversion_repair_retest.py"
    )
    pr166_sm3_index = command_names.index(
        "validate_pr166_sm3_score_memory_refresh_v3.py"
    )
    pr166_q_index = command_names.index(
        "validate_pr166_q_quantum_classical_hybrid_comparator.py"
    )
    pr166_qb_index = command_names.index(
        "validate_pr166_qb_bounded_quantum_benchmark.py"
    )
    pr166_qc_index = command_names.index(
        "validate_pr166_qc_quantum_selected_replay_paper_retest.py"
    )
    pr162e_q_index = command_names.index(
        "validate_pr162e_q_quantum_automapper.py"
    )
    pr167_index = command_names.index(
        "validate_pr167_open_trade_simulator_integration.py"
    )
    pr162e_plugin_index = command_names.index(
        "validate_pr162e_plugin_framework.py"
    )
    pr162e_negative_repair_index = command_names.index(
        "validate_pr162e_negative_repair_factory.py"
    )
    pr162e_no_orphan_index = command_names.index(
        "validate_pr162e_no_orphan_lineage.py"
    )
    pr165_d2_index = command_names.index(
        "validate_pr165_d2_score_refreshed_scenario_selection_v2.py"
    )
    pr165_d3_index = command_names.index(
        "validate_pr165_d3_quantum_aware_scenario_selection_v3.py"
    )
    next_gate_index = command_names.index(
        "validate_qtt_agent_role_operating_charter_registry.py"
    )

    assert (
        command_names.count(
            "validate_agent_consumable_parameter_default_registry.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_agent_default_binding_universal_intake_gate.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr157_pr154_atomicrows_completion_materialization_bridge.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr158_owner_response_selection_readiness_bridge.py"
        )
        == 1
    )
    assert (
        command_names.count("validate_pr159_official_source_completion_bridge.py")
        == 1
    )
    assert (
        command_names.count("validate_pr160_split_reclassification_route_closure.py")
        == 1
    )
    assert command_names.count("validate_pr159r_source_locator_value_capture.py") == 1
    assert command_names.count("validate_pr159s_open_intake_completion.py") == 1
    assert (
        command_names.count(
            "validate_pr161a_atomicrows_pr154_value_state_materialization.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr161b_master_plan_residual_candidate_coverage.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr161c_qku_residual_candidate_assimilation.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr161d_qku_candidate_quality_replay_paper_prioritization.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr161e_replay_paper_outcome_capture_scenario_learning.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr161f_replay_paper_executor_input_run_artifact_generation.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr162b_qku_formula_algorithm_solver_market_scope_materialization.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr162d_aggressive_qku_candidate_materialization_agent_routing.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr162r_a_replay_paper_executability_classification_audit.py"
        )
        == 1
    )
    assert command_names.count("validate_pr162d_r2a_real_formulations.py") == 1
    assert (
        command_names.count(
            "validate_pr162r_generic_replay_paper_adapter_rerun.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr162r_b_replay_paper_data_binding_completion.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr163_generic_paper_adapter_capture_framework.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr163_b_paired_replay_paper_concurrent_executor.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr164_review_provenance_qku_canonical_coverage_audit.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr163_c_pretrade_infrastructure_rejection_remediation.py"
        )
        == 1
    )
    assert (
        command_names.count("validate_pr165_evidence_backed_scoring_ranking.py")
        == 1
    )
    assert (
        command_names.count("validate_pr165_b_condition_scoped_negative_memory.py")
        == 1
    )
    assert (
        command_names.count(
            "validate_pr165_c_replay_paper_memory_consumer_integration.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr165_d_scenario_qku_combination_selection.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr166_s_replay_paper_scenario_retest_execution.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr166_sm_score_memory_refresh_from_pr166_s_results.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr166_sf_repair_materialization_before_retest.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr166_s2_replay_paper_retest_loop_v2.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr166_sm2_score_memory_refresh_v2.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr166_sf_r2_targeted_conversion_repair_retest.py"
        )
        == 1
    )
    assert command_names.count("validate_pr166_sm3_score_memory_refresh_v3.py") == 1
    assert (
        command_names.count("validate_pr166_q_quantum_classical_hybrid_comparator.py")
        == 1
    )
    assert command_names.count("validate_pr166_qb_bounded_quantum_benchmark.py") == 1
    assert (
        command_names.count(
            "validate_pr166_qc_quantum_selected_replay_paper_retest.py"
        )
        == 1
    )
    assert command_names.count("validate_pr162e_q_quantum_automapper.py") == 1
    assert command_names.count("validate_pr167_open_trade_simulator_integration.py") == 1
    assert command_names.count("validate_pr162e_plugin_framework.py") == 1
    assert command_names.count("validate_pr162e_negative_repair_factory.py") == 1
    assert command_names.count("validate_pr162e_no_orphan_lineage.py") == 1
    assert (
        command_names.count(
            "validate_pr165_d2_score_refreshed_scenario_selection_v2.py"
        )
        == 1
    )
    assert (
        command_names.count(
            "validate_pr165_d3_quantum_aware_scenario_selection_v3.py"
        )
        == 1
    )
    assert (
        pr154_index
        < pr155_index
        < pr156_index
        < pr157_index
        < pr158_index
        < pr159_index
        < pr160_index
        < pr159r_index
        < pr159s_index
        < pr161a_index
        < pr161b_index
        < pr161c_index
        < pr161d_index
        < pr161e_index
        < pr161f_index
        < pr162_index
        < pr162a_index
        < pr162b_index
        < pr162c_index
        < pr162d_index
        < pr162r_a_index
        < pr162d_r2a_index
        < pr162r_index
        < pr162r_b_index
        < pr163_index
        < pr163_b_index
        < pr164_index
        < pr163_c_index
        < pr165_index
        < pr165_b_index
        < pr165_c_index
        < pr165_d_index
        < pr166_s_index
        < pr166_sm_index
        < pr166_sf_index
        < pr166_s2_index
        < pr166_sm2_index
        < pr166_sf_r2_index
        < pr166_sm3_index
        < pr166_q_index
        < pr166_qb_index
        < pr166_qc_index
        < pr162e_q_index
        < pr167_index
        < pr162e_plugin_index
        < pr162e_negative_repair_index
        < pr162e_no_orphan_index
        < pr165_d2_index
        < pr165_d3_index
        < next_gate_index
    )
    assert commands[pr155_index] == [
        python_executable,
        str(Path("tools") / "validate_agent_consumable_parameter_default_registry.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr155_index]
    assert "--output" not in commands[pr155_index]
    assert commands[pr156_index] == [
        python_executable,
        str(Path("tools") / "validate_agent_default_binding_universal_intake_gate.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr156_index]
    assert "--output" not in commands[pr156_index]
    assert commands[pr157_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr157_pr154_atomicrows_completion_materialization_bridge.py"
        ),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr157_index]
    assert "--output" not in commands[pr157_index]
    assert commands[pr158_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr158_owner_response_selection_readiness_bridge.py"
        ),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr158_index]
    assert commands[pr159_index] == [
        python_executable,
        str(Path("tools") / "validate_pr159_official_source_completion_bridge.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr159_index]
    assert commands[pr160_index] == [
        python_executable,
        str(Path("tools") / "validate_pr160_split_reclassification_route_closure.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr160_index]
    assert "--branch" not in commands[pr160_index]
    assert "--allow-main" not in commands[pr160_index]
    assert commands[pr159r_index] == [
        python_executable,
        str(Path("tools") / "validate_pr159r_source_locator_value_capture.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr159r_index]
    assert "--branch" not in commands[pr159r_index]
    assert "--allow-main" not in commands[pr159r_index]
    assert commands[pr159s_index] == [
        python_executable,
        str(Path("tools") / "validate_pr159s_open_intake_completion.py"),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr159s_index]
    assert "--branch" not in commands[pr159s_index]
    assert "--allow-main" not in commands[pr159s_index]
    assert commands[pr161a_index] == [
        python_executable,
        str(Path("tools") / "validate_pr161a_atomicrows_pr154_value_state_materialization.py"),
        "--repo-root",
        ".",
    ]
    pr161b_index = command_names.index(
        "validate_pr161b_master_plan_residual_candidate_coverage.py"
    )
    assert commands[pr161b_index] == [
        python_executable,
        str(Path("tools") / "validate_pr161b_master_plan_residual_candidate_coverage.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr161c_index] == [
        python_executable,
        str(Path("tools") / "validate_pr161c_qku_residual_candidate_assimilation.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr161d_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr161d_qku_candidate_quality_replay_paper_prioritization.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr161e_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr161e_replay_paper_outcome_capture_scenario_learning.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr161f_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr161f_replay_paper_executor_input_run_artifact_generation.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr162_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr162_safe_nonlive_replay_paper_data_adapter_quantum_forward_bridge.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr162a_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr162a_safe_repo_local_nonlive_dataset_materialization_authority_gate.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr162b_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr162b_qku_formula_algorithm_solver_market_scope_materialization.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr162c_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr162c_multisource_safe_nonlive_dataset_expansion_strict_qku_coverage.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr162d_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr162d_aggressive_qku_candidate_materialization_agent_routing.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr162r_a_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr162r_a_replay_paper_executability_classification_audit.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr162d_r2a_index] == [
        python_executable,
        str(Path("tools") / "validate_pr162d_r2a_real_formulations.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr162r_index] == [
        python_executable,
        str(Path("tools") / "validate_pr162r_generic_replay_paper_adapter_rerun.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr162r_b_index] == [
        python_executable,
        str(Path("tools") / "validate_pr162r_b_replay_paper_data_binding_completion.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr163_index] == [
        python_executable,
        str(Path("tools") / "validate_pr163_generic_paper_adapter_capture_framework.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr163_b_index] == [
        python_executable,
        str(Path("tools") / "validate_pr163_b_paired_replay_paper_concurrent_executor.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr164_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr164_review_provenance_qku_canonical_coverage_audit.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr163_c_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr163_c_pretrade_infrastructure_rejection_remediation.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr165_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr165_evidence_backed_scoring_ranking.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr165_b_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr165_b_condition_scoped_negative_memory.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr165_c_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr165_c_replay_paper_memory_consumer_integration.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr165_d_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr165_d_scenario_qku_combination_selection.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_s_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr166_s_replay_paper_scenario_retest_execution.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_sm_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr166_sm_score_memory_refresh_from_pr166_s_results.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_sf_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr166_sf_repair_materialization_before_retest.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_s2_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr166_s2_replay_paper_retest_loop_v2.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_sm2_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr166_sm2_score_memory_refresh_v2.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_sf_r2_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr166_sf_r2_targeted_conversion_repair_retest.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_sm3_index] == [
        python_executable,
        str(Path("tools") / "validate_pr166_sm3_score_memory_refresh_v3.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_q_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr166_q_quantum_classical_hybrid_comparator.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_qb_index] == [
        python_executable,
        str(Path("tools") / "validate_pr166_qb_bounded_quantum_benchmark.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr166_qc_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr166_qc_quantum_selected_replay_paper_retest.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr162e_q_index] == [
        python_executable,
        str(Path("tools") / "validate_pr162e_q_quantum_automapper.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr167_index] == [
        python_executable,
        str(Path("tools") / "validate_pr167_open_trade_simulator_integration.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr162e_plugin_index] == [
        python_executable,
        str(Path("tools") / "validate_pr162e_plugin_framework.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr162e_negative_repair_index] == [
        python_executable,
        str(Path("tools") / "validate_pr162e_negative_repair_factory.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr162e_no_orphan_index] == [
        python_executable,
        str(Path("tools") / "validate_pr162e_no_orphan_lineage.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr165_d2_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_pr165_d2_score_refreshed_scenario_selection_v2.py"
        ),
        "--repo-root",
        ".",
    ]
    assert "--write-report" not in commands[pr161a_index]
    assert "--write-report" not in commands[pr161b_index]
    assert "--write-report" not in commands[pr161c_index]
    assert "--write-report" not in commands[pr161d_index]
    assert "--write-report" not in commands[pr161e_index]
    assert "--write-report" not in commands[pr161f_index]
    assert "--write-report" not in commands[pr162_index]
    assert "--write-report" not in commands[pr162a_index]
    assert "--write-report" not in commands[pr162b_index]
    assert "--write-report" not in commands[pr162c_index]
    assert "--write-report" not in commands[pr162d_index]
    assert "--write-report" not in commands[pr162r_a_index]
    assert "--write-report" not in commands[pr162d_r2a_index]
    assert "--write-report" not in commands[pr162r_index]
    assert "--write-report" not in commands[pr162r_b_index]
    assert "--write-report" not in commands[pr163_index]
    assert "--write-report" not in commands[pr163_b_index]
    assert "--write-report" not in commands[pr164_index]
    assert "--write-report" not in commands[pr163_c_index]
    assert "--write-report" not in commands[pr165_index]
    assert "--write-report" not in commands[pr165_b_index]
    assert "--write-report" not in commands[pr165_c_index]
    assert "--write-report" not in commands[pr165_d_index]
    assert "--write-report" not in commands[pr166_s_index]
    assert "--write-report" not in commands[pr166_sm_index]
    assert "--write-report" not in commands[pr166_s2_index]
    assert "--write-report" not in commands[pr166_sm2_index]
    assert "--write-report" not in commands[pr166_sf_r2_index]
    assert "--write-report" not in commands[pr166_sm3_index]
    assert "--write-report" not in commands[pr166_q_index]
    assert "--write-report" not in commands[pr165_d2_index]
    assert "--branch" not in commands[pr161a_index]
    assert "--branch" not in commands[pr161b_index]
    assert "--branch" not in commands[pr161c_index]
    assert "--branch" not in commands[pr161d_index]
    assert "--branch" not in commands[pr161e_index]
    assert "--branch" not in commands[pr161f_index]
    assert "--branch" not in commands[pr162_index]
    assert "--branch" not in commands[pr162a_index]
    assert "--branch" not in commands[pr162b_index]
    assert "--branch" not in commands[pr162c_index]
    assert "--branch" not in commands[pr162d_index]
    assert "--branch" not in commands[pr162d_r2a_index]
    assert "--branch" not in commands[pr162r_a_index]
    assert "--branch" not in commands[pr162r_index]
    assert "--branch" not in commands[pr162r_b_index]
    assert "--branch" not in commands[pr163_index]
    assert "--branch" not in commands[pr164_index]
    assert "--branch" not in commands[pr163_c_index]
    assert "--branch" not in commands[pr165_index]
    assert "--branch" not in commands[pr165_b_index]
    assert "--branch" not in commands[pr165_c_index]
    assert "--branch" not in commands[pr165_d_index]
    assert "--branch" not in commands[pr166_s_index]
    assert "--branch" not in commands[pr166_sm_index]
    assert "--branch" not in commands[pr166_s2_index]
    assert "--branch" not in commands[pr166_sf_r2_index]
    assert "--branch" not in commands[pr166_sm3_index]
    assert "--branch" not in commands[pr166_q_index]
    assert "--branch" not in commands[pr165_d2_index]
    assert "--allow-main" not in commands[pr161a_index]
    assert "--allow-main" not in commands[pr161b_index]
    assert "--allow-main" not in commands[pr161c_index]
    assert "--allow-main" not in commands[pr161d_index]
    assert "--allow-main" not in commands[pr161e_index]
    assert "--allow-main" not in commands[pr161f_index]
    assert "--allow-main" not in commands[pr162_index]
    assert "--allow-main" not in commands[pr162a_index]
    assert "--allow-main" not in commands[pr162b_index]
    assert "--allow-main" not in commands[pr162c_index]
    assert "--allow-main" not in commands[pr162d_index]
    assert "--allow-main" not in commands[pr162r_a_index]
    assert "--allow-main" not in commands[pr162d_r2a_index]
    assert "--allow-main" not in commands[pr162r_index]
    assert "--allow-main" not in commands[pr162r_b_index]
    assert "--allow-main" not in commands[pr163_index]
    assert "--allow-main" not in commands[pr164_index]
    assert "--allow-main" not in commands[pr163_c_index]
    assert "--allow-main" not in commands[pr165_index]
    assert "--allow-main" not in commands[pr165_b_index]
    assert "--allow-main" not in commands[pr165_c_index]
    assert "--allow-main" not in commands[pr165_d_index]
    assert "--allow-main" not in commands[pr166_s_index]
    assert "--allow-main" not in commands[pr166_sm_index]
    assert "--allow-main" not in commands[pr166_s2_index]
    assert "--allow-main" not in commands[pr166_sf_r2_index]
    assert "--allow-main" not in commands[pr166_sm3_index]
    assert "--allow-main" not in commands[pr166_q_index]
    assert "--allow-main" not in commands[pr165_d2_index]
    assert "--output" not in commands[pr158_index]
    assert "--output" not in commands[pr159_index]
    assert "--output" not in commands[pr160_index]
    assert "--output" not in commands[pr159r_index]
    assert "--output" not in commands[pr159s_index]
    assert "--output" not in commands[pr161a_index]
    assert "--output" not in commands[pr161b_index]
    assert "--output" not in commands[pr161c_index]
    assert "--output" not in commands[pr161d_index]
    assert "--output" not in commands[pr161e_index]
    assert "--output" not in commands[pr161f_index]
    assert "--output" not in commands[pr162_index]
    assert "--output" not in commands[pr162a_index]
    assert "--output" not in commands[pr162b_index]
    assert "--output" not in commands[pr162c_index]
    assert "--output" not in commands[pr162d_index]
    assert "--output" not in commands[pr162r_a_index]
    assert "--output" not in commands[pr162d_r2a_index]
    assert "--output" not in commands[pr162r_index]
    assert "--output" not in commands[pr162r_b_index]
    assert "--output" not in commands[pr163_index]
    assert "--output" not in commands[pr163_b_index]
    assert "--output" not in commands[pr164_index]
    assert "--output" not in commands[pr163_c_index]
    assert "--output" not in commands[pr165_b_index]
    assert "--output" not in commands[pr165_c_index]
    assert "--output" not in commands[pr165_d_index]
    assert "--output" not in commands[pr166_s_index]
    assert "--output" not in commands[pr166_sm_index]
    assert "--output" not in commands[pr166_s2_index]
    assert "--output" not in commands[pr166_sf_r2_index]
    assert "--output" not in commands[pr166_sm3_index]
    assert "--output" not in commands[pr166_q_index]
    assert "--output" not in commands[pr165_d2_index]


def test_runner_validates_pr138_without_tracked_artifact_writer(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    pr138_mutating_commands = [
        command
        for command in commands
        if command[1] == str(Path("tools") / "stage1_atomicrows_semantic_row_contract_gate.py")
    ]
    pr138_non_mutating_commands = [
        command
        for command in commands
        if command[1] == "-c"
        and command[2] == runner.PR138_NON_MUTATING_VALIDATION_SCRIPT
    ]

    assert pr138_mutating_commands == []
    assert pr138_non_mutating_commands == [
        [
            python_executable,
            "-c",
            runner.PR138_NON_MUTATING_VALIDATION_SCRIPT,
        ]
    ]
    assert "--write-report" not in pr138_non_mutating_commands[0]


def test_runner_runs_pr140_gate_before_tracked_generated_report_writers(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    scope_index = command_names.index("validate_first_pr_scope.py")
    pr138_index = next(
        index
        for index, command in enumerate(commands)
        if command[1] == "-c"
        and command[2] == runner.PR138_NON_MUTATING_VALIDATION_SCRIPT
    )
    pr139_index = command_names.index(
        "validate_atomicrows_row_family_source_manifest_currentization.py"
    )
    pr140_index = command_names.index(
        "validate_atomicrows_semantic_field_coverage_enrichment_plan.py"
    )
    pr141_index = command_names.index(
        "validate_atomicrows_semantic_value_materialization_owner_authorization_gate.py"
    )
    pr142_index = command_names.index(
        "validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py"
    )
    owner_override_index = command_names.index(
        "validate_qtt_owner_global_override_authority.py"
    )

    assert (
        scope_index
        < pr138_index
        < pr139_index
        < pr140_index
        < pr141_index
        < pr142_index
        < owner_override_index
    )
    assert commands[pr139_index][-2:] == [
        "--out",
        str(
            runner._default_validation_dir()
            / "AtomicRowsRowFamilySourceManifestCurrentization.report.json"
        ),
    ]
    assert commands[pr140_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_semantic_field_coverage_enrichment_plan.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr141_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_semantic_value_materialization_owner_authorization_gate.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[pr142_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py"
        ),
        "--repo-root",
        ".",
    ]


def test_runner_routes_generated_report_outputs_to_validation_temp(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    validation_dir = Path("validation-dir")
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands(
        validation_dir,
        Path("pytest-basetemp"),
    )

    tracked_prefixes = (
        "docs/master_plan/generated/",
        "docs/roadmap/generated/",
        "docs/master_plan/source_evidence/generated/",
    )
    for command in commands:
        for token in command:
            normalized = str(token).replace("\\", "/")
            assert not normalized.startswith(tracked_prefixes)

    command_by_name = {Path(command[1]).name: command for command in commands}
    owner_override_command = command_by_name[
        "validate_qtt_owner_global_override_authority.py"
    ]
    assert owner_override_command[-2:] == [
        "--out",
        str(
            validation_dir
            / "master_plan_generated"
            / "QTTOwnerGlobalOverrideAuthority.report.json"
        ),
    ]
    assert "--check-only" in command_by_name[
        "validate_source_evidence_retrieval_executor.py"
    ]
    assert "--check-only" in command_by_name["validate_source_evidence_acceptance.py"]
    assert "--check-only" in command_by_name[
        "validate_source_revalidation_scheduler.py"
    ]
    assert "--check-only" in command_by_name[
        "validate_connector_semantic_binding_implementation_gate.py"
    ]
    assert "--check-only" in command_by_name[
        "runtime_cash_component_field_map_validate.py"
    ]
    assert "--check-only" in command_by_name[
        "private_state_read_receipt_gate_validate.py"
    ]
    assert "--write-artifacts" not in command_by_name[
        "validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py"
    ]


def test_runner_allows_routed_temp_generated_report_to_differ_from_tracked_by_default(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    with tempfile.TemporaryDirectory(prefix="qtt_pr146_runner_test_") as temp_dir:
        repo_root = Path(temp_dir)
        tracked_report = (
            repo_root
            / "docs"
            / "master_plan"
            / "generated"
            / "QTTOwnerGlobalOverrideAuthority.report.json"
        )
        temp_report = (
            repo_root
            / "validation"
            / "master_plan_generated"
            / "QTTOwnerGlobalOverrideAuthority.report.json"
        )
        tracked_report.parent.mkdir(parents=True)
        temp_report.parent.mkdir(parents=True)
        tracked_report.write_text('{"value": "tracked"}\n', encoding="utf-8")
        temp_report.write_text('{"value": "expected"}\n', encoding="utf-8")

        def fake_run(command: list[str], **kwargs) -> Completed:
            return Completed()

        monkeypatch.setattr(runner.subprocess, "run", fake_run)

        exit_code = runner.run_commands(
            [
                [
                    "python",
                    str(
                        Path("tools")
                        / "validate_qtt_owner_global_override_authority.py"
                    ),
                    "--out",
                    str(temp_report),
                ]
            ],
            repo_root=repo_root,
        )
        tracked_text = tracked_report.read_text(encoding="utf-8")

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "TRACKED_GENERATED_REPORT_STALE" not in captured.err
    assert tracked_text == '{"value": "tracked"}\n'


def test_runner_ignores_volatile_branch_context_when_comparing_temp_report(
    monkeypatch,
):
    class Completed:
        def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = ""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    with tempfile.TemporaryDirectory(prefix="qtt_pr146_runner_test_") as temp_dir:
        repo_root = Path(temp_dir)
        tracked_report = (
            repo_root
            / "docs"
            / "master_plan"
            / "generated"
            / "QTTOwnerGlobalOverrideAuthority.report.json"
        )
        temp_report = (
            repo_root
            / "validation"
            / "master_plan_generated"
            / "QTTOwnerGlobalOverrideAuthority.report.json"
        )
        tracked_report.parent.mkdir(parents=True)
        temp_report.parent.mkdir(parents=True)
        tracked_report.write_text(
            '{"base_head": "old", "branch": "original", "value": "same"}\n',
            encoding="utf-8",
        )
        temp_report.write_text(
            '{"base_head": "new", "branch": "downstream", "value": "same"}\n',
            encoding="utf-8",
        )

        def fake_run(command: list[str], **kwargs) -> Completed:
            return Completed()

        monkeypatch.setattr(runner.subprocess, "run", fake_run)
        monkeypatch.setitem(
            runner.GENERATED_REPORT_CURRENTNESS_OUTPUT_ARGS,
            "validate_qtt_owner_global_override_authority.py",
            (
                "--out",
                "docs/master_plan/generated/QTTOwnerGlobalOverrideAuthority.report.json",
            ),
        )

        exit_code = runner.run_commands(
            [
                [
                    "python",
                    str(
                        Path("tools")
                        / "validate_qtt_owner_global_override_authority.py"
                    ),
                    "--out",
                    str(temp_report),
                ]
            ],
            repo_root=repo_root,
        )

    assert exit_code == 0


@pytest.mark.parametrize(
    ("command_returncode", "expected_returncode"),
    ((0, 0), (7, 7)),
)
def test_runner_restores_new_generated_untracked_outputs_at_terminal_boundaries(
    monkeypatch,
    command_returncode,
    expected_returncode,
):
    class Completed:
        def __init__(self, returncode: int):
            self.returncode = returncode
            self.stdout = ""
            self.stderr = ""

    with tempfile.TemporaryDirectory(prefix="qtt_gate_containment_") as temp_dir:
        repo_root = Path(temp_dir)
        preexisting_generated_rel = (
            "docs/master_plan/generated/Preexisting.report.json"
        )
        preexisting_other_rel = "local-notes.txt"
        new_generated_rel = (
            "docs/master_plan/generated/pr168_gfp_shards/"
            "GeneratedDuringGate.report.shard_0001.json"
        )
        new_workspace_output_rel = (
            ".tmp/qtt_stack_runs/deterministic_run/manifest.json"
        )
        paths = {
            relative: repo_root / relative
            for relative in (
                preexisting_generated_rel,
                preexisting_other_rel,
                new_generated_rel,
                new_workspace_output_rel,
            )
        }
        for relative in (preexisting_generated_rel, preexisting_other_rel):
            paths[relative].parent.mkdir(parents=True, exist_ok=True)
            paths[relative].write_text("preserve\n", encoding="utf-8")

        def current_untracked(_repo_root):
            return {
                relative for relative, path in paths.items() if path.is_file()
            }

        def fake_run(command, **kwargs):
            paths[new_generated_rel].parent.mkdir(parents=True, exist_ok=True)
            paths[new_generated_rel].write_text("generated\n", encoding="utf-8")
            paths[new_workspace_output_rel].parent.mkdir(parents=True, exist_ok=True)
            paths[new_workspace_output_rel].write_text(
                "workspace output\n",
                encoding="utf-8",
            )
            return Completed(command_returncode)

        monkeypatch.setattr(runner, "_tracked_modified_paths", lambda repo_root: set())
        monkeypatch.setattr(runner, "_untracked_paths", current_untracked)
        monkeypatch.setattr(runner.subprocess, "run", fake_run)

        commands = [["python", "tools/example_gate.py"]]
        plan = runner._prepare_execution_plan(commands)
        paths[new_generated_rel].parent.mkdir(parents=True, exist_ok=True)
        observe = lambda: tuple(sorted(current_untracked(repo_root) - {new_workspace_output_rel}))
        candidate = _synthetic_candidate_custody_v1(repo_root, plan, observed_paths=observe, effects=(new_generated_rel,))
        exit_code = runner.run_commands(commands, repo_root=repo_root, execution_plan=plan, candidate_custody=candidate)

        assert exit_code == expected_returncode
        assert paths[preexisting_generated_rel].read_text(encoding="utf-8") == (
            "preserve\n"
        )
        assert paths[preexisting_other_rel].read_text(encoding="utf-8") == (
            "preserve\n"
        )
        assert not paths[new_generated_rel].exists()
        assert paths[new_workspace_output_rel].read_text(encoding="utf-8") == (
            "workspace output\n"
        )


def test_runner_fails_closed_without_removing_new_untracked_output_outside_prefix(
    monkeypatch,
    capsys,
):
    class Completed:
        returncode = 0
        stdout = ""
        stderr = ""

    with tempfile.TemporaryDirectory(prefix="qtt_gate_containment_") as temp_dir:
        repo_root = Path(temp_dir)
        preexisting_rel = "preexisting.txt"
        unexpected_rel = "unexpected.txt"
        paths = {
            relative: repo_root / relative
            for relative in (preexisting_rel, unexpected_rel)
        }
        paths[preexisting_rel].write_text("preserve\n", encoding="utf-8")

        def current_untracked(_repo_root):
            return {
                relative for relative, path in paths.items() if path.is_file()
            }

        def fake_run(command, **kwargs):
            paths[unexpected_rel].write_text("diagnostic\n", encoding="utf-8")
            return Completed()

        monkeypatch.setattr(runner, "_tracked_modified_paths", lambda repo_root: set())
        monkeypatch.setattr(runner, "_untracked_paths", current_untracked)
        monkeypatch.setattr(runner.subprocess, "run", fake_run)

        commands = [["python", "tools/example_gate.py"]]
        plan = runner._prepare_execution_plan(commands)
        observe = lambda: tuple(sorted(current_untracked(repo_root)))
        candidate = _synthetic_candidate_custody_v1(repo_root, plan, observed_paths=observe, effects=())
        exit_code = runner.run_commands(commands, repo_root=repo_root, execution_plan=plan, candidate_custody=candidate)

        assert exit_code == 1
        assert paths[preexisting_rel].read_text(encoding="utf-8") == "preserve\n"
        assert paths[unexpected_rel].read_text(encoding="utf-8") == "diagnostic\n"
        assert (
            "VALIDATION_CANDIDATE_UNADMITTED_EFFECT: "
            "unexpected.txt"
        ) in capsys.readouterr().err

    # A mixed invalid batch must preserve even the generated diagnostic prefix.
    with tempfile.TemporaryDirectory(prefix="qtt_gate_batch_") as temp_dir:
        root = Path(temp_dir)
        generated = root / "docs/master_plan/generated/first.json"
        generated.parent.mkdir(parents=True)
        generated.write_bytes(b"retained diagnostic")
        other = root / "outside.txt"
        other.write_bytes(b"outside diagnostic")
        with monkeypatch.context() as scoped:
            scoped.setattr(runner, "_untracked_paths", lambda _: {
                "docs/master_plan/generated/first.json", "outside.txt"
            })
            with pytest.raises(RuntimeError, match="OUTSIDE_GENERATED_PREFIX"):
                runner._restore_untracked_gate_side_effects(root, set())
        assert generated.read_bytes() == b"retained diagnostic"
        assert other.read_bytes() == b"outside diagnostic"

    # All candidate leaf types are checked before any unlink in the batch.
    with tempfile.TemporaryDirectory(prefix="qtt_gate_kinds_") as temp_dir:
        root = Path(temp_dir)
        generated = root / "docs/master_plan/generated/first.json"
        generated.parent.mkdir(parents=True)
        generated.write_bytes(b"retained diagnostic")
        directory = generated.parent / "last.json"
        directory.mkdir()
        with monkeypatch.context() as scoped:
            scoped.setattr(runner, "_untracked_paths", lambda _: {
                "docs/master_plan/generated/first.json",
                "docs/master_plan/generated/last.json"
            })
            with pytest.raises(RuntimeError, match="GENERATED_OUTPUT_NOT_FILE"):
                runner._restore_untracked_gate_side_effects(root, set())
        assert generated.read_bytes() == b"retained diagnostic"
        assert directory.is_dir()

    # Reparse admission is tested without requiring Windows symlink privilege.
    import stat as file_stat
    with tempfile.TemporaryDirectory(prefix="qtt_gate_reparse_") as temp_dir:
        root = Path(temp_dir)
        generated = root / "docs/master_plan/generated/alias.json"
        generated.parent.mkdir(parents=True)
        generated.write_bytes(b"retained diagnostic")
        original_lstat = Path.lstat
        for selected in (generated, generated.parent):
            def observed(path, *args, **kwargs):
                value = original_lstat(path, *args, **kwargs)
                if path == selected:
                    return SimpleNamespace(
                        st_mode=value.st_mode,
                        st_file_attributes=getattr(file_stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400),
                    )
                return value
            with monkeypatch.context() as scoped:
                scoped.setattr(Path, "lstat", observed)
                with pytest.raises(RuntimeError, match="UNSAFE_GENERATED_OUTPUT_PATH"):
                    runner._generated_gate_output_path(root, "docs/master_plan/generated/alias.json")
        assert generated.read_bytes() == b"retained diagnostic"



def test_generated_gate_output_path_rejects_nonportable_or_escaping_paths(
    tmp_path,
):
    invalid_paths = (
        "docs/master_plan/generated/../outside.json",
        "/docs/master_plan/generated/output.json",
        r"docs\master_plan\generated\CON.json",
        r"docs\master_plan\generated\CONIN$.json",
        r"docs\master_plan\generated\CONOUT$.json",
        r"docs\master_plan\generated\CLOCK$.json",
        "docs/master_plan/generated/" + chr(127) + "control.json",
        "docs/master_plan/generated/output.json:stream",
        *(
            f"docs/master_plan/generated/invalid{character}name.json"
            for character in '<>:"|?*'
        ),
        "docs/master_plan/generated/trailing-space.json ",
        "docs/master_plan/generated/trailing-dot.json.",
        r"C:\repo\docs\master_plan\generated\output.json",
        r"\\server\share\docs\master_plan\generated\output.json",
    )
    for path_text in invalid_paths:
        with pytest.raises(
            RuntimeError,
            match="VALIDATION_GATE_UNSAFE_GENERATED_OUTPUT_PATH",
        ):
            runner._generated_gate_output_path(tmp_path, path_text)

    valid_paths = (
        "CONTEXT.json",
        "CONIN$foo.json",
        "CONOUT$foo.json",
        "CLOCKWORK.json",
        "COM10.json",
        "LPT10.json",
        "Unicode-\N{SNOWMAN}.json",
    )
    for filename in valid_paths:
        path_text = f"docs/master_plan/generated/{filename}"
        assert runner._generated_gate_output_path(
            tmp_path,
            path_text,
        ) == (
            tmp_path
            / "docs"
            / "master_plan"
            / "generated"
            / filename
        ).resolve()


def test_validation_workspace_output_path_uses_exact_cross_platform_boundary():
    cases = (
        (".tmp/qtt_stack_runs/run/manifest.json", True),
        (r".tmp\qtt-validation-timing\phase.json", True),
        (".tmp/CONTEXT.json", True),
        (".tmp/CONIN$foo.json", True),
        (".tmp/CONOUT$foo.json", True),
        (".tmp/CLOCKWORK.json", True),
        (".tmp/COM10.json", True),
        (".tmp/LPT10.json", True),
        (".tmp-other/output.json", False),
        (".tmp/../output.json", False),
        (".tmp/CON.json", False),
        (".tmp/CONIN$.json", False),
        (".tmp/CONOUT$.json", False),
        (".tmp/CLOCK$.json", False),
        (".tmp/trailing./output.json", False),
        (r"C:\repo\.tmp\output.json", False),
        (r"\\server\share\.tmp\output.json", False),
        (".tmp/a:b", False),
        (".tmp/\x7fcontrol.json", False),
        *(
            (f".tmp/name{character}.json", False)
            for character in '<>:"|?*'
        ),
    )
    for path_text, expected in cases:
        assert (
            runner._is_validation_workspace_output_path(path_text) is expected
        ), path_text


def test_runner_restores_only_runtime_side_effects_before_pr142_pr143_and_final_pytest(
    monkeypatch, capsys, tmp_path, _central_supervision_test_adapter,
):
    import stat
    _exercise_preflight_observation_v1(tmp_path, monkeypatch)
    _exercise_preflight_candidate_debits_v1(tmp_path, monkeypatch)
    _exercise_preflight_transport_v1(tmp_path, monkeypatch, capsys)
    class Completed:
        returncode = 0
        stderr = ""
        def __init__(self, stdout=""):
            self.stdout = stdout
    intended_repair_paths = ("tools/run_validation_gates.py", "tests/fail_closed/test_run_validation_gates.py")
    generated_side_effect_paths = ("docs/master_plan/generated/GateSideEffect.report.json",
                                  "tests/fixtures/atomicrows/synthetic_gate_side_effect.v1.fixture.json")
    root = tmp_path / "candidate-repo"
    root.mkdir()
    repo_root = root
    assert repo_root.is_absolute()
    assert repo_root.is_dir()
    assert not (repo_root / ".git").exists()
    paths = (*intended_repair_paths, *generated_side_effect_paths, "unowned/keep.txt", "mapper-fixture.json")
    candidate_bytes = {path: ("working-candidate:" + path).encode() for path in paths}
    candidate_bytes["mapper-fixture.json"] = b"{}\n"
    for path, data in candidate_bytes.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    index = root / "synthetic-index"
    index.write_bytes(b"synthetic staged state differs from working bytes")
    commands = runner.build_validation_commands(Path("validation-dir"), Path("pytest-basetemp"))
    original_vectors = tuple(tuple(command) for command in commands)
    plan = runner._prepare_execution_plan(commands)
    events = []
    observations = []
    timeline = []
    activity = ["acquisition"]

    def observed_paths():
        return tuple(sorted(path.relative_to(root).as_posix() for path in root.rglob("*")
                            if path.is_file() and path != index))

    def independent_surface():
        # Read the actual fixture surface independently of the candidate's map.
        assert set(observed_paths()) == set(paths)
        rows = []
        for relative in sorted(paths):
            path = root / relative
            info = path.lstat()
            assert stat.S_ISREG(info.st_mode) and info.st_nlink == 1
            assert not (getattr(info, "st_file_attributes", 0) & 0x400)
            rows.append((relative, "FILE", stat.S_IMODE(info.st_mode), path.read_bytes()))
        assert index.read_bytes() == b"synthetic staged state differs from working bytes"
        return tuple(rows)

    original_surface = independent_surface()
    original_snapshot = runner._ValidationCandidateCustodyV1._snapshot

    def observed_snapshot(owner, selected_paths, *, baseline=False):
        if owner.root != root:
            return original_snapshot(owner, selected_paths, baseline=baseline)
        before = independent_surface()
        actual = original_snapshot(owner, selected_paths, baseline=baseline)
        after = independent_surface()
        assert before == after
        assert actual == {path: (mode, data) for path, kind, mode, data in after}
        observation = (activity[0], baseline, after)
        observations.append(observation)
        timeline.append(("observation", observation))
        return actual

    monkeypatch.setattr(runner._ValidationCandidateCustodyV1, "_snapshot", observed_snapshot)
    fixture_deadline = runner.time.monotonic_ns() + 60_000_000_000
    restoration_observations = []

    def observed_restore():
        activity[0] = ("restoration", len(restoration_observations))
        start = len(observations)
        before = independent_surface()
        try:
            restored = original_restore()
            after = independent_surface()
        finally:
            activity[0] = "occurrence"
        selected = observations[start:]
        # Both original owner observations must occur, even for an empty plan.
        assert len(selected) == 2 and all(row[1] is False for row in selected)
        assert selected[0][2] == before and selected[1][2] == after == original_surface
        assert {path for path, _, mode, data in before
                if (mode, data) != candidate.baseline[path]} == set(restored)
        assert set(restored) <= set(generated_side_effect_paths)
        restoration_observations.append((before, after, tuple(restored)))
        timeline.append(("restoration_complete", tuple(restored)))
        if restored:
            events.append(("restore", restored))
        return restored
    def fake_run(command, **kwargs):
        assert command[0] != "git", "HEAD/index restoration is forbidden"
        assert timeline[0] == ("observation", ("acquisition", True, original_surface))
        timeline.append(("child", tuple(command)))
        events.append(("gate", command))
        for path in generated_side_effect_paths:
            (root / path).write_bytes(b"synthetic permitted validation output")
        return Completed(_st12h_mock_terminal_output(command))
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(runner, "_routed_generated_output_currentness_failures", lambda command, repo_root: [])
    # This complete synthetic launch belongs only to the existing simulated
    # orchestration case. It supplies no capacity or builder-read authority to
    # an authentic campaign, and every original command vector is retained.
    from tools import pr168_rp5a_git_grep_scanner as scan_owner

    run_paths, probe = reliability.resolve_validation_run_paths(
        root, explicit_process_root=tmp_path / "synthetic-launch-parent",
        run_id="run_test_supervision_active",
        projected_relative_paths=("command-1.json",),
    )
    scratch = run_paths.process_root / "scan-input"
    scratch.mkdir()
    limits = reliability._ScanRunReadLimits(100_000, 1_000, 16, 1)
    immutable_names = (*intended_repair_paths, "unowned/keep.txt")
    surfaces = tuple(reliability._ScanCandidateSurface(
        name, "FILE", next(mode for path, kind, mode, raw in original_surface if path == name), candidate_bytes[name], (),
    ) for name in immutable_names)
    fence = reliability._ScanCandidateFence(
        root, surfaces, limits=limits, candidate_read_bytes=100_000,
        deadline_ns=fixture_deadline,
    )
    capacity_calls = []
    issued_inputs = []
    reader_inputs = []

    def synthetic_capacity(original_paths, phase, expected_plan):
        assert original_paths is run_paths and phase == runner.ALL_PHASE
        capacity_calls.append(expected_plan)
        selected = tuple(row for row in expected_plan
                         if runner._scan_full_builder_argv(row.argv))
        assert len(selected) == 1
        selected_entry = selected[0]
        git_executable = str(Path(shutil.which("git")).resolve())
        profile = reliability._Rp5aScanProfile(
            run_paths.run_id, selected_entry.command_index, str(root), str(scratch),
            immutable_names, len(immutable_names),
            sum(len(name.encode("utf-8")) + 1 for name in immutable_names),
            tuple((name, len(candidate_bytes[name])) for name in immutable_names),
            git_executable, git_executable, "git",
            tuple(scan_owner._scan_child_environment(os.environ).items()),
            100_000, 100_000, 4096, 100_000, fixture_deadline, 3,
        )
        identity = reliability._ScanLaunchIdentity(
            run_paths.run_id, phase, selected_entry.command_index,
            len(expected_plan), selected_entry.argv, str(root),
        )
        original_input = reliability._ScanLaunchInput(
            identity, surfaces, limits=limits, candidate_read_bytes=100_000,
            deadline_ns=fixture_deadline, scratch_root=scratch,
            scratch_bytes=100_000, parent_frame_reread_bytes=100_000,
            check_candidate=fence,
        )
        issued_inputs.append(original_input)
        return _extend_synthetic_reader_launch_v1(
            reliability._prepare_scan_launch(
            run_paths, phase=phase, plan=expected_plan,
            profiles={selected_entry.command_index: profile},
            read_limits=limits, deadline_ns=fixture_deadline,
            launch_inputs={selected_entry.command_index: original_input},
        ), issued_inputs, reader_inputs)

    original_supervise_fixture = runner._execute_supervised_command
    consumed_inputs = []

    def supervise_fixture(command, **kwargs):
        original_input = kwargs.get("launch_input")
        if original_input is None:
            return original_supervise_fixture(command, **kwargs)
        if original_input not in reader_inputs:
            assert original_input is issued_inputs[0]
        stream = original_input._claim(
            run_id=kwargs["run_id"], phase=kwargs["phase"],
            command_index=kwargs["command_index"], argv=tuple(command),
            cwd=kwargs["cwd"],
        )
        # The existing process adapter is synthetic; label its lifecycle too.
        process = SimpleNamespace(pid=4321, returncode=None)
        process.poll = lambda: process.returncode
        original_input._attached(process)
        captured_frame = stream.read(original_input.extent + 1)
        assert len(captured_frame) == original_input.extent
        receipt = original_supervise_fixture(command, **kwargs)
        process.returncode = receipt.native_exit_code
        original_input._finished(process, receipt.native_exit_code)
        if original_input not in reader_inputs:
            consumed_inputs.append(original_input)
        return receipt

    with monkeypatch.context() as publication:
        for name, value in (
            ("_RUN_COMMANDS_ACTIVE_PATHS", run_paths),
            ("_ACTIVE_FILESYSTEM_PROBE", probe),
            ("_RUN_PROVENANCE_ATTEMPTED", False),
            ("_RUN_PROVENANCE_WRITTEN", False),
            ("_SCAN_CAPACITY_ATTEMPTED", False),
            ("_ACTIVE_SCAN_LAUNCH", None),
            ("_ACTIVE_SCAN_CAPACITY_SOURCE", synthetic_capacity),
            ("_LAST_EXPECTED_COMMAND_PLAN", ()),
            ("_LAST_PLANNED_COMMAND_COUNT", None),
            ("_MAPPER_READ_SOURCE_ATTEMPTED", False),
            ("_ACTIVE_MAPPER_READ_PROFILES_V1", None),
            ("_ACTIVE_MAPPER_OCCURRENCES_V1", {}),
            ("write_run_provenance", reliability.write_run_provenance),
            ("_execute_supervised_command", supervise_fixture),
        ):
            publication.setattr(runner, name, value)
        suppliers = _central_supervision_test_adapter(scan_source=synthetic_capacity,
            resolve_paths=False, deadline_ns=fixture_deadline, patcher=publication)
        publication.setattr(runner, "_ACTIVE_SCAN_CAPACITY_SOURCE", suppliers["scan_capacity_source"])
        publication.setattr(runner, "_ACTIVE_MAPPER_READ_SOURCE_V1", suppliers["mapper_read_source"])
        runner._publish_active_plan_provenance(runner.ALL_PHASE, plan)
        candidate = _synthetic_candidate_custody_v1(root, runner._LAST_EXPECTED_COMMAND_PLAN,
            observed_paths=observed_paths, effects=generated_side_effect_paths, index_path=index,
            deadline_ns=fixture_deadline)
        assert observations == [("acquisition", True, original_surface)]
        activity[0] = "occurrence"
        original_restore = candidate.restore
        candidate.restore = observed_restore
        assert len(capacity_calls) == 1
        assert capacity_calls[0] is runner._LAST_EXPECTED_COMMAND_PLAN
        exit_code = runner.run_commands(commands, repo_root=root, execution_plan=plan, candidate_custody=candidate)
        assert consumed_inputs == issued_inputs and len(consumed_inputs) == 1
        assert consumed_inputs[0].state == "CLOSED"
        assert reader_inputs and all(value.state == "CLOSED" for value in reader_inputs)
        assert list(scratch.iterdir()) == []
    assert exit_code == 0
    assert all((root / path).read_bytes() == data for path, data in candidate_bytes.items())
    assert index.read_bytes() == b"synthetic staged state differs from working bytes"
    assert all(path not in restored for kind, restored in events if kind == "restore" for path in intended_repair_paths)
    selected_scripts = {runner.PR142_HANDOFF_READINESS_VALIDATOR_SCRIPT,
                        runner.PR143_OWNER_OVERRIDE_CURRENTIZATION_VALIDATOR_SCRIPT}
    expected_occurrences = tuple((index, vector) for index, vector in enumerate(original_vectors)
                                 if Path(vector[1]).name in selected_scripts)
    assert len(expected_occurrences) == 2
    pr142_command = next(command for command in commands
                        if Path(command[1]).name == runner.PR142_HANDOFF_READINESS_VALIDATOR_SCRIPT)
    pr143_command = next(command for command in commands
                        if Path(command[1]).name == runner.PR143_OWNER_OVERRIDE_CURRENTIZATION_VALIDATOR_SCRIPT)

    def assert_original_command_occurrences(recorded):
        gates = [(position, tuple(vector)) for position, (kind, vector) in enumerate(recorded) if kind == "gate"]
        assert len(gates) == len(original_vectors)
        for ordinal, expected in expected_occurrences:
            position, vector = gates[ordinal]
            assert vector == expected
            assert recorded[position - 1][0] == "restore"
        assert [vector for _, vector in gates if Path(vector[1]).name in selected_scripts] == [
            vector for _, vector in expected_occurrences]

    assert_original_command_occurrences(events)
    # The script name alone cannot conceal a changed operand or missing occurrence.
    for ordinal, expected in expected_occurrences:
        changed = list(events)
        position = [i for i, event in enumerate(changed) if event[0] == "gate"][ordinal]
        changed[position] = ("gate", [*expected, "--unapproved-argument"])
        with pytest.raises(AssertionError):
            assert_original_command_occurrences(changed)
        with pytest.raises(AssertionError):
            assert_original_command_occurrences(events[:position] + events[position + 1:])
    # The registered plan is distinct from the dispatched execution projection.
    # This finite fixture is the retained 367-occurrence unsplit plan, not the
    # real 450/449 campaign. The fake child changes both admitted files each time.
    assert len(original_vectors) == len(plan) == 367
    assert tuple(entry.registered_argv for entry in plan) == original_vectors
    expected_script_positions = {
        "validate_atomicrows_semantic_value_materialization_authorization_handoff_readiness_gate.py": (9,),
        "validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py": (11,),
        "run_pytest_fresh_basetemp.py": (366, 367),
    }
    for script, expected_positions in expected_script_positions.items():
        assert tuple(i for i, vector in enumerate(original_vectors, 1)
                     if len(vector) > 1 and Path(vector[1]).name == script) == expected_positions

    effect_names = tuple(sorted(generated_side_effect_paths, key=lambda p: (p.casefold(), p)))
    dirty_surface = tuple((path, kind, mode,
                           b"synthetic permitted validation output" if path in effect_names else data)
                          for path, kind, mode, data in original_surface)
    expected_events = []
    expected_observations = [("acquisition", True, original_surface)]
    expected_timeline = [("observation", expected_observations[0])]
    expected_restorations = []
    expected_checkpoints = []
    dirty = False

    def expect_restoration(checkpoint):
        nonlocal dirty
        before = dirty_surface if dirty else original_surface
        restored = effect_names if dirty else ()
        tag = ("restoration", len(expected_restorations))
        for surface in (before, original_surface):
            observation = (tag, False, surface)
            expected_observations.append(observation)
            expected_timeline.append(("observation", observation))
        expected_timeline.append(("restoration_complete", restored))
        expected_restorations.append((before, original_surface, restored))
        expected_checkpoints.append(checkpoint)
        if restored:
            expected_events.append(("restore", restored))
        dirty = False

    # Normative barrier selection is independent of the implementation predicate.
    for ordinal, entry in enumerate(plan, 1):
        if ordinal in (9, 11, 366, 367):
            expect_restoration(("before", ordinal))
        before = dirty_surface if dirty else original_surface
        observed_before = ("occurrence", False, before)
        expected_observations.append(observed_before)
        expected_timeline.append(("observation", observed_before))
        expected_timeline.append(("child", tuple(entry.execution_argv)))
        expected_events.append(("gate", list(entry.execution_argv)))
        dirty = True
        observed_after = ("occurrence", False, dirty_surface)
        expected_observations.append(observed_after)
        expected_timeline.append(("observation", observed_after))
        if ordinal in (366, 367):
            expect_restoration(("after", ordinal))
    expect_restoration(("final", None))

    assert expected_checkpoints == [
        ("before", 9), ("before", 11), ("before", 366),
        ("after", 366), ("before", 367), ("after", 367), ("final", None),
    ]
    assert events == expected_events
    assert observations == expected_observations
    assert restoration_observations == expected_restorations
    assert timeline == expected_timeline
    restore_positions = [i for i, event in enumerate(events) if event[0] == "restore"]
    assert restore_positions == [8, 11, 367, 369, 371]
    assert len(restore_positions) == 5
    restore_indices = restore_positions
    assert events[restore_indices[0] + 1] == ("gate", pr142_command)
    assert events[restore_indices[1] + 1] == ("gate", pr143_command)
    for restore_position, (_, expected) in zip(restore_positions[:2], expected_occurrences, strict=True):
        assert events[restore_position + 1] == ("gate", list(expected))
    assert events[restore_positions[2] + 1] == ("gate", commands[-2])
    assert events[restore_positions[3] - 1] == ("gate", commands[-2])
    assert events[restore_positions[3] + 1] == ("gate", commands[-1])
    assert events[-2] == ("gate", commands[-1])
    assert all(set(events[i][1]) == set(generated_side_effect_paths) for i in restore_positions)
    assert events[-1][0] == "restore" and candidate.state == "RESTORED_VERIFIED"
    assert len(restoration_observations) == 7
    assert [bool(restored) for _, _, restored in restoration_observations] == [
        True, True, True, True, False, True, False,
    ]
    assert all(after == original_surface for _, after, _ in restoration_observations)
    assert len([row for row in observations if isinstance(row[0], tuple)]) == 14
    assert timeline[-1] == ("restoration_complete", ())

    # Finite copied observations only: no additional child, restore, or campaign.
    from copy import deepcopy
    expected_trace = (expected_events, expected_observations,
                      expected_restorations, expected_timeline)
    assert (events, observations, restoration_observations, timeline) == expected_trace
    invalid_traces = []
    for checkpoint_index in (2, 4, 6):
        altered = deepcopy(expected_trace)
        tag = ("restoration", checkpoint_index)
        altered[1][:] = [row for row in altered[1] if row[0] != tag]
        start = next(i for i, row in enumerate(altered[3])
                     if row[0] == "observation" and row[1][0] == tag)
        del altered[3][start:start + 3]
        del altered[2][checkpoint_index]
        if checkpoint_index == 2:
            del altered[0][367]  # Lose the nonempty pre366 barrier too.
        invalid_traces.append(altered)
    # Merge adjacent post366/pre367 into one pair, with subsequent tags renumbered.
    merged = deepcopy(expected_trace)
    merge_tag = ("restoration", 4)
    merged[1][:] = [row for row in merged[1] if row[0] != merge_tag]
    start = next(i for i, row in enumerate(merged[3])
                 if row[0] == "observation" and row[1][0] == merge_tag)
    del merged[3][start:start + 3]
    del merged[2][4]
    for i, row in enumerate(merged[1]):
        if isinstance(row[0], tuple) and row[0][1] > 4:
            merged[1][i] = (("restoration", row[0][1] - 1), row[1], row[2])
    for i, row in enumerate(merged[3]):
        if row[0] == "observation" and isinstance(row[1][0], tuple) and row[1][0][1] > 4:
            observed = row[1]
            merged[3][i] = ("observation", (("restoration", observed[0][1] - 1), observed[1], observed[2]))
    invalid_traces.append(merged)
    reordered = deepcopy(expected_trace)
    reordered[1][1], reordered[1][2] = reordered[1][2], reordered[1][1]
    invalid_traces.append(reordered)
    unowned = deepcopy(expected_trace)
    unowned[0][8] = ("restore", (*effect_names, "unowned/keep.txt"))
    unowned[2][0] = (dirty_surface, original_surface, (*effect_names, "unowned/keep.txt"))
    invalid_traces.append(unowned)
    changed_vector = deepcopy(expected_trace)
    gate_position = next(i for i, row in enumerate(changed_vector[0]) if row[0] == "gate")
    changed_vector[0][gate_position][1].append("--unapproved-argument")
    invalid_traces.append(changed_vector)
    missing_occurrence = deepcopy(expected_trace)
    del missing_occurrence[0][gate_position]
    invalid_traces.append(missing_occurrence)
    for altered in invalid_traces:
        with pytest.raises(AssertionError):
            assert altered == expected_trace

    assert independent_surface() == original_surface
    assert capsys.readouterr().out.splitlines()[-1] == runner.SUCCESS_MARKER
    repo_root = root

    # A pre-command restoration failure must not be retried by finish().
    with monkeypatch.context() as scoped:
        attempted = []
        spawned = []
        def failed_restore(*args):
            attempted.append("tracked")
            raise RuntimeError("synthetic restoration failure")
        scoped.setattr(runner, "_tracked_modified_paths", lambda _: set())
        scoped.setattr(runner, "_untracked_paths", lambda _: set())
        scoped.setattr(runner, "_restore_tracked_gate_side_effects", failed_restore)
        scoped.setattr(runner, "_execute_supervised_command", lambda *a, **k: spawned.append(a))
        scoped.setattr(runner, "_st12h_scratch_budget_failures", lambda _: [])
        result = runner.run_commands(
            [["python", "tools/run_pytest_fresh_basetemp.py", "tests/example.py"]],
            repo_root=tmp_path,
        )
        assert result == 1
        assert attempted == ["tracked"]
        assert spawned == []
        assert "prior restoration failure; not retried" in capsys.readouterr().err
    _exercise_candidate_custody_failures_v1(tmp_path, monkeypatch)

    # Append separate finite caller faults; the complete 367-occurrence trace
    # above is unchanged. No native child or extra campaign is used here.
    for fault in ("unproven", "exception", "group", "cancel", "system-exit", "base-group",
                  "context-exit", "missing", "shape", "bool-pid", "bool-exit", "unknown",
                  "conflicting-proof", "run", "phase", "index", "argv", "cwd", "proven-timeout"):
        fault_root = tmp_path / ("retention-" + fault)
        fault_root.mkdir()
        (fault_root / "source.py").write_bytes(b"original source\n")
        (fault_root / "output.json").write_bytes(b"original output\n")
        fault_index = fault_root / "index"
        fault_index.write_bytes(b"original index\n")
        fault_commands = ((sys.executable, "tools/first_gate.py"),
                          (sys.executable, "tools/next_gate.py"))
        fault_plan = runner._prepare_execution_plan(fault_commands)
        fault_candidate = _synthetic_candidate_custody_v1(
            fault_root, fault_plan, observed_paths=lambda: ("source.py", "output.json"),
            effects=("output.json",), index_path=fault_index,
        )
        fault_paths, fault_probe = reliability.resolve_validation_run_paths(
            fault_root, explicit_process_root=tmp_path / ("retention-parent-" + fault),
            run_id="run_retention_" + fault,
        )
        caller_events, emitted, deletions, returned = [], [], [], []
        original_begin = fault_candidate.begin_occurrence
        original_end = fault_candidate.end_occurrence
        original_restore = fault_candidate.restore

        def begin_fault(index, entry, **kwargs):
            caller_events.append(("begin", index))
            return original_begin(index, entry, **kwargs)

        def end_fault(index, entry):
            caller_events.append(("end", index))
            return original_end(index, entry)

        def restore_fault():
            caller_events.append(("restore", None))
            return original_restore()

        fault_candidate.begin_occurrence = begin_fault
        fault_candidate.end_occurrence = end_fault
        fault_candidate.restore = restore_fault
        original_error = reliability.ValidationReliabilityError(
            "ENGVR_PROCESS_TERMINATION_FAILED", "synthetic original unresolved child",
        )
        original_error.owned_process = SimpleNamespace(pid=7822)
        raised = {
            "exception": original_error,
            "group": ExceptionGroup("outer", [ExceptionGroup("inner", [original_error])]),
            "cancel": KeyboardInterrupt("original interruption"),
            "system-exit": SystemExit(23),
            "base-group": BaseExceptionGroup("cancel and child", [KeyboardInterrupt(), original_error]),
            "context-exit": RuntimeError("original context exit failed"),
        }.get(fault)

        class ExitFailure:
            def __enter__(self):
                return None

            def __exit__(self, *args):
                caller_events.append(("context-exit", 1))
                raise raised

        def supervise_fault(command, **kwargs):
            caller_events.append(("supervise", kwargs["command_index"]))
            assert fault_candidate.active_occurrence == 1
            (fault_root / "output.json").write_bytes(b"child effect\n")
            if raised is not None and fault != "context-exit":
                raise raised
            receipt = reliability.CommandExecutionReceiptV1(
                schema_version=1, run_id=kwargs["run_id"], phase=kwargs["phase"],
                command_index=kwargs["command_index"], argv=tuple(command), cwd=str(kwargs["cwd"]),
                pid=7822, platform="nt", start_time_utc="2026-08-24T00:00:00Z",
                end_time_utc="2026-08-24T00:00:01Z", elapsed_monotonic_seconds=1.0,
                native_exit_code=0, start_failure_class=None, timeout_seconds_or_null=None,
                timeout_state="NOT_CONFIGURED", termination_state="NOT_REQUIRED",
                stdout_path=str(fault_paths.evidence_root / "command-1.stdout.bin"),
                stderr_path=str(fault_paths.evidence_root / "command-1.stderr.bin"),
                stdout_byte_count=0, stderr_byte_count=0, stdout_required_markers=(),
                stdout_marker_state="NOT_REQUIRED", stderr_was_nonempty=False, failure_class=None,
            )
            changes = {
                "unproven": {"termination_state": "TASKKILL_T:128;TERMINAL:UNPROVEN",
                             "failure_class": "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED"},
                "bool-pid": {"pid": True}, "bool-exit": {"native_exit_code": False},
                "unknown": {"termination_state": "UNKNOWN"},
                "conflicting-proof": {"termination_state": "TERMINAL:UNPROVEN;TERMINAL:PROVEN"},
                "run": {"run_id": "different_run"}, "phase": {"phase": "different-phase"},
                "index": {"command_index": 2}, "argv": {"argv": (*tuple(command), "--different")},
                "cwd": {"cwd": str(tmp_path)},
                "proven-timeout": {"native_exit_code": 1, "failure_class": "ENGVR_PROCESS_TIMEOUT",
                    "timeout_seconds_or_null": 1.0, "timeout_state": "TRIGGERED",
                    "termination_state": "TASKKILL_T:0;TERMINAL:PROVEN"},
            }.get(fault, {})
            receipt = replace(receipt, **changes)
            if fault == "missing":
                receipt = None
            elif fault == "shape":
                receipt = SimpleNamespace(pid=7822, native_exit_code=0)
            returned.append(receipt)
            return receipt

        with monkeypatch.context() as fault_patch:
            fault_patch.setattr(runner, "_RUN_COMMANDS_SUPERVISION", None)
            fault_patch.setattr(runner, "_RUN_PROVENANCE_WRITTEN", False)
            fault_patch.setattr(runner, "_ACTIVE_SCAN_LAUNCH", None)
            fault_patch.setattr(runner, "_execute_supervised_command", supervise_fault)
            fault_patch.setattr(runner, "atomic_write_json", lambda path, value: emitted.append((path.name, value)))
            fault_patch.setattr(runner, "cleanup_validation_run",
                                lambda paths: deletions.append(paths) or "PASS_REMOVED_EXACT_RUN_ROOT")
            if fault == "context-exit":
                original_nullcontext = runner.nullcontext
                context_calls = []
                def fail_original_launch_context(*args, **kwargs):
                    context_calls.append((args, kwargs))
                    return ExitFailure() if len(context_calls) == 1 else original_nullcontext(*args, **kwargs)
                fault_patch.setattr(runner, "nullcontext", fail_original_launch_context)
            if fault == "proven-timeout":
                fault_patch.setattr(runner, "_st12h_command_contract", lambda argv: (1.0, ()))
            call = lambda: runner.run_commands(
                fault_commands, repo_root=fault_root, phase=runner.FAST_PREFLIGHT_PHASE,
                run_paths=fault_paths, execution_plan=fault_plan, candidate_custody=fault_candidate,
            )
            if fault in {"group", "cancel", "system-exit", "base-group"}:
                with pytest.raises(type(raised)) as caught:
                    call()
                assert caught.value is raised
            else:
                assert call() == 1
            pending = runner._RUN_COMMANDS_SUPERVISION
            if raised is not None:
                assert pending["errors"][0] is raised
            retained = runner._LAST_COMMAND_RECEIPTS
            assert len(retained) == (1 if returned and type(returned[0]) is reliability.CommandExecutionReceiptV1 else 0)
            if retained:
                assert retained[0] is returned[0]
            if fault == "proven-timeout":
                assert pending["pending"] is False
                assert caller_events == [("begin", 1), ("supervise", 1), ("end", 1), ("restore", None)]
                assert fault_candidate.active_occurrence is None
                assert (fault_root / "output.json").read_bytes() == b"original output\n"
            else:
                assert pending["pending"] is True
                assert caller_events == [("begin", 1), ("supervise", 1)] + (
                    [("context-exit", 1)] if fault == "context-exit" else [])
                if fault == "context-exit":
                    assert context_calls == [((), {}), ((), {})]
                assert fault_candidate.active_occurrence == 1
                assert (fault_root / "output.json").read_bytes() == b"child effect\n"
                with pytest.raises(RuntimeError, match="VALIDATION_CANDIDATE_CHILD_STILL_OWNED"):
                    original_restore()
                assert runner.run_commands(fault_commands, run_paths=fault_paths) == 1
                assert runner._RUN_COMMANDS_SUPERVISION is pending
            final_result, cleanup, completion = runner._finalize_validation_run(
                run_paths=fault_paths, probe=fault_probe, phase=runner.FAST_PREFLIGHT_PHASE,
                planned_count=2, expected_plan=runner._LAST_EXPECTED_COMMAND_PLAN,
                receipts=retained, result=1, text_state="PASS",
            )
            assert final_result == 1 and completion.final_state == "FAIL"
            if fault == "proven-timeout":
                assert deletions == [fault_paths] and cleanup == "PASS_REMOVED_EXACT_RUN_ROOT"
            else:
                assert deletions == [] and cleanup == "SKIPPED_PROCESS_TERMINATION_UNPROVEN"
                assert fault_paths.process_root.is_dir()
                assert emitted[0][1]["cleanup_state"] == "SKIPPED_PROCESS_TERMINATION_UNPROVEN"
                assert runner._RUN_COMMANDS_SUPERVISION is pending and pending["pending"] is True
            assert (fault_root / "source.py").read_bytes() == b"original source\n"
            assert fault_index.read_bytes() == b"original index\n"
        capsys.readouterr()



def test_runner_preserves_initially_modified_files_after_final_pytest(
    monkeypatch,
):
    class Completed:
        returncode = 0
        stdout = ""
        stderr = ""

    with tempfile.TemporaryDirectory(prefix="qtt_pr162r_runner_test_") as temp_dir:
        repo_root = Path(temp_dir)
        report_rel = (
            "docs/master_plan/generated/"
            "PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
        )
        report_path = repo_root / report_rel
        report_path.parent.mkdir(parents=True)
        report_path.write_text("updated\n", encoding="utf-8")
        modified_sets = iter([{report_rel}, {report_rel}, set(), {report_rel}])

        def fake_run(command: list[str], **kwargs) -> Completed:
            report_path.write_text("head\n", encoding="utf-8")
            return Completed()

        monkeypatch.setattr(
            runner, "_tracked_modified_paths", lambda repo_root: next(modified_sets)
        )
        monkeypatch.setattr(runner, "_untracked_paths", lambda repo_root: set())
        monkeypatch.setattr(runner.subprocess, "run", fake_run)
        monkeypatch.setattr(
            runner,
            "_routed_generated_output_currentness_failures",
            lambda command, repo_root: [],
        )

        command = [
            runner.sys.executable,
            str(Path("tools") / runner.PYTEST_FRESH_BASETEMP_SCRIPT),
        ]
        commands = [command]
        plan = runner._prepare_execution_plan(commands)
        candidate = _synthetic_candidate_custody_v1(repo_root, plan,
            observed_paths=lambda: (report_rel,), effects=(report_rel,))
        assert runner.run_commands(commands, repo_root=repo_root,
            execution_plan=plan, candidate_custody=candidate) == 0
        assert report_path.read_text(encoding="utf-8") == "updated\n"


def test_runner_includes_qtt_pr_identity_roster_validator(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    active_registry_index = command_names.index(
        "validate_qtt_active_non_sha_day1_gate_state_registry_contract.py"
    )
    roster_index = command_names.index("validate_qtt_pr_identity_roster.py")
    controller_index = command_names.index(
        "validate_qtt_roadmap_execution_state_controller.py"
    )
    pr100_index = command_names.index(
        "validate_atomicrows_bundle_sha_freeze_authority_gate.py"
    )

    assert active_registry_index < roster_index < controller_index < pr100_index
    assert commands[roster_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_pr_identity_roster.py"),
        "--report-out",
        _default_temp_generated_report("QttPrIdentityRoster.report.json"),
    ]


def test_runner_includes_pr130_private_state_receipt_gate_after_runtime_cash(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    runtime_cash_index = command_names.index("runtime_cash_component_field_map_validate.py")
    private_state_index = command_names.index("private_state_read_receipt_gate_validate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert runtime_cash_index < private_state_index < no_runtime_index
    assert commands[private_state_index] == [
        python_executable,
        str(Path("tools") / "private_state_read_receipt_gate_validate.py"),
        "--repo-root",
        ".",
        "--check-only",
    ]


def test_runner_includes_pr131_credential_readiness_gate_after_private_state(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    private_state_index = command_names.index("private_state_read_receipt_gate_validate.py")
    credential_index = command_names.index(
        "credential_alias_secret_no_capture_readiness_validate.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert private_state_index < credential_index < no_runtime_index
    assert commands[credential_index] == [
        python_executable,
        str(Path("tools") / "credential_alias_secret_no_capture_readiness_validate.py"),
        "--repo-root",
        ".",
        "--check-only",
    ]


def test_runner_includes_pr132_market_data_ingest_after_pr131_credential_readiness(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    credential_index = command_names.index(
        "credential_alias_secret_no_capture_readiness_validate.py"
    )
    market_data_index = command_names.index(
        "venue_market_data_ingest_adapters_validate.py"
    )
    connector_index = command_names.index("validate_connector_capability_static.py")

    assert credential_index < market_data_index < connector_index
    assert commands[market_data_index] == [
        python_executable,
        str(Path("tools") / "venue_market_data_ingest_adapters_validate.py"),
        "--repo-root",
        ".",
        "--check-only",
    ]


def test_runner_includes_pr133_snapshot_builder_after_pr132_market_data_ingest(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    market_data_index = command_names.index(
        "venue_market_data_ingest_adapters_validate.py"
    )
    snapshot_index = command_names.index(
        "orderbook_event_state_snapshot_builder_validate.py"
    )
    runtime_resolver_index = command_names.index(
        "runtime_resolver_snapshot_executor_validate.py"
    )
    policy_drift_index = command_names.index(
        "validate_historical_dataset_policy_literal_drift.py"
    )
    historical_dataset_index = command_names.index(
        "validate_historical_dataset_digest_and_loader.py"
    )
    pr136_policy_drift_index = command_names.index(
        "validate_pr136_roadmap_policy_literal_drift.py"
    )
    pr136_roadmap_index = command_names.index(
        "validate_pr136_day1_launch_readiness_roadmap.py"
    )
    pr137_integrity_index = command_names.index(
        "validate_pr137_generated_integrity_authority_boundary.py"
    )
    pr137_controller_index = command_names.index(
        "validate_pr137_launch_readiness_dependency_controller.py"
    )
    connector_index = command_names.index("validate_connector_capability_static.py")

    assert (
        market_data_index
        < snapshot_index
        < runtime_resolver_index
        < policy_drift_index
        < historical_dataset_index
        < pr136_policy_drift_index
        < pr136_roadmap_index
        < pr137_integrity_index
        < pr137_controller_index
        < connector_index
    )
    assert commands[snapshot_index] == [
        python_executable,
        str(Path("tools") / "orderbook_event_state_snapshot_builder_validate.py"),
        "--repo-root",
        ".",
        "--check-only",
    ]
    assert commands[runtime_resolver_index] == [
        python_executable,
        str(Path("tools") / "runtime_resolver_snapshot_executor_validate.py"),
        "--repo-root",
        ".",
        "--check-only",
    ]
    assert commands[policy_drift_index] == [
        python_executable,
        str(Path("tools") / "validate_historical_dataset_policy_literal_drift.py"),
        "--repo-root",
        ".",
    ]
    assert commands[historical_dataset_index] == [
        python_executable,
        str(Path("tools") / "validate_historical_dataset_digest_and_loader.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr136_policy_drift_index] == [
        python_executable,
        str(Path("tools") / "validate_pr136_roadmap_policy_literal_drift.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr136_roadmap_index] == [
        python_executable,
        str(Path("tools") / "validate_pr136_day1_launch_readiness_roadmap.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr137_integrity_index] == [
        python_executable,
        str(Path("tools") / "validate_pr137_generated_integrity_authority_boundary.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr137_controller_index] == [
        python_executable,
        str(Path("tools") / "validate_pr137_launch_readiness_dependency_controller.py"),
        "--repo-root",
        ".",
    ]


def test_runner_includes_pr137_validators_after_pr136_and_before_downstream_static_gates(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr136_policy_drift_index = command_names.index(
        "validate_pr136_roadmap_policy_literal_drift.py"
    )
    pr136_roadmap_index = command_names.index(
        "validate_pr136_day1_launch_readiness_roadmap.py"
    )
    pr137_integrity_index = command_names.index(
        "validate_pr137_generated_integrity_authority_boundary.py"
    )
    pr137_controller_index = command_names.index(
        "validate_pr137_launch_readiness_dependency_controller.py"
    )
    connector_index = command_names.index("validate_connector_capability_static.py")

    assert command_names.count("validate_pr137_generated_integrity_authority_boundary.py") == 1
    assert command_names.count("validate_pr137_launch_readiness_dependency_controller.py") == 1
    assert (
        pr136_policy_drift_index
        < pr136_roadmap_index
        < pr137_integrity_index
        < pr137_controller_index
        < connector_index
    )
    assert commands[pr137_integrity_index] == [
        python_executable,
        str(Path("tools") / "validate_pr137_generated_integrity_authority_boundary.py"),
        "--repo-root",
        ".",
    ]
    assert commands[pr137_controller_index] == [
        python_executable,
        str(Path("tools") / "validate_pr137_launch_readiness_dependency_controller.py"),
        "--repo-root",
        ".",
    ]


def test_cumulative_gate_calls_validate_historical_dataset_digest_and_loader(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]

    assert "validate_historical_dataset_digest_and_loader.py" in command_names


def test_cumulative_gate_calls_policy_literal_drift_validator(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]

    assert "validate_historical_dataset_policy_literal_drift.py" in command_names


def test_cumulative_gate_calls_pr136_validator(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]

    assert "validate_pr136_day1_launch_readiness_roadmap.py" in command_names


def test_cumulative_gate_calls_pr136_policy_literal_drift_validator(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    command_names = [Path(command[1]).name for command in runner.build_validation_commands()]

    assert "validate_pr136_roadmap_policy_literal_drift.py" in command_names


def _assert_pr135_gate_failure_stops(monkeypatch, capsys, failing_name: str) -> None:
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_historical_dataset_policy_literal_drift.py"],
        ["python", "validate_historical_dataset_digest_and_loader.py"],
        ["python", "later_gate.py"],
    ]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(51 if command[1] == failing_name else 0)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 51
    assert seen == commands[: len(seen)]
    assert seen[-1][1] == failing_name
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_cumulative_gate_fails_when_pr135_report_missing(monkeypatch, capsys):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def test_cumulative_gate_fails_when_pr135_schema_invalid(monkeypatch, capsys):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def test_cumulative_gate_fails_when_pr135_marker_absent(monkeypatch, capsys):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def test_cumulative_gate_fails_when_validator_emits_marker_with_forbidden_authority_flag(
    monkeypatch, capsys
):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def test_cumulative_gate_fails_when_owner_verified_placeholders_remain(
    monkeypatch, capsys
):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def test_cumulative_gate_fails_when_policy_literal_drift_exists(monkeypatch, capsys):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_policy_literal_drift.py"
    )


def test_cumulative_gate_fails_when_atomicrows_bundle_or_sha_diff_exists(
    monkeypatch, capsys
):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def test_cumulative_gate_fails_when_master_plan_diff_exists_for_unauthorized_edit(
    monkeypatch, capsys
):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def test_cumulative_gate_fails_when_repo_pr135_maps_to_roadmap_pr135(
    monkeypatch, capsys
):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def test_cumulative_gate_fails_when_source_acceptance_or_connector_binding_appears(
    monkeypatch, capsys
):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def test_cumulative_gate_fails_when_quantum_execution_or_optimizer_input_appears(
    monkeypatch, capsys
):
    _assert_pr135_gate_failure_stops(
        monkeypatch, capsys, "validate_historical_dataset_digest_and_loader.py"
    )


def _assert_pr136_gate_failure_stops(monkeypatch, capsys, failing_name: str) -> None:
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_pr136_roadmap_policy_literal_drift.py"],
        ["python", "validate_pr136_day1_launch_readiness_roadmap.py"],
        ["python", "later_gate.py"],
    ]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(61 if command[1] == failing_name else 0)

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 61
    assert seen[-1][1] == failing_name
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_cumulative_gate_fails_when_pr136_reports_missing(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_pr136_marker_absent(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_pr135_currentization_missing(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_same_number_inference_true(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_domain_count_hardcoded_to_13(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_roadmap_policy_literal_drift.py"
    )


def test_cumulative_gate_fails_when_arbitrary_domain_count_forced(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_fixed_13_domain_model_used(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_roadmap_policy_literal_drift.py"
    )


def test_cumulative_gate_fails_when_derived_domain_evidence_missing(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_provisional_pr_unclassified(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_classification_evidence_missing(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_domain_map_missing_entry(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_dependency_graph_cycle_exists(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_market_scope_missing(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_atomicrows_bundle_sha_diff_exists(
    monkeypatch, capsys
):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_master_plan_diff_exists(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_source_or_connector_authority_created(
    monkeypatch, capsys
):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_replay_paper_order_profit_live_authority_created(
    monkeypatch, capsys
):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_quantum_execution_or_advantage_claim_created(
    monkeypatch, capsys
):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_agent_authority_escalates(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_live_hot_path_accepts_control_plane_call(
    monkeypatch, capsys
):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_cumulative_gate_fails_when_day1_launch_marked_started(monkeypatch, capsys):
    _assert_pr136_gate_failure_stops(
        monkeypatch, capsys, "validate_pr136_day1_launch_readiness_roadmap.py"
    )


def test_runner_fails_closed_if_pr134_runtime_resolver_snapshot_executor_fails(
    monkeypatch,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "orderbook_event_state_snapshot_builder_validate.py"],
        ["python", "runtime_resolver_snapshot_executor_validate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 1, 0]
    seen = []

    def fake_run(command, cwd=None):
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 1
    assert seen == commands[:2]


def test_runner_fails_closed_if_pr131_credential_readiness_gate_fails(monkeypatch, capsys):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "private_state_read_receipt_gate_validate.py"],
        ["python", "credential_alias_secret_no_capture_readiness_validate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 41, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 41
    assert seen == commands[:2]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_fails_closed_if_pr132_market_data_ingest_gate_fails(monkeypatch, capsys):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "credential_alias_secret_no_capture_readiness_validate.py"],
        ["python", "venue_market_data_ingest_adapters_validate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 42, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 42
    assert seen == commands[:2]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_fails_closed_if_pr133_snapshot_builder_gate_fails(monkeypatch, capsys):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "venue_market_data_ingest_adapters_validate.py"],
        ["python", "orderbook_event_state_snapshot_builder_validate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 43, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 43
    assert seen == commands[:2]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_invokes_pytest_through_fresh_basetemp_helper(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    pytest_basetemp = Path(".tmp") / "run_validation_gates_pytest_123"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands(pytest_basetemp=pytest_basetemp)

    assert commands[-1] == [
        python_executable,
        str(Path("tools") / "run_pytest_fresh_basetemp.py"),
        "tests",
        "-q",
        "--ignore",
        str(
            Path("tests")
            / "source_evidence"
            / "test_controlled_official_source_capture_candidate_packets.py"
        ),
        runner.PYTEST_DURATIONS_ARG,
        "--basetemp",
        str(pytest_basetemp),
    ]


def test_runner_includes_owner_global_override_authority_dev_gate(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    scope_index = command_names.index("validate_first_pr_scope.py")
    owner_override_index = command_names.index(
        "validate_qtt_owner_global_override_authority.py"
    )
    owner_override_currentization_index = command_names.index(
        "validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py"
    )
    agent_charter_index = command_names.index(
        "validate_qtt_agent_role_operating_charter_registry.py"
    )
    algorithm_registry_index = command_names.index(
        "validate_qtt_algorithm_formula_family_registry.py"
    )
    agent_algorithm_binding_index = command_names.index(
        "validate_qtt_agent_algorithm_binding_registry.py"
    )
    agent_algorithm_consumer_gate_index = command_names.index(
        "validate_qtt_agent_algorithm_consumer_gate.py"
    )
    agent_algorithm_cumulative_readiness_index = command_names.index(
        "validate_qtt_agent_algorithm_cumulative_readiness_gate.py"
    )
    agent_algorithm_command_matrix_index = command_names.index(
        "validate_qtt_agent_algorithm_command_matrix.py"
    )
    source_evidence_index = command_names.index("validate_source_evidence_static.py")

    assert (
        scope_index
        < owner_override_index
        < owner_override_currentization_index
        < agent_charter_index
        < algorithm_registry_index
        < agent_algorithm_binding_index
        < agent_algorithm_consumer_gate_index
        < agent_algorithm_cumulative_readiness_index
        < agent_algorithm_command_matrix_index
        < source_evidence_index
    )
    assert commands[owner_override_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_owner_global_override_authority.py"),
        "--mode",
        "dev",
        "--repo-root",
        ".",
        "--out",
        _default_temp_generated_report("QTTOwnerGlobalOverrideAuthority.report.json"),
    ]
    assert commands[owner_override_currentization_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_qtt_owner_global_override_directive_currentization_and_internal_gate_release.py"
        ),
        "--repo-root",
        ".",
    ]
    assert commands[agent_charter_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_agent_role_operating_charter_registry.py"),
        "--mode",
        "dev",
        "--repo-root",
        ".",
        "--out",
        _default_temp_generated_report("QTTAgentRoleOperatingCharterReport.json"),
    ]
    assert commands[algorithm_registry_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_algorithm_formula_family_registry.py"),
        "--mode",
        "dev",
        "--repo-root",
        ".",
        "--out",
        _default_temp_generated_report("QTTAlgorithmFormulaFamilyReport.json"),
    ]
    assert commands[agent_algorithm_binding_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_agent_algorithm_binding_registry.py"),
        "--mode",
        "dev",
        "--repo-root",
        ".",
        "--out",
        _default_temp_generated_report("QTTAgentAlgorithmBindingReport.json"),
    ]
    assert commands[agent_algorithm_consumer_gate_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_agent_algorithm_consumer_gate.py"),
        "--mode",
        "dev",
        "--repo-root",
        ".",
        "--out",
        _default_temp_generated_report("QTTAgentAlgorithmConsumerGate.report.json"),
    ]
    assert commands[agent_algorithm_cumulative_readiness_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_agent_algorithm_cumulative_readiness_gate.py"),
        "--mode",
        "dev",
        "--repo-root",
        ".",
        "--out",
        _default_temp_generated_report(
            "QTTAgentAlgorithmCumulativeReadinessGate.report.json"
        ),
    ]
    assert commands[agent_algorithm_command_matrix_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_agent_algorithm_command_matrix.py"),
        "--out",
        _default_temp_generated_report("QTTAgentAlgorithmCommandMatrix.json"),
    ]


def test_runner_exposes_agent_algorithm_command_matrix_success_marker():
    assert command_matrix_gate.SUCCESS_MARKER == "QTT_AGENT_ALGORITHM_COMMAND_MATRIX_OK"


def test_runner_exposes_atomicrows_research_provenance_success_marker():
    assert (
        research_provenance_gate.SUCCESS_MARKER
        == "ATOMICROWS_RESEARCH_PROVENANCE_EVIDENCE_TIER_CLASSIFICATION_OK"
    )


def test_runner_exposes_owner_submitted_research_source_intake_success_marker():
    assert (
        owner_intake_gate.SUCCESS_MARKER
        == "ATOMICROWS_OWNER_SUBMITTED_RESEARCH_SOURCE_INTAKE_REGISTRY_OK"
    )


def test_runner_exposes_research_source_to_candidate_family_gate_success_marker():
    assert (
        candidate_family_gate.SUCCESS_MARKER
        == "ATOMICROWS_RESEARCH_SOURCE_TO_CANDIDATE_FAMILY_GATE_OK"
    )


def test_runner_exposes_parameter_stack_role_taxonomy_success_marker():
    assert (
        parameter_stack_role_gate.SUCCESS_MARKER
        == "ATOMICROWS_PARAMETER_STACK_ROLE_TAXONOMY_OK"
    )


def test_runner_exposes_parameter_stack_completeness_gate_success_marker():
    assert (
        parameter_stack_completeness_gate.SUCCESS_MARKER
        == "ATOMICROWS_PARAMETER_STACK_COMPLETENESS_GATE_OK"
    )


def test_runner_exposes_parameter_stack_compatibility_gate_success_marker():
    assert (
        parameter_stack_compatibility_gate.SUCCESS_MARKER
        == "ATOMICROWS_PARAMETER_STACK_COMPATIBILITY_GATE_OK"
    )


def test_runner_exposes_edge_parameter_stack_selection_packet_success_marker():
    assert edge_packet_gate.SUCCESS_MARKER == "EDGE_PARAMETER_STACK_SELECTION_PACKET_SCHEMA_OK"


def test_runner_exposes_qtt_trade_context_packet_success_marker():
    assert trade_context_gate.SUCCESS_MARKER == "QTT_TRADE_CONTEXT_PACKET_SCHEMA_OK"


def test_runner_exposes_parameter_selection_universe_consumer_gate_success_marker():
    assert (
        selection_universe_consumer_gate.SUCCESS_MARKER
        == "ATOMICROWS_PARAMETER_SELECTION_UNIVERSE_CONSUMER_GATE_OK"
    )


def test_runner_exposes_trade_context_selection_universe_routing_gate_success_marker():
    assert (
        trade_context_routing_gate.SUCCESS_MARKER
        == "QTT_TRADE_CONTEXT_SELECTION_UNIVERSE_ROUTING_GATE_OK"
    )


def test_runner_exposes_quantum_applicability_classification_registry_success_marker():
    assert (
        quantum_applicability_gate.SUCCESS_MARKER
        == "QTT_QUANTUM_APPLICABILITY_CLASSIFICATION_REGISTRY_OK"
    )


def test_runner_exposes_owner_quantum_priority_policy_registry_success_marker():
    assert (
        owner_quantum_priority_gate.SUCCESS_MARKER
        == "QTT_OWNER_QUANTUM_PRIORITY_POLICY_REGISTRY_OK"
    )


def test_runner_exposes_parameter_algorithm_scoring_policy_registry_success_marker():
    assert (
        scoring_policy_gate.SUCCESS_MARKER
        == "QTT_PARAMETER_AND_ALGORITHM_SCORING_POLICY_REGISTRY_OK"
    )


def test_runner_exposes_parameter_stack_scoring_and_ranking_gate_success_marker():
    assert (
        stack_scoring_gate.SUCCESS_MARKER
        == "QTT_PARAMETER_STACK_SCORING_AND_RANKING_GATE_OK"
    )


def test_runner_exposes_quantum_classical_optimizer_arbitration_gate_success_marker():
    assert (
        optimizer_arbitration_gate.SUCCESS_MARKER
        == "QTT_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_GATE_OK"
    )


def test_runner_exposes_candidate_parameter_stack_generation_gate_success_marker():
    assert (
        candidate_generation_gate.SUCCESS_MARKER
        == "QTT_CANDIDATE_PARAMETER_STACK_GENERATION_GATE_OK"
    )


def test_runner_exposes_trade_context_parameter_stack_selection_gate_success_marker():
    assert (
        trade_context_stack_selection_gate.SUCCESS_MARKER
        == "QTT_TRADE_CONTEXT_PARAMETER_STACK_SELECTION_GATE_OK"
    )


def test_runner_exposes_selected_parameter_stack_handoff_packet_success_marker():
    assert (
        selected_stack_handoff_gate.SUCCESS_MARKER
        == "QTT_SELECTED_PARAMETER_STACK_HANDOFF_PACKET_OK"
    )


def test_runner_exposes_replay_paper_candidate_stack_competition_gate_success_marker():
    assert (
        replay_paper_competition_gate.SUCCESS_MARKER
        == "QTT_REPLAY_PAPER_CANDIDATE_STACK_COMPETITION_GATE_OK"
    )


def test_runner_exposes_dual_result_review_for_parameter_stacks_success_marker():
    assert (
        dual_result_review_gate.SUCCESS_MARKER
        == "QTT_DUAL_RESULT_REVIEW_FOR_PARAMETER_STACKS_OK"
    )


def test_runner_exposes_owner_live_promotion_review_for_parameter_stacks_success_marker():
    assert (
        owner_live_promotion_review_gate.SUCCESS_MARKER
        == "QTT_OWNER_LIVE_PROMOTION_REVIEW_FOR_PARAMETER_STACKS_OK"
    )


def test_runner_exposes_owner_approval_request_queue_registry_success_marker():
    assert (
        owner_approval_request_queue_gate.SUCCESS_MARKER
        == "QTT_OWNER_APPROVAL_REQUEST_QUEUE_REGISTRY_OK"
    )


def test_runner_exposes_owner_override_receipt_authoring_gate_success_marker():
    assert (
        owner_override_receipt_authoring_gate.SUCCESS_MARKER
        == "QTT_OWNER_OVERRIDE_RECEIPT_AUTHORING_GATE_OK"
    )


def test_pr153r_repair_branch_is_explicit_downstream_validation_branch():
    assert (
        ci_branch_context.is_downstream_or_main_validation_branch(
            PR153R_REPAIR_BRANCH,
            after_pr=138,
            allow_repair=False,
        )
        is True
    )
    assert (
        ci_branch_context.is_downstream_or_main_validation_branch(
            PR153R_REPAIR_BRANCH,
            after_pr=153,
            allow_repair=False,
        )
        is False
    )
    assert (
        ci_branch_context.is_downstream_or_main_validation_branch(
            "repair-pr999-unapproved",
            after_pr=138,
        )
        is False
    )
    assert (
        ci_branch_context.is_downstream_or_main_validation_branch(
            "feature/non-downstream-validation",
            after_pr=138,
        )
        is False
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR153R_REPAIR_BRANCH,
            "tools/ci_branch_context.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR153R_REPAIR_BRANCH,
            "tools/run_validation_gates.py",
        )
        is False
    )


def test_pr153s_repair_branch_is_narrow_explicit_downstream_validation_branch():
    assert (
        ci_branch_context.is_downstream_or_main_validation_branch(
            PR153S_REPAIR_BRANCH,
            after_pr=152,
            allow_repair=False,
        )
        is True
    )
    assert (
        ci_branch_context.is_downstream_or_main_validation_branch(
            PR153S_REPAIR_BRANCH,
            after_pr=153,
            allow_repair=False,
        )
        is False
    )
    assert (
        ci_branch_context.is_downstream_or_main_validation_branch(
            "repair/pr999-unapproved",
            after_pr=152,
            allow_repair=False,
        )
        is False
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR153S_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/"
            "pr153s_source_value_capture_closure_classifier/report.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR153S_REPAIR_BRANCH,
            "tests/atomicrows/"
            "test_atomicrows_semantic_value_materialization_owner_authorization_gate.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR153S_REPAIR_BRANCH,
            "docs/master_plan/QTT_MasterPlan_Current.md",
        )
        is False
    )


def test_pr163_c_main_context_repair_branch_is_narrow_explicit_downstream_validation_branch():
    assert (
        ci_branch_context.is_explicit_downstream_repair_branch_context_allowed(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            upstream_pr=159,
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_branch_context_allowed(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            upstream_pr=160,
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_branch_context_allowed(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            upstream_pr=161,
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_branch_context_allowed(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            upstream_pr=162,
        )
        is False
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_branch_context_allowed(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            upstream_pr=163,
        )
        is False
    )
    assert (
        ci_branch_context.is_downstream_or_main_validation_branch(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            after_pr=160,
            allow_repair=False,
        )
        is True
    )
    assert (
        ci_branch_context.is_downstream_or_main_validation_branch(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            after_pr=163,
            allow_repair=False,
        )
        is False
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/"
            "pr159r_source_locator_value_capture/validator.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "tests/stage1_prediction_markets/"
            "pr159r_source_locator_value_capture/"
            "test_pr159r_branch_context_relaxation.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/"
            "source_intelligence/pr159s_open_intake/validator.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "tests/stage1_prediction_markets/"
            "source_intelligence/test_pr159s_branch_context.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/"
            "pr160_split_reclassification_route_closure/validator.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/atomicrows_pr154_value_state/"
            "pr161a_materialization_bridge/validator.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "tests/stage1_prediction_markets/atomicrows_pr154_value_state/"
            "test_pr161a_branch_context.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/"
            "master_plan_residual_candidate_coverage/validator.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "tests/stage1_prediction_markets/"
            "master_plan_residual_candidate_coverage/"
            "test_pr161b_branch_context.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/"
            "safe_repo_local_nonlive_dataset_materialization_authority_gate/"
            "validator.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "src/qtt/stage1_prediction_markets/"
            "pr163_c_pretrade_infrastructure_rejection_remediation/paths.py",
        )
        is True
    )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "tests/stage1_prediction_markets/"
            "pr163_c_pretrade_infrastructure_rejection_remediation/"
            "test_pr163_c_repeat_run_determinism.py",
        )
        is True
    )
    atomicrows_bundle_path = (
        "docs/master_plan/atomic_rows/" + "AtomicRows" + ".bundle" + ".jsonl"
    )
    atomicrows_sidecar_path = (
        "docs/master_plan/atomic_rows/"
        + "AtomicRows"
        + ".bundle"
        + "."
        + "sha256"
    )
    forbidden_repair_paths = (
        "docs/master_plan/generated/PR163_C_FinalSummary.report.json",
        "tools/validate_pr163_c_pretrade_infrastructure_rejection_remediation.py",
        "docs/master_plan/QTT_MasterPlan_Current.md",
        "docs/master_plan/generated/PR163_C_RuntimeCashAuthority.report.json",
        atomicrows_bundle_path,
        atomicrows_sidecar_path,
        "docs/master_plan/source_evidence/accepted_source_packet.json",
        "src/qtt/source_evidence/connector_binding.py",
        "src/qtt/stage1_prediction_markets/private_state/account_snapshot.py",
        "src/qtt/stage1_prediction_markets/runtime_cash/cash_state.py",
        "src/qtt/stage1_prediction_markets/order_live/live_order_router.py",
        "src/qtt/stage1_prediction_markets/quantum_backend/backend_runtime.py",
        "src/qtt/stage1_prediction_markets/llm_runtime/model_client.py",
        "src/qtt/stage1_prediction_markets/freeze_checksum/qku_digest.py",
        "src/qtt/stage1_prediction_markets/profit_claims/profit_summary.py",
    )
    for forbidden_path in forbidden_repair_paths:
        assert (
            ci_branch_context.is_explicit_downstream_repair_changed_path(
                PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
                forbidden_path,
            )
            is False
        )
    assert (
        ci_branch_context.is_explicit_downstream_repair_changed_path(
            PR163_C_MAIN_BRANCH_CONTEXT_REPAIR_BRANCH,
            "docs/master_plan/generated/PR163_C_FinalSummary.report.json",
        )
        is False
    )


def test_pr93_pr94_metadata_allow_pr153r_repair_downstream_branch(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    fake_git_stdout = _owner_gate_git_metadata_responses(PR153R_REPAIR_BRANCH)
    monkeypatch.setattr(owner_approval_request_queue_gate, "_git_stdout", fake_git_stdout)
    monkeypatch.setattr(owner_override_receipt_authoring_gate, "_git_stdout", fake_git_stdout)

    pr93_failures, pr93_metadata = (
        owner_approval_request_queue_gate.validate_pr93_roadmap_metadata(Path("."))
    )
    pr94_failures, pr94_metadata = (
        owner_override_receipt_authoring_gate.validate_pr94_roadmap_metadata(Path("."))
    )

    assert pr93_failures == []
    assert pr94_failures == []
    assert pr93_metadata["branch"] == PR153R_REPAIR_BRANCH
    assert pr94_metadata["branch"] == PR153R_REPAIR_BRANCH
    assert (
        owner_approval_request_queue_gate.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER
        in pr93_metadata["ci_info_lines"]
    )
    assert (
        owner_override_receipt_authoring_gate.DOWNSTREAM_ROADMAP_BRANCH_VALIDATION_MODE_MARKER
        in pr94_metadata["ci_info_lines"]
    )


def test_pr93_pr94_metadata_still_reject_arbitrary_branch(monkeypatch):
    _clear_branch_context_env(monkeypatch)
    branch = "feature/non-downstream-validation"
    fake_git_stdout = _owner_gate_git_metadata_responses(branch)
    monkeypatch.setattr(owner_approval_request_queue_gate, "_git_stdout", fake_git_stdout)
    monkeypatch.setattr(owner_override_receipt_authoring_gate, "_git_stdout", fake_git_stdout)

    pr93_failures, pr93_metadata = (
        owner_approval_request_queue_gate.validate_pr93_roadmap_metadata(Path("."))
    )
    pr94_failures, pr94_metadata = (
        owner_override_receipt_authoring_gate.validate_pr94_roadmap_metadata(Path("."))
    )

    assert (
        f"current branch must be {owner_approval_request_queue_gate.TARGET_BRANCH}, "
        f"got {branch}"
    ) in pr93_failures
    assert (
        f"current branch must be {owner_override_receipt_authoring_gate.TARGET_BRANCH}, "
        f"got {branch}"
    ) in pr94_failures
    assert pr93_metadata["branch"] == branch
    assert pr94_metadata["branch"] == branch


def test_runner_exposes_owner_dashboard_approval_menu_schema_success_marker():
    assert (
        owner_dashboard_approval_menu_schema_gate.SUCCESS_MARKER
        == "QTT_OWNER_DASHBOARD_APPROVAL_MENU_SCHEMA_OK"
    )


def test_runner_exposes_owner_dashboard_approval_static_screen_contract_success_marker():
    assert (
        owner_dashboard_approval_static_screen_contract_gate.SUCCESS_MARKER
        == "QTT_OWNER_DASHBOARD_APPROVAL_STATIC_SCREEN_CONTRACT_OK"
    )


def test_runner_exposes_atomicrows_full_bundle_row_expansion_plan_success_marker():
    assert (
        atomicrows_full_bundle_row_expansion_plan_gate.SUCCESS_MARKER
        == "QTT_ATOMICROWS_FULL_BUNDLE_ROW_EXPANSION_PLAN_OK"
    )


def test_runner_exposes_atomicrows_bundle_row_family_source_files_success_marker():
    assert (
        atomicrows_bundle_row_family_source_files_gate.SUCCESS_MARKER
        == "QTT_ATOMICROWS_BUNDLE_ROW_FAMILY_SOURCE_FILES_OK"
    )


def test_runner_exposes_atomicrows_bundle_builder_success_marker():
    assert (
        atomicrows_bundle_builder_deterministic_assembly_gate.SUCCESS_MARKER
        == "QTT_ATOMICROWS_BUNDLE_BUILDER_OK"
    )


def test_runner_exposes_active_non_sha_gate_registry_success_marker():
    assert (
        qtt_active_non_sha_day1_gate_state_registry_contract.SUCCESS_MARKER
        == "QTT_ACTIVE_NON_SHA_DAY1_GATE_STATE_REGISTRY_OK"
    )


def test_runner_exposes_roadmap_execution_state_controller_success_marker():
    assert (
        qtt_roadmap_execution_state_controller.SUCCESS_MARKER
        == "QTT_ROADMAP_EXECUTION_STATE_CONTROLLER_OK"
    )


def test_runner_exposes_atomicrows_bundle_sha_freeze_authority_gate_success_marker():
    assert (
        atomicrows_bundle_sha_freeze_authority_gate.SUCCESS_MARKER
        == "QTT_ATOMICROWS_BUNDLE_SHA_FREEZE_AUTHORITY_GATE_BLOCKED_OK"
    )


def test_runner_exposes_atomicrows_exact_row_authority_classifier_bridge_success_marker():
    assert (
        atomicrows_exact_row_authority_classifier_bridge.SUCCESS_MARKER
        == "QTT_ATOMICROWS_EXACT_ROW_AUTHORITY_CLASSIFIER_BRIDGE_OK"
    )


def test_runner_exposes_atomicrows_exact_row_expansion_manifest_success_marker():
    assert (
        atomicrows_exact_row_expansion_manifest.SUCCESS_MARKER
        == "QTT_ATOMICROWS_EXACT_ROW_EXPANSION_MANIFEST_OK"
    )


def test_runner_exposes_atomicrows_exact_row_generator_dry_run_success_marker():
    assert (
        atomicrows_exact_row_generator_dry_run_manifest.SUCCESS_MARKER
        == "QTT_ATOMICROWS_EXACT_ROW_GENERATOR_DRY_RUN_OK"
    )


def test_runner_exposes_atomicrows_repair_chain_grand_debug_logic_audit_success_marker():
    assert (
        atomicrows_repair_chain_grand_debug_logic_audit_manifest.SUCCESS_MARKER
        == "QTT_ATOMICROWS_REPAIR_CHAIN_GRAND_DEBUG_LOGIC_AUDIT_OK"
    )


def test_runner_exposes_atomicrows_exact_row_source_materialization_success_marker():
    assert (
        atomicrows_exact_row_source_materialization_manifest.SUCCESS_MARKER
        == "QTT_ATOMICROWS_EXACT_ROW_SOURCE_MATERIALIZATION_OK"
    )


def test_runner_exposes_atomicrows_exact_row_agent_family_eligibility_matrix_success_marker():
    assert (
        atomicrows_exact_row_agent_family_eligibility_matrix.SUCCESS_MARKER
        == "QTT_ATOMICROWS_EXACT_ROW_AGENT_FAMILY_ELIGIBILITY_MATRIX_OK"
    )


def test_runner_exposes_atomicrows_bundle_materialization_success_marker():
    assert (
        atomicrows_bundle_materialization_manifest.SUCCESS_MARKER
        == "QTT_ATOMICROWS_BUNDLE_MATERIALIZATION_OK"
    )


def test_runner_exposes_atomicrows_bundle_boundary_state_contract_success_marker():
    assert (
        atomicrows_bundle_boundary_state_contract.SUCCESS_MARKER
        == "QTT_ATOMICROWS_BUNDLE_BOUNDARY_STATE_CONTRACT_OK"
    )


def test_runner_does_not_use_direct_python_m_pytest(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert not any(command[:3] == [python_executable, "-m", "pytest"] for command in commands)


def test_runner_does_not_use_direct_pytest_command(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert not any(
        Path(token).name.lower() in {"pytest", "pytest.exe"}
        for command in commands
        for token in command
    )


def test_runner_includes_no_runtime_artifact_flags(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    no_runtime_command = next(
        command
        for command in commands
        if command[1] == str(Path("tools") / "validate_no_runtime_artifacts.py")
    )

    assert "--forbid-source-retrieval" in no_runtime_command
    assert "--forbid-source-acceptance" in no_runtime_command
    assert "--forbid-connector-binding" in no_runtime_command
    assert "--forbid-private-state-fetch" in no_runtime_command
    assert "--forbid-order-execution" in no_runtime_command
    assert "--forbid-neural-training" in no_runtime_command
    assert "--forbid-neural-inference" in no_runtime_command
    assert "--forbid-external-repo-clone" in no_runtime_command
    assert "--forbid-package-install-scripts" in no_runtime_command


def test_runner_keeps_scope_runtime_live_order_profit_and_source_blocks(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    scope_command = next(
        command
        for command in commands
        if command[1] == str(Path("tools") / "validate_first_pr_scope.py")
    )

    assert "--block-runtime" in scope_command
    assert "--block-live" in scope_command
    assert "--block-profit-claims" in scope_command
    assert "--block-source-retrieval" in scope_command
    assert "--block-source-acceptance" in scope_command
    assert "--block-connector-binding" in scope_command
    assert "--block-order-execution" in scope_command


def test_runner_orders_owner_intake_after_pr70_classifier(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr70_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    owner_intake_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    candidate_family_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )
    parameter_stack_role_index = command_names.index(
        "validate_atomicrows_parameter_stack_role_taxonomy.py"
    )
    parameter_stack_completeness_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    parameter_stack_compatibility_index = command_names.index(
        "validate_atomicrows_parameter_stack_compatibility_gate.py"
    )
    edge_packet_index = command_names.index(
        "validate_edge_parameter_stack_selection_packet.py"
    )
    trade_context_index = command_names.index("validate_qtt_trade_context_packet.py")
    selection_universe_index = command_names.index(
        "validate_atomicrows_parameter_selection_universe_registry.py"
    )
    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert (
        pr70_index
        < owner_intake_index
        < candidate_family_index
        < parameter_stack_role_index
        < parameter_stack_completeness_index
        < parameter_stack_compatibility_index
        < edge_packet_index
        < trade_context_index
        < selection_universe_index
        < generated_gate_index
        < no_runtime_index
    )
    assert commands[pr70_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_research_provenance_evidence_tier_classification.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsResearchProvenanceEvidenceTierClassification.report.json"
        ),
    ]
    assert commands[owner_intake_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsOwnerSubmittedResearchSourceIntakeRegistry.report.json"
        ),
    ]
    assert commands[candidate_family_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_research_source_to_candidate_family_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsResearchSourceToCandidateFamilyGate.report.json"
        ),
    ]
    assert commands[parameter_stack_role_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_parameter_stack_role_taxonomy.py"),
        "--out",
        _default_temp_generated_report("AtomicRowsParameterStackRoleTaxonomy.report.json"),
    ]
    assert commands[parameter_stack_completeness_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_completeness_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterStackCompletenessGate.report.json"
        ),
    ]
    assert commands[parameter_stack_compatibility_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_compatibility_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterStackCompatibilityGate.report.json"
        ),
    ]
    assert commands[edge_packet_index] == [
        python_executable,
        str(Path("tools") / "validate_edge_parameter_stack_selection_packet.py"),
        "--out",
        _default_temp_generated_report("EDGEParameterStackSelectionPacket.report.json"),
    ]
    assert commands[trade_context_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_trade_context_packet.py"),
        "--out",
        _default_temp_generated_report("QTTTradeContextPacket.report.json"),
    ]
    assert commands[selection_universe_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_selection_universe_registry.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterSelectionUniverseRegistry.report.json"
        ),
    ]


def test_runner_pr74_completeness_gate_has_no_runtime_source_or_bundle_args(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr73_index = command_names.index("validate_atomicrows_parameter_stack_role_taxonomy.py")
    pr74_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    pr70_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    pr71_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    pr72_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )

    assert pr70_index < pr71_index < pr72_index < pr73_index < pr74_index
    assert commands[pr74_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_completeness_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterStackCompletenessGate.report.json"
        ),
    ]
    pr74_text = " ".join(commands[pr74_index]).lower()
    assert "source-retrieval" not in pr74_text
    assert "source-acceptance" not in pr74_text
    assert "connector" not in pr74_text
    assert "runtime" not in pr74_text
    assert "live" not in pr74_text
    assert "order" not in pr74_text
    assert "profit" not in pr74_text
    assert "atomicrows.bundle.jsonl" not in pr74_text
    assert "atomicrows.bundle.sha256" not in pr74_text


def test_runner_includes_pr75_compatibility_gate_after_pr74_and_before_generated_derivative(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr70_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    pr71_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    pr72_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )
    pr73_index = command_names.index("validate_atomicrows_parameter_stack_role_taxonomy.py")
    pr74_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    pr75_index = command_names.index(
        "validate_atomicrows_parameter_stack_compatibility_gate.py"
    )
    pr77_index = command_names.index("validate_edge_parameter_stack_selection_packet.py")
    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert (
        pr70_index
        < pr71_index
        < pr72_index
        < pr73_index
        < pr74_index
        < pr75_index
        < pr77_index
        < generated_gate_index
        < no_runtime_index
    )
    assert commands[pr75_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_compatibility_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterStackCompatibilityGate.report.json"
        ),
    ]
    assert commands[pr77_index] == [
        python_executable,
        str(Path("tools") / "validate_edge_parameter_stack_selection_packet.py"),
        "--out",
        _default_temp_generated_report("EDGEParameterStackSelectionPacket.report.json"),
    ]


def test_runner_pr75_compatibility_gate_has_no_runtime_source_connector_or_future_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr75_command = commands[
        command_names.index("validate_atomicrows_parameter_stack_compatibility_gate.py")
    ]

    assert pr75_command == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_compatibility_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterStackCompatibilityGate.report.json"
        ),
    ]
    pr75_text = " ".join(pr75_command).lower()
    assert "source-retrieval" not in pr75_text
    assert "source-acceptance" not in pr75_text
    assert "connector" not in pr75_text
    assert "runtime" not in pr75_text
    assert "live" not in pr75_text
    assert "order" not in pr75_text
    assert "profit" not in pr75_text
    assert "replay" not in pr75_text
    assert "paper" not in pr75_text
    assert "quantum-backend" not in pr75_text
    assert "quantum-advantage" not in pr75_text
    assert "ranking" not in pr75_text
    assert "scoring" not in pr75_text
    assert "selection" not in pr75_text
    assert "arbitration" not in pr75_text
    assert "trade-context" not in pr75_text
    assert "candidate-stack" not in pr75_text
    assert "atomicrows.bundle.jsonl" not in pr75_text
    assert "atomicrows.bundle.sha256" not in pr75_text


def test_pr75_static_contract_preserves_no_claim_boundaries():
    production = parameter_stack_compatibility_gate.load_yaml(
        parameter_stack_compatibility_gate.DEFAULT_PRODUCTION_GATE
    )
    flags = production["explicit_no_claim_flags"]
    future = production["future_consumer_contract"]
    quantum = production["quantum_compatibility_policy"]
    runtime = production["runtime_live_order_boundary_policy"]
    source = production["source_evidence_boundary_policy"]
    connector = production["connector_semantic_boundary_policy"]

    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert connector["connector_semantics_created"] is False
    assert connector["connector_semantic_binding_created"] is False
    assert runtime["runtime_artifacts_created"] is False
    assert runtime["live_readiness_created"] is False
    assert runtime["runtime_live_use_created"] is False
    assert runtime["order_authority_created"] is False
    assert runtime["cash_receipts_created"] is False
    assert runtime["order_receipts_created"] is False
    assert runtime["fill_receipts_created"] is False
    assert flags["creates_profit_evidence"] is False
    assert flags["creates_replay_results"] is False
    assert flags["creates_paper_results"] is False
    assert quantum["quantum_backend_execution_created"] is False
    assert flags["creates_quantum_backend_evidence"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert flags["creates_quantum_advantage_claim"] is False
    assert flags["creates_scoring"] is False
    assert flags["creates_ranking"] is False
    assert flags["creates_stack_selection"] is False
    assert flags["creates_optimizer_arbitration"] is False
    assert flags["creates_trade_context_routing"] is False
    assert flags["creates_candidate_stack_generation"] is False
    assert future["this_gate_performs_scoring"] is False
    assert future["this_gate_performs_ranking"] is False
    assert future["this_gate_performs_selection"] is False
    assert future["this_gate_performs_arbitration"] is False
    assert future["this_gate_routes_trade_context"] is False
    assert future["this_gate_executes_replay_or_paper"] is False
    assert future["this_gate_executes_runtime_or_live"] is False
    assert (
        Path(".") / parameter_stack_compatibility_gate.CANONICAL_BUNDLE_JSONL
    ).exists()
    assert not (
        Path(".") / parameter_stack_compatibility_gate.CANONICAL_BUNDLE_SHA256
    ).exists()


def test_runner_includes_pr77_edge_packet_after_pr75_and_before_generated_derivative(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr70_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    pr71_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    pr72_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )
    pr73_index = command_names.index("validate_atomicrows_parameter_stack_role_taxonomy.py")
    pr74_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    pr75_index = command_names.index(
        "validate_atomicrows_parameter_stack_compatibility_gate.py"
    )
    pr77_index = command_names.index("validate_edge_parameter_stack_selection_packet.py")
    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )

    assert (
        pr70_index
        < pr71_index
        < pr72_index
        < pr73_index
        < pr74_index
        < pr75_index
        < pr77_index
        < generated_gate_index
    )
    assert commands[pr77_index] == [
        python_executable,
        str(Path("tools") / "validate_edge_parameter_stack_selection_packet.py"),
        "--out",
        _default_temp_generated_report("EDGEParameterStackSelectionPacket.report.json"),
    ]


def test_runner_includes_pr78_trade_context_packet_after_pr77_and_before_pr79(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr70_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    pr71_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    pr72_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )
    pr73_index = command_names.index("validate_atomicrows_parameter_stack_role_taxonomy.py")
    pr74_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    pr75_index = command_names.index(
        "validate_atomicrows_parameter_stack_compatibility_gate.py"
    )
    pr77_index = command_names.index("validate_edge_parameter_stack_selection_packet.py")
    pr78_index = command_names.index("validate_qtt_trade_context_packet.py")
    pr79_index = command_names.index(
        "validate_atomicrows_parameter_selection_universe_registry.py"
    )
    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )

    assert (
        pr70_index
        < pr71_index
        < pr72_index
        < pr73_index
        < pr74_index
        < pr75_index
        < pr77_index
        < pr78_index
        < pr79_index
        < generated_gate_index
    )
    assert commands[pr78_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_trade_context_packet.py"),
        "--out",
        _default_temp_generated_report("QTTTradeContextPacket.report.json"),
    ]
    assert commands[pr79_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_selection_universe_registry.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterSelectionUniverseRegistry.report.json"
        ),
    ]


def test_runner_pr77_edge_packet_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr77_command = commands[
        command_names.index("validate_edge_parameter_stack_selection_packet.py")
    ]

    assert pr77_command == [
        python_executable,
        str(Path("tools") / "validate_edge_parameter_stack_selection_packet.py"),
        "--out",
        _default_temp_generated_report("EDGEParameterStackSelectionPacket.report.json"),
    ]
    pr77_text = " ".join(pr77_command).lower()
    assert "source-retrieval" not in pr77_text
    assert "source-acceptance" not in pr77_text
    assert "connector-binding" not in pr77_text
    assert "runtime-live" not in pr77_text
    assert "live-use" not in pr77_text
    assert "order-authority" not in pr77_text
    assert "profit-evidence" not in pr77_text
    assert "replay-execution" not in pr77_text
    assert "paper-execution" not in pr77_text
    assert "quantum-backend" not in pr77_text
    assert "quantum-advantage" not in pr77_text
    assert "atomicrows.bundle.jsonl" not in pr77_text
    assert "atomicrows.bundle.sha256" not in pr77_text


def test_pr77_static_contract_preserves_no_claim_boundaries():
    production = edge_packet_gate.load_yaml(edge_packet_gate.DEFAULT_PRODUCTION_PACKET)
    flags = production["explicit_no_claim_flags"]
    future = production["future_consumer_contract"]
    quantum = production["quantum_advisory_policy"]
    source = production["source_evidence_boundary_policy"]
    bundle = production["atomicrows_bundle_boundary_policy"]
    readiness = production["production_readiness"]
    static_policy = production["static_packet_policy"]

    assert production["selected_stack_id"] == "SYNTHETIC_SELECTED_STACK_ID_SCHEMA_FIELD_ONLY"
    assert production["candidate_stack_generation_count"] == 0
    assert production["replay_paper_competition_required_flag"] is True
    assert production["owner_review_required_flag"] is True
    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert source["source_dependency_state_is_static_metadata_only"] is True
    assert bundle["atomicrows_bundle_digest_ref_static_placeholder_allowed"] is True
    assert bundle["atomicrows_bundle_file_created_by_this_pr"] is False
    assert bundle["atomicrows_bundle_sha_created_by_this_pr"] is False
    assert bundle["atomicrows_bundle_hash_authority_created_by_this_pr"] is False
    assert bundle["atomicrows_bundle_rows_created_by_this_pr"] is False
    assert quantum["selected_quantum_advisory_family_ids_required"] is True
    assert quantum["quantum_advisory_static_metadata_only"] is True
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert quantum["quantum_scoring_created"] is False
    assert quantum["quantum_ranking_created"] is False
    assert quantum["quantum_selection_created"] is False
    assert quantum["quantum_arbitration_created"] is False
    assert readiness["edge_parameter_stack_selection_packet_schema_ready"] is True
    assert readiness["production_edge_packet_evaluated"] is False
    assert readiness["production_edge_packet_ready"] is False
    assert readiness["production_stack_selected"] is False
    assert readiness["final_ready"] is False
    assert static_policy["selected_stack_id_is_static_schema_field_only"] is True
    assert all(flags[field] is False for field in edge_packet_gate.EXPLICIT_NO_CLAIM_FALSE_FIELDS)
    assert all(future[field] is False for field in edge_packet_gate.FUTURE_CONSUMER_FALSE_FIELDS)
    assert (Path(".") / edge_packet_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / edge_packet_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / edge_packet_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / edge_packet_gate.PR76_OLD_LONG_TEST).exists()


def test_runner_pr78_trade_context_packet_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr78_command = commands[command_names.index("validate_qtt_trade_context_packet.py")]

    assert pr78_command == [
        python_executable,
        str(Path("tools") / "validate_qtt_trade_context_packet.py"),
        "--out",
        _default_temp_generated_report("QTTTradeContextPacket.report.json"),
    ]
    pr78_text = " ".join(pr78_command).lower()
    assert "source-retrieval" not in pr78_text
    assert "source-acceptance" not in pr78_text
    assert "connector-binding" not in pr78_text
    assert "runtime-live" not in pr78_text
    assert "live-use" not in pr78_text
    assert "order-authority" not in pr78_text
    assert "profit-evidence" not in pr78_text
    assert "replay-execution" not in pr78_text
    assert "paper-execution" not in pr78_text
    assert "quantum-backend" not in pr78_text
    assert "quantum-advantage" not in pr78_text
    assert "atomicrows.bundle.jsonl" not in pr78_text
    assert "atomicrows.bundle.sha256" not in pr78_text


def test_pr78_static_contract_preserves_no_claim_boundaries():
    production = trade_context_gate.load_yaml(trade_context_gate.DEFAULT_PRODUCTION_PACKET)
    flags = production["explicit_no_claim_flags"]
    future = production["future_consumer_contract"]
    quantum = production["quantum_priority_boundary_policy"]
    source = production["source_evidence_boundary_policy"]
    connector = production["connector_semantic_boundary_policy"]
    runtime = production["runtime_live_order_boundary_policy"]
    readiness = production["production_readiness"]
    context = production["context_static_policy"]

    assert context["trade_context_is_static_schema_only"] is True
    assert context["trade_context_routes_selection_universe"] is False
    assert context["trade_context_selects_stack"] is False
    assert context["trade_context_scores_stack"] is False
    assert context["trade_context_ranks_stack"] is False
    assert context["trade_context_arbitrates_optimizer"] is False
    assert context["trade_context_executes_replay_or_paper"] is False
    assert context["trade_context_executes_runtime_or_live"] is False
    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert connector["connector_semantics_created"] is False
    assert connector["connector_semantic_binding_created"] is False
    assert runtime["runtime_artifacts_created"] is False
    assert runtime["runtime_resolver_execution_created"] is False
    assert runtime["runtime_live_use_created"] is False
    assert runtime["order_authority_created"] is False
    assert runtime["profit_evidence_created"] is False
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert quantum["quantum_selection_created"] is False
    assert quantum["quantum_arbitration_created"] is False
    assert readiness["qtt_trade_context_packet_schema_ready"] is True
    assert readiness["production_trade_context_evaluated"] is False
    assert readiness["production_trade_context_ready"] is False
    assert readiness["production_routing_ready"] is False
    assert readiness["production_selection_ready"] is False
    assert readiness["final_ready"] is False
    assert all(flags[field] is False for field in trade_context_gate.EXPLICIT_NO_CLAIM_FALSE_FIELDS)
    assert all(future[field] is False for field in trade_context_gate.FUTURE_CONSUMER_FALSE_FIELDS)
    assert (Path(".") / trade_context_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / trade_context_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / trade_context_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / trade_context_gate.PR76_OLD_LONG_TEST).exists()


def test_runner_pr79_selection_universe_registry_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr79_command = commands[
        command_names.index("validate_atomicrows_parameter_selection_universe_registry.py")
    ]

    assert pr79_command == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_selection_universe_registry.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterSelectionUniverseRegistry.report.json"
        ),
    ]
    pr79_text = " ".join(pr79_command).lower()
    assert "source-retrieval" not in pr79_text
    assert "source-acceptance" not in pr79_text
    assert "connector-binding" not in pr79_text
    assert "runtime-live" not in pr79_text
    assert "live-use" not in pr79_text
    assert "order-authority" not in pr79_text
    assert "profit-evidence" not in pr79_text
    assert "replay-execution" not in pr79_text
    assert "paper-execution" not in pr79_text
    assert "quantum-backend" not in pr79_text
    assert "quantum-advantage" not in pr79_text
    assert "consumer-gate" not in pr79_text
    assert "routing-gate" not in pr79_text
    assert "score" not in pr79_text
    assert "ranking" not in pr79_text
    assert "arbitration" not in pr79_text
    assert "candidate-stack" not in pr79_text
    assert "atomicrows.bundle.jsonl" not in pr79_text
    assert "atomicrows.bundle.sha256" not in pr79_text


def test_pr79_static_contract_preserves_no_claim_boundaries():
    production = selection_universe_gate.load_yaml(
        selection_universe_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    flags = production["explicit_no_claim_flags"]
    static = production["registry_static_policy"]
    membership = production["universe_membership_policy"]
    source = production["source_evidence_boundary_policy"]
    connector = production["connector_semantic_boundary_policy"]
    runtime = production["runtime_live_order_boundary_policy"]
    quantum = production["quantum_universe_policy"]
    readiness = production["production_readiness"]
    future = production["future_consumer_contract"]

    assert static["selection_universe_consumer_gate_created"] is False
    assert static["trade_context_to_selection_universe_routing_created"] is False
    assert static["route_result_created"] is False
    assert static["selected_stack_created"] is False
    assert static["stack_selection_created"] is False
    assert static["scoring_created"] is False
    assert static["ranking_created"] is False
    assert static["optimizer_arbitration_created"] is False
    assert static["candidate_stack_generation_created"] is False
    assert static["replay_paper_execution_created"] is False
    assert static["runtime_live_order_authority_created"] is False
    assert static["member_row_ids_created"] is False
    assert membership["membership_uses_random_sampling"] is False
    assert membership["membership_evaluated_against_live_data"] is False
    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert connector["connector_semantics_created"] is False
    assert connector["connector_semantic_binding_created"] is False
    assert runtime["runtime_artifacts_created"] is False
    assert runtime["runtime_resolver_execution_created"] is False
    assert runtime["live_readiness_created"] is False
    assert runtime["runtime_live_use_created"] is False
    assert runtime["private_state_fetch_created"] is False
    assert runtime["order_intent_authority_created"] is False
    assert runtime["order_authority_created"] is False
    assert runtime["cash_receipts_created"] is False
    assert runtime["order_receipts_created"] is False
    assert runtime["fill_receipts_created"] is False
    assert runtime["profit_evidence_created"] is False
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert quantum["quantum_selection_created"] is False
    assert quantum["quantum_arbitration_created"] is False
    assert future["this_pr_performs_selection_universe_consumer_gate"] is False
    assert future["this_pr_performs_routing"] is False
    assert future["this_pr_performs_scoring"] is False
    assert future["this_pr_performs_ranking"] is False
    assert future["this_pr_performs_arbitration"] is False
    assert future["this_pr_generates_candidate_stacks"] is False
    assert future["this_pr_executes_replay_or_paper"] is False
    assert future["this_pr_executes_runtime_or_live"] is False
    assert readiness["atomicrows_parameter_selection_universe_registry_ready"] is True
    assert readiness["production_selection_universe_registry_evaluated"] is False
    assert readiness["production_selection_universe_registry_ready"] is False
    assert readiness["production_universe_membership_evaluated"] is False
    assert readiness["production_routing_ready"] is False
    assert readiness["production_selection_ready"] is False
    assert readiness["final_ready"] is False
    assert all(
        flags[field] is False
        for field in selection_universe_gate.EXPLICIT_NO_CLAIM_FALSE_FIELDS
    )
    assert (Path(".") / selection_universe_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / selection_universe_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / selection_universe_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / selection_universe_gate.PR76_OLD_LONG_TEST).exists()


def test_runner_includes_pr80_pr81_pr82_pr83_pr84_pr85_pr86_pr87_pr88_pr89_pr90_pr91_pr92_and_pr93_gates_after_pr79(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr70_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    pr71_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    pr72_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )
    pr73_index = command_names.index("validate_atomicrows_parameter_stack_role_taxonomy.py")
    pr74_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    pr75_index = command_names.index(
        "validate_atomicrows_parameter_stack_compatibility_gate.py"
    )
    pr77_index = command_names.index("validate_edge_parameter_stack_selection_packet.py")
    pr78_index = command_names.index("validate_qtt_trade_context_packet.py")
    pr79_index = command_names.index(
        "validate_atomicrows_parameter_selection_universe_registry.py"
    )
    pr80_index = command_names.index(
        "validate_atomicrows_parameter_selection_universe_consumer_gate.py"
    )
    pr81_index = command_names.index(
        "validate_trade_context_selection_universe_routing_gate.py"
    )
    pr82_index = command_names.index(
        "validate_quantum_applicability_classification_registry.py"
    )
    pr83_index = command_names.index(
        "validate_owner_quantum_priority_policy_registry.py"
    )
    pr84_index = command_names.index(
        "validate_parameter_algorithm_scoring_policy_registry.py"
    )
    pr85_index = command_names.index(
        "validate_parameter_stack_scoring_and_ranking_gate.py"
    )
    pr86_index = command_names.index(
        "validate_quantum_classical_optimizer_arbitration_gate.py"
    )
    pr87_index = command_names.index(
        "validate_candidate_parameter_stack_generation_gate.py"
    )
    pr88_index = command_names.index(
        "validate_trade_context_parameter_stack_selection_gate.py"
    )
    pr89_index = command_names.index(
        "validate_selected_parameter_stack_handoff_packet.py"
    )
    pr90_index = command_names.index(
        "validate_replay_paper_candidate_stack_competition_gate.py"
    )
    pr91_index = command_names.index(
        "validate_dual_result_review_for_parameter_stacks.py"
    )
    pr92_index = command_names.index(
        "validate_owner_live_promotion_review_for_parameter_stacks.py"
    )
    pr93_index = command_names.index(
        "validate_owner_approval_request_queue_registry.py"
    )
    pr94_index = command_names.index(
        "validate_owner_override_receipt_authoring_gate.py"
    )
    pr95_index = command_names.index(
        "validate_owner_dashboard_approval_menu_schema.py"
    )
    pr96_index = command_names.index(
        "validate_owner_dashboard_approval_static_screen_contract.py"
    )
    pr97_index = command_names.index(
        "validate_atomicrows_full_bundle_row_expansion_plan.py"
    )
    pr98_index = command_names.index(
        "validate_atomicrows_bundle_row_family_source_files.py"
    )
    pr99_index = command_names.index(
        "validate_atomicrows_bundle_builder_deterministic_assembly_gate.py"
    )
    sha_dormancy_index = command_names.index(
        "validate_atomicrows_sha_system_dormancy_state_contract.py"
    )
    final_readiness_dependency_policy_index = command_names.index(
        "validate_qtt_final_readiness_dependency_policy_contract.py"
    )
    active_non_sha_gate_registry_index = command_names.index(
        "validate_qtt_active_non_sha_day1_gate_state_registry_contract.py"
    )
    pr_identity_roster_index = command_names.index(
        "validate_qtt_pr_identity_roster.py"
    )
    roadmap_execution_state_controller_index = command_names.index(
        "validate_qtt_roadmap_execution_state_controller.py"
    )
    pr100_index = command_names.index(
        "validate_atomicrows_bundle_sha_freeze_authority_gate.py"
    )
    repair_bridge_index = command_names.index(
        "validate_atomicrows_exact_row_authority_classifier_bridge.py"
    )
    repair_c0_index = command_names.index(
        "validate_atomicrows_owner_approved_exact_15_family_count_distribution.py"
    )
    repair_manifest_index = command_names.index(
        "validate_atomicrows_exact_row_expansion_manifest.py"
    )
    repair_dry_run_index = command_names.index(
        "validate_atomicrows_exact_row_generator_dry_run_manifest.py"
    )
    repair_c1_index = command_names.index(
        "validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest.py"
    )
    repair_d_index = command_names.index(
        "validate_atomicrows_exact_row_source_materialization_manifest.py"
    )
    repair_d2_e0_index = command_names.index(
        "validate_atomicrows_exact_row_agent_family_eligibility_matrix.py"
    )
    bundle_materialization_index = command_names.index(
        "validate_atomicrows_bundle_materialization_manifest.py"
    )
    bundle_boundary_index = command_names.index(
        "validate_atomicrows_bundle_boundary_state_contract.py"
    )
    sha_freeze_final_readiness_state_index = command_names.index(
        "validate_atomicrows_sha_freeze_final_readiness_state_contract.py"
    )
    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert (
        pr70_index
        < pr71_index
        < pr72_index
        < pr73_index
        < pr74_index
        < pr75_index
        < pr77_index
        < pr78_index
        < pr79_index
        < pr80_index
        < pr81_index
        < pr82_index
        < pr83_index
        < pr84_index
        < pr85_index
        < pr86_index
        < pr87_index
        < pr88_index
        < pr89_index
        < pr90_index
        < pr91_index
        < pr92_index
        < pr93_index
        < pr94_index
        < pr95_index
        < pr96_index
        < pr97_index
        < pr98_index
        < pr99_index
        < sha_dormancy_index
        < final_readiness_dependency_policy_index
        < active_non_sha_gate_registry_index
        < pr_identity_roster_index
        < roadmap_execution_state_controller_index
        < pr100_index
        < repair_bridge_index
        < repair_manifest_index
        < repair_c0_index
        < repair_dry_run_index
        < repair_c1_index
        < repair_d_index
        < repair_d2_e0_index
        < bundle_materialization_index
        < bundle_boundary_index
        < sha_freeze_final_readiness_state_index
        < generated_gate_index
        < no_runtime_index
    )
    assert commands[pr80_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_selection_universe_consumer_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterSelectionUniverseConsumerGate.report.json"
        ),
    ]
    assert commands[pr81_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_trade_context_selection_universe_routing_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsTradeContextSelectionUniverseRoutingGate.report.json"
        ),
    ]
    assert commands[pr82_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_quantum_applicability_classification_registry.py"
        ),
        "--out",
        _default_temp_generated_report(
            "QuantumApplicabilityClassificationRegistry.report.json"
        ),
    ]
    assert commands[pr83_index] == [
        python_executable,
        str(Path("tools") / "validate_owner_quantum_priority_policy_registry.py"),
        "--out",
        _default_temp_generated_report("OwnerQuantumPriorityPolicyRegistry.report.json"),
    ]
    assert commands[pr84_index] == [
        python_executable,
        str(Path("tools") / "validate_parameter_algorithm_scoring_policy_registry.py"),
        "--out",
        _default_temp_generated_report(
            "ParameterAlgorithmScoringPolicyRegistry.report.json"
        ),
    ]
    assert commands[pr85_index] == [
        python_executable,
        str(Path("tools") / "validate_parameter_stack_scoring_and_ranking_gate.py"),
        "--out",
        _default_temp_generated_report("ParameterStackScoringAndRankingGate.report.json"),
    ]
    assert commands[pr86_index] == [
        python_executable,
        str(Path("tools") / "validate_quantum_classical_optimizer_arbitration_gate.py"),
        "--out",
        _default_temp_generated_report(
            "QuantumClassicalOptimizerArbitrationGate.report.json"
        ),
    ]
    assert commands[pr87_index] == [
        python_executable,
        str(Path("tools") / "validate_candidate_parameter_stack_generation_gate.py"),
        "--out",
        _default_temp_generated_report("CandidateParameterStackGenerationGate.report.json"),
    ]
    assert commands[pr88_index] == [
        python_executable,
        str(Path("tools") / "validate_trade_context_parameter_stack_selection_gate.py"),
        "--out",
        _default_temp_generated_report(
            "TradeContextParameterStackSelectionGate.report.json"
        ),
    ]
    assert commands[pr89_index] == [
        python_executable,
        str(Path("tools") / "validate_selected_parameter_stack_handoff_packet.py"),
        "--out",
        _default_temp_generated_report("SelectedParameterStackHandoffPacket.report.json"),
    ]
    assert commands[pr90_index] == [
        python_executable,
        str(Path("tools") / "validate_replay_paper_candidate_stack_competition_gate.py"),
        "--out",
        _default_temp_generated_report(
            "ReplayPaperCandidateStackCompetitionGate.report.json"
        ),
    ]
    assert commands[pr91_index] == [
        python_executable,
        str(Path("tools") / "validate_dual_result_review_for_parameter_stacks.py"),
        "--out",
        _default_temp_generated_report("DualResultReviewForParameterStacks.report.json"),
    ]
    assert commands[pr92_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_owner_live_promotion_review_for_parameter_stacks.py"
        ),
        "--out",
        _default_temp_generated_report(
            "OwnerLivePromotionReviewForParameterStacks.report.json"
        ),
    ]
    assert commands[pr93_index] == [
        python_executable,
        str(Path("tools") / "validate_owner_approval_request_queue_registry.py"),
        "--out",
        _default_temp_generated_report("OwnerApprovalRequestQueueRegistry.report.json"),
    ]
    assert commands[pr94_index] == [
        python_executable,
        str(Path("tools") / "validate_owner_override_receipt_authoring_gate.py"),
        "--out",
        _default_temp_generated_report("OwnerOverrideReceiptAuthoringGate.report.json"),
    ]
    assert commands[pr95_index] == [
        python_executable,
        str(Path("tools") / "validate_owner_dashboard_approval_menu_schema.py"),
        "--out",
        _default_temp_generated_report("OwnerDashboardApprovalMenuSchema.report.json"),
    ]
    assert commands[pr96_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_owner_dashboard_approval_static_screen_contract.py"
        ),
        "--out",
        _default_temp_generated_report(
            "OwnerDashboardApprovalStaticScreenContract.report.json"
        ),
    ]
    assert commands[pr97_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_full_bundle_row_expansion_plan.py"),
        "--out",
        _default_temp_generated_report("AtomicRowsFullBundleRowExpansionPlan.report.json"),
    ]
    assert commands[pr98_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_bundle_row_family_source_files.py"),
        "--out",
        _default_temp_generated_report("AtomicRowsBundleRowFamilySourceFiles.report.json"),
    ]
    assert commands[pr99_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_bundle_builder_deterministic_assembly_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsBundleBuilderDeterministicAssemblyGate.report.json"
        ),
    ]
    assert commands[sha_dormancy_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_sha_system_dormancy_state_contract.py"),
        "--report-out",
        _default_temp_generated_report(
            "AtomicRowsShaSystemDormancyStateContract.report.json"
        ),
    ]
    assert commands[final_readiness_dependency_policy_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_qtt_final_readiness_dependency_policy_contract.py"
        ),
        "--report-out",
        _default_temp_generated_report("QttFinalReadinessDependencyPolicy.report.json"),
    ]
    assert commands[active_non_sha_gate_registry_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_qtt_active_non_sha_day1_gate_state_registry_contract.py"
        ),
        "--report-out",
        _default_temp_generated_report(
            "QttActiveNonShaDay1GateStateRegistry.report.json"
        ),
    ]
    assert commands[pr_identity_roster_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_pr_identity_roster.py"),
        "--report-out",
        _default_temp_generated_report("QttPrIdentityRoster.report.json"),
    ]
    assert commands[roadmap_execution_state_controller_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_roadmap_execution_state_controller.py"),
        "--report-out",
        _default_temp_generated_report("QttRoadmapExecutionStateController.report.json"),
    ]
    assert commands[pr100_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_bundle_sha_freeze_authority_gate.py"),
        "--report-out",
        _default_temp_generated_report("AtomicRowsBundleShaFreezeAuthorityGate.report.json"),
    ]
    assert commands[repair_bridge_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_exact_row_authority_classifier_bridge.py"
        ),
        "--report-out",
        _default_temp_generated_report(
            "AtomicRowsExactRowAuthorityClassifierBridge.report.json"
        ),
    ]
    assert commands[repair_c0_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_owner_approved_exact_15_family_count_distribution.py"
        ),
        "--report-out",
        _default_temp_generated_report(
            "AtomicRowsOwnerApprovedExact15FamilyCountDistribution.report.json"
        ),
    ]
    assert commands[repair_manifest_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_exact_row_expansion_manifest.py"),
        "--report-out",
        _default_temp_generated_report("AtomicRowsExactRowExpansionManifest.report.json"),
    ]
    assert commands[repair_dry_run_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_exact_row_generator_dry_run_manifest.py"
        ),
        "--report-out",
        _default_temp_generated_report("AtomicRowsExactRowGeneratorDryRun.report.json"),
    ]
    assert commands[repair_c1_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_repair_chain_grand_debug_logic_audit_manifest.py"
        ),
        "--report-out",
        _default_temp_generated_report(
            "AtomicRowsRepairChainGrandDebugLogicAudit.report.json"
        ),
    ]
    assert commands[repair_d_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_exact_row_source_materialization_manifest.py"
        ),
        "--report-out",
        _default_temp_generated_report(
            "AtomicRowsExactRowSourceMaterialization.report.json"
        ),
    ]
    assert commands[repair_d2_e0_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_exact_row_agent_family_eligibility_matrix.py"
        ),
        "--report-out",
        _default_temp_generated_report(
            "AtomicRowsExactRowAgentFamilyEligibilityMatrix.report.json"
        ),
    ]
    assert commands[bundle_materialization_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_bundle_materialization_manifest.py"),
        "--report-out",
        _default_temp_generated_report("AtomicRowsBundleMaterialization.report.json"),
    ]
    assert commands[bundle_boundary_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_bundle_boundary_state_contract.py"),
        "--report-out",
        _default_temp_generated_report("AtomicRowsBundleBoundaryStateContract.report.json"),
    ]
    assert commands[sha_freeze_final_readiness_state_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_sha_freeze_final_readiness_state_contract.py"
        ),
        "--report-out",
        _default_temp_generated_report(
            "AtomicRowsShaFreezeFinalReadinessStateContract.report.json"
        ),
    ]


def test_runner_does_not_emit_success_marker_if_selection_universe_consumer_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 37, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 37
    assert seen == commands[:2]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_trade_context_routing_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 41, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 41
    assert seen == commands[:3]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_quantum_applicability_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 43, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 43
    assert seen == commands[:4]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_quantum_priority_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 47, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 47
    assert seen == commands[:5]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_parameter_algorithm_scoring_policy_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 53, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 53
    assert seen == commands[:6]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_parameter_stack_scoring_and_ranking_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 59, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 59
    assert seen == commands[:7]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_optimizer_arbitration_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 61, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 61
    assert seen == commands[:8]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_candidate_generation_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 62, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 62
    assert seen == commands[:9]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_selected_stack_handoff_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 63, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 63
    assert seen == commands[:11]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_replay_paper_competition_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 64, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 64
    assert seen == commands[:12]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_dual_result_review_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 65, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 65
    assert seen == commands[:13]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_live_promotion_review_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 66, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 66
    assert seen == commands[:14]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_approval_request_queue_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "validate_owner_approval_request_queue_registry.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 67, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 67
    assert seen == commands[:15]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_override_receipt_authoring_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "validate_owner_approval_request_queue_registry.py"],
        ["python", "validate_owner_override_receipt_authoring_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 68, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 68
    assert seen == commands[:16]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_dashboard_approval_menu_schema_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "validate_owner_approval_request_queue_registry.py"],
        ["python", "validate_owner_override_receipt_authoring_gate.py"],
        ["python", "validate_owner_dashboard_approval_menu_schema.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 69, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 69
    assert seen == commands[:17]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_dashboard_approval_static_screen_contract_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "validate_owner_approval_request_queue_registry.py"],
        ["python", "validate_owner_override_receipt_authoring_gate.py"],
        ["python", "validate_owner_dashboard_approval_menu_schema.py"],
        ["python", "validate_owner_dashboard_approval_static_screen_contract.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 70, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 70
    assert seen == commands[:18]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_atomicrows_full_bundle_row_expansion_plan_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "validate_owner_approval_request_queue_registry.py"],
        ["python", "validate_owner_override_receipt_authoring_gate.py"],
        ["python", "validate_owner_dashboard_approval_menu_schema.py"],
        ["python", "validate_owner_dashboard_approval_static_screen_contract.py"],
        ["python", "validate_atomicrows_full_bundle_row_expansion_plan.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 71, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 71
    assert seen == commands[:19]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_atomicrows_bundle_row_family_source_files_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_consumer_gate.py"],
        ["python", "validate_trade_context_selection_universe_routing_gate.py"],
        ["python", "validate_quantum_applicability_classification_registry.py"],
        ["python", "validate_owner_quantum_priority_policy_registry.py"],
        ["python", "validate_parameter_algorithm_scoring_policy_registry.py"],
        ["python", "validate_parameter_stack_scoring_and_ranking_gate.py"],
        ["python", "validate_quantum_classical_optimizer_arbitration_gate.py"],
        ["python", "validate_candidate_parameter_stack_generation_gate.py"],
        ["python", "validate_trade_context_parameter_stack_selection_gate.py"],
        ["python", "validate_selected_parameter_stack_handoff_packet.py"],
        ["python", "validate_replay_paper_candidate_stack_competition_gate.py"],
        ["python", "validate_dual_result_review_for_parameter_stacks.py"],
        ["python", "validate_owner_live_promotion_review_for_parameter_stacks.py"],
        ["python", "validate_owner_approval_request_queue_registry.py"],
        ["python", "validate_owner_override_receipt_authoring_gate.py"],
        ["python", "validate_owner_dashboard_approval_menu_schema.py"],
        ["python", "validate_owner_dashboard_approval_static_screen_contract.py"],
        ["python", "validate_atomicrows_full_bundle_row_expansion_plan.py"],
        ["python", "validate_atomicrows_bundle_row_family_source_files.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        72,
        0,
    ]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 72
    assert seen == commands[:20]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_pr80_consumer_gate_has_no_runtime_source_connector_or_routing_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr80_command = commands[
        command_names.index(
            "validate_atomicrows_parameter_selection_universe_consumer_gate.py"
        )
    ]

    assert pr80_command == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_selection_universe_consumer_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterSelectionUniverseConsumerGate.report.json"
        ),
    ]
    pr80_text = " ".join(pr80_command).lower()
    assert "source-retrieval" not in pr80_text
    assert "source-acceptance" not in pr80_text
    assert "connector-binding" not in pr80_text
    assert "runtime-live" not in pr80_text
    assert "live-use" not in pr80_text
    assert "order-authority" not in pr80_text
    assert "profit-evidence" not in pr80_text
    assert "replay-execution" not in pr80_text
    assert "paper-execution" not in pr80_text
    assert "quantum-backend" not in pr80_text
    assert "quantum-advantage" not in pr80_text
    assert "atomicrows.bundle.jsonl" not in pr80_text
    assert "atomicrows.bundle.sha256" not in pr80_text


def test_pr80_static_contract_preserves_consumer_gate_no_claim_boundaries():
    production = selection_universe_consumer_gate.load_yaml(
        selection_universe_consumer_gate.DEFAULT_PRODUCTION_GATE
    )
    flags = production["explicit_no_claim_flags"]
    static = production["gate_static_policy"]
    source = production["source_evidence_boundary_policy"]
    connector = production["connector_semantic_boundary_policy"]
    runtime = production["runtime_live_order_boundary_policy"]
    quantum = production["quantum_consumer_policy"]
    readiness = production["production_readiness"]
    future = production["future_consumer_contract"]

    assert static["selection_universe_consumer_gate_is_static_only"] is True
    assert static["agent_universe_consumer_access_is_deterministic"] is True
    assert static["trade_context_to_selection_universe_routing_created"] is False
    assert static["routed_universe_ids_created"] is False
    assert static["route_result_created"] is False
    assert static["selected_stack_created"] is False
    assert static["stack_selection_created"] is False
    assert static["scoring_created"] is False
    assert static["ranking_created"] is False
    assert static["optimizer_arbitration_created"] is False
    assert static["candidate_stack_generation_created"] is False
    assert static["replay_paper_execution_created"] is False
    assert static["runtime_live_order_authority_created"] is False
    assert source["source_retrieval_created"] is False
    assert source["source_acceptance_created"] is False
    assert source["accepted_source_packets_created"] is False
    assert connector["connector_semantics_created"] is False
    assert connector["connector_semantic_binding_created"] is False
    assert runtime["runtime_artifacts_created"] is False
    assert runtime["runtime_resolver_execution_created"] is False
    assert runtime["live_readiness_created"] is False
    assert runtime["runtime_live_use_created"] is False
    assert runtime["private_state_fetch_created"] is False
    assert runtime["order_intent_authority_created"] is False
    assert runtime["order_authority_created"] is False
    assert runtime["cash_receipts_created"] is False
    assert runtime["order_receipts_created"] is False
    assert runtime["fill_receipts_created"] is False
    assert runtime["profit_evidence_created"] is False
    assert quantum["quantum_backend_execution_created"] is False
    assert quantum["quantum_advantage_claim_created"] is False
    assert quantum["quantum_selection_created"] is False
    assert quantum["quantum_arbitration_created"] is False
    assert future["this_pr_performs_routing"] is False
    assert future["this_pr_performs_scoring"] is False
    assert future["this_pr_performs_ranking"] is False
    assert future["this_pr_performs_selection"] is False
    assert future["this_pr_performs_arbitration"] is False
    assert future["this_pr_generates_candidate_stacks"] is False
    assert future["this_pr_executes_replay_or_paper"] is False
    assert future["this_pr_executes_runtime_or_live"] is False
    assert readiness["parameter_selection_universe_consumer_gate_ready"] is True
    assert readiness["production_selection_universe_consumer_gate_evaluated"] is False
    assert readiness["production_selection_universe_consumer_gate_ready"] is False
    assert readiness["production_consumer_access_evaluated"] is False
    assert readiness["production_routing_evaluated"] is False
    assert readiness["production_routing_ready"] is False
    assert readiness["production_selection_ready"] is False
    assert readiness["final_ready"] is False
    assert all(
        flags[field] is False
        for field in selection_universe_consumer_gate.EXPLICIT_NO_CLAIM_FALSE_FIELDS
    )
    assert (Path(".") / selection_universe_consumer_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / selection_universe_consumer_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / selection_universe_consumer_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / selection_universe_consumer_gate.PR76_OLD_LONG_TEST).exists()


def test_runner_pr81_routing_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr81_command = commands[
        command_names.index("validate_trade_context_selection_universe_routing_gate.py")
    ]

    assert pr81_command == [
        python_executable,
        str(Path("tools") / "validate_trade_context_selection_universe_routing_gate.py"),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsTradeContextSelectionUniverseRoutingGate.report.json"
        ),
    ]
    pr81_text = " ".join(pr81_command).lower()
    assert "source-retrieval" not in pr81_text
    assert "source-acceptance" not in pr81_text
    assert "connector-binding" not in pr81_text
    assert "runtime-live" not in pr81_text
    assert "live-use" not in pr81_text
    assert "order-authority" not in pr81_text
    assert "profit-evidence" not in pr81_text
    assert "replay-execution" not in pr81_text
    assert "paper-execution" not in pr81_text
    assert "quantum-backend" not in pr81_text
    assert "quantum-advantage" not in pr81_text
    assert "atomicrows.bundle.jsonl" not in pr81_text
    assert "atomicrows.bundle.sha256" not in pr81_text


def test_runner_pr82_quantum_applicability_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr82_command = commands[
        command_names.index("validate_quantum_applicability_classification_registry.py")
    ]

    assert pr82_command == [
        python_executable,
        str(
            Path("tools")
            / "validate_quantum_applicability_classification_registry.py"
        ),
        "--out",
        _default_temp_generated_report(
            "QuantumApplicabilityClassificationRegistry.report.json"
        ),
    ]
    pr82_text = " ".join(pr82_command).lower()
    assert "source-retrieval" not in pr82_text
    assert "source-acceptance" not in pr82_text
    assert "connector-binding" not in pr82_text
    assert "runtime-live" not in pr82_text
    assert "live-use" not in pr82_text
    assert "order-authority" not in pr82_text
    assert "profit-evidence" not in pr82_text
    assert "replay-execution" not in pr82_text
    assert "paper-execution" not in pr82_text
    assert "quantum-backend" not in pr82_text
    assert "quantum-simulator" not in pr82_text
    assert "atomicrows.bundle.jsonl" not in pr82_text
    assert "atomicrows.bundle.sha256" not in pr82_text


def test_runner_pr83_owner_quantum_priority_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr83_command = commands[
        command_names.index("validate_owner_quantum_priority_policy_registry.py")
    ]

    assert pr83_command == [
        python_executable,
        str(Path("tools") / "validate_owner_quantum_priority_policy_registry.py"),
        "--out",
        _default_temp_generated_report("OwnerQuantumPriorityPolicyRegistry.report.json"),
    ]
    pr83_text = " ".join(pr83_command).lower()
    assert "source-retrieval" not in pr83_text
    assert "source-acceptance" not in pr83_text
    assert "connector-binding" not in pr83_text
    assert "runtime-live" not in pr83_text
    assert "live-use" not in pr83_text
    assert "order-authority" not in pr83_text
    assert "profit-evidence" not in pr83_text
    assert "replay-execution" not in pr83_text
    assert "paper-execution" not in pr83_text
    assert "quantum-backend" not in pr83_text
    assert "quantum-simulator" not in pr83_text
    assert "optimizer-execution" not in pr83_text
    assert "optimizer-arbitration" not in pr83_text
    assert "scoring-execution" not in pr83_text
    assert "ranking" not in pr83_text
    assert "selection" not in pr83_text
    assert "atomicrows.bundle.jsonl" not in pr83_text
    assert "atomicrows.bundle.sha256" not in pr83_text


def test_runner_pr84_parameter_algorithm_scoring_policy_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr84_command = commands[
        command_names.index("validate_parameter_algorithm_scoring_policy_registry.py")
    ]

    assert pr84_command == [
        python_executable,
        str(Path("tools") / "validate_parameter_algorithm_scoring_policy_registry.py"),
        "--out",
        _default_temp_generated_report(
            "ParameterAlgorithmScoringPolicyRegistry.report.json"
        ),
    ]
    pr84_text = " ".join(pr84_command).lower()
    assert "source-retrieval" not in pr84_text
    assert "source-acceptance" not in pr84_text
    assert "connector-binding" not in pr84_text
    assert "runtime-live" not in pr84_text
    assert "live-use" not in pr84_text
    assert "order-authority" not in pr84_text
    assert "profit-evidence" not in pr84_text
    assert "replay-execution" not in pr84_text
    assert "paper-execution" not in pr84_text
    assert "quantum-backend" not in pr84_text
    assert "quantum-simulator" not in pr84_text
    assert "optimizer-execution" not in pr84_text
    assert "optimizer-arbitration" not in pr84_text
    assert "scoring-execution" not in pr84_text
    assert "ranking" not in pr84_text
    assert "selection" not in pr84_text
    assert "atomicrows.bundle.jsonl" not in pr84_text
    assert "atomicrows.bundle.sha256" not in pr84_text


def test_runner_pr85_parameter_stack_scoring_and_ranking_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr85_command = commands[
        command_names.index("validate_parameter_stack_scoring_and_ranking_gate.py")
    ]

    assert pr85_command == [
        python_executable,
        str(Path("tools") / "validate_parameter_stack_scoring_and_ranking_gate.py"),
        "--out",
        _default_temp_generated_report("ParameterStackScoringAndRankingGate.report.json"),
    ]
    pr85_text = " ".join(pr85_command).lower()
    assert "source-retrieval" not in pr85_text
    assert "source-acceptance" not in pr85_text
    assert "connector-binding" not in pr85_text
    assert "runtime-live" not in pr85_text
    assert "live-use" not in pr85_text
    assert "order-authority" not in pr85_text
    assert "profit-evidence" not in pr85_text
    assert "replay-execution" not in pr85_text
    assert "paper-execution" not in pr85_text
    assert "quantum-backend" not in pr85_text
    assert "quantum-simulator" not in pr85_text
    assert "optimizer-execution" not in pr85_text
    assert "optimizer-arbitration" not in pr85_text
    assert "atomicrows.bundle.jsonl" not in pr85_text
    assert "atomicrows.bundle.sha256" not in pr85_text


def test_runner_pr86_optimizer_arbitration_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr86_command = commands[
        command_names.index("validate_quantum_classical_optimizer_arbitration_gate.py")
    ]

    assert pr86_command == [
        python_executable,
        str(Path("tools") / "validate_quantum_classical_optimizer_arbitration_gate.py"),
        "--out",
        _default_temp_generated_report(
            "QuantumClassicalOptimizerArbitrationGate.report.json"
        ),
    ]
    pr86_text = " ".join(pr86_command).lower()
    assert "source-retrieval" not in pr86_text
    assert "source-acceptance" not in pr86_text
    assert "connector-binding" not in pr86_text
    assert "runtime-live" not in pr86_text
    assert "live-use" not in pr86_text
    assert "order-authority" not in pr86_text
    assert "profit-evidence" not in pr86_text
    assert "replay-execution" not in pr86_text
    assert "paper-execution" not in pr86_text
    assert "quantum-backend" not in pr86_text
    assert "quantum-simulator" not in pr86_text
    assert "optimizer-execution" not in pr86_text
    assert "atomicrows.bundle.jsonl" not in pr86_text
    assert "atomicrows.bundle.sha256" not in pr86_text


def test_runner_pr87_candidate_generation_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr87_command = commands[
        command_names.index("validate_candidate_parameter_stack_generation_gate.py")
    ]

    assert pr87_command == [
        python_executable,
        str(Path("tools") / "validate_candidate_parameter_stack_generation_gate.py"),
        "--out",
        _default_temp_generated_report("CandidateParameterStackGenerationGate.report.json"),
    ]
    pr87_text = " ".join(pr87_command).lower()
    assert "source-retrieval" not in pr87_text
    assert "source-acceptance" not in pr87_text
    assert "connector-binding" not in pr87_text
    assert "runtime-live" not in pr87_text
    assert "live-use" not in pr87_text
    assert "order-authority" not in pr87_text
    assert "profit-evidence" not in pr87_text
    assert "replay-execution" not in pr87_text
    assert "paper-execution" not in pr87_text
    assert "quantum-backend" not in pr87_text
    assert "quantum-simulator" not in pr87_text
    assert "optimizer-execution" not in pr87_text
    assert "atomicrows.bundle.jsonl" not in pr87_text
    assert "atomicrows.bundle.sha256" not in pr87_text


def test_runner_pr88_trade_context_stack_selection_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr88_command = commands[
        command_names.index("validate_trade_context_parameter_stack_selection_gate.py")
    ]

    assert pr88_command == [
        python_executable,
        str(Path("tools") / "validate_trade_context_parameter_stack_selection_gate.py"),
        "--out",
        _default_temp_generated_report(
            "TradeContextParameterStackSelectionGate.report.json"
        ),
    ]
    pr88_text = " ".join(pr88_command).lower()
    assert "source-retrieval" not in pr88_text
    assert "source-acceptance" not in pr88_text
    assert "connector-binding" not in pr88_text
    assert "runtime-live" not in pr88_text
    assert "live-use" not in pr88_text
    assert "order-authority" not in pr88_text
    assert "profit-evidence" not in pr88_text
    assert "replay-execution" not in pr88_text
    assert "paper-execution" not in pr88_text
    assert "selected-stack-handoff" not in pr88_text
    assert "quantum-backend" not in pr88_text
    assert "quantum-simulator" not in pr88_text
    assert "optimizer-execution" not in pr88_text
    assert "atomicrows.bundle.jsonl" not in pr88_text
    assert "atomicrows.bundle.sha256" not in pr88_text


def test_runner_pr89_selected_stack_handoff_packet_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr89_command = commands[
        command_names.index("validate_selected_parameter_stack_handoff_packet.py")
    ]

    assert pr89_command == [
        python_executable,
        str(Path("tools") / "validate_selected_parameter_stack_handoff_packet.py"),
        "--out",
        _default_temp_generated_report("SelectedParameterStackHandoffPacket.report.json"),
    ]
    pr89_text = " ".join(pr89_command).lower()
    assert "source-retrieval" not in pr89_text
    assert "source-acceptance" not in pr89_text
    assert "connector-binding" not in pr89_text
    assert "runtime-live" not in pr89_text
    assert "live-use" not in pr89_text
    assert "order-authority" not in pr89_text
    assert "profit-evidence" not in pr89_text
    assert "replay-execution" not in pr89_text
    assert "paper-execution" not in pr89_text
    assert "quantum-backend" not in pr89_text
    assert "quantum-simulator" not in pr89_text
    assert "optimizer-execution" not in pr89_text
    assert "atomicrows.bundle.jsonl" not in pr89_text
    assert "atomicrows.bundle.sha256" not in pr89_text


def test_runner_pr90_replay_paper_competition_gate_has_no_runtime_source_connector_or_live_args(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]
    pr90_command = commands[
        command_names.index("validate_replay_paper_candidate_stack_competition_gate.py")
    ]

    assert pr90_command == [
        python_executable,
        str(Path("tools") / "validate_replay_paper_candidate_stack_competition_gate.py"),
        "--out",
        _default_temp_generated_report(
            "ReplayPaperCandidateStackCompetitionGate.report.json"
        ),
    ]
    pr90_text = " ".join(pr90_command).lower()
    assert "source-retrieval" not in pr90_text
    assert "source-acceptance" not in pr90_text
    assert "connector-binding" not in pr90_text
    assert "runtime-live" not in pr90_text
    assert "live-use" not in pr90_text
    assert "order-authority" not in pr90_text
    assert "profit-evidence" not in pr90_text
    assert "replay-execution" not in pr90_text
    assert "paper-execution" not in pr90_text
    assert "quantum-backend" not in pr90_text
    assert "quantum-simulator" not in pr90_text
    assert "optimizer-execution" not in pr90_text
    assert "atomicrows.bundle.jsonl" not in pr90_text
    assert "atomicrows.bundle.sha256" not in pr90_text


def test_pr81_static_contract_preserves_route_only_boundaries():
    production = trade_context_routing_gate.load_yaml(
        trade_context_routing_gate.DEFAULT_PRODUCTION_GATE
    )
    report = json.loads(
        trade_context_routing_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["routing_static_policy"]["routing_gate_is_static_only"] is True
    assert production["routing_static_policy"][
        "trade_context_to_selection_universe_static_routing_gate_created"
    ] is True
    assert report["route_scope"] == (
        "STATIC_TRADE_CONTEXT_TO_SELECTION_UNIVERSE_ELIGIBILITY_ONLY"
    )
    assert report["route_is_selection"] is False
    assert report["stack_selection_created"] is False
    assert report["selected_stack_id"] is None
    assert report["score_breakdown_created"] is False
    assert report["optimizer_arbitration_created"] is False
    assert report["runtime_authority_created"] is False
    assert report["live_authority_created"] is False
    assert report["order_authority_created"] is False
    assert report["source_retrieval_created"] is False
    assert report["source_acceptance_created"] is False
    assert report["connector_semantic_binding_created"] is False
    assert report["quantum_backend_execution_created"] is False
    assert report["quantum_advantage_claim_created"] is False
    assert report["profit_evidence_created"] is False
    assert report["random_selection_used"] is False
    assert all(
        production["explicit_no_claim_flags"][field] is False
        for field in trade_context_routing_gate.EXPLICIT_NO_CLAIM_FALSE_FIELDS
    )
    assert (Path(".") / trade_context_routing_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / trade_context_routing_gate.CANONICAL_BUNDLE_SHA256).exists()


def test_pr82_static_contract_preserves_metadata_only_boundaries():
    production = quantum_applicability_gate.load_yaml(
        quantum_applicability_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    report = json.loads(
        quantum_applicability_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["semantic_task_id"] == "ROADMAP-QUANTUM-APPLICABILITY-REGISTRY"
    assert production["registry_scope"] == "STATIC_QUANTUM_APPLICABILITY_METADATA_ONLY"
    assert production["static_only_flag"] is True
    assert production["metadata_only_flag"] is True
    assert report["classification_is_metadata_only"] is True
    assert report["backend_execution_created"] is False
    assert report["quantum_backend_execution_created"] is False
    assert report["quantum_simulator_execution_created"] is False
    assert report["optimizer_arbitration_created"] is False
    assert report["scoring_execution_created"] is False
    assert report["ranking_created"] is False
    assert report["selection_created"] is False
    assert report["runtime_authority_created"] is False
    assert report["live_authority_created"] is False
    assert report["order_authority_created"] is False
    assert report["source_retrieval_created"] is False
    assert report["source_acceptance_created"] is False
    assert report["connector_semantic_binding_created"] is False
    assert report["quantum_advantage_claim_created"] is False
    assert report["profit_evidence_created"] is False
    assert report["random_classification_used"] is False
    assert report["future_owner_quantum_priority_policy_required"] is True
    assert report["future_scoring_policy_required"] is True
    assert report["future_optimizer_arbitration_required"] is True
    assert report["missing_canonical_family_ids"] == []
    assert (Path(".") / quantum_applicability_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / quantum_applicability_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / quantum_applicability_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / quantum_applicability_gate.PR76_OLD_LONG_TEST).exists()


def test_pr83_static_contract_preserves_owner_quantum_priority_boundaries(monkeypatch, tmp_path):
    # Redirect only the CLI's output default; execute the real validator and writer.
    original_report = owner_quantum_priority_gate.DEFAULT_REPORT
    assert original_report.as_posix() == "docs/master_plan/generated/OwnerQuantumPriorityPolicyRegistry.report.json"
    before = (original_report.read_bytes(), original_report.stat().st_mode,
              original_report.stat().st_mtime_ns)
    monkeypatch.setattr(owner_quantum_priority_gate, "DEFAULT_REPORT", tmp_path / original_report.name)
    assert owner_quantum_priority_gate.main([]) == 0
    production = owner_quantum_priority_gate.load_yaml(
        owner_quantum_priority_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    report = json.loads(
        owner_quantum_priority_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["semantic_task_id"] == "ROADMAP-OWNER-QUANTUM-PRIORITY-POLICY"
    assert production["policy_scope"] == "STATIC_OWNER_QUANTUM_PRIORITY_POLICY_ONLY"
    assert production["static_only_flag"] is True
    assert production["metadata_only_flag"] is True
    assert report["policy_is_metadata_only"] is True
    assert report["owner_quantum_priority_enabled"] is True
    assert report["default_quantum_priority_mode"] == "QUANTUM_PREFERRED"
    assert report["supported_quantum_priority_modes"] == list(
        owner_quantum_priority_gate.MODE_ORDER
    )
    assert report["classical_only_families_valid_as_comparators"] is True
    assert report["hybrid_compare_requires_classical_comparator"] is True
    assert report["future_scoring_policy_required"] is True
    assert report["future_stack_ranking_gate_required"] is True
    assert report["future_optimizer_arbitration_required"] is True
    assert report["future_candidate_stack_generation_required"] is True
    assert report["future_trade_context_stack_selection_required"] is True
    assert report["future_consumer_contract_execution_created"] is False
    assert report["pr82_quantum_applicability_registry_consumed"] is True
    assert report["classical_only_label_validated_from_pr82"] is True
    for field in owner_quantum_priority_gate.ROOT_FALSE_FIELDS:
        assert report[field] is False
    assert (Path(".") / owner_quantum_priority_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / owner_quantum_priority_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / owner_quantum_priority_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / owner_quantum_priority_gate.PR76_OLD_LONG_TEST).exists()
    assert (original_report.read_bytes(), original_report.stat().st_mode,
            original_report.stat().st_mtime_ns) == before


def test_pr84_static_contract_preserves_formula_registry_only_boundaries(monkeypatch, tmp_path):
    # Redirect only the CLI's output default; execute the real validator and writer.
    original_report = scoring_policy_gate.DEFAULT_REPORT
    assert original_report.as_posix() == "docs/master_plan/generated/ParameterAlgorithmScoringPolicyRegistry.report.json"
    before = (original_report.read_bytes(), original_report.stat().st_mode,
              original_report.stat().st_mtime_ns)
    monkeypatch.setattr(scoring_policy_gate, "DEFAULT_REPORT", tmp_path / original_report.name)
    assert scoring_policy_gate.main([]) == 0
    production = scoring_policy_gate.load_yaml(
        scoring_policy_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    report = json.loads(
        scoring_policy_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["semantic_task_id"] == (
        "ROADMAP-PARAMETER-AND-ALGORITHM-SCORING-POLICY-REGISTRY"
    )
    assert production["policy_scope"] == (
        "STATIC_PARAMETER_AND_ALGORITHM_SCORING_FORMULA_REGISTRY_ONLY"
    )
    assert production["static_only_flag"] is True
    assert production["metadata_only_flag"] is True
    assert production["formula_registry_only_flag"] is True
    assert report["formula_definition_allowed"] is True
    assert report["formula_execution_created"] is False
    assert report["scoring_result_created"] is False
    assert report["ranking_created"] is False
    assert report["selection_created"] is False
    assert report["candidate_stack_generation_created"] is False
    assert report["pr82_quantum_applicability_metadata_consumed"] is True
    assert report["pr83_owner_quantum_priority_policy_consumed"] is True
    assert report["formula_ids"] == list(scoring_policy_gate.FORMULA_ORDER)
    assert report["formula_outputs"] == list(scoring_policy_gate.FORMULA_OUTPUT_ORDER)
    assert report["scoring_component_names"] == list(scoring_policy_gate.COMPONENT_ORDER)
    assert report["future_consumer_ids"] == list(scoring_policy_gate.FUTURE_CONSUMER_ORDER)
    for field in scoring_policy_gate.NO_AUTHORITY_FALSE_FIELDS:
        assert report[field] is False
    assert report["expected_net_profit_score_is_profit_evidence"] is False
    assert report["latency_fit_score_is_latency_superiority_evidence"] is False
    assert report["optimizer_score_is_optimizer_execution"] is False
    assert report["runtime_readiness_score_is_runtime_receipt"] is False
    assert report["replay_paper_score_is_replay_paper_result"] is False
    assert report["source_currentness_penalty_is_source_authority"] is False
    assert report["execution_cost_penalty_is_venue_fact"] is False
    assert report["owner_override_score_can_fabricate_external_facts"] is False
    assert (Path(".") / scoring_policy_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / scoring_policy_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / scoring_policy_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / scoring_policy_gate.PR76_OLD_LONG_TEST).exists()
    assert (original_report.read_bytes(), original_report.stat().st_mode,
            original_report.stat().st_mtime_ns) == before


def test_pr85_static_contract_preserves_parameter_stack_ranking_boundaries(monkeypatch, tmp_path):
    # Redirect only the CLI's output default; execute the real validator and writer.
    original_report = stack_scoring_gate.DEFAULT_REPORT
    assert original_report.as_posix() == "docs/master_plan/generated/ParameterStackScoringAndRankingGate.report.json"
    before = (original_report.read_bytes(), original_report.stat().st_mode,
              original_report.stat().st_mtime_ns)
    monkeypatch.setattr(stack_scoring_gate, "DEFAULT_REPORT", tmp_path / original_report.name)
    assert stack_scoring_gate.main([]) == 0
    production = stack_scoring_gate.load_yaml(
        stack_scoring_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    report = json.loads(
        stack_scoring_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["semantic_task_id"] == (
        "ROADMAP-PARAMETER-STACK-SCORING-AND-RANKING-GATE"
    )
    assert production["gate_scope"] == (
        "STATIC_PARAMETER_STACK_SCORING_AND_RANKING_CONTRACT_ONLY"
    )
    assert production["static_only_flag"] is True
    assert production["metadata_only_flag"] is True
    assert production["synthetic_fixture_only_flag"] is True
    assert production["scoring_ranking_contract_only_flag"] is True
    assert report["pr82_quantum_applicability_labels"] == list(
        stack_scoring_gate.pr84_gate.PR82_LABEL_ORDER
    )
    assert report["pr83_supported_quantum_priority_modes"] == list(
        stack_scoring_gate.pr84_gate.PR83_MODE_ORDER
    )
    assert report["pr84_formula_ids"] == list(stack_scoring_gate.FORMULA_ORDER)
    assert report["ranked_candidate_descriptor_ids"] == [
        "OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE",
        "QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE",
        "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK_STACK_FIXTURE",
        "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE",
        "TIE_BREAK_STABILITY_FIXTURE_A",
        "TIE_BREAK_STABILITY_FIXTURE_B",
    ]
    assert report["blocked_candidate_descriptor_ids"] == [
        "BLOCKED_INVALID_STACK_FIXTURE"
    ]
    assert report["highest_ranked_candidate_is_final_selected_stack"] is False
    assert report["future_pr86_optimizer_arbitration_implemented"] is False
    assert report["future_pr87_candidate_generation_implemented"] is False
    assert report["future_pr88_trade_context_selection_implemented"] is False
    for field in stack_scoring_gate.REPORT_FALSE_FIELDS:
        assert report[field] is False
    assert (Path(".") / stack_scoring_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / stack_scoring_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / stack_scoring_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / stack_scoring_gate.PR76_OLD_LONG_TEST).exists()
    assert (original_report.read_bytes(), original_report.stat().st_mode,
            original_report.stat().st_mtime_ns) == before


def test_pr86_static_contract_preserves_optimizer_arbitration_boundaries(monkeypatch, tmp_path):
    # Redirect only the CLI's output default; execute the real validator and writer.
    original_report = optimizer_arbitration_gate.DEFAULT_REPORT
    assert original_report.as_posix() == "docs/master_plan/generated/QuantumClassicalOptimizerArbitrationGate.report.json"
    before = (original_report.read_bytes(), original_report.stat().st_mode,
              original_report.stat().st_mtime_ns)
    monkeypatch.setattr(optimizer_arbitration_gate, "DEFAULT_REPORT", tmp_path / original_report.name)
    assert optimizer_arbitration_gate.main([]) == 0
    production = optimizer_arbitration_gate.load_yaml(
        optimizer_arbitration_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    report = json.loads(
        optimizer_arbitration_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["semantic_task_id"] == (
        "ROADMAP-QUANTUM-CLASSICAL-OPTIMIZER-ARBITRATION-GATE"
    )
    assert production["gate_scope"] == (
        "STATIC_QUANTUM_CLASSICAL_OPTIMIZER_ARBITRATION_CONTRACT_ONLY"
    )
    assert production["static_only_flag"] is True
    assert production["metadata_only_flag"] is True
    assert production["synthetic_fixture_only_flag"] is True
    assert production["optimizer_arbitration_contract_only_flag"] is True
    assert report["pr82_quantum_applicability_labels"] == list(
        optimizer_arbitration_gate.pr85_gate.pr84_gate.PR82_LABEL_ORDER
    )
    assert report["pr83_supported_quantum_priority_modes"] == list(
        optimizer_arbitration_gate.pr85_gate.pr84_gate.PR83_MODE_ORDER
    )
    assert report["pr84_formula_ids"] == list(
        optimizer_arbitration_gate.pr85_gate.FORMULA_ORDER
    )
    assert report["pr85_ranked_candidate_descriptor_ids"] == [
        "OWNER_OVERRIDE_QUANTUM_PRIORITY_STACK_FIXTURE",
        "QUANTUM_APPLICABLE_PREFERRED_STACK_FIXTURE",
        "HYBRID_COMPARE_THEN_QUANTUM_TIEBREAK_STACK_FIXTURE",
        "CLASSICAL_BASELINE_COMPARATOR_STACK_FIXTURE",
        "TIE_BREAK_STABILITY_FIXTURE_A",
        "TIE_BREAK_STABILITY_FIXTURE_B",
    ]
    assert report["arbitration_ordered_fixture_ids"] == list(
        optimizer_arbitration_gate.EXPECTED_ORDERED_VALID_FIXTURE_IDS
    )
    assert report["blocked_arbitration_fixture_ids"] == [
        "BLOCKED_BACKEND_EXECUTION_ATTEMPT_FIXTURE",
        "BLOCKED_MISSING_CLASSICAL_COMPARATOR_FIXTURE",
    ]
    assert report["static_arbitration_decision_is_final_selected_stack"] is False
    assert report["static_arbitration_decision_is_live_order_authority"] is False
    assert report["future_pr87_candidate_generation_implemented"] is False
    assert report["future_pr88_trade_context_selection_implemented"] is False
    assert report["future_pr90_replay_paper_competition_implemented"] is False
    for field in optimizer_arbitration_gate.REPORT_FALSE_FIELDS:
        assert report[field] is False
    assert (Path(".") / optimizer_arbitration_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / optimizer_arbitration_gate.CANONICAL_BUNDLE_SHA256).exists()
    assert (Path(".") / optimizer_arbitration_gate.PR76_SHORT_TEST).exists()
    assert not (Path(".") / optimizer_arbitration_gate.PR76_OLD_LONG_TEST).exists()
    assert (original_report.read_bytes(), original_report.stat().st_mode,
            original_report.stat().st_mtime_ns) == before


def test_pr87_static_contract_preserves_candidate_generation_boundaries(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")

    assert candidate_generation_gate.main([]) == 0
    production = candidate_generation_gate.load_yaml(
        candidate_generation_gate.DEFAULT_PRODUCTION_REGISTRY
    )
    report = json.loads(
        candidate_generation_gate.DEFAULT_REPORT.read_text(encoding="utf-8")
    )

    assert production["semantic_task_id"] == (
        "ROADMAP-CANDIDATE-PARAMETER-STACK-GENERATION-GATE"
    )
    assert production["gate_scope"] == (
        "STATIC_CANDIDATE_PARAMETER_STACK_GENERATION_GATE_ONLY"
    )
    assert production["static_only_flag"] is True
    assert production["metadata_only_flag"] is True
    assert production["synthetic_fixture_only_flag"] is True
    assert production["candidate_generation_contract_only_flag"] is True
    assert report["candidate_generation_packet_status"] == (
        "STATIC_CANDIDATE_GENERATION_PACKET_READY"
    )
    assert report["active_candidate_stack_ids"] == list(
        candidate_generation_gate.EXPECTED_ACTIVE_CANDIDATE_IDS
    )
    assert report["blocked_candidate_stack_ids"] == list(
        candidate_generation_gate.EXPECTED_BLOCKED_CANDIDATE_IDS
    )
    assert report["static_candidate_generation_packet_is_final_selection"] is False
    assert report["static_candidate_generation_packet_is_live_order_authority"] is False
    assert report["future_pr88_trade_context_selection_implemented"] is False
    assert report["future_pr90_replay_paper_competition_implemented"] is False
    for field in candidate_generation_gate.REPORT_FALSE_FIELDS:
        assert report[field] is False
    assert (Path(".") / candidate_generation_gate.CANONICAL_BUNDLE_JSONL).exists()
    assert not (Path(".") / candidate_generation_gate.CANONICAL_BUNDLE_SHA256).exists()


def test_runner_orders_source_evidence_gate_confirmation_before_connectors(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    source_evidence_index = command_names.index("validate_source_evidence_static.py")
    gate_confirmation_index = command_names.index(
        "validate_source_evidence_gate_confirmation_static.py"
    )
    retrieval_index = command_names.index("validate_source_evidence_retrieval_executor.py")
    acceptance_index = command_names.index("validate_source_evidence_acceptance.py")
    binding_index = command_names.index(
        "validate_accepted_source_to_connector_semantic_binding.py"
    )
    revalidation_index = command_names.index("validate_source_revalidation_scheduler.py")
    implementation_index = command_names.index(
        "validate_connector_semantic_binding_implementation_gate.py"
    )
    lifecycle_index = command_names.index(
        "validate_per_venue_execution_lifecycle_model.py"
    )
    normalization_index = command_names.index(
        "validate_cross_venue_execution_normalization_binding.py"
    )
    runtime_cash_index = command_names.index("runtime_cash_component_field_map_validate.py")
    private_state_index = command_names.index("private_state_read_receipt_gate_validate.py")
    credential_index = command_names.index(
        "credential_alias_secret_no_capture_readiness_validate.py"
    )
    market_data_index = command_names.index(
        "venue_market_data_ingest_adapters_validate.py"
    )
    connector_index = command_names.index("validate_connector_capability_static.py")

    assert source_evidence_index < gate_confirmation_index < retrieval_index
    assert retrieval_index < acceptance_index < binding_index < revalidation_index
    assert (
        revalidation_index
        < implementation_index
        < lifecycle_index
        < normalization_index
        < runtime_cash_index
        < private_state_index
        < credential_index
        < market_data_index
        < connector_index
    )


def test_runner_includes_per_venue_execution_lifecycle_model_validator(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert [
        python_executable,
        str(Path("tools") / "validate_per_venue_execution_lifecycle_model.py"),
        "--repo-root",
        ".",
        "--check-only",
    ] in commands


def test_runner_includes_cross_venue_execution_normalization_validator(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert [
        python_executable,
        str(Path("tools") / "validate_cross_venue_execution_normalization_binding.py"),
        "--repo-root",
        ".",
        "--check-only",
    ] in commands


def test_runner_includes_runtime_cash_component_field_map_validator(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()

    assert [
        python_executable,
        str(Path("tools") / "runtime_cash_component_field_map_validate.py"),
        "--repo-root",
        ".",
        "--check-only",
    ] in commands


def test_runner_includes_non_mutating_atomicrows_readiness_audit(monkeypatch):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    audit_command = next(
        command
        for command in commands
        if command[1] == str(Path("tools") / "validate_atomicrows_readiness_static.py")
    )

    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_readiness_static.py"),
        "--repo-root",
        ".",
        "--schema",
        str(Path("schemas") / "atomicrows" / "atomicrows_readiness_audit.schema.json"),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "atomicrows"
            / "synthetic_atomicrows_readiness_blocked.v1.fixture.json"
        ),
    ]
    assert "AtomicRows.bundle.jsonl" not in audit_command
    assert "".join(("AtomicRows.bundle", ".sha256")) not in audit_command


def test_runner_includes_non_mutating_atomicrows_unblocking_requirements_audit(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    audit_command = next(
        command
        for command in commands
        if command[1]
        == str(Path("tools") / "validate_atomicrows_unblocking_requirements_static.py")
    )

    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_unblocking_requirements_static.py"),
        "--repo-root",
        ".",
        "--schema",
        str(
            Path("schemas")
            / "atomicrows"
            / "atomicrows_unblocking_requirements_audit.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "atomicrows"
            / "synthetic_atomicrows_unblocking_requirements_required.v1.fixture.json"
        ),
    ]
    assert "AtomicRows.bundle.jsonl" not in audit_command
    assert "".join(("AtomicRows.bundle", ".sha256")) not in audit_command


def test_runner_includes_non_mutating_atomicrows_canonical_row_specification_audit(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    audit_command = next(
        command
        for command in commands
        if command[1]
        == str(
            Path("tools")
            / "validate_atomicrows_canonical_row_specification_static.py"
        )
    )

    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_canonical_row_specification_static.py"),
        "--repo-root",
        ".",
        "--schema",
        str(
            Path("schemas")
            / "atomicrows"
            / "atomicrows_canonical_row_specification_audit.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "atomicrows"
            / "synthetic_atomicrows_canonical_row_specification_required.v1.fixture.json"
        ),
    ]
    assert "AtomicRows.bundle.jsonl" not in audit_command
    assert "".join(("AtomicRows.bundle", ".sha256")) not in audit_command


def test_runner_includes_atomicrows_bundle_schema_checker_after_row_specification(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    row_spec_index = command_names.index(
        "validate_atomicrows_canonical_row_specification_static.py"
    )
    bundle_checker_index = command_names.index(
        "validate_atomicrows_bundle_schema_checker_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")
    assert row_spec_index < bundle_checker_index < no_runtime_index

    audit_command = commands[bundle_checker_index]
    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_bundle_schema_checker_static.py"),
        "--repo-root",
        ".",
        "--row-schema",
        str(Path("schemas") / "atomicrows" / "atomic_parameter_row.schema.json"),
        "--bundle-schema",
        str(Path("schemas") / "atomicrows" / "atomic_row_bundle.schema.json"),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "atomicrows"
            / "synthetic_atomicrows_bundle_bootstrap_absent.v1.fixture.json"
        ),
    ]


def test_runner_includes_generated_derivative_gate_after_bundle_checker(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    bundle_checker_index = command_names.index(
        "validate_atomicrows_bundle_schema_checker_static.py"
    )
    lifecycle_build_index = command_names.index(
        "build_atomicrows_parameter_lifecycle_report.py"
    )
    lifecycle_validate_index = command_names.index(
        "validate_atomicrows_parameter_lifecycle.py"
    )
    consumer_gate_index = command_names.index(
        "validate_atomicrows_lifecycle_consumer_gate.py"
    )
    promotion_receipt_gate_index = command_names.index(
        "validate_atomicrows_lifecycle_promotion_receipt_gate.py"
    )
    mutation_guard_index = command_names.index(
        "validate_atomicrows_lifecycle_registry_mutation_guard.py"
    )
    cumulative_readiness_index = command_names.index(
        "validate_atomicrows_lifecycle_cumulative_readiness_gate.py"
    )
    lifecycle_command_matrix_index = command_names.index(
        "validate_atomicrows_lifecycle_gate_command_matrix.py"
    )
    parameter_agent_binding_index = command_names.index(
        "validate_atomicrows_parameter_agent_binding_registry.py"
    )
    parameter_agent_binding_consumer_gate_index = command_names.index(
        "validate_atomicrows_parameter_agent_binding_consumer_gate.py"
    )
    parameter_agent_binding_cumulative_gate_index = command_names.index(
        "validate_atomicrows_parameter_agent_binding_cumulative_readiness_gate.py"
    )
    parameter_agent_binding_command_matrix_index = command_names.index(
        "validate_atomicrows_parameter_agent_binding_command_matrix.py"
    )
    research_provenance_index = command_names.index(
        "validate_atomicrows_research_provenance_evidence_tier_classification.py"
    )
    owner_intake_index = command_names.index(
        "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
    )
    candidate_family_index = command_names.index(
        "validate_atomicrows_research_source_to_candidate_family_gate.py"
    )
    parameter_stack_role_index = command_names.index(
        "validate_atomicrows_parameter_stack_role_taxonomy.py"
    )
    parameter_stack_completeness_index = command_names.index(
        "validate_atomicrows_parameter_stack_completeness_gate.py"
    )
    parameter_stack_compatibility_index = command_names.index(
        "validate_atomicrows_parameter_stack_compatibility_gate.py"
    )
    edge_packet_index = command_names.index(
        "validate_edge_parameter_stack_selection_packet.py"
    )
    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")
    assert (
        bundle_checker_index
        < lifecycle_build_index
        < lifecycle_validate_index
        < consumer_gate_index
        < promotion_receipt_gate_index
        < mutation_guard_index
        < cumulative_readiness_index
        < lifecycle_command_matrix_index
        < parameter_agent_binding_index
        < parameter_agent_binding_consumer_gate_index
        < parameter_agent_binding_cumulative_gate_index
        < parameter_agent_binding_command_matrix_index
        < research_provenance_index
        < owner_intake_index
        < candidate_family_index
        < parameter_stack_role_index
        < parameter_stack_completeness_index
        < parameter_stack_compatibility_index
        < edge_packet_index
        < generated_gate_index
        < no_runtime_index
    )
    assert commands[lifecycle_build_index] == [
        python_executable,
        str(Path("tools") / "build_atomicrows_parameter_lifecycle_report.py"),
        "--out",
        _default_temp_generated_report("AtomicRowsParameterLifecycleReport.json"),
    ]
    assert commands[lifecycle_validate_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_parameter_lifecycle.py"),
        "--mode",
        "dev",
    ]
    assert "final" not in commands[lifecycle_validate_index]
    assert commands[consumer_gate_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_lifecycle_consumer_gate.py"),
        "--mode",
        "dev",
        "--out",
        _default_temp_generated_report("AtomicRowsLifecycleConsumerGate.report.json"),
    ]
    assert commands[promotion_receipt_gate_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_lifecycle_promotion_receipt_gate.py"),
        "--mode",
        "dev",
        "--out",
        _default_temp_generated_report(
            "AtomicRowsLifecyclePromotionReceiptGate.report.json"
        ),
    ]
    assert commands[mutation_guard_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_lifecycle_registry_mutation_guard.py"),
        "--mode",
        "dev",
        "--out",
        _default_temp_generated_report(
            "AtomicRowsLifecycleRegistryMutationGuard.report.json"
        ),
    ]
    assert commands[cumulative_readiness_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_lifecycle_cumulative_readiness_gate.py"
        ),
        "--mode",
        "dev",
        "--out",
        _default_temp_generated_report(
            "AtomicRowsLifecycleCumulativeReadinessGate.report.json"
        ),
    ]
    assert commands[lifecycle_command_matrix_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_lifecycle_gate_command_matrix.py"),
        "--mode",
        "dev",
        "--out",
        _default_temp_generated_report("AtomicRowsLifecycleGateCommandMatrix.json"),
    ]
    assert commands[parameter_agent_binding_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_parameter_agent_binding_registry.py"),
        "--mode",
        "dev",
        "--out",
        _default_temp_generated_report("AtomicRowsParameterAgentBindingReport.json"),
    ]
    assert commands[parameter_agent_binding_consumer_gate_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_agent_binding_consumer_gate.py"
        ),
        "--mode",
        "dev",
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterAgentBindingConsumerGate.report.json"
        ),
    ]
    assert commands[parameter_agent_binding_cumulative_gate_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_agent_binding_cumulative_readiness_gate.py"
        ),
        "--mode",
        "dev",
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterAgentBindingCumulativeReadinessGate.report.json"
        ),
    ]
    assert commands[parameter_agent_binding_command_matrix_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_agent_binding_command_matrix.py"
        ),
        "--mode",
        "dev",
        "--out",
        _default_temp_generated_report("AtomicRowsParameterAgentBindingCommandMatrix.json"),
    ]
    assert commands[research_provenance_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_research_provenance_evidence_tier_classification.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsResearchProvenanceEvidenceTierClassification.report.json"
        ),
    ]
    assert commands[owner_intake_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_owner_submitted_research_source_intake_registry.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsOwnerSubmittedResearchSourceIntakeRegistry.report.json"
        ),
    ]
    assert commands[candidate_family_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_research_source_to_candidate_family_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsResearchSourceToCandidateFamilyGate.report.json"
        ),
    ]
    assert commands[parameter_stack_role_index] == [
        python_executable,
        str(Path("tools") / "validate_atomicrows_parameter_stack_role_taxonomy.py"),
        "--out",
        _default_temp_generated_report("AtomicRowsParameterStackRoleTaxonomy.report.json"),
    ]
    assert commands[parameter_stack_completeness_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_completeness_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterStackCompletenessGate.report.json"
        ),
    ]
    assert commands[parameter_stack_compatibility_index] == [
        python_executable,
        str(
            Path("tools")
            / "validate_atomicrows_parameter_stack_compatibility_gate.py"
        ),
        "--out",
        _default_temp_generated_report(
            "AtomicRowsParameterStackCompatibilityGate.report.json"
        ),
    ]
    assert commands[edge_packet_index] == [
        python_executable,
        str(Path("tools") / "validate_edge_parameter_stack_selection_packet.py"),
        "--out",
        _default_temp_generated_report("EDGEParameterStackSelectionPacket.report.json"),
    ]

    audit_command = commands[generated_gate_index]
    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_generated_derivative_bootstrap_gate_static.py"),
        "--repo-root",
        ".",
        "--schema",
        str(
            Path("schemas")
            / "master_plan"
            / "generated_derivative_bootstrap_gate.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "master_plan"
            / "synthetic_generated_derivative_bootstrap_gate.v1.fixture.json"
        ),
    ]


def test_runner_includes_stage1_packet_schema_gate_after_generated_derivative_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    generated_gate_index = command_names.index(
        "validate_generated_derivative_bootstrap_gate_static.py"
    )
    stage1_gate_index = command_names.index(
        "validate_stage1_packet_schema_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")
    assert generated_gate_index < stage1_gate_index < no_runtime_index

    audit_command = commands[stage1_gate_index]
    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_stage1_packet_schema_gate_static.py"),
        "--repo-root",
        ".",
        "--schema-dir",
        str(Path("schemas") / "stage1_prediction_markets"),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "stage1_prediction_markets"
            / "synthetic_stage1_packet_schema_gate_blocked.v1.fixture.json"
        ),
    ]


def test_runner_includes_venue_neutral_adapter_gate_after_stage1_and_before_no_runtime(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    stage1_gate_index = command_names.index(
        "validate_stage1_packet_schema_gate_static.py"
    )
    adapter_gate_index = command_names.index(
        "validate_venue_neutral_prediction_adapter_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")
    assert stage1_gate_index < adapter_gate_index < no_runtime_index

    audit_command = commands[adapter_gate_index]
    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_venue_neutral_prediction_adapter_gate_static.py"),
        "--repo-root",
        ".",
        "--schema-dir",
        str(Path("schemas") / "venue_neutral_prediction_adapter"),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "venue_neutral_prediction_adapter"
            / "synthetic_venue_neutral_prediction_adapter_gate_blocked.v1.fixture.json"
        ),
    ]


def test_runner_includes_connector_scaffold_gate_after_adapter_and_before_no_runtime(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    adapter_gate_index = command_names.index(
        "validate_venue_neutral_prediction_adapter_gate_static.py"
    )
    connector_scaffold_gate_index = command_names.index(
        "validate_connector_scaffold_source_required_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")
    assert adapter_gate_index < connector_scaffold_gate_index < no_runtime_index

    audit_command = commands[connector_scaffold_gate_index]
    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_connector_scaffold_source_required_gate_static.py"),
        "--repo-root",
        ".",
        "--schema",
        str(
            Path("schemas")
            / "connectors"
            / "connector_scaffold_source_required_gate.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "connectors"
            / "synthetic_connector_scaffold_source_required_blocked.v1.fixture.json"
        ),
    ]


def test_runner_includes_stage1_runtime_scaffold_gate_after_connector_and_before_no_runtime(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    connector_scaffold_gate_index = command_names.index(
        "validate_connector_scaffold_source_required_gate_static.py"
    )
    stage1_runtime_scaffold_gate_index = command_names.index(
        "validate_stage1_runtime_scaffold_gate_static.py"
    )
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")
    assert (
        connector_scaffold_gate_index
        < stage1_runtime_scaffold_gate_index
        < no_runtime_index
    )

    audit_command = commands[stage1_runtime_scaffold_gate_index]
    assert audit_command == [
        python_executable,
        str(Path("tools") / "validate_stage1_runtime_scaffold_gate_static.py"),
        "--repo-root",
        ".",
        "--schema",
        str(
            Path("schemas")
            / "runtime_orchestration"
            / "stage1_runtime_scaffold_gate.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "runtime_orchestration"
            / "synthetic_stage1_runtime_scaffold_gate_blocked.v1.fixture.json"
        ),
    ]


def test_runner_includes_pr37_static_gates_after_stage1_runtime_and_before_no_runtime(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    stage1_runtime_index = command_names.index(
        "validate_stage1_runtime_scaffold_gate_static.py"
    )
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    matrix_index = command_names.index("local_gate_command_matrix.py")
    handoff_index = command_names.index("pr_handoff_check.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert (
        stage1_runtime_index
        < qtt_gate_index
        < matrix_index
        < handoff_index
        < no_runtime_index
    )
    assert commands[qtt_gate_index] == [
        python_executable,
        str(Path("tools") / "qtt_test_gate.py"),
        "--phase",
        "first-coding-runbook",
        "--repo-root",
        ".",
        "--strict-no-claim",
        "--out",
        _default_temp_generated_report("QTTTestGate.report.json"),
    ]
    assert commands[matrix_index] == [
        python_executable,
        str(Path("tools") / "local_gate_command_matrix.py"),
        "--repo-root",
        ".",
        "--out",
        _default_temp_generated_report("LocalGateCommandMatrix.json"),
    ]
    assert commands[handoff_index] == [
        python_executable,
        str(Path("tools") / "pr_handoff_check.py"),
        "--repo-root",
        ".",
        "--out",
        _default_temp_generated_report("FirstCodingPRHandoff.packet.json"),
    ]


def test_runner_includes_pr41_runtime_resolver_contract_gate_after_pr40_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr40_index = command_names.index("stage1_connector_semantic_binding_ledger_check.py")
    pr41_index = command_names.index("stage1_runtime_resolver_snapshot_contract_check.py")
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr40_index < pr41_index < qtt_gate_index < no_runtime_index
    assert commands[pr41_index] == [
        python_executable,
        str(Path("tools") / "stage1_runtime_resolver_snapshot_contract_check.py"),
        "--repo-root",
        ".",
        "--input-lock-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver"
            / "stage1_runtime_resolver_snapshot_input_lock.schema.json"
        ),
        "--manifest-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver"
            / "stage1_runtime_resolver_snapshot_manifest.schema.json"
        ),
        "--consumer-contract-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver"
            / "stage1_runtime_resolver_consumer_contract.schema.json"
        ),
        "--gate-report-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver"
            / "stage1_runtime_resolver_snapshot_gate_report.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "source_evidence"
            / "runtime_resolver"
            / "synthetic_stage1_runtime_resolver_snapshot_contracts.v1.fixture.json"
        ),
        "--out",
        _default_temp_generated_report(
            "Stage1RuntimeResolverSnapshotContractCheck.report.json"
        ),
    ]


def test_runner_includes_pr42_runtime_resolver_to_replay_paper_handoff_after_pr41_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr41_index = command_names.index("stage1_runtime_resolver_snapshot_contract_check.py")
    pr42_index = command_names.index(
        "stage1_runtime_resolver_to_replay_paper_handoff_check.py"
    )
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr41_index < pr42_index < qtt_gate_index < no_runtime_index
    assert commands[pr42_index] == [
        python_executable,
        str(
            Path("tools")
            / "stage1_runtime_resolver_to_replay_paper_handoff_check.py"
        ),
        "--repo-root",
        ".",
        "--consumer-allowlist-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver_snapshot"
            / "stage1_runtime_resolver_snapshot_consumer_allowlist.schema.json"
        ),
        "--handoff-contract-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver_snapshot"
            / "stage1_runtime_resolver_to_replay_paper_handoff_contract.schema.json"
        ),
        "--handoff-report-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "runtime_resolver_snapshot"
            / "stage1_runtime_resolver_to_replay_paper_handoff_report.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "source_evidence"
            / "runtime_resolver_snapshot"
            / "synthetic_stage1_runtime_resolver_to_replay_paper_handoff.v1.fixture.json"
        ),
        "--out",
        _default_temp_generated_report(
            "Stage1RuntimeResolverToReplayPaperHandoff.report.json"
        ),
    ]


def test_runner_includes_pr43_concurrent_replay_paper_contract_after_pr42_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr42_index = command_names.index(
        "stage1_runtime_resolver_to_replay_paper_handoff_check.py"
    )
    pr43_index = command_names.index("stage1_concurrent_replay_paper_contract_check.py")
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr42_index < pr43_index < qtt_gate_index < no_runtime_index
    assert commands[pr43_index] == [
        python_executable,
        str(Path("tools") / "stage1_concurrent_replay_paper_contract_check.py"),
        "--repo-root",
        ".",
        "--input-identity-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "replay_paper"
            / "concurrent_replay_paper_input_identity.schema.json"
        ),
        "--replay-lane-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "replay_paper"
            / "concurrent_replay_lane_contract.schema.json"
        ),
        "--paper-lane-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "replay_paper"
            / "concurrent_paper_lane_contract.schema.json"
        ),
        "--replay-result-boundary-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "replay_paper"
            / "replay_result_packet_boundary.schema.json"
        ),
        "--paper-result-boundary-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "replay_paper"
            / "paper_result_packet_boundary.schema.json"
        ),
        "--gate-report-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "replay_paper"
            / "concurrent_replay_paper_execution_gate_report.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "source_evidence"
            / "replay_paper"
            / "synthetic_concurrent_replay_paper_contracts.v1.fixture.json"
        ),
        "--out",
        _default_temp_generated_report(
            "Stage1ConcurrentReplayPaperContractCheck.report.json"
        ),
    ]


def test_runner_includes_pr44_dual_result_review_contract_after_pr43_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr43_index = command_names.index("stage1_concurrent_replay_paper_contract_check.py")
    pr44_index = command_names.index("stage1_dual_result_review_contract_check.py")
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr43_index < pr44_index < qtt_gate_index < no_runtime_index
    assert commands[pr44_index] == [
        python_executable,
        str(Path("tools") / "stage1_dual_result_review_contract_check.py"),
        "--repo-root",
        ".",
        "--input-contract-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "dual_result_review"
            / "stage1_dual_result_review_input_contract.schema.json"
        ),
        "--comparison-matrix-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "dual_result_review"
            / "stage1_replay_paper_comparison_matrix.schema.json"
        ),
        "--gate-report-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "dual_result_review"
            / "stage1_dual_result_review_gate_report.schema.json"
        ),
        "--owner-handoff-block-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "dual_result_review"
            / "stage1_owner_live_promotion_handoff_block.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "source_evidence"
            / "dual_result_review"
            / "synthetic_stage1_dual_result_review_contracts.v1.fixture.json"
        ),
        "--out",
        _default_temp_generated_report("Stage1DualResultReviewContractCheck.report.json"),
    ]


def test_runner_includes_pr45_owner_live_promotion_review_contract_after_pr44_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr44_index = command_names.index("stage1_dual_result_review_contract_check.py")
    pr45_index = command_names.index(
        "stage1_owner_live_promotion_review_contract_check.py"
    )
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr44_index < pr45_index < qtt_gate_index < no_runtime_index
    assert commands[pr45_index] == [
        python_executable,
        str(Path("tools") / "stage1_owner_live_promotion_review_contract_check.py"),
        "--repo-root",
        ".",
        "--input-contract-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "owner_live_promotion_review"
            / "stage1_owner_live_promotion_review_input_contract.schema.json"
        ),
        "--owner-approval-receipt-boundary-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "owner_live_promotion_review"
            / "stage1_owner_approval_receipt_boundary.schema.json"
        ),
        "--gate-report-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "owner_live_promotion_review"
            / "stage1_owner_live_promotion_review_gate_report.schema.json"
        ),
        "--handoff-block-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "owner_live_promotion_review"
            / "stage1_three_venue_canary_eligibility_handoff_block.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "source_evidence"
            / "owner_live_promotion_review"
            / "synthetic_stage1_owner_live_promotion_review_contracts.v1.fixture.json"
        ),
        "--out",
        _default_temp_generated_report(
            "Stage1OwnerLivePromotionReviewContractCheck.report.json"
        ),
    ]


def test_runner_includes_pr46_three_venue_canary_eligibility_contract_after_pr45_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    pr45_index = command_names.index(
        "stage1_owner_live_promotion_review_contract_check.py"
    )
    pr46_index = command_names.index(
        "stage1_three_venue_canary_eligibility_contract_check.py"
    )
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert pr45_index < pr46_index < qtt_gate_index < no_runtime_index
    assert commands[pr46_index] == [
        python_executable,
        str(Path("tools") / "stage1_three_venue_canary_eligibility_contract_check.py"),
        "--repo-root",
        ".",
        "--input-contract-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "three_venue_canary_eligibility"
            / "stage1_three_venue_canary_eligibility_input_contract.schema.json"
        ),
        "--readiness-matrix-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "three_venue_canary_eligibility"
            / "stage1_three_venue_platform_readiness_matrix.schema.json"
        ),
        "--handoff-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "three_venue_canary_eligibility"
            / "stage1_owner_review_to_canary_eligibility_handoff.schema.json"
        ),
        "--gate-report-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "three_venue_canary_eligibility"
            / "stage1_three_venue_canary_eligibility_gate_report.schema.json"
        ),
        "--execution-block-schema",
        str(
            Path("src")
            / "qtt"
            / "stage1_prediction_markets"
            / "three_venue_canary_eligibility"
            / "stage1_limited_live_canary_execution_block.schema.json"
        ),
        "--fixture",
        str(
            Path("tests")
            / "fixtures"
            / "source_evidence"
            / "three_venue_canary_eligibility"
            / "synthetic_stage1_three_venue_canary_eligibility_contracts.v1.fixture.json"
        ),
        "--out",
        _default_temp_generated_report(
            "Stage1ThreeVenueCanaryEligibilityContractCheck.report.json"
        ),
    ]


def test_runner_includes_section_coverage_dev_gate_after_three_venue_and_before_qtt_gate(
    monkeypatch,
):
    python_executable = r"C:\repo\.venv\Scripts\python.exe"
    monkeypatch.setattr(runner.sys, "executable", python_executable)

    commands = runner.build_validation_commands()
    command_names = [Path(command[1]).name for command in commands]

    three_venue_index = command_names.index(
        "stage1_three_venue_canary_eligibility_contract_check.py"
    )
    build_index = command_names.index("build_master_plan_section_coverage_report.py")
    validate_index = command_names.index("validate_master_plan_section_coverage.py")
    triage_routes_index = command_names.index(
        "validate_qtt_master_plan_section_coverage_triage_routes.py"
    )
    crosswalk_index = command_names.index(
        "validate_qtt_master_plan_section_roadmap_crosswalk.py"
    )
    command_matrix_index = command_names.index(
        "validate_qtt_master_plan_section_coverage_command_matrix.py"
    )
    qtt_gate_index = command_names.index("qtt_test_gate.py")
    no_runtime_index = command_names.index("validate_no_runtime_artifacts.py")

    assert three_venue_index < build_index < validate_index < triage_routes_index
    assert triage_routes_index < crosswalk_index < command_matrix_index < qtt_gate_index
    assert qtt_gate_index < no_runtime_index
    assert commands[build_index] == [
        python_executable,
        str(Path("tools") / "build_master_plan_section_coverage_report.py"),
        "--out",
        _default_temp_generated_report("MasterPlanSectionCoverageReport.json"),
    ]
    assert commands[validate_index] == [
        python_executable,
        str(Path("tools") / "validate_master_plan_section_coverage.py"),
        "--mode",
        "dev",
    ]
    assert "final" not in commands[validate_index]
    assert commands[triage_routes_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_master_plan_section_coverage_triage_routes.py"),
    ]
    assert commands[crosswalk_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_master_plan_section_roadmap_crosswalk.py"),
    ]
    assert commands[command_matrix_index] == [
        python_executable,
        str(Path("tools") / "validate_qtt_master_plan_section_coverage_command_matrix.py"),
    ]


def test_runner_stops_on_first_failure_and_returns_failing_exit_code(monkeypatch, capsys):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [["python", "gate_a.py"], ["python", "gate_b.py"], ["python", "gate_c.py"]]
    returncodes = [0, 9, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 9
    assert seen == commands[:2]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_owner_intake_validator_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 7, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 7
    assert seen == commands[:2]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_candidate_family_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 11, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 11
    assert seen == commands[:3]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_parameter_stack_role_taxonomy_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "validate_atomicrows_parameter_stack_role_taxonomy.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 13, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 13
    assert seen == commands[:4]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_parameter_stack_completeness_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "validate_atomicrows_parameter_stack_role_taxonomy.py"],
        ["python", "validate_atomicrows_parameter_stack_completeness_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 17, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 17
    assert seen == commands[:5]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_parameter_stack_compatibility_gate_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "validate_atomicrows_parameter_stack_role_taxonomy.py"],
        ["python", "validate_atomicrows_parameter_stack_completeness_gate.py"],
        ["python", "validate_atomicrows_parameter_stack_compatibility_gate.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 19, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 19
    assert seen == commands[:6]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_edge_packet_validator_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "validate_atomicrows_parameter_stack_role_taxonomy.py"],
        ["python", "validate_atomicrows_parameter_stack_completeness_gate.py"],
        ["python", "validate_atomicrows_parameter_stack_compatibility_gate.py"],
        ["python", "validate_edge_parameter_stack_selection_packet.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 23, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 23
    assert seen == commands[:7]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_qtt_trade_context_packet_validator_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "validate_atomicrows_parameter_stack_role_taxonomy.py"],
        ["python", "validate_atomicrows_parameter_stack_completeness_gate.py"],
        ["python", "validate_atomicrows_parameter_stack_compatibility_gate.py"],
        ["python", "validate_edge_parameter_stack_selection_packet.py"],
        ["python", "validate_qtt_trade_context_packet.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 29, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 29
    assert seen == commands[:8]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_does_not_emit_success_marker_if_selection_universe_registry_fails(
    monkeypatch,
    capsys,
):
    class Completed:
        def __init__(self, returncode: int) -> None:
            self.returncode = returncode

    commands = [
        [
            "python",
            "validate_atomicrows_research_provenance_evidence_tier_classification.py",
        ],
        [
            "python",
            "validate_atomicrows_owner_submitted_research_source_intake_registry.py",
        ],
        [
            "python",
            "validate_atomicrows_research_source_to_candidate_family_gate.py",
        ],
        ["python", "validate_atomicrows_parameter_stack_role_taxonomy.py"],
        ["python", "validate_atomicrows_parameter_stack_completeness_gate.py"],
        ["python", "validate_atomicrows_parameter_stack_compatibility_gate.py"],
        ["python", "validate_edge_parameter_stack_selection_packet.py"],
        ["python", "validate_qtt_trade_context_packet.py"],
        ["python", "validate_atomicrows_parameter_selection_universe_registry.py"],
        ["python", "later_gate.py"],
    ]
    returncodes = [0, 0, 0, 0, 0, 0, 0, 0, 31, 0]
    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed(returncodes[len(seen) - 1])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(commands)

    assert exit_code == 31
    assert seen == commands[:9]
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_timing_summary_preserves_success_return_code(monkeypatch, capsys):
    class Completed:
        returncode = 0

    seen: list[list[str]] = []

    def fake_run(command: list[str]) -> Completed:
        seen.append(command)
        return Completed()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands([["python", "ok.py"]], phase="timing-test")

    output = capsys.readouterr().out
    assert exit_code == 0
    assert seen == [["python", "ok.py"]]
    assert "QTT_VALIDATION_TIMING_COMMAND phase=timing-test" in output
    assert "QTT_VALIDATION_TIMING_TOTAL phase=timing-test" in output
    assert output.splitlines()[-1] == runner.SUCCESS_MARKER


def test_runner_timing_summary_preserves_failure_return_code(monkeypatch, capsys):
    class Completed:
        returncode = 7

    def fake_run(command: list[str], **kwargs) -> Completed:
        return Completed()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands([["python", "fails.py"]], phase="timing-test")

    output = capsys.readouterr().out
    assert exit_code == 7
    assert "QTT_VALIDATION_TIMING_TOTAL phase=timing-test" in output
    assert runner.SUCCESS_MARKER not in output


def test_st12g_validators_are_in_full_gate_and_failure_propagates(
    monkeypatch,
    capsys,
):
    commands = runner.build_deterministic_validator_commands(
        Path(".tmp/st12g-gate"),
        Path(".tmp/st12g-gate/pytest"),
    )
    command_text = {" ".join(command) for command in commands}
    assert any(
        "validate_qku_computation_control_plane.py --domain g" in command
        for command in command_text
    )
    assert any(
        command.endswith("independent_validate_qku_computation_control_plane_g.py")
        for command in command_text
    )
    assert any(
        "validate_pr169_dash1_owner_dashboard_ui.py" in command
        for command in command_text
    )

    class Completed:
        returncode = 19

    monkeypatch.setattr(runner.subprocess, "run", lambda command, **kwargs: Completed())
    exit_code = runner.run_commands(
        [["python", "tools/independent_validate_qku_computation_control_plane_g.py"]],
        phase="st12g-failure-propagation",
    )
    assert exit_code == 19
    assert runner.SUCCESS_MARKER not in capsys.readouterr().out


def test_runner_timing_report_writes_only_when_requested(monkeypatch, tmp_path):
    class Completed:
        returncode = 0

    def fake_run(command: list[str], **kwargs) -> Completed:
        return Completed()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    report_path = tmp_path / "timing" / "report.json"

    assert runner.run_commands([["python", "ok.py"]], phase="no-report") == 0
    assert not report_path.exists()

    assert (
        runner.run_commands(
            [["python", "ok.py"]],
            phase="with-report",
            timing_report_path=report_path,
        )
        == 0
    )
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == runner.TIMING_SCHEMA_VERSION
    assert payload["phase"] == "with-report"
    assert payload["runtime_budget_policy"] == runner.RUNTIME_BUDGET_POLICY
    assert payload["runtime_budget_warnings"] == []
    assert payload["command_entries"][0]["command"] == ["python", "ok.py"]
    assert payload["slowest_entries"]
    assert payload["total_elapsed_seconds"] >= 0


def test_runner_rejects_tracked_generated_timing_report_path(monkeypatch):
    class Completed:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(command: list[str], **kwargs) -> Completed:
        return Completed()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    exit_code = runner.run_commands(
        [["python", "ok.py"]],
        repo_root=REPO_ROOT,
        phase="bad-report",
        timing_report_path=(
            REPO_ROOT
            / "docs"
            / "master_plan"
            / "generated"
            / "timing.json"
        ),
    )

    assert exit_code == 2


def test_runner_returns_zero_when_all_mocked_commands_pass(monkeypatch, capsys, tmp_path, _central_supervision_test_adapter):
    _clear_branch_context_env(monkeypatch)
    fixture_repo = tmp_path / "mocked-runner-repo"
    fixture_repo.mkdir()
    monkeypatch.setattr(runner, "_repo_root", lambda: fixture_repo)

    class Completed:
        def __init__(self, stdout: str = "", stderr: str = "") -> None:
            self.returncode = 0
            self.stdout = stdout
            self.stderr = stderr

    seen: list[list[str]] = []
    provenance_counts: list[int] = []
    completion_receipts = []

    def fake_run(command: list[str], **kwargs) -> Completed:
        if command[0] == "git":
            return Completed()
        seen.append(command)
        return Completed(stdout=_st12h_mock_terminal_output(command))

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        runner,
        "write_run_provenance",
        lambda _paths, _probe, **kwargs: provenance_counts.append(
            kwargs["command_count"]
        ),
    )
    monkeypatch.setattr(
        runner,
        "atomic_write_json",
        lambda path, payload: completion_receipts.append(payload)
        if Path(path).name == "completion.json"
        else None,
    )
    monkeypatch.setattr(
        runner,
        "_routed_generated_output_currentness_failures",
        lambda command, repo_root: [],
    )

    # A synthetic success dependency must remain explicit, never a default.
    scan_vector = (sys.executable, "tools/build_pr168_rp5a_legacy_semantic_audit.py")
    negative_plan = reliability.build_command_evidence_plan(
        run_id="run_test_supervision_active", phase=runner.ALL_PHASE,
        commands=(scan_vector,), cwd=fixture_repo,
    )
    with monkeypatch.context() as absent_capacity:
        absent_capacity.setattr(runner, "_ACTIVE_SCAN_CAPACITY_SOURCE", None)
        absent_capacity.setattr(runner, "_ACTIVE_SCAN_LAUNCH", None)
        absent_capacity.setattr(runner, "_SCAN_CAPACITY_ATTEMPTED", False)
        with pytest.raises(ValueError, match="independently admitted scan capacity source"):
            runner._scan_resolve_parent_capacity(
                runner._RUN_COMMANDS_ACTIVE_PATHS, runner.ALL_PHASE, negative_plan,
            )
        assert runner._ACTIVE_SCAN_LAUNCH is None
        assert seen == [] and provenance_counts == []

    exit_code = runner.main([], **_central_supervision_test_adapter())

    assert exit_code == 0
    validation_dir = _validation_dir_from_commands(seen)
    pytest_basetemp = _pytest_basetemp_from_commands(seen)
    assert pytest_basetemp.name == reliability.PYTEST_BASETEMP_DIR_NAME
    expected = [
        runner._execution_command_with_qku_root_importlib(
            runner._execution_command_with_st12g_architecture_roster(command)
        )
        for command in runner.build_phase_commands(
            runner.ALL_PHASE,
            validation_dir,
            pytest_basetemp,
        )
        if command[0] != "git"
    ]
    assert seen == expected
    output = capsys.readouterr().out.splitlines()
    assert output[-1] == runner.SUCCESS_MARKER
    assert output.count(
        "QTT_QKU_ROOT_PYTEST_IMPORT_MODE_APPLIED "
        "mode=importlib "
        f"selected_root={runner.ST12A_TEST_ROOT}"
    ) == 1
    architecture_command = list(
        runner.build_st12g_architecture_validation_command(sys.executable)
    )
    assert architecture_command in seen
    assert subprocess.list2cmdline(architecture_command) in output
    assert provenance_counts == [completion_receipts[-1].command_count_planned]
    assert completion_receipts[-1].command_count_started == provenance_counts[0]
    assert completion_receipts[-1].command_count_completed == provenance_counts[0]

    # Mixed v2/v3 provenance uses real typed inputs and ordinary local paths.
    # No command below invokes a scanner/domain body or grants a real campaign.
    import dataclasses
    import stat
    import time
    from types import MappingProxyType
    from tools import pr168_rp5a_git_grep_scanner as scan_owner
    mixed_root = tmp_path / "mixed-wire-repository"
    mixed_root.mkdir()
    live = mixed_root / "data.bin"
    live.write_bytes(b"\x00\xffAB")
    snapshot_root = tmp_path / "mixed-wire-snapshots"
    snapshot_root.mkdir()
    saved = snapshot_root / "data.bin"
    saved.write_bytes(b"\x00\xffAB")
    descriptor = reliability._open_regular_worktree_descriptor(saved)
    try:
        snapshot_version = reliability._scan_same_api_version(os.fstat(descriptor))
    finally:
        os.close(descriptor)
    carrier = reliability._ScanDiskSnapshotV3("data.bin", saved, snapshot_version,
        reliability._scan_file_identity(live.lstat()), stat.S_IMODE(live.stat().st_mode), 4)
    disk_rows = (reliability._ScanCandidateSurface("data.bin", "FILE", carrier.mode, carrier, ()),)
    byte_rows = (reliability._ScanCandidateSurface("data.bin", "FILE", carrier.mode, b"\x00\xffAB", ()),)
    mixed_paths, mixed_probe = reliability.resolve_validation_run_paths(
        mixed_root, explicit_process_root=tmp_path / "mixed-wire-process",
        run_id="run_mixed_v3_provenance", projected_relative_paths=("command-2.json",))
    phase = "mixed-wire-fixture"
    command_vectors = (
        (sys.executable, "-B", "tools/build_pr168_rp5a_legacy_semantic_audit.py", "--offline"),
        (sys.executable, "-B", "tools/run_pytest_fresh_basetemp.py", "tests/pr168_rp5a"))
    mixed_plan = reliability.build_command_evidence_plan(run_id=mixed_paths.run_id, phase=phase,
        commands=command_vectors, cwd=mixed_root)
    limits = reliability._ScanRunReadLimits(2_000_000, 50_000, 64, 3)
    deadline = time.monotonic_ns() + 120_000_000_000
    basis = reliability._Rp5aReadBasisV1("1" * 40, b"# synthetic historical source\n",
        100000, 10, 512, 100000, 10000, 100, 1000)
    executable = str(Path(shutil.which("git")).resolve())
    profiles = []
    for name, index in (("scan", 1), ("reader1", 1), ("reader2", 2)):
        directory = mixed_paths.process_root / name
        directory.mkdir()
        profiles.append(reliability._Rp5aScanProfile(mixed_paths.run_id, index, str(mixed_root), str(directory),
            ("data.bin",), 1, 9, (("data.bin", 4),), executable, executable, "git",
            tuple(scan_owner._scan_child_environment(os.environ).items()),
            1000000, 1000000, 4096, 2000000, deadline, 10))
    inputs = {}
    for index in (1, 2):
        directory = mixed_paths.process_root / ("input" + str(index))
        directory.mkdir()
        is_v3 = index == 1
        fence = reliability._ScanCandidateFence(mixed_root, disk_rows if is_v3 else byte_rows,
            limits=limits, candidate_read_bytes=1000000, deadline_ns=deadline,
            **({"wire_version":3, "surface_role":"sender", "snapshot_root":snapshot_root} if is_v3 else {}))
        identity = reliability._ScanLaunchIdentity(mixed_paths.run_id, phase, index, 2,
            command_vectors[index - 1], str(mixed_root))
        inputs[index] = reliability._ScanLaunchInput(identity, disk_rows if is_v3 else byte_rows,
            limits=limits, candidate_read_bytes=1000000, deadline_ns=deadline, scratch_root=directory,
            scratch_bytes=2000000, parent_frame_reread_bytes=10000000, check_candidate=fence,
            rp5a_read_basis=basis, **({"wire_version":3, "snapshot_root":snapshot_root} if is_v3 else {}))
    readers = {1:profiles[1], 2:profiles[2]}
    bases = {1:basis, 2:basis}
    def prepare(plan=mixed_plan, **changes):
        operands = {"phase":phase, "plan":plan, "profiles":{1:profiles[0]}, "reader_profiles":readers,
            "reader_bases":bases, "launch_inputs":inputs, "read_limits":limits, "deadline_ns":deadline}
        operands.update(changes)
        return reliability._prepare_scan_launch(mixed_paths, **operands)
    launch = prepare()
    assert launch.plan is mixed_plan and launch.reader_profiles[1] is profiles[1] and launch.reader_bases[1] is basis
    assert dict(launch.rp5a_launch_wire_versions) == {1:3, 2:2}
    assert dict(launch.rp5a_payload_byte_limits) == {1:4, 2:0}
    with pytest.raises(TypeError):
        launch.rp5a_payload_byte_limits[1] = 5
    for changes in (
        {"reader_profiles": {1:profiles[1]}}, {"reader_bases": {2:basis}},
        {"reader_profiles": {**readers,3:dataclasses.replace(profiles[2],command_index=3)}},
        {"profiles": {}}, {"launch_inputs": {1:inputs[1]}},
    ):
        with pytest.raises((ValueError,TypeError)):
            prepare(**changes)
    for versions, counts in (({1:3,2:3},{1:4,2:0}), ({1:3},{1:4}), ({1:3,2:2},{1:5,2:0}),
                             ({1:True,2:2},{1:4,2:0}), ({1:3,2:2},{1:4,2:True})):
        with pytest.raises((ValueError,TypeError)):
            dataclasses.replace(launch, rp5a_launch_wire_versions=MappingProxyType(versions),
                                rp5a_payload_byte_limits=MappingProxyType(counts))
    publication = {"phase":phase, "command_count":2, "text_integrity_preflight_state":"PASS",
        "rp5a_scan_profiles":launch.profiles, "rp5a_reader_profiles":launch.reader_profiles,
        "rp5a_reader_bases":launch.reader_bases, "rp5a_launch_wire_versions":launch.rp5a_launch_wire_versions,
        "rp5a_payload_byte_limits":launch.rp5a_payload_byte_limits}
    expected_keys = {"schema_version","run_id","phase","command_count","text_integrity_preflight_state",
        "paths","filesystem_probe","rp5a_scan_profiles","rp5a_reader_profiles","rp5a_reader_bases",
        "rp5a_launch_wire_version","rp5a_launch_wire_versions","rp5a_payload_byte_limits"}
    run_payload = reliability._run_provenance_payload(mixed_paths,mixed_probe,**publication)
    assert set(run_payload) == expected_keys and run_payload["rp5a_launch_wire_version"] == 3
    assert run_payload["rp5a_launch_wire_versions"] == {"1":3,"2":2}
    assert run_payload["rp5a_payload_byte_limits"] == {"1":4,"2":0}
    legacy_publication = {key:value for key,value in publication.items()
                          if key not in {"rp5a_launch_wire_versions","rp5a_payload_byte_limits"}}
    legacy_payload = reliability._run_provenance_payload(mixed_paths,mixed_probe,**legacy_publication)
    assert set(legacy_payload) == expected_keys - {"rp5a_launch_wire_versions","rp5a_payload_byte_limits"}
    assert legacy_payload["rp5a_launch_wire_version"] == 2
    reliability.write_run_provenance(mixed_paths,mixed_probe,**publication)
    # Real finite operational decode and lease scopes, with explicit no-child
    # body/close faults. Neither a scanner body nor a builder output runs.
    from tools import build_pr168_rp5a_legacy_semantic_audit as builder
    for scope_case in ("success", "body", "body-and-close", "construction"):
        original = inputs[1]
        scope_input = reliability._ScanLaunchInput(original.identity, original.candidate_files,
            limits=limits, candidate_read_bytes=1000000, deadline_ns=deadline,
            scratch_root=original.scratch_root, scratch_bytes=2000000, parent_frame_reread_bytes=10000000,
            check_candidate=original.check_candidate, rp5a_read_basis=basis,
            wire_version=3, snapshot_root=snapshot_root)
        with scope_input:
            decoded = reliability._read_rp5a_bound_launch_fd_v1(scope_input.reader.fileno(),
                repo_root=mixed_root, environment=reliability._scan_child_launch_environment(
                    {},launch=launch,planned=mixed_plan[0]),
                explicit_basetemp=mixed_paths.pytest_basetemp_root,
                original_argv=command_vectors[0],expected_role="SCANNER")
            assert len(decoded) == 6 and decoded[5] is None
            fence = decoded[4]
            lease = fence.payload_lease
            assert lease.initial_consumption_complete and fence.wire_version == 3
            ledger = reliability._ScanReservationLedger(profiles[1],reader_only=True)
            context = builder._Rp5aBuilderReadContext(ledger=ledger,
                **{name:getattr(basis,name) for name in tuple(basis.__dataclass_fields__)[2:]},
                expected_historical_source=basis.historical_runner_bytes,
                current_runner_source=b"# current\n",expected_current_runner_source=b"# current\n",
                scope_source=b"# scope\n",expected_scope_source=b"# scope\n",
                python_executable=sys.executable,check_candidate=fence,before_surfaces=MappingProxyType({}),
                observe_surfaces=fence.observe_surfaces,expected_baseline_ref=basis.baseline_ref)
            body_error = RuntimeError("original scoped body failure")
            close_error = OSError("original scoped lease close failure")
            original_close = reliability.os.close
            with monkeypatch.context() as scope_fault:
                if scope_case == "body-and-close":
                    def failing_close(fd):
                        original_close(fd)
                        if fd == lease._fd:
                            raise close_error
                    scope_fault.setattr(reliability.os,"close",failing_close)
                if scope_case == "construction":
                    scope_fault.setattr(builder.sys,"stdin",scope_input.reader)
                    scope_fault.setattr(reliability,"_read_rp5a_bound_launch_fd_v1",lambda *args,**kwargs:decoded)
                    def failed_reconstruction(*args,**kwargs):
                        raise body_error
                    scope_fault.setattr(builder,"_rp5a_reconstruct_reader_v1",failed_reconstruction)
                    with pytest.raises(RuntimeError) as caught:
                        builder._standalone_main_v1(["--offline"])
                    assert caught.value is body_error
                elif scope_case == "success":
                    with builder._rp5a_bound_reader_v1(context):
                        assert builder._require_builder_reads_v1() is context
                else:
                    with pytest.raises(RuntimeError if scope_case == "body" else BaseExceptionGroup) as caught:
                        with builder._rp5a_bound_reader_v1(context):
                            raise body_error
                    assert (caught.value is body_error if scope_case == "body"
                            else caught.value.exceptions == (body_error,close_error))
            assert lease._close_attempted
            assert lease.closed if scope_case != "body-and-close" else lease.held
            assert builder._BUILDER_READ_SCOPE_V1.get() is None
        assert not scope_input.path.exists()
    for index in (1,2):
        forwarded = reliability._scan_child_launch_environment({},launch=launch,planned=mixed_plan[index - 1])
        default = reliability._scan_read_forwarded_profile(mixed_root,environment=forwarded,
            explicit_basetemp=mixed_paths.pytest_basetemp_root,reader_required=True)
        selected = reliability._scan_read_forwarded_profile(mixed_root,environment=forwarded,
            explicit_basetemp=mixed_paths.pytest_basetemp_root,reader_required=True,include_wire_binding=True)
        assert len(default) == 4 and len(selected) == 6
        assert selected[1:] == (*default[1:],3 if index==1 else 2,4 if index==1 else 0)
        assert default[3] == basis
        value = selected[0]._scan_snapshot.value
        for wire_changes in (
            {"rp5a_launch_wire_versions":MappingProxyType({"1":3})},
            {"rp5a_payload_byte_limits":MappingProxyType({"1":4,"2":1})},
            {"rp5a_launch_wire_versions":MappingProxyType({"1":3,"2":3})},
            {"rp5a_payload_byte_limits":MappingProxyType({"1":True,"2":0})},
            {"rp5a_launch_wire_version":2},
        ):
            with pytest.raises((ValueError,TypeError)):
                reliability._rp5a_reader_profiles_from_run_v1(selected[0],MappingProxyType({**value,**wire_changes}),
                    command_index=index,repo_root=mixed_root,inherited_run_id=mixed_paths.run_id,
                    read_limits=limits,deadline_ns=deadline,include_wire_binding=True)
    # Wrong operational argv is rejected before a decoder/descriptor acquisition.
    for argv,role in (((sys.executable,"transport_diagnostic.py"),"SCANNER"),
                      ((sys.executable,"tools/validate_pr168_rp5a_legacy_semantic_audit.py"),"VALIDATE"),
                      ((sys.executable,"tools/run_pytest_fresh_basetemp.py","tests/pr168_rp5a"),"PYTEST"),
                      ((sys.executable,"tools/build_pr168_rp5a_legacy_semantic_audit.py","--validation-scope-evidence-only"),"EVIDENCE")):
        calls = []
        with monkeypatch.context() as denied:
            denied.setattr(reliability,"_read_scan_launch_fd",lambda *args,**kwargs:calls.append((args,kwargs)))
            with pytest.raises(ValueError):
                reliability._read_rp5a_bound_launch_fd_v1(99999,repo_root=mixed_root,
                    environment=reliability._scan_child_launch_environment({},launch=launch,planned=mixed_plan[0]),
                    explicit_basetemp=mixed_paths.pytest_basetemp_root,original_argv=argv,expected_role=role)
        assert calls == []
    # Original runner publishes exactly one plan and forwards both new tables.
    published = []
    capacity_calls = []
    selected_launches = []
    def capacity(paths, selected_phase, plan):
        assert paths is mixed_paths and selected_phase == phase
        capacity_calls.append(plan)
        value = prepare(plan)
        selected_launches.append(value)
        return value
    publication_state = {name: getattr(runner, name) for name in (
        "_LAST_PLANNED_COMMAND_COUNT", "_LAST_EXPECTED_COMMAND_PLAN", "_RUN_PROVENANCE_WRITTEN")}
    with monkeypatch.context() as forwarding:
        # Register the publisher's direct assignments for exact scoped teardown,
        # including when an assertion or the publisher itself raises.
        for name, value in publication_state.items():
            forwarding.setattr(runner, name, value)
        forwarding.setattr(runner,"_RUN_COMMANDS_ACTIVE_PATHS",mixed_paths)
        forwarding.setattr(runner,"_ACTIVE_FILESYSTEM_PROBE",mixed_probe)
        forwarding.setattr(runner,"_ACTIVE_TEXT_INTEGRITY_STATE","PASS")
        forwarding.setattr(runner,"_LAST_PLANNED_COMMAND_COUNT",None)
        forwarding.setattr(runner,"_LAST_EXPECTED_COMMAND_PLAN",())
        forwarding.setattr(runner,"_MAPPER_READ_SOURCE_ATTEMPTED",False)
        forwarding.setattr(runner,"_ACTIVE_MAPPER_READ_SOURCE_V1",None)
        forwarding.setattr(runner,"_ACTIVE_MAPPER_READ_PROFILES_V1",None)
        forwarding.setattr(runner,"_RUN_PROVENANCE_ATTEMPTED",False)
        forwarding.setattr(runner,"_SCAN_CAPACITY_ATTEMPTED",False)
        forwarding.setattr(runner,"_ACTIVE_SCAN_CAPACITY_SOURCE",capacity)
        forwarding.setattr(runner,"_ACTIVE_SCAN_LAUNCH",None)
        forwarding.setattr(runner,"write_run_provenance",lambda paths,probe,**kwargs:published.append((paths,probe,kwargs)))
        runner._publish_active_plan_provenance(phase,runner._prepare_execution_plan(command_vectors))
        assert len(capacity_calls) == len(published) == len(selected_launches) == 1
        selected_launch = selected_launches[0]
        assert capacity_calls[0] is runner._LAST_EXPECTED_COMMAND_PLAN is selected_launch.plan
        assert published[0][2]["rp5a_launch_wire_versions"] is selected_launch.rp5a_launch_wire_versions
        assert published[0][2]["rp5a_payload_byte_limits"] is selected_launch.rp5a_payload_byte_limits
        with pytest.raises(ValueError):
            runner._publish_active_plan_provenance(phase,runner._prepare_execution_plan(command_vectors))
        assert len(capacity_calls) == 1
    assert all(getattr(runner, name) is value for name, value in publication_state.items())
    # Completion uses the real original evidence validator; no child was
    # dispatched, so this synthetic terminal record is explicitly FAIL.
    completed_bindings = []
    original_validator = reliability.validate_complete_run_evidence
    def observed_validation(*args,**kwargs):
        completed_bindings.append(kwargs)
        return original_validator(*args,**kwargs)
    with monkeypatch.context() as completion:
        completion.setattr(runner,"_RUN_COMMANDS_SUPERVISION",None)
        completion.setattr(runner,"cleanup_validation_run",reliability.cleanup_validation_run)
        completion.setattr(runner,"atomic_write_json",reliability.atomic_write_json)
        completion.setattr(runner,"validate_complete_run_evidence",observed_validation)
        completion.setattr(runner,"validate_published_completion_receipt",reliability.validate_published_completion_receipt)
        result,cleanup,receipt = runner._finalize_validation_run(run_paths=mixed_paths,probe=mixed_probe,
            phase=phase,planned_count=2,expected_plan=mixed_plan,receipts=(),result=1,text_state="PASS",scan_launch=launch)
    assert result == 1 and receipt.final_state == "FAIL"
    assert cleanup == "PASS_REMOVED_EXACT_RUN_ROOT"
    assert len(completed_bindings) == 1
    assert completed_bindings[0]["rp5a_launch_wire_versions"] is launch.rp5a_launch_wire_versions
    assert completed_bindings[0]["rp5a_payload_byte_limits"] is launch.rp5a_payload_byte_limits
    assert not mixed_paths.process_root.exists()
    capsys.readouterr()


def test_runner_sets_run_local_no_runtime_scan_cache_env(monkeypatch, tmp_path):
    _clear_branch_context_env(monkeypatch)
    monkeypatch.delenv(runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV, raising=False)
    monkeypatch.delenv(runner.PR152_BUILD_REPORT_CACHE_ENV, raising=False)

    repo_root = (tmp_path / "test_run_validation_gates_scan_cache").resolve()
    shutil.rmtree(repo_root, ignore_errors=True)
    repo_root.mkdir(parents=True)
    cache_paths: list[Path] = []
    pr152_cache_paths: list[Path] = []

    def fake_run_commands(
        commands: list[list[str]],
        repo_root: Path | None = None,
        **kwargs,
    ) -> int:
        cache_text = os.environ.get(runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV)
        assert cache_text is not None
        cache_path = Path(cache_text)
        assert cache_path.name == "NoRuntimeArtifactScanCache.json"
        assert cache_path.parent.name == reliability.VALIDATION_OUTPUT_DIR_NAME
        cache_paths.append(cache_path)
        pr152_cache_text = os.environ.get(runner.PR152_BUILD_REPORT_CACHE_ENV)
        assert pr152_cache_text is not None
        pr152_cache_path = Path(pr152_cache_text)
        assert pr152_cache_path.name == "PR152BuildReportCache.json"
        assert pr152_cache_path.parent.name == reliability.VALIDATION_OUTPUT_DIR_NAME
        pr152_cache_paths.append(pr152_cache_path)
        _record_fake_aggregate_success_receipts(commands)
        return 0

    monkeypatch.setattr(runner, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(runner, "run_commands", fake_run_commands)

    try:
        assert runner.main(["--phase", "fast-preflight"]) == 0
        assert cache_paths
    finally:
        shutil.rmtree(repo_root, ignore_errors=True)

    assert os.environ.get(runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV) is None
    assert os.environ.get(runner.PR152_BUILD_REPORT_CACHE_ENV) is None
    assert pr152_cache_paths


def test_runner_preserves_explicit_no_runtime_scan_cache_env(monkeypatch, tmp_path):
    _clear_branch_context_env(monkeypatch)

    repo_root = (tmp_path / "test_run_validation_gates_explicit_scan_cache").resolve()
    shutil.rmtree(repo_root, ignore_errors=True)
    repo_root.mkdir(parents=True)
    explicit_cache = repo_root / ".tmp" / "explicit_scan_cache.json"
    monkeypatch.setenv(runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV, str(explicit_cache))
    seen: list[str] = []

    def fake_run_commands(
        commands: list[list[str]],
        repo_root: Path | None = None,
        **kwargs,
    ) -> int:
        seen.append(os.environ[runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV])
        _record_fake_aggregate_success_receipts(commands)
        return 0

    monkeypatch.setattr(runner, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(runner, "run_commands", fake_run_commands)

    try:
        assert runner.main(["--phase", "fast-preflight"]) == 0
        assert seen == [str(explicit_cache)]
        assert os.environ[runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV] == str(
            explicit_cache
        )
    finally:
        shutil.rmtree(repo_root, ignore_errors=True)


def test_runner_preserves_explicit_pr152_build_report_cache_env(monkeypatch, tmp_path):
    _clear_branch_context_env(monkeypatch)

    repo_root = (tmp_path / "test_run_validation_gates_explicit_pr152_cache").resolve()
    shutil.rmtree(repo_root, ignore_errors=True)
    repo_root.mkdir(parents=True)
    explicit_cache = repo_root / ".tmp" / "explicit_pr152_build_cache.json"
    monkeypatch.setenv(runner.PR152_BUILD_REPORT_CACHE_ENV, str(explicit_cache))
    seen: list[str] = []

    def fake_run_commands(
        commands: list[list[str]],
        repo_root: Path | None = None,
        **kwargs,
    ) -> int:
        seen.append(os.environ[runner.PR152_BUILD_REPORT_CACHE_ENV])
        _record_fake_aggregate_success_receipts(commands)
        return 0

    monkeypatch.setattr(runner, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(runner, "run_commands", fake_run_commands)

    try:
        assert runner.main(["--phase", "fast-preflight"]) == 0
        assert seen == [str(explicit_cache)]
        assert os.environ[runner.PR152_BUILD_REPORT_CACHE_ENV] == str(explicit_cache)
    finally:
        shutil.rmtree(repo_root, ignore_errors=True)


def _no_runtime_strict_options():
    from tools.validate_no_runtime_artifacts import ScanOptions

    return ScanOptions(
        forbid_source_retrieval=True,
        forbid_source_acceptance=True,
        forbid_connector_binding=True,
        forbid_private_state_fetch=True,
        forbid_order_execution=True,
        forbid_neural_training=True,
        forbid_neural_inference=True,
        forbid_external_repo_clone=True,
        forbid_package_install_scripts=True,
    )


def _runtime_scan_cache_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    (repo_root / "src").mkdir(parents=True)
    (repo_root / "src" / "ok.py").write_text("# ok\n", encoding="utf-8")
    return repo_root


def test_runner_no_runtime_scan_cache_reuses_matching_result(tmp_path, monkeypatch):
    from tools import validate_no_runtime_artifacts as scanner

    repo_root = _runtime_scan_cache_repo(tmp_path)
    monkeypatch.setenv(
        runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV,
        str(repo_root / ".tmp" / "no_runtime_scan_cache.json"),
    )
    calls = 0

    def fake_scan(root: Path, options) -> list[str]:
        nonlocal calls
        calls += 1
        assert root == repo_root.resolve()
        return ["synthetic violation"]

    monkeypatch.setattr(scanner, "scan_repository", fake_scan)

    assert runner.scan_no_runtime_artifacts_with_run_cache(
        repo_root,
        _no_runtime_strict_options(),
    ) == ["synthetic violation"]
    assert runner.scan_no_runtime_artifacts_with_run_cache(
        repo_root,
        _no_runtime_strict_options(),
    ) == ["synthetic violation"]
    assert calls == 1


def test_runner_no_runtime_scan_cache_reruns_when_stale(tmp_path, monkeypatch):
    from tools import validate_no_runtime_artifacts as scanner

    repo_root = _runtime_scan_cache_repo(tmp_path)
    monkeypatch.setenv(
        runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV,
        str(repo_root / ".tmp" / "no_runtime_scan_cache.json"),
    )
    calls: list[str] = []

    def fake_scan(root: Path, options) -> list[str]:
        calls.append("scan")
        return []

    monkeypatch.setattr(scanner, "scan_repository", fake_scan)

    assert runner.scan_no_runtime_artifacts_with_run_cache(
        repo_root,
        _no_runtime_strict_options(),
    ) == []
    (repo_root / "src" / "new.py").write_text("# new\n", encoding="utf-8")
    assert runner.scan_no_runtime_artifacts_with_run_cache(
        repo_root,
        _no_runtime_strict_options(),
    ) == []
    assert calls == ["scan", "scan"]


def test_runner_no_runtime_scan_cache_reruns_when_corrupt(tmp_path, monkeypatch):
    from tools import validate_no_runtime_artifacts as scanner

    repo_root = _runtime_scan_cache_repo(tmp_path)
    cache_path = repo_root / ".tmp" / "no_runtime_scan_cache.json"
    cache_path.parent.mkdir()
    cache_path.write_text("{not-json", encoding="utf-8")
    monkeypatch.setenv(runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV, str(cache_path))

    calls = 0

    def fake_scan(root: Path, options) -> list[str]:
        nonlocal calls
        calls += 1
        return []

    monkeypatch.setattr(scanner, "scan_repository", fake_scan)

    assert runner.scan_no_runtime_artifacts_with_run_cache(
        repo_root,
        _no_runtime_strict_options(),
    ) == []
    assert calls == 1


def test_runner_no_runtime_scan_cache_rejects_scanned_tree_path(
    tmp_path,
    monkeypatch,
):
    repo_root = _runtime_scan_cache_repo(tmp_path)
    monkeypatch.setenv(
        runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV,
        str(repo_root / "no_runtime_scan_cache.json"),
    )

    with pytest.raises(RuntimeError, match="must point outside the scanned tree"):
        runner.scan_no_runtime_artifacts_with_run_cache(
            repo_root,
            _no_runtime_strict_options(),
        )


def test_runner_records_successful_no_runtime_command_cache(
    tmp_path,
    monkeypatch,
):
    from tools import validate_no_runtime_artifacts as scanner

    repo_root = _runtime_scan_cache_repo(tmp_path)
    cache_path = repo_root / ".tmp" / "no_runtime_scan_cache.json"
    monkeypatch.setenv(runner.NO_RUNTIME_ARTIFACT_SCAN_CACHE_ENV, str(cache_path))

    class Completed:
        returncode = 0

    monkeypatch.setattr(runner.subprocess, "run", lambda command: Completed())

    command = [
        sys.executable,
        str(Path("tools") / "validate_no_runtime_artifacts.py"),
        "--repo-root",
        str(repo_root),
        "--forbid-source-retrieval",
        "--forbid-source-acceptance",
        "--forbid-connector-binding",
        "--forbid-private-state-fetch",
        "--forbid-order-execution",
        "--forbid-neural-training",
        "--forbid-neural-inference",
        "--forbid-external-repo-clone",
        "--forbid-package-install-scripts",
    ]

    assert runner.run_commands([command]) == 0
    assert cache_path.is_file()

    def fail_if_uncached(root: Path, options) -> list[str]:
        raise AssertionError("successful scanner command should seed the cache")

    monkeypatch.setattr(scanner, "scan_repository", fail_if_uncached)
    assert runner.scan_no_runtime_artifacts_with_run_cache(
        repo_root,
        _no_runtime_strict_options(),
    ) == []


def test_runner_pr152_build_report_cache_reuses_matching_result(
    tmp_path,
    monkeypatch,
):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setenv(
        runner.PR152_BUILD_REPORT_CACHE_ENV,
        str(repo_root / ".tmp" / "pr152_build_cache.json"),
    )
    monkeypatch.setattr(
        runner,
        "_pr152_build_report_fingerprint",
        lambda root: {"repo_root": str(root), "state": "stable"},
    )
    calls = 0

    def fake_builder(root: Path) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {"calls": calls, "root": str(root)}

    first = runner.build_pr152_report_with_run_cache(repo_root, fake_builder)
    first["calls"] = 99
    second = runner.build_pr152_report_with_run_cache(repo_root, fake_builder)

    assert second == {"calls": 1, "root": str(repo_root.resolve())}
    assert calls == 1


def test_runner_pr152_build_report_cache_reruns_when_stale(
    tmp_path,
    monkeypatch,
):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setenv(
        runner.PR152_BUILD_REPORT_CACHE_ENV,
        str(repo_root / ".tmp" / "pr152_build_cache.json"),
    )
    state = {"value": "initial"}
    monkeypatch.setattr(
        runner,
        "_pr152_build_report_fingerprint",
        lambda root: {"repo_root": str(root), "state": state["value"]},
    )
    calls: list[str] = []

    def fake_builder(root: Path) -> dict[str, object]:
        calls.append(state["value"])
        return {"state": state["value"]}

    assert runner.build_pr152_report_with_run_cache(repo_root, fake_builder) == {
        "state": "initial"
    }
    state["value"] = "changed"
    assert runner.build_pr152_report_with_run_cache(repo_root, fake_builder) == {
        "state": "changed"
    }
    assert calls == ["initial", "changed"]


def test_runner_pr152_build_report_cache_reruns_when_corrupt(
    tmp_path,
    monkeypatch,
):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    cache_path = repo_root / ".tmp" / "pr152_build_cache.json"
    cache_path.parent.mkdir()
    cache_path.write_text("{not-json", encoding="utf-8")
    monkeypatch.setenv(runner.PR152_BUILD_REPORT_CACHE_ENV, str(cache_path))
    monkeypatch.setattr(
        runner,
        "_pr152_build_report_fingerprint",
        lambda root: {"repo_root": str(root), "state": "stable"},
    )
    calls = 0

    def fake_builder(root: Path) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {"rebuilt": True}

    assert runner.build_pr152_report_with_run_cache(repo_root, fake_builder) == {
        "rebuilt": True
    }
    assert calls == 1


def test_runner_pr152_build_report_cache_rejects_repo_root_path(
    tmp_path,
    monkeypatch,
):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setenv(
        runner.PR152_BUILD_REPORT_CACHE_ENV,
        str(repo_root / "pr152_build_cache.json"),
    )

    with pytest.raises(RuntimeError, match="must point outside the repo"):
        runner.build_pr152_report_with_run_cache(repo_root, lambda root: {})


def test_runner_keeps_process_roots_external_to_repo(monkeypatch, capsys, tmp_path, _central_supervision_test_adapter):
    _assert_repository_local_layout_contract()
    _clear_branch_context_env(monkeypatch)

    class Completed:
        def __init__(self, stdout: str = "", stderr: str = "") -> None:
            self.returncode = 0
            self.stdout = stdout
            self.stderr = stderr

    repo_root = (tmp_path / "test_run_validation_gates_repo_root").resolve()
    shutil.rmtree(repo_root, ignore_errors=True)
    repo_root.mkdir(parents=True)
    tmp_parent = repo_root / ".tmp"
    seen: list[list[str]] = []

    def fake_run(command: list[str], **kwargs) -> Completed:
        assert not tmp_parent.exists()
        assert runner._RUN_COMMANDS_ACTIVE_PATHS.process_root.is_dir()
        if command[0] == "git":
            return Completed()
        seen.append(command)
        return Completed(stdout=_st12h_mock_terminal_output(command))

    monkeypatch.setattr(runner, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(
        runner,
        "_routed_generated_output_currentness_failures",
        lambda command, repo_root: [],
    )

    assert not tmp_parent.exists()

    try:
        exit_code = runner.main([], **_central_supervision_test_adapter())

        assert exit_code == 0
        assert seen
        pytest_basetemp = _pytest_basetemp_from_commands(seen)
        assert not tmp_parent.exists()
        assert not pytest_basetemp.is_relative_to(repo_root)
        assert pytest_basetemp.name == reliability.PYTEST_BASETEMP_DIR_NAME
        assert capsys.readouterr().out.splitlines()[-1] == runner.SUCCESS_MARKER
    finally:
        shutil.rmtree(repo_root, ignore_errors=True)


def test_runner_uses_unique_pytest_basetemp_for_each_main_run(monkeypatch, tmp_path, _central_supervision_test_adapter):
    _clear_branch_context_env(monkeypatch)

    repo_root = (tmp_path / "test_run_validation_gates_unique_repo_root").resolve()
    shutil.rmtree(repo_root, ignore_errors=True)
    repo_root.mkdir(parents=True)
    pytest_basetemps: list[Path] = []

    def fake_run_commands(
        commands: list[list[str]],
        repo_root: Path | None = None,
        **kwargs,
    ) -> int:
        pytest_basetemp = _pytest_basetemp_from_commands(commands)
        assert not pytest_basetemp.is_relative_to(repo_root)
        assert pytest_basetemp.name == reliability.PYTEST_BASETEMP_DIR_NAME
        assert pytest_basetemp.is_dir()
        pytest_basetemps.append(pytest_basetemp)
        return _PRODUCTION_RUN_COMMANDS(commands, repo_root=repo_root, **kwargs)

    monkeypatch.setattr(runner, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(runner, "run_commands", fake_run_commands)

    try:
        assert runner.main([], **_central_supervision_test_adapter(mock_commands=True)) == 0
        assert runner.main([], **_central_supervision_test_adapter(mock_commands=True)) == 0

        assert len(pytest_basetemps) == 2
        assert pytest_basetemps[0] != pytest_basetemps[1]
    finally:
        shutil.rmtree(repo_root, ignore_errors=True)


def test_runner_does_not_touch_stale_fixed_pytest_basetemp(monkeypatch, tmp_path, _central_supervision_test_adapter):
    _clear_branch_context_env(monkeypatch)

    repo_root = (tmp_path / "test_run_validation_gates_stale_repo_root").resolve()
    shutil.rmtree(repo_root, ignore_errors=True)
    tmp_parent = repo_root / ".tmp"
    stale_basetemp = tmp_parent / "run_validation_gates_pytest"
    sentinel = stale_basetemp / "sentinel.txt"
    stale_basetemp.mkdir(parents=True)
    sentinel.write_text("do-not-touch", encoding="utf-8")
    pytest_basetemps: list[Path] = []

    def fake_run_commands(
        commands: list[list[str]],
        repo_root: Path | None = None,
        **kwargs,
    ) -> int:
        pytest_basetemp = _pytest_basetemp_from_commands(commands)
        assert pytest_basetemp != stale_basetemp
        assert pytest_basetemp.name == reliability.PYTEST_BASETEMP_DIR_NAME
        assert stale_basetemp.is_dir()
        assert sentinel.read_text(encoding="utf-8") == "do-not-touch"
        pytest_basetemps.append(pytest_basetemp)
        return _PRODUCTION_RUN_COMMANDS(commands, repo_root=repo_root, **kwargs)

    original_cwd = Path.cwd()
    monkeypatch.chdir(repo_root)
    monkeypatch.setattr(runner, "_repo_root", lambda: repo_root)
    monkeypatch.setattr(runner, "run_commands", fake_run_commands)

    try:
        assert runner.main([], **_central_supervision_test_adapter(mock_commands=True)) == 0

        assert pytest_basetemps
        assert stale_basetemp.is_dir()
        assert sentinel.read_text(encoding="utf-8") == "do-not-touch"
    finally:
        monkeypatch.chdir(original_cwd)
        shutil.rmtree(repo_root, ignore_errors=True)


def _workflow_text() -> str:
    return (
        Path(__file__).resolve().parents[2]
        / ".github/workflows/qtt_validation.yml"
    ).read_text(encoding="utf-8")


def _workflow_job_block(workflow: str, job_id: str) -> str:
    marker = f"  {job_id}:\n"
    start = workflow.index(marker)
    next_job = workflow.find("\n  ", start + len(marker))
    while next_job != -1 and workflow[next_job + 3 : next_job + 5] == "  ":
        next_job = workflow.find("\n  ", next_job + 1)
    if next_job == -1:
        return workflow[start:]
    return workflow[start:next_job]


def test_github_workflow_preserves_required_validation_check_identity():
    workflow = _workflow_text()
    validation_block = _workflow_job_block(workflow, "validation")

    assert workflow.startswith("name: QTT Validation\n")
    assert "  validation:\n" in workflow
    assert "    name: Validation Gates\n" in validation_block


def test_github_workflow_splits_validation_into_parallel_phase_jobs():
    workflow = _workflow_text()
    shard_block = _workflow_job_block(workflow, "validation_shards")

    assert "    timeout-minutes: 90\n" in shard_block
    assert "    strategy:\n" in shard_block
    assert "      fail-fast: false\n" in shard_block
    assert "          python-version: '3.14.6'\n" in shard_block
    assert "      - name: Restore pip download cache\n" in shard_block
    assert "        uses: actions/cache@v4\n" in shard_block
    assert "cache-dependency-path" not in shard_block
    assert "          cache: pip\n" not in shard_block
    assert "        with: &pip_cache\n" in shard_block
    assert "          path: ~/.cache/pip\n" in shard_block
    assert (
        "          key: ${{ runner.os }}-python-3.14.6-pip-pytest-9.1.1-"
        "${{ hashFiles('.github/workflows/qtt_validation.yml') }}\n"
    ) in shard_block
    assert (
        "            ${{ runner.os }}-python-3.14.6-pip-pytest-9.1.1-\n"
        in shard_block
    )
    assert "        run: &install_pytest |\n" in shard_block
    expected_pins = ("pytest==9.1.1", "iniconfig==2.3.0", "packaging==26.0", "pluggy==1.6.0",
        "pygments==2.21.0", "websockets==17.0.1", "cryptography==50.0.1", "cffi==2.1.1", "pycparser==3.0",
        "jsonschema==4.26.0", "jsonschema-specifications==2025.9.1", "referencing==0.37.0", "rpds-py==2026.5.1", "attrs==26.1.0")
    install = shard_block.split("        run: &install_pytest |\n", 1)[1].split("          python -m pip check\n", 1)[0]
    import shlex
    assert tuple(shlex.split(install.replace("\\\n", " "))) == (
        "python", "-m", "pip", "install", "--only-binary=:all:", "--no-deps", "--index-url",
        "https://pypi.org/simple", *expected_pins)
    assert "          python -m pip check\n" in shard_block
    for phase in runner.ORDERED_PHASES:
        assert f"          - phase: {phase}\n" in shard_block
    assert "          - phase: deterministic-validators\n" not in shard_block
    assert "--phase ${{ matrix.phase }}" in shard_block
    assert "--timing-report .tmp/qtt-validation-timing/${{ matrix.phase }}.json" in shard_block
    assert "--router-report .tmp/qtt-validation-router/${{ matrix.phase }}.json" in shard_block
    assert "uses: actions/upload-artifact@v4" in shard_block
    assert "validation-timing-${{ matrix.phase }}" in shard_block
    assert "validation-router-${{ matrix.phase }}" in shard_block
    assert shard_block.count("if: ${{ always() }}") >= 2
    assert "Run canonical validation gates" not in workflow


def test_github_workflow_aggregate_depends_on_validation_shard_matrix():
    workflow = _workflow_text()
    validation_block = _workflow_job_block(workflow, "validation")

    assert "      - validation_shards\n" in validation_block
    assert "    if: ${{ always() }}\n" in validation_block
    assert "uses: actions/download-artifact@v4" in validation_block
    assert "pattern: validation-*" in validation_block
    assert "tools/validate_pr169_val1.py" in validation_block
    assert 'if result != "success":' in validation_block
    assert "raise SystemExit(1)" in validation_block


def test_github_workflow_matrix_contains_post_validation_phase():
    workflow = _workflow_text()
    shard_block = _workflow_job_block(workflow, "validation_shards")

    assert "          - phase: post-validation\n" in shard_block
    assert "            group: repo-wide-integrity\n" in shard_block


def test_nested_validator_contract_scan_blocks_hidden_full_rerun():
    from tools import validate_nested_validator_contracts as nested_contracts

    with tempfile.TemporaryDirectory(prefix="qtt_nested_contract_") as temp_dir:
        repo_root = Path(temp_dir)
        validator = repo_root / "tools" / "validate_pr200_downstream.py"
        validator.parent.mkdir(parents=True)
        validator.write_text(
            "import subprocess\n"
            "subprocess.run(['python', "
            "'tools/validate_pr159r_source_locator_value_capture.py'])\n",
            encoding="utf-8",
        )

        failures = nested_contracts.nested_validator_contract_failures_for_paths(
            repo_root,
            (validator,),
        )

    assert len(failures) == 1
    assert "nested full validator rerun forbidden" in failures[0]
    assert "validate_pr159r_source_locator_value_capture.py" in failures[0]

    import pytest
    from tools.validation_reliability import ValidationReliabilityError
    with tempfile.TemporaryDirectory(prefix="qtt_nested_required_") as temp_dir:
        with pytest.raises(ValidationReliabilityError):
            nested_contracts._candidate_files(Path(temp_dir))



def test_nested_validator_contract_scan_allows_recorded_receipt_contract_text():
    from tools import validate_nested_validator_contracts as nested_contracts

    with tempfile.TemporaryDirectory(prefix="qtt_nested_contract_") as temp_dir:
        repo_root = Path(temp_dir)
        validator = repo_root / "tools" / "validate_pr200_downstream.py"
        validator.parent.mkdir(parents=True)
        validator.write_text(
            "RECEIPT_CONTRACT = {\n"
            "    'validator_that_recorded_receipt': "
            "'tools/validate_pr159r_source_locator_value_capture.py',\n"
            "    'rerun_full_validator': False,\n"
            "}\n",
            encoding="utf-8",
        )

        assert (
            nested_contracts.nested_validator_contract_failures_for_paths(
                repo_root,
                (validator,),
            )
            == ()
        )
def test_st12f_focused_validators_remain_in_existing_validation_phase() -> None:
    commands = tuple(
        tuple(command)
        for phase in runner.build_phase_manifest(Path(".tmp/st12f-runner"), Path(".tmp/st12f-runner/pytest"))
        for command in phase["commands"]
    )
    joined = tuple(" ".join(command) for command in commands)
    for token in (
        "--domain llm",
        "--domain model_risk",
        "--domain quantum",
        "independent_validate_qku_computation_control_plane_llm.py",
        "independent_validate_qku_computation_control_plane_model_risk.py",
        "independent_validate_qku_computation_control_plane_quantum.py",
    ):
        assert any(token in command for command in joined)


def test_st12h_commands_use_only_existing_phases_and_one_existing_pytest_shard() -> None:
    manifest = runner.build_phase_manifest(
        Path(".tmp/st12h-runner-contract"),
        Path(".tmp/st12h-runner-contract-pytest"),
    )
    by_phase = {
        str(record["phase"]): tuple(record["commands"]) for record in manifest
    }
    frozen = tuple(
        runner._st12h_normalized_command(command)
        for command in runner.build_st12h_validation_commands(sys.executable)
    )
    deterministic_c = tuple(
        runner._st12h_normalized_command(command)
        for command in by_phase["deterministic-validators-c"]
    )
    indices = [deterministic_c.index(command) for command in frozen]

    assert len(runner.ORDERED_PHASES) == 13
    assert runner._st12h_runner_topology_failures() == ()
    assert indices == list(range(indices[0], indices[0] + 12))
    assert all(deterministic_c.count(command) == 1 for command in frozen)
    for phase, commands in by_phase.items():
        if phase != "deterministic-validators-c":
            assert not {
                runner._st12h_normalized_command(command) for command in commands
            }.intersection(frozen)
    direct_grouped_matrix_commands = [
        command
        for command in by_phase["pytest-shard-8"]
        if runner.ST12H_TEST_MODULE in runner._pytest_path_args(command)
    ]
    complete_qku_root_commands = [
        command
        for command in by_phase["pytest-shard-8"]
        if runner._pytest_path_args(command) == (runner.ST12A_TEST_ROOT,)
    ]
    assert direct_grouped_matrix_commands == []
    assert len(complete_qku_root_commands) == 1
    assert (
        runner.ST12H_TEST_MODULE
        in runner.pytest_shard_manifest(REPO_ROOT)["pytest-shard-8"]
    )
    workflow = _workflow_text()
    assert workflow.count("  validation_shards:\n") == 1
    assert workflow.count("  validation:\n") == 1


def _assert_path_projection_contract(monkeypatch, tmp_path: Path) -> None:
    commands = runner.build_phase_commands(
        runner.ALL_PHASE,
        Path(".tmp/st12h-timeout-contract"),
        Path(".tmp/st12h-timeout-contract-pytest"),
    )
    contracts = [
        runner._st12h_command_contract(command)
        for command in commands
        if runner._st12h_command_contract(command) is not None
    ]

    assert len(contracts) == 15
    assert sum(timeout == 1200 for timeout, _markers in contracts) == 14
    assert sum(timeout == 1800 for timeout, _markers in contracts) == 1
    assert runner.ST12H_MAX_CONCURRENT_VALIDATION_PROCESSES == 1
    assert runner.ST12H_AUTOMATIC_FULL_CAMPAIGN_RETRIES == 0
    assert runner.ST12H_MAX_FULL_LOCAL_CAMPAIGNS_PER_TRACKED_STATE == 1

    projected_paths = runner._projected_validation_relative_paths(runner.ALL_PHASE)
    inline_programs = {
        str(command[index + 1])
        for command in commands
        for index, argument in enumerate(command[:-1])
        if argument == "-c"
    }
    assert inline_programs
    assert inline_programs.isdisjoint(projected_paths)
    assert "command-9999.stdout.bin" in projected_paths
    assert any(path.startswith("validation-output/") for path in projected_paths)
    projected_run_root = tmp_path / "short-root" / "run_projection_matrix"
    test_component, fixture_suffixes = reliability._pytest_tmp_path_budget(
        REPO_ROOT,
        projected_paths,
    )
    deepest = reliability._deepest_projection(
        projected_run_root,
        projected_paths,
        repo_root=REPO_ROOT,
    )
    assert deepest.is_relative_to(projected_run_root)
    deepest_relative = deepest.relative_to(projected_run_root)
    assert deepest_relative.parts[0] == reliability.PYTEST_BASETEMP_DIR_NAME
    assert deepest_relative.parts[1] == test_component
    assert Path(*deepest_relative.parts[2:]) in {
        reliability._safe_relative_projection(path) for path in fixture_suffixes
    }
    assert len(test_component) <= reliability.PYTEST_TMP_PATH_NAME_LIMIT + 1
    assert max(map(len, fixture_suffixes)) >= 135

    _assert_exact_stat_command_boundary(monkeypatch, tmp_path)

    synthetic_repo = tmp_path / "class-projection-repo"
    synthetic_test = synthetic_repo / "tests" / "test_class_projection.py"
    synthetic_test.parent.mkdir(parents=True)
    synthetic_test.write_text(
        "class TestClassBasedProjection:\n"
        "    def test_deep_class_fixture(self, tmp_path):\n"
        "        target = (\n"
        "            tmp_path\n"
        "            / 'deep'\n"
        "            / 'class'\n"
        "            / 'fixture'\n"
        "            / 'very_long_current_fixture_name.json'\n"
        "        )\n",
        encoding="utf-8",
    )
    class_component, class_suffixes = reliability._pytest_tmp_path_budget(
        synthetic_repo,
        ("tests/test_class_projection.py",),
    )
    class_suffix = "deep/class/fixture/very_long_current_fixture_name.json"
    assert class_component == "test_deep_class_fixture0"
    assert class_suffix in class_suffixes
    class_process_root = tmp_path / "class-projection-root" / "r1"
    class_process_root.mkdir(parents=True)
    class_deepest = reliability._deepest_projection(
        class_process_root,
        ("tests/test_class_projection.py",),
        repo_root=synthetic_repo,
    )
    assert class_deepest == (
        class_process_root
        / reliability.PYTEST_BASETEMP_DIR_NAME
        / class_component
        / reliability._safe_relative_projection(class_suffix)
    )
    class_probe = reliability.probe_run_filesystem(
        class_process_root,
        deepest_projected_path=class_deepest,
    )
    assert class_probe.write_path == class_deepest
    assert class_probe.created_directory is True
    assert class_probe.written_bytes == len(reliability.FILESYSTEM_PROBE_BYTES)
    assert class_probe.readback_equal is True
    assert class_probe.rename_equal is True
    assert class_probe.unlink_success is True
    assert class_probe.directory_cleanup_success is True
    assert class_probe.failure_operation is None
    assert class_probe.native_error_class is None
    assert not any(class_process_root.iterdir())
    class_process_root.rmdir()

    selector_repo = tmp_path / "selector-repo"
    selector = "tests/test_selected_source_" + "x" * 60 + ".py"
    selected_source = selector_repo / selector
    selected_source.parent.mkdir(parents=True)
    source_text = (
        "def test_selected_source(tmp_path):\n"
        "    actual = tmp_path / 'actual-output.json'\n"
        "    fixture = tmp_path / 'tests' / 'fixtures' / 'retained.json'\n"
    )
    selected_source.write_text(source_text, encoding="utf-8")
    _, selected_suffixes = reliability._pytest_tmp_path_budget(
        selector_repo, (selector,)
    )
    assert selector not in selected_suffixes
    assert "actual-output.json" in selected_suffixes
    assert "tests/fixtures/retained.json" in selected_suffixes

    # A selected source may also be a real AST-derived temporary destination.
    selected_source.write_text(
        source_text + f"    same_spelling = tmp_path / {selector!r}\n",
        encoding="utf-8",
    )
    _, identical_suffixes = reliability._pytest_tmp_path_budget(
        selector_repo, (selector,)
    )
    assert set(selected_suffixes) <= set(identical_suffixes)
    assert selector in identical_suffixes

    fixture_input = "tests/fixtures/source_selector_metadata.json"
    fixture_file = selector_repo / fixture_input
    fixture_file.parent.mkdir(parents=True)
    fixture_file.write_text("{}\n", encoding="utf-8")
    unknown_paths = ("tests/test_unknown_destination.py", "unknown/retained.json")
    conservative_inputs = (selector, fixture_input, *unknown_paths)
    _, conservative_suffixes = reliability._pytest_tmp_path_budget(
        selector_repo, conservative_inputs
    )
    assert fixture_input in conservative_suffixes
    assert set(unknown_paths) <= set(conservative_suffixes)
    _, no_repository_suffixes = reliability._pytest_tmp_path_budget(
        None, conservative_inputs
    )
    assert set(conservative_inputs) <= set(no_repository_suffixes)

    # These are projection-only paths; their complete spelling must survive.
    long_output = "/".join(["explicit-output-component"] * 20) + "/retained.json"
    projection_root = Path("projection-only-root")
    for prefix, directory in (
        ("validation-output/", reliability.VALIDATION_OUTPUT_DIR_NAME),
        ("pytest-basetemp/", reliability.PYTEST_BASETEMP_DIR_NAME),
    ):
        explicit_output = prefix + long_output
        explicit_deepest = reliability._deepest_projection(
            projection_root, (selector, explicit_output), repo_root=selector_repo
        )
        assert explicit_deepest == projection_root / directory / long_output
        assert len(str(explicit_deepest)) == len(
            str(projection_root / directory / long_output)
        )

    malformed_selector = "tests/test_malformed_selected.py"
    (selector_repo / malformed_selector).write_text(
        "def test_malformed(\n", encoding="utf-8"
    )
    with pytest.raises(
        reliability.ValidationReliabilityError,
        match="ENGVR_LONGEST_PATH_PROBE_FAILED",
    ):
        reliability._pytest_tmp_path_budget(selector_repo, (malformed_selector,))

    from tools import independent_validate_qku_computation_control_plane as st12h

    declarations = tuple(
        f"validation-output/w \u00fc/{directory}/{member}"
        for directory in ("x \u00e9", "r \u00e9", "c \u00e9")
        for member in st12h._ST12H_PUBLICATION_MEMBERS
    ) + (
        "validation-output/w \u00fc/publication archive.zip",
        "validation-output/w \u00fc/stage journal.partial",
        "validation-output/w \u00fc/stage journal.json",
    )
    expected_destinations = tuple(
        projection_root / reliability.VALIDATION_OUTPUT_DIR_NAME / Path(*value.split("/")[1:])
        for value in declarations
    )
    assert len(declarations) == 9
    for declaration, expected_path in zip(declarations, expected_destinations, strict=True):
        assert reliability._safe_fixture_path_text(declaration) == declaration
        assert reliability._safe_fixture_path_text(declaration.replace("/", "\\")) == declaration
        materialized = reliability._safe_relative_projection(declaration.removeprefix("validation-output/"))
        assert materialized.parts == tuple(declaration.split("/")[1:])
        assert (projection_root / reliability.VALIDATION_OUTPUT_DIR_NAME / materialized).parts == expected_path.parts
    expected_deepest = max(
        expected_destinations,
        key=lambda path: (len(str(path).encode("utf-16-le")) // 2, len(str(path)), str(path)),
    )
    assert reliability._deepest_projection(projection_root, declarations).parts == expected_deepest.parts

    literal_paths = (
        "reports/two  internal spaces.txt", "reports/caf\u00e9.txt",
        "reports/cafe\u0301.txt", "\u6f22\u5b57/\u0434\u0430\u043d\u043d\u044b\u0435.json",
        "reports/\U0001f9ea \U00010400.json", ".hidden/MixedCase_.txt",
        "names/COM0.txt", "names/COM10.txt", "names/LPT0.txt",
    )
    materialized_spellings = []
    for value in literal_paths:
        assert reliability._safe_fixture_path_text(value) == value
        path = reliability._safe_relative_projection(value)
        assert path.parts == tuple(value.split("/"))
        assert path.as_posix() == value
        materialized_spellings.append(path.as_posix())
    assert len(set(materialized_spellings)) == len(literal_paths)
    assert materialized_spellings[1] != materialized_spellings[2]

    invalid_paths = (
        "", ".", "..", "../escape", "a/../escape", "/absolute", "C:/drive",
        "C:relative", "\\\\server\\share", "a//b", "a/./b", "a/", "-option",
        " leading/file", "a/ leading", "trailing /file", "a/trailing ",
        "trailing./file", "a/trailing.", "a:stream", "a/b:stream",
        "bad[0].json", "bad@name", "bad*name", "bad?name", "bad|name",
        'bad"name', "bad<name", "bad>name", "a/\x00file", "a/\x1ffile",
        "a/\x7ffile", "a/\tfile", "a/line\nfeed", "a/\u00a0file",
        "a/\u2003file", "a/\u200dfile", "a/\ud800file", "a/\udffffile",
    ) + tuple(
        f"directory/{name}{suffix}"
        for name in ("CON", "con", "PRN", "AUX", "NUL", "nul ", "COM1", "COM9", "LPT1", "LPT9", "COM\u00b9", "COM\u00b2", "LPT\u00b3")
        for suffix in ("", ".json")
    )
    for value in (*invalid_paths, None, 1, b"literal"):
        assert reliability._safe_fixture_path_text(value) is None
        with pytest.raises(reliability.ValidationReliabilityError, match="ENGVR_LONGEST_PATH_PROBE_FAILED"):
            reliability._safe_relative_projection(value)
    for namespace in ("validation-output", "pytest-basetemp"):
        bad_outputs = (namespace, namespace + "/") + tuple(
            namespace + "/" + value
            for value in ("../escape", "a/./b", "a//b", "/absolute", "C:/drive", "a:stream", "CON.json", "trailing.", " leading", "a/\ud800file", "a/\tfile")
        )
        for value in bad_outputs:
            for spelling in (value, value.replace("/", "\\")):
                with pytest.raises(reliability.ValidationReliabilityError, match="ENGVR_LONGEST_PATH_PROBE_FAILED") as rejected:
                    reliability._deepest_projection(projection_root, (spelling,))
                assert repr(spelling) in str(rejected.value)
    assert reliability._pytest_tmp_path_budget(None, ()) == ("test_validation_path_budget0", ("sentinel.bin",))
    assert reliability._deepest_projection(projection_root, ("unknown:heuristic",)) == reliability._deepest_projection(projection_root, ())

    ascii_leaf = "a" * 80 + ".bin"
    supplementary_leaf = "\U0001f9ea" * 50 + ".bin"
    for namespace, directory in (("validation-output", reliability.VALIDATION_OUTPUT_DIR_NAME), ("pytest-basetemp", reliability.PYTEST_BASETEMP_DIR_NAME)):
        inputs = (f"{namespace}/utf16/{ascii_leaf}", f"{namespace}/utf16/{supplementary_leaf}")
        ascii_path = projection_root / directory / "utf16" / ascii_leaf
        supplementary_path = projection_root / directory / "utf16" / supplementary_leaf
        assert len(str(supplementary_path)) < len(str(ascii_path))
        assert len(str(supplementary_path).encode("utf-16-le")) > len(str(ascii_path).encode("utf-16-le"))
        assert reliability._deepest_projection(projection_root, inputs).parts == supplementary_path.parts

    unicode_selector = "tests/test_\u00e9_\u6f22.py"
    unicode_source = selector_repo / unicode_selector
    ascii_test_name = "test_" + "a" * 24
    unicode_test_name = "test_" + "\U00010400" * 16
    unicode_source_text = (
        f"def {ascii_test_name}(tmp_path):\n"
        "    actual = tmp_path / 'actual caf\\u00e9.json'\n"
        f"def {unicode_test_name}(tmp_path):\n"
        "    fixture = tmp_path / 'tests/fixtures/\\u65e5\\u672c.json'\n"
    )
    unicode_source.write_text(unicode_source_text, encoding="utf-8")
    unicode_component, unicode_suffixes = reliability._pytest_tmp_path_budget(selector_repo, (unicode_selector,))
    assert len(unicode_test_name + "0") < len(ascii_test_name + "0")
    assert len((unicode_test_name + "0").encode("utf-16-le")) > len((ascii_test_name + "0").encode("utf-16-le"))
    assert unicode_component == unicode_test_name + "0"
    assert unicode_selector not in unicode_suffixes
    assert {"actual caf\u00e9.json", "tests/fixtures/\u65e5\u672c.json"} <= set(unicode_suffixes)
    unicode_source.write_text(unicode_source_text + f"    same_spelling = tmp_path / {unicode_selector!r}\n", encoding="utf-8")
    _, same_spelling_suffixes = reliability._pytest_tmp_path_budget(selector_repo, (unicode_selector,))
    assert set(unicode_suffixes) <= set(same_spelling_suffixes)
    assert unicode_selector in same_spelling_suffixes

    real_admission = reliability._safe_fixture_path_text
    real_materialization = reliability._safe_relative_projection
    def old_ascii_admission(value):
        if any(character.isspace() or ord(character) >= 128 for character in value):
            return None
        return real_admission(value)
    def old_underscore_materialization(value):
        return Path(*(re.sub(r"[^A-Za-z0-9._-]", "_", part) for part in value.split("/")))
    with monkeypatch.context() as half_fix:
        half_fix.setattr(reliability, "_safe_fixture_path_text", old_ascii_admission)
        with pytest.raises(reliability.ValidationReliabilityError, match="ENGVR_LONGEST_PATH_PROBE_FAILED"):
            reliability._deepest_projection(projection_root, declarations)
    with monkeypatch.context() as half_fix:
        half_fix.setattr(reliability, "_safe_relative_projection", old_underscore_materialization)
        with pytest.raises(AssertionError):
            assert reliability._deepest_projection(projection_root, declarations).parts == expected_deepest.parts
    assert reliability._safe_fixture_path_text is real_admission
    assert reliability._safe_relative_projection is real_materialization


def _assert_process_supervision_contract(monkeypatch, tmp_path: Path) -> None:
    class WindowsStartupInfo:
        def __init__(self):
            self.dwFlags = 0
            self.wShowWindow = 0

    with monkeypatch.context() as windows_patch:
        windows_patch.setattr(reliability.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)
        windows_patch.setattr(reliability.subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200, raising=False)
        windows_patch.setattr(reliability.subprocess, "STARTF_USESHOWWINDOW", 0x00000001, raising=False)
        windows_patch.setattr(reliability.subprocess, "SW_HIDE", 0, raising=False)
        windows_patch.setattr(reliability.subprocess, "STARTUPINFO", WindowsStartupInfo, raising=False)
        windows_kwargs = reliability.hidden_subprocess_kwargs(platform_name="nt")
    assert windows_kwargs["creationflags"] & 0x08000000
    assert windows_kwargs["creationflags"] & 0x00000200
    assert windows_kwargs["startupinfo"].dwFlags & 0x00000001
    assert windows_kwargs["startupinfo"].wShowWindow == 0
    posix_kwargs = reliability.hidden_subprocess_kwargs(platform_name="posix")
    assert posix_kwargs == {"start_new_session": True}

    evidence = tmp_path / "supervised-evidence"
    pass_receipt = reliability.supervise_command(
        (
            sys.executable,
            "-c",
            "import sys;"
            "sys.stdout.buffer.write(b'O'*200000+b'\\nREQUIRED_OK\\n');"
            "sys.stderr.buffer.write(b'warning-only\\n'+b'E'*200000)",
        ),
        cwd=REPO_ROOT,
        run_id="run_supervision_matrix",
        phase="unit-supervision",
        command_index=1,
        evidence_root=evidence,
        required_markers=("REQUIRED_OK",),
        timeout_seconds=30,
        mirror_stdout=False,
        mirror_stderr=False,
    )
    assert isinstance(pass_receipt.pid, int) and pass_receipt.pid > 0
    assert pass_receipt.native_exit_code == 0
    assert pass_receipt.failure_class is None
    assert pass_receipt.stderr_was_nonempty is True
    assert pass_receipt.stdout_marker_state == "PASS"
    assert pass_receipt.stdout_byte_count > 200_000
    assert pass_receipt.stderr_byte_count > 200_000
    assert Path(pass_receipt.stdout_path).read_bytes().endswith(b"REQUIRED_OK\n")

    nonzero_receipt = reliability.supervise_command(
        (sys.executable, "-c", "raise SystemExit(7)"),
        cwd=REPO_ROOT,
        run_id="run_supervision_matrix",
        phase="unit-supervision",
        command_index=2,
        evidence_root=evidence,
        mirror_stdout=False,
        mirror_stderr=False,
    )
    assert nonzero_receipt.native_exit_code == 7
    assert nonzero_receipt.failure_class == "ENGVR_NATIVE_EXIT_NONZERO"

    marker_receipt = reliability.supervise_command(
        (sys.executable, "-c", "print('ordinary output')"),
        cwd=REPO_ROOT,
        run_id="run_supervision_matrix",
        phase="unit-supervision",
        command_index=3,
        evidence_root=evidence,
        required_markers=("MISSING_REQUIRED",),
        mirror_stdout=False,
        mirror_stderr=False,
    )
    assert marker_receipt.native_exit_code == 0
    assert marker_receipt.failure_class == "ENGVR_REQUIRED_MARKER_MISSING"

    stderr_marker_receipt = reliability.supervise_command(
        (sys.executable, "-c", "import sys;print('STDOUT_ONLY_OK', file=sys.stderr)"),
        cwd=REPO_ROOT,
        run_id="run_supervision_matrix",
        phase="unit-supervision",
        command_index=6,
        evidence_root=evidence,
        required_markers=("STDOUT_ONLY_OK",),
        mirror_stdout=False,
        mirror_stderr=False,
    )
    embedded_marker_receipt = reliability.supervise_command(
        (sys.executable, "-c", "print('prefix EMBEDDED_MARKER suffix')"),
        cwd=REPO_ROOT,
        run_id="run_supervision_matrix",
        phase="unit-supervision",
        command_index=7,
        evidence_root=evidence,
        required_markers=("EMBEDDED_MARKER",),
        mirror_stdout=False,
        mirror_stderr=False,
    )
    assert stderr_marker_receipt.failure_class == "ENGVR_REQUIRED_MARKER_MISSING"
    assert embedded_marker_receipt.failure_class == "ENGVR_REQUIRED_MARKER_MISSING"

    start_receipt = reliability.supervise_command(
        (str(tmp_path / "definitely-missing-command.exe"),),
        cwd=REPO_ROOT,
        run_id="run_supervision_matrix",
        phase="unit-supervision",
        command_index=4,
        evidence_root=evidence,
        mirror_stdout=False,
        mirror_stderr=False,
    )
    assert start_receipt.pid is None
    assert start_receipt.native_exit_code is None
    assert start_receipt.start_failure_class
    assert start_receipt.failure_class == "ENGVR_PROCESS_START_FAILED"

    escalation_calls = []

    class EscalationProcess:
        pid = 24680
        returncode = 1
        waits = 0

        def wait(self, timeout=None):
            self.waits += 1
            if self.waits == 1:
                raise subprocess.TimeoutExpired("owned", timeout)
            return self.returncode

    with monkeypatch.context() as escalation_patch:
        escalation_patch.setattr(
            reliability,
            "_hidden_taskkill",
            lambda argv: escalation_calls.append(tuple(argv)) or 0,
        )
        termination_state, terminal = reliability._terminate_owned_process_tree(
            EscalationProcess(),
            platform_name="nt",
            grace_seconds=0.01,
        )
    assert terminal is True
    assert termination_state.endswith("TERMINAL:PROVEN")
    assert escalation_calls == [
        ("taskkill.exe", "/PID", "24680", "/T"),
        ("taskkill.exe", "/PID", "24680", "/T", "/F"),
    ]

    pid_file = tmp_path / "owned-tree-pids.txt"
    tree_script = (
        "import os,pathlib,subprocess,sys,time;"
        "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);"
        f"pathlib.Path({str(pid_file)!r}).write_text(str(os.getpid())+','+str(child.pid));"
        "time.sleep(60)"
    )
    sibling = subprocess.Popen(
        (sys.executable, "-c", "import time;time.sleep(60)"),
        shell=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        **reliability.hidden_subprocess_kwargs(platform_name=os.name),
    )
    try:
        timeout_receipt = reliability.supervise_command(
            (sys.executable, "-c", tree_script),
            cwd=REPO_ROOT,
            run_id="run_supervision_matrix",
            phase="unit-supervision",
            command_index=5,
            evidence_root=evidence,
            timeout_seconds=1,
            termination_grace_seconds=2,
            mirror_stdout=False,
            mirror_stderr=False,
        )
        assert timeout_receipt.failure_class == "ENGVR_PROCESS_TIMEOUT"
        assert timeout_receipt.timeout_state == "TRIGGERED"
        assert "TERMINAL:PROVEN" in timeout_receipt.termination_state
        assert sibling.poll() is None
        root_pid, descendant_pid = (
            int(value) for value in pid_file.read_text(encoding="utf-8").split(",")
        )
        for owned_pid in (root_pid, descendant_pid):
            terminal = False
            for _attempt in range(100):
                if os.name == "nt":
                    tasklist = subprocess.run(
                        ("tasklist.exe", "/FI", f"PID eq {owned_pid}", "/FO", "CSV", "/NH"),
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    terminal = f'"{owned_pid}"' not in tasklist.stdout
                else:
                    proc_stat = Path(f"/proc/{owned_pid}/stat")
                    if not proc_stat.exists():
                        terminal = True
                    else:
                        fields = proc_stat.read_text(encoding="utf-8").split()
                        terminal = len(fields) > 2 and fields[2] == "Z"
                if terminal:
                    break
                time.sleep(0.05)
            assert terminal
    finally:
        if sibling.poll() is None:
            sibling.terminate()
        sibling.wait(timeout=10)

    # The receipt veto adds no process discovery. These are finite data copies;
    # the original actual-child cases above and their assertions remain intact.
    from copy import copy
    for terminal_receipt in (pass_receipt, nonzero_receipt, marker_receipt,
                             start_receipt, timeout_receipt):
        assert reliability._command_requires_process_retention_v1(terminal_receipt) is False
    for malformed in (None, {}, SimpleNamespace(pid=123, native_exit_code=0),
                      object.__new__(reliability.CommandExecutionReceiptV1)):
        assert reliability._command_requires_process_retention_v1(malformed) is True
    for field, value in (
        ("pid", True), ("pid", 0), ("pid", "123"), ("native_exit_code", False),
        ("native_exit_code", None), ("native_exit_code", "0"),
        ("failure_class", "ENGVR_PROCESS_TERMINATION_FAILED"),
        ("start_failure_class", "OSError"), ("failure_class", "ENGVR_PROCESS_START_FAILED"),
        ("failure_class", False), ("timeout_state", None), ("timeout_state", "UNKNOWN"),
        ("timeout_seconds_or_null", True), ("termination_state", None),
        ("termination_state", "TERMINAL:PROVEN"), ("termination_state", "UNKNOWN:0;TERMINAL:PROVEN"),
        ("termination_state", "TASKKILL_T:0;TERMINAL:UNPROVEN;TERMINAL:PROVEN"),
        ("termination_state", "TASKKILL_T:0;TERMINAL:PROVEN;NATIVE_TREE_UNPROVEN_OUTPUT_PIPE_OPEN"),
        ("stdout_byte_count", True), ("command_index", True), ("schema_version", True),
        ("argv", list(pass_receipt.argv)), ("elapsed_monotonic_seconds", float("nan")),
    ):
        malformed = copy(pass_receipt)
        object.__setattr__(malformed, field, value)
        assert reliability._command_requires_process_retention_v1(malformed) is True
    for state in ("TASKKILL_T:0;TERMINAL:PROVEN",
                  "TASKKILL_T:128;TASKKILL_T_F:0;TERMINAL:PROVEN"):
        proven = replace(pass_receipt, platform="nt", native_exit_code=1,
                         timeout_state="TRIGGERED", failure_class="ENGVR_PROCESS_TIMEOUT",
                         termination_state=state)
        assert reliability._command_requires_process_retention_v1(proven) is False
        for invalid_state in ("NOT_REQUIRED", "TASKKILL_T:128;TERMINAL:PROVEN",
                              state + ";", "TASKKILL_T_F:0;TERMINAL:PROVEN",
                              "TASKKILL_T:00;TERMINAL:PROVEN"):
            assert reliability._command_requires_process_retention_v1(
                replace(proven, termination_state=invalid_state)) is True
    for field, value in (("start_failure_class", None), ("start_failure_class", ""),
                         ("native_exit_code", 0), ("timeout_state", "TRIGGERED"),
                         ("failure_class", "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED")):
        malformed = copy(start_receipt)
        object.__setattr__(malformed, field, value)
        assert reliability._command_requires_process_retention_v1(malformed) is True

def _assert_mirror_isolation_contract(monkeypatch, tmp_path: Path) -> None:
    marker = "MIRROR_OK"
    intended_bytes = 300_000 + 1 + len(marker.encode("utf-8")) + 1
    mirror_calls = []

    def broken_mirror(_data, _target):
        mirror_calls.append("write")
        raise BrokenPipeError("synthetic broken console mirror")

    mirror_evidence = tmp_path / "mirror-isolation-evidence"
    with monkeypatch.context() as mirror_patch:
        mirror_patch.setattr(reliability, "_mirror_bytes", broken_mirror)
        receipt = reliability.supervise_command(
            (
                sys.executable,
                "-c",
                "import sys;"
                "sys.stdout.buffer.write(b'M'*300000+b'\\nMIRROR_OK\\n');"
                "sys.stdout.buffer.flush()",
            ),
            cwd=REPO_ROOT,
            run_id="run_mirror_isolation",
            phase="unit-supervision",
            command_index=1,
            evidence_root=mirror_evidence,
            required_markers=(marker,),
            timeout_seconds=30,
            mirror_stdout=True,
            mirror_stderr=False,
        )
    assert mirror_calls == ["write"]
    assert receipt.native_exit_code == 0
    assert receipt.stdout_byte_count == intended_bytes
    assert Path(receipt.stdout_path).stat().st_size == intended_bytes
    assert receipt.stdout_marker_state == "PASS"
    assert receipt.failure_class is None


def _assert_descriptor_ownership_and_drain_contract(monkeypatch, tmp_path: Path) -> None:
    evidence_root = tmp_path / "descriptor-ownership-evidence"
    writer_entered = reliability.threading.Event()
    writer_release = reliability.threading.Event()
    result: dict[str, object] = {}
    real_write_chunk = reliability._write_evidence_chunk

    def blocked_writer(stream, data):
        if (
            Path(stream.name).name == "command-1.stdout.bin"
            and not writer_entered.is_set()
        ):
            writer_entered.set()
            assert writer_release.wait(timeout=30)
        return real_write_chunk(stream, data)

    def run_supervisor():
        result["receipt"] = reliability.supervise_command(
            (
                sys.executable,
                "-c",
                "import sys;"
                "sys.stdout.buffer.write(b'D'*50000);"
                "sys.stdout.buffer.flush()",
            ),
            cwd=REPO_ROOT,
            run_id="run_descriptor_ownership",
            phase="unit-supervision",
            command_index=1,
            evidence_root=evidence_root,
            timeout_seconds=30,
            mirror_stdout=False,
            mirror_stderr=False,
        )

    with monkeypatch.context() as descriptor_patch:
        descriptor_patch.setattr(
            reliability,
            "_write_evidence_chunk",
            blocked_writer,
        )
        supervisor = reliability.threading.Thread(
            target=run_supervisor,
            name="engvr-descriptor-ownership-supervisor",
        )
        supervisor.start()
        assert writer_entered.wait(timeout=10)
        assert not (evidence_root / "command-1.json").exists()
        sentinel_paths = tuple(
            tmp_path / f"descriptor-sentinel-{index}.bin" for index in range(3)
        )
        sentinel_descriptors = tuple(
            os.open(
                path,
                os.O_RDWR | os.O_CREAT | os.O_EXCL | int(getattr(os, "O_BINARY", 0)),
            )
            for path in sentinel_paths
        )
        for descriptor in sentinel_descriptors:
            os.write(descriptor, b"before-release\n")
        time.sleep(reliability.OUTPUT_DRAIN_INITIAL_WAIT_SECONDS + 0.2)
        assert supervisor.is_alive()
        assert not (evidence_root / "command-1.json").exists()
        writer_release.set()
        supervisor.join(timeout=30)
        assert not supervisor.is_alive()
    for descriptor in sentinel_descriptors:
        os.write(descriptor, b"after-release\n")
        os.fsync(descriptor)
        os.close(descriptor)
    for path in sentinel_paths:
        assert path.read_bytes() == b"before-release\nafter-release\n"
    descriptor_receipt = result["receipt"]
    assert isinstance(descriptor_receipt, reliability.CommandExecutionReceiptV1)
    assert descriptor_receipt.native_exit_code == 0
    assert descriptor_receipt.failure_class is None
    assert descriptor_receipt.stdout_byte_count == 50_000
    assert not any(
        worker.is_alive()
        and worker.name.startswith(
            ("qtt-validation-stdout-", "qtt-validation-stderr-")
        )
        for worker in reliability.threading.enumerate()
    )
    reliability_source = Path(reliability.__file__).read_text(encoding="utf-8")
    assert "_close_owned_pipe_read_handle" not in reliability_source
    assert "os.close(pipe.fileno())" not in reliability_source


def _assert_output_drain_terminality_contract(monkeypatch, tmp_path: Path) -> None:
    def matching_drain_workers(pid: int):
        names = {
            f"qtt-validation-stdout-{pid}",
            f"qtt-validation-stderr-{pid}",
        }
        return tuple(
            worker
            for worker in reliability.threading.enumerate()
            if worker.is_alive() and worker.name in names
        )

    slow_evidence = tmp_path / "slow-output-drain"
    slow_intended_bytes = 50_000
    real_write_chunk = reliability._write_evidence_chunk
    delayed_writes = []

    def delayed_stdout_write(stream, data):
        if (
            Path(stream.name).name == "command-1.stdout.bin"
            and not delayed_writes
        ):
            delayed_writes.append(len(data))
            time.sleep(2.0)
        return real_write_chunk(stream, data)

    assert reliability.OUTPUT_DRAIN_INITIAL_WAIT_SECONDS < 2.0
    started = time.monotonic()
    with monkeypatch.context() as slow_patch:
        slow_patch.setattr(
            reliability,
            "_write_evidence_chunk",
            delayed_stdout_write,
        )
        slow_receipt = reliability.supervise_command(
            (
                sys.executable,
                "-c",
                "import sys;"
                "sys.stdout.buffer.write(b'S'*50000);"
                "sys.stdout.buffer.flush()",
            ),
            cwd=REPO_ROOT,
            run_id="run_slow_output_drain",
            phase="unit-supervision",
            command_index=1,
            evidence_root=slow_evidence,
            timeout_seconds=30,
            mirror_stdout=False,
            mirror_stderr=False,
        )
    slow_elapsed = time.monotonic() - started
    slow_stdout_path = Path(slow_receipt.stdout_path)
    slow_stderr_path = Path(slow_receipt.stderr_path)
    slow_command_path = slow_evidence / "command-1.json"
    slow_stable_bytes = {
        path: path.read_bytes()
        for path in (slow_stdout_path, slow_stderr_path, slow_command_path)
    }
    assert delayed_writes
    assert slow_elapsed >= 1.8
    assert slow_receipt.pid is not None
    assert slow_receipt.native_exit_code == 0
    assert slow_receipt.failure_class is None
    assert "OUTPUT_DRAIN" not in slow_receipt.termination_state
    assert slow_receipt.stdout_byte_count == slow_intended_bytes
    assert slow_stdout_path.stat().st_size == slow_intended_bytes
    assert matching_drain_workers(slow_receipt.pid) == ()
    time.sleep(0.2)
    assert {
        path: path.read_bytes()
        for path in (slow_stdout_path, slow_stderr_path, slow_command_path)
    } == slow_stable_bytes
    assert matching_drain_workers(slow_receipt.pid) == ()

    raw_failure_evidence = tmp_path / "raw-evidence-failure"
    raw_marker = "RAW_EVIDENCE_OK"
    raw_intended_bytes = 350_000 + 1 + len(raw_marker.encode("utf-8")) + 1
    failed_writes = []

    def fail_stdout_evidence(stream, data):
        if Path(stream.name).name == "command-1.stdout.bin":
            failed_writes.append(len(data))
            raise OSError("synthetic raw evidence write failure")
        return real_write_chunk(stream, data)

    original_terminate = reliability._terminate_owned_process_tree
    termination_observations = []

    def observe_original_termination(original_process, *, platform_name, grace_seconds):
        observed = {
            "process": original_process,
            "pid": original_process.pid,
            "platform_name": platform_name,
            "grace_seconds": grace_seconds,
        }
        termination_observations.append(observed)
        try:
            returned = original_terminate(
                original_process, platform_name=platform_name,
                grace_seconds=grace_seconds,
            )
            observed["returned"] = returned
            observed["post_poll"] = original_process.poll()
            observed["post_returncode"] = original_process.returncode
        except BaseException as exc:
            observed["exception"] = exc
            raise
        return returned

    with monkeypatch.context() as evidence_patch:
        evidence_patch.setattr(
            reliability,
            "_terminate_owned_process_tree",
            observe_original_termination,
        )
        evidence_patch.setattr(
            reliability,
            "_write_evidence_chunk",
            fail_stdout_evidence,
        )
        raw_failure_receipt = reliability.supervise_command(
            (
                sys.executable,
                "-c",
                "import sys;"
                "sys.stdout.buffer.write(b'R'*350000+b'\\nRAW_EVIDENCE_OK\\n');"
                "sys.stdout.buffer.flush()",
            ),
            cwd=REPO_ROOT,
            run_id="run_raw_evidence_failure",
            phase="unit-supervision",
            command_index=1,
            evidence_root=raw_failure_evidence,
            required_markers=(raw_marker,),
            timeout_seconds=30,
            mirror_stdout=False,
            mirror_stderr=False,
        )
    assert failed_writes
    assert raw_intended_bytes > 64 * 1024
    assert raw_failure_receipt.pid is not None
    assert len(termination_observations) == 1
    observed_termination = termination_observations[0]
    assert "exception" not in observed_termination
    original_process = observed_termination["process"]
    assert observed_termination["pid"] == original_process.pid == raw_failure_receipt.pid
    assert observed_termination["platform_name"] == os.name
    assert observed_termination["grace_seconds"] == reliability.TERMINATION_GRACE_SECONDS
    termination_result = observed_termination["returned"]
    assert type(termination_result) is tuple and len(termination_result) == 2
    termination_state, proven = termination_result
    assert type(proven) is bool and proven is True
    assert type(termination_state) is str and termination_state.endswith(";TERMINAL:PROVEN")
    assert "UNPROVEN" not in termination_state
    assert raw_failure_receipt.termination_state == termination_state
    terminal_exit = original_process.returncode
    assert type(terminal_exit) is int
    assert type(observed_termination["post_poll"]) is int
    assert type(observed_termination["post_returncode"]) is int
    assert type(raw_failure_receipt.native_exit_code) is int
    assert raw_failure_receipt.native_exit_code == observed_termination["post_poll"] == (
        observed_termination["post_returncode"]
    ) == terminal_exit
    assert raw_failure_receipt.timeout_state == "NOT_TRIGGERED"
    raw_stdout_path = Path(raw_failure_receipt.stdout_path)
    raw_stderr_path = Path(raw_failure_receipt.stderr_path)
    raw_command_path = raw_failure_evidence / "command-1.json"
    assert raw_failure_receipt.stdout_byte_count == raw_stdout_path.stat().st_size
    assert raw_failure_receipt.failure_class == "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED"
    assert raw_failure_receipt.failure_class != "ENGVR_PROCESS_TERMINATION_FAILED"
    assert raw_failure_receipt.stdout_marker_state == "EVIDENCE_UNAVAILABLE"
    assert raw_failure_receipt.stdout_marker_state != "PASS"
    assert matching_drain_workers(raw_failure_receipt.pid) == ()
    raw_stable_bytes = {
        path: path.read_bytes()
        for path in (raw_stdout_path, raw_stderr_path, raw_command_path)
    }
    assert raw_failure_receipt.stderr_byte_count == raw_stderr_path.stat().st_size
    assert {path.name for path in raw_failure_evidence.glob("command-*.json")} == {"command-1.json"}
    raw_command_record = json.loads(raw_stable_bytes[raw_command_path])
    observed_metadata = {key: observed_termination[key] for key in (
        "pid", "returned", "post_poll", "post_returncode",
    )}
    retained_lengths = (len(raw_stable_bytes[raw_stdout_path]), len(raw_stable_bytes[raw_stderr_path]))

    def assert_failed_retention_record(record, observed, *, expected_pid, expected_exit):
        assert type(expected_pid) is int and expected_pid > 0
        assert type(expected_exit) is int
        assert type(observed["pid"]) is int and observed["pid"] == expected_pid
        assert type(record["pid"]) is int and record["pid"] == expected_pid
        result = observed["returned"]
        assert type(result) is tuple and len(result) == 2
        state, terminal_proven = result
        assert type(state) is str and state.endswith(";TERMINAL:PROVEN")
        assert "UNPROVEN" not in state
        assert type(terminal_proven) is bool and terminal_proven is True
        assert record["termination_state"] == state == termination_state
        for value in (observed["post_poll"], observed["post_returncode"], record["native_exit_code"]):
            assert type(value) is int and value == expected_exit
        assert record["timeout_state"] == "NOT_TRIGGERED"
        assert record["failure_class"] == "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED"
        assert record["failure_class"] != "ENGVR_PROCESS_TERMINATION_FAILED"
        assert record["stdout_marker_state"] == "EVIDENCE_UNAVAILABLE"
        assert record["stdout_marker_state"] != "PASS"
        for key, length in zip(("stdout_byte_count", "stderr_byte_count"), retained_lengths, strict=True):
            assert type(record[key]) is int and record[key] == length

    assert_failed_retention_record(
        raw_command_record, observed_metadata,
        expected_pid=original_process.pid, expected_exit=terminal_exit,
    )
    for key in ("pid", "native_exit_code", "termination_state", "timeout_state",
                "failure_class", "stdout_marker_state", "stdout_byte_count", "stderr_byte_count"):
        assert type(raw_command_record[key]) is type(getattr(raw_failure_receipt, key))
        assert raw_command_record[key] == getattr(raw_failure_receipt, key)
    assert raw_command_record["run_id"] == "run_raw_evidence_failure"
    assert raw_command_record["command_index"] == 1
    # FD-level ordinary stdout survives the later helper's capsys.readouterr().
    # This is the existing actual receipt, not a new receipt or inferred exit.
    print("Actual raw-evidence-failure command-1.json:", file=sys.__stdout__, flush=True)
    print(json.dumps(raw_command_record, sort_keys=True), file=sys.__stdout__, flush=True)
    print("Original child terminal observation:",
          json.dumps(observed_metadata, sort_keys=True), file=sys.__stdout__, flush=True)

    from copy import deepcopy
    invalid_metadata = []
    for key, value in (
        ("pid", original_process.pid + 1),
        ("native_exit_code", True), ("native_exit_code", None), ("native_exit_code", str(terminal_exit)),
        ("timeout_state", "TRIGGERED"), ("termination_state", "NONE"),
        ("stdout_marker_state", "PASS"), ("failure_class", None),
        ("failure_class", "ENGVR_PROCESS_TERMINATION_FAILED"),
        ("stdout_byte_count", retained_lengths[0] + 1),
    ):
        altered_record = deepcopy(raw_command_record)
        altered_record[key] = value
        invalid_metadata.append((altered_record, deepcopy(observed_metadata)))
    for key, value in (
        ("pid", original_process.pid + 1),
        ("returned", (termination_state, False)),
        ("returned", (termination_state, 1)),
        ("returned", ("TERMINAL:UNPROVEN;TERMINAL:PROVEN", True)),
        ("returned", ("NONE", True)),
        ("post_poll", True), ("post_poll", None), ("post_poll", str(terminal_exit)),
        ("post_returncode", None),
    ):
        altered_observed = deepcopy(observed_metadata)
        altered_observed[key] = value
        invalid_metadata.append((deepcopy(raw_command_record), altered_observed))
    for altered_record, altered_observed in invalid_metadata:
        with pytest.raises(AssertionError):
            assert_failed_retention_record(
                altered_record, altered_observed,
                expected_pid=original_process.pid, expected_exit=terminal_exit,
            )
    # Explicit copied-metadata counterexample only: no child or receipt is changed.
    # A real observed zero remains valid; taskkill's zero cannot replace a nonzero child.
    nonzero_witness = terminal_exit if terminal_exit != 0 else 7
    copied_observed = deepcopy(observed_metadata)
    copied_observed["post_poll"] = copied_observed["post_returncode"] = nonzero_witness
    fabricated_zero = deepcopy(raw_command_record)
    fabricated_zero["native_exit_code"] = 0
    with pytest.raises(AssertionError):
        assert_failed_retention_record(
            fabricated_zero, copied_observed,
            expected_pid=original_process.pid, expected_exit=nonzero_witness,
        )
    time.sleep(0.2)
    assert {
        path: path.read_bytes()
        for path in (raw_stdout_path, raw_stderr_path, raw_command_path)
    } == raw_stable_bytes
    assert matching_drain_workers(raw_failure_receipt.pid) == ()


def _assert_exact_marker_line_contract(tmp_path: Path) -> None:
    marker = "REQUIRED_OK"
    chunk_size = 64 * 1024
    h_command = [
        sys.executable,
        "tools/validate_qku_computation_control_plane.py",
        "--domain",
        "h",
    ]
    assert runner._st12h_command_contract(h_command) == (
        1200,
        (
            "QKU_COMPUTATION_CONTROL_PLANE_VALIDATED domain=h "
            "contract_checks=36 golden_vectors=0",
            "ST12H_GROUPED_MATRIX_VALIDATED functions=6 control_cases=36 "
            "semantic_identities=42 custom_case_labels=0",
        ),
    )
    domain_contracts = (
        ("accounting", "contract_checks=16 golden_vectors=11"),
        ("execution", "contract_checks=14 golden_vectors=2"),
        ("llm", "contract_checks=15 golden_vectors=0"),
        ("operations", "contract_checks=15 golden_vectors=0"),
        ("security", "contract_checks=9 golden_vectors=0"),
        ("source", "contract_checks=7 golden_vectors=0"),
    )
    for domain, contract_counts in domain_contracts:
        command = [
            sys.executable,
            "tools/validate_qku_computation_control_plane.py",
            "--domain",
            domain,
        ]
        assert runner._st12h_command_contract(command) == (
            1200,
            (
                "QKU_COMPUTATION_CONTROL_PLANE_VALIDATED "
                f"domain={domain} {contract_counts}",
            ),
        )
    independent_command = [
        sys.executable,
        "tools/independent_validate_qku_computation_control_plane.py",
    ]
    assert runner._st12h_command_contract(independent_command) == (
        1800,
        (
            "QKU_COMPUTATION_CONTROL_PLANE_INDEPENDENTLY_VALIDATED domains=13",
            "ST12H_MATH_40_44_INDEPENDENTLY_RECONSTRUCTED count=5",
            "ST12H_MATH_01_52_COVERAGE_RECONSTRUCTED count=52 h_direct=5 "
            "inherited=47 identity_only=0 unexecuted=0",
        ),
    )
    accounting_command = [
        sys.executable,
        "tools/independent_validate_qku_computation_control_plane_accounting.py",
    ]
    assert runner._st12h_command_contract(accounting_command) == (
        1200,
        (
            "QKU_ACCOUNTING_INDEPENDENTLY_VALIDATED controls=16 policies=80 "
            "bindings=80 math=13 oracles=13 vectors=13 effects=0",
        ),
    )
    execution_command = [
        sys.executable,
        "tools/independent_validate_qku_computation_control_plane_execution.py",
    ]
    assert runner._st12h_command_contract(execution_command) == (
        1200,
        (
            "QKU_EXECUTION_INDEPENDENTLY_VALIDATED controls=9 identities=8 "
            "gates=13 lifecycle=NO_WRITE effects=0 blockers=9",
        ),
    )
    remaining_independent_contracts = (
        (
            "independent_validate_qku_computation_control_plane_llm.py",
            "QKU_LLM_INDEPENDENTLY_VALIDATED checks=8 rejection_cases=9 "
            "inference_calls=0 numeric_authority=0",
        ),
        (
            "independent_validate_qku_computation_control_plane_operations.py",
            "QKU_OPERATIONS_INDEPENDENTLY_VALIDATED operation_contracts=15 "
            "executable_op14_checks=21 bundle_fields=30 lifecycle_transitions=6 "
            "prohibited_transition_rejections=58 v18_integration_rows=16 "
            "real_review_truths_reconstructed=1 canonical_math01_partition=39+9 "
            "metric_durable_values_consumed_and_validated=38/38 "
            "metric_values_produced_by_st12f=0",
        ),
        (
            "independent_validate_qku_computation_control_plane_security.py",
            "QKU_SECURITY_INDEPENDENTLY_VALIDATED "
            "certified_importlib_resource_import_count=2 "
            "other_importlib_import_count=0 dynamic_import_call_count=0",
        ),
        (
            "independent_validate_qku_computation_control_plane_source.py",
            "QKU_SOURCE_INDEPENDENTLY_VALIDATED source_rows=29 overlays=7 "
            "binding_rules=1 v34_primary_sources=55 v34_numeric_authorities=621",
        ),
    )
    for script_name, expected_marker in remaining_independent_contracts:
        assert runner._st12h_command_contract([sys.executable, f"tools/{script_name}"]) == (
            1200,
            (expected_marker,),
        )
    positive_lines = (
        b"REQUIRED_OK\n",
        b"   REQUIRED_OK\n",
        b"REQUIRED_OK   \n",
        b"\tREQUIRED_OK\t\n",
        b"\vREQUIRED_OK\f\r\n",
        b"REQUIRED_OK",
        b"REQUIRED_OK\r\n",
        b" " * (chunk_size - 4) + b"REQUIRED_OK\n",
    )
    negative_lines = (
        b"REQUIRED_OK trailing-garbage\n",
        b"REQUIRED_OK:detail\n",
        b"REQUIRED_OK_suffix\n",
        b"prefix REQUIRED_OK\n",
        b"xREQUIRED_OK\n",
        b"REQUIRED_OK\ttrailing-garbage\n",
        b"prefix EMBEDDED REQUIRED_OK suffix\n",
    )
    marker_root = tmp_path / "exact-marker-lines"
    marker_root.mkdir()
    for index, content in enumerate(positive_lines, start=1):
        path = marker_root / f"positive-{index}.bin"
        path.write_bytes(content)
        assert reliability._file_marker_states((path,), (marker,)) == (), content
    for index, content in enumerate(negative_lines, start=1):
        path = marker_root / f"negative-{index}.bin"
        path.write_bytes(content)
        assert reliability._file_marker_states((path,), (marker,)) == (marker,), content


def _assert_prestart_failure_custody_contract(
    monkeypatch,
    tmp_path: Path,
) -> None:
    REPO_ROOT = (tmp_path / "prestart-fixture-repo").resolve()
    REPO_ROOT.mkdir(parents=True, exist_ok=False)
    evidence_root = tmp_path / "prestart-failure-evidence"
    missing_cwd = (tmp_path / "missing-cwd").resolve()
    missing_executable = str((tmp_path / "missing-executable.exe").resolve())
    cases = (
        ((sys.executable, "embedded\0nul"), REPO_ROOT, None, "ValueError"),
        ((sys.executable, "-c", "pass"), REPO_ROOT, {1: "value"}, "TypeError"),
        ((sys.executable, "-c", "pass"), REPO_ROOT, {"KEY": 1}, "TypeError"),
        ((missing_executable,), REPO_ROOT, None, "FileNotFoundError"),
        ((sys.executable, "-c", "pass"), missing_cwd, None, "FileNotFoundError"),
    )
    real_popen = reliability.subprocess.Popen
    actual_child_starts = []

    def track_successful_start(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        actual_child_starts.append(process.pid)
        return process

    with monkeypatch.context() as start_patch:
        start_patch.setattr(
            reliability.subprocess,
            "Popen",
            track_successful_start,
        )
        receipts = tuple(
            reliability.supervise_command(
                command,
                cwd=cwd,
                run_id="run_prestart_failure_matrix",
                phase="unit-prestart",
                command_index=index,
                evidence_root=evidence_root,
                required_markers=("MUST_NOT_PASS",),
                environment=environment,
                mirror_stdout=False,
                mirror_stderr=False,
            )
            for index, (command, cwd, environment, _expected_start) in enumerate(
                cases,
                start=1,
            )
        )
    assert actual_child_starts == []
    for receipt, (_command, _cwd, _environment, expected_start) in zip(
        receipts,
        cases,
        strict=True,
    ):
        assert receipt.pid is None
        assert receipt.native_exit_code is None
        assert receipt.start_failure_class == expected_start
        assert receipt.failure_class == "ENGVR_PROCESS_START_FAILED"
        assert receipt.timeout_state == "NOT_CONFIGURED"
        assert receipt.termination_state == "NOT_REQUIRED"
        assert receipt.stdout_marker_state != "PASS"
        assert Path(receipt.stdout_path).stat().st_size == 0
        assert Path(receipt.stderr_path).stat().st_size == 0
        assert json.loads(
            (evidence_root / f"command-{receipt.command_index}.json").read_text(
                encoding="utf-8"
            )
        ) == reliability._json_compatible(receipt)
        assert reliability.command_attempt_accounting((receipt,)) == (
            0,
            0,
            receipt.command_index,
            None,
        )
    assert not list(evidence_root.glob(".command-*.reserve"))
    assert not list(evidence_root.glob(".*.tmp"))

    aggregate_parent = (tmp_path / "prestart-aggregate-parent").resolve()
    aggregate_paths, aggregate_probe = reliability.resolve_validation_run_paths(
        REPO_ROOT,
        explicit_process_root=aggregate_parent,
        run_id="run_prestart_aggregate",
        projected_relative_paths=("command-1.json",),
    )
    aggregate_commands = (
        (sys.executable, "embedded\0nul"),
        (sys.executable, "-c", "print('MUST_NOT_START')"),
    )
    reliability.write_run_provenance(
        aggregate_paths,
        aggregate_probe,
        phase=runner.FAST_PREFLIGHT_PHASE,
        command_count=2,
        text_integrity_preflight_state="PASS",
    )
    aggregate_starts = []

    def track_aggregate_start(*args, **kwargs):
        process = real_popen(*args, **kwargs)
        aggregate_starts.append(process.pid)
        return process

    with monkeypatch.context() as aggregate_patch:
        aggregate_patch.setattr(
            runner,
            "_execute_supervised_command",
            reliability.supervise_command,
        )
        aggregate_patch.setattr(
            reliability.subprocess,
            "Popen",
            track_aggregate_start,
        )
        aggregate_patch.setattr(runner, "_RUN_COMMANDS_CLEANUP_REPO_ROOT", None)
        aggregate_result = runner.run_commands(
            aggregate_commands,
            phase=runner.FAST_PREFLIGHT_PHASE,
            run_paths=aggregate_paths,
            defer_success_markers=True,
            execution_plan=runner._prepare_execution_plan(aggregate_commands),
        )
        aggregate_receipts = runner._LAST_COMMAND_RECEIPTS
        final_result, cleanup_state, completion = runner._finalize_validation_run(
            run_paths=aggregate_paths,
            probe=aggregate_probe,
            phase=runner.FAST_PREFLIGHT_PHASE,
            planned_count=2,
            expected_plan=runner._LAST_EXPECTED_COMMAND_PLAN,
            receipts=aggregate_receipts,
            result=aggregate_result,
            text_state="PASS",
        )
    assert aggregate_starts == []
    assert len(aggregate_receipts) == 1
    assert aggregate_receipts[0].failure_class == "ENGVR_PROCESS_START_FAILED"
    assert not (aggregate_paths.evidence_root / "command-2.json").exists()
    assert final_result != 0
    assert cleanup_state.startswith("PASS")
    assert completion.command_count_started == 0
    assert completion.command_count_completed == 0
    assert completion.first_failed_command_index_or_null == 1
    assert completion.final_state == "FAIL"


def _assert_write_once_command_evidence_contract(monkeypatch, tmp_path: Path) -> None:
    evidence_root = tmp_path / "write-once-command-evidence"
    first_receipt = reliability.supervise_command(
        (
            sys.executable,
            "-c",
            "import sys;print('FIRST');print('FIRST-ERR', file=sys.stderr)",
        ),
        cwd=REPO_ROOT,
        run_id="run_write_once_command",
        phase="unit-supervision",
        command_index=1,
        evidence_root=evidence_root,
        mirror_stdout=False,
        mirror_stderr=False,
    )
    assert first_receipt.native_exit_code == 0
    evidence_paths = tuple(
        evidence_root / name
        for name in (
            "command-1.stdout.bin",
            "command-1.stderr.bin",
            "command-1.json",
        )
    )
    first_bytes = {path: path.read_bytes() for path in evidence_paths}
    real_popen = reliability.subprocess.Popen
    second_starts = []

    def track_second_start(*args, **kwargs):
        second_starts.append((args, kwargs))
        return real_popen(*args, **kwargs)

    with monkeypatch.context() as duplicate_patch:
        duplicate_patch.setattr(reliability.subprocess, "Popen", track_second_start)
        with pytest.raises(
            reliability.ValidationReliabilityError,
            match="ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
        ) as raised:
            reliability.supervise_command(
                (sys.executable, "-c", "print('SECOND')"),
                cwd=REPO_ROOT,
                run_id="run_write_once_command",
                phase="unit-supervision",
                command_index=1,
                evidence_root=evidence_root,
                mirror_stdout=False,
                mirror_stderr=False,
            )
    assert raised.value.code == "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED"
    assert second_starts == []
    assert {path: path.read_bytes() for path in evidence_paths} == first_bytes
    assert not list(evidence_root.glob(".command-*.reserve"))
    run_path = evidence_root / "run.json"
    reliability.atomic_write_json(run_path, {"run": "FIRST"})
    run_bytes = run_path.read_bytes()
    with pytest.raises(
        reliability.ValidationReliabilityError,
        match="ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
    ):
        reliability.atomic_write_json(run_path, {"run": "SECOND"})
    assert run_path.read_bytes() == run_bytes


def _assert_receipt_accounting_contract(tmp_path: Path) -> None:
    count_evidence = tmp_path / "count-evidence"
    reliability.atomic_write_json(count_evidence / "command-1.json", {"index": 1})
    reliability.atomic_write_json(count_evidence / "command-2.json", {"index": 2})
    completion_path = count_evidence / "completion.json"
    reliability.atomic_write_json(
        completion_path,
        reliability.ValidationCompletionReceiptV1(
            run_id="run_supervision_matrix",
            phase="unit-supervision",
            command_count_planned=7,
            command_count_started=2,
            command_count_completed=2,
            first_failed_command_index_or_null=2,
            terminal_native_exit_code=7,
            required_marker_state="FAIL",
            process_root_cleanup_state="PENDING",
            evidence_root_state="PRESENT",
            text_integrity_preflight_state="PASS",
            final_state="FAIL",
        ),
    )
    assert json.loads(completion_path.read_text(encoding="utf-8"))["run_id"] == (
        "run_supervision_matrix"
    )
    completion_payload = json.loads(completion_path.read_text(encoding="utf-8"))
    assert completion_payload["command_count_started"] == 2
    assert completion_payload["command_count_completed"] == 2
    assert completion_payload["first_failed_command_index_or_null"] == 2
    assert reliability.command_receipt_file_indexes(count_evidence) == (1, 2)
    assert not list(count_evidence.glob(".completion.json.*.tmp"))

def _assert_complete_terminal_evidence_contract(monkeypatch, tmp_path: Path) -> None:
    REPO_ROOT = (tmp_path / "terminal-fixture-repo").resolve()
    REPO_ROOT.mkdir(parents=True, exist_ok=False)
    phase = runner.FAST_PREFLIGHT_PHASE
    marker = "COMPLETE_EVIDENCE_OK"
    external_parent = (tmp_path / "complete-evidence-parent").resolve()
    probes = {}

    def build_case(label: str, tamper: str | None):
        run_paths, probe = reliability.resolve_validation_run_paths(
            REPO_ROOT,
            explicit_process_root=external_parent,
            run_id=f"run_complete_evidence_{label}",
            projected_relative_paths=("command-1.stdout.bin",),
        )
        probes[label] = probe
        reliability.write_run_provenance(
            run_paths,
            probe,
            phase=phase,
            command_count=1,
            text_integrity_preflight_state="PASS",
        )
        command = (
            sys.executable,
            "-c",
            "import sys;print('COMPLETE_EVIDENCE_OK');"
            "print('retained-stderr', file=sys.stderr)",
        )
        receipt = reliability.supervise_command(
            command,
            cwd=REPO_ROOT,
            run_id=run_paths.run_id,
            phase=phase,
            command_index=1,
            evidence_root=run_paths.evidence_root,
            required_markers=(marker,),
            timeout_seconds=30,
            mirror_stdout=False,
            mirror_stderr=False,
        )
        stdout_path = run_paths.evidence_root / "command-1.stdout.bin"
        stderr_path = run_paths.evidence_root / "command-1.stderr.bin"
        command_path = run_paths.evidence_root / "command-1.json"
        if tamper == "missing-run":
            (run_paths.evidence_root / "run.json").unlink()
        elif tamper == "missing-stdout":
            stdout_path.unlink()
        elif tamper == "truncated-stderr":
            stderr_path.write_bytes(b"")
        elif tamper == "modified-command-json":
            payload = json.loads(command_path.read_text(encoding="utf-8"))
            payload["phase"] = "tampered-phase"
            command_path.write_text(
                json.dumps(payload, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        elif tamper == "extra-command-artifact":
            (run_paths.evidence_root / "command-2.json").write_text(
                "{}\n",
                encoding="utf-8",
            )
        elif tamper == "linked-stdout":
            link_source = run_paths.evidence_root / "linked-stdout-source.bin"
            stdout_path.replace(link_source)
            os.link(link_source, stdout_path)
        elif tamper == "outside-receipt-path":
            outside_path = tmp_path / "outside-command-stdout.bin"
            outside_path.write_bytes(stdout_path.read_bytes())
            receipt = replace(receipt, stdout_path=str(outside_path.resolve()))

        expected_plan = reliability.build_command_evidence_plan(
            run_id=run_paths.run_id,
            phase=phase,
            commands=(command,),
            cwd=REPO_ROOT,
        )
        if tamper in {
            "plan-wrong-run",
            "plan-wrong-phase",
            "plan-wrong-argv",
            "plan-wrong-cwd",
        }:
            receipt = replace(
                receipt,
                run_id=(
                    "wrong_run_id"
                    if tamper == "plan-wrong-run"
                    else receipt.run_id
                ),
                phase=(
                    "wrong-phase"
                    if tamper == "plan-wrong-phase"
                    else receipt.phase
                ),
                argv=(
                    (sys.executable, "-c", "print('wrong argv')")
                    if tamper == "plan-wrong-argv"
                    else receipt.argv
                ),
                cwd=(
                    str(tmp_path.resolve())
                    if tamper == "plan-wrong-cwd"
                    else receipt.cwd
                ),
            )
            command_path.write_text(
                json.dumps(
                    reliability._json_compatible(receipt),
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
        elif tamper == "missing-plan-entry":
            expected_plan = ()
        elif tamper == "duplicate-plan-entry":
            expected_plan = (expected_plan[0], expected_plan[0])

        result, cleanup_state, completion = runner._finalize_validation_run(
            run_paths=run_paths,
            probe=probe,
            phase=phase,
            planned_count=1,
            expected_plan=expected_plan,
            receipts=(receipt,),
            result=0,
            text_state="PASS",
        )
        return result, cleanup_state, completion, run_paths

    with monkeypatch.context() as production_patch:
        production_patch.setattr(
            runner,
            "cleanup_validation_run",
            reliability.cleanup_validation_run,
        )
        production_patch.setattr(
            runner,
            "atomic_write_json",
            reliability.atomic_write_json,
        )
        production_patch.setattr(
            runner,
            "validate_complete_run_evidence",
            reliability.validate_complete_run_evidence,
        )
        production_patch.setattr(
            runner,
            "validate_published_completion_receipt",
            reliability.validate_published_completion_receipt,
        )
        valid_result, valid_cleanup, valid_completion, valid_paths = build_case(
            "valid",
            None,
        )
        assert valid_result == 0
        assert valid_cleanup.startswith("PASS")
        assert valid_completion.final_state == "PASS"
        assert {
            path.name for path in valid_paths.evidence_root.iterdir() if path.is_file()
        } == {
            "run.json",
            "command-1.stdout.bin",
            "command-1.stderr.bin",
            "command-1.json",
            "cleanup.json",
            "completion.json",
        }
        completion_before = (
            valid_paths.evidence_root / "completion.json"
        ).read_bytes()
        cleanup_before = (valid_paths.evidence_root / "cleanup.json").read_bytes()
        second_result, _second_cleanup, second_completion = (
            runner._finalize_validation_run(
                run_paths=valid_paths,
                probe=probes["valid"],
                phase=phase,
                planned_count=1,
                expected_plan=reliability.build_command_evidence_plan(
                    run_id=valid_paths.run_id,
                    phase=phase,
                    commands=((sys.executable, "-c", "unused"),),
                    cwd=REPO_ROOT,
                ),
                receipts=(),
                result=1,
                text_state="PASS",
            )
        )
        assert second_result != 0
        assert second_completion.final_state == "FAIL"
        assert (valid_paths.evidence_root / "completion.json").read_bytes() == (
            completion_before
        )
        assert (valid_paths.evidence_root / "cleanup.json").read_bytes() == cleanup_before

        for label, tamper in (
            ("missing_run", "missing-run"),
            ("missing_stdout", "missing-stdout"),
            ("truncated_stderr", "truncated-stderr"),
            ("modified_command", "modified-command-json"),
            ("extra_command", "extra-command-artifact"),
            ("linked_stdout", "linked-stdout"),
            ("outside_path", "outside-receipt-path"),
            ("wrong_run", "plan-wrong-run"),
            ("wrong_phase", "plan-wrong-phase"),
            ("wrong_argv", "plan-wrong-argv"),
            ("wrong_cwd", "plan-wrong-cwd"),
            ("missing_plan", "missing-plan-entry"),
            ("duplicate_plan", "duplicate-plan-entry"),
        ):
            failed_result, failed_cleanup, failed_completion, _failed_paths = (
                build_case(label, tamper)
            )
            assert failed_result != 0
            assert failed_cleanup.startswith("PASS")
            assert failed_completion.final_state == "FAIL"
            if tamper == "linked-stdout":
                # The negative assertion above observes the real hard link.
                # Release only the extra link created by this synthetic case.
                linked_source = _failed_paths.evidence_root / "linked-stdout-source.bin"
                assert os.path.samefile(
                    linked_source, _failed_paths.evidence_root / "command-1.stdout.bin"
                )
                linked_source.unlink()

        reordered_paths, reordered_probe = reliability.resolve_validation_run_paths(
            REPO_ROOT,
            explicit_process_root=external_parent,
            run_id="run_complete_evidence_reordered",
            projected_relative_paths=("command-2.stdout.bin",),
        )
        reordered_commands = (
            (sys.executable, "-c", "print('ONE')"),
            (sys.executable, "-c", "print('TWO')"),
        )
        reliability.write_run_provenance(
            reordered_paths,
            reordered_probe,
            phase=phase,
            command_count=2,
            text_integrity_preflight_state="PASS",
        )
        reordered_receipts = tuple(
            reliability.supervise_command(
                command,
                cwd=REPO_ROOT,
                run_id=reordered_paths.run_id,
                phase=phase,
                command_index=index,
                evidence_root=reordered_paths.evidence_root,
                mirror_stdout=False,
                mirror_stderr=False,
            )
            for index, command in enumerate(reordered_commands, start=1)
        )
        reordered_result, reordered_cleanup, reordered_completion = (
            runner._finalize_validation_run(
                run_paths=reordered_paths,
                probe=reordered_probe,
                phase=phase,
                planned_count=2,
                expected_plan=reliability.build_command_evidence_plan(
                    run_id=reordered_paths.run_id,
                    phase=phase,
                    commands=reordered_commands,
                    cwd=REPO_ROOT,
                ),
                receipts=tuple(reversed(reordered_receipts)),
                result=0,
                text_state="PASS",
            )
        )
        assert reordered_result != 0
        assert reordered_cleanup.startswith("PASS")
        assert reordered_completion.final_state == "FAIL"


def _assert_receipt_publication_failure_accounting(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    REPO_ROOT = (tmp_path / "publication-fixture-repo").resolve()
    REPO_ROOT.mkdir(parents=True, exist_ok=False)
    capsys.readouterr()
    external_parent = (tmp_path / "publication-failure-parent").resolve()
    run_paths, probe = reliability.resolve_validation_run_paths(
        REPO_ROOT,
        explicit_process_root=external_parent,
        run_id="run_receipt_publication_failure",
        projected_relative_paths=("command-1.stdout.bin",),
    )
    commands = (
        (sys.executable, "-c", "print('ATTEMPT_ONE')"),
        (sys.executable, "-c", "print('MUST_NOT_START')"),
    )
    reliability.write_run_provenance(
        run_paths,
        probe,
        phase=runner.FAST_PREFLIGHT_PHASE,
        command_count=len(commands),
        text_integrity_preflight_state="PASS",
    )
    real_atomic_write = reliability.atomic_write_json
    real_popen = reliability.subprocess.Popen
    child_starts = []

    def fail_command_receipt(path, payload):
        if Path(path).name == "command-1.json":
            raise reliability.ValidationReliabilityError(
                "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
                "synthetic command receipt publication failure",
            )
        return real_atomic_write(path, payload)

    def track_child_start(*args, **kwargs):
        child_starts.append((args, kwargs))
        return real_popen(*args, **kwargs)

    with monkeypatch.context() as production_patch:
        production_patch.setattr(
            runner,
            "_execute_supervised_command",
            reliability.supervise_command,
        )
        production_patch.setattr(
            runner,
            "cleanup_validation_run",
            reliability.cleanup_validation_run,
        )
        production_patch.setattr(
            runner,
            "atomic_write_json",
            reliability.atomic_write_json,
        )
        production_patch.setattr(
            runner,
            "validate_complete_run_evidence",
            reliability.validate_complete_run_evidence,
        )
        production_patch.setattr(
            runner,
            "validate_published_completion_receipt",
            reliability.validate_published_completion_receipt,
        )
        production_patch.setattr(runner, "_RUN_COMMANDS_CLEANUP_REPO_ROOT", None)
        with monkeypatch.context() as publication_patch:
            publication_patch.setattr(
                reliability,
                "atomic_write_json",
                fail_command_receipt,
            )
            publication_patch.setattr(
                reliability.subprocess,
                "Popen",
                track_child_start,
            )
            run_result = runner.run_commands(
                commands,
                phase=runner.FAST_PREFLIGHT_PHASE,
                run_paths=run_paths,
                defer_success_markers=True,
                execution_plan=runner._prepare_execution_plan(commands),
            )
        receipts = runner._LAST_COMMAND_RECEIPTS
        assert run_result != 0
        assert len(child_starts) == 1
        assert len(receipts) == 1
        assert receipts[0].native_exit_code == 0
        assert receipts[0].failure_class == "ENGVR_ATOMIC_RECEIPT_WRITE_FAILED"
        result, cleanup_state, completion = runner._finalize_validation_run(
            run_paths=run_paths,
            probe=probe,
            phase=runner.FAST_PREFLIGHT_PHASE,
            planned_count=len(commands),
            expected_plan=runner._LAST_EXPECTED_COMMAND_PLAN,
            receipts=receipts,
            result=run_result,
            text_state="PASS",
        )
    output = capsys.readouterr()
    assert result != 0
    assert cleanup_state.startswith("PASS")
    assert completion.command_count_started == 1
    assert completion.command_count_completed == 1
    assert completion.first_failed_command_index_or_null == 1
    assert completion.terminal_native_exit_code == 0
    assert completion.final_state == "FAIL"
    assert not (run_paths.evidence_root / "command-1.json").exists()
    assert json.loads(
        (run_paths.evidence_root / "completion.json").read_text(encoding="utf-8")
    )["final_state"] == "FAIL"
    assert output.out.count(runner.SUCCESS_MARKER) == 0
    assert output.out.count(runner.PHASE_SUCCESS_MARKER_PREFIX) == 0

    # Unlike the terminal publication failure above, this deterministic port
    # returns an integer leader exit while the original tree remains UNPROVEN.
    uncertain_paths, uncertain_probe = reliability.resolve_validation_run_paths(
        REPO_ROOT, explicit_process_root=tmp_path / "uncertain-publication-parent",
        run_id="run_uncertain_publication", projected_relative_paths=("command-1.json",),
    )
    command_process = SimpleNamespace(pid=7811, returncode=7)
    publication_error = OSError("synthetic secondary publication failure")
    publications, acquisitions, reports, cleanups = [], [], [], []

    def acquire_one(*args, **kwargs):
        acquisitions.append((args, kwargs))
        return command_process

    def uncertain_output(process, **kwargs):
        assert process is command_process
        for name, payload in (("stdout", b"OUT"), ("stderr", b"ERR")):
            stream = kwargs[name + "_stream"]
            stream.write(payload)
            stream.close()
            kwargs[name + "_outcome"]["evidence_complete"] = True
        return (7, "NOT_CONFIGURED", "TASKKILL_T:128;TERMINAL:UNPROVEN",
                "ENGVR_PROCESS_TERMINATION_FAILED")

    def reject_publication(path, payload):
        publications.append((path, payload))
        raise publication_error

    with monkeypatch.context() as uncertainty:
        uncertainty.setattr(runner, "_RUN_COMMANDS_SUPERVISION", None)
        uncertainty.setattr(runner, "_RUN_COMMANDS_CLEANUP_REPO_ROOT", None)
        uncertainty.setattr(runner, "_RUN_PROVENANCE_WRITTEN", False)
        uncertainty.setattr(runner, "_ACTIVE_SCAN_LAUNCH", None)
        uncertainty.setattr(runner, "_execute_supervised_command", reliability.supervise_command)
        uncertainty.setattr(reliability.subprocess, "Popen", acquire_one)
        uncertainty.setattr(reliability, "_supervise_native_output", uncertain_output)
        uncertainty.setattr(reliability, "atomic_write_json", reject_publication)
        uncertainty.setattr(runner, "cleanup_validation_run", lambda paths: cleanups.append(paths))
        uncertainty.setattr(runner, "atomic_write_json", lambda path, value: reports.append((path.name, value)))
        uncertain_result = runner.run_commands(
            commands, phase=runner.FAST_PREFLIGHT_PHASE, run_paths=uncertain_paths,
            defer_success_markers=True, execution_plan=runner._prepare_execution_plan(commands),
        )
        pending = runner._RUN_COMMANDS_SUPERVISION
        assert uncertain_result == 1 and pending["pending"] is True
        assert len(acquisitions) == len(publications) == 1
        original_receipt = publications[0][1]
        original_error = pending["errors"][0]
        assert type(original_error) is reliability.ValidationReliabilityError
        assert original_error.code == "ENGVR_PROCESS_TERMINATION_FAILED"
        assert original_error.__cause__ is publication_error
        assert original_error.owned_process is command_process
        assert original_error.command_receipt is original_receipt
        assert pending["receipt"] is original_receipt
        assert runner._LAST_COMMAND_RECEIPTS == (original_receipt,)
        assert runner._LAST_COMMAND_RECEIPTS[0] is original_receipt
        assert original_receipt.native_exit_code == 7
        assert original_receipt.failure_class == "ENGVR_PROCESS_TERMINATION_FAILED"
        assert original_receipt.termination_state == "TASKKILL_T:128;TERMINAL:UNPROVEN"
        assert original_receipt.stdout_byte_count == original_receipt.stderr_byte_count == 3
        assert not (uncertain_paths.evidence_root / "command-1.json").exists()
        result, state, completion = runner._finalize_validation_run(
            run_paths=uncertain_paths, probe=uncertain_probe, phase=runner.FAST_PREFLIGHT_PHASE,
            planned_count=2, expected_plan=runner._LAST_EXPECTED_COMMAND_PLAN,
            receipts=runner._LAST_COMMAND_RECEIPTS, result=uncertain_result, text_state="PASS",
        )
        assert result == 1 and state == "SKIPPED_PROCESS_TERMINATION_UNPROVEN"
        assert completion.final_state == "FAIL"
        assert completion.command_count_started == completion.command_count_completed == 1
        assert completion.terminal_native_exit_code == 7
        assert cleanups == [] and uncertain_paths.process_root.is_dir()
        assert [name for name, _ in reports] == ["cleanup.json", "completion.json"]
        assert reports[0][1]["cleanup_state"] == "SKIPPED_PROCESS_TERMINATION_UNPROVEN"
        assert original_error in pending["errors"]
    assert Path(original_receipt.stdout_path).read_bytes() == b"OUT"
    assert Path(original_receipt.stderr_path).read_bytes() == b"ERR"

    # Exceptions retain a taskkill helper's different ownership and the original
    # group/cancellation object; no substitute process is actually launched.
    for ordinal, kind in enumerate(("direct", "group", "cancel"), 1):
        helper_process = SimpleNamespace(pid=8822)
        original = reliability.ValidationReliabilityError(
            "ENGVR_PROCESS_TERMINATION_FAILED", "synthetic taskkill unresolved",
        )
        original.owned_process = helper_process
        original.stdout_prefix, original.stderr_prefix = b"partial out", b"partial err"
        escaped = (original if kind == "direct" else
                   ExceptionGroup("nested", [ExceptionGroup("inner", [original])])
                   if kind == "group" else KeyboardInterrupt("synthetic cancellation"))
        starts, writes = [], []

        def acquire_error_case(*args, **kwargs):
            starts.append(command_process)
            return command_process

        def raise_after_acquisition(process, **kwargs):
            assert process is command_process
            kwargs["stdout_stream"].close()
            kwargs["stderr_stream"].close()
            raise escaped

        with monkeypatch.context() as exception_patch:
            exception_patch.setattr(reliability.subprocess, "Popen", acquire_error_case)
            exception_patch.setattr(reliability, "_supervise_native_output", raise_after_acquisition)
            exception_patch.setattr(reliability, "atomic_write_json", lambda *args: writes.append(args))
            with pytest.raises(type(escaped)) as caught:
                reliability.supervise_command(
                    commands[0], cwd=REPO_ROOT, run_id="run_escaped_supervision",
                    phase=runner.FAST_PREFLIGHT_PHASE, command_index=ordinal,
                    evidence_root=tmp_path / f"escaped-supervision-{ordinal}",
                    mirror_stdout=False, mirror_stderr=False,
                )
        assert caught.value is escaped
        assert starts == [command_process] and writes == []
        assert not hasattr(escaped, "command_receipt")
        if kind == "direct":
            assert escaped.owned_process is helper_process
            assert escaped.command_process is command_process
            assert escaped.stdout_prefix == b"partial out" and escaped.stderr_prefix == b"partial err"
        else:
            assert escaped.owned_process is command_process
            if kind == "group":
                assert escaped.exceptions[0].exceptions[0] is original
                assert original.owned_process is helper_process


def _assert_exact_cleanup_contract(monkeypatch) -> None:
    with tempfile.TemporaryDirectory(prefix="qtt-supervision-cleanup-") as temp_root:
        REPO_ROOT = (Path(temp_root) / "cleanup-fixture-repo").resolve()
        REPO_ROOT.mkdir()
        external_parent = Path(temp_root) / "qttv"
        historical = external_parent / "historical-unrelated"
        historical.mkdir(parents=True)
        historical_sentinel = historical / "owner.txt"
        historical_sentinel.write_text("preserve\n", encoding="utf-8")
        historical_mode = historical_sentinel.stat().st_mode
        retained_evidence = external_parent / "owner-retained.evidence"
        retained_evidence.mkdir()
        retained_evidence_sentinel = retained_evidence / "owner.txt"
        retained_evidence_sentinel.write_text("preserve\n", encoding="utf-8")
        retained_evidence_mode = retained_evidence_sentinel.stat().st_mode
        run_paths, _probe = reliability.resolve_validation_run_paths(
            REPO_ROOT,
            explicit_process_root=external_parent.resolve(),
            run_id="run_cleanup_matrix",
        )
        assert run_paths.process_root.name == run_paths.process_child_name
        assert re.fullmatch(r"r\d{12}_\d+_\d+(?:_\d+)?", run_paths.process_child_name)
        assert run_paths.process_child_name != run_paths.run_id
        assert run_paths.evidence_root.name == f"{run_paths.run_id}.evidence"
        run_evidence_sentinel = run_paths.evidence_root / "owner.txt"
        run_evidence_sentinel.write_text("preserve\n", encoding="utf-8")
        read_only_path = run_paths.process_root / "git-like" / "objects" / "aa" / "object"
        read_only_path.parent.mkdir(parents=True)
        read_only_path.write_bytes(b"read-only object\n")
        if os.name == "nt":
            os.chmod(read_only_path, reliability.stat.S_IREAD)
        real_chmod = reliability.os.chmod
        chmod_paths = []

        def tracked_chmod(path, mode, **kwargs):
            chmod_paths.append(Path(path).resolve(strict=False))
            return real_chmod(path, mode, **kwargs)

        with monkeypatch.context() as cleanup_patch:
            cleanup_patch.setattr(reliability.os, "chmod", tracked_chmod)
            assert reliability.cleanup_validation_run(run_paths).startswith("PASS")
        cleanup_payload = json.loads(
            (run_paths.evidence_root / "cleanup.json").read_text(encoding="utf-8")
        )
        expected_retry_count = 1 if os.name == "nt" else 0
        assert cleanup_payload["read_only_retry_count"] == expected_retry_count
        assert chmod_paths == (
            [read_only_path.resolve(strict=False)] if os.name == "nt" else []
        )
        assert not run_paths.process_root.exists()
        assert external_parent.is_dir()
        assert historical_sentinel.read_text(encoding="utf-8") == "preserve\n"
        assert historical_sentinel.stat().st_mode == historical_mode
        assert retained_evidence_sentinel.read_text(encoding="utf-8") == "preserve\n"
        assert retained_evidence_sentinel.stat().st_mode == retained_evidence_mode
        assert run_evidence_sentinel.read_text(encoding="utf-8") == "preserve\n"

        real_rmtree = reliability.shutil.rmtree
        nonpermission_root = external_parent / "nonpermission-owned-root"
        nonpermission_path = nonpermission_root / "object"
        nonpermission_root.mkdir()
        nonpermission_path.write_bytes(b"object\n")
        nonpermission_chmod_calls = []

        def invoke_nonpermission(_target, *, onexc):
            onexc(
                os.unlink,
                nonpermission_path,
                FileNotFoundError("synthetic non-permission failure"),
            )

        with monkeypatch.context() as nonpermission_patch:
            nonpermission_patch.setattr(
                reliability.shutil,
                "rmtree",
                invoke_nonpermission,
            )
            nonpermission_patch.setattr(
                reliability.os,
                "chmod",
                lambda *args, **kwargs: nonpermission_chmod_calls.append(
                    (args, kwargs)
                ),
            )
            with pytest.raises(
                FileNotFoundError,
                match="synthetic non-permission failure",
            ):
                reliability.remove_exact_run_owned_process_tree(
                    nonpermission_root,
                    expected_run_root=nonpermission_root,
                    repo_root=REPO_ROOT,
                    evidence_root=retained_evidence,
                )
        assert nonpermission_chmod_calls == []
        assert nonpermission_path.read_bytes() == b"object\n"
        real_rmtree(nonpermission_root)

        second_failure_root = external_parent / "second-failure-owned-root"
        second_failure_path = second_failure_root / "object"
        second_failure_root.mkdir()
        second_failure_path.write_bytes(b"object\n")
        second_failure_chmod_paths = []

        def fail_second_removal(_path):
            raise PermissionError("synthetic second removal failure")

        def invoke_permission_failure(_target, *, onexc):
            onexc(
                fail_second_removal,
                second_failure_path,
                PermissionError("synthetic first removal failure"),
            )

        with monkeypatch.context() as second_failure_patch:
            second_failure_patch.setattr(
                reliability.shutil,
                "rmtree",
                invoke_permission_failure,
            )
            second_failure_patch.setattr(
                reliability.os,
                "chmod",
                lambda path, _mode, **_kwargs: second_failure_chmod_paths.append(
                    Path(path).resolve(strict=False)
                ),
            )
            expected_second_failure_type = (
                reliability.ValidationReliabilityError
                if os.name == "nt"
                else PermissionError
            )
            with pytest.raises(
                expected_second_failure_type,
                match=(
                    "ENGVR_RUN_SCOPED_CLEANUP_FAILED.*synthetic second removal failure"
                    if os.name == "nt"
                    else "synthetic first removal failure"
                ),
            ):
                reliability.remove_exact_run_owned_process_tree(
                    second_failure_root,
                    expected_run_root=second_failure_root,
                    repo_root=REPO_ROOT,
                    evidence_root=retained_evidence,
                )
        assert second_failure_chmod_paths == (
            [second_failure_path.resolve(strict=False)] if os.name == "nt" else []
        )
        assert second_failure_path.read_bytes() == b"object\n"
        real_rmtree(second_failure_root)

        exact_owned_root = external_parent / "exact-owned-root"
        outside_root = external_parent / "outside-root"
        exact_owned_root.mkdir()
        outside_root.mkdir()
        outside_sentinel = outside_root / "owner.txt"
        outside_sentinel.write_text("preserve\n", encoding="utf-8")
        rejected_delete_calls = []
        rejected_chmod_calls = []
        with monkeypatch.context() as outside_patch:
            outside_patch.setattr(
                reliability.shutil,
                "rmtree",
                lambda *args, **kwargs: rejected_delete_calls.append((args, kwargs)),
            )
            outside_patch.setattr(
                reliability.os,
                "chmod",
                lambda *args, **kwargs: rejected_chmod_calls.append((args, kwargs)),
            )
            with pytest.raises(
                reliability.ValidationReliabilityError,
                match="exact current run-owned root",
            ):
                reliability.remove_exact_run_owned_process_tree(
                    outside_root,
                    expected_run_root=exact_owned_root,
                    repo_root=REPO_ROOT,
                    evidence_root=retained_evidence,
                )
        assert rejected_delete_calls == []
        assert rejected_chmod_calls == []
        assert outside_sentinel.read_text(encoding="utf-8") == "preserve\n"

        callback_root = external_parent / "callback-owned-root"
        callback_root.mkdir()
        callback_path = callback_root / "object"
        callback_path.write_bytes(b"object\n")
        callback_chmod_calls = []

        def invoke_outside_failure(_target, *, onexc):
            onexc(os.unlink, outside_sentinel, PermissionError("outside failure"))

        with monkeypatch.context() as callback_patch:
            callback_patch.setattr(
                reliability.shutil,
                "rmtree",
                invoke_outside_failure,
            )
            callback_patch.setattr(
                reliability.os,
                "chmod",
                lambda *args, **kwargs: callback_chmod_calls.append((args, kwargs)),
            )
            with pytest.raises(PermissionError, match="outside failure"):
                reliability.remove_exact_run_owned_process_tree(
                    callback_root,
                    expected_run_root=callback_root,
                    repo_root=REPO_ROOT,
                    evidence_root=retained_evidence,
                )
        assert callback_chmod_calls == []
        assert callback_path.read_bytes() == b"object\n"
        assert outside_sentinel.read_text(encoding="utf-8") == "preserve\n"

        junction_root = external_parent / "junction-owned-root"
        junction_root.mkdir()
        junction_delete_calls = []
        with monkeypatch.context() as junction_patch:
            junction_patch.setattr(
                reliability,
                "_path_is_junction",
                lambda path: Path(path) == junction_root,
            )
            junction_patch.setattr(
                reliability.shutil,
                "rmtree",
                lambda *args, **kwargs: junction_delete_calls.append((args, kwargs)),
            )
            with pytest.raises(
                reliability.ValidationReliabilityError,
                match="symlink or junction",
            ):
                reliability.remove_exact_run_owned_process_tree(
                    junction_root,
                    expected_run_root=junction_root,
                    repo_root=REPO_ROOT,
                    evidence_root=retained_evidence,
                )
        assert junction_delete_calls == []
        assert junction_root.is_dir()
        real_rmtree(junction_root)
        real_rmtree(callback_root)
        real_rmtree(exact_owned_root)
        real_rmtree(outside_root)

        failed_paths, _probe = reliability.resolve_validation_run_paths(
            REPO_ROOT,
            explicit_process_root=external_parent.resolve(),
            run_id="run_cleanup_failure_matrix",
        )
        with monkeypatch.context() as cleanup_patch:
            cleanup_patch.setattr(
                reliability.shutil,
                "rmtree",
                lambda _target, *, onexc: (_ for _ in ()).throw(
                    PermissionError("owned failure")
                ),
            )
            with pytest.raises(
                reliability.ValidationReliabilityError,
                match="ENGVR_RUN_SCOPED_CLEANUP_FAILED",
            ):
                reliability.cleanup_validation_run(failed_paths)
        real_rmtree(failed_paths.process_root)
        assert historical.is_dir()

        # Exercise the original main/finalizer unwind with no returned receipt.
        # The process port raises; no native process is created by these cases.
        for fault in ("direct", "group", "cancel", "report-failure", "preflight"):
            held_paths, held_probe = reliability.resolve_validation_run_paths(
                REPO_ROOT, explicit_process_root=external_parent.resolve(),
                run_id="run_pending_finalization_" + fault,
            )
            primary = reliability.ValidationReliabilityError(
                "ENGVR_PROCESS_TERMINATION_FAILED", "synthetic unresolved original process",
            )
            primary.owned_process = SimpleNamespace(pid=9012)
            raised = (ExceptionGroup("outer", [ExceptionGroup("inner", [primary])])
                      if fault == "group" else KeyboardInterrupt("original cancellation")
                      if fault == "cancel" else primary)
            publication_error = OSError("synthetic cleanup evidence unavailable")
            commands = ((sys.executable, "-c", "raise AssertionError('must not execute')"),)
            calls, cleanup_calls, published, allocations = [], [], [], []

            def resolve_held(*args, **kwargs):
                allocations.append((args, kwargs))
                return held_paths, held_probe

            def unresolved_call(*args, **kwargs):
                calls.append((args, kwargs))
                raise raised

            def dispatch_held(_argv):
                return runner.run_commands(commands, phase=runner.FAST_PREFLIGHT_PHASE)

            def record_finalization(path, payload):
                published.append((path.name, payload))
                if fault == "report-failure" and path.name == "cleanup.json":
                    raise publication_error

            def fail_preflight(_root):
                raise ValueError("definite failure before supervision")

            with monkeypatch.context() as pending_patch:
                pending_patch.setattr(runner, "_RUN_COMMANDS_SUPERVISION", None)
                pending_patch.setattr(runner, "_RUN_COMMANDS_CLEANUP_REPO_ROOT", None)
                pending_patch.setattr(runner, "_ACTIVE_SCAN_LAUNCH", None)
                pending_patch.setattr(runner, "_repo_root", lambda: REPO_ROOT)
                pending_patch.setattr(runner, "resolve_validation_run_paths", resolve_held)
                pending_patch.setattr(runner, "_projected_validation_relative_paths", lambda _phase: ())
                pending_patch.setattr(runner, "_main_impl", dispatch_held)
                pending_patch.setattr(runner, "_execute_supervised_command", unresolved_call)
                pending_patch.setattr(runner, "atomic_write_json", record_finalization)
                pending_patch.setattr(runner, "cleanup_validation_run",
                                      lambda paths: cleanup_calls.append(paths) or "PASS_REMOVED_EXACT_RUN_ROOT")
                if fault == "preflight":
                    pending_patch.setattr(runner, "_validation_text_integrity_preflight", fail_preflight)
                if fault in {"group", "cancel"}:
                    with pytest.raises(type(raised)) as caught:
                        runner._main_owned(["--phase", runner.FAST_PREFLIGHT_PHASE])
                    assert caught.value is raised
                elif fault == "report-failure":
                    with pytest.raises(BaseExceptionGroup) as caught:
                        runner._main_owned(["--phase", runner.FAST_PREFLIGHT_PHASE])
                    pending_errors = [caught.value]
                    leaves = []
                    while pending_errors:
                        error = pending_errors.pop()
                        if isinstance(error, BaseExceptionGroup):
                            pending_errors.extend(error.exceptions)
                        else:
                            leaves.append(error)
                    assert any(error is primary for error in leaves)
                    assert any(error is publication_error for error in leaves)
                else:
                    assert runner._main_owned(["--phase", runner.FAST_PREFLIGHT_PHASE]) == 1
                assert len(allocations) == 1
                if fault == "preflight":
                    assert calls == [] and cleanup_calls == [held_paths]
                    assert runner._RUN_COMMANDS_SUPERVISION is None
                else:
                    retained_state = runner._RUN_COMMANDS_SUPERVISION
                    assert retained_state["pending"] is True
                    assert retained_state["paths"] is held_paths
                    assert retained_state["receipt"] is None
                    assert retained_state["errors"][0] is raised
                    assert len(calls) == 1 and cleanup_calls == []
                    assert runner._LAST_COMMAND_RECEIPTS == ()
                    assert held_paths.process_root.is_dir()
                    assert published[0][0] == "cleanup.json"
                    assert published[0][1]["cleanup_state"] == "SKIPPED_PROCESS_TERMINATION_UNPROVEN"
                    assert runner._main_owned(["--phase", runner.ALL_PHASE]) == 1
                    assert len(allocations) == len(calls) == 1
                    assert runner._RUN_COMMANDS_SUPERVISION is retained_state
                    if fault == "direct":
                        other_paths, other_probe = reliability.resolve_validation_run_paths(
                            REPO_ROOT, explicit_process_root=external_parent.resolve(),
                            run_id="run_different_cannot_clear_pending",
                        )
                        final_result, cleanup, completion = runner._finalize_validation_run(
                            run_paths=other_paths, probe=other_probe, phase=runner.ALL_PHASE,
                            planned_count=0, expected_plan=(), receipts=(), result=0, text_state="PASS",
                            _supervision_state={"paths": other_paths, "phase": runner.ALL_PHASE,
                                                "pending": False, "receipt": None, "errors": []},
                        )
                        assert final_result == 1 and completion.final_state == "FAIL"
                        assert cleanup == "SKIPPED_PROCESS_TERMINATION_UNPROVEN"
                        assert cleanup_calls == [] and other_paths.process_root.is_dir()
                        assert runner._RUN_COMMANDS_SUPERVISION is retained_state
                        assert retained_state["pending"] is True
                        assert retained_state["errors"][0] is primary

        overwritten = reliability.CommandExecutionReceiptV1(
            schema_version=1, run_id=held_paths.run_id, phase=runner.FAST_PREFLIGHT_PHASE,
            command_index=1, argv=(sys.executable, "tools/original.py"), cwd=str(REPO_ROOT),
            pid=9023, platform="nt", start_time_utc="2026-08-24T00:00:00Z",
            end_time_utc="2026-08-24T00:00:01Z", elapsed_monotonic_seconds=1.0,
            native_exit_code=0, start_failure_class=None, timeout_seconds_or_null=None,
            timeout_state="NOT_CONFIGURED", termination_state="TASKKILL_T:128;TERMINAL:UNPROVEN",
            stdout_path=str(held_paths.evidence_root / "command-1.stdout.bin"),
            stderr_path=str(held_paths.evidence_root / "command-1.stderr.bin"),
            stdout_byte_count=0, stderr_byte_count=0, stdout_required_markers=(),
            stdout_marker_state="NOT_REQUIRED", stderr_was_nonempty=False,
            failure_class="ENGVR_ATOMIC_RECEIPT_WRITE_FAILED",
        )
        no_deletions, final_reports = [], []
        with monkeypatch.context() as overwritten_patch:
            overwritten_patch.setattr(runner, "_RUN_COMMANDS_SUPERVISION", None)
            overwritten_patch.setattr(runner, "cleanup_validation_run", lambda paths: no_deletions.append(paths))
            overwritten_patch.setattr(runner, "atomic_write_json", lambda path, value: final_reports.append((path.name, value)))
            result, cleanup, completion = runner._finalize_validation_run(
                run_paths=held_paths, probe=held_probe, phase=runner.FAST_PREFLIGHT_PHASE,
                planned_count=1, expected_plan=(), receipts=(overwritten,), result=0, text_state="PASS",
            )
            assert result == 1 and completion.final_state == "FAIL"
            assert cleanup == "SKIPPED_PROCESS_TERMINATION_UNPROVEN" and no_deletions == []
            assert final_reports[0][1]["cleanup_state"] == "SKIPPED_PROCESS_TERMINATION_UNPROVEN"
            retained_state = runner._RUN_COMMANDS_SUPERVISION
            assert retained_state["pending"] is True and retained_state["receipt"] is overwritten
            assert runner.run_commands(((sys.executable, "tools/never.py"),), run_paths=held_paths) == 1
            assert runner._RUN_COMMANDS_SUPERVISION is retained_state
            assert held_paths.process_root.is_dir() and no_deletions == []

        # Known process uncertainty must be retained before unrelated scan-plan
        # identity validation can raise. No native process or scan is started.
        identity_plan = reliability.build_command_evidence_plan(
            run_id=held_paths.run_id, phase=runner.FAST_PREFLIGHT_PHASE,
            commands=(overwritten.argv,), cwd=REPO_ROOT,
        )
        for supplied_state in (False, True):
            for mismatch in ("paths", "plan", "phase", "count"):
                scan = SimpleNamespace(
                    paths=held_paths, plan=identity_plan,
                    phase=runner.FAST_PREFLIGHT_PHASE, profiles=(),
                )
                if mismatch == "paths":
                    scan.paths = object()
                elif mismatch == "plan":
                    scan.plan = tuple(list(identity_plan))
                elif mismatch == "phase":
                    scan.phase = runner.ALL_PHASE
                count = 2 if mismatch == "count" else 1
                state = ({"paths": held_paths, "phase": runner.FAST_PREFLIGHT_PHASE,
                          "pending": False, "receipt": None, "errors": []}
                         if supplied_state else None)
                calls = []
                with monkeypatch.context() as early_failure_patch:
                    early_failure_patch.setattr(runner, "_RUN_COMMANDS_SUPERVISION", None)
                    early_failure_patch.setattr(runner, "cleanup_validation_run",
                                                lambda *a, **k: calls.append("cleanup"))
                    early_failure_patch.setattr(runner, "atomic_write_json",
                                                lambda *a, **k: calls.append("publication"))
                    early_failure_patch.setattr(runner, "_execute_supervised_command",
                                                lambda *a, **k: calls.append("dispatch"))
                    with pytest.raises(ValueError, match="finalizer lost original scan launch identity") as caught:
                        runner._finalize_validation_run(
                            run_paths=held_paths, probe=held_probe,
                            phase=runner.FAST_PREFLIGHT_PHASE, planned_count=count,
                            expected_plan=identity_plan, receipts=(overwritten,),
                            result=1, text_state="PASS", scan_launch=scan,
                            _supervision_state=state,
                        )
                    retained = runner._RUN_COMMANDS_SUPERVISION
                    assert retained is not None and retained["pending"] is True
                    assert state is None or retained is state
                    assert retained["paths"] is held_paths
                    assert retained["receipt"] is overwritten
                    assert retained["errors"] == [caught.value]
                    assert calls == []
                    assert runner.run_commands((overwritten.argv,), run_paths=held_paths) == 1
                    assert runner._RUN_COMMANDS_SUPERVISION is retained
                    assert calls == [] and held_paths.process_root.is_dir()

        # The same identity failure without process uncertainty does not invent
        # an unresolved child or bypass the original scan identity check.
        terminal = replace(overwritten, termination_state="NOT_REQUIRED", failure_class=None)
        calls = []
        with monkeypatch.context() as terminal_identity_patch:
            terminal_identity_patch.setattr(runner, "_RUN_COMMANDS_SUPERVISION", None)
            terminal_identity_patch.setattr(runner, "cleanup_validation_run",
                                            lambda *a, **k: calls.append("cleanup"))
            terminal_identity_patch.setattr(runner, "atomic_write_json",
                                            lambda *a, **k: calls.append("publication"))
            with pytest.raises(ValueError, match="finalizer lost original scan launch identity"):
                runner._finalize_validation_run(
                    run_paths=held_paths, probe=held_probe,
                    phase=runner.FAST_PREFLIGHT_PHASE, planned_count=1,
                    expected_plan=identity_plan, receipts=(terminal,), result=1,
                    text_state="PASS", scan_launch=SimpleNamespace(paths=object()),
                )
            assert runner._RUN_COMMANDS_SUPERVISION is None and calls == []


def test_st12h_runner_enforces_exact_timeouts_one_process_and_zero_retry(
    monkeypatch,
    tmp_path,
    capsys,
    _central_supervision_test_adapter,
) -> None:
    _exercise_failed_admission_plan_v1(tmp_path, monkeypatch, _central_supervision_test_adapter)
    _assert_path_projection_contract(monkeypatch, tmp_path)
    _assert_process_supervision_contract(monkeypatch, tmp_path)
    _assert_mirror_isolation_contract(monkeypatch, tmp_path)
    _assert_descriptor_ownership_and_drain_contract(monkeypatch, tmp_path)
    _assert_output_drain_terminality_contract(monkeypatch, tmp_path)
    _assert_exact_marker_line_contract(tmp_path)
    _assert_prestart_failure_custody_contract(monkeypatch, tmp_path)
    _assert_write_once_command_evidence_contract(monkeypatch, tmp_path)
    _assert_receipt_accounting_contract(tmp_path)
    _assert_complete_terminal_evidence_contract(monkeypatch, tmp_path)
    _assert_receipt_publication_failure_accounting(monkeypatch, tmp_path, capsys)
    _assert_exact_cleanup_contract(monkeypatch)


def test_st12h_pr152_guidance_follows_stable_outputs_before_one_full_route() -> None:
    assert runner.build_pre_validation_finalization_guidance() == [
        {
            "command_id": "pr152_currentize_after_generated_artifacts",
            "command": (
                ".\\.venv\\Scripts\\python.exe "
                "tools\\currentize_pr152_after_generated_artifacts.py"
            ),
            "when": (
                "after final generated artifacts settle and before validation gates"
            ),
            "ci_tracked_report_mutation_allowed": False,
        }
    ]
    manifest = runner.build_phase_manifest(
        Path(".tmp/st12h-full-route"),
        Path(".tmp/st12h-full-route-pytest"),
    )
    flattened = [
        list(command)
        for record in manifest
        for command in record["commands"]
    ]
    assert runner.build_phase_commands(
        runner.ALL_PHASE,
        Path(".tmp/st12h-full-route"),
        Path(".tmp/st12h-full-route-pytest"),
    ) == flattened
    assert runner._st12h_selected_command_failures(
        flattened,
        phase=runner.ALL_PHASE,
    ) == ()


def test_st12h_runner_fails_closed_for_missing_marker(monkeypatch, capsys) -> None:
    command = [
        sys.executable,
        "tools/validate_qku_computation_control_plane.py",
        "--domain",
        "h",
    ]

    def fake_run(argv, **kwargs):
        assert kwargs["timeout"] == 1200
        return subprocess.CompletedProcess(
            argv,
            0,
            stdout=(
                "QKU_COMPUTATION_CONTROL_PLANE_VALIDATED domain=h "
                "contract_checks=36 golden_vectors=0\n"
            ),
            stderr="",
        )

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    assert runner.run_commands([command], phase="deterministic-validators-c") == 1
    assert "ST12H_VALIDATION_TERMINAL_MARKER_MISSING" in capsys.readouterr().err


def test_st12h_runner_fails_closed_for_timeout(monkeypatch, capsys) -> None:
    command = [
        sys.executable,
        "tools/independent_validate_qku_computation_control_plane.py",
    ]

    def fake_run(argv, **kwargs):
        assert kwargs["timeout"] == 1800
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    assert runner.run_commands([command], phase="deterministic-validators-c") == 1
    assert "ST12H_VALIDATION_COMMAND_TIMEOUT" in capsys.readouterr().err


def test_st12h_runner_fails_closed_for_skipped_command_and_protected_change() -> None:
    commands = runner.build_phase_commands(
        runner.ALL_PHASE,
        Path(".tmp/st12h-skipped-command"),
        Path(".tmp/st12h-skipped-command-pytest"),
    )
    skipped = tuple(runner.build_st12h_validation_commands(sys.executable))[0]
    commands.remove(list(skipped))

    assert any(
        failure.startswith("ST12H_VALIDATION_COMMAND_SKIPPED_OR_DUPLICATED")
        for failure in runner._st12h_selected_command_failures(
            commands,
            phase=runner.ALL_PHASE,
        )
    )
    protected = (
        "src/qtt/stage1_prediction_markets/qku_computation_control_plane/"
        "accounting.py"
    )
    assert runner._st12h_execution_budget_failures(
        protected_predecessor_changes=(protected,)
    ) == (f"ST12H_READ_ONLY_PREDECESSOR_CHANGED: {protected}",)


def test_st12h_runner_fails_closed_for_budget_overrun_and_second_campaign(
    monkeypatch,
    capsys,
) -> None:
    failures = runner._st12h_execution_budget_failures(
        concurrent_validation_processes=2,
        automatic_full_campaign_retry_count=1,
        full_local_campaign_count=2,
        scratch_logical_bytes=runner.ST12H_MAX_SCRATCH_LOGICAL_BYTES + 1,
        scratch_allocated_bytes=runner.ST12H_MAX_SCRATCH_ALLOCATED_BYTES + 1,
        scratch_file_count=runner.ST12H_MAX_SCRATCH_FILES + 1,
        scratch_directory_count=runner.ST12H_MAX_SCRATCH_DIRECTORIES + 1,
    )
    assert set(failures) == {
        "ST12H_CONCURRENT_VALIDATION_PROCESS_BUDGET_EXCEEDED",
        "ST12H_AUTOMATIC_FULL_CAMPAIGN_RETRY_FORBIDDEN",
        "ST12H_FULL_LOCAL_CAMPAIGN_BUDGET_EXCEEDED",
        "ST12H_SCRATCH_LOGICAL_BYTE_BUDGET_EXCEEDED",
        "ST12H_SCRATCH_ALLOCATED_BYTE_BUDGET_EXCEEDED",
        "ST12H_SCRATCH_FILE_BUDGET_EXCEEDED",
        "ST12H_SCRATCH_DIRECTORY_BUDGET_EXCEEDED",
    }

    monkeypatch.setattr(
        runner,
        "_st12h_scratch_usage",
        lambda roots: (runner.ST12H_MAX_SCRATCH_LOGICAL_BYTES + 1, 0, 0, 0),
    )
    monkeypatch.setattr(
        runner.subprocess,
        "run",
        lambda command: subprocess.CompletedProcess(command, 0),
    )
    assert runner.run_commands([[sys.executable, "noop.py"]]) == 1
    assert "ST12H_SCRATCH_LOGICAL_BYTE_BUDGET_EXCEEDED" in capsys.readouterr().err


def _assert_repository_local_layout_contract() -> int:
    import dataclasses
    r = reliability
    checks=[]
    def check(name,condition):
     if not condition: raise AssertionError(name)
     checks.append(name)
    def rejects(name,fn):
     try: fn()
     except (r.ValidationReliabilityError,ValueError,OSError,RuntimeError): checks.append(name)
     else: raise AssertionError('accepted:'+name)
    def git(p,*a):
     clean_env={key:value for key,value in os.environ.items() if not key.upper().startswith('GIT_')}
     clean_env.update(GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_TERMINAL_PROMPT='0')
     c=subprocess.run(['git','-c','init.templateDir=','-c','commit.gpgSign=false','-C',str(p),*a],env=clean_env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True);return c.stdout
    with tempfile.TemporaryDirectory(prefix='qtt-local-layout-contract-') as t:
     root=Path(t)/'repo';root.mkdir()
     git(root,'init','-q');git(root,'config','user.name','Synthetic');git(root,'config','user.email','local@example.invalid')
     (root/'.gitignore').write_text('/.qtt/\n',encoding='utf-8');(root/'protected.txt').write_bytes(b'preserve')
     git(root,'add','.');git(root,'commit','-qm','synthetic')
     before=git(root,'status','--porcelain=v1');
     paths,probe=r.resolve_validation_run_paths(root,explicit_process_root=root/'.qtt/runs',run_id='run_local')
     check('local_flag_false',paths.process_root_is_external_to_repo is False)
     check('separate_evidence',paths.evidence_root.parent==root/'.qtt/evidence')
     check('probe_pass',probe.failure_operation is None)
     check('git_ignored',git(root,'status','--porcelain=v1')==before)
     r.write_run_provenance(paths,probe,phase='test',command_count=1,text_integrity_preflight_state='PASS')
     a=r.attest_inherited_validation_run(root,inherited_run_id=paths.run_id,inherited_evidence_root=paths.evidence_root,explicit_basetemp=paths.pytest_basetemp_root/'child')
     check('inherited_works',a.process_root==paths.process_root)
     from tools import run_validation_gates as runner_module
     from tools import validate_no_runtime_artifacts as scanner_module
     from src.qtt.core.testing.gate_result import hidden_zip_paths
     violations,skipped=scanner_module._validate_top_level_local_custody_boundary(root)
     check('scanner_guard_admission',not violations and '.qtt' in skipped)
     (root/'.qtt/local.zip').write_bytes(b'not a real archive; discovery test only')
     check('hidden_zip_local_exclusion',hidden_zip_paths(root)==[])
     outside=root/'visible.zip';outside.write_bytes(b'visible')
     check('ordinary_zip_still_visible',[str(x) for x in hidden_zip_paths(root)]==['visible.zip'])
     outside.unlink()
     cache=paths.validation_output_root/'NoRuntimeArtifactScanCache.json'
     runner_module._validate_no_runtime_scan_cache_path(root,cache)
     runner_module._validate_run_local_cache_path(root,paths.validation_output_root/'PR152BuildReportCache.json',runner_module.PR152_BUILD_REPORT_CACHE_ENV)
     check('both_actual_cache_owners_admit',True)
     rejects('wrong_local_cache_slot',lambda:runner_module._validate_no_runtime_scan_cache_path(root,root/'.qtt/cache/NoRuntimeArtifactScanCache.json'))
     runfile=paths.evidence_root/'run.json';original=runfile.read_bytes();payload=json.loads(original)
     payload['paths']['process_root_is_external_to_repo']=True
     runfile.write_text(json.dumps(payload),encoding='utf8')
     rejects('forged_inherited_external_flag',lambda:r.attest_inherited_validation_run(root,inherited_run_id=paths.run_id,inherited_evidence_root=paths.evidence_root,explicit_basetemp=paths.pytest_basetemp_root))
     runfile.write_bytes(original)
     rejects('false_external_flag',lambda:dataclasses.replace(paths,process_root_is_external_to_repo=True))
     rejects('wrong_cleanup_identity',lambda:r.remove_exact_run_owned_process_tree(paths.process_root,expected_run_root=paths.process_root/'child',repo_root=root,evidence_root=paths.evidence_root))
     for relative in ('.tmp','.qtt','.qtt/envs','.qtt/cache','.qtt/evidence','.qtt/runs/child'):
      rejects('bad_candidate_'+relative,lambda rel=relative:r.resolve_validation_run_paths(root,explicit_process_root=root/rel))
     for relative in ('.qtt','.qtt/runs','.qtt/evidence','protected.txt'):
      target=root/relative
      rejects('bad_cleanup_'+relative,lambda target=target:r.remove_exact_run_owned_process_tree(target,expected_run_root=target,repo_root=root,evidence_root=paths.evidence_root))
     rogue=root/'.qtt/runs/r260913000000_1_1';rogue.mkdir();(rogue/'preserve').write_bytes(b'keep')
     rejects('unowned_root',lambda:r.remove_exact_run_owned_process_tree(rogue,expected_run_root=rogue,repo_root=root,evidence_root=paths.evidence_root))
     link=paths.process_root/'escape'
     try:
         link.symlink_to(root,target_is_directory=True)
     except OSError as exc:
         if os.name != 'nt' or getattr(exc, 'winerror', None) != 1314:
             raise
         # A standard Windows account may lack symlink-creation privilege.
         # Do not alter privileges or mark native symlink execution as passed.
         # Exercise the same no-traversal boundary through a simulated junction.
         import warnings
         from unittest.mock import patch
         link.mkdir()
         original_junction = r._path_is_junction
         with patch.object(r, '_path_is_junction', lambda value: Path(value) == link or original_junction(value)):
             rejects('descendant_reparse_simulated_no_native_privilege',lambda:r.remove_exact_run_owned_process_tree(paths.process_root, expected_run_root=paths.process_root, repo_root=root, evidence_root=paths.evidence_root))
         link.rmdir()
         warnings.warn('Native Windows symlink creation unavailable (1314); junction rejection was simulated, not native-qualified.', RuntimeWarning)
     else:
         rejects('descendant_symlink',lambda:r.remove_exact_run_owned_process_tree(paths.process_root, expected_run_root=paths.process_root, repo_root=root, evidence_root=paths.evidence_root))
         link.unlink()
     check('source_preserved', (root/'protected.txt').read_bytes()==b'preserve')
     # Existing immutable failure cleanup receipt cannot be overwritten. Check direct
     # cleanup to demonstrate that correcting test-only link permits exact removal.
     hard=paths.process_root/'hard';os.link(root/'protected.txt',hard)
     rejects('descendant_hardlink',lambda:r.remove_exact_run_owned_process_tree(paths.process_root,expected_run_root=paths.process_root,repo_root=root,evidence_root=paths.evidence_root))
     hard.unlink()
     tracked=root/'.qtt/forced';tracked.write_bytes(b'keep');git(root,'add','-f','.qtt/forced')
     rejects('index_tracked_area',lambda:r.remove_exact_run_owned_process_tree(paths.process_root,expected_run_root=paths.process_root,repo_root=root,evidence_root=paths.evidence_root))
     git(root,'reset','-q','HEAD','--','.qtt/forced')
     check('direct_cleanup_succeeds',r.remove_exact_run_owned_process_tree(paths.process_root,expected_run_root=paths.process_root,repo_root=root,evidence_root=paths.evidence_root)==0)
     check('evidence_preserved',paths.evidence_root.exists())
     check('unowned_preserved',(rogue/'preserve').read_bytes()==b'keep')
     second,probe=r.resolve_validation_run_paths(root,explicit_process_root=root/'.qtt/runs',run_id='run_second')
     r.write_run_provenance(second,probe,phase='test',command_count=0)
     check('cleanup_success',r.cleanup_validation_run(second).startswith('PASS'))
     check('cleanup_receipt',json.loads((second.evidence_root/'cleanup.json').read_text(encoding='utf-8'))['parent_preserved'])
     from tools import independent_validate_qku_computation_control_plane as st12h
     tracked_paths = git(root, 'ls-files', '-z').decode('utf-8').rstrip('\0').split('\0')
     tracked_bytes = {name: (root / name).read_bytes() for name in tracked_paths}
     tracked_entries = git(root, 'ls-files', '--stage', '-z')
     fixture_head = git(root, 'rev-parse', 'HEAD')
     evidence_parent = root / '.qtt/evidence'
     evidence_before = set(evidence_parent.iterdir())
     st12h_probe_calls = []
     real_st12h_probe = r.probe_run_filesystem
     def observe_st12h_probe(process_root, *, deepest_projected_path):
         receipt = real_st12h_probe(process_root, deepest_projected_path=deepest_projected_path)
         st12h_probe_calls.append((process_root, deepest_projected_path, receipt))
         return receipt
     with pytest.MonkeyPatch.context() as patch:
         patch.setenv(r.PROCESS_ROOT_ENV, str(root / '.qtt/runs'))
         patch.delenv(r.RUN_ID_ENV, raising=False)
         patch.delenv(r.EVIDENCE_ROOT_ENV, raising=False)
         patch.setattr(r, 'probe_run_filesystem', observe_st12h_probe)
         stages = st12h.execute_st12h_backup_restore_portability_v1(root)
     check('st12h_twelve_executed_stages', len(stages) == 12 and tuple(stage.stage_id for stage in stages) == tuple(plan.plan_id for plan in st12h.ST12H_BACKUP_RESTORE_PLANS))
     check('st12h_real_restore_parity', all(stage.terminal_state == 'PASS_EXECUTED_STAGE' and stage.artifact_refs == st12h._ST12H_PUBLICATION_MEMBERS and stage.artifact_member_count == stage.restored_member_count == stage.byte_parity_count == 2 for stage in stages))
     check('st12h_no_effects_or_repository_copies', all(stage.no_effect_flags == st12h.NO_EFFECTS_V1 and stage.repository_copy_count == stage.copied_git_index_count == 0 for stage in stages))
     markers = {marker for stage in stages for marker in stage.validation_markers}
     check('st12h_scratch_confinement_marker', 'RESTORE_WRITES_CONFINED_TO_SCRATCH=true' in markers and 'REPOSITORY_WRITE_COUNT=0' not in markers)
     check('st12h_real_subprocess_and_unicode_paths', {'PATH_HAS_SPACES=true', 'PATH_HAS_NON_ASCII=true', 'DECLARED_RESTORE_COMMAND_COUNT=1', 'RESTORED_REPORT_VALIDATION=PASS'} <= markers)
     scratch_evidence = set(evidence_parent.iterdir()) - evidence_before
     check('st12h_one_retained_evidence_pair', len(scratch_evidence) == 1)
     scratch_evidence_root = scratch_evidence.pop()
     check('st12h_no_fabricated_campaign_acceptance', {path.name for path in scratch_evidence_root.iterdir()} == {'run.json', 'cleanup.json'})
     provenance = json.loads((scratch_evidence_root / 'run.json').read_bytes().decode('utf-8'))
     cleanup = json.loads((scratch_evidence_root / 'cleanup.json').read_bytes().decode('utf-8'))
     scratch = provenance['paths']
     check('st12h_scratch_provenance', provenance['phase'] == 'st12h-backup-restore-scratch' and provenance['command_count'] == 0 and provenance['text_integrity_preflight_state'] == 'NOT_APPLICABLE')
     check('st12h_truthful_local_placement', Path(scratch['repo_root']) == root.resolve() and scratch['process_root_is_external_to_repo'] is False and Path(scratch['process_root']).parent == root / '.qtt/runs' and Path(scratch['evidence_root']) == scratch_evidence_root)
     actual_probe = provenance['filesystem_probe']
     check('st12h_actual_filesystem_probe', scratch['filesystem_probe_state'] == 'PASS' and actual_probe['failure_operation'] is None and actual_probe['native_error_class'] is None and actual_probe['written_bytes'] > 0 and all(actual_probe[name] is True for name in ('created_directory', 'readback_equal', 'rename_equal', 'unlink_success', 'directory_cleanup_success')))
     check('st12h_exact_root_removed_evidence_preserved', cleanup['cleanup_state'] == 'PASS_REMOVED_EXACT_RUN_ROOT' and Path(cleanup['cleanup_target']) == Path(scratch['process_root']) and not Path(scratch['process_root']).exists() and not (Path(scratch['validation_output_root']) / 'w ü').exists() and scratch_evidence_root.is_dir())
     attacks = st12h.exercise_st12h_archive_safety_mutations_v1()
     check('st12h_all_archive_attacks_rejected', len(attacks) == 13 and all(value is True for value in attacks.values()))
     check('st12h_valid_archive_is_not_attack', st12h._archive_mutation_rejected(tuple((st12h.zipfile.ZipInfo(member), b'{}\n') for member in st12h._ST12H_PUBLICATION_MEMBERS)) is False)
     for relative in ('.tmp', '.qtt', '.qtt/envs', '.qtt/cache', '.qtt/evidence', '.qtt/runs/child'):
         evidence_before = set(evidence_parent.iterdir())
         with pytest.MonkeyPatch.context() as patch:
             patch.setenv(r.PROCESS_ROOT_ENV, str(root / relative))
             with pytest.raises(r.ValidationReliabilityError, match='ENGVR_SHORT_PROCESS_ROOT_UNAVAILABLE'):
                 st12h.execute_st12h_backup_restore_portability_v1(root)
         check('st12h_invalid_local_root_no_fallback_' + relative, set(evidence_parent.iterdir()) == evidence_before)
     real_cleanup = st12h.cleanup_validation_run
     for failure in ('stage', 'cleanup'):
         cleanup_calls = []
         def observed_cleanup(allocated):
             cleanup_calls.append(allocated)
             result = real_cleanup(allocated)
             if failure == 'cleanup':
                 # Raise after real exact-root removal so the injected exception
                 # tests propagation and no retry without leaving a test artifact.
                 raise RuntimeError('ST12H_TEST_CLEANUP_FAILURE')
             return result
         def fail_stage(extracted):
             assert extracted.is_relative_to(root / '.qtt/runs')
             assert all((extracted / member).is_file() for member in st12h._ST12H_PUBLICATION_MEMBERS)
             raise RuntimeError('ST12H_TEST_STAGE_FAILURE')
         with pytest.MonkeyPatch.context() as patch:
             patch.setenv(r.PROCESS_ROOT_ENV, str(root / '.qtt/runs'))
             patch.setattr(st12h, 'cleanup_validation_run', observed_cleanup)
             if failure == 'stage':
                 patch.setattr(st12h, 'validate_st12h_portable_directory_v1', fail_stage)
             with pytest.raises(RuntimeError, match='ST12H_TEST_' + failure.upper() + '_FAILURE'):
                 st12h.execute_st12h_backup_restore_portability_v1(root)
         check('st12h_' + failure + '_failure_cleanup_once', len(cleanup_calls) == 1)
         failed_paths = cleanup_calls[0]
         check('st12h_' + failure + '_failure_keeps_evidence', not failed_paths.process_root.exists() and (failed_paths.evidence_root / 'run.json').is_file() and (failed_paths.evidence_root / 'cleanup.json').is_file() and not (failed_paths.evidence_root / 'completion.json').exists())
     check('st12h_fixture_source_and_stage_entries_unchanged', {name: (root / name).read_bytes() for name in tracked_paths} == tracked_bytes and git(root, 'ls-files', '--stage', '-z') == tracked_entries and git(root, 'rev-parse', 'HEAD') == fixture_head and git(root, 'status', '--porcelain=v1') == before)
     check('st12h_no_canonical_generated_artifacts', not (root / 'docs').exists())
     # HEAD protection remains after staging deletion.
     git(root,'add','-f','.qtt/forced');git(root,'commit','-qm','synthetic tracked');git(root,'rm','--cached','-q','.qtt/forced')
     rejects('head_still_tracked',lambda:r.resolve_validation_run_paths(root,explicit_process_root=root/'.qtt/runs'))

     actual_destinations = tuple(
         Path(scratch['validation_output_root']) / 'w \u00fc' / directory / member
         for directory in ('x \u00e9', 'r \u00e9', 'c \u00e9')
         for member in st12h._ST12H_PUBLICATION_MEMBERS
     ) + tuple(
         Path(scratch['validation_output_root']) / 'w \u00fc' / name
         for name in ('publication archive.zip', 'stage journal.partial', 'stage journal.json')
     )
     # A passing fallback sentinel cannot qualify an omitted scratch destination.
     check('st12h_longest_actual_destination_probed', Path(actual_probe['write_path']) == max(actual_destinations, key=lambda path: (len(str(path)), str(path))))
     expected_target = max(actual_destinations, key=lambda path: (len(str(path).encode('utf-16-le')) // 2, len(str(path)), str(path)))
     check('st12h_one_real_probe_call', len(st12h_probe_calls) == 1)
     called_root, called_target, returned_probe = st12h_probe_calls[0]
     check('st12h_exact_argument_return_and_provenance', called_root == Path(scratch['process_root']) and str(called_target) == str(returned_probe.write_path) == actual_probe['write_path'] == scratch['deepest_projected_path'] == str(expected_target))
     check('st12h_probe_receipt_matches_provenance', all((str(value) if isinstance(value, Path) else value) == actual_probe[name] for name, value in dataclasses.asdict(returned_probe).items()))
     check('st12h_character_count_units_preserved', scratch['deepest_projected_path_text_length'] == len(str(expected_target)))
     check('st12h_real_probe_restored_after_observation', r.probe_run_filesystem is real_st12h_probe)

    return len(checks)


def _exercise_preflight_observation_v1(tmp_path, monkeypatch):
    """Finite synthetic acquisitions; independent expected bytes, never acceptance."""
    from tools import validation_reliability as owner
    from contextlib import contextmanager
    original_vectors = tuple(tuple(row) for row in runner.build_phase_commands(
        runner.FAST_PREFLIGHT_PHASE, tmp_path / "validation", tmp_path / "pytest"))
    assert len(original_vectors) == 8
    assert all(owner._preflight_vector_v1(row) for row in original_vectors)
    assert not any(owner._preflight_vector_v1((*row, "--extra")) for row in original_vectors)
    _exercise_preflight_startup_v1(tmp_path, monkeypatch)
    root = tmp_path / "preflight-observations"
    root.mkdir()
    path = root / "source.txt"
    expected = b"a\r\nb\rc\n"
    path.write_bytes(expected)
    argv = (sys.executable, "tools/validate_repair_pr_changed_file_scope.py", "--repo-root", ".")

    def session(**updates):
        limits = dict(attempts=20, bytes=200, entries=20, retained_bytes=200,
                      git_attempts=4, stdout_bytes=4096, stderr_bytes=4096, combined_output_bytes=8192)
        limits.update(updates)
        return owner._PreflightObservationV1(root=root, run_id="synthetic-preflight", occurrence=3,
            argv=argv, files={"source.txt": expected}, directories={".": (("source.txt", "file"),)},
            limits=limits, deadline_ns=owner.time.monotonic_ns() + 60_000_000_000)

    @contextmanager
    def activate(value):
        with owner._preflight_observation_v1(value, run_id=value.run_id,
                occurrence=3, argv=argv, root=root):
            yield

    native_read = owner.os.read
    value = session()
    with monkeypatch.context() as scoped, activate(value):
        scoped.setattr(owner.os, "read", lambda fd, n: native_read(fd, min(n, 2)))
        assert owner._preflight_read_text_v1(path) == "a\nb\nc\n"
        assert value.observed["bytes"] == len(expected)
        assert value.reserved["attempts"] == 1
        assert value.reserved["retained_bytes"] == value.observed["retained_bytes"] == len(expected)
        assert owner._preflight_directory_v1(root) == ((path, "file"),)
        assert value.observed["entries"] == 1
    for fault in ("early-eof", "overdelivery", "late-deadline", "growth", "close"):
        value = session(bytes=len(expected) + 1)
        seen = []
        original_close = owner.os.close
        with monkeypatch.context() as scoped:
            def deliver(fd, n):
                seen.append(n)
                if fault == "early-eof":
                    return b""
                if fault == "overdelivery":
                    return b"x" * (len(expected) + 5)
                block = native_read(fd, n)
                if fault == "late-deadline":
                    value.deadline_ns = owner.time.monotonic_ns()
                if fault == "growth" and len(seen) == 1:
                    return expected + b"!"
                return block
            scoped.setattr(owner.os, "read", deliver)
            if fault == "close":
                def failed_close(fd):
                    original_close(fd)
                    raise OSError("synthetic descriptor close failure")
                scoped.setattr(owner.os, "close", failed_close)
            with pytest.raises(owner.ValidationReliabilityError):
                with activate(value):
                    owner._preflight_read_bytes_v1(path)
            failure = value.failure
            assert failure is not None and seen
            assert value.observed["bytes"] == (0 if fault == "early-eof" else len(expected) + 5 if fault == "overdelivery" else len(expected) + 1 if fault == "growth" else len(expected))
            assert value.remaining["bytes"] == max(0, len(expected) + 1 - value.observed["bytes"])
            with pytest.raises(owner.ValidationReliabilityError) as again:
                value.check()
            assert again.value is failure
    # Capacity is reserved before any native read, but an attempt is still spent.
    value = session(bytes=len(expected))
    with monkeypatch.context() as scoped:
        scoped.setattr(owner.os, "read", lambda *a: pytest.fail("pre-effect denial performed a read"))
        with pytest.raises(owner.ValidationReliabilityError), activate(value):
            owner._preflight_read_bytes_v1(path)
    assert value.reserved["attempts"] == 1 and value.observed["bytes"] == 0
    # Every directory entry is charged, including an unmatched over-limit entry.
    value = session(entries=0)
    with pytest.raises(owner.ValidationReliabilityError), activate(value):
        owner._preflight_files_v1(root, "*.py")
    assert value.observed["entries"] == 1 and value.remaining["entries"] == 0
    for fault in ("denied", "iteration", "close", "duplicate"):
        value = session()
        real_scandir = owner.os.scandir
        class BrokenDirectory:
            def __init__(self):
                self.original = real_scandir(root)
            def __iter__(self):
                entry = next(self.original)
                yield entry
                if fault == "duplicate":
                    yield entry
                if fault == "iteration":
                    raise PermissionError("synthetic enumeration failure")
            def close(self):
                self.original.close()
                if fault == "close":
                    raise OSError("synthetic iterator close failure")
        with monkeypatch.context() as scoped:
            def broken_scan(_path):
                if fault == "denied":
                    raise PermissionError("synthetic directory denial")
                return BrokenDirectory()
            scoped.setattr(owner.os, "scandir", broken_scan)
            with pytest.raises(owner.ValidationReliabilityError), activate(value):
                owner._preflight_directory_v1(root)
        assert value.observed["entries"] == (0 if fault == "denied" else 2 if fault == "duplicate" else 1)
        assert value.failure is not None
    with pytest.raises(owner.ValidationReliabilityError):
        owner._preflight_directory_v1(root / "missing")
    assert owner._preflight_kind_v1(root / "missing", optional=True) is None
    # Successful status settlement follows the last real ancestor/stat call.
    for kind in ("absent-leaf", "absent-parent", "file", "directory"):
        for late in (False, True):
            value, clock, calls = session(), [100], []
            value.deadline_ns = 1000
            target = {"absent-leaf": root / "missing", "absent-parent": root / "missing-parent/leaf",
                      "file": path, "directory": root}[kind]
            native_chain, native_lstat = owner._preflight_chain_v1, Path.lstat
            with monkeypatch.context() as scoped:
                scoped.setattr(owner.time, "monotonic_ns", lambda: clock[0])
                def final_chain(*args, **kwargs):
                    result = native_chain(*args, **kwargs)
                    calls.append(result)
                    if late and len(calls) == 2:
                        clock[0] = 1000
                    return result
                def final_stat(p, *args, **kwargs):
                    result = native_lstat(p, *args, **kwargs)
                    if p == target:
                        calls.append(result)
                        if late and len(calls) == 2:
                            clock[0] = 1000
                    return result
                if kind.startswith("absent"):
                    scoped.setattr(owner, "_preflight_chain_v1", final_chain)
                else:
                    scoped.setattr(Path, "lstat", final_stat)
                if late:
                    with pytest.raises(owner.ValidationReliabilityError, match="deadline"), activate(value):
                        owner._preflight_kind_v1(target, optional=True)
                else:
                    with activate(value):
                        assert owner._preflight_kind_v1(target, optional=True) == (
                            None if kind.startswith("absent") else kind)
            assert len(calls) == 2 and value.observed["attempts"] == 1
            assert (value.failure is not None) is late
    value = session()
    with monkeypatch.context() as scoped:
        native_lstat = Path.lstat
        denied_path = root / "unreadable-optional"
        def denied_stat(p, *args, **kwargs):
            if p == denied_path:
                raise PermissionError("optional status is unreadable")
            return native_lstat(p, *args, **kwargs)
        scoped.setattr(Path, "lstat", denied_stat)
        with pytest.raises(owner.ValidationReliabilityError, match="optional status is unreadable"), activate(value):
            owner._preflight_kind_v1(denied_path, optional=True)
    assert value.observed["attempts"] == 1 and value.failure is not None
    # Parsing follows complete acquisition and keeps its independent semantics.
    value = session()
    with activate(value):
        with pytest.raises(json.JSONDecodeError):
            json.loads(owner._preflight_read_text_v1(path))
        assert value.failure is None and value.observed["bytes"] == len(expected)
    parent = {"PythonPath": "untrusted", "PYTHONHOME": "untrusted", "SystemRoot": "C:\\Windows", "OMP_NUM_THREADS": "1"}
    original = dict(parent)
    projected, projection = owner._preflight_environment_v1(argv, parent, cache_root=root / "cache")
    assert parent == original and projected == {"SystemRoot": "C:\\Windows", "OMP_NUM_THREADS": "1",
        "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1", "PYTHONPYCACHEPREFIX": str(root / "cache")}
    assert projection["registered_argv"] == argv
    for mutation in ({**projected, "EXTRA": "1"}, {**projected, "PYTHONNOUSERSITE": "0"}):
        assert mutation != projected
        with pytest.raises(owner.ValidationReliabilityError):
            owner._preflight_launch_guard_v1(argv, mutation, expected_argv=argv, expected_environment=projected)
    with pytest.raises(ValueError):
        owner._preflight_environment_v1(argv, {"PATH": "a", "Path": "b"}, cache_root=root / "not-created")
    assert not (root / "not-created").exists()
    assert owner._preflight_pth_v1(b"\xef\xbb\xbf# comment\n\n.  \n", site_root=root, bound_roots=(root,)) == (root,)
    for raw in (b"import os\n", b"import\tos\n", b"../outside\n", b"\xff\n", b"path\0\n"):
        with pytest.raises((ValueError, UnicodeError)):
            owner._preflight_pth_v1(raw, site_root=root, bound_roots=(root,))
    with pytest.raises(ValueError, match="binding unavailable"):
        owner._preflight_startup_v1(argv, parent, binding=None, cache_root=root / "no-start")
    with monkeypatch.context() as scoped:
        scoped.setenv(owner.RUN_ID_ENV, "selected-without-binding")
        scoped.setattr(owner.sys, "argv", [argv[1], *argv[2:]])
        with pytest.raises(owner.ValidationReliabilityError, match="no original observation binding"):
            owner._preflight_read_bytes_v1(path)
    # Two tiny real native children exercise the existing finite pipe owner.
    for index, limit in enumerate((32, 4), 1):
        observation = {}
        program = "import os; os.write(1,b'abcdefgh'); os.write(2,b'err')"
        if limit == 4:
            # Keep the offending child alive for the original tree owner to
            # prove termination; a raced dead PID is deliberately not proof.
            program += "; import time; time.sleep(30)"
        receipt = owner.supervise_command(
            (sys.executable, "-I", "-B", "-c", program),
            cwd=root, run_id="synthetic-preflight-stream", phase="engineering",
            command_index=index, evidence_root=root / "streams", environment=dict(os.environ),
            timeout_seconds=30, mirror_stdout=False, mirror_stderr=False,
            output_limits={"stdout_bytes": limit, "stderr_bytes": 8, "combined_output_bytes": limit + 8},
            output_observation=observation)
        assert not owner._command_requires_process_retention_v1(receipt)
        assert receipt.output_observation == observation
        assert Path(receipt.stdout_path).read_bytes() == (b"abcdefgh" if limit == 32 else b"abcd")
        assert observation["stdout"]["retained_byte_count"] == min(limit, 8)
        if limit == 32:
            assert receipt.native_exit_code == 0 and receipt.failure_class is None
            assert observation["stdout"]["complete"] and observation["stderr"]["complete"]
        else:
            assert receipt.failure_class is not None and observation["stdout"]["overflow"]
            assert not observation["stdout"]["complete"]
            assert observation["stdout"]["drained_byte_count"] >= 5
    with monkeypatch.context() as scoped:
        scoped.setattr(owner.subprocess, "Popen", lambda *a, **k: pytest.fail("mismatched startup launched a child"))
        altered = {**projected, "PYTHONPATH": "injected"}
        assert altered != projected
        receipt = owner.supervise_command(argv, cwd=root, run_id="synthetic-launch-guard",
            phase="engineering", command_index=3, evidence_root=root / "streams",
            environment=altered, preflight_launch=(argv, projected), mirror_stdout=False, mirror_stderr=False)
        assert receipt.pid is None and receipt.native_exit_code is None
        assert receipt.failure_class == "ENGVR_PROCESS_START_FAILED"
    with monkeypatch.context() as scoped:
        def partial_write(stream, block):
            stream.write(block[:1])
            raise OSError("synthetic partial evidence write")
        scoped.setattr(owner, "_write_evidence_chunk", partial_write)
        observation = {}
        receipt = owner.supervise_command(
            (sys.executable, "-I", "-B", "-c", "import os,time; os.write(1,b'abcdefgh'); os.write(2,b'err'); time.sleep(30)"),
            cwd=root, run_id="synthetic-partial-evidence", phase="engineering", command_index=4,
            evidence_root=root / "streams", environment=dict(os.environ), timeout_seconds=30,
            output_limits={"stdout_bytes": 32, "stderr_bytes": 8, "combined_output_bytes": 40},
            output_observation=observation, mirror_stdout=False, mirror_stderr=False)
        assert not owner._command_requires_process_retention_v1(receipt)
        assert receipt.failure_class is not None
        assert sum(observation[s]["retained_byte_count"] for s in ("stdout", "stderr")) == 1
        assert not any(observation[s]["complete"] for s in ("stdout", "stderr"))
        assert any("synthetic partial evidence write" in e for s in ("stdout", "stderr") for e in observation[s]["errors"])


def _exercise_preflight_startup_v1(tmp_path, monkeypatch):
    """Known literal startup data, separated namespaces, and the actual readers."""
    import site
    import sysconfig
    import struct
    from contextlib import contextmanager
    from pathlib import PurePosixPath, PureWindowsPath
    from types import SimpleNamespace
    from tools import validation_reliability as owner

    original_vectors = tuple(tuple(row) for row in runner.build_phase_commands(
        runner.FAST_PREFLIGHT_PHASE, tmp_path / "validation", tmp_path / "pytest"))
    assert len(original_vectors) == 8
    executable_raw = b"synthetic executable\n"
    module_raw = b"# stdlib fixture\n"
    pth_raw = b"# no executable path code\n"
    script_raw = b"# synthetic source location; never executed\n"

    def fixture(name, occurrence=3, *, colocated=False, owned=False):
        parent = tmp_path / ("startup-" + name)
        repo, run = parent / "repo", parent / "run"
        runtime = repo if colocated else parent / "runtime"
        lib, site_root = runtime / "Lib", runtime / "Lib/site-packages"
        for directory in (repo / "tools", runtime / "bin", site_root, run):
            directory.mkdir(parents=True, exist_ok=True)
        executable, module, pth = runtime / "bin/python.exe", lib / "module.py", site_root / "no_import.pth"
        for path, raw in ((executable, executable_raw), (module, module_raw), (pth, pth_raw)):
            path.write_bytes(raw)
        vectors = tuple((str(executable), *row[1:]) for row in original_vectors)
        argv = vectors[occurrence - 1]
        script_relative = Path(argv[1]).as_posix()
        (repo / script_relative).write_bytes(script_raw)
        assert script_relative.startswith("tools/") and owner._preflight_vector_v1(argv)
        if not colocated:
            assert not executable.is_relative_to(repo)
        assert not run.is_relative_to(repo) and not run.is_relative_to(runtime)
        roots = tuple(str(p) for p in (repo, repo / "tools", executable.parent, lib, site_root))
        config = (str(executable.parent / "pyvenv.cfg"), str(runtime / "pyvenv.cfg"),
                  str(executable.with_suffix("._pth")),
                  str(executable.parent / f"python{sys.version_info.major}{sys.version_info.minor}._pth"))
        customizers = tuple(str(Path(root) / (stem + suffix)) for root in roots
            for stem in ("sitecustomize", "usercustomize") for suffix in (".py", ".pyc", ".pyd", ".so", ""))
        basis = dict(files={str(executable): executable_raw, str(module): module_raw, str(pth): pth_raw},
            directories={str(lib): (("module.py", "file"), ("site-packages", "directory")),
                         str(site_root): (("no_import.pth", "file"),)}, absent=config + customizers)
        catalog_entries = 3 + 2 + len(config) + len(customizers) + 3
        # The existing finite acquisition allowance plus the known literal
        # catalog index demand. Raw lengths are not a native memory grant.
        limits = dict(attempts=200, bytes=4096, entries=catalog_entries + 20, retained_bytes=4096,
            git_attempts=0, stdout_bytes=0, stderr_bytes=0, combined_output_bytes=0)
        paths = None
        if owned:
            paths, probe = owner.resolve_validation_run_paths(repo, explicit_process_root=run)
            assert probe.failure_operation is None and probe.readback_equal and probe.directory_cleanup_success
            assert paths.repo_root == repo and paths.process_root.parent == run
        observation = owner._PreflightObservationV1(root=repo,
            run_id=paths.run_id if paths else "synthetic-startup", occurrence=occurrence,
            argv=argv, files={script_relative: script_raw}, directories={"tools": ((Path(argv[1]).name, "file"),)},
            limits=limits, deadline_ns=owner.time.monotonic_ns() + 60_000_000_000)
        env = {"SystemRoot": "C:\\Windows"}
        binding = dict(observation=observation, version=tuple(sys.version_info[:3]),
            abi=(sys.implementation.cache_tag, sysconfig.get_config_var("SOABI"), struct.calcsize("P") * 8,
                 sysconfig.get_config_var("Py_GIL_DISABLED"), getattr(sys, "abiflags", "")),
            stdlib_roots=(str(lib),), site_roots=(str(site_root),), loader_environment=dict(env),
            config_paths=config, customizer_paths=customizers, startup_basis=basis)
        return SimpleNamespace(repo=repo, run=run, runtime=runtime, executable=executable,
            module=module, pth=pth, lib=lib, site_root=site_root, vectors=vectors, argv=argv, script_relative=script_relative,
            basis=basis, binding=binding, observation=observation, env=env, paths=paths,
            catalog_entries=catalog_entries, limits=limits, cache=run / "cache")

    @contextmanager
    def installation(case):
        with monkeypatch.context() as scoped:
            scoped.chdir(case.repo)
            scoped.setattr(owner.sys, "executable", str(case.executable))
            scoped.setattr(sysconfig, "get_path", lambda key: str(case.lib))
            scoped.setattr(site, "getsitepackages", lambda: [str(case.site_root)])
            # No startup check may execute the literal data file (or a probe).
            scoped.setattr(owner.subprocess, "Popen", lambda *a, **k: pytest.fail("startup launched a process"))
            yield scoped

    @contextmanager
    def active(case):
        value = case.observation
        with owner._preflight_observation_v1(value, run_id=value.run_id,
                occurrence=value.occurrence, argv=value.argv, root=case.repo):
            yield value

    def settled(case):
        assert case.observation._startup_catalog is None
        assert owner._PREFLIGHT_OBSERVATION_V1.get() is None
        assert case.observation.root == case.repo

    def candidate(case):
        plan = runner._prepare_execution_plan(case.vectors)
        custody = runner._ValidationCandidateCustodyV1(repo_root=case.repo, plan=plan,
            observe_paths=lambda: (case.script_relative,), check_exclusive=lambda: None,
            index_path=None, effects_by_occurrence={i: () for i in range(1, 9)}, ignored_paths=(),
            entry_limit=100, snapshot_byte_limit=1_000_000, read_byte_limit=100_000_000,
            deadline_ns=runner.time.monotonic_ns() + 60_000_000_000,
            operation_checks={i: (lambda **kw: None) for i in range(1, 9)},
            preflight_bindings={case.observation.occurrence: case.binding})
        return custody, plan

    # Every original vector gets a fresh observation and actual run-owned cache.
    # Keep the older colocated positive as additional, separately scoped coverage.
    for occurrence, colocated in (*((i, False) for i in range(1, 9)), (3, True)):
        case = fixture(f"positive-{occurrence}-{colocated}", occurrence, colocated=colocated, owned=True)
        with installation(case) as scoped:
            custody, plan = candidate(case)
            original_environment = owner._preflight_environment_v1
            def project(*args, **kwargs):
                assert case.observation._startup_catalog is None
                assert owner._PREFLIGHT_OBSERVATION_V1.get() is None
                assert kwargs["cache_root"] == case.paths.process_root / f"preflight-cache-{occurrence}"
                return original_environment(*args, **kwargs)
            scoped.setattr(owner, "_preflight_environment_v1", project)
            projected, receipt = custody.prepare_preflight(occurrence, plan[occurrence - 1],
                environment=case.env, run_paths=case.paths)
            assert projected["PYTHONNOUSERSITE"] == "1" and receipt["registered_argv"] == case.argv
            assert Path(projected["PYTHONPYCACHEPREFIX"]).is_dir()
            assert not Path(projected["PYTHONPYCACHEPREFIX"]).is_relative_to(case.repo)
            expected_read = len(executable_raw) + len(module_raw) + 2 * len(pth_raw)
            retained_basis = len(executable_raw) + len(module_raw) + len(pth_raw)
            assert expected_read > 0 and case.observation.observed["bytes"] == expected_read
            assert case.observation.observed["entries"] == 4  # nested site visits remain separate
            assert case.observation.reserved["entries"] == case.catalog_entries
            assert case.observation.retained_entries == case.catalog_entries + 4
            assert case.observation.observed["retained_bytes"] == retained_basis + expected_read
            assert case.observation.reserved["retained_bytes"] == retained_basis + expected_read
            assert case.observation.observed["attempts"] == 1 + 4 + 3 + len(case.basis["absent"])
            assert case.observation.remaining["bytes"] == 4096 - expected_read
        settled(case)

    # Preserve the original trust denials and add actual separated-location faults.
    failures = {
        "hook": "executable startup", "config": "._pth", "customizer": "customizer",
        "loader": "loader injection", "version": "version/ABI", "abi": "version/ABI",
        "missing-executable": r"python\.exe", "changed-executable": "expected bytes differ",
        "missing-directory": "undeclared startup directory", "missing-file": "undeclared startup file",
        "declared-present-missing": "startup status differs", "declared-absent-present": "startup status differs",
        "roster": "directory basis differs", "close": "startup close failure",
    }
    for fault, message in failures.items():
        case = fixture(fault)
        basis = case.basis
        if fault == "hook":
            case.pth.write_bytes(b"import os\n")
            basis["files"][str(case.pth)] = b"import os\n"
        elif fault in ("config", "customizer"):
            path = case.executable.with_suffix("._pth") if fault == "config" else case.lib / "sitecustomize.py"
            raw = b"import site\n" if fault == "config" else b"raise RuntimeError('must not execute')\n"
            path.write_bytes(raw)
            basis["files"][str(path)] = raw
            basis["absent"] = tuple(p for p in basis["absent"] if p != str(path))
            if fault == "customizer":
                basis["directories"][str(case.lib)] += ((path.name, "file"),)
        elif fault == "loader":
            case.env["LD_PRELOAD"] = "synthetic injection"
            case.binding["loader_environment"] = dict(case.env)
        elif fault == "version":
            case.binding["version"] = (0, 0, 0)
        elif fault == "abi":
            abi = case.binding["abi"]
            case.binding["abi"] = (abi[0], "wrong-abi", *abi[2:])
        elif fault == "missing-executable":
            case.executable.unlink()
        elif fault == "changed-executable":
            case.executable.write_bytes(b"Synthetic executable\n")
            assert case.executable.read_bytes() != executable_raw
        elif fault == "missing-directory":
            del basis["directories"][str(case.site_root)]
        elif fault == "missing-file":
            del basis["files"][str(case.pth)]
        elif fault == "declared-present-missing":
            path = basis["absent"][0]
            basis["absent"] = basis["absent"][1:]
            basis["files"][path] = b"missing but declared present\n"
        elif fault == "declared-absent-present":
            Path(basis["absent"][0]).write_bytes(b"unexpected\n")
        elif fault == "roster":
            (case.site_root / "undeclared.py").write_bytes(b"# not in the roster\n")
        with installation(case) as scoped:
            if fault == "close":
                native_close = owner.os.close
                def close(fd):
                    native_close(fd)
                    raise OSError("startup close failure")
                scoped.setattr(owner.os, "close", close)
            expected_error = ValueError if fault in ("loader", "version", "abi") else owner.ValidationReliabilityError
            with pytest.raises(expected_error, match=message) as failure:
                owner._preflight_startup_v1(case.argv, case.env, binding=case.binding, cache_root=case.cache)
            if fault == "missing-executable":
                assert isinstance(failure.value.__cause__, FileNotFoundError)
        settled(case)
        assert not case.cache.exists()
        if fault not in ("loader", "version", "abi"):
            assert case.observation.failure is not None
            assert case.observation.reserved["entries"] > 0
            assert case.observation.remaining["bytes"] == 4096 - case.observation.observed["bytes"]

    # Real declared file/directory/absence statuses and unchanged byte content.
    case = fixture("exact-status")
    with active(case), owner._preflight_startup_access_v1(case.observation, case.basis):
        assert owner._preflight_kind_v1(case.executable, optional=True) == "file"
        assert owner._preflight_kind_v1(case.lib, optional=True) == "directory"
        assert owner._preflight_kind_v1(Path(case.basis["absent"][0]), optional=True) is None
        assert owner._preflight_read_bytes_v1(case.executable) == executable_raw
    settled(case)
    assert case.observation.observed["attempts"] == 5
    assert case.observation.observed["bytes"] == len(executable_raw)

    # Exact role membership, no evidence exception, no reentry, immutable basis.
    for fault in ("sibling", "repository-role", "repository-only", "evidence", "reentry", "catalog-mutation", "wrong-observation"):
        case = fixture("role-" + fault)
        value = case.observation
        with pytest.raises(owner.ValidationReliabilityError), active(case):
            if fault == "repository-role":
                owner._preflight_read_bytes_v1(case.executable)
            else:
                with owner._preflight_startup_access_v1(value, case.basis):
                    if fault == "sibling":
                        owner._preflight_kind_v1(case.executable.parent / "unlisted.py", optional=True)
                    elif fault == "repository-only":
                        owner._preflight_read_bytes_v1(case.repo / case.argv[1])
                    elif fault == "evidence":
                        value.git_receipts.append(SimpleNamespace(stdout_path=str(case.executable), stderr_path=str(case.module)))
                        owner._preflight_read_bytes_v1(case.executable, evidence=True)
                    elif fault == "reentry":
                        with owner._preflight_startup_access_v1(value, case.basis):
                            pytest.fail("reentered startup role")
                    elif fault == "wrong-observation":
                        other = fixture("other-observation").observation
                        with owner._preflight_startup_access_v1(other, case.basis):
                            pytest.fail("wrong observation entered")
                    else:
                        immutable = value._startup_catalog
                        assert immutable[0][str(case.executable)] is executable_raw
                        with pytest.raises(TypeError):
                            immutable[0][str(case.executable)] = b"changed"
                        case.basis["files"][str(case.executable)] = b"wrong"
                        assert owner._preflight_read_bytes_v1(case.executable) == executable_raw
                        case.basis["files"][str(case.executable.parent / "later.py")] = b"new"
                        owner._preflight_read_bytes_v1(case.executable.parent / "later.py")
        settled(case)
        assert value.failure is not None
        assert value.remaining["bytes"] == 4096 - value.observed["bytes"]
        assert value.observed["bytes"] == (len(executable_raw) if fault == "catalog-mutation" else 0)

    # Exact types/shape, aliases, cross-kind contradictions and finite indexing.
    mutations = (
        lambda b, c: b.update(absent=list(b["absent"])),
        lambda b, c: b["files"].update({str(c.executable): bytearray(executable_raw)}),
        lambda b, c: b["files"].update({str(c.executable).swapcase(): executable_raw}),
        lambda b, c: b.update(absent=b["absent"] + (b["absent"][0],)),
        lambda b, c: b.update(absent=b["absent"] + (str(c.executable),)),
        lambda b, c: b["files"].update({str(c.runtime) + "/../runtime/alias": b""}),
        lambda b, c: b["files"].update({"relative/path": b""}),
        lambda b, c: b["files"].update({str(c.executable) + "\0": b""}),
        lambda b, c: b["files"].update({c.executable: b""}),
        lambda b, c: b["directories"].update({str(c.lib): (("MODULE.py", "file"), ("module.py", "file"))}),
        lambda b, c: b["directories"].update({str(c.lib): (("../escape", "file"),)}),
        lambda b, c: b["directories"].update({str(c.lib): (("module.py", True),)}),
        lambda b, c: b["directories"].update({str(c.lib): (("module.py", "directory"),)}),
        lambda b, c: b["directories"].update({str(c.lib): ()}),
        lambda b, c: b["files"].update({str(c.repo / c.script_relative): b"contradicts repository bytes"}),
        lambda b, c: b["directories"].update({str(c.lib): (("oversized", "file"),) * (c.limits["entries"] + 1)}),
    )
    for index, mutate in enumerate(mutations):
        case = fixture(f"catalog-{index}")
        mutate(case.basis, case)
        with pytest.raises(owner.ValidationReliabilityError), active(case):
            with owner._preflight_startup_access_v1(case.observation, case.basis):
                pytest.fail("invalid catalog was installed")
        settled(case)
        assert case.observation.observed["bytes"] == 0 and case.observation.failure is not None

    # Pure lexical checks cover both layouts; only the actual platform fixture
    # above establishes physical I/O observations.
    for path_type, good, bad in (
        (PurePosixPath, "/runtime/bin/python", ("relative", "/runtime/../python", "/runtime/./python", "/runtime//python", "/runtime/python\x7f")),
        (PureWindowsPath, r"C:\runtime\bin\python.exe", (r"C:python.exe", r"\runtime\python.exe", r"C:\runtime\..\python.exe", "C:/runtime/python.exe", r"C:\runtime\python.exe.", r"C:\runtime\NUL")),
    ):
        assert owner._preflight_startup_path_v1(good, path_type) == good
        for operand in bad:
            with pytest.raises(ValueError):
                owner._preflight_startup_path_v1(operand, path_type)

    # Candidate association is checked before the startup owner can acquire I/O.
    for field in ("root", "run_id", "occurrence"):
        case = fixture("candidate-" + field, owned=True)
        with installation(case):
            custody, plan = candidate(case)
            before = getattr(case.observation, field)
            changed = case.runtime if field == "root" else "different-run" if field == "run_id" else 4
            assert changed != before
            setattr(case.observation, field, changed)
            try:
                with pytest.raises(RuntimeError, match="STARTUP_ASSOCIATION"):
                    custody.prepare_preflight(3, plan[2], environment=case.env, run_paths=case.paths)
            finally:
                setattr(case.observation, field, before)
        settled(case)
        assert case.observation.observed["attempts"] == 0
        assert not (case.paths.process_root / "preflight-cache-3").exists()

    # Both absence paths retain real no-follow observations. The final native
    # ancestor check advances a deterministic clock only in the negative case.
    for parent_missing in (False, True):
        for late in (False, True):
            case = fixture(f"absence-{parent_missing}-{late}")
            path = case.runtime / ("missing-parent/optional.py" if parent_missing else "optional.py")
            case.basis["absent"] += (str(path),)
            value, clock, calls = case.observation, [100], []
            value.deadline_ns = 1000
            native_chain = owner._preflight_chain_v1
            with monkeypatch.context() as scoped:
                scoped.setattr(owner.time, "monotonic_ns", lambda: clock[0])
                def chain(*args, **kwargs):
                    result = native_chain(*args, **kwargs)
                    calls.append(result)
                    if late and len(calls) == 2:
                        clock[0] = 1000
                    return result
                scoped.setattr(owner, "_preflight_chain_v1", chain)
                if late:
                    with pytest.raises(owner.ValidationReliabilityError, match="deadline"), active(case):
                        with owner._preflight_startup_access_v1(value, case.basis):
                            owner._preflight_kind_v1(path, optional=True)
                else:
                    with active(case), owner._preflight_startup_access_v1(value, case.basis):
                        assert owner._preflight_kind_v1(path, optional=True) is None
            settled(case)
            assert len(calls) == 2 and value.observed["attempts"] == 2
            assert value.reserved["entries"] == case.catalog_entries + 1
            assert (value.failure is not None) is late

    for fault in ("permission", "already-failed", "expired", "process", "thread"):
        case = fixture("entry-" + fault)
        value = case.observation
        with monkeypatch.context() as scoped:
            if fault == "permission":
                native_lstat = Path.lstat
                target = Path(case.basis["absent"][0])
                def lstat(path, *args, **kwargs):
                    if path == target:
                        raise PermissionError("startup status denied")
                    return native_lstat(path, *args, **kwargs)
                scoped.setattr(Path, "lstat", lstat)
                with pytest.raises(owner.ValidationReliabilityError, match="startup status denied"), active(case):
                    with owner._preflight_startup_access_v1(value, case.basis):
                        owner._preflight_kind_v1(target, optional=True)
            else:
                with pytest.raises(owner.ValidationReliabilityError), active(case):
                    if fault == "already-failed":
                        with pytest.raises(owner.ValidationReliabilityError):
                            value.fail("original startup failure")
                    elif fault == "expired":
                        value.deadline_ns = owner.time.monotonic_ns()
                    elif fault == "process":
                        value.pid = -1
                    else:
                        value.thread = -1
                    with owner._preflight_startup_access_v1(value, case.basis):
                        pytest.fail("invalid observation entered startup access")
        settled(case)
        assert value.failure is not None and value.observed["bytes"] == 0
def _exercise_preflight_candidate_debits_v1(tmp_path, monkeypatch):
    plan = runner._prepare_execution_plan([["python", "tools/example_gate.py"]])
    root = tmp_path / "candidate-debits"
    root.mkdir()
    source = root / "source.py"
    source.write_bytes(b"source\n")
    for bad in (True, 1.0, type("IntegerAlias", (int,), {})(1)):
        for field in ("effects_by_occurrence", "operation_checks"):
            kwargs = dict(repo_root=root, plan=plan, observe_paths=lambda: pytest.fail("aliased input performed I/O"),
                check_exclusive=lambda: None, index_path=None, effects_by_occurrence={1: ()}, ignored_paths=(),
                entry_limit=10, snapshot_byte_limit=100, read_byte_limit=100, deadline_ns=runner.time.monotonic_ns() + 60_000_000_000,
                operation_checks={1: lambda **kw: None})
            kwargs[field] = {bad: () if field == "effects_by_occurrence" else lambda **kw: None}
            assert type(next(iter(kwargs[field]))) is not int
            with pytest.raises(ValueError):
                runner._ValidationCandidateCustodyV1(**kwargs)
    custody = _synthetic_candidate_custody_v1(root, plan, observed_paths=lambda: ("source.py",), effects=())
    baseline = custody.observed_read_bytes
    custody.remaining_read_bytes = 8
    with monkeypatch.context() as scoped:
        scoped.setattr(runner.os, "read", lambda fd, n: b"x" * 13)
        with pytest.raises(RuntimeError, match="READ_BUDGET"):
            custody._read(source)
    assert custody.observed_read_bytes == baseline + 13 and custody.remaining_read_bytes == 0
    failure = custody.failure
    assert custody.state == "CLEANUP_REJECTED"
    with pytest.raises(RuntimeError, match="READ_BUDGET"):
        custody.restore()
    assert custody.failure is failure

    # The real absent acquisition settles through _read's common final check.
    # A delayed FileNotFoundError cannot escape as a timely successful None.
    for fault in ("timely", "late", "permission"):
        custody = _synthetic_candidate_custody_v1(root, plan, observed_paths=lambda: ("source.py",), effects=())
        custody.deadline_ns = 1000
        missing, clock = root / ("absent-" + fault), [100]
        native_lstat = Path.lstat
        before_attempts, before_bytes = custody.read_attempts, custody.observed_read_bytes
        remaining = custody.remaining_read_bytes
        with monkeypatch.context() as scoped:
            scoped.setattr(runner.time, "monotonic_ns", lambda: clock[0])
            def final_absence(p, *args, **kwargs):
                if p == missing:
                    if fault == "permission":
                        raise PermissionError("candidate optional status denied")
                    try:
                        return native_lstat(p, *args, **kwargs)
                    finally:
                        if fault == "late":
                            clock[0] = 1000
                return native_lstat(p, *args, **kwargs)
            scoped.setattr(Path, "lstat", final_absence)
            if fault == "timely":
                assert custody._read(missing) is None and custody.failure is None
            else:
                expected = RuntimeError if fault == "late" else PermissionError
                with pytest.raises(expected, match="CUSTODY_UNAVAILABLE" if fault == "late" else "status denied") as failure:
                    custody._read(missing)
                assert custody.failure is failure.value and custody.state == "CLEANUP_REJECTED"
        assert custody.read_attempts == before_attempts + 1
        assert custody.observed_read_bytes == before_bytes and custody.remaining_read_bytes == remaining


def _exercise_failed_admission_plan_v1(tmp_path, monkeypatch, fixture_factory):
    """Real selection/acquisition/finalizer negatives, with no command dispatch."""
    for fault in ("before-selection", "scan", "mapper", "publication"):
        root = tmp_path / ("admission-" + fault)
        root.mkdir()
        primary = ValueError("synthetic admission failure: " + fault)
        calls, writes, final = [], [], []
        selected = {}
        with monkeypatch.context() as scoped:
            scoped.setattr(runner, "_repo_root", lambda: root)
            suppliers = fixture_factory(patcher=scoped)
            original_scan, original_mapper = suppliers["scan_capacity_source"], suppliers["mapper_read_source"]
            def scan(paths, phase, plan):
                calls.append("scan")
                selected.update(paths=paths, phase=phase, plan=plan)
                assert runner._RUN_PROVENANCE_ATTEMPTED is False
                if fault == "scan":
                    raise primary
                launch = original_scan(paths, phase, plan)
                selected["launch"] = launch
                return launch
            def mapper(paths, phase, plan):
                calls.append("mapper")
                assert paths is selected["paths"] and plan is selected["plan"]
                assert phase == selected["phase"] and runner._RUN_PROVENANCE_ATTEMPTED is False
                if fault == "mapper":
                    raise primary
                return original_mapper(paths, phase, plan)
            def publish(*args, **kwargs):
                writes.append(kwargs["command_count"])
                assert runner._RUN_PROVENANCE_ATTEMPTED is True
                if fault == "publication":
                    raise primary
                reliability.write_run_provenance(*args, **kwargs)
            def implementation(_argv):
                paths = runner._RUN_COMMANDS_ACTIVE_PATHS
                commands = runner.build_phase_commands(runner.ALL_PHASE,
                    paths.validation_output_root, paths.pytest_basetemp_root)
                selected["execution"] = runner._prepare_execution_plan(commands)
                runner._publish_active_plan_provenance(runner.ALL_PHASE, selected["execution"])
                raise AssertionError("failed admission must never reach dispatch")
            original_finalize = runner._finalize_validation_run
            def finalize(**kwargs):
                final.append(kwargs)
                assert kwargs["receipts"] == () and kwargs["result"] != 0
                if fault == "before-selection":
                    assert kwargs["expected_plan"] == () and kwargs["planned_count"] == 0
                    assert kwargs["scan_launch"] is None
                    assert not runner._SCAN_CAPACITY_ATTEMPTED and not runner._MAPPER_READ_SOURCE_ATTEMPTED
                else:
                    assert kwargs["expected_plan"] is selected["plan"]
                    assert kwargs["run_paths"] is selected["paths"] and kwargs["phase"] == selected["phase"]
                    assert kwargs["planned_count"] == len(selected["plan"]) > 0
                    assert kwargs["scan_launch"] is selected.get("launch")
                    assert runner._RUN_PROVENANCE_ATTEMPTED is (fault == "publication")
                    assert not runner._RUN_PROVENANCE_WRITTEN
                    assert not (kwargs["run_paths"].evidence_root / "run.json").exists()
                    counts = tuple(calls)
                    with pytest.raises(ValueError, match="cannot be retried"):
                        runner._publish_active_plan_provenance(runner.ALL_PHASE, selected["execution"])
                    assert tuple(calls) == counts
                    if fault == "publication":
                        for field in ("expected_plan", "run_paths", "phase"):
                            changed = dict(kwargs)
                            changed["_supervision_state"] = dict(paths=kwargs["run_paths"],
                                phase=kwargs["phase"], pending=False, receipt=None, errors=[])
                            changed[field] = (tuple(list(kwargs[field])) if field == "expected_plan"
                                else replace(kwargs[field]) if field == "run_paths" else "different-phase")
                            assert changed[field] is not kwargs[field]
                            # Each deliberately corrupt identity owns separate
                            # synthetic custody. Its retained pending state must
                            # not contaminate the real failed-publication case.
                            original_supervision = runner._RUN_COMMANDS_SUPERVISION
                            with monkeypatch.context() as identity_case:
                                identity_case.setattr(runner, "_RUN_COMMANDS_SUPERVISION",
                                    changed["_supervision_state"])
                                with pytest.raises(ValueError, match="finalizer lost original scan launch identity"):
                                    original_finalize(**changed)
                                assert changed["_supervision_state"]["pending"] is (field != "expected_plan")
                            assert runner._RUN_COMMANDS_SUPERVISION is original_supervision
                            assert not original_supervision["pending"]
                assert any(error is primary for error in kwargs["_supervision_state"]["errors"])
                outcome = original_finalize(**kwargs)
                result, cleanup, completion = outcome
                assert result == 1 and completion.final_state == "FAIL"
                assert completion.command_count_started == completion.command_count_completed == 0
                assert completion.command_count_planned == kwargs["planned_count"]
                assert cleanup == "PASS_REMOVED_EXACT_RUN_ROOT"
                return outcome
            scoped.setattr(runner, "_main_impl", implementation)
            scoped.setattr(runner, "write_run_provenance", publish)
            scoped.setattr(runner, "_finalize_validation_run", finalize)
            scoped.setattr(runner, "cleanup_validation_run", reliability.cleanup_validation_run)
            scoped.setattr(runner, "validate_complete_run_evidence", reliability.validate_complete_run_evidence)
            scoped.setattr(runner, "validate_published_completion_receipt", reliability.validate_published_completion_receipt)
            scoped.setattr(runner, "_execute_supervised_command", lambda *a, **k:
                (_ for _ in ()).throw(AssertionError("unexpected native dispatch")))
            if fault == "before-selection":
                scoped.setattr(runner, "_validation_text_integrity_preflight", lambda root:
                    (_ for _ in ()).throw(primary))
            assert runner.main([], scan_capacity_source=scan, mapper_read_source=mapper) == 1
            assert len(final) == 1
            assert calls == ([] if fault == "before-selection" else ["scan"] if fault == "scan" else ["scan", "mapper"])
            assert writes == ([0] if fault == "before-selection" else [len(selected["plan"])] if fault == "publication" else [])
            assert not final[0]["run_paths"].process_root.exists()
            if "launch" in selected:
                assert all(value.process is None and value.reader is None and value.writer is None
                           for value in selected["launch"].launch_inputs.values())


def _exercise_windows_job_resource_v1(area, monkeypatch, capsys, deadline, settlement):
    """Grouped resource-only qualification; pure injections never claim native work."""
    import ctypes as C
    import json
    import os
    import subprocess
    import sys
    import threading
    import time
    from contextlib import nullcontext,contextmanager
    from types import SimpleNamespace
    import pytest
    from tools import validation_reliability as owner
    group=area/'windows-job'; group.mkdir()
    environment={key:value for key,value in os.environ.items() if not key.upper().startswith(('QTT_','PYTHON'))}
    environment.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
    bounds=dict(stdout_bytes=16384,stderr_bytes=16384,combined_output_bytes=32768)
    count=0
    def operands(argv,cwd,evidence,run,index,end,settle,cap=2,env=None,phase='standalone-pytest-helper'):
        return dict(run_id=run,phase=phase,command_index=index,argv=tuple(argv),cwd=cwd,evidence_root=evidence,
            environment=dict(environment if env is None else env),active_process_limit=cap,
            process_commit_bytes=268435456,job_commit_bytes=536870912,cpu_rate_10000=2000,
            execution_deadline_ns=end,settlement_deadline_ns=settle)
    def fresh_deadline(seconds=60):
        end=min(deadline,time.monotonic_ns()+int(seconds*1e9))
        settle=min(settlement,end+10_000_000_000)
        assert time.monotonic_ns()<end<settle
        return end,settle
    end,settle=fresh_deadline()
    pure_argv=(sys.executable,'-I','-B','-X','utf8','-c','print("PURE_REFERENCE_ONLY")')
    good=operands(pure_argv,group,group/'pure','pure-job',1,end,settle)
    for key in ('command_index','active_process_limit','process_commit_bytes','job_commit_bytes',
                'cpu_rate_10000','execution_deadline_ns','settlement_deadline_ns'):
        for value in (True,1.0,'1'):
            changed=dict(good); changed[key]=value
            with pytest.raises((TypeError,ValueError)): owner._WindowsJobScopeV1(**changed)
    for key,value in (('active_process_limit',0),('active_process_limit',3),('process_commit_bytes',0),
            ('job_commit_bytes',536870913),('cpu_rate_10000',2001),('cpu_rate_10000',0),
            ('execution_deadline_ns',time.monotonic_ns()-1),('settlement_deadline_ns',end),
            ('argv',list(pure_argv)),('environment',{'Path':'a','PATH':'b'}),
            ('environment',{'X':'z'*32768}),('argv',(sys.executable,'z'*32768))):
        changed=dict(good); changed[key]=value
        with pytest.raises((TypeError,ValueError)): owner._WindowsJobScopeV1(**changed)
    scope=owner._WindowsJobScopeV1(**good)
    original=scope.owner; scope.owner=(original[0],original[1]+1)
    with pytest.raises(RuntimeError,match='foreign'): scope.check()
    scope.owner=original
    with pytest.raises(TypeError):
        with owner._windows_job_scope_v1(object()): pass
    # This pure oracle is separate from the native witness produced below.
    from copy import deepcopy
    U32=(1<<32)-1
    def dword(value,positive=False):
        if type(value) is not int or not int(positive)<=value<=U32:
            raise ValueError('exact DWORD required')
        return value
    def snapshot(value,expected):
        keys={'total','active','terminated_by_limit','assigned','listed','pids'}
        if type(value) is not dict or set(value)!=keys:
            raise ValueError('complete native observation required')
        if type(expected) is not tuple or len(set(expected))!=len(expected):
            raise ValueError('distinct expected identities required')
        for pid in expected: dword(pid,True)
        for name in keys-{'pids'}: dword(value[name])
        pids=value['pids']
        if type(pids) is not tuple: raise ValueError('exact PID sequence required')
        for pid in pids: dword(pid,True)
        if len(set(pids))!=len(pids): raise ValueError('duplicate native PID')
        if value['assigned']!=value['listed'] or value['listed']!=len(pids):
            raise ValueError('incomplete native member list')
        if set(pids)!=set(expected) or value['active']!=len(expected):
            raise ValueError('unexpected current member')
        if value['total']<len(expected): raise ValueError('impossible lifetime lower bound')
        return value['total']
    def pair_reference(record):
        fields={'root_pid','child_pid','before','held_first','held_last','after',
            'root_handle_verified','child_handle_verified','root_live_at_barrier','child_live_at_barrier',
            'creation_identities_match','image_matches','root_signaled','child_signaled',
            'configured_cap','cap_readback','handle_close_errors'}
        if type(record) is not dict or set(record)!=fields: raise ValueError('incomplete witness')
        root,child=record['root_pid'],record['child_pid']; dword(root,True); dword(child,True)
        if root==child: raise ValueError('root/child alias')
        for key in ('configured_cap','cap_readback'):
            if type(record[key]) is not int or record[key]!=2: raise ValueError('changed cap')
        for key in ('root_handle_verified','child_handle_verified','root_live_at_barrier','child_live_at_barrier',
                'creation_identities_match','image_matches','root_signaled','child_signaled'):
            if record[key] is not True: raise ValueError('missing actual witness: '+key)
        if type(record['handle_close_errors']) is not tuple or record['handle_close_errors']!=():
            raise ValueError('unresolved handle')
        totals=[snapshot(record['before'],(root,)),snapshot(record['held_first'],(root,child)),
            snapshot(record['held_last'],(root,child)),snapshot(record['after'],())]
        if any(b<a for a,b in zip(totals,totals[1:])): raise ValueError('decreasing lifetime count')
        return dict(resource_witness='consistent',lifetime_attribution='not_established',
            raw_totals=tuple(totals),historical_process_trace_complete=False)
    def reference_row(total,*pids):
        return dict(total=total,active=len(pids),terminated_by_limit=0,
            assigned=len(pids),listed=len(pids),pids=tuple(pids))
    def reference_case(total=4):
        return dict(root_pid=101,child_pid=202,before=reference_row(1,101),
            held_first=reference_row(total,101,202),held_last=reference_row(total,202,101),after=reference_row(total),
            root_handle_verified=True,child_handle_verified=True,root_live_at_barrier=True,child_live_at_barrier=True,
            creation_identities_match=True,image_matches=True,root_signaled=True,child_signaled=True,
            configured_cap=2,cap_readback=2,handle_close_errors=())
    positives=[]
    for total in (2,3,4,9,U32):
        for order in ((101,202),(202,101)):
            value=reference_case(total); value['held_first']['pids']=order
            positives.append(pair_reference(value))
    mutations=[]
    for key in ('root_handle_verified','child_handle_verified','root_live_at_barrier','child_live_at_barrier',
            'creation_identities_match','image_matches','root_signaled','child_signaled'):
        for bad in (False,1,None):
            value=reference_case(); value[key]=bad; mutations.append((key,value))
    for key in ('configured_cap','cap_readback'):
        for bad in (1,3,True,2.0):
            value=reference_case(); value[key]=bad; mutations.append((key,value))
    for label,keys,bad in (
        ('unknown_pid',('held_first','pids'),(101,303)),
        ('extra_current_member',('held_first',),reference_row(4,101,202,303)),
        ('truncated',('held_first','listed'),1),('duplicate',('held_last','pids'),(101,101)),
        ('survivor',('after',),reference_row(4,202)),('decrease',('after','total'),3),
        ('impossible_lower_bound',('held_first','total'),1),('alias',('child_pid',),101),
        ('close_failure',('handle_close_errors',),('close_error',)),
        ('missing_first',('held_first',),None),('missing_last',('held_last',),None)):
        value=reference_case(); target=value
        for key in keys[:-1]: target=target[key]
        target[keys[-1]]=bad; mutations.append((label,value))
    value=reference_case(); del value['held_first']; mutations.append(('absent_barrier',value))
    for key in ('total','active','terminated_by_limit','assigned','listed'):
        for bad in (True,1.0,-1,U32+1):
            value=reference_case(); value['held_first'][key]=bad; mutations.append((key,value))
    for label,value in mutations:
        assert repr(value)!=repr(reference_case()),label
        with pytest.raises(ValueError): pair_reference(value)
    histories=({'successful_associations':2,'failed_associations':2},
               {'successful_associations':4,'failed_associations':0})
    assert all(sum(value.values())==4 for value in histories) and histories[0]!=histories[1]
    with capsys.disabled():
        print('WINDOWS_JOB_ACCOUNTING_PURE_REFERENCE '+json.dumps(dict(valid_reference_witnesses=len(positives),
            invalid_reference_witnesses_rejected=len(mutations),nonidentifiability_examples=2,
            native_execution=False,historical_report_requalified=False)),flush=True)

    if sys.platform!='win32':
        with pytest.raises(RuntimeError,match='unsupported'):
            with owner._windows_job_scope_v1(scope): pass
        with capsys.disabled(): print('WINDOWS_JOB_UNSUPPORTED_NATIVE_NOT_EXECUTED',flush=True)
        return (lambda **kw:nullcontext(),lambda *args:None,lambda:None)
    worker_source="import ctypes as C\nimport json\nimport os\nfrom pathlib import Path\nimport subprocess\nimport sys\nimport time\n\nrepo,area,mode,end,settle,role=sys.argv[1:]\nroot=Path(area); end=int(end); settle=int(settle)\nassert root.is_absolute() and Path(repo).is_absolute() and mode in ('normal','timeout')\nassert os.path.normcase(os.getcwd())==os.path.normcase(str(root))\nsys.path.insert(0,repo)\nfrom tools import validation_reliability as owner\napi=owner._windows_job_api_v1()\nqueries=0\nchecks=0\nreads=set()\ndef call(name,*args):\n    global queries\n    assert time.monotonic_ns()<settle\n    C.set_last_error(0); value=getattr(api,name)(*args)\n    if not value: raise owner._windows_job_error_v1(name,int(C.get_last_error()))\n    queries+=1\n    assert queries<=4\n    return value\ndef creation(handle):\n    values=[api.FileTime() for _ in range(4)]\n    call('GetProcessTimes',handle,*(C.byref(value) for value in values))\n    value=(int(values[0].high)<<32)|int(values[0].low)\n    assert value>0\n    return value\ndef pairs(items):\n    value={}\n    for key,item in items:\n        if key in value: raise ValueError('duplicate synchronization key')\n        value[key]=item\n    return value\ndef read(name,keys=None):\n    global checks\n    assert name in ('child-ready.json','release.bin') and name not in reads\n    assert time.monotonic_ns()<settle\n    checks+=1; assert checks<=3000\n    path=root/name\n    try: before=path.lstat()\n    except FileNotFoundError: return None\n    identity=owner._scan_file_identity(before)\n    assert before.st_size<=4096\n    fd=owner._open_regular_worktree_descriptor(path,nonblocking=True)\n    try:\n        opened=os.fstat(fd)\n        assert owner._scan_file_identity(opened)==identity\n        raw=os.read(fd,4097)\n        assert len(raw)==before.st_size and len(raw)<=4096\n        assert owner._scan_same_api_version(os.fstat(fd))==owner._scan_same_api_version(opened)\n        assert owner._scan_same_api_version(path.lstat())==owner._scan_same_api_version(before)\n    finally: os.close(fd)\n    reads.add(name)\n    if keys is None: return raw\n    value=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs)\n    assert type(value) is dict and set(value)==keys\n    assert all(type(v) is int and 0<v<=(0xffffffffffffffff if 'filetime' in k else 0xffffffff) for k,v in value.items())\n    return value\ndef wait_file(name,keys,deadline):\n    while time.monotonic_ns()<deadline:\n        value=read(name,keys)\n        if value is not None: return value\n        time.sleep(min(0.01,max(0,(deadline-time.monotonic_ns())/1e9)))\n    raise TimeoutError('native fixture readiness cutoff: '+name)\ndef publish(name,value):\n    path=root/name; temporary=root/('.'+name+'.pending')\n    assert name in ('child-ready.json','pair-ready.json')\n    assert not os.path.lexists(path) and not os.path.lexists(temporary)\n    owner.atomic_write_json(temporary,value)\n    # Windows rename refuses an existing destination. Publish only after the\n    # existing atomic owner has removed its temporary hard link.\n    os.rename(temporary,path)\n\nif role=='child':\n    stamp=creation(api.GetCurrentProcess())\n    print('OWNED_DESCENDANT_STARTED' if mode=='normal' else 'OWNED_SLEEPING_DESCENDANT',flush=True)\n    publish('child-ready.json',dict(pid=os.getpid(),parent_pid=os.getppid(),creation_filetime_100ns=stamp))\n    print(json.dumps(dict(child_identity_queries=queries)),flush=True)\n    byte=sys.stdin.buffer.read(1)\n    raise SystemExit(0 if byte==b'R' else 3)\n\nassert role=='root'\nroot_stamp=creation(api.GetCurrentProcess())\nevents={'subprocess.Popen':0,'_winapi.CreateProcess':0}\ndef audit(event,args):\n    if event in events:\n        events[event]+=1\n        if events[event]>1: raise RuntimeError('unexpected repeated worker creation audit')\nsys.addaudithook(audit)\ndescendant_creation_flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP\nif type(descendant_creation_flags) is not int or descendant_creation_flags != 0x208:\n    raise ValueError('exact console-detached descendant flags required')\ntry:\n    child=subprocess.Popen([sys.executable,'-I','-B','-X','utf8',__file__,repo,area,mode,str(end),str(settle),'child'],\n        shell=False,close_fds=True,creationflags=descendant_creation_flags,stdin=subprocess.PIPE,stdout=sys.stdout,stderr=sys.stderr)\nexcept OSError as error:\n    print(json.dumps(dict(child_returncode=None,create_error=dict(error_class=type(error).__name__,\n        winerror=error.winerror,errno=error.errno),root_pid=os.getpid(),child_pid=None,\n        creation_audit_counts=events,worker_identity_queries=queries,descendant_creation_flags=descendant_creation_flags)),flush=True)\n    raise SystemExit(2)\nprint('OWNED_PARENT_STARTED' if mode=='normal' else 'OWNED_SLEEPING_PARENT',flush=True)\nready=wait_file('child-ready.json',{'pid','parent_pid','creation_filetime_100ns'},end)\nhandle=int(child._handle)\nactual_pid=int(call('GetProcessId',handle))\nactual_stamp=creation(handle)\nC.set_last_error(0); state=int(api.WaitForSingleObject(handle,0)); queries+=1\nif state==0xffffffff: raise owner._windows_job_error_v1('WaitForSingleObject:child',int(C.get_last_error()))\nassert queries<=4 and state==258\nassert ready==dict(pid=actual_pid,parent_pid=os.getpid(),creation_filetime_100ns=actual_stamp)\nassert actual_pid==child.pid and events=={'subprocess.Popen':1,'_winapi.CreateProcess':1}\npublish('pair-ready.json',dict(root_pid=os.getpid(),root_creation_filetime_100ns=root_stamp,\n    child_pid=actual_pid,child_creation_filetime_100ns=actual_stamp,popen_events=events['subprocess.Popen'],\n    createprocess_events=events['_winapi.CreateProcess']))\nprint(json.dumps(dict(worker_identity_queries=queries,worker_ready_checks=checks,\n    child_ready=ready,child_handle=handle,child_wait=state,descendant_creation_flags=descendant_creation_flags)),flush=True)\nif mode=='timeout':\n    while time.monotonic_ns()<settle:\n        time.sleep(min(0.01,max(0,(settle-time.monotonic_ns())/1e9)))\n    raise TimeoutError('supervisor did not settle held timeout pair')\nrelease=wait_file('release.bin',None,end)\nassert release==b'RELEASE\\n'\nassert child.stdin.write(b'R')==1\nchild.stdin.flush(); child.stdin.close()\nresult=child.wait(timeout=max(0,(end-time.monotonic_ns())/1e9))\nchild._handle.Close()\nprint(json.dumps(dict(child_returncode=result,create_error=None,root_pid=os.getpid(),child_pid=actual_pid,\n    creation_audit_counts=events,worker_identity_queries=queries,descendant_creation_flags=descendant_creation_flags,worker_ready_checks=checks,\n    worker_child_handle_closed=True)),flush=True)\nraise SystemExit(0 if result==0 else 2)\n"
    real_api=owner._windows_job_api_v1()
    assert real_api.sizes==dict(BASIC_LIMIT=64,IO_COUNTERS=48,EXTENDED_LIMIT=144,
        BASIC_ACCOUNTING=48,CPU_RATE=8,STARTUPINFOW=104,STARTUPINFOEXW=112,PROCESS_INFORMATION=24)
    # Independent launch-input expectations; no new native process or console.
    import ast
    import copy
    root_word=0x0008060C; descendant_word=0x00000208
    assert owner._WindowsJobScopeV1._checked_root_creation_flags(root_word)==root_word
    rejected_flags=0
    invalid_root=[root_word^(1<<bit) for bit in range(32)]
    invalid_root += [True,False,float(root_word),str(root_word),None,-1,1<<32]
    for bad in invalid_root:
        with pytest.raises((TypeError,ValueError)):
            owner._WindowsJobScopeV1._checked_root_creation_flags(bad)
        rejected_flags+=1
    assert root_word&(0x08000000|0x10|0x01000000)==0
    worker_tree=ast.parse(worker_source)
    worker_calls=[node for node in ast.walk(worker_tree) if isinstance(node,ast.Call)
        and isinstance(node.func,ast.Attribute) and node.func.attr=='Popen']
    assert len(worker_calls)==1  # One shared site implements both normal and timeout modes.
    keywords={node.arg:node.value for node in worker_calls[0].keywords}
    assert set(keywords)=={'shell','close_fds','creationflags','stdin','stdout','stderr'}
    assert ast.literal_eval(keywords['shell']) is False and ast.literal_eval(keywords['close_fds']) is True
    assert isinstance(keywords['creationflags'],ast.Name) and keywords['creationflags'].id=='descendant_creation_flags'
    for name,expression in (('stdin','subprocess.PIPE'),('stdout','sys.stdout'),('stderr','sys.stderr')):
        assert ast.dump(keywords[name])==ast.dump(ast.parse(expression,mode='eval').body)
    flag_assignments=[node for node in worker_tree.body if isinstance(node,ast.Assign)
        and any(isinstance(target,ast.Name) and target.id=='descendant_creation_flags' for target in node.targets)]
    assert len(flag_assignments)==1
    assert ast.dump(flag_assignments[0].value)==ast.dump(ast.parse(
        'subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP',mode='eval').body)
    assert (subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)==descendant_word
    expected_guard=ast.parse("if type(descendant_creation_flags) is not int or descendant_creation_flags != 0x208:\n    raise ValueError('exact console-detached descendant flags required')").body[0]
    assert any(ast.dump(node)==ast.dump(expected_guard) for node in worker_tree.body)
    assert any(isinstance(node,ast.Compare) and ast.dump(node)==ast.dump(ast.parse("mode=='timeout'",mode='eval').body)
        for node in ast.walk(worker_tree))
    # Existing no-scope supervisor behavior is exercised with a deliberate
    # injected creation failure; the real Windows helper's operands are retained.
    assert owner._WINDOWS_JOB_SCOPE_V1.get() is None
    ordinary=owner.hidden_subprocess_kwargs(platform_name='nt',new_process_group=True)
    assert ordinary['creationflags']==0x08000200
    assert ordinary['startupinfo'].dwFlags&subprocess.STARTF_USESHOWWINDOW
    assert ordinary['startupinfo'].wShowWindow==subprocess.SW_HIDE
    assert owner.hidden_subprocess_kwargs(platform_name='nt',new_process_group=False)['creationflags']==0x08000000
    assert owner.hidden_subprocess_kwargs(platform_name='posix',new_process_group=True)=={'start_new_session':True}
    assert owner.hidden_subprocess_kwargs(platform_name='posix',new_process_group=False)=={}
    ordinary_calls=[]
    def denied_ordinary(*args,**kwargs):
        ordinary_calls.append((args,kwargs))
        raise OSError('injected ordinary no-scope creation failure')
    ordinary_evidence=group/'ordinary-noninterference'; ordinary_evidence.mkdir()
    with monkeypatch.context() as patch:
        patch.setattr(owner.subprocess,'Popen',denied_ordinary)
        ordinary_receipt=owner.supervise_command(pure_argv,cwd=group,run_id='pure-no-scope',
            phase='standalone-pytest-helper',command_index=1,evidence_root=ordinary_evidence,
            environment=environment,output_limits=bounds,output_observation={},
            execution_deadline_ns=end,mirror_stdout=False,mirror_stderr=False)
    assert len(ordinary_calls)==1 and ordinary_receipt.pid is None
    assert ordinary_receipt.failure_class=='ENGVR_PROCESS_START_FAILED'
    args,kwargs=ordinary_calls[0]
    assert args==(list(pure_argv),) and kwargs['creationflags']==0x08000200
    assert kwargs['shell'] is False and kwargs['close_fds'] is True
    assert kwargs['stdin']==subprocess.DEVNULL and kwargs['stdout']==kwargs['stderr']==subprocess.PIPE
    assert kwargs['cwd']==group and kwargs['env']==environment
    with capsys.disabled():
        print('WINDOWS_JOB_CONSOLE_PRECHECKS '+json.dumps(dict(root_flags=root_word,
            descendant_popen_argument=descendant_word,invalid_root_flags_rejected=rejected_flags,
            shared_descendant_site_modes=['normal','timeout'],explicit_standard_handles=True,
            ordinary_windows_group_flags=ordinary['creationflags'],ordinary_non_group_flags=0x08000000,
            posix_unchanged=True,ordinary_creation_failure_injected=True,native_execution=False)),flush=True)

    # An API model exercises the complete backend, not the actual native cases.
    class ApiModel:
        def __init__(self,fault):
            self.api=SimpleNamespace(**vars(real_api)); self.fault=fault; self.triggered=False
            self.calls={}; self.alive=False; self.created=False; self.resumed=False; self.terminated=False
            self.handle=100; self.ext=None; self.cpu=None; self.closed=[]
            self.order=[]; self.attributes={}; self.duplicates=[]; self.creation_inputs=None
            for name in ('CreateJobObjectW','SetInformationJobObject','QueryInformationJobObject',
                    'GetHandleInformation','DuplicateHandle','InitializeProcThreadAttributeList',
                    'UpdateProcThreadAttribute','DeleteProcThreadAttributeList','CreateProcessW',
                    'IsProcessInJob','GetProcessTimes','GetProcessId','QueryFullProcessImageNameW','ResumeThread','WaitForSingleObject',
                    'GetExitCodeProcess','TerminateJobObject','CloseHandle'):
                setattr(self.api,name,self.function(name))
            self.api.GetCurrentProcess=lambda:-1
        def function(self,name):
            def call(*args):
                n=self.calls.get(name,0)+1; self.calls[name]=n
                self.order.append(name)
                if self.fault==(name,n):
                    self.triggered=True; C.set_last_error(5)
                    return 0xffffffff if name=='ResumeThread' else 0
                if name=='CreateJobObjectW': return 99
                if name=='GetHandleInformation':
                    C.cast(args[1],C.POINTER(real_api.D))[0]=0 if args[0]==99 else 1
                elif name=='SetInformationJobObject':
                    cls=real_api.Extended if args[1]==9 else real_api.Cpu
                    value=cls.from_buffer_copy(C.string_at(args[2],args[3]))
                    if args[1]==9: self.ext=value
                    else: self.cpu=value
                elif name=='QueryInformationJobObject':
                    kind=args[1]; length=args[3]
                    if kind==9:
                        value=real_api.Extended.from_buffer_copy(bytes(self.ext))
                        if self.fault=='readback' and self.created:
                            self.triggered=True; value.process_memory+=1
                        C.memmove(args[2],C.byref(value),C.sizeof(value))
                    elif kind==15: C.memmove(args[2],C.byref(self.cpu),C.sizeof(self.cpu))
                    elif kind==1:
                        value=real_api.Accounting(); value.total=int(self.created)
                        value.active=int(self.alive or (self.fault in ('descendant','nonzero-descendant') and self.resumed and not self.terminated))
                        C.memmove(args[2],C.byref(value),C.sizeof(value))
                    else:
                        values=C.cast(args[2],C.POINTER(real_api.D)); active=int(self.alive or (self.fault in ('descendant','nonzero-descendant') and self.resumed and not self.terminated))
                        values[0]=values[1]=active
                        if active: C.cast(args[2],C.POINTER(real_api.S))[1]=4322 if self.fault in ('descendant','nonzero-descendant') and self.resumed else 4321
                        if self.fault=='short-list': self.triggered=True; length=7
                        if self.fault=='oversized-list': self.triggered=True; values[0]=values[1]=9
                    C.cast(args[4],C.POINTER(real_api.D))[0]=length
                elif name=='DuplicateHandle':
                    self.handle+=1; C.cast(args[3],C.POINTER(real_api.H))[0]=self.handle
                    assert type(args[1]) is int and args[1]>0 and args[5] is True
                    self.duplicates.append(dict(source=args[1],duplicate=self.handle))
                elif name=='InitializeProcThreadAttributeList':
                    if args[0] is None:
                        C.cast(args[3],C.POINTER(real_api.S))[0]=65537 if self.fault=='attribute-size' else 128
                        self.triggered=self.triggered or self.fault=='attribute-size'
                        C.set_last_error(122); return 0
                elif name=='UpdateProcThreadAttribute':
                    assert args[2] in (0x20002,0x2000D) and args[2] not in self.attributes
                    count=3 if args[2]==0x20002 else 1
                    assert args[4]==8*count
                    self.attributes[args[2]]=tuple(int(C.cast(args[3],C.POINTER(real_api.H))[i]) for i in range(count))
                elif name=='DeleteProcThreadAttributeList': return None
                elif name=='CreateProcessW':
                    assert type(args[5]) is int and args[5]==0x0008060C
                    assert args[2] is args[3] is None and args[4] is True
                    startup=C.cast(args[8],C.POINTER(real_api.StartupEx)).contents
                    stdio=(startup.startup.stdin,startup.startup.stdout,startup.startup.stderr)
                    assert stdio==tuple(row['duplicate'] for row in self.duplicates)==self.attributes[0x20002]
                    assert all(stdio) and len(set(stdio))==3 and self.attributes[0x2000D]==(99,)
                    assert startup.startup.cb==112 and startup.startup.flags==0x101 and startup.startup.show==0
                    first=self.order.index('audit:subprocess.Popen'); second=self.order.index('audit:_winapi.CreateProcess')
                    assert first<second<self.order.index('CreateProcessW')
                    self.creation_inputs=dict(creation_flags=args[5],standard_handles=stdio,
                        job_list=self.attributes[0x2000D],handle_list=self.attributes[0x20002],
                        startup_flags=startup.startup.flags,show_window=startup.startup.show,audit_before_create=True)
                    value=C.cast(args[9],C.POINTER(real_api.ProcessInfo)).contents
                    value.process=501; value.thread=502; value.pid=4321; value.tid=765
                    self.created=True; self.alive=True
                elif name=='IsProcessInJob':
                    member=args[0]!=-1
                    if self.fault=='membership' and member: self.triggered=True; member=False
                    C.cast(args[2],C.POINTER(real_api.B))[0]=int(member)
                elif name=='GetProcessId':
                    if self.fault=='process-id': self.triggered=True; return 4322
                    return 4321
                elif name=='QueryFullProcessImageNameW':
                    value=pure_argv[0]
                    if self.fault=='image': self.triggered=True; value=value+'.wrong'
                    C.memmove(args[2],C.create_unicode_buffer(value),(len(value)+1)*2)
                    C.cast(args[3],C.POINTER(real_api.D))[0]=len(value)
                elif name=='GetProcessTimes':
                    C.cast(args[1],C.POINTER(real_api.FileTime)).contents.low=12345
                elif name=='ResumeThread':
                    self.resumed=True; self.alive=False
                    if self.fault in ('descendant','nonzero-descendant'): self.triggered=True
                    return 1
                elif name=='WaitForSingleObject':
                    if self.fault=='pre-resume-signal' and self.created and not self.resumed:
                        self.triggered=True; return 0
                    return 258 if self.alive else 0
                elif name=='GetExitCodeProcess':
                    C.cast(args[1],C.POINTER(real_api.D))[0]=259 if self.fault=='exit-259' else 2 if self.fault=='nonzero-descendant' else 1 if self.terminated else 0
                    if self.fault=='exit-259': self.triggered=True
                elif name=='TerminateJobObject': self.terminated=True; self.alive=False
                elif name=='CloseHandle': self.closed.append(args[0])
                return 1
            return call
    fault_cases=[None,('CreateJobObjectW',1),('GetHandleInformation',1),('SetInformationJobObject',1),
        ('SetInformationJobObject',2),('DuplicateHandle',1),('DuplicateHandle',2),('DuplicateHandle',3),
        ('GetHandleInformation',2),('GetHandleInformation',3),('GetHandleInformation',4),
        ('InitializeProcThreadAttributeList',1),('InitializeProcThreadAttributeList',2),
        ('UpdateProcThreadAttribute',1),('UpdateProcThreadAttribute',2),('CreateProcessW',1),
        ('GetProcessTimes',1),('ResumeThread',1),('CloseHandle',1),('CloseHandle',2),('CloseHandle',3),
        ('CloseHandle',4),('CloseHandle',5),('CloseHandle',6),
        'membership','readback','attribute-size','short-list','oversized-list','descendant','nonzero-descendant','exit-259',
        'audit-popen','audit-create',('GetProcessId',1),('QueryFullProcessImageNameW',1),
        'image','process-id','pre-resume-signal','flags-no-window','flags-new-console','flags-breakaway','flags-type']
    references=[]
    for index,fault in enumerate(fault_cases):
        model=ApiModel(fault); end,settle=fresh_deadline()
        evidence=group/('model-'+str(index)); evidence.mkdir()
        args=operands(pure_argv,group,evidence,'pure-job-'+str(index),1,end,settle)
        probe=owner._WindowsJobScopeV1(**args); actual={}; receipt=None; error=None
        with monkeypatch.context() as patch:
            patch.setattr(owner,'_windows_job_api_v1',lambda:model.api)
            patch.setattr(owner,'_WINDOWS_JOB_LIVE_LOCK_V1',threading.Lock())
            original_audit=sys.audit
            def audit(name,*values):
                if name in ('subprocess.Popen','_winapi.CreateProcess'): model.order.append('audit:'+name)
                event='subprocess.Popen' if fault=='audit-popen' else '_winapi.CreateProcess' if fault=='audit-create' else None
                if name==event:
                    model.triggered=True
                    raise PermissionError('injected creation audit denial')
                return original_audit(name,*values)
            patch.setattr(owner.sys,'audit',audit)
            if fault in ('flags-no-window','flags-new-console','flags-breakaway','flags-type'):
                original_flags=owner._WindowsJobScopeV1._checked_root_creation_flags
                def bad_flags(value):
                    assert value==0x0008060C
                    model.triggered=True
                    invalid={'flags-no-window':value|0x08000000,'flags-new-console':value|0x10,
                        'flags-breakaway':value|0x01000000,'flags-type':float(value)}[fault]
                    return original_flags(invalid)
                patch.setattr(owner._WindowsJobScopeV1,'_checked_root_creation_flags',staticmethod(bad_flags))
            try:
                with owner._windows_job_scope_v1(probe):
                    with pytest.raises(RuntimeError,match='reused|reentered'):
                        with owner._windows_job_scope_v1(probe): pass
                    receipt=owner.supervise_command(pure_argv,cwd=group,run_id=args['run_id'],phase=args['phase'],
                        command_index=1,evidence_root=evidence,environment=environment,execution_deadline_ns=end,
                        output_limits=bounds,output_observation=actual,mirror_stdout=False,mirror_stderr=False)
            except BaseException as exc: error=exc
            if fault is None:
                assert error is None and receipt.failure_class is None
                assert not owner._command_requires_process_retention_v1(receipt)
                for invalid in (None,True,float(0x0008060C),0x08080604,0x0008060C|0x10):
                    bad=copy.deepcopy(actual['windows_job']); bad['creation']['creation_flags']=invalid
                    assert owner._windows_job_projection_retains_v1(receipt,bad)
                bad=copy.deepcopy(actual['windows_job']); del bad['creation']['creation_flags']
                assert owner._windows_job_projection_retains_v1(receipt,bad)
                with pytest.raises(RuntimeError,match='reused|reentered'):
                    with owner._windows_job_scope_v1(probe): pass
            else:
                assert model.triggered,(fault,model.calls)
                assert error is not None or receipt.failure_class is not None,fault
                if fault=='exit-259': assert receipt.native_exit_code==259
                if fault=='descendant':
                    assert receipt.failure_class=='ENGVR_PROCESS_DESCENDANTS_REMAIN' and model.calls['TerminateJobObject']==1
                if fault=='nonzero-descendant':
                    assert receipt.native_exit_code==2 and receipt.failure_class=='ENGVR_NATIVE_EXIT_NONZERO'
                    assert model.calls['TerminateJobObject']==1 and any(type(item) is dict and 'root_terminal_nonempty' in item for item in probe.history)
                if fault in ('audit-popen','audit-create','flags-no-window','flags-new-console','flags-breakaway','flags-type'):
                    assert model.calls.get('CreateProcessW',0)==0
                if model.created:
                    assert probe.creation['pid']==4321
                    if receipt is not None: assert receipt.pid==4321
            assert model.calls.get('TerminateJobObject',0)<=1
            if probe.handle_close_errors: assert error is not None or owner._command_requires_process_retention_v1(receipt)
            references.append(dict(fault=fault,triggered=model.triggered,native_execution=False,
                created=model.created,resumed=model.resumed,termination_calls=model.calls.get('TerminateJobObject',0),
                retained_handle_errors=probe.handle_close_errors,creation_inputs=model.creation_inputs))
    with capsys.disabled(): print('WINDOWS_JOB_PURE_REFERENCES '+json.dumps(references),flush=True)
    # Selected engineering evidence is external to the disposable wrapper root.
    # This test-only location supplies no native grant or production option.
    retained_text=os.environ.get('QTT_TEST_WINDOWS_JOB_DIAGNOSTIC_EVIDENCE')
    if not retained_text: raise ValueError('selected native fixture requires its external attempt evidence directory')
    retained=Path(retained_text)
    owner._local_unlinked_path(retained)
    assert retained.is_absolute() and retained.is_dir() and not any(retained.iterdir())
    assert not retained.is_relative_to(area) and not retained.is_relative_to(REPO_ROOT)
    diagnostic_used=False
    last_diagnostic=None
    def render_error(error):
        import traceback
        return ''.join(traceback.format_exception(error))
    def retain_streams(evidence,receipt,target,errors):
        streams={}
        for label in ('stdout','stderr'):
            path=Path(getattr(receipt,label+'_path')) if receipt is not None else evidence/('command-1.'+label+'.bin')
            value=dict(source_path=str(path),copy_path=str(target/(label+'.bin')),bytes=None,
                complete_utf8=None,complete_hex=None,copied=False,error=None)
            streams[label]=value
            try:
                info=path.lstat(); identity=owner._scan_file_identity(info)
                assert info.st_size<=bounds[label+'_bytes']
                fd=owner._open_regular_worktree_descriptor(path,nonblocking=True)
                try:
                    opened=os.fstat(fd)
                    assert owner._scan_file_identity(opened)==identity
                    raw=os.read(fd,bounds[label+'_bytes']+1)
                    assert len(raw)==info.st_size and len(raw)<=bounds[label+'_bytes']
                    assert owner._scan_same_api_version(os.fstat(fd))==owner._scan_same_api_version(opened)
                    assert owner._scan_same_api_version(path.lstat())==owner._scan_same_api_version(info)
                finally: os.close(fd)
                destination=target/(label+'.bin')
                owner._local_unlinked_path(destination.parent)
                with destination.open('xb') as out:
                    assert out.write(raw)==len(raw)
                    out.flush(); os.fsync(out.fileno())
                copied=destination.lstat(); checked=owner._scan_file_identity(copied)
                copy_fd=owner._open_regular_worktree_descriptor(destination,nonblocking=True)
                try:
                    current=os.fstat(copy_fd)
                    assert owner._scan_file_identity(current)==checked
                    assert os.read(copy_fd,bounds[label+'_bytes']+1)==raw
                    assert owner._scan_same_api_version(os.fstat(copy_fd))==owner._scan_same_api_version(current)
                    assert owner._scan_same_api_version(destination.lstat())==owner._scan_same_api_version(copied)
                finally: os.close(copy_fd)
                value.update(bytes=len(raw),complete_hex=raw.hex(),copied=True)
                try: value['complete_utf8']=raw.decode('utf-8')
                except UnicodeDecodeError: pass  # Exact bytes remain available, never a guessed text stream.
            except BaseException as error:
                errors.append(error); value['error']=render_error(error)
        return streams
    def write_diagnostic(path,value):
        # Measure incremental UTF-8 output before the bounded aggregate allocation.
        encoder=json.JSONEncoder(ensure_ascii=True,allow_nan=False,separators=(',',':'))
        parts=[]; size=0
        for part in encoder.iterencode(value):
            size+=len(part)  # ensure_ascii=True: exact UTF-8 byte measurement
            if size>1_048_576: raise ValueError('membership diagnostic reporting ceiling exceeded')
            parts.append(part.encode('utf-8'))
        raw=b''.join(parts)
        assert len(raw)==size
        with path.open('xb') as stream:
            assert stream.write(raw)==size
            stream.flush(); os.fsync(stream.fileno())
        return dict(path=str(path),bytes=size,exclusive=True)
    def diagnostic_members(scope,observation,witness):
        nonlocal diagnostic_used
        assert witness['state']=='failed' and not diagnostic_used
        diagnostic_used=True
        record=dict(attempts=0,maximum_attempts=96,job_handle=int(scope.handles['job']),
            observations=[],native_calls=[],errors=[],after_closed_accounting=None,
            failed_latch_preserved=True,attribution='not_established')
        witness['diagnostic']=record
        query=observation.get('query') or {}
        if query.get('complete') is not True or query.get('status')!='complete':
            record['not_opened']='membership unavailable or incomplete'
            return record
        pids=observation['pids']
        assert type(pids) is tuple and len(pids)<=8 and len(set(pids))==len(pids)
        def call(name,*args,close=False):
            if not close: scope.check()
            assert record['attempts']<96
            record['attempts']+=1
            started=time.monotonic_ns(); C.set_last_error(0)
            value=getattr(scope.api,name)(*args)
            error=int(C.get_last_error()); number=int(value or 0)
            failed=number==0xffffffff if name=='WaitForSingleObject' else not number
            record['native_calls'].append(dict(operation=name,result=number,last_error_raw=error,
                before_ns=started,after_ns=time.monotonic_ns()))
            if failed: raise owner._windows_job_error_v1(name,error)
            return number
        for pid in pids:
            row=dict(listed_pid=pid,handle=None,borrowed=False,closed=None,actual_pid=None,
                explicit_job_member=None,wait_before=None,wait_after=None,creation_filetime_100ns=None,
                image=None,image_capacity=4096,native_exit=None,errors=[])
            record['observations'].append(row)
            handle=None; borrowed=pid==scope.process.pid
            try:
                assert type(pid) is int and 0<pid<=0xffffffff and pid!=os.getpid()
                if borrowed: handle=scope.handles['process']
                else: handle=call('OpenProcess',0x00101000,False,pid)
                row.update(handle=int(handle),borrowed=borrowed)
                row['actual_pid']=call('GetProcessId',handle)
                if row['actual_pid']!=pid: raise ValueError('diagnostic handle PID differs from listed PID')
                member=scope.api.B(); call('IsProcessInJob',handle,scope.handles['job'],C.byref(member))
                row['explicit_job_member']=int(member.value)
                if member.value!=1: raise ValueError('diagnostic handle is not verified in the explicit owned job')
                for operation in ('wait_before','creation','image','wait_after'):
                    try:
                        if operation.startswith('wait_'):
                            state=call('WaitForSingleObject',handle,0)
                            row[operation]=state
                            if state not in (0,258): raise ValueError('unexpected diagnostic process wait result')
                        elif operation=='creation':
                            values=[scope.api.FileTime() for _ in range(4)]
                            call('GetProcessTimes',handle,*(C.byref(v) for v in values))
                            row['creation_filetime_100ns']=(int(values[0].high)<<32)|int(values[0].low)
                            assert row['creation_filetime_100ns']>0
                        else:
                            image=C.create_unicode_buffer(4096); length=scope.api.D(4096)
                            call('QueryFullProcessImageNameW',handle,0,image,C.byref(length))
                            row['image_returned_units']=int(length.value)
                            if not 0<length.value<4096: raise ValueError('diagnostic image exceeds fixed capacity')
                            row['image']=image[:length.value]
                    except BaseException as error: row['errors'].append(render_error(error))
                if row['wait_before']==0 and row['wait_after']==258:
                    row['errors'].append('signaled-to-nonsignaled handle inconsistency')
                if 0 in (row['wait_before'],row['wait_after']):
                    code=scope.api.D(); call('GetExitCodeProcess',handle,C.byref(code))
                    row['native_exit']=int(code.value)
            except BaseException as error: row['errors'].append(render_error(error))
            finally:
                if handle is not None and not borrowed:
                    try:
                        call('CloseHandle',handle,close=True); row['closed']=True
                    except BaseException as error:
                        row['closed']=False; row['errors'].append(render_error(error))
                record['errors'].extend(row['errors'])
        # This last read cannot clear the latch, and never reissues membership.
        try:
            value=scope.api.Accounting(); length=scope.api.D(0xffffffff)
            call('QueryInformationJobObject',scope.handles['job'],1,C.byref(value),C.sizeof(value),C.byref(length))
            record['after_closed_accounting']=dict(raw_hex=bytes(value).hex(),returned_bytes_raw=int(length.value),
                total=int(value.total),active=int(value.active),terminated_by_limit=int(value.terminated))
            assert length.value==C.sizeof(value)
        except BaseException as error: record['errors'].append(render_error(error))
        assert witness['state']=='failed'
        return record

    # Deterministic fail paths exercise the actual shared query owner before any
    # new native job is created. These injected answers are never native evidence.
    import struct
    class OldIds(C.Structure):
        _fields_=[('assigned',real_api.D),('listed',real_api.D),('ids',real_api.S*2)]
    class NewIds(C.Structure):
        _fields_=[('assigned',real_api.D),('listed',real_api.D),('ids',real_api.S*8)]
    assert (C.sizeof(real_api.D),C.sizeof(real_api.S),C.sizeof(OldIds),C.sizeof(NewIds),
        NewIds.assigned.offset,NewIds.listed.offset,NewIds.ids.offset)==(4,8,24,72,0,4,8)
    def raw_ids(pids,assigned=None,listed=None):
        value=bytearray(72)
        struct.pack_into('<II',value,0,len(pids) if assigned is None else assigned,len(pids) if listed is None else listed)
        for index,pid in enumerate(pids): struct.pack_into('<Q',value,8+8*index,pid)
        return bytes(value)
    response_cases=[]
    for pids in ((),(11,),(11,22),(11,22,33,44),tuple(range(11,19))):
        response_cases.append((raw_ids(pids),1,234,8+8*len(pids),'complete',pids))
    for error in (234,5,6,87,0):
        for length in (None,0,24,72,0xffffffff):
            response_cases.append((raw_ids((11,22)),0,error,length,'incomplete' if error==234 else 'api_error',None))
    for raw,length,status in ((raw_ids((11,22)),None,'malformed'),(raw_ids((11,22)),73,'malformed'),
            (raw_ids((11,22)),23,'malformed'),(raw_ids((11,22)),0,'malformed'),
            (raw_ids((11,22),4,2),24,'incomplete'),(raw_ids((11,22),1,2),24,'malformed'),
            (raw_ids((11,11)),24,'malformed'),(raw_ids((0,22)),24,'malformed'),
            (raw_ids((1<<32,22)),24,'malformed'),(raw_ids(tuple(range(11,19)),9,9),72,'malformed')):
        response_cases.append((raw,1,0,length,status,None))
    response_results=[]
    for raw,ok,error,length,status,pids in response_cases:
        calls=[]
        def injected_query(handle,kind,pointer,size,returned):
            calls.append(kind); assert handle==99
            if kind==1:
                value=real_api.Accounting(); value.total=4; value.active=2
                C.memmove(pointer,C.byref(value),C.sizeof(value))
                C.cast(returned,C.POINTER(real_api.D))[0]=C.sizeof(value)
                return 1
            assert kind==3 and size==72
            assert C.string_at(pointer,72)==bytes(72)
            assert C.cast(returned,C.POINTER(real_api.D))[0]==0xffffffff
            C.memmove(pointer,raw,72)
            if length is not None: C.cast(returned,C.POINTER(real_api.D))[0]=length
            C.set_last_error(error)
            return ok
        probe=owner._WindowsJobScopeV1(**good)
        probe.api=SimpleNamespace(**vars(real_api)); probe.api.QueryInformationJobObject=injected_query
        probe.handles['job']=99
        if pids is None:
            with pytest.raises((OSError,ValueError)): probe.membership(bracket=True)
        else: probe.membership(bracket=True)
        observed=probe.membership_observation; query=observed['query']
        assert calls==[1,3,1] and query['status']==status and query['raw_hex']==raw.hex()
        assert query['api_return']==ok and query['last_error_raw']==error
        assert query['returned_bytes_raw']==(0xffffffff if length is None else length)
        assert observed['pids']==pids and query['complete']==(status=='complete')
        assert observed['accounting_before']['active']==observed['accounting_after']['active']==2
        assert query['before_ns']<=query['after_ns']<=observed['accounting_after']['before_ns']
        if pids is None: assert observed['assigned'] is observed['listed'] is observed['returned_bytes'] is None
        if pids==(11,22): snapshot({k:observed[k] for k in ('total','active','terminated_by_limit','assigned','listed','pids')},pids)
        elif pids is not None:
            with pytest.raises(ValueError): snapshot({k:observed[k] for k in ('total','active','terminated_by_limit','assigned','listed','pids')},(11,22))
        response_results.append(dict(status=status,raw_preserved=True,parsed_pids=pids,native_execution=False))
    # Receipt-less exceptional streams use the same copier, including byte data
    # that is not valid UTF-8. A secondary failure never replaces the first one.
    precheck=group/'evidence-precheck'; precheck.mkdir()
    source=precheck/'source'; source.mkdir(); target=precheck/'copy'; target.mkdir()
    payloads={'stdout':b'actual\x00output\xff\r\n','stderr':b'actual error\r\n'}
    for label,raw in payloads.items(): (source/('command-1.'+label+'.bin')).write_bytes(raw)
    primary=RuntimeError('injected primary native exception'); errors=[primary]
    copied=retain_streams(source,None,target,errors)
    assert errors==[primary] and all(copied[k]['copied'] for k in payloads)
    for label,raw in payloads.items():
        assert (target/(label+'.bin')).read_bytes()==raw and copied[label]['bytes']==len(raw)
    collision_errors=[primary]
    failed=retain_streams(source,None,target,collision_errors)
    assert collision_errors[0] is primary and len(collision_errors)==3
    assert all(not value['copied'] and value['error'] for value in failed.values())
    assert all((source/('command-1.'+k+'.bin')).read_bytes()==raw for k,raw in payloads.items())
    with pytest.raises(ValueError,match='reporting ceiling'):
        write_diagnostic(precheck/'too-large.json',{'data':'x'*1_048_577})
    assert not (precheck/'too-large.json').exists()
    write_diagnostic(precheck/'record.json',dict(primary=str(primary),streams=copied))
    with pytest.raises(FileExistsError): write_diagnostic(precheck/'record.json',{})
    # Exercise the exact diagnostic helper with injected query-only outcomes;
    # no process, job membership or termination result is represented as native.
    diagnostic_results=[]
    for fault in ('signaled-259','open-denied','pid-mismatch','not-member','image-denied','close-denied','incomplete'):
        closed=[]; opened=[]; queried=[]
        fake=SimpleNamespace(**vars(real_api))
        def fake_open(rights,inherit,pid):
            assert rights==0x00101000 and inherit is False and pid in (22,33,44)
            opened.append(pid)
            if fault=='open-denied' and pid==33: C.set_last_error(5); return 0
            return 1000+pid
        def fake_pid(handle):
            queried.append(('pid',handle))
            return 99 if fault=='pid-mismatch' and handle==1033 else handle-1000
        def fake_member(handle,job,pointer):
            queried.append(('member',handle)); assert job==99
            C.cast(pointer,C.POINTER(real_api.B))[0]=int(not(fault=='not-member' and handle==1033))
            return 1
        def fake_wait(handle,milliseconds):
            queried.append(('wait',handle)); assert milliseconds==0
            return 0 if handle==1033 else 258
        def fake_times(handle,*pointers):
            queried.append(('times',handle)); C.cast(pointers[0],C.POINTER(real_api.FileTime)).contents.low=123+handle
            return 1
        def fake_image(handle,flags,pointer,length):
            queried.append(('image',handle)); assert C.cast(length,C.POINTER(real_api.D))[0]==4096
            if fault=='image-denied' and handle==1033: C.set_last_error(122); return 0
            value='C:\\synthetic-query-only.exe'; C.memmove(pointer,C.create_unicode_buffer(value),(len(value)+1)*2)
            C.cast(length,C.POINTER(real_api.D))[0]=len(value)
            return 1
        def fake_exit(handle,pointer):
            queried.append(('exit',handle)); assert handle==1033
            C.cast(pointer,C.POINTER(real_api.D))[0]=259
            return 1
        def fake_close(handle):
            assert handle!=1011; closed.append(handle)
            if fault=='close-denied' and handle==1033: C.set_last_error(6); return 0
            return 1
        def fake_accounting(handle,kind,pointer,size,length):
            assert handle==99 and kind==1
            value=real_api.Accounting(); value.total=4; value.active=2
            C.memmove(pointer,C.byref(value),size); C.cast(length,C.POINTER(real_api.D))[0]=size
            return 1
        for name,value in dict(OpenProcess=fake_open,GetProcessId=fake_pid,IsProcessInJob=fake_member,
                WaitForSingleObject=fake_wait,GetProcessTimes=fake_times,QueryFullProcessImageNameW=fake_image,
                GetExitCodeProcess=fake_exit,CloseHandle=fake_close,QueryInformationJobObject=fake_accounting).items(): setattr(fake,name,value)
        scope=SimpleNamespace(api=fake,handles={'job':99,'process':1011},process=SimpleNamespace(pid=11),check=lambda:None)
        witness={'state':'failed'}
        observation=dict(query=dict(complete=fault!='incomplete',status='incomplete' if fault=='incomplete' else 'complete'),pids=(11,22,33,44))
        diagnostic_used=False
        result=diagnostic_members(scope,observation,witness)
        assert witness['state']=='failed' and result['attempts']<=96
        assert closed==[1000+pid for pid in opened if not(fault=='open-denied' and pid==33)]
        assert 1011 not in closed
        if fault=='incomplete': assert not opened and result['attempts']==0
        if fault in ('pid-mismatch','not-member'):
            assert not any(operation in ('wait','times','image','exit') and handle==1033 for operation,handle in queried)
        if fault=='signaled-259':
            assert result['observations'][2]['native_exit']==259 and result['observations'][2]['wait_after']==0
            assert result['after_closed_accounting']['active']==2 and witness['state']=='failed'
        if fault=='close-denied': assert result['observations'][2]['closed'] is False and result['errors']
        diagnostic_results.append(dict(fault=fault,attempts=result['attempts'],closed=closed,failed_latch=True,native_execution=False))
    diagnostic_used=False
    with capsys.disabled():
        print('WINDOWS_JOB_MEMBERSHIP_PRECHECKS '+json.dumps(dict(layouts=[24,72],response_checks=response_results,
            receiptless_stream_bytes={key:len(value) for key,value in payloads.items()},
            primary_and_secondary_preserved=True,exclusive_collision_preserved=True,
            oversized_record_rejected=True,diagnostics=diagnostic_results,native_execution=False)),flush=True)

    # Selected inherited settings only. Live accounting counts are not compared.
    def inherited_policy():
        member=real_api.B(); C.set_last_error(0)
        if not real_api.IsProcessInJob(real_api.GetCurrentProcess(),None,C.byref(member)):
            raise owner._windows_job_error_v1('IsProcessInJob:controller',int(C.get_last_error()))
        values={'member':bool(member.value)}
        if member.value:
            for name,kind,cls in (('extended',9,real_api.Extended),('cpu',15,real_api.Cpu)):
                value=cls(); length=real_api.D(); C.set_last_error(0)
                if not real_api.QueryInformationJobObject(None,kind,C.byref(value),C.sizeof(value),C.byref(length)):
                    raise owner._windows_job_error_v1('QueryInformationJobObject:inherited-'+name,int(C.get_last_error()))
                assert length.value==C.sizeof(value)
                values[name]=(dict(flags=int(value.basic.flags),process_time=int(value.basic.process_time),
                    job_time=int(value.basic.job_time),active=int(value.basic.active),process_memory=int(value.process_memory),
                    job_memory=int(value.job_memory)) if kind==9 else dict(flags=int(value.flags),rate=int(value.rate)))
        return values
    before=inherited_policy()
    @contextmanager
    def make_scope(**kw):
        nonlocal count
        count+=1; assert count<=8
        scope=owner._WindowsJobScopeV1(**kw)
        try:
            with owner._windows_job_scope_v1(scope): yield scope
        except BaseException:
            with capsys.disabled():
                print('WINDOWS_JOB_NATIVE_FAILURE '+json.dumps(dict(windows_job=scope.projection(),
                    native_errors=scope.native_errors,history=scope.history,successful_job_handle_created='job' in scope.close_attempts or bool(scope.handles.get('job')))),flush=True)
            raise
    def check_job(receipt,actual):
        job=actual['windows_job']
        assert job==receipt.output_observation['windows_job']
        assert set(job)=={'kind','configured','queried','creation','terminal','handle_close_errors'}
        assert job['kind']=='WINDOWS_JOB_RESOURCE_ONLY_V1' and job['configured']==job['queried']
        assert job['configured']==dict(limit_flags=0x2308,active_process_limit=job['configured']['active_process_limit'],
            process_commit_bytes=268435456,job_commit_bytes=536870912,cpu_flags=5,cpu_rate_10000=2000)
        assert job['creation']['pid']==receipt.pid and job['creation']['creation_filetime_100ns']>0
        assert type(job['creation']['creation_flags']) is int and job['creation']['creation_flags']==0x0008060C
        assert job['creation']['membership_verified_before_resume'] is True and job['creation']['resume_previous_count']==1
        assert job['terminal']['root_exit']==receipt.native_exit_code
        assert job['terminal']['active_processes']==0 and job['terminal']['process_ids']==[]
        assert job['terminal']['empty_verified'] is True and job['handle_close_errors']==[]
        assert all(job['terminal'][key] is True for key in ('job_handle_closed','process_handle_closed','primary_thread_handle_closed'))
        assert not owner._command_requires_process_retention_v1(receipt)
    def lifecycle_body():
        nonlocal last_diagnostic
        import traceback
        worker=retained/'held-pair.py'
        worker.write_text(worker_source,encoding='utf-8')
        cases=[]
        def native_snapshot(scope):
            value=dict(scope.membership_observation)
            assert value['query']['complete'] is True
            for key in ('total','active','terminated_by_limit','assigned','listed','returned_bytes'): dword(value[key])
            return value
        def semantic_snapshot(value):
            return {key:value[key] for key in ('total','active','terminated_by_limit','assigned','listed','pids')}
        def checked_pair(path,before):
            identity=owner._scan_file_identity(before)
            assert before.st_size<=4096
            fd=owner._open_regular_worktree_descriptor(path,nonblocking=True)
            try:
                opened=os.fstat(fd)
                assert owner._scan_file_identity(opened)==identity
                raw=os.read(fd,4097)
                assert len(raw)==before.st_size and len(raw)<=4096
                assert owner._scan_same_api_version(os.fstat(fd))==owner._scan_same_api_version(opened)
                assert owner._scan_same_api_version(path.lstat())==owner._scan_same_api_version(before)
            finally: os.close(fd)
            def pairs(items):
                result={}
                for key,value in items:
                    if key in result: raise ValueError('duplicate synchronized pair field')
                    result[key]=value
                return result
            result=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs)
            assert type(result) is dict and set(result)=={'root_pid','root_creation_filetime_100ns',
                'child_pid','child_creation_filetime_100ns','popen_events','createprocess_events'}
            assert all(type(v) is int and 0<v<=(0xffffffffffffffff if 'filetime' in k else U32) for k,v in result.items())
            assert result['popen_events']==result['createprocess_events']==1
            return result,dict(bytes=len(raw),path=str(path),generation=identity,complete_utf8=raw.decode('utf-8'))
        def publish_release(case_root):
            path=case_root/'release.bin'; temporary=case_root/'.release.bin.pending'
            assert not os.path.lexists(path) and not os.path.lexists(temporary)
            with temporary.open('xb') as stream:
                assert stream.write(b'RELEASE\n')==8
                stream.flush(); os.fsync(stream.fileno())
            os.rename(temporary,path)  # Windows: atomic publication, never replace an existing file.
            owner._fsync_directory(case_root)
            return dict(path=str(path),bytes=8,write_once=True)
        for case,cap,mode,seconds in (('process-cap-2',2,'normal',60),('process-cap-1',1,'normal',60),
                ('whole-job-timeout',2,'timeout',5)):
            case_root=retained/case; case_root.mkdir()
            evidence=case_root/'evidence'; evidence.mkdir()
            copies=case_root/'retained-streams'; copies.mkdir()
            for name in ('child-ready.json','pair-ready.json','release.bin'):
                assert not os.path.lexists(case_root/name)
            end,settle=fresh_deadline(seconds)
            argv=(sys.executable,'-I','-B','-X','utf8',str(worker),str(REPO_ROOT),str(case_root),
                mode,str(end),str(settle),'root')
            kw=operands(argv,case_root,evidence,case,1,end,settle,cap)
            actual={}; receipt=None; scope=None; child_handle=None; hook_error=None; errors=[]
            retained_streams={}; stdout=None; stderr=None; result=None
            witness=dict(state='waiting',readiness_checks=0,ready_reads=0,native_call_slots_reserved=0,
                native_calls=[],snapshots=[],handle_close_errors=[],release=None,child_settlement=None,
                lifetime_attribution='not_established',historical_process_trace_complete=False)
            last_check=0
            def reserve(count):
                # Keep the adopted 32-call allowance: five worker queries
                # plus at most 27 controller calls. Earlier fixed setup/cleanup
                # keeps its original bounds; each bracket now charges three.
                assert witness['native_call_slots_reserved']+count<=27
                witness['native_call_slots_reserved']+=count
            def query(name,*args,settling=False):
                nonlocal child_handle
                scope.check(settling=settling); reserve(1); C.set_last_error(0)
                value=getattr(scope.api,name)(*args)
                number=int(value or 0)
                error=int(C.get_last_error()) if (number==0xffffffff if name=='WaitForSingleObject' else not number) else 0
                witness['native_calls'].append(dict(operation=name,result=number,error=error))
                if (number==0xffffffff if name=='WaitForSingleObject' else not number):
                    raise owner._windows_job_error_v1(name,error)
                if name=='OpenProcess':
                    child_handle=number; witness['child_handle']=number
                scope.check(settling=settling)
                return number
            def stamp(handle,settling=False):
                values=[scope.api.FileTime() for _ in range(4)]
                query('GetProcessTimes',handle,*(C.byref(value) for value in values),settling=settling)
                value=(int(values[0].high)<<32)|int(values[0].low)
                assert value>0
                return value
            def take_snapshot(label):
                reserve(3)
                try:
                    try:
                        scope.membership(bracket=True)
                    finally:
                        witness['snapshots'].append(dict(label=label,raw=None if scope.membership_observation is None
                            else dict(scope.membership_observation)))
                    value=native_snapshot(scope)
                    snapshot(semantic_snapshot(value),(scope.process.pid,witness['ready']['child_pid']))
                    after=value['accounting_after']; before=value['accounting_before']
                    if after is None or before['active']!=2 or after['active']!=2:
                        raise ValueError('held pair accounting bracket is not exactly two')
                    if not before['total']<=after['total'] or after['total']<2:
                        raise ValueError('held pair lifetime accounting decreased or fell below two')
                    return value
                except BaseException:
                    witness['state']='failed'
                    if not diagnostic_used:
                        try: diagnostic_members(scope,scope.membership_observation or {},witness)
                        except BaseException as error:
                            witness['diagnostic_secondary_error']=render_error(error)
                    raise
            def identity(handle,pid,creation):
                actual_pid=query('GetProcessId',handle); actual_creation=stamp(handle)
                image=C.create_unicode_buffer(32768); capacity=scope.api.D(32768)
                query('QueryFullProcessImageNameW',handle,0,image,C.byref(capacity))
                assert 0<capacity.value<32768
                member=scope.api.B()
                query('IsProcessInJob',handle,scope.handles['job'],C.byref(member))
                wait=query('WaitForSingleObject',handle,0)
                value=dict(handle=int(handle),pid=actual_pid,creation_filetime_100ns=actual_creation,
                    image=image[:capacity.value],explicit_job_member=int(member.value),wait_result=wait)
                witness.setdefault('identities',[]).append(value)
                assert actual_pid==pid and actual_creation==creation and member.value==1 and wait==258
                assert owner._lexical_path_key(Path(value['image']))==owner._lexical_path_key(Path(sys.executable))
                return value
            def observer(process):
                nonlocal child_handle,hook_error,last_check
                result=original_poll(process)  # Always invoke the genuine poll; never replace its result.
                if process is not scope.process: return result
                if result is not None: witness['root_native_poll_result']=result
                if witness['state'] in ('checking','verified','failed'): return result
                now=time.monotonic_ns()
                if now-last_check<10_000_000: return result
                last_check=now
                try:
                    scope.check(); witness['readiness_checks']+=1
                    assert witness['readiness_checks']<=3000
                    path=case_root/'pair-ready.json'
                    try: before=path.lstat()
                    except FileNotFoundError:
                        if result is not None: raise RuntimeError('root exited before synchronized pair readiness')
                        return result
                    witness['state']='checking'
                    ready,read_record=checked_pair(path,before); witness['ready_reads']+=1
                    witness['ready']=ready; witness['ready_file']=read_record
                    assert witness['ready_reads']==1 and result is None
                    root_handle=scope.handles['process']; root_pid=scope.process.pid
                    root_stamp=scope.creation['creation_filetime_100ns']
                    assert query('GetProcessId',root_handle)==root_pid==ready['root_pid']
                    assert stamp(root_handle)==root_stamp==ready['root_creation_filetime_100ns']
                    first=take_snapshot('held-first')
                    snapshot(semantic_snapshot(first),(root_pid,ready['child_pid']))
                    assert root_pid!=ready['child_pid']
                    child_handle=query('OpenProcess',0x00101000,False,ready['child_pid'])
                    witness['child_handle']=child_handle
                    flags=scope.api.D(); query('GetHandleInformation',child_handle,C.byref(flags))
                    witness['child_handle_flags']=int(flags.value); assert not flags.value&1
                    root_identity=identity(root_handle,root_pid,root_stamp)
                    child_identity=identity(child_handle,ready['child_pid'],ready['child_creation_filetime_100ns'])
                    last=take_snapshot('held-last')
                    snapshot(semantic_snapshot(last),(root_pid,ready['child_pid']))
                    rechecks=[]
                    for handle,expected in ((root_handle,root_stamp),(child_handle,ready['child_creation_filetime_100ns'])):
                        current=stamp(handle); wait=query('WaitForSingleObject',handle,0)
                        rechecks.append(dict(handle=int(handle),creation_filetime_100ns=current,wait_result=wait))
                        assert current==expected and wait==258
                    witness['identity_rechecks']=rechecks
                    totals=[scope.configured_membership['total'],scope.creation_membership['total'],first['total'],last['total']]
                    assert all(b>=a for a,b in zip(totals,totals[1:]))
                    witness['state']='verified'
                    if mode=='normal': witness['release']=publish_release(case_root)
                except BaseException as error:
                    hook_error=error; witness['state']='failed'
                    witness['error']=str(error); witness['complete_exception']=''.join(traceback.format_exception(error))
                    raise
                return result
            try:
                with make_scope(**kw) as scope:
                    original_poll=owner._WindowsJobProcessV1.poll
                    with monkeypatch.context() as observe_patch:
                        if cap==2: observe_patch.setattr(owner._WindowsJobProcessV1,'poll',observer)
                        receipt=owner.supervise_command(argv,cwd=case_root,run_id=kw['run_id'],phase=kw['phase'],
                            command_index=1,evidence_root=evidence,environment=environment,execution_deadline_ns=end,
                            output_limits=bounds,output_observation=actual,mirror_stdout=False,mirror_stderr=False)
                    check_job(receipt,actual)
            except BaseException as error:
                errors.append(error)
            finally:
                if child_handle is not None:
                    try:
                        wait=query('WaitForSingleObject',child_handle,min(10000,max(0,(settle-time.monotonic_ns())//1_000_000)),settling=True)
                        assert wait==0,'query-held descendant not signaled at settlement'
                        exit_code=scope.api.D(); query('GetExitCodeProcess',child_handle,C.byref(exit_code),settling=True)
                        witness['child_settlement']=dict(handle=int(child_handle),wait_result=wait,native_exit=int(exit_code.value))
                    except BaseException as error: errors.append(error)
                    finally:
                        try:
                            C.set_last_error(0)
                            if not scope.api.CloseHandle(child_handle):
                                raise owner._windows_job_error_v1('CloseHandle:query-child',int(C.get_last_error()))
                            witness['query_child_handle_closed']=True
                        except BaseException as error:
                            witness['handle_close_errors'].append(dict(operation='CloseHandle:query-child',error=getattr(error,'winerror',None)))
                            errors.append(error)
                if hook_error is not None and all(error is not hook_error for error in errors): errors.append(hook_error)
                # Guaranteed exceptional path; original evidence is already
                # outside the wrapper root and survives any failed copy/encoding.
                retained_streams=retain_streams(evidence,receipt,copies,errors)
                stdout=retained_streams['stdout']['complete_utf8']; stderr=retained_streams['stderr']['complete_utf8']
            final_membership=None if scope is None else scope.membership_observation
            result=dict(case=case,argv=argv,cwd=str(case_root),native_exit=None if receipt is None else receipt.native_exit_code,
                failure_class=None if receipt is None else receipt.failure_class,complete_stdout=stdout,complete_stderr=stderr,
                retained_streams=retained_streams,original_evidence_root=str(evidence),
                original_evidence_retained_outside_disposable_root=True,
                windows_job=None if scope is None else scope.projection(),witness=witness,
                configured_empty=None if scope is None else scope.configured_membership,
                suspended_membership=None if scope is None else scope.creation_membership,
                suspended_identity=None if scope is None else scope.creation_identity,terminal_membership=final_membership,
                root_wait_result=None if scope is None or scope.process is None else scope.process.last_wait_result,
                errors=[''.join(traceback.format_exception(error)) for error in errors],
                lifetime_attribution='not_established',historical_process_trace_complete=False)
            last_diagnostic=result
            with capsys.disabled(): print('WINDOWS_JOB_HELD_PAIR_NATIVE '+json.dumps(result),flush=True)
            if errors: owner._scan_raise_errors(errors)
            assert receipt is not None and scope.process.last_wait_result==0
            launch_records=[json.loads(line) for line in stdout.splitlines() if line.startswith('{')]
            descendant_flags=[value['descendant_creation_flags'] for value in launch_records if 'descendant_creation_flags' in value]
            assert descendant_flags and all(type(value) is int and value==0x00000208 for value in descendant_flags)
            result['descendant_creation_flags']=descendant_flags
            snapshot(semantic_snapshot(scope.configured_membership),())
            snapshot(semantic_snapshot(scope.creation_membership),(receipt.pid,))
            snapshot(semantic_snapshot(final_membership),())
            totals=[scope.configured_membership['total'],scope.creation_membership['total'],final_membership['total']]
            assert all(b>=a for a,b in zip(totals,totals[1:]))
            if cap==1:
                outcome=json.loads(stdout.splitlines()[-1])
                assert receipt.native_exit_code==2 and receipt.failure_class=='ENGVR_NATIVE_EXIT_NONZERO'
                assert outcome['root_pid']==receipt.pid and outcome['creation_audit_counts']=={'subprocess.Popen':1,'_winapi.CreateProcess':1}
                assert type(outcome['create_error']) is dict or (type(outcome['child_returncode']) is int and outcome['child_returncode']!=0)
                assert 'OWNED_DESCENDANT_STARTED' not in stdout and child_handle is None
                assert all(not os.path.lexists(case_root/name) for name in ('child-ready.json','pair-ready.json','release.bin'))
            else:
                assert witness['state']=='verified' and witness['query_child_handle_closed'] is True
                ready=witness['ready']; identities=witness['identities']; rechecks=witness['identity_rechecks']
                reference=dict(root_pid=receipt.pid,child_pid=ready['child_pid'],
                    before=semantic_snapshot(scope.creation_membership),held_first=semantic_snapshot(witness['snapshots'][0]['raw']),
                    held_last=semantic_snapshot(witness['snapshots'][1]['raw']),after=semantic_snapshot(final_membership),
                    root_handle_verified=identities[0]['pid']==receipt.pid and identities[0]['explicit_job_member']==1,
                    child_handle_verified=identities[1]['pid']==ready['child_pid'] and identities[1]['explicit_job_member']==1,
                    root_live_at_barrier=identities[0]['wait_result']==rechecks[0]['wait_result']==258,
                    child_live_at_barrier=identities[1]['wait_result']==rechecks[1]['wait_result']==258,
                    creation_identities_match=all(a['creation_filetime_100ns']==b['creation_filetime_100ns'] for a,b in zip(identities,rechecks)),
                    image_matches=all(owner._lexical_path_key(Path(v['image']))==owner._lexical_path_key(Path(sys.executable)) for v in identities),
                    root_signaled=scope.process.last_wait_result==0,child_signaled=witness['child_settlement']['wait_result']==0,
                    configured_cap=scope.configured['active_process_limit'],cap_readback=scope.queried['active_process_limit'],
                    handle_close_errors=tuple(witness['handle_close_errors']))
                result['resource_oracle']=pair_reference(reference)
                assert witness['native_call_slots_reserved']<=27 and witness['readiness_checks']<=3000
                if mode=='normal':
                    outcome=json.loads(stdout.splitlines()[-1])
                    assert receipt.native_exit_code==0 and receipt.failure_class is None and witness['child_settlement']['native_exit']==0
                    assert outcome['child_returncode']==0 and outcome['child_pid']==ready['child_pid'] and outcome['create_error'] is None
                    assert outcome['worker_child_handle_closed'] is True and outcome['worker_identity_queries']==4
                    assert outcome['worker_ready_checks']+witness['readiness_checks']<=6000
                    assert witness['release'] is not None and 'OWNED_DESCENDANT_STARTED' in stdout
                else:
                    assert receipt.failure_class=='ENGVR_PROCESS_TIMEOUT' and receipt.timeout_state=='TRIGGERED'
                    assert actual['windows_job']['terminal']['termination_attempted'] is True
                    assert 'OWNED_SLEEPING_DESCENDANT' in stdout and 'OWNED_SLEEPING_PARENT' in stdout
                    assert witness['release'] is None and not os.path.lexists(case_root/'release.bin')
            cases.append(result)
        end,settle=fresh_deadline(); evidence=group/'native-last-close'; evidence.mkdir()
        argv=(sys.executable,'-I','-B','-X','utf8','-c','print("MUST_NOT_BE_RESUMED")')
        kw=operands(argv,group,evidence,'native-last-close',1,end,settle,1)
        with make_scope(**kw) as scope:
            scope.match(run_id=kw['run_id'],phase=kw['phase'],command_index=1,argv=argv,cwd=group,
                evidence_root=evidence,environment=environment,execution_deadline_ns=end)
            process=scope.create_suspended(subprocess.DEVNULL)
            scope.verify_created()
            projection=scope.close_suspended_backstop()
            assert process.poll() is not None and projection['creation']['resume_previous_count'] is None
            assert projection['creation']['membership_verified_before_resume'] is True and scope.final_close_test
            assert type(projection['creation']['creation_flags']) is int and projection['creation']['creation_flags']==0x0008060C
            assert projection['terminal']['termination_attempted'] is False
            assert all(projection['terminal'][k] for k in ('job_handle_closed','process_handle_closed','primary_thread_handle_closed'))
            # No running application or independent collector: reuse the original finite drain.
            stdout_path=evidence/'stdout.bin'; stderr_path=evidence/'stderr.bin'
            out=stdout_path.open('xb'); err=stderr_path.open('xb')
            outcomes=[dict(drained_byte_count=0,retained_byte_count=0,retention_limit=16384,
                cleanup_drained_byte_count=0,evidence_write_enabled=True,mirror=None) for _ in range(2)]
            terminal=owner._supervise_native_output(process,stdout_stream=out,stderr_stream=err,
                stdout_outcome=outcomes[0],stderr_outcome=outcomes[1],started_monotonic=time.monotonic(),
                timeout_seconds=min(10,(settle-time.monotonic_ns())/1e9),termination_grace_seconds=1,platform_name=os.name)
            assert stdout_path.read_bytes()==stderr_path.read_bytes()==b''
            cases.append(dict(case='final-handle-close-not-application-success',argv=argv,native_exit=process.returncode,
                complete_stdout='',complete_stderr='',windows_job=projection,history=scope.history,
                configured_empty=scope.configured_membership,suspended_membership=scope.creation_membership,
                suspended_identity=scope.creation_identity,final_close_test=True,root_signaled=True,
                lifetime_attribution='not_established'))
        assert count==6
        assert len(cases)==4
        with capsys.disabled():
            print('WINDOWS_JOB_NATIVE_LIFECYCLE '+json.dumps(dict(cases=cases,successful_new_jobs=count,
                memory_cpu_stress_run=False,full_host_qualified=False,canonical_execution=False)),flush=True)
        return cases
    def lifecycle():
        errors=[]; after=None; cases=None; record=None
        try:
            cases=lifecycle_body()
        except BaseException as error:
            errors.append(error)
        finally:
            # A failed witness must also reach this selected policy after-read.
            try:
                if time.monotonic_ns()>=settlement: raise TimeoutError('inherited-policy after-read settlement cutoff')
                after=inherited_policy()
                if after!=before: raise ValueError('selected inherited job policy changed')
            except BaseException as error: errors.append(error)
            value=dict(last_case=last_diagnostic,completed_cases=cases,inherited_before=before,inherited_after=after,
                inherited_selected_policy_equal=None if after is None else after==before,
                primary_and_secondary_errors=[render_error(error) for error in errors],
                buffer_capacity=8,buffer_bytes=72,paired_execution_cap=2,
                full_host_qualified=False,canonical_execution=False,attribution='not_established')
            try:
                record=write_diagnostic(retained/'membership-diagnostic.json',value)
            except BaseException as error:
                errors.append(error)
            with capsys.disabled():
                print('WINDOWS_JOB_DIAGNOSTIC_SETTLEMENT '+json.dumps(dict(record=record,
                    retained_source_root=str(retained),source_root_preserved=True,inherited_before=before,
                    inherited_after=after,inherited_selected_policy_equal=None if after is None else after==before,
                    errors=[render_error(error) for error in errors])),flush=True)
        if errors: owner._scan_raise_errors(errors)
    return make_scope,check_job,lifecycle
def _exercise_preflight_transport_v1(tmp_path, monkeypatch, capsys):
    """Synthetic engineering: real original CLI children, no canonical host grant."""
    import copy
    import json
    import os
    import struct
    import sys
    import time
    import pytest
    from tools import validation_reliability as owner
    from tools import run_validation_gates as runner
    root = Path(owner.__file__).resolve().parents[1]
    area = tmp_path/'preflight-transport'
    area.mkdir()
    process_root, evidence_root = area/'process',area/'evidence'
    process_root.mkdir(); evidence_root.mkdir()
    run_id = 'synthetic-preflight-transport'
    deadline = time.monotonic_ns()+120_000_000_000
    settlement = deadline+30_000_000_000
    # Optional engineering caps only shorten this helper's existing window;
    # they never supply a native lease or enter the five transport controls.
    caps = tuple(os.environ.get(key) for key in ('QTT_TEST_EXECUTION_CUTOFF_NS','QTT_TEST_SETTLEMENT_CUTOFF_NS'))
    if any(value is not None for value in caps):
        assert all(type(value) is str and value.isascii() and value.isdecimal() for value in caps)
        deadline = min(deadline,int(caps[0]))
        settlement = min(deadline+30_000_000_000,int(caps[1]))
        assert time.monotonic_ns() < deadline < settlement
    job_scope,check_job,job_lifecycle = _exercise_windows_job_resource_v1(area,monkeypatch,capsys,deadline,settlement)
    transport = dict(frame_byte_limit=2_000_000,header_byte_limit=100_000,lexical_units=100_000,
        depth=32,quoted_bytes=100_000,read_calls=10000,write_calls=10000,chunk_bytes=97,
        retained_buffer_bytes=8_000_000,receiver_byte_limit=20000)
    zero = dict.fromkeys(owner._PREFLIGHT_DIMENSIONS_V1,0)
    limits = dict(zero,attempts=20,bytes=40,entries=30,retained_bytes=50)
    tail = dict(zero,attempts=2,bytes=3,entries=4,retained_bytes=5)
    class SyntheticLease(owner._PreflightHostLeaseV1):
        def __init__(self, *, fixture_root=root, fixture_process_root=process_root, fixture_run_id=run_id, fixture_deadline=deadline):
            self.calls=[]
            self.deadline=fixture_deadline
            self.root, self.process_root, self.run_id = fixture_root, fixture_process_root, fixture_run_id
        def check_parent(self, root, index_path):
            assert root == self.root
            assert index_path is None
            self.calls.append('parent')
        def check_launch(self, entry, argv, environment, scratch_roots, deadline_ns):
            assert tuple(argv) == entry.argv and owner._preflight_vector_v1(tuple(argv))
            assert deadline_ns == self.deadline and scratch_roots == (self.process_root,)
            assert entry.cwd == str(self.root)
            assert environment[owner.RUN_ID_ENV] == self.run_id
            self.calls.append('launch')
        def check_child(self, process):
            assert type(process.pid) is int and process.pid != os.getpid()
            self.calls.append(('child',process.pid))
        def check_settled(self, process):
            assert process.poll() is not None
            self.calls.append(('settled',process.pid))
    lease = SyntheticLease()
    parent_meter = owner._PreflightTransportV1(transport,settlement)
    def identity(n):
        argv = (sys.executable,str(Path(owner._PREFLIGHT_SCRIPTS_V1[n-1])),*(('--repo-root','.') if n != 6 else ()))
        return dict(run_id=run_id,phase='fast-preflight',command_index=n,original_position=n,command_count=8,
            argv=list(argv),repo_root=str(root),process_root=str(process_root),evidence_root=str(evidence_root),parent_pid=os.getpid())
    def header(n):
        return dict(identity=identity(n),allowance=dict(limits),deadline_ns=deadline,
            git=dict(executable=None,evidence_root=None),files=[['a.bin',0,3],['z.bin',3,0]],
            directories=[['.',[['a.bin','file'],['z.bin','file']]]])
    # Every original vector is projected and decoded without editing its argv.
    for n in range(1,9):
        h = header(n)
        owner._preflight_header_v1(h,3,identity(n))
        raw = owner._preflight_canonical_v1(h)
        decoded,_ = owner._preflight_json_v1(raw,transport,parent_meter.check)
        assert decoded == h
    valid = header(2)
    bad_headers = []
    for field,value in (('run_id','wrong'),('phase','later'),('command_index',True),('parent_pid',0),
            ('repo_root',str(process_root)),('argv',[sys.executable,'tools/other.py'])):
        bad=copy.deepcopy(valid); bad['identity'][field]=value; bad_headers.append(bad)
    for key,value in (('deadline_ns',True),('extra',1)):
        bad=copy.deepcopy(valid); bad[key]=value; bad_headers.append(bad)
    for mutate in (
        lambda h:h['files'][1].__setitem__(1,2),
        lambda h:h['files'][0].__setitem__(0,'../a.bin'),
        lambda h:h['files'][1].__setitem__(0,'A.BIN'),
        lambda h:h['directories'][0][1][0].__setitem__(1,'directory'),
        lambda h:h['allowance'].__setitem__('entries',0),
        lambda h:h['allowance'].__setitem__('retained_bytes',2),
        lambda h:h['git'].__setitem__('executable',sys.executable)):
        bad=copy.deepcopy(valid); mutate(bad); assert bad != valid; bad_headers.append(bad)
    for bad in bad_headers:
        with pytest.raises((ValueError,RuntimeError)):
            owner._preflight_header_v1(bad,3,identity(2))
    no_entries=copy.deepcopy(valid); no_entries['allowance']['entries']=0
    with monkeypatch.context() as scoped:
        scoped.setattr(owner,'_preflight_rosters_v1',lambda *a,**k:pytest.fail('index constructed before admission'))
        with pytest.raises(RuntimeError,match='decoded basis allowance'):
            owner._preflight_header_v1(no_entries,3,identity(2))
    oversized=copy.deepcopy(valid); oversized['identity']['run_id']='x'*1025
    with monkeypatch.context() as scoped:
        scoped.setattr(owner.json.JSONEncoder,'iterencode',lambda *a,**k:pytest.fail('header allocated before bound'))
        with pytest.raises(RuntimeError,match='header emission capacity'):
            owner._preflight_encode_header_v1(oversized,dict(transport,header_byte_limit=1024),
                parent_meter.check,parent_meter.buffers)
    raw = owner._preflight_canonical_v1(valid)
    duplicate = b'{"deadline_ns":1,'+raw[1:]
    for raw_bad,match in ((duplicate,'duplicate'),(raw+b'\n','noncanonical'),
            (b'{"x":1e2}','noninteger'),(b'{"x":-1}','integer token'),
            (b'{"x":NaN}','noninteger'),(b'{"x":"\\ud800"}','surrogate')):
        with pytest.raises((ValueError,RuntimeError),match=match):
            owner._preflight_json_v1(raw_bad,transport,parent_meter.check)
    for key,bound in (('depth',1),('lexical_units',1),('quoted_bytes',1)):
        with pytest.raises(RuntimeError,match='capacity'):
            owner._preflight_json_v1(raw,dict(transport,**{key:bound}),parent_meter.check)
    frame = struct.pack('>8sQQ',b'QTTPF01\n',len(raw),3)+raw+b'abc'
    def decode(data, *, shape=None, patch=None):
        path=area/('wire-'+str(len(list(area.glob('wire-*'))))+'.bin')
        path.write_bytes(data)
        fd=os.open(path,os.O_RDONLY|int(getattr(os,'O_BINARY',0)))
        meter=owner._PreflightTransportV1(transport,deadline)
        def validate(h,p):
            d,c=owner._preflight_header_v1(h,p,identity(2))
            return [row[2] for row in h['files']],(d,c)
        try:
            with monkeypatch.context() as scoped:
                if patch:
                    real=owner.os.read
                    scoped.setattr(owner.os,'read',lambda handle,size: real(handle,min(size,patch)))
                return owner._preflight_frame_read_v1(fd,magic=b'QTTPF01\n',extent=len(data) if shape is None else shape,
                    meter=meter,validate=validate)
        finally: os.close(fd)
    for fragment in (1,2,7,31):
        decoded,body,(_dirs,count)=decode(frame,patch=fragment)
        assert body == [b'abc',b''] and decoded == valid and count == 5
    for bad in (frame[:-1],frame+b'x',b'QTTPA01\n'+frame[8:],frame+frame):
        with pytest.raises((ValueError,RuntimeError)):
            decode(bad)
    # The shared adapter preserves unselected main semantics and rejects partial controls before stdin.
    with monkeypatch.context() as scoped:
        for key in tuple(os.environ):
            if key.upper().startswith('QTT_'): scoped.delenv(key,raising=False)
        calls=[]
        assert owner._preflight_cli_v1(lambda:(calls.append(1) or 7),__file__) == 7 and calls == [1]
        scoped.setenv('QTT_PREFLIGHT_INPUT_BYTES','10')
        with pytest.raises(RuntimeError,match='partial'):
            owner._preflight_cli_v1(lambda:pytest.fail('entered without input'),__file__)
    # No JSON Boolean or pathname can supply the absent native host owner.
    with pytest.raises(RuntimeError,match='NATIVE_HOST_PROVIDER_UNAVAILABLE'):
        owner._preflight_acquire_native_input_v1(area/'declaration.bin',root)
    with pytest.raises(RuntimeError,match='NATIVE_HOST_PROVIDER_UNAVAILABLE'):
        owner._PreflightHostLeaseV1().check_parent(root,None)
    for args in (['--phase','all'],['--phase','fast-preflight','--validation-mode','reduced']):
        with pytest.raises(ValueError,match='full first phase'):
            runner.main([*args,'--preflight-input',str(area/'declaration.bin')])
    with pytest.raises(ValueError,match='competing suppliers'):
        runner.main(['--phase','fast-preflight','--preflight-input',str(area/'declaration.bin')],candidate_source=lambda *a:None)
    # Independent complete-ledger references are pure verification cases, not
    # native executions or grants. Real byte-consuming CLI cases follow below.
    from types import SimpleNamespace
    accounting_area=area/'accounting'; accounting_area.mkdir()
    accounting_process=accounting_area/'process'; accounting_process.mkdir()
    accounting_meter=owner._PreflightTransportV1(transport,settlement)
    reference_initial=dict.fromkeys(zero,100)
    reference_initial['combined_output_bytes']=200  # Separate streams have a valid combined cap.
    reference_count=mutation_count=0
    def reference_result(basis, observed, exit_code):
        reserved=dict(zero,attempts=observed['attempts'],git_attempts=observed['git_attempts'],
            entries=basis['entries'],retained_bytes=basis['bytes']+observed['retained_bytes'])
        debit=dict(observed)
        debit['entries']+=basis['entries']; debit['retained_bytes']+=basis['bytes']
        return dict(run_id=run_id,phase='fast-preflight',command_index=2,original_position=2,
            argv=accounting_identity['argv'],cwd=str(root),pid=12345,parent_pid=os.getpid(),
            input_bytes_consumed=999,decode_complete=True,application_entered=True,application_exit=exit_code,
            observation_complete=True,failure_class=None if exit_code==0 else 'PREFLIGHT_APPLICATION_DENIED',
            initial_limits=dict(reference_initial),remaining_limits={k:reference_initial[k]-debit[k] for k in zero},
            observed=dict(observed),reserved=reserved,retained_entries=debit['entries'])
    def reference_receipt(value,basis):
        return SimpleNamespace(fixed_environment_controls=tuple(zip(owner._PREFLIGHT_INPUT_KEYS_V1,
            ('999','900','10000,32,10000,10000,97','2',str(deadline)))),
            output_observation=dict(preflight=dict(identity=accounting_identity,initial_limits=reference_initial,
                input_bytes=999,receiver=value,row_total=reference_initial,parent_spend=dict(zero),
                parent_tail=dict(zero),basis_counts=basis)),phase='fast-preflight',command_index=2,
            argv=tuple(accounting_identity['argv']),cwd=str(root),pid=12345,native_exit_code=value['application_exit'])
    def verify_reference(value,basis):
        owner._preflight_verify_result_v1(value,identity=accounting_identity,initial=reference_initial,
            extent=999,pid=12345,native_exit=value['application_exit'],basis_counts=basis)
    def reject_reference(value,basis,original,original_basis,match='preflight receiver|preflight exact integer|preflight exact object|preflight copied/changed initial allowance'):
        nonlocal mutation_count
        # JSON distinguishes Boolean/float substitutions even where Python == does not.
        assert json.dumps([value,basis],sort_keys=True) != json.dumps([original,original_basis],sort_keys=True)
        with pytest.raises(RuntimeError,match=match): verify_reference(value,basis)
        with pytest.raises(RuntimeError,match=match):
            owner._preflight_command_evidence_v1(reference_receipt(value,basis),accounting_paths,accounting_meter)
        mutation_count+=1
    scenarios=(
        ('zero-work',dict(entries=0,bytes=0),dict(zero)),
        ('nonempty-basis',dict(entries=5,bytes=3),dict(zero)),
        ('zero-length-file',dict(entries=1,bytes=0),dict(zero,attempts=1)),
        ('repeated-file-acquisition',dict(entries=5,bytes=3),dict(zero,attempts=2,bytes=6,retained_bytes=6)),
        ('directory-delivery',dict(entries=4,bytes=0),dict(zero,attempts=1,entries=3)),
        ('Git-stream-evidence-readback',dict(entries=0,bytes=0),
            dict(zero,attempts=2,git_attempts=1,bytes=7,retained_bytes=7,
                stdout_bytes=4,stderr_bytes=3,combined_output_bytes=7)),
    )
    for case,basis,observed in scenarios:
        for exit_code in (0,1,2):
            accounting_evidence=accounting_area/(case+'-'+str(exit_code)); accounting_evidence.mkdir()
            accounting_result=accounting_evidence/'preflight-2'; accounting_result.mkdir()
            accounting_identity=dict(identity(2),process_root=str(accounting_process),evidence_root=str(accounting_evidence))
            accounting_paths=SimpleNamespace(run_id=run_id,repo_root=root,process_root=accounting_process,
                evidence_root=accounting_evidence)
            original=reference_result(basis,observed,exit_code)
            verify_reference(original,basis)
            owner.atomic_write_json(accounting_result/'receiver.json',original)
            owner._preflight_command_evidence_v1(reference_receipt(original,basis),accounting_paths,accounting_meter)
            reference_count+=1
            # All eight independently changed remaining dimensions must reject,
            # including shared attempt views which must not be added together.
            for key in zero:
                bad=copy.deepcopy(original); bad['remaining_limits'][key]-=1
                reject_reference(bad,basis,original,basis,match='preflight receiver exact')
            for ledger in ('observed','reserved'):
                for key in zero:
                    bad=copy.deepcopy(original)
                    bad[ledger][key]+=(-1 if bad[ledger][key] else 1)
                    reject_reference(bad,basis,original,basis)
            bad=copy.deepcopy(original)
            bad['retained_entries']+=(-1 if bad['retained_entries'] else 1)
            reject_reference(bad,basis,original,basis)
            for key in ('entries','bytes'):
                wrong=dict(basis); wrong[key]+=1
                reject_reference(original,wrong,original,basis)
            for ledger in ('initial_limits','remaining_limits','observed','reserved'):
                for key in zero:
                    for scalar in (False,float(original[ledger][key]),-1,1<<63):
                        bad=copy.deepcopy(original); bad[ledger][key]=scalar
                        reject_reference(bad,basis,original,basis)
                for extra in (False,True):
                    bad=copy.deepcopy(original)
                    if extra: bad[ledger]['extra']=0
                    else: del bad[ledger]['attempts']
                    reject_reference(bad,basis,original,basis)
            for key in ('entries','bytes'):
                for scalar in (False,float(basis[key]),-1,1<<63):
                    wrong=dict(basis); wrong[key]=scalar
                    reject_reference(original,wrong,original,basis)
            for wrong in ({},dict(basis,extra=0),{'entries':basis['entries']},None):
                reject_reference(original,wrong,original,basis)
            for scalar in (False,float(original['retained_entries']),-1,1<<63):
                bad=copy.deepcopy(original); bad['retained_entries']=scalar
                reject_reference(bad,basis,original,basis)
            missing=reference_receipt(original,basis)
            del missing.output_observation['preflight']['basis_counts']
            with pytest.raises(RuntimeError,match='exact object fields'):
                owner._preflight_command_evidence_v1(missing,accounting_paths,accounting_meter)
            if case=='Git-stream-evidence-readback':
                bad=copy.deepcopy(original)
                bad['remaining_limits']['combined_output_bytes']+=1
                bad['observed']['combined_output_bytes']-=1
                reject_reference(bad,basis,original,basis,match='exact Git stream sum')
                bad=copy.deepcopy(original)
                bad['remaining_limits']['retained_bytes']+=1
                bad['observed']['retained_bytes']-=1
                bad['reserved']['retained_bytes']-=1
                reject_reference(bad,basis,original,basis,match='complete acquisition byte accounting')
    with capsys.disabled():
        print('PREFLIGHT_ACCOUNTING_REFERENCE '+json.dumps(dict(valid_complete_references=reference_count,
            rejected_mutations_each_through_direct_and_final_verifier=mutation_count,
            application_exits=[0,1,2],cases=[case for case,_,_ in scenarios],native_execution=False)),flush=True)
    # A real child receives its own PID/thread and executes each original pure CLI.
    # These two synthetic selections are not an admitted canonical eight-command run.
    for n in (2,6):
        ident=identity(n); argv=tuple(ident['argv'])
        observation=owner._PreflightObservationV1(root=root,run_id=run_id,occurrence=n,argv=argv,
            files={},directories={},limits=dict(limits),deadline_ns=deadline)
        observation.reserve('attempts',1)
        observation.received('bytes',2)
        before=dict(observation.remaining)
        entry=owner.build_command_evidence_plan(run_id=run_id,phase='fast-preflight',commands=[argv],cwd=root)[0]
        from dataclasses import replace
        entry=replace(entry,command_index=n)
        environment={k:v for k,v in os.environ.items() if not k.upper().startswith(('QTT_','PYTHON'))}
        environment.update({owner.RUN_ID_ENV:run_id,owner.PROCESS_ROOT_ENV:str(process_root),
            owner.EVIDENCE_ROOT_ENV:str(evidence_root),'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'})
        launch=owner._PreflightLaunchInputV1(identity=ident,observation=observation,row_total=limits,parent_tail_reserve=tail,
            limits=transport,parent_meter=parent_meter,settlement_deadline_ns=settlement,host_lease=lease,
            plan_entry=entry,environment=environment,scratch_roots=(process_root,),
            output_limits=dict(stdout_bytes=16384,stderr_bytes=16384,combined_output_bytes=32768))
        assert observation.remaining == tail
        assert observation.observed['attempts'] == 1 and observation.observed['bytes'] == 2
        assert all(before[k] == tail[k]+launch.delegated[k] for k in before)
        assert launch.delegated != limits and launch.delegated['attempts'] == 17
        environment.update(launch.controls); launch.environment=environment
        projection=dict(registered_argv=argv,removed_environment_keys=(),
            fixed_environment_controls=tuple((k,environment[k]) for k in (*owner._PREFLIGHT_INPUT_KEYS_V1,
                owner.RUN_ID_ENV,owner.PROCESS_ROOT_ENV,owner.EVIDENCE_ROOT_ENV)))
        actual={}
        with launch, owner._command_projection_v1(projection):
            receipt=owner.supervise_command(argv,cwd=root,run_id=run_id,phase='fast-preflight',command_index=n,
                evidence_root=evidence_root,environment=environment,execution_deadline_ns=deadline,
                output_limits=launch.output_limits,output_observation=actual,launch_input=launch,
                preflight_launch=(argv,dict(environment)),mirror_stdout=False,mirror_stderr=False)
            assert receipt.native_exit_code == 0, Path(receipt.stderr_path).read_bytes().decode('utf-8')
            assert receipt.failure_class is None,actual
            assert launch.state == 'CONSUMED' and launch.result['pid'] == receipt.pid != os.getpid()
            assert launch.result['initial_limits'] == launch.delegated and launch.result['observation_complete']
            assert launch.result['remaining_limits'] == launch.delegated
            assert launch.result['observed'] == zero and launch.result['reserved'] == zero
            assert all(actual[s]['complete'] for s in ('stdout','stderr'))
            assert Path(receipt.stderr_path).read_bytes() == b''
            with pytest.raises(RuntimeError,match='replay'):
                launch._claim(run_id=run_id,phase='fast-preflight',command_index=n,argv=argv,cwd=root)
        assert launch.reader.closed and launch.state == 'CLOSED' and owner._PREFLIGHT_OBSERVATION_V1.get() is None
        assert ('child',receipt.pid) in lease.calls and ('settled',receipt.pid) in lease.calls
        from types import SimpleNamespace
        actual_paths=SimpleNamespace(run_id=run_id,repo_root=root,process_root=process_root,evidence_root=evidence_root)
        owner._preflight_command_evidence_v1(receipt,actual_paths,parent_meter)
        changed_proof=copy.deepcopy(receipt.output_observation)
        changed_proof['preflight']['row_total']['attempts'] += 1
        assert changed_proof != receipt.output_observation
        with pytest.raises(RuntimeError,match='conservation'):
            owner._preflight_command_evidence_v1(replace(receipt,output_observation=changed_proof),actual_paths,parent_meter)
        with capsys.disabled():
            print('PREFLIGHT_SYNTHETIC_NATIVE_CHILD '+json.dumps(dict(original_position=n,
                argv=argv,pid=receipt.pid,parent_pid=os.getpid(),native_exit=receipt.native_exit_code,
                failure_class=receipt.failure_class,termination_state=receipt.termination_state,
                complete_stdout=Path(receipt.stdout_path).read_bytes().decode('utf-8'),
                complete_stderr=Path(receipt.stderr_path).read_bytes().decode('utf-8'),
                receiver=launch.result,parent_after_transfer=observation.remaining,
                parent_actual_observed=observation.observed,closed_reader=launch.reader.closed)),flush=True)
        original=copy.deepcopy(launch.result)
        for field,value in (('pid',os.getpid()),('decode_complete',False),('application_exit',1),('input_bytes_consumed',1)):
            bad=copy.deepcopy(original); bad[field]=value; assert bad != original
            with pytest.raises(RuntimeError):
                owner._preflight_verify_result_v1(bad,identity=ident,initial=launch.delegated,
                    extent=launch.extent,pid=receipt.pid,native_exit=0,basis_counts=dict(launch.basis_counts))
        bad=copy.deepcopy(original); bad['remaining_limits']['attempts'] += 100
        with pytest.raises(RuntimeError,match='debit'):
            owner._preflight_verify_result_v1(bad,identity=ident,initial=launch.delegated,
                extent=launch.extent,pid=receipt.pid,native_exit=0,basis_counts=dict(launch.basis_counts))
    assert parent_meter.received > 0 and parent_meter.emitted > 0 and parent_meter.readback_bytes > 0
    assert parent_meter.read_calls > 0 and parent_meter.write_calls > 0
    # The same production receiver rejects a corrupt identity in a real child.
    # Corrupt the wire deliberately after the sender's normal validation, prove
    # the operand changed, and retain the real traceback/native terminal result.
    for n in (1,3):
        ident=identity(n); argv=tuple(ident['argv'])
        observation=owner._PreflightObservationV1(root=root,run_id=run_id,occurrence=n,argv=argv,
            files={},directories={},limits=dict(limits),deadline_ns=deadline)
        entry=owner.build_command_evidence_plan(run_id=run_id,phase='fast-preflight',commands=[argv],cwd=root)[0]
        environment={k:v for k,v in os.environ.items() if not k.upper().startswith(('QTT_','PYTHON'))}
        environment.update({owner.RUN_ID_ENV:run_id,owner.PROCESS_ROOT_ENV:str(process_root),
            owner.EVIDENCE_ROOT_ENV:str(evidence_root),'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'})
        launch=owner._PreflightLaunchInputV1(identity=ident,observation=observation,row_total=limits,parent_tail_reserve=tail,
            limits=transport,parent_meter=parent_meter,settlement_deadline_ns=settlement,host_lease=lease,
            plan_entry=entry,environment=environment,scratch_roots=(process_root,),
            output_limits=dict(stdout_bytes=32768,stderr_bytes=32768,combined_output_bytes=65536))
        bad=copy.deepcopy(launch.header)
        if n==1: bad['identity']['run_id']='synthetic-preflight-corrupted'
        corrupted=owner._preflight_canonical_v1(bad)
        assert (corrupted != launch.raw_header) is (n==1)
        launch.raw_header=corrupted; launch.prefix=struct.pack('>8sQQ',b'QTTPF01\n',len(corrupted),0)
        launch.extent=24+len(corrupted); launch.controls['QTT_PREFLIGHT_INPUT_BYTES']=str(launch.extent)
        environment.update(launch.controls); launch.environment=environment
        projection=dict(registered_argv=argv,removed_environment_keys=(),fixed_environment_controls=tuple(launch.controls.items()))
        actual={}
        with launch,owner._command_projection_v1(projection):
            receipt=owner.supervise_command(argv,cwd=root,run_id=run_id,phase='fast-preflight',command_index=n,
                evidence_root=evidence_root,environment=environment,execution_deadline_ns=deadline,
                output_limits=launch.output_limits,output_observation=actual,launch_input=launch,
                preflight_launch=(argv,dict(environment)),mirror_stdout=False,mirror_stderr=False)
            assert receipt.native_exit_code != 0 and receipt.failure_class is not None
            assert launch.state == 'HELD' and launch.process.poll() is not None
        raw_error=Path(receipt.stderr_path).read_bytes().decode('utf-8')
        assert ('invocation identity mismatch' if n==1 else 'missing admitted absolute Git/evidence operands') in raw_error
        failed=json.loads((launch.evidence/'receiver.json').read_text())
        assert failed['decode_complete'] is (n==3) and failed['application_entered'] is (n==3)
        assert failed['application_exit'] is None
        assert (failed['initial_limits'] is None) is (n==1)
        assert launch.reader.closed and launch.path.exists()
        with capsys.disabled():
            print('PREFLIGHT_SYNTHETIC_NATIVE_NEGATIVE '+json.dumps(dict(argv=argv,pid=receipt.pid,
                native_exit=receipt.native_exit_code,failure_class=receipt.failure_class,
                termination_state=receipt.termination_state,complete_stdout=Path(receipt.stdout_path).read_bytes().decode('utf-8'),
                complete_stderr=raw_error,receiver=failed,closed_reader=True,failed_input_retained=launch.path.exists())),flush=True)
    # Real position-4 applications read complete current copied source. The
    # copied tree is disposable test support, not an accepted QTT checkout.
    import stat
    from tools import validate_nested_validator_contracts as nested
    source_paths=['tools/validation_reliability.py','tools/validate_nested_validator_contracts.py']
    if (root/'tools/__init__.py').exists(): source_paths.append('tools/__init__.py')
    source_bytes={}
    for name in source_paths:
        info=(root/name).lstat()
        assert stat.S_ISREG(info.st_mode) and info.st_nlink==1 and not owner._stat_is_reparse_point(info)
        source_bytes[name]=(root/name).read_bytes()
    for case,payload,expected_exit in (
            ('positive',b'VALUE = 7\n',0),
            ('semantic-rejection',b'import subprocess\nsubprocess.run(["pytest"])\n',1)):
        fixture_deadline=min(deadline,time.monotonic_ns()+60_000_000_000)
        fixture_settlement=min(settlement,fixture_deadline+10_000_000_000)
        assert time.monotonic_ns()<fixture_deadline<fixture_settlement
        case_root=area/('position-4-'+case); case_root.mkdir()
        copied_root=case_root/'repo'; copied_root.mkdir()
        for name,raw in source_bytes.items():
            target=copied_root/name; target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw); assert target.read_bytes()==raw
        data_path=copied_root/'src/qtt/stage1_prediction_markets/transport_fixture.py'
        data_path.parent.mkdir(parents=True); data_path.write_bytes(payload)
        fixture_paths,fixture_probe=owner.resolve_validation_run_paths(copied_root,
            explicit_process_root=case_root,projected_relative_paths=('preflight-input-4.bin',))
        assert fixture_paths.repo_root==copied_root
        assert fixture_paths.process_root.parent==fixture_paths.evidence_root.parent==copied_root.parent
        assert fixture_probe.failure_operation is None and fixture_paths.filesystem_probe_state=='PASS'
        fixture_run=fixture_paths.run_id
        fixture_process,fixture_evidence=fixture_paths.process_root,fixture_paths.evidence_root
        fixture_lease=SyntheticLease(fixture_root=copied_root,fixture_process_root=fixture_process,fixture_run_id=fixture_run,fixture_deadline=fixture_deadline)
        fixture_environment={k:v for k,v in os.environ.items() if not k.upper().startswith(('QTT_','PYTHON'))}
        fixture_environment.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
        # This additional bounded bootstrap probe imports complete copied modules
        # and records actual origins. It does not call/extract their functions or
        # claim that bootstrap reads are application observations.
        import_code=('import json,os,sys; sys.path.insert(0,os.getcwd()); '
            'import tools.validation_reliability as r; import tools.validate_nested_validator_contracts as v; '
            'print(json.dumps({"reliability":r.__file__,"validator":v.__file__}))')
        import_evidence=fixture_evidence/'imports'; import_evidence.mkdir()
        import_output={}
        import_receipt=owner.supervise_command((sys.executable,'-I','-B','-c',import_code),cwd=copied_root,
            run_id=fixture_run,phase='standalone-pytest-helper',command_index=1,evidence_root=import_evidence,
            environment=fixture_environment,execution_deadline_ns=fixture_deadline,
            output_limits=dict(stdout_bytes=16384,stderr_bytes=16384,combined_output_bytes=32768),
            output_observation=import_output,mirror_stdout=False,mirror_stderr=False)
        assert import_receipt.native_exit_code==0 and import_receipt.failure_class is None,Path(import_receipt.stderr_path).read_bytes()
        assert not owner._command_requires_process_retention_v1(import_receipt)
        import_stdout=Path(import_receipt.stdout_path).read_bytes().decode('utf-8')
        import_stderr=Path(import_receipt.stderr_path).read_bytes().decode('utf-8')
        assert import_stderr=='' and all(import_output[s]['complete'] for s in ('stdout','stderr'))
        origins=json.loads(import_stdout)
        assert origins==dict(reliability=str(copied_root/'tools/validation_reliability.py'),
            validator=str(copied_root/'tools/validate_nested_validator_contracts.py'))
        files,rosters={},{}
        scanned=[]
        def inventory(directory):
            info=directory.lstat()
            assert stat.S_ISDIR(info.st_mode) and not owner._stat_is_reparse_point(info)
            entries=[]; descendants=[]
            with os.scandir(directory) as iterator:
                for entry in iterator:
                    path=Path(entry.path); info=path.lstat()
                    assert not stat.S_ISLNK(info.st_mode) and not owner._stat_is_reparse_point(info)
                    if stat.S_ISDIR(info.st_mode):
                        kind='directory'; descendants.append(path)
                    else:
                        assert stat.S_ISREG(info.st_mode) and info.st_nlink==1
                        kind='file'
                        name=path.relative_to(copied_root).as_posix()
                        if path.name.endswith('.py'):
                            scanned.append(name)
                            if name not in nested.ORCHESTRATOR_ALLOWLIST: files[name]=path.read_bytes()
                    entries.append((entry.name,kind))
            rosters[directory.relative_to(copied_root).as_posix()]=tuple(sorted(entries,key=lambda row:row[0].encode('utf-8')))
            for child in descendants: inventory(child)
        for subtree in (copied_root/'tools',copied_root/'src/qtt/stage1_prediction_markets'): inventory(subtree)
        assert 'tools/validate_nested_validator_contracts.py' in scanned
        assert 'tools/validate_nested_validator_contracts.py' not in files
        assert set(files)==set(source_paths)-{'tools/validate_nested_validator_contracts.py'}|{'src/qtt/stage1_prediction_markets/transport_fixture.py'}
        P=sum(len(raw) for raw in files.values()); N=len(files); L=len(rosters); E=sum(map(len,rosters.values())); C=N+L+E
        assert P>0 and N>0 and L>0 and E>0
        fixture_limits=dict(zero,attempts=L+N,bytes=P+N,entries=C+E,retained_bytes=2*P)
        expected_observed=dict(zero,attempts=L+N,bytes=P,entries=E,retained_bytes=P)
        expected_reserved=dict(zero,attempts=L+N,entries=C,retained_bytes=2*P)
        expected_remaining=dict(zero,bytes=N)
        fixture_argv=(sys.executable,str(Path('tools/validate_nested_validator_contracts.py')),'--repo-root','.')
        fixture_identity=dict(run_id=fixture_run,phase='fast-preflight',command_index=4,original_position=4,
            command_count=8,argv=list(fixture_argv),repo_root=str(copied_root),process_root=str(fixture_process),
            evidence_root=str(fixture_evidence),parent_pid=os.getpid())
        offset=0; file_rows=[]
        for name in sorted(files,key=lambda name:name.encode('utf-8')):
            file_rows.append([name,offset,len(files[name])]); offset+=len(files[name])
        fixture_header=dict(identity=fixture_identity,allowance=fixture_limits,deadline_ns=fixture_deadline,
            git=dict(executable=None,evidence_root=None),files=file_rows,
            directories=[[name,[list(item) for item in rosters[name]]] for name in sorted(rosters,key=lambda name:name.encode('utf-8'))])
        assert owner._preflight_header_v1(fixture_header,P,fixture_identity)==(rosters,C)
        emitted=owner._preflight_encode_header_v1(fixture_header,transport,parent_meter.check,parent_meter.buffers)
        H=len(emitted); B=owner._preflight_result_bound_v1(fixture_identity); F=24+H+P; chunk=min(65536,F)
        fixture_transport=dict(frame_byte_limit=3*F+2*B,header_byte_limit=H,lexical_units=H+B,depth=32,
            quoted_bytes=H+B,read_calls=3*F+2*B+5,write_calls=F,chunk_bytes=chunk,
            retained_buffer_bytes=max(3*F+2*B,3*H+2*B+chunk),receiver_byte_limit=B)
        fixture_meter=owner._PreflightTransportV1(fixture_transport,fixture_settlement)
        fixture_observation=owner._PreflightObservationV1(root=copied_root,run_id=fixture_run,occurrence=4,
            argv=fixture_argv,files=files,directories=rosters,limits=fixture_limits,deadline_ns=fixture_deadline)
        fixture_entry=owner.build_command_evidence_plan(run_id=fixture_run,phase='fast-preflight',commands=[fixture_argv],cwd=copied_root)[0]
        fixture_entry=replace(fixture_entry,command_index=4)
        fixture_environment.update({owner.RUN_ID_ENV:fixture_run,owner.PROCESS_ROOT_ENV:str(fixture_process),
            owner.EVIDENCE_ROOT_ENV:str(fixture_evidence)})
        fixture_launch=owner._PreflightLaunchInputV1(identity=fixture_identity,observation=fixture_observation,
            row_total=fixture_limits,parent_tail_reserve=zero,limits=fixture_transport,parent_meter=fixture_meter,
            settlement_deadline_ns=fixture_settlement,host_lease=fixture_lease,plan_entry=fixture_entry,
            environment=fixture_environment,scratch_roots=(fixture_process,),
            output_limits=dict(stdout_bytes=16384,stderr_bytes=16384,combined_output_bytes=32768))
        assert fixture_launch.raw_header==emitted and fixture_launch.extent==F
        assert dict(fixture_launch.basis_counts)==dict(entries=C,bytes=P)
        with pytest.raises(TypeError): fixture_launch.basis_counts['bytes']=0
        original_counts=fixture_launch.basis_counts
        fixture_launch.basis_counts=dict(entries=C,bytes=P-1)
        with pytest.raises(RuntimeError,match='emitted basis binding'): fixture_launch._proof_basis_counts()
        fixture_launch.basis_counts=original_counts
        original_frame=fixture_launch.raw_header
        fixture_launch.raw_header=original_frame+b' '
        with pytest.raises(RuntimeError,match='emitted basis binding'): fixture_launch._proof_basis_counts()
        fixture_launch.raw_header=original_frame
        assert fixture_launch._proof_basis_counts()==dict(entries=C,bytes=P)
        fixture_environment.update(fixture_launch.controls); fixture_launch.environment=fixture_environment
        fixture_projection=dict(registered_argv=fixture_argv,removed_environment_keys=(),
            fixed_environment_controls=tuple((key,fixture_environment[key]) for key in (*owner._PREFLIGHT_INPUT_KEYS_V1,
                owner.RUN_ID_ENV,owner.PROCESS_ROOT_ENV,owner.EVIDENCE_ROOT_ENV)))
        fixture_output={}
        resource_scope=job_scope(run_id=fixture_run,phase='fast-preflight',command_index=4,
            argv=fixture_argv,cwd=copied_root,evidence_root=fixture_evidence,environment=dict(fixture_environment),
            active_process_limit=2,process_commit_bytes=268435456,job_commit_bytes=536870912,cpu_rate_10000=2000,
            execution_deadline_ns=fixture_deadline,settlement_deadline_ns=fixture_settlement)
        with fixture_launch,owner._command_projection_v1(fixture_projection),resource_scope as resource_measurement:
            fixture_receipt=owner.supervise_command(fixture_argv,cwd=copied_root,run_id=fixture_run,
                phase='fast-preflight',command_index=4,evidence_root=fixture_evidence,environment=fixture_environment,
                execution_deadline_ns=fixture_deadline,output_limits=fixture_launch.output_limits,output_observation=fixture_output,
                launch_input=fixture_launch,preflight_launch=(fixture_argv,dict(fixture_environment)),
                mirror_stdout=False,mirror_stderr=False)
            fixture_stdout=Path(fixture_receipt.stdout_path).read_bytes().decode('utf-8')
            fixture_stderr=Path(fixture_receipt.stderr_path).read_bytes().decode('utf-8')
            assert fixture_receipt.native_exit_code==expected_exit,fixture_stderr
            assert fixture_receipt.failure_class==(None if expected_exit==0 else 'ENGVR_NATIVE_EXIT_NONZERO'),fixture_stderr
            check_job(fixture_receipt,fixture_output)
            assert fixture_launch.state=='CONSUMED' and fixture_launch.result is not None
            measured=fixture_launch.result
            assert measured['pid']==fixture_receipt.pid!=os.getpid() and measured['parent_pid']==os.getpid()
            assert measured['cwd']==str(copied_root) and measured['argv']==list(fixture_argv)
            assert measured['run_id']==fixture_run and measured['original_position']==measured['command_index']==4
            assert measured['decode_complete'] is measured['application_entered'] is measured['observation_complete'] is True
            assert measured['application_exit']==expected_exit
            assert measured['failure_class']==(None if expected_exit==0 else 'PREFLIGHT_APPLICATION_DENIED')
            assert measured['initial_limits']==fixture_limits and measured['remaining_limits']==expected_remaining
            assert measured['observed']==expected_observed and measured['reserved']==expected_reserved
            assert measured['retained_entries']==C+E and measured['input_bytes_consumed']==F
            assert fixture_observation.observed==zero and fixture_observation.remaining==zero
            assert all(fixture_output[stream]['complete'] for stream in ('stdout','stderr'))
            if expected_exit==0:
                assert fixture_stdout=='NESTED_VALIDATOR_CONTRACTS_OK'+os.linesep and fixture_stderr==''
            else:
                assert fixture_stdout==''
                assert fixture_stderr==('src/qtt/stage1_prediction_markets/transport_fixture.py:2: nested full validator rerun '
                    'forbidden: pytest; validate recorded receipts/contracts or add NESTED_VALIDATOR_RERUN_ALLOWED_SAFE_FAST_INTENTIONAL'+os.linesep)
        assert fixture_launch.state=='CLOSED' and fixture_launch.reader.closed
        assert owner._PREFLIGHT_OBSERVATION_V1.get() is None
        assert not owner._command_requires_process_retention_v1(fixture_receipt)
        assert ('child',fixture_receipt.pid) in fixture_lease.calls and ('settled',fixture_receipt.pid) in fixture_lease.calls
        owner._preflight_command_evidence_v1(fixture_receipt,fixture_paths,fixture_meter)
        assert fixture_receipt.output_observation['preflight']['basis_counts']==dict(entries=C,bytes=P)
        result_bytes=(fixture_launch.evidence/'receiver.json').stat().st_size
        assert fixture_meter.emitted==F and fixture_meter.readback_bytes==3*F
        assert fixture_meter.received==3*F+2*result_bytes<=3*F+2*B
        assert fixture_meter.read_calls<=3*F+2*B+5 and fixture_meter.write_calls<=F
        assert fixture_meter.lexical_units<=H+B and fixture_meter.quoted_bytes<=H+B
        assert fixture_meter.peak_buffers<=fixture_transport['retained_buffer_bytes']
        cleanup=owner.cleanup_validation_run(fixture_paths)
        assert cleanup=='PASS_REMOVED_EXACT_RUN_ROOT' and not fixture_process.exists()
        assert copied_root.is_dir() and fixture_evidence.is_dir() and data_path.read_bytes()==payload
        cleanup_record=json.loads((fixture_evidence/'cleanup.json').read_text())
        with capsys.disabled():
            print('PREFLIGHT_SYNTHETIC_BYTE_CONSUMING_CHILD '+json.dumps(dict(case=case,original_position=4,
                argv=fixture_argv,cwd=str(copied_root),pid=fixture_receipt.pid,parent_pid=os.getpid(),
                native_exit=fixture_receipt.native_exit_code,failure_class=fixture_receipt.failure_class,
                complete_stdout=fixture_stdout,complete_stderr=fixture_stderr,receiver=measured,
                copied_source_paths=source_paths,source_lengths={name:len(raw) for name,raw in source_bytes.items()},
                import_probe=dict(argv=import_receipt.argv,native_exit=import_receipt.native_exit_code,
                    complete_stdout=import_stdout,complete_stderr=import_stderr,origins=origins),
                independent_counts=dict(P=P,N=N,L=L,E=E,C=C,H=H,B=B,F=F),
                basis_counts=dict(fixture_launch.basis_counts),expected_observed=expected_observed,
                expected_reserved=expected_reserved,expected_remaining=expected_remaining,
                parent_transport=dict(emitted=fixture_meter.emitted,received=fixture_meter.received,
                    readback_bytes=fixture_meter.readback_bytes,read_calls=fixture_meter.read_calls,
                    write_calls=fixture_meter.write_calls,lexical_units=fixture_meter.lexical_units,
                    quoted_bytes=fixture_meter.quoted_bytes,peak_buffers=fixture_meter.peak_buffers),
                transport_limits=fixture_transport,execution_deadline_ns=fixture_deadline,settlement_deadline_ns=fixture_settlement,
                windows_job=fixture_output.get('windows_job'),
                configured_empty=getattr(resource_measurement,'configured_membership',None),
                suspended_membership=getattr(resource_measurement,'creation_membership',None),
                suspended_identity=getattr(resource_measurement,'creation_identity',None),
                terminal_membership=getattr(resource_measurement,'membership_observation',None),
                lifetime_attribution='not_established',
                native_host_qualified=False,canonical_run=False,closed_reader=fixture_launch.reader.closed,
                actual_cleanup=cleanup_record)),flush=True)
    job_lifecycle()
    # One-shot parent declaration and candidate assembly over a tiny literal
    # no-Git repository. Startup is intentionally not qualified or executed.
    fixture_root=area/'candidate'; fixture_root.mkdir(); (fixture_root/'a.bin').write_bytes(b'abc')
    allocation=area/'assembly-runs'; allocation.mkdir()
    paths,probe=owner.resolve_validation_run_paths(fixture_root,explicit_process_root=allocation,
        projected_relative_paths=('a.bin',))
    vectors=tuple(tuple(identity(i)['argv']) for i in range(1,9))
    plan=owner.build_command_evidence_plan(run_id=paths.run_id,phase='fast-preflight',commands=vectors,cwd=fixture_root)
    capture=dict(zero,attempts=1000,bytes=100000,entries=1000,retained_bytes=100000)
    declaration=dict(phase='fast-preflight',repository=dict(root=str(fixture_root),files=[['a.bin',0]],
        directories=[['.',[['a.bin','file']]]],index=None,protected_paths=['a.bin']),
        installation=dict(executable=sys.executable,version=list(sys.version_info[:3]),
            abi=[sys.implementation.cache_tag,None,64,0,''],stdlib_roots=[],site_roots=[],loader_environment={},
            config_paths=[],customizer_paths=[],startup_basis=dict(files=[[sys.executable,1]],directories=[],absent=[])),
        candidate_limits=dict(entry_limit=1000,snapshot_byte_limit=100000,read_byte_limit=100000,deadline_ns=settlement),
        parent_limits=dict(capture=capture,terminal=capture,transport=transport,deadline_ns=settlement),
        rows=[dict(original_position=i,argv=list(vectors[i-1]),files=[['a.bin',0]],directories=[['.',[['a.bin','file']]]],
            limits=limits,parent_tail_reserve=zero,deadline_ns=deadline,settlement_deadline_ns=settlement,
            transport=transport,application_output_limits=dict(stdout_bytes=1000,stderr_bytes=1000,combined_output_bytes=2000),
            git_executable=None) for i in range(1,9)],blobs=[[0,3],[3,4]])
    class AssemblyLease(owner._PreflightHostLeaseV1):
        def check_parent(self,checked_root,index_path):
            assert checked_root == fixture_root and index_path is None
            assert (fixture_root/'a.bin').read_bytes() == b'abc'
    sequence=0
    def source(h):
        nonlocal sequence
        sequence+=1
        declaration_path=area/('declaration-'+str(sequence)+'.bin')
        raw=owner._preflight_canonical_v1(h)
        declaration_path.write_bytes(struct.pack('>8sQQ',b'QTTPA01\n',len(raw),7)+raw+b'abcboot')
        return owner._PreflightNativeInputV1(path=declaration_path,root=fixture_root,index_path=None,
            expected_path_version=owner._scan_same_api_version(declaration_path.lstat()),
            expected_chain=owner._preflight_chain_v1(declaration_path.parent),limits=transport,deadline_ns=settlement,
            host_lease=AssemblyLease(),capture_limits=capture,terminal_limits=capture)
    native=source(declaration)
    with owner._preflight_native_input_v1(native):
        assert owner._preflight_acquire_native_input_v1(native.path,fixture_root) is native
        assembly=runner._PreflightAssemblyV1(native,paths,plan)
        assert assembly.state == 'CUSTODY_READY' and native.state == 'CONSUMED'
        assert assembly.plan is plan and assembly.candidate.plan is plan
        assert assembly.candidate_source(fixture_root,plan) is assembly.candidate
        assert assembly.candidate.baseline['a.bin'][1] == b'abc'
        assert set(assembly.candidate.effects) == set(range(1,9)) and not any(assembly.candidate.effects.values())
        assert assembly.candidate.nested_evidence_limits == {} and assembly.launches == {}
        with pytest.raises(RuntimeError,match='single use'):
            native.consume(assembly._validate_declaration)
    assert owner._PREFLIGHT_NATIVE_INPUT_V1.get() is None
    for mutate in (lambda h:h.__setitem__('host_lease',True),
            lambda h:h['rows'].pop(),lambda h:h['rows'][7].__setitem__('original_position',1),
            lambda h:h['rows'][2].__setitem__('git_executable',sys.executable),
            lambda h:h['repository']['files'][0].__setitem__(1,True),
            lambda h:h['rows'][0]['parent_tail_reserve'].__setitem__('bytes',9999)):
        bad=copy.deepcopy(declaration); mutate(bad); assert bad != declaration
        denied=source(bad)
        with pytest.raises((ValueError,RuntimeError)):
            runner._PreflightAssemblyV1(denied,paths,plan)
        assert denied.state == 'FAILED'
    assert not (paths.evidence_root/'run.json').exists()
    cleanup=owner.cleanup_validation_run(paths)
    assert cleanup == 'PASS_REMOVED_EXACT_RUN_ROOT'
    with capsys.disabled():
        print('PREFLIGHT_SYNTHETIC_PARENT_ASSEMBLY '+json.dumps(dict(original_positions=8,one_plan_identity=True,
            candidate_bytes_compared=3,application_children_started=0,startup_qualified=False,canonical_host_qualified=False,
            run_header_published=False,actual_cleanup=cleanup)),flush=True)
    # Deadline and exhausted transport negatives operate on the real reader.
    expired=owner._PreflightTransportV1(transport,time.monotonic_ns()-1)
    with pytest.raises(RuntimeError,match='deadline'):
        expired.check()
    tiny=owner._PreflightTransportV1(dict(transport,read_calls=1),deadline)
    path=area/'short-read-budget.bin'; path.write_bytes(b'ab')
    fd=os.open(path,os.O_RDONLY|int(getattr(os,'O_BINARY',0)))
    try:
        assert tiny.read(fd,1) == b'a'
        with pytest.raises(RuntimeError,match='read calls'):
            tiny.read(fd,1)
        assert tiny.received == 1 and tiny.read_calls == 1
    finally: os.close(fd)
    # Actual normal parent CLI, with no configured native provider, denies
    # before path/probe allocation. This extra engineering probe is not a ninth
    # selected command or a canonical run.
    parent_argv=(sys.executable,'tools/run_validation_gates.py','--phase','fast-preflight',
        '--preflight-input',str(area/'unavailable-parent-input.bin'))
    parent_env={k:v for k,v in os.environ.items() if not k.upper().startswith(('QTT_','PYTHON'))}
    parent_env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1')
    parent_output={}
    parent_receipt=owner.supervise_command(parent_argv,cwd=root,run_id='synthetic-parent-port',
        phase='standalone-pytest-helper',command_index=9,evidence_root=evidence_root,environment=parent_env,
        execution_deadline_ns=deadline,output_limits=dict(stdout_bytes=32768,stderr_bytes=32768,combined_output_bytes=65536),
        output_observation=parent_output,mirror_stdout=False,mirror_stderr=False)
    assert parent_receipt.native_exit_code==1 and parent_receipt.failure_class=='ENGVR_NATIVE_EXIT_NONZERO'
    parent_error=Path(parent_receipt.stderr_path).read_bytes().decode('utf-8')
    assert 'PREFLIGHT_NATIVE_HOST_PROVIDER_UNAVAILABLE' in parent_error
    assert not owner._command_requires_process_retention_v1(parent_receipt)
    with capsys.disabled():
        print('PREFLIGHT_SYNTHETIC_PARENT_CLI_DENIAL '+json.dumps(dict(argv=parent_argv,pid=parent_receipt.pid,
            native_exit=parent_receipt.native_exit_code,failure_class=parent_receipt.failure_class,
            termination_state=parent_receipt.termination_state,
            complete_stdout=Path(parent_receipt.stdout_path).read_bytes().decode('utf-8'),complete_stderr=parent_error)),flush=True)
    # Exact selected CLI reaches the missing-provider denial without opening a declaration or dispatching.
    with monkeypatch.context() as scoped:
        scoped.setattr(runner,'_legacy_run_commands_test_adapter_active',lambda:False)
        with pytest.raises(RuntimeError,match='NATIVE_HOST_PROVIDER_UNAVAILABLE'):
            runner.main(['--phase','fast-preflight','--preflight-input',str(area/'missing.bin')])
