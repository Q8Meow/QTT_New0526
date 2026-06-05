from __future__ import annotations


def test_family_subfamily_variant_hierarchy_is_not_collapsed(records, summary):
    rows = records("PR162D_R2A_FamilySubfamilyVariantHierarchy.report.json")
    assert len({row["domain_family_key"] for row in rows}) == summary["family_count"]
    assert summary["family_count"] >= 9
    assert summary["subfamily_count"] > summary["family_count"]
    assert summary["variant_count"] >= summary["subfamily_count"]
    assert all(row["subfamily_key"] for row in rows)
    assert all(row["variant_key"] for row in rows)
    assert all(row["formulation_refs"] for row in rows)
