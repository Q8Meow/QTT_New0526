from src.qtt.stage1_prediction_markets.pr166_sf_repair_materialization_before_retest import constants as c
from src.qtt.stage1_prediction_markets.pr166_sf_repair_materialization_before_retest.io import read_json, resolve_repo_relative
from src.qtt.stage1_prediction_markets.pr166_sf_repair_materialization_before_retest.report_writer import write_artifacts
from .conftest import REPO_ROOT


def _snapshot() -> dict[str, bytes]:
    paths = []
    for filename in c.REPORT_FILENAMES:
        path = REPO_ROOT / c.GENERATED_DIR / filename
        paths.append(path)
        payload = read_json(path)
        paths.extend(resolve_repo_relative(REPO_ROOT, shard) for shard in payload.get("shard_files") or [])
    paths.extend(REPO_ROOT / c.SCHEMA_DIR / filename for filename in c.SCHEMA_FILENAMES)
    return {path.relative_to(REPO_ROOT).as_posix(): path.read_bytes() for path in sorted(paths)}


def test_pr166_sf_builder_is_idempotent():
    write_artifacts(REPO_ROOT)
    before = _snapshot()
    write_artifacts(REPO_ROOT)
    assert _snapshot() == before
