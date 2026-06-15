from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import REPO_ROOT, final_summary


def test_pr165_d3_idempotence():
    before = final_summary()["selected_combination_rows"]
    cmd = [sys.executable, str(REPO_ROOT / "tools" / "build_pr165_d3_quantum_aware_scenario_selection_v3.py"), "--repo-root", str(REPO_ROOT)]
    completed = subprocess.run(cmd, cwd=REPO_ROOT, check=True, capture_output=True, text=True)
    assert "PR165-D3" in completed.stdout
    after = final_summary()["selected_combination_rows"]
    assert before == after
