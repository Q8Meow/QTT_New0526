"""Roll up PR162D's 6,502-candidate universe without rebuilding it."""

from __future__ import annotations

from typing import Any

from .json_io import stable_counter


def coverage_rollup_record(inputs: Any) -> dict[str, Any]:
    summary = inputs.pr162d_summary
    router = inputs.pr162d_replay_router_records
    trace = inputs.pr162d_trace_records
    return {
        "record_id": "PR162R_A_PR162D_6502_COVERAGE_ROLLUP",
        "pr162d_consumed_not_rebuilt_flag": True,
        "candidate_universe_source": "docs/master_plan/generated/PR162D_ReplayPaperCandidateRouterQueue.report.json",
        "candidate_universe_expected_count": int(summary.get("candidate_materialization_target_count", 6502)),
        "candidate_universe_observed_count": len(router),
        "traceability_observed_count": len(trace),
        "candidate_progress_status_counts": summary.get("candidate_progress_status_counts", {}),
        "router_route_status_counts": stable_counter(
            record.get("route_status") or record.get("replay_paper_route_status") or "ROUTED_OR_PARTIAL"
            for record in router
        ),
        "coverage_status": "ROLLED_UP_FROM_PR162D_NO_REBUILD",
        "live_order_authority": False,
    }
