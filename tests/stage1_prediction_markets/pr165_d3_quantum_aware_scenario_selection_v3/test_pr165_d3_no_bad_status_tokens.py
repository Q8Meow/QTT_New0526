from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import assert_no_forbidden_status_tokens


def test_pr165_d3_no_bad_status_tokens():
    assert_no_forbidden_status_tokens()
