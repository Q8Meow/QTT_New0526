"""PR162A fetch-plan and owner materialization command records."""

from __future__ import annotations

from typing import Any

from . import constants as c


def fetch_plan_records(source_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, source in enumerate(source_records, start=1):
        blocked = source["access_rights_status"] != "PUBLIC_UNAUTHENTICATED_CANDIDATE_USE_OK"
        plan_id = f"PR162A-FETCH-PLAN-{index:03d}"
        records.append(
            {
                "record_id": plan_id,
                "created_by_pr": c.PR_ID,
                "authority_class": c.AUTHORITY_CLASS,
                "source_candidate_ref": source["record_id"],
                "source_name": source["source_name"],
                "source_class": source["source_class"],
                "source_classes": source["source_classes"],
                "source_locator": source["source_locator"],
                "source_endpoint_family": source["source_endpoint_family"],
                "access_rights_status": source["access_rights_status"],
                "materialization_mode": source["materialization_mode"],
                "ci_requires_network": False,
                "network_disabled_by_default_flag": True,
                "bounded_fetch_caps": {
                    "max_rows": 1000,
                    "max_bytes": 250000,
                    "timeout_seconds": 20,
                    "retry_count": 0,
                },
                "owner_materialization_command_ref": f"{plan_id}-OWNER-COMMAND",
                "owner_command_type": "STRUCTURED_REVIEW_PLAN_NOT_EXECUTED_BY_CI",
                "owner_command_parameters": {
                    "method": "GET_OR_POST_AS_DOCUMENTED",
                    "endpoint_family": source["source_endpoint_family"],
                    "repo_local_output_root": c.DATASET_ROOT.as_posix(),
                    "requires_credentials": source["credential_required_flag"],
                    "requires_private_state": source["private_state_flag"],
                    "requires_order_endpoint": source["order_endpoint_dependency_flag"],
                },
                "execute_in_pr162a_default_build_flag": False,
                "safe_to_execute_without_owner_review_flag": not blocked,
                "blocked_reason": source["blocker_code"] if blocked else "NETWORK_DISABLED_BY_DEFAULT_IN_CI",
                "blocker_code": source["blocker_code"] if blocked else "PR162A_BLOCKED_NETWORK_DISABLED_BY_DEFAULT",
                "recommended_owner_action": "REVIEW_TERMS_AND_RUN_BOUNDED_FETCH_OUTSIDE_CI"
                if not blocked
                else "PROVIDE_OWNER_ATTESTATION_OR_REJECT_SOURCE",
            }
        )
    return records
