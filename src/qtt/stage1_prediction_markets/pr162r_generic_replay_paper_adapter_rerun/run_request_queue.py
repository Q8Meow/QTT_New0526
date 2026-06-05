"""Replay/paper run-request candidate queue builders."""

from __future__ import annotations

from typing import Any


def build_replay_run_requests(replay_inputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(replay_inputs, start=1):
        rows.append(
            {
                "replay_run_request_candidate_id": f"PR162R_REPLAY_RUN_REQUEST_CANDIDATE::{index:05d}",
                "adapter_input_ref": row["adapter_input_id"],
                "candidate_packet_ref": row["candidate_packet_ref"],
                "qku_ids": row["qku_ids"],
                "run_request_status": "REPLAY_RUN_REQUEST_FILL_REQUIRED",
                "missing_inputs": row["missing_inputs"],
                "fill_action_refs": row["fill_action_refs"],
                "source_truth_status": row["source_truth_status"],
                "candidate_truth_status": row["candidate_truth_status"],
                "replay_execution_count": 0,
                "result_packet_created_count": 0,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def build_paper_run_requests(paper_inputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(paper_inputs, start=1):
        rows.append(
            {
                "paper_run_request_candidate_id": f"PR162R_PAPER_RUN_REQUEST_CANDIDATE::{index:05d}",
                "adapter_input_ref": row["adapter_input_id"],
                "candidate_packet_ref": row["candidate_packet_ref"],
                "qku_ids": row["qku_ids"],
                "run_request_status": "PAPER_RUN_REQUEST_FILL_REQUIRED",
                "missing_inputs": row["missing_inputs"],
                "fill_action_refs": row["fill_action_refs"],
                "source_truth_status": row["source_truth_status"],
                "candidate_truth_status": row["candidate_truth_status"],
                "paper_execution_count": 0,
                "result_packet_created_count": 0,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows


def build_paired_run_plan(
    replay_requests: list[dict[str, Any]],
    paper_requests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    paper_by_packet = {row["candidate_packet_ref"]: row for row in paper_requests}
    rows: list[dict[str, Any]] = []
    for index, replay in enumerate(replay_requests, start=1):
        paper = paper_by_packet[replay["candidate_packet_ref"]]
        rows.append(
            {
                "paired_run_request_candidate_id": f"PR162R_PAIRED_RUN_REQUEST_CANDIDATE::{index:05d}",
                "candidate_packet_ref": replay["candidate_packet_ref"],
                "replay_run_request_candidate_ref": replay["replay_run_request_candidate_id"],
                "paper_run_request_candidate_ref": paper["paper_run_request_candidate_id"],
                "paired_status": "PAIRED_FILL_REQUIRED",
                "fill_action_refs": sorted(set(replay["fill_action_refs"]) | set(paper["fill_action_refs"])),
                "replay_execution_count": 0,
                "paper_execution_count": 0,
                "result_packet_created_count": 0,
                "live_order_authority": False,
                "validation_status": "PASS",
            }
        )
    return rows
