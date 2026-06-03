from .pr162d_test_support import assert_quantum_no_live_order


def test_pr162d_quantum_output_does_not_route_to_live_order_submission():
    assert_quantum_no_live_order()
