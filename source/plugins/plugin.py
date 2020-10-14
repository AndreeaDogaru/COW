from collections import namedtuple
import importlib
import inspect
import os
from typing import List


def get_plugins(block_list):
    block = set(block_list + ["plugin"])
    plugin_groups = {}
    for filename in os.listdir("plugins"):
        if filename.endswith(".py"):
            module_name = filename[:-3]
            if not (module_name in block):
                module = importlib.import_module(f"source.plugins.{module_name}")
                plugin = inspect.getmembers(module, inspect.isclass)[0][1]()
                add_plugin(plugin_groups, plugin)
    return plugin_groups


def add_plugin(plugin_groups, plugin):
    if plugin.group_name not in plugin_groups:
        plugin_groups[plugin.group_name] = []
    plugin_groups[plugin.group_name].append(plugin)


PluginAction = namedtuple('PluginAction', ['name', 'function'])


class Plugin:
    def __init__(self, plugin_name, group_name, z_index=0):
        self.group_name = group_name
        self.plugin_name = plugin_name
        self.z_index = z_index

    def get_actions(self) -> List[PluginAction]:
        raise NotImplementedError()

    def process(self, frame):
        return frame
