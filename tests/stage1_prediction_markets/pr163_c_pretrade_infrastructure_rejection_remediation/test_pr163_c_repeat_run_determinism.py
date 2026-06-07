import subprocess
import sys


def test_pr163_c_repeat_run_determinism():
    result = subprocess.run(
        [sys.executable, "tools/build_pr163_c_pretrade_infrastructure_rejection_remediation.py", "--verify-idempotent"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "PR163_C_PRETRADE_INFRA_REPAIR_IDEMPOTENT" in result.stdout
