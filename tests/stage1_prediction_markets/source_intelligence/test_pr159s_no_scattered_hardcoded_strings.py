from pathlib import Path

from src.qtt.stage1_prediction_markets.source_intelligence.pr159s_open_intake import constants as c


def test_pr159s_source_and_profit_tags_are_centralized_in_constants():
    package_root = Path(__file__).resolve().parents[3] / "src/qtt/stage1_prediction_markets/source_intelligence/pr159s_open_intake"
    non_constant_files = [
        path
        for path in package_root.glob("*.py")
        if path.name not in {"constants.py", "__init__.py"}
    ]
    source_tag_literal = f'"{c.SourceProvenanceTag.NON_OFFICIAL_PARAMETER_CANDIDATE.value}"'
    profit_tag_literal = f'"{c.ProfitValidationTag.REPLAY_AND_PAPER_PROFITABLE.value}"'
    assert all(source_tag_literal not in path.read_text(encoding="utf-8") for path in non_constant_files)
    assert all(profit_tag_literal not in path.read_text(encoding="utf-8") for path in non_constant_files)
