from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.qtt.stage1_prediction_markets.pr159r_source_locator_value_capture import constants as c
from src.qtt.stage1_prediction_markets.pr159r_source_locator_value_capture.validator import (
    validate_existing_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def _load(rel_path: Path):
    return json.loads((REPO_ROOT / rel_path).read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def pr159r_validation_result():
    result = validate_existing_artifacts(REPO_ROOT)
    assert not result.failures, "\n".join(result.failures)
    return result


@pytest.fixture(scope="session")
def pr159r_artifacts(pr159r_validation_result):
    return {
        "master": _load(c.MASTER_REPORT_PATH),
        "targets": _load(c.TARGET_RECONCILIATION_REGISTRY_PATH),
        "requeue": _load(c.PR160_REQUEUE_RECONCILIATION_PATH),
        "candidates": _load(c.CANDIDATE_PACKET_REGISTRY_PATH),
        "accepted": _load(c.ACCEPTED_PACKET_REGISTRY_PATH),
        "ledger": _load(c.TARGET_FIELD_LEDGER_REGISTRY_PATH),
        "fill_paths": _load(c.UNRESOLVED_EXACT_FILL_PATH_PATH),
        "agent_matrix": _load(c.TARGET_AGENT_MATRIX_PATH),
        "search_plan": _load(c.OFFICIAL_SOURCE_SEARCH_PLAN_PATH),
        "locator_matrix": _load(c.EXACT_LOCATOR_EXTRACTION_MATRIX_PATH),
        "source_family_reuse": _load(c.SOURCE_FAMILY_REUSABLE_ACCEPTANCE_MATRIX_PATH),
        "second_pass_attempts": _load(c.SECOND_PASS_EXACT_ACCEPTANCE_ATTEMPT_MATRIX_PATH),
        "pr154_completion": _load(c.PR154_SOURCE_COMPLETION_REGISTRY_PATH),
        "atomic_completion": _load(c.ATOMICROWS_SOURCE_READY_REGISTRY_PATH),
        "pr161_handoff": _load(c.PR161_MATERIALIZATION_HANDOFF_PATH),
        "selection": _load(c.SELECTION_READINESS_UPDATE_PATH),
        "trade": _load(c.TRADE_CONTEXT_UPDATE_PATH),
        "scoring": _load(c.SCORING_RANKING_UPDATE_PATH),
        "latency": _load(c.LOW_LATENCY_UPDATE_PATH),
        "quantum": _load(c.QUANTUM_UPSTREAM_DOWNSTREAM_BRIDGE_PATH),
        "quantum_provider": _load(c.QUANTUM_PROVIDER_READINESS_PATH),
    }


def records(payload):
    return payload["records"]
