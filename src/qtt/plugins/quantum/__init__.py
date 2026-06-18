"""Quantum structural plugin adapter exports."""

from ..contracts import PluginAdapterBase


class QuantumRecipePluginAdapter(PluginAdapterBase):
    plugin_family = "QUANTUM_RECIPE_PLUGIN"
    runtime_lane = "PRECOMPUTE_PATH"
