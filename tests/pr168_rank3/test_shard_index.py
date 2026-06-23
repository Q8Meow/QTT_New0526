from tests.pr168_rank3._helpers import assert_rank3_valid, rows


def test_no_rp3_shard_family_silently_ignored() -> None:
    assert_rank3_valid()
    shard_rows = rows("rp3_shard_family")
    assert len(shard_rows) == 50
    assert all(row["no_orphan_status"] == "NO_ORPHAN" for row in shard_rows)
