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
    committed_preflight_path = report_path("PR168_RP5A_Preflight.report.json")
    original_preflight_read_json = builder.read_json
    committed_preflight_report = builder.read_json(committed_preflight_path)
    forbidden_preflight_calls = []

    def forbidden_preflight_call(name):
        def fail(*args, **kwargs):
            forbidden_preflight_calls.append((name, args, kwargs))
            raise AssertionError(f"offline preflight called {name}")

        return fail

    with monkeypatch.context() as offline_preflight_patch:
        for owner, name in (
            (builder, "_run_text"),
            (builder, "_run_json"),
            (builder.subprocess, "run"),
        ):
            offline_preflight_patch.setattr(
                owner, name, forbidden_preflight_call(name)
            )
        offline_preflight = builder._collect_preflight(
            committed_preflight_path, offline=True
        )
    assert offline_preflight == dict(committed_preflight_report["records"])
    assert (
        offline_preflight["pr240_closed_not_merged_preflight_passed"] is True
    )
    assert forbidden_preflight_calls == []

    preflight_mutation_cases = (
        ([], "RP5A_PREFLIGHT_COMMITTED_PAYLOAD_INVALID"),
        ({"records": []}, "RP5A_PREFLIGHT_COMMITTED_RECORDS_INVALID"),
        (
            {
                "pr240_closed_not_merged_preflight_passed": True,
                "records": {"pr240_closed_not_merged_preflight_passed": False},
            },
            "RP5A_PREFLIGHT_COMMITTED_PR240_CLOSURE_INVALID",
        ),
        (
            {
                "pr240_closed_not_merged_preflight_passed": False,
                "records": {"pr240_closed_not_merged_preflight_passed": True},
            },
            "RP5A_PREFLIGHT_COMMITTED_PR240_CLOSURE_INVALID",
        ),
    )
    with monkeypatch.context() as preflight_mutation_patch:
        for payload, expected_error in preflight_mutation_cases:
            preflight_mutation_patch.setattr(
                builder,
                "read_json",
                lambda path, value=payload: (
                    copy.deepcopy(value)
                    if path == committed_preflight_path
                    else original_preflight_read_json(path)
                ),
            )
            try:
                builder._load_committed_preflight_owner(
                    committed_preflight_path
                )
            except RuntimeError as exc:
                assert str(exc) == expected_error
            else:
                raise AssertionError(
                    f"committed preflight mutation accepted:{expected_error}"
                )

    online_text_calls = []
    online_json_calls = []
    committed_preflight_loader_calls = []
    synthetic_origin_main = "synthetic-origin-main"
    live_pr240 = {
        "number": 240,
        "state": "CLOSED",
        "mergedAt": None,
        "headRefName": builder.PR240_HEAD_REF,
    }
    live_main_run = {
        "status": "completed",
        "conclusion": "success",
        "headSha": synthetic_origin_main,
    }
    online_text_results = {
        ("git", "branch", "--show-current"): ST12A_BRANCH,
        ("git", "rev-parse", "origin/main"): synthetic_origin_main,
        (
            "git",
            "status",
            "--short",
            "--untracked-files=all",
        ): "",
    }
    online_json_results = {
        (
            "gh",
            "pr",
            "view",
            "240",
            "--json",
            (
                "number,state,mergedAt,headRefName,headRefOid,"
                "baseRefName,mergeable"
            ),
        ): live_pr240,
        (
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--limit",
            "50",
            "--json",
            "number,title,headRefName",
        ): [],
        (
            "gh",
            "run",
            "list",
            "--branch",
            "main",
            "--limit",
            "1",
            "--json",
            "status,conclusion,databaseId,headSha,displayTitle",
        ): [live_main_run],
    }

    def online_text(args):
        online_text_calls.append(tuple(args))
        return online_text_results[tuple(args)]

    def online_json(args):
        online_json_calls.append(tuple(args))
        return copy.deepcopy(online_json_results[tuple(args)])

    def reject_committed_preflight_loader(path):
        committed_preflight_loader_calls.append(path)
        return {}

    with monkeypatch.context() as online_preflight_patch:
        online_preflight_patch.setattr(builder, "_run_text", online_text)
        online_preflight_patch.setattr(builder, "_run_json", online_json)
        online_preflight_patch.setattr(
            builder,
            "_load_committed_preflight_owner",
            reject_committed_preflight_loader,
        )
        online_preflight = builder._collect_preflight(
            committed_preflight_path, offline=False
        )
    assert online_text_calls == list(online_text_results)
    assert online_json_calls == list(online_json_results)
    assert committed_preflight_loader_calls == []
    assert online_preflight["current_branch"] == ST12A_BRANCH
    assert online_preflight["origin_main_head"] == synthetic_origin_main
    assert (
        online_preflight["git_status_short_after_rp5a_edits"]
        == "<clean>"
    )
    assert online_preflight["latest_main_run_state"] == live_main_run
    assert online_preflight["open_prs_excluding_rp5a_branch"] == []
    assert (
        online_preflight["pr240_closed_not_merged_preflight_passed"] is True
    )

    class _PreflightDispatchSentinel(Exception):
        pass

    preflight_dispatches = []

    def preflight_dispatch_spy(path, *, offline):
        preflight_dispatches.append((path, offline))
        raise _PreflightDispatchSentinel

    with monkeypatch.context() as build_dispatch_patch:
        build_dispatch_patch.setattr(builder, "_collect_preflight", preflight_dispatch_spy)
        try:
            builder.build_all(offline=True)
        except _PreflightDispatchSentinel:
            pass
        else:
            raise AssertionError(
                "build_all did not dispatch through preflight"
            )
    assert preflight_dispatches == [(committed_preflight_path, True)]

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

    committed_rows_path = builder.shard_path(
        "legacy_pr_semantic_rows"
    )
    committed_manifest_path = builder.manifest_path_for_shard(
        committed_rows_path
    )
    committed_report_path = report_path(
        "PR168_RP5A_LegacyPRSemanticAudit.report.json"
    )
    original_builder_read_json = builder.read_json
    original_builder_read_jsonl = builder.read_jsonl
    committed_rows = original_builder_read_jsonl(
        committed_rows_path
    )
    committed_manifest = original_builder_read_json(
        committed_manifest_path
    )
    committed_report = original_builder_read_json(
        committed_report_path
    )
    committed_summary = {
        key: value
        for key, value in committed_report.items()
        if key not in builder._REPORT_PAYLOAD_METADATA_FIELDS
    }
    offline_rows, offline_summary = builder._resolve_pr_metadata(
        offline=True,
        existing_rows_path=committed_rows_path,
        existing_report_path=committed_report_path,
    )
    assert offline_rows == committed_rows
    assert offline_summary == committed_summary
    assert (
        len(offline_rows)
        == committed_manifest["row_count"]
        == sum(
            bool(row.get("matched_terms"))
            for row in offline_rows
        )
        == offline_summary["github_prs_with_stale_terms_count"]
    )
    assert (
        offline_summary["github_prs_scanned_count"]
        >= offline_summary["github_prs_with_stale_terms_count"]
    )
    assert (
        offline_summary[
            "pr240_closed_not_merged_preflight_passed"
        ]
        is True
    )

    fallback_fetch_calls = []
    filtered_fallback_rows = committed_rows[:3]
    monkeypatch.setattr(
        builder,
        "fetch_pr_metadata_rows",
        lambda path: (
            fallback_fetch_calls.append(path)
            or (
                filtered_fallback_rows,
                {
                    "github_metadata_source": (
                        "existing_committed_rows_fallback"
                    ),
                    "github_prs_scanned_count": len(
                        filtered_fallback_rows
                    ),
                },
            )
        ),
    )
    fallback_rows, fallback_summary = builder._resolve_pr_metadata(
        offline=False,
        existing_rows_path=committed_rows_path,
        existing_report_path=committed_report_path,
    )
    assert fallback_fetch_calls == [committed_rows_path]
    assert fallback_rows == committed_rows
    assert fallback_summary == committed_summary

    mutation_cases = []
    bad_manifest = copy.deepcopy(committed_manifest)
    bad_manifest["row_count"] += 1
    mutation_cases.append(
        (
            "manifest-row-count",
            committed_rows,
            bad_manifest,
            committed_report,
            (
                "RP5A_PR_METADATA_COMMITTED_"
                "MANIFEST_ROW_COUNT_MISMATCH"
            ),
        )
    )
    missing_stale_report = copy.deepcopy(committed_report)
    missing_stale_report.pop(
        "github_prs_with_stale_terms_count"
    )
    mutation_cases.append(
        (
            "missing-stale-count",
            committed_rows,
            committed_manifest,
            missing_stale_report,
            "RP5A_PR_METADATA_COMMITTED_STALE_COUNT_INVALID",
        )
    )
    scanned_below_stale_report = copy.deepcopy(committed_report)
    scanned_below_stale_report["github_prs_scanned_count"] = (
        committed_report["github_prs_with_stale_terms_count"] - 1
    )
    mutation_cases.append(
        (
            "scanned-below-stale",
            committed_rows,
            committed_manifest,
            scanned_below_stale_report,
            "RP5A_PR_METADATA_COMMITTED_SCANNED_BELOW_STALE",
        )
    )
    stale_row_mismatch_report = copy.deepcopy(committed_report)
    stale_row_mismatch_report[
        "github_prs_with_stale_terms_count"
    ] -= 1
    mutation_cases.append(
        (
            "stale-row-mismatch",
            committed_rows,
            committed_manifest,
            stale_row_mismatch_report,
            (
                "RP5A_PR_METADATA_COMMITTED_"
                "STALE_ROW_COUNT_MISMATCH"
            ),
        )
    )
    pr240_false_report = copy.deepcopy(committed_report)
    pr240_false_report[
        "pr240_closed_not_merged_preflight_passed"
    ] = False
    mutation_cases.append(
        (
            "pr240-closure-false",
            committed_rows,
            committed_manifest,
            pr240_false_report,
            "RP5A_PR_METADATA_COMMITTED_PR240_CLOSURE_INVALID",
        )
    )
    for (
        mutation_label,
        mutation_rows,
        mutation_manifest,
        mutation_report,
        expected_error,
    ) in mutation_cases:
        monkeypatch.setattr(
            builder,
            "read_jsonl",
            lambda path, payload=mutation_rows: (
                copy.deepcopy(payload)
                if path == committed_rows_path
                else original_builder_read_jsonl(path)
            ),
        )
        monkeypatch.setattr(
            builder,
            "read_json",
            lambda path,
            manifest_payload=mutation_manifest,
            report_payload=mutation_report: (
                copy.deepcopy(manifest_payload)
                if path == committed_manifest_path
                else (
                    copy.deepcopy(report_payload)
                    if path == committed_report_path
                    else original_builder_read_json(path)
                )
            ),
        )
        try:
            builder._load_committed_pr_metadata_owner(
                committed_rows_path,
                committed_report_path,
            )
        except RuntimeError as exc:
            assert str(exc) == expected_error, mutation_label
        else:
            raise AssertionError(
                "committed metadata mutation accepted:"
                f"{mutation_label}"
            )
    monkeypatch.setattr(
        builder,
        "read_json",
        original_builder_read_json,
    )
    monkeypatch.setattr(
        builder,
        "read_jsonl",
        original_builder_read_jsonl,
    )

    complete_live_rows = [
        {"pr_number": 999, "matched_terms": ["stale-term"]},
        {"pr_number": 240, "matched_terms": []},
    ]
    complete_live_summary = {
        "github_metadata_source": "gh_pr_list",
        "github_prs_scanned_count": 9,
        "github_prs_with_stale_terms_count": 1,
        "pr240_closed_not_merged_preflight_passed": True,
    }
    monkeypatch.setattr(
        builder,
        "fetch_pr_metadata_rows",
        lambda _path: (
            copy.deepcopy(complete_live_rows),
            copy.deepcopy(complete_live_summary),
        ),
    )
    resolved_live_rows, resolved_live_summary = (
        builder._resolve_pr_metadata(
            offline=False,
            existing_rows_path=committed_rows_path,
            existing_report_path=committed_report_path,
        )
    )
    assert resolved_live_rows == complete_live_rows
    assert resolved_live_summary == complete_live_summary

    incomplete_live_summary = copy.deepcopy(
        complete_live_summary
    )
    incomplete_live_summary.pop(
        "github_prs_with_stale_terms_count"
    )
    monkeypatch.setattr(
        builder,
        "fetch_pr_metadata_rows",
        lambda _path: (
            copy.deepcopy(complete_live_rows),
            copy.deepcopy(incomplete_live_summary),
        ),
    )
    try:
        builder._resolve_pr_metadata(
            offline=False,
            existing_rows_path=committed_rows_path,
            existing_report_path=committed_report_path,
        )
    except RuntimeError as exc:
        assert str(exc) == (
            "RP5A_PR_METADATA_LIVE_SUMMARY_INCOMPLETE:"
            "github_prs_with_stale_terms_count"
        )
    else:
        raise AssertionError(
            "unexpected incomplete live metadata was accepted"
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
