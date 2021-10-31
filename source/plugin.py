from typing import List

import importlib
import inspect
from pathlib import Path
from collections import namedtuple


def get_plugin_groups(block_list):
    groups = {}
    for plugin in get_plugins(block_list):
        add_plugin(groups, plugin)
    return groups


def get_plugins(block_list):
    block = set(block_list + ["plugin", "__pycache__"])
    plugins = []
    for plugin_path in Path("plugins").iterdir():
        module_name = plugin_path.stem
        if module_name in block:
            continue
        if plugin_path.is_dir() and not (plugin_path / f"{module_name}.py").exists():
            continue
        if plugin_path.suffix == ".py":
            plugin = load_plugin_from_module(module_name)  
        else:  # directory
            plugin = load_plugin_from_module(f"{module_name}.{module_name}")
        plugins.append(plugin)

    return plugins


def load_plugin_from_module(module_name):
    module = importlib.import_module(f"plugins.{module_name}")
    members = inspect.getmembers(module, inspect.isclass)
    plugin = [m[1] for m in members
                if m[1].__module__.endswith(module_name) and issubclass(m[1], Plugin)][0]()
    return plugin

def add_plugin(plugin_groups, plugin):
    if plugin.group_name not in plugin_groups:
        plugin_groups[plugin.group_name] = []
    plugin_groups[plugin.group_name].append(plugin)


def make_chain_process(plugins):
    def chained(frame):
        out = frame
        for plugin in plugins:
            out = plugin.process(out)
        return out
    return chained


PluginAction = namedtuple('PluginAction', ['name', 'function', 'toggle'])


class Plugin:
    def __init__(self, plugin_name, group_name, z_index=0):
        self.group_name = group_name
        self.plugin_name = plugin_name
        self.z_index = z_index

    def get_actions(self) -> List[PluginAction]:
        raise NotImplementedError()

    def process(self, frame):
        return frame

    def save(self):
        # Returns an object that stores all customized options
        # It can be any serializable object
        return {}

    def load(self, plugin_state):
        # Loads a previously saved state
        pass