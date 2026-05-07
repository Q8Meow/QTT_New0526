from pathlib import Path


def test_no_runtime_artifacts_present():
    forbidden = ['AtomicRows.bundle.jsonl', 'AtomicRows.bundle.sha256', '.env', 'secrets.json']
    for name in forbidden:
        assert not any(Path('.').rglob(name))


def test_full_master_plan_markers_present():
    content = Path('docs/master_plan/QTT_MasterPlan_Current.md').read_text(encoding='utf-8')
    assert 'v9.9.778' in content
    assert 'OWNER-START READY FOR EXACT FIRST-PR SCHEMA-ONLY SCOPE' in content
    assert content.count('\n') + 1 > 100000


def test_source_packet_markers_present():
    content = Path('docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md').read_text(encoding='utf-8')
    assert 'packet_id = QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET' in content
    assert 'packet_version = v1.3A_OWNER_APPROVED_EXECUTION_MECHANICS_ABSTRACTION_AND_RETRIEVAL_READINESS_CURRENTIZATION_NOT_EXTERNAL_FACT_AUTHORITY' in content
    assert 'owner_source_evidence_definitions_packet_can_authorize_external_fact_value = false' in content
