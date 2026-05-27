"""Schema projection derived from PR156 constants."""

from __future__ import annotations

from typing import Any

from . import constants as c


def registry_record_schema_projection() -> dict[str, Any]:
    return {
        "type": "object",
        "required": list(c.RECORD_REQUIRED_FIELDS),
        "properties": {
            "record_kind": {"enum": list(c.RECORD_KIND_VALUES)},
            "population_lane": {"enum": list(c.POPULATION_LANE_VALUES)},
            "agent_binding_state": {"enum": list(c.AGENT_BINDING_STATE_VALUES)},
            "template_type": {
                "anyOf": [
                    {"type": "null"},
                    {"enum": list(c.UNIVERSAL_INTAKE_TEMPLATE_TYPE_VALUES)},
                ]
            },
            "candidate_instance_state": {
                "enum": list(c.CANDIDATE_INSTANCE_STATE_VALUES)
            },
            "candidate_research_intake_state": {
                "enum": list(c.SOURCE_EVIDENCE_REQUIREMENT_STATE_VALUES)
            },
            "applicability_class": {
                "enum": list(c.CLASSICAL_QUANTUM_HYBRID_APPLICABILITY_VALUES)
            },
            "owner_strategy_priority_state": {
                "enum": list(c.OWNER_STRATEGY_PRIORITY_STATE_VALUES)
            },
            "atomicrows_ingestion_state": {
                "enum": list(c.ATOMICROWS_INGESTION_STATE_VALUES)
            },
            "scoring_ranking_readiness_state": {
                "enum": list(c.SCORING_RANKING_READINESS_STATE_VALUES)
            },
            "optimizer_routing_hint": {"enum": list(c.OPTIMIZER_ROUTING_HINT_VALUES)},
            "replay_paper_routing_hint": {
                "enum": list(c.REPLAY_PAPER_ROUTING_HINT_VALUES)
            },
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
