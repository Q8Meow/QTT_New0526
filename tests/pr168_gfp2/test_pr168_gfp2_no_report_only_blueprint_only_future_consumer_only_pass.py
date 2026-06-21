from tests.pr168_gfp2.pr168_gfp2_test_support import root
from tools.pr168_gfp2_constants import REQUIRED_REPORTS


def test_no_report_only_blueprint_only_future_consumer_only_pass() -> None:
    for name in REQUIRED_REPORTS:
        report = root(name)
        assert report["record_count"] >= 0
        assert report["downstream_consumers"]
        assert report["authority_class"]
