"""Source tier classification for PR162D-R1."""

from __future__ import annotations


def classify_source_tier(source_class: str, source_locator: str) -> str:
    official_hosts = (
        "docs.kalshi.com",
        "docs.polymarket.com",
        "forecastex.com",
        "scikit-learn.org",
        "ta-lib.github.io",
        "pyportfolioopt.readthedocs.io",
        "docs.scipy.org",
        "docs.dwavequantum.com",
        "qiskit-community.github.io",
        "numpy.org",
        "pandas.pydata.org",
    )
    if source_class.startswith("OFFICIAL") or any(host in source_locator for host in official_hosts):
        return "TIER_1_OFFICIAL_OR_PROJECT_DOC"
    if "arxiv.org" in source_locator or "docs.dune.com" in source_locator:
        return "TIER_2_RESEARCH_OR_INSTITUTIONAL"
    if "github.com" in source_locator:
        return "TIER_3_PUBLIC_CODE_RESEARCH"
    return "TIER_4_NON_OFFICIAL_REPLAY_PAPER_CANDIDATE"
