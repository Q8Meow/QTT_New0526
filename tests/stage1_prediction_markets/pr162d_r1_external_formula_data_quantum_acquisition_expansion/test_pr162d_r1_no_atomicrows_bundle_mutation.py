from __future__ import annotations


def test_pr162d_r1_no_atomicrows_bundle_mutation(records, summary):
    audit = records("PR162D_R1_NoAtomicRowsBundleMutationAudit.report.json")[0]
    assert summary["atomicrows_bundle_mutation_count"] == 0
    assert summary["atomicrows_bundle_jsonl_changed_flag"] is False
    assert audit["atomicrows_bundle_jsonl_changed_flag"] is False
