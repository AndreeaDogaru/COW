import os
import PIL
import cv2
import numpy as np

from pathlib import Path
from datetime import datetime
from PyQt5 import QtWidgets

from plugin import Plugin, PluginAction
from utils import ToggleLink
from PIL import Image
from mss import mss

class ScreenPlugin(Plugin):
    def __init__(self):
        super().__init__("Screen", "High Level", z_index=-100)
        self.share_screen = ToggleLink()
        self.path = Path('plugin_data/ScreenPlugin')
        os.makedirs(self.path, exist_ok=True)

        self.sct = None
        self.monitor_region = None

    def start_screen_sharing(self):
        self.sct = mss()
        self.monitor_region = self.sct.monitors[1]  # Share 1st screen

    def stop_screen_sharing(self):
        if self.sct is not None:
            self.sct.close()

    def toggle_screen_sharing(self, window):
        self.share_screen.flip()
        if self.share_screen.get():
            self.start_screen_sharing()
        else:
            self.stop_screen_sharing()

    def get_actions(self):
        return [PluginAction("Share Screen", self.toggle_screen_sharing, self.share_screen),]

    def save(self):
        if self.share_screen.get():
            self.stop_screen_sharing()
        return {'share_screen': self.share_screen.get()}

    def load(self, plugin_state):
        self.share_screen.set(plugin_state.get('share_screen', False))
        if self.share_screen.get():
            self.start_screen_sharing()

    def process(self, frame):
        image_size = frame.shape[:2]
        if self.share_screen.get() and self.sct is not None:
            screen_img = np.array(self.sct.grab(self.monitor_region))[:, :, :3]
            screen_img = cv2.resize(screen_img, image_size[::-1], interpolation=cv2.INTER_CUBIC)
            screen_img = cv2.cvtColor(screen_img, cv2.COLOR_BGR2RGB)
            return screen_img
        return frame
