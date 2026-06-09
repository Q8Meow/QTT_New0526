"""Write narrow PR165-B schema stubs with central vocabulary references."""

from __future__ import annotations

from . import paths as p
from .json_io import write_json
from .report_sharding import VOCAB_REFS


def write_schemas(repo_root) -> None:
    for filename in p.SCHEMA_FILENAMES:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": filename,
            "$comment": "PR165-B schemas reference central condition-memory vocabularies.",
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "validation_status": {"type": "string"},
                "vocab_refs": {"type": "array", "items": {"type": "string"}},
                "candidate_packet_id": {"type": "string"},
                "qku_id": {"type": "string"},
                "condition_fingerprint_id": {"type": "string"},
                "combination_fingerprint_id": {"type": "string"},
                "memory_classification": {"type": "string"},
                "memory_action_policy": {"type": "string"},
            },
            "x_pr165_b_vocab_refs": list(VOCAB_REFS),
        }
        write_json(p.schema_path(repo_root, filename), schema)
