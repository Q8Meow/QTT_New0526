from tools.pr168_gfp2r_config import ROW_SHARDS
from tests.pr168_gfp2r._helpers import records


def test_pr168_gfp2r_windows_linux_path_and_basetemp_safe() -> None:
    discovery = records("PR168_GFP2R_InputDiscovery")
    assert discovery["snapshot_jsonl_refs"]
    for path in ROW_SHARDS.values():
        assert "\\" not in path.as_posix()
