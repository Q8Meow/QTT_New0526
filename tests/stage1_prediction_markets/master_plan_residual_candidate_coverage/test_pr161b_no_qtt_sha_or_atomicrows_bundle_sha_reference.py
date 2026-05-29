from pathlib import Path


def test_pr161b_no_qtt_integrity_or_atomicrows_digest_authority_strings():
    root = Path(__file__).resolve().parents[3]
    forbidden = (
        "AtomicRows.bundle" + ".sha256",
        "QTT " + "SHA authority",
        "QTT-generated " + "SHA",
    )
    paths = [
        *Path(root, "src/qtt/stage1_prediction_markets/master_plan_residual_candidate_coverage").rglob("*"),
        *Path(root, "tests/stage1_prediction_markets/master_plan_residual_candidate_coverage").rglob("*.py"),
    ]
    for path in paths:
        if path.is_file() and path.suffix in {".py", ".json"}:
            text = path.read_text(encoding="utf-8")
            for pattern in forbidden:
                assert pattern not in text
