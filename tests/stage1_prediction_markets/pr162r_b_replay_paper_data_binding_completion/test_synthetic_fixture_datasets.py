from src.qtt.stage1_prediction_markets.pr162r_b_replay_paper_data_binding_completion import paths as p


def test_synthetic_fixture_datasets(repo_root, summary):
    assert summary["fixture_datasets_created"] >= 10
    for filename in p.FIXTURE_FILENAMES:
        assert (repo_root / p.FIXTURE_DIR / filename).exists()
