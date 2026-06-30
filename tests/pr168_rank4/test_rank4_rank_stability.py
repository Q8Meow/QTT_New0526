from ._helpers import rows


def test_rank_stability_surfaces_exist() -> None:
    assert rows("rank_rank_stability.jsonl")
    assert rows("rank_sensitivity_surface.jsonl")

