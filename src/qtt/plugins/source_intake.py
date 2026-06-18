"""External candidate source intake helpers."""

from __future__ import annotations


def candidate_source_row(
    *,
    source_id: str,
    source_url: str,
    source_class: str,
    topic: str,
    plugin_family_mapping: str,
) -> dict[str, object]:
    return {
        "source_id": source_id,
        "scout_query": topic,
        "source_url": source_url,
        "source_class": source_class,
        "topic": topic,
        "plugin_family_mapping": plugin_family_mapping,
        "source_truth_accepted": False,
        "replay_paper_route": "PR162E_ExternalCandidateToPluginMap.report.json",
        "owner_agent_route": "External Scout Agent",
        "confidence": "CANDIDATE_PROVISIONAL",
    }
