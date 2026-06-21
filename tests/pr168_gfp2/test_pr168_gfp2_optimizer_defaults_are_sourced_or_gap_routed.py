from tests.pr168_gfp2.pr168_gfp2_test_support import validate_optimizer_and_seeds


def test_optimizer_defaults_are_sourced_or_gap_routed() -> None:
    validate_optimizer_and_seeds()
