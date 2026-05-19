"""Stage-1 connector semantic binding static consumer machinery."""

from .canonicalize import CanonicalizationResult, canonicalize_semantic_payload
from .ledger import load_json_object, write_json_object
from .validator import (
    PR124_REPORT_PATH,
    consume_pr124_fixture_inputs,
    load_pr124_fixture_inputs,
    validate_pr124_connector_semantic_binding,
)

__all__ = [
    "CanonicalizationResult",
    "PR124_REPORT_PATH",
    "canonicalize_semantic_payload",
    "consume_pr124_fixture_inputs",
    "load_json_object",
    "load_pr124_fixture_inputs",
    "validate_pr124_connector_semantic_binding",
    "write_json_object",
]
