"""PR162C formula value extraction facade."""

from __future__ import annotations

from .qku_registry_delta import parameter_value_delta_records, tradable_value_candidate_delta_records


def extracted_value_records() -> list[dict[str, object]]:
    parameters = parameter_value_delta_records()
    return parameters + tradable_value_candidate_delta_records(parameters)
