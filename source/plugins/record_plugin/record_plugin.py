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


class RecordPlugin(Plugin):
    def __init__(self):
        super().__init__("Record", "High Level", z_index=1000)
        self.record = ToggleLink()
        self.path = Path('plugin_data/RecordPlugin')
        os.makedirs(self.path, exist_ok=True)

        self.icon_size = (64, 64)
        self.record_icon = self.load_icon()
        self.record_path = None
        self.image_size = None  # (height, width)
        self.writer = None

    def load_icon(self):
        img = Image.open('plugins/record_plugin/record_icon.png')
        img = img.resize(self.icon_size, Image.BILINEAR)
        return np.array(img)

    def start_recording(self):
        now = datetime.now()
        self.record_path = self.path / now.strftime("%Y-%m-%d_%H-%M-%S.mp4")
        self.writer= cv2.VideoWriter(str(self.record_path), cv2.VideoWriter_fourcc(*'MP4V'), 30, self.image_size[::-1])

    def stop_recording(self):
        self.writer.release()

    def toggle_record(self, window):
        if self.image_size is None:  # Must learn image size first
            return
        self.record.flip()
        if self.record.get():
            self.start_recording()
        else:
            self.stop_recording()

    def get_actions(self):
        return [PluginAction("Record", self.toggle_record, self.record),]

    def save(self):
        if self.record.get():
            self.stop_recording()
        return {}

    def load(self, plugin_state):
        self.record_path = None
        self.record.set(False)  # Always start with record False

    def process(self, frame):
        self.image_size = frame.shape[:2]
        if self.record.get():
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            frame_bgr = np.flip(frame_bgr, 1)
            self.writer.write(frame_bgr)

            # Display record icon
            corner = frame[:self.icon_size[0], :self.icon_size[1], :]
            mask = self.record_icon[:, :, 3:] / 255.0
            corner = corner * (1 - mask) + self.record_icon[:, :, :3] * mask
            corner = corner.round().astype(np.uint8)
            frame[:self.icon_size[0], :self.icon_size[1], :] = corner
        return frame
