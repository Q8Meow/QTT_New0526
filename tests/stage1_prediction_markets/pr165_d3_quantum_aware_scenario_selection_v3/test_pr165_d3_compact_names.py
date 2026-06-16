from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import assert_compact_names_only, assert_reports_for_test


def test_pr165_d3_compact_names():
    assert_reports_for_test(__file__)
    assert_compact_names_only()
