from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.pr168_map3_validator import validate_pr168_map3


def main() -> int:
    summary = validate_pr168_map3()
    print(
        "PR168-MAP3 online scouting validation passed: "
        f"online_scout_row_count={summary['online_scout_row_count']} "
        f"distinct_source_url_count={summary['distinct_source_url_count']} "
        f"query_family_count={summary['query_family_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
