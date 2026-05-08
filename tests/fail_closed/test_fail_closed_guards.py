from pathlib import Path

from tools.master_plan_traceability_check import (
    MASTER_PLAN_MARKERS,
    MIN_MASTER_PLAN_BYTES,
    MIN_MASTER_PLAN_LINES,
    SOURCE_EVIDENCE_PACKET_MARKERS,
)
from tools.validate_no_runtime_artifacts import ScanOptions, scan_repository


def test_no_runtime_artifacts_present():
    violations = scan_repository(Path('.'), ScanOptions())
    forbidden = ['AtomicRows.bundle.jsonl', 'AtomicRows.bundle.sha256', '.env', 'secrets.json']
    for name in forbidden:
        assert not any(name in violation for violation in violations)


def test_full_master_plan_markers_present():
    path = Path('docs/master_plan/QTT_MasterPlan_Current.md')
    content = path.read_text(encoding='utf-8')
    assert path.stat().st_size >= MIN_MASTER_PLAN_BYTES
    assert content.count('\n') + 1 >= MIN_MASTER_PLAN_LINES
    for marker in MASTER_PLAN_MARKERS.values():
        assert marker in content


def test_source_packet_markers_present():
    content = Path('docs/master_plan/source_evidence/QTT_OWNER_SOURCE_EVIDENCE_DEFINITIONS_PACKET.md').read_text(encoding='utf-8')
    for marker in SOURCE_EVIDENCE_PACKET_MARKERS.values():
        assert marker in content


def test_static_no_runtime_artifact_scanner_accepts_current_repo_surface():
    violations = scan_repository(
        Path('.'),
        ScanOptions(
            forbid_source_retrieval=True,
            forbid_source_acceptance=True,
            forbid_connector_binding=True,
            forbid_private_state_fetch=True,
            forbid_order_execution=True,
            forbid_neural_training=True,
            forbid_neural_inference=True,
            forbid_external_repo_clone=True,
            forbid_package_install_scripts=True,
        ),
    )
    assert violations == []
