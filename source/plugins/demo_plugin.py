from source.plugins.plugin import Plugin, PluginAction
from PyQt5.QtWidgets import QDialog


class DemoPlugin(Plugin):
    def __init__(self):
        super().__init__("Demo", "Misc")

    def get_actions(self):
        return [PluginAction("Echo", self.template_function)]

    def template_function(self, window):
        dlg = QDialog(window)
        dlg.setWindowTitle(self.plugin_name)
        dlg.exec_()

