from tests.stage1_prediction_markets.pr160_split_reclassification_route_closure.pr160_test_support import ROOT


def test_pr160_no_scattered_hardcoded_blocker_no_authority_vocabulary():
    src_dir = ROOT / "src/qtt/stage1_prediction_markets/pr160_split_reclassification_route_closure"
    constants_text = (src_dir / "constants.py").read_text(encoding="utf-8")
    assert "class ReclassificationFinalRouteClass" in constants_text
    assert "class BlockerClass" in constants_text
    for path in src_dir.glob("*.py"):
        if path.name == "constants.py":
            continue
        text = path.read_text(encoding="utf-8")
        assert '"PR160_NO_RUNTIME_NO_LIVE_NO_CONNECTOR_BINDING"' not in text
        assert '"MULTIPLE_PLAUSIBLE_ROUTES_OWNER_CHOICE_REQUIRED"' not in text
