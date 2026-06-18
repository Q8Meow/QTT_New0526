"""Execution and TCA plugin adapter exports."""

from ..contracts import PluginAdapterBase


class ExecutionTCAPluginAdapter(PluginAdapterBase):
    plugin_family = "EXECUTION_TCA_PLUGIN"
    runtime_lane = "REPLAY_PATH_ONLY"
