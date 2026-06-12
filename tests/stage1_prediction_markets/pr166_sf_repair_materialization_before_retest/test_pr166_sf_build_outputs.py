from .conftest import REPO_ROOT
from src.qtt.stage1_prediction_markets.pr166_sf_repair_materialization_before_retest import constants as c


def test_pr166_sf_required_reports_schemas_and_shards_exist(pr166_sf_payloads):
    assert len(c.REPORT_FILENAMES) == 58
    for filename in c.REPORT_FILENAMES:
        assert (REPO_ROOT / c.GENERATED_DIR / filename).is_file()
        assert pr166_sf_payloads[filename]["created_by_pr"] == "PR166-SF"
        assert pr166_sf_payloads[filename]["schema_ref"] == c.REPORT_SCHEMA_REFS[filename]
    for schema_name in c.SCHEMA_FILENAMES:
        assert (REPO_ROOT / c.SCHEMA_DIR / schema_name).is_file()
    assert sorted((REPO_ROOT / c.SHARD_DIR).glob("PR166_SF_*.json"))
    assert not list((REPO_ROOT / c.GENERATED_DIR).glob("*.sha256"))
