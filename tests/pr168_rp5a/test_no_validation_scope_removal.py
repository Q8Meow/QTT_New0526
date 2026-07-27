from collections import Counter

from tests.pr168_rp5a._helpers import load_report
from tools.build_pr168_rp5a_legacy_semantic_audit import (
    VALIDATION_SCOPE_EVIDENCE_FIELDS,
    _validation_scope_counter_delta,
    _validation_scope_delta,
)


def test_no_validation_scope_removal() -> None:
    report = load_report("PR168_RP5A_NoDeletionProof.report.json")
    final_summary = load_report("PR168_RP5A_FinalSummary.report.json")
    live_evidence = _validation_scope_delta()
    for report_name, payload in (
        ("NoDeletionProof", report),
        ("FinalSummary", final_summary),
    ):
        records = payload["records"]
        assert isinstance(records, dict), report_name
        for field in VALIDATION_SCOPE_EVIDENCE_FIELDS:
            assert payload[field] == live_evidence[field], (
                report_name,
                "top-level",
                field,
            )
            assert records[field] == live_evidence[field], (
                report_name,
                "records",
                field,
            )
    assert report["validation_scope_removed_count"] == 0
    assert report["no_legacy_scope_removal_flag"] is True

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
