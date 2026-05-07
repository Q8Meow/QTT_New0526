from pathlib import Path
import json


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
