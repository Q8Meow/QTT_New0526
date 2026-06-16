from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import REPO_ROOT, assert_manifest_is_synchronized, final_summary
from src.qtt.stage1_prediction_markets.pr165_d3_quantum_aware_scenario_selection_v3 import constants as c


def test_pr165_d3_build_outputs():
    summary = final_summary()
    assert summary["generated_root_report_count"] == 136
    assert summary["generated_schema_count"] == 137
    assert summary["generated_shard_count"] > 0
    assert summary["selected_combination_rows"] > 0
    assert summary["quantum_comparator_rows"] == 559
    for report in c.REPORT_FILENAMES:
        assert (REPO_ROOT / c.GENERATED_DIR / report).exists()
    assert_manifest_is_synchronized()
