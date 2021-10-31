import cv2

from plugin import Plugin, PluginAction
import time

from utils import ToggleLink


class FPSPlugin(Plugin):
    def __init__(self):
        super().__init__("FPS", "Misc")
        self.display = ToggleLink()
        self.counter = 0
        self.last_time = time.time()
        self.update_time = 1
        self.fps = "?"

    def get_actions(self):
        return [PluginAction("Display FPS", self.toggle_display, self.display)]

    def toggle_display(self, window):
        self.display.flip()

    def process(self, frame):
        if self.display.get():
            frame = self.write_fps(frame)
        self.counter += 1
        current = time.time()
        if current - self.last_time > self.update_time:
            self.fps = "{0:.2f} fps".format(self.counter / (current - self.last_time))
            self.last_time = current
            self.counter = 0

        return frame

    def write_fps(self, frame):
        font = cv2.FONT_HERSHEY_SIMPLEX
        xy = (10, 30)
        font_scale = 0.6
        font_color = (255, 255, 255)
        line_type = 2
        frame = cv2.flip(frame, 1)
        frame = cv2.putText(frame, self.fps, xy, font, font_scale, font_color, lineType=line_type)
        frame = cv2.flip(frame, 1)
        return frame

    def save(self):
        return {"display": self.display.get()}

    def load(self, plugin_state):
        self.display.set(plugin_state.get("display", False))
