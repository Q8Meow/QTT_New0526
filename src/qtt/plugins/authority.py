"""Central authority envelope helpers for PR162E plugin rows."""

from .contracts import PluginAuthorityEnvelope


DEFAULT_AUTHORITY_ENVELOPE = PluginAuthorityEnvelope(
    authority_envelope_id="PR162E_AUTHORITY::NO_LIVE_NO_SOURCE_TRUTH_NO_CONNECTOR_NO_CASH_NO_BACKEND"
)


def default_authority_row() -> dict[str, object]:
    return DEFAULT_AUTHORITY_ENVELOPE.to_row()
