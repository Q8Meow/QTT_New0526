"""PR127 per-venue execution lifecycle model builder."""

from .builder import (
    ACTIVE_STAGE1_VENUES,
    DETERMINISTIC_FIXTURE_TIME,
    FIXTURE_AUTHORITY_CLASS,
    READY_FOR_PR127_FIXTURE_SCOPE_MODEL,
    REQUIRED_SEMANTIC_FAMILIES,
    build_execution_lifecycle_artifacts,
    load_fixture_inputs,
)
from .handoff import REQUIRED_FUTURE_NORMALIZATION_DIMENSIONS
from .phases import GENERIC_FIXTURE_PHASE_FAMILIES
from .transitions import GENERIC_FIXTURE_TRANSITION_FAMILIES

__all__ = [
    "ACTIVE_STAGE1_VENUES",
    "DETERMINISTIC_FIXTURE_TIME",
    "FIXTURE_AUTHORITY_CLASS",
    "GENERIC_FIXTURE_PHASE_FAMILIES",
    "GENERIC_FIXTURE_TRANSITION_FAMILIES",
    "READY_FOR_PR127_FIXTURE_SCOPE_MODEL",
    "REQUIRED_FUTURE_NORMALIZATION_DIMENSIONS",
    "REQUIRED_SEMANTIC_FAMILIES",
    "build_execution_lifecycle_artifacts",
    "load_fixture_inputs",
]
