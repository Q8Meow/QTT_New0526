from __future__ import annotations

from tools.pr168_gfp2_constants import BASELINE_COUNTS
from tools.pr168_gfp2_validator import (
    load,
    root,
    validate_agent_and_dag,
    validate_counts,
    validate_gap_repair_recovery,
    validate_handoffs,
    validate_no_real_positive_negative_without_accepted_data,
    validate_nonofficial_sources,
    validate_optimizer_and_seeds,
    validate_prior_supersession,
    validate_quantum,
    validate_reports_exist,
    validate_windows_linux,
    validate_zero_positive_not_final,
)


def full_universe_count() -> int:
    return root("PR168_GFP2_AllQKUComputabilityClassificationLedger.report.json")["record_count"]
