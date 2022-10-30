import cv2

from plugin import Plugin, PluginAction

from utils import ToggleLink


class MirrorPlugin(Plugin):
    def __init__(self):
        super().__init__("Mirror", "High Level", z_index=10000)
        self.display = ToggleLink()

    def get_actions(self):
        return [PluginAction("Mirror diplay", self.toggle_display, self.display)]

    def toggle_display(self, window):
        self.display.flip()
        window.mirrored_output = not window.mirrored_output

    def process(self, frame):
        if self.display.get():
            frame = cv2.flip(frame, 1)

        return frame

    def save(self):
        return {"display": self.display.get()}

    def load(self, plugin_state):
        self.display.set(plugin_state.get("display", False))
