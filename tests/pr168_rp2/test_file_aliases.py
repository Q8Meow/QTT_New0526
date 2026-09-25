from tests.pr168_rp2._helpers import assert_rp2_valid


def test_file_aliases(tmp_path) -> None:
    assert_rp2_valid()

    import math
    import pytest
    from tools.pr168_rp2_reports import write_jsonl

    path = tmp_path / "finite-jsonl-fixture.jsonl"
    finite = [{"label": "\u00e9", "value": 0.5}]
    assert write_jsonl(path, finite) == finite
    expected = b'{"label":"\\u00e9","value":0.5}\n'
    assert path.read_bytes() == expected
    for invalid in (math.nan, math.inf, -math.inf):
        with pytest.raises(ValueError):
            write_jsonl(path, [finite[0], {"value": invalid}])
        # Prefix writes remain visible; an invalid suffix is never a successful shard.
        assert path.read_bytes() == expected
