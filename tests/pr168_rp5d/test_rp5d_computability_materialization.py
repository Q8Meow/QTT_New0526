from __future__ import annotations

from ._helpers import rows


def test_computability_rows_are_actionable_not_metadata_or_placeholder() -> None:
    rows_ = rows("rp5d_comp_materialization.jsonl")

    assert rows_
    for row in rows_:
        assert row["metadata_only_flag"] is False
        assert row["placeholder_flag"] is False
        assert row["computability_materialization_state"] not in {"UNKNOWN", "TBD", "PLACEHOLDER"}
        if not row["computable_now_flag"]:
            assert (
                row["adapter_queue_refs"]
                or row["preservation_reason_if_not_executable"]
                or row["computable_after_adapter_flag"]
            )
