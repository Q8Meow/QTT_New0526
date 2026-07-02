import json
from pathlib import Path
from typing import Any

from tests.pr169_dash1.conftest import BASE


def _walk(value: Any) -> list[Any]:
    values = [value]
    if isinstance(value, dict):
        for key, child in value.items():
            values.append(key)
            values.extend(_walk(child))
    elif isinstance(value, list):
        for child in value:
            values.extend(_walk(child))
    return values


def test_rejected_timeline_tokens_absent_from_new_artifact_names_fields_and_ids() -> None:
    forbidden = ("timeline",)
    for path in BASE.rglob("*"):
        assert not any(token in path.name.lower() for token in forbidden), path
        if path.suffix not in {".json", ".jsonl"}:
            continue
        payloads = []
        if path.suffix == ".jsonl":
            payloads = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        else:
            payloads = [json.loads(path.read_text(encoding="utf-8"))]
        for payload in payloads:
            for value in _walk(payload):
                if isinstance(value, str) and ("_id" in value.lower() or "status" in value.lower()):
                    assert not any(token in value.lower() for token in forbidden), (path, value)
