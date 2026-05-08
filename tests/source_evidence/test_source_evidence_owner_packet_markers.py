from pathlib import Path

from tools.validate_source_evidence_static import (
    CONNECTOR_SEMANTIC_POPULATION_BLOCKED_MARKER,
    EXTERNAL_FACT_AUTHORITY_BLOCKED_MARKER,
    PACKET_ACCEPTS_NO_FACTS_MARKER,
    PACKET_RETRIEVES_NO_FACTS_MARKER,
    PACKET_VERSION_MARKER,
)


OWNER_PACKET_PATH = Path(
    "docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md"
)


def test_owner_source_evidence_packet_contains_pr4_static_markers():
    text = OWNER_PACKET_PATH.read_text(encoding="utf-8")

    assert PACKET_VERSION_MARKER in text
    assert EXTERNAL_FACT_AUTHORITY_BLOCKED_MARKER in text
    assert CONNECTOR_SEMANTIC_POPULATION_BLOCKED_MARKER in text
    assert PACKET_RETRIEVES_NO_FACTS_MARKER in text
    assert PACKET_ACCEPTS_NO_FACTS_MARKER in text
