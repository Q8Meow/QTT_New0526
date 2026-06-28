from ._helpers import read_json


def test_live_dryrun_and_shadow_handoffs_are_future_only() -> None:
    for name in ("to_live_dry.report.json", "to_shadow.report.json"):
        report = read_json(name)
        assert report["non_authority_handoff_flag"] is True
        assert report["live_authority_flag"] is False
        assert report["order_authority_flag"] is False
