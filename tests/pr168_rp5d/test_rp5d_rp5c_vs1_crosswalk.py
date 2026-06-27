from __future__ import annotations

from ._helpers import rows


def test_vs1_crosswalk_marks_bounded_evidence_only() -> None:
    crosswalk = rows("rp5d_rp5c_vs1_crosswalk.jsonl")

    assert crosswalk
    assert all(row["vs1_evidence_scope"] == "BOUNDED_FIXTURE_EVIDENCE_ONLY" for row in crosswalk)
    assert any(row["vs1_binding_refs"] for row in crosswalk)
    assert any(row["vs1_no_trade_refs"] for row in crosswalk)
