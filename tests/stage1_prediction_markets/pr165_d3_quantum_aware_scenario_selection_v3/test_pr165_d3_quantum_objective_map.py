from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import assert_reports_for_test


def test_pr165_d3_quantum_objective_map():
    assert_reports_for_test(__file__)
