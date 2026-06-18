"""Algorithm plugin adapter exports."""

from ..contracts import PluginAdapterBase


class AlgorithmPluginAdapter(PluginAdapterBase):
    plugin_family = "ALGORITHM_PLUGIN"
