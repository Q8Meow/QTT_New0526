from .pr162d_test_support import assert_no_scattered_boundary_literals


def test_pr162d_no_scattered_boundary_literals_uses_constants():
    assert_no_scattered_boundary_literals()
