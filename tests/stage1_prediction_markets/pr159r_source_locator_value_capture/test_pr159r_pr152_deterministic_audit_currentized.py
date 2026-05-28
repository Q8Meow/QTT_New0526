from pathlib import Path


def test_pr159r_pr152_deterministic_audit_currentized():
    root = Path(__file__).resolve().parents[3]
    audit = root / "docs/master_plan/generated/PR152_GrandGlobalDebugLogicalConsistencyAuditEntireQTTRepo.report.json"
    assert audit.exists()

