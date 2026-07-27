import copy
from collections import Counter
from pathlib import Path

from tests.pr168_rp5a._helpers import load_report
from tools import build_pr168_rp5a_legacy_semantic_audit as builder
from tools import pr168_rp5a_validator as validator
from tools.build_pr168_rp5a_legacy_semantic_audit import (
    VALIDATION_SCOPE_EVIDENCE_FIELDS,
    VALIDATION_SCOPE_MAIN_BASELINE_LABEL,
    VALIDATION_SCOPE_MAIN_COMPARISON_MODE,
    VALIDATION_SCOPE_MERGE_BASELINE_LABEL,
    VALIDATION_SCOPE_MERGE_BASE_COMPARISON_MODE,
    _validation_scope_counter_delta,
    _validation_scope_delta,
)
from tools.ci_branch_context import BranchContext, current_branch_context
from tools.pr168_rp5a_config import report_path
from tools.validation_scope_registry import ST12A_BRANCH


def test_no_validation_scope_removal(monkeypatch) -> None:
    report = load_report("PR168_RP5A_NoDeletionProof.report.json")
    final_summary = load_report("PR168_RP5A_FinalSummary.report.json")
    persisted_evidence = {
        field: copy.deepcopy(report[field])
        for field in VALIDATION_SCOPE_EVIDENCE_FIELDS
    }
    persisted_locations = (
        report,
        report["records"],
        final_summary,
        final_summary["records"],
    )
    for payload in persisted_locations:
        assert {
            field: payload[field]
            for field in VALIDATION_SCOPE_EVIDENCE_FIELDS
        } == persisted_evidence

    repo_root = Path(__file__).resolve().parents[2]
    live_evidence = _validation_scope_delta()
    branch = current_branch_context(repo_root).branch
    assert validator._validation_scope_failures(
        report,
        final_summary,
        live_evidence,
        branch,
    ) == []
    assert report["validation_scope_removed_count"] == 0
    assert report["validation_scope_removed_refs"] == []
    assert report["current_validation_inventory_failures"] == []
    assert report["no_legacy_scope_removal_flag"] is True

    same_count_merge_live = copy.deepcopy(persisted_evidence)
    same_count_merge_live.update(
        {
            "validation_scope_comparison_mode": (
                VALIDATION_SCOPE_MERGE_BASE_COMPARISON_MODE
            ),
            "validation_scope_baseline_ref": (
                VALIDATION_SCOPE_MERGE_BASELINE_LABEL
            ),
            "validation_scope_baseline_command_count": (
                persisted_evidence[
                    "validation_scope_current_command_count"
                ]
            ),
            "validation_scope_added_count": 0,
            "validation_scope_removed_count": 0,
            "validation_scope_removed_refs": [],
            "validation_scope_changed_flag": False,
            "validation_scope_change_type": "NONE",
            "no_legacy_scope_removal_flag": True,
        }
    )
    same_count_main_live = copy.deepcopy(same_count_merge_live)
    same_count_main_live.update(
        {
            "validation_scope_comparison_mode": (
                VALIDATION_SCOPE_MAIN_COMPARISON_MODE
            ),
            "validation_scope_baseline_ref": (
                VALIDATION_SCOPE_MAIN_BASELINE_LABEL
            ),
        }
    )
    context_cases = (
        (ST12A_BRANCH, persisted_evidence, True),
        (ST12A_BRANCH, same_count_merge_live, False),
        ("main", same_count_main_live, True),
        ("ordinary/downstream", same_count_merge_live, True),
    )
    for context_branch, context_live, expected_pass in context_cases:
        context_failures = validator._validation_scope_failures(
            report,
            final_summary,
            context_live,
            context_branch,
        )
        if expected_pass:
            assert context_failures == [], context_branch
        else:
            assert any(
                failure.startswith(
                    "VALIDATION_SCOPE_EVIDENCE_LIVE_MISMATCH:"
                )
                for failure in context_failures
            ), context_branch

    removal_contexts = (
        (ST12A_BRANCH, same_count_merge_live),
        ("main", same_count_main_live),
        ("ordinary/downstream", same_count_merge_live),
    )
    for context_branch, safe_live in removal_contexts:
        removed_live = copy.deepcopy(safe_live)
        removed_live.update(
            {
                "validation_scope_current_command_count": (
                    safe_live[
                        "validation_scope_baseline_command_count"
                    ]
                    - 1
                ),
                "validation_scope_removed_count": 1,
                "validation_scope_removed_refs": [
                    {
                        "phase": "phase-removed",
                        "validator_id": "validator-removed",
                        "canonical_command": ["python", "removed.py"],
                        "multiplicity": 1,
                    }
                ],
                "validation_scope_changed_flag": True,
                "validation_scope_change_type": (
                    "SEMANTIC_COMMAND_REMOVAL_DETECTED"
                ),
                "no_legacy_scope_removal_flag": False,
            }
        )
        removal_failures = validator._validation_scope_failures(
            report,
            final_summary,
            removed_live,
            context_branch,
        )
        assert "LIVE_VALIDATION_SCOPE_REMOVED" in removal_failures
        assert (
            "LIVE_VALIDATION_SCOPE_REMOVED_REFS_PRESENT"
            in removal_failures
        )

    command_a = ("phase-a", "validator-a", ("python", "a.py"))
    command_b = ("phase-b", "validator-b", ("python", "b.py"))
    command_c = ("phase-c", "validator-c", ("python", "c.py"))
    command_a_changed_phase = (
        "phase-changed",
        "validator-a",
        ("python", "a.py"),
    )
    cases = (
        (
            "addition-only",
            Counter({command_a: 1, command_b: 1}),
            Counter({command_a: 1, command_b: 1, command_c: 1}),
            Counter(),
        ),
        (
            "command-removed",
            Counter({command_a: 1, command_b: 1}),
            Counter({command_a: 1}),
            Counter({command_b: 1}),
        ),
        (
            "duplicate-removed",
            Counter({command_a: 2}),
            Counter({command_a: 1}),
            Counter({command_a: 1}),
        ),
        (
            "phase-changed",
            Counter({command_a: 1}),
            Counter({command_a_changed_phase: 1}),
            Counter({command_a: 1}),
        ),
    )
    for label, baseline, current, expected_removed in cases:
        removed, _added = _validation_scope_counter_delta(
            baseline,
            current,
        )
        assert removed == expected_removed, label

    unrelated_main_advance = Counter(
        {command_a: 1, command_c: 1}
    )
    branch_merge_base = Counter({command_a: 1})
    branch_effective_worktree = Counter({command_a: 1})
    merge_base_removed, _ = _validation_scope_counter_delta(
        branch_merge_base,
        branch_effective_worktree,
    )
    moving_main_removed, _ = _validation_scope_counter_delta(
        unrelated_main_advance,
        branch_effective_worktree,
    )
    assert merge_base_removed == Counter()
    assert moving_main_removed == Counter({command_c: 1})

    forbidden_calls = (
        "scannable_files",
        "scan_files_for_terms",
        "fetch_pr_metadata_rows",
        "write_shard",
        "write_report",
    )
    for function_name in forbidden_calls:
        monkeypatch.setattr(
            builder,
            function_name,
            lambda *args, _name=function_name, **kwargs: (
                (_ for _ in ()).throw(
                    AssertionError(
                        f"evidence-only called {_name}"
                    )
                )
            ),
        )
    evidence_only_payloads = (
        builder._validation_scope_evidence_only_payloads()
    )
    assert tuple(evidence_only_payloads) == (
        "PR168_RP5A_NoDeletionProof.report.json",
        "PR168_RP5A_FinalSummary.report.json",
    )
    assert all(
        payload["physical_filename"] == report_name
        for report_name, payload in evidence_only_payloads.items()
    )

    original_read_json = validator.read_json
    input_path = report_path("PR168_RP5A_Input.report.json")
    mutated_input = original_read_json(input_path)
    mutated_input["files_scanned_count"] += 1
    monkeypatch.setattr(
        validator,
        "read_json",
        lambda path: (
            copy.deepcopy(mutated_input)
            if path == input_path
            else original_read_json(path)
        ),
    )
    detailed_count_failures = validator._failures()
    assert any(
        failure.startswith(
            "FILES_SCANNED_DETAILED_OWNER_COUNT_MISMATCH:"
        )
        for failure in detailed_count_failures
    )

    final_summary_path = report_path(
        "PR168_RP5A_FinalSummary.report.json"
    )
    mutated_final_summary = original_read_json(final_summary_path)
    mutated_classification_field = "unclear_do_not_delete_count"
    mutated_final_summary[mutated_classification_field] += 1
    mutated_final_summary["records"][
        mutated_classification_field
    ] += 1
    monkeypatch.setattr(
        validator,
        "read_json",
        lambda path: (
            copy.deepcopy(mutated_final_summary)
            if path == final_summary_path
            else original_read_json(path)
        ),
    )
    classification_count_failures = validator._failures()
    assert any(
        failure.startswith(
            "FINAL_DELETE_CLASSIFICATION_COUNT_MISMATCH:"
        )
        for failure in classification_count_failures
    )
    monkeypatch.setattr(validator, "read_json", original_read_json)

    baseline_cases = (
        (
            "main",
            ("git", "rev-parse", "HEAD^1"),
            VALIDATION_SCOPE_MAIN_BASELINE_LABEL,
            VALIDATION_SCOPE_MAIN_COMPARISON_MODE,
        ),
        (
            ST12A_BRANCH,
            ("git", "merge-base", "HEAD", "origin/main"),
            VALIDATION_SCOPE_MERGE_BASELINE_LABEL,
            VALIDATION_SCOPE_MERGE_BASE_COMPARISON_MODE,
        ),
        (
            "ordinary/downstream",
            ("git", "merge-base", "HEAD", "origin/main"),
            VALIDATION_SCOPE_MERGE_BASELINE_LABEL,
            VALIDATION_SCOPE_MERGE_BASE_COMPARISON_MODE,
        ),
    )
    for (
        context_branch,
        expected_command,
        expected_label,
        expected_mode,
    ) in baseline_cases:
        git_calls = []
        monkeypatch.setattr(
            builder,
            "current_branch_context",
            lambda _root, value=context_branch: BranchContext(
                branch=value,
                source="test",
            ),
        )
        monkeypatch.setattr(
            builder,
            "_run_text",
            lambda args, calls=git_calls: (
                calls.append(tuple(args)) or "internal-git-ref"
            ),
        )
        internal_ref, semantic_label, comparison_mode = (
            builder._validation_scope_baseline()
        )
        assert internal_ref == "internal-git-ref"
        assert semantic_label == expected_label
        assert comparison_mode == expected_mode
        assert git_calls == [expected_command]

    try:
        builder.currentize_validation_scope_evidence_only()
    except RuntimeError as exc:
        assert str(exc) == (
            "RP5A_VALIDATION_SCOPE_EVIDENCE_ONLY_BRANCH_INVALID:"
            "ordinary/downstream"
        )
    else:
        raise AssertionError(
            "evidence-only currentizer accepted a non-ST12-A branch"
        )
