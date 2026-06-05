from pathlib import Path
import tempfile

from src.qtt.stage1_prediction_markets.pr162r_generic_replay_paper_adapter_rerun import (
    paths as p,
)
from src.qtt.stage1_prediction_markets.pr162r_generic_replay_paper_adapter_rerun import (
    validators,
)


def test_orphan_audit(summary, records):
    row = records("PR162R_OrphanCandidateReportAudit.report.json")[0]
    assert row["orphan_candidate_count"] == 0
    assert row["orphan_generated_report_count"] == 0
    assert row["orphan_qku_count"] == 0
    assert row["orphan_handoff_count"] == 0
    assert summary["orphan_candidate_count"] == 0


def test_pr162r_b_downstream_reports_are_not_pr162r_orphans():
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_root = Path(temp_dir)
        generated_dir = repo_root / p.GENERATED_DIR
        generated_dir.mkdir(parents=True)
        for filename in p.REPORT_FILENAMES:
            (generated_dir / filename).write_text("{}", encoding="utf-8")
        (generated_dir / "PR162R_A_UpstreamAudit.report.json").write_text(
            "{}",
            encoding="utf-8",
        )
        (generated_dir / "PR162R_B_DownstreamBinding.report.json").write_text(
            "{}",
            encoding="utf-8",
        )

        failures: list[str] = []
        validators._validate_generated_file_set(repo_root, failures)

    assert failures == []
