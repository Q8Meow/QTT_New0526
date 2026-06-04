from __future__ import annotations


def test_pr162r_a_no_atomicrows_bundle_mutation(summary, records):
    audit = records("PR162R_A_NoAtomicRowsBundleMutationAudit.report.json")[0]
    assert summary["atomicrows_bundle_mutation_count"] == 0
    assert audit["atomicrows_bundle_mutation_count"] == 0
