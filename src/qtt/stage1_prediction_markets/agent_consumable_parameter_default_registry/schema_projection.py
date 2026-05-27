"""Schema projection derived from PR155 constants."""

from __future__ import annotations

from typing import Any

from . import constants as c


def registry_record_schema_projection() -> dict[str, Any]:
    return {
        "type": "object",
        "required": list(c.RECORD_REQUIRED_FIELDS),
        "properties": {
            "registry_consumption_state": {
                "enum": list(c.REGISTRY_CONSUMPTION_STATES)
            },
            "agent_assignment_state": {"enum": list(c.AGENT_ASSIGNMENT_STATES)},
            "default_use_class": {"enum": list(c.DEFAULT_USE_CLASSES)},
            "atomicrows_compatibility_state": {
                "enum": list(c.ATOMICROWS_COMPATIBILITY_STATES)
            },
            "quantum_forward_compatibility_state": {
                "enum": list(c.QUANTUM_FORWARD_COMPATIBILITY_STATES)
            },
            "optimizer_readiness_hint": {"enum": list(c.OPTIMIZER_READINESS_HINTS)},
            "latency_path_state": {"enum": list(c.LATENCY_PATH_STATES)},
        },
        "additionalProperties": True,
    }


def registry_artifact_schema_projection() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": c.REGISTRY_TYPE,
        "type": "object",
        "required": list(c.REGISTRY_TOP_LEVEL_KEYS),
        "properties": {
            "registry_type": {"const": c.REGISTRY_TYPE},
            "pr_id": {"const": c.PR_ID},
            "semantic_task_id": {"const": c.SEMANTIC_TASK_ID},
            "authority_class": {"enum": list(c.AUTHORITY_CLASS_VALUES)},
            "records": {"type": "array", "items": registry_record_schema_projection()},
            "blocked_records": {
                "type": "array",
                "items": registry_record_schema_projection(),
            },
        },
        "additionalProperties": True,
    }
