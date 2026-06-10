"""Write narrow PR165-C schema stubs with central vocabulary references."""

from __future__ import annotations

from . import paths as p
from .json_io import write_json
from .report_sharding import VOCAB_REFS


def write_schemas(repo_root) -> None:
    for filename in p.SCHEMA_FILENAMES:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": filename,
            "$comment": "PR165-C schemas reference centralized replay/paper memory consumer vocabularies.",
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "validation_status": {"type": "string"},
                "vocab_refs": {"type": "array", "items": {"type": "string"}},
                "candidate_packet_id": {"type": "string"},
                "qku_id": {"type": "string"},
                "condition_fingerprint_id": {"type": "string"},
                "combination_fingerprint_id": {"type": "string"},
                "authority_boundary_ref": {"type": "string"},
                "core_table_row_id": {"type": "string"},
                "no_orphan_status": {"type": "string"},
            },
            "x_pr165_c_vocab_refs": list(VOCAB_REFS),
        }
        write_json(p.schema_path(repo_root, filename), schema)
