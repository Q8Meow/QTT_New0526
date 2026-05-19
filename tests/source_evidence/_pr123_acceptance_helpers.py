from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from src.qtt.source_evidence.acceptance import validator as acceptance
from tools.validate_source_evidence_acceptance import rejection_case_candidate


FIXTURE_PATH = Path(
    "tests/fixtures/source_evidence/pr106_evidence_executor/pr123_candidate_packets.v1.fixture.json"
)


def fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def valid_candidate() -> dict[str, Any]:
    return copy.deepcopy(fixture()["candidate_source_evidence_packets"][0])


def rejection_case(case_id: str) -> dict[str, Any]:
    return next(
        case
        for case in fixture()["rejection_mutation_cases"]
        if case["case_id"] == case_id
    )


def mutated_candidate(case_id: str) -> dict[str, Any]:
    return rejection_case_candidate(valid_candidate(), rejection_case(case_id))


def execute(candidate: dict[str, Any]):
    return acceptance.build_acceptance_artifacts(candidate)


def assert_rejected_with(case_id: str, expected_code: str) -> None:
    result = execute(mutated_candidate(case_id))

    assert result.decision_receipt["decision"] == "REJECTED"
    assert expected_code in result.decision_receipt["rejection_codes"]
    assert result.accepted_packet is None
    assert result.accepted_ledger_record is None
    assert result.reject_receipt is not None
    assert result.reject_receipt["accepted_source_evidence_packet_created"] is False
    assert result.reject_receipt["accepted_ledger_record_created"] is False


def set_text_digests(candidate: dict[str, Any], raw_text: str, canonical_text: str) -> None:
    raw_digest = acceptance.text_digest(raw_text)
    canonical_digest = acceptance.text_digest(canonical_text)
    candidate["raw_capture_text"] = raw_text
    candidate["canonical_text"] = canonical_text
    candidate["raw_capture_digest_sha256"] = raw_digest
    candidate["canonical_text_digest_sha256"] = canonical_digest
    candidate["source_digest_sha256"] = acceptance.text_digest(
        f"{raw_digest}:{canonical_digest}"
    )
