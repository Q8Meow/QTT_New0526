from pathlib import Path
import json

from tools.master_plan_ingest import build_section_manifest, build_traceability_report


def test_generated_reports_exist_and_shape():
    for p in [
        'docs/master_plan/generated/SectionManifest.json',
        'docs/master_plan/generated/TraceabilityReport.json',
        'docs/master_plan/generated/FirstPrScopeReport.json',
    ]:
        assert Path(p).exists()
        assert isinstance(json.loads(Path(p).read_text(encoding='utf-8')), dict)


def test_section_manifest_generated_from_full_master_plan():
    manifest = json.loads(Path('docs/master_plan/generated/SectionManifest.json').read_text(encoding='utf-8'))
    assert manifest['source'] == 'full_owner_master_plan'
    assert manifest['line_count'] > 100000
    assert manifest['section_count'] > 100


def test_ingest_reports_have_deterministic_static_metadata_fields():
    path = Path('docs/master_plan/QTT_MasterPlan_Current.md')
    text = path.read_text(encoding='utf-8')
    manifest = build_section_manifest(
        'docs/master_plan/QTT_MasterPlan_Current.md',
        text,
        file_size_bytes=path.stat().st_size,
    )
    trace = build_traceability_report('docs/master_plan/QTT_MasterPlan_Current.md', manifest, text)

    assert manifest['schema_version'] == 2
    assert manifest['deterministic_output'] is True
    assert manifest['parser'] == 'tools/master_plan_ingest.py'
    assert manifest['file_size_bytes'] == path.stat().st_size
    assert manifest['line_count'] == trace['line_count']
    assert manifest['file_size_bytes'] == trace['file_size_bytes']
    assert manifest['section_count'] == trace['sections_indexed']
    assert manifest['canonical_id_count'] == trace['canonical_ids_indexed']
    assert all(manifest['required_markers'].values())
    assert all(trace['consistency_checks'].values())
