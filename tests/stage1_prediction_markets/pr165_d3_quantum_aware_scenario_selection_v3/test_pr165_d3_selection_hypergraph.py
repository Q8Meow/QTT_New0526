from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import assert_reports_for_test


def test_pr165_d3_selection_hypergraph():
    assert_reports_for_test(__file__)
