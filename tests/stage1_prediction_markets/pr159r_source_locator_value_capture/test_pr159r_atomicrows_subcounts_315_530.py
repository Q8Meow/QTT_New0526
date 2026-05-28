from .helpers import counts


def test_pr159r_atomicrows_subcounts_315_530(pr159r_artifacts):
    receipt = counts(pr159r_artifacts)
    assert receipt["atomicrows_public_external_source_required_count"] == 315
    assert receipt["atomicrows_parameter_range_source_required_count"] == 530

