from __future__ import annotations

import pytest

from tools.build_pr168_gfp2_full_universe_formula_data_provenance_reopen import build_all_reports


@pytest.fixture(scope="session", autouse=True)
def _build_pr168_gfp2_reports() -> None:
    build_all_reports()
