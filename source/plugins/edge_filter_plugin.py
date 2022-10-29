from typing import Optional

import cv2
import numpy as np
from PyQt5.QtWidgets import QDialog
from PyQt5 import QtWidgets, QtCore

from plugin import Plugin, PluginAction
from source.utils import create_adjustment_slider

from utils import ToggleLink


class EdgeFilterPlugin(Plugin):
    def __init__(self):
        super().__init__("Edge Filter", "Video Filters", z_index=0)
        self.dlg: Optional[OptionsDialog] = None
        self.display = ToggleLink()
        self.binary_output = True
        self.threshold = 0.55
        self.clip_value = 500  # Clip for gradient stability
        self.kernel_size = 5

    def get_actions(self):
        return [PluginAction("Activate Filter", self.toggle_display, self.display),
                PluginAction("Options", self.show_dialog, False)]

    def show_dialog(self, window):
        if not self.dlg:
            self.dlg = OptionsDialog(window)
            self.set_sliders()
        if self.dlg.isHidden():
            pw = self.dlg.parent().geometry().width()
            ph = self.dlg.parent().geometry().height()
            dx = self.dlg.parent().geometry().x()
            dy = self.dlg.parent().geometry().y()
            h = self.dlg.height()
            self.dlg.move(dx + pw, dy + (ph - h) // 2)
            self.dlg.show()

    def set_sliders(self):
        self.dlg.base_values(self.kernel_size, self.clip_value, int(self.threshold * 100))

    def get_sliders(self):
        self.kernel_size = self.dlg.kernel_slider.value()
        self.clip_value = self.dlg.clip_value_slider.value()
        self.threshold = self.dlg.threshold_slider.value() / 100

    def toggle_display(self, window):
        self.display.flip()

    def process(self, frame):
        if self.display.get():
            if self.dlg:
                self.get_sliders()
            frame = self.apply_filter(frame)
        return frame

    def apply_filter(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        gray = cv2.blur(gray, ksize=(self.kernel_size, self.kernel_size))  # Additional blurring

        laplacian = cv2.Laplacian(gray, cv2.CV_64F, ksize=self.kernel_size)
        laplacian = np.clip(laplacian, a_min=-self.clip_value, a_max=self.clip_value)

        mini, maxi = np.min(laplacian), np.max(laplacian)
        normalized = (laplacian - mini) / (maxi - mini + 1e-8)
        if self.binary_output:
            normalized = normalized > self.threshold
        result = (normalized * 255).astype(np.uint8)
        result = np.repeat(result[:, :, None], repeats=3, axis=2)  # Expand to color channel
        return result

    def save(self):
        return {"display": self.display.get()}

    def load(self, plugin_state):
        self.display.set(plugin_state.get("display", False))


class OptionsDialog(QDialog):
    def __init__(self, args, **kwargs):
        super(OptionsDialog, self).__init__(args, **kwargs)
        self.setup_ui()

    # noinspection PyAttributeOutsideInit
    def setup_ui(self):
        self.setWindowTitle("Edge Filter Options")

        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        self.clip_value_slider = create_adjustment_slider(1, 1000, step=50)
        self.layout.addWidget(self.clip_value_slider, 1, 1, 1, 1)
        self.label("Clip Value", 1, 0, 1, 1)

        self.kernel_slider = create_adjustment_slider(1, 9, step=2)
        self.layout.addWidget(self.kernel_slider, 2, 1, 1, 1)
        self.label("Kernel Size", 2, 0, 1, 1)

        self.threshold_slider = create_adjustment_slider(1, 100, step=5)
        self.layout.addWidget(self.threshold_slider, 3, 1, 1, 1)
        self.label("Threshold", 3, 0, 1, 1)

        self.push_button = QtWidgets.QPushButton()
        self.push_button.setText("Reset")
        self.push_button.clicked.connect(self.reset_sliders)
        self.layout.addWidget(self.push_button, 5, 1, 1, 1, QtCore.Qt.AlignRight)

    def label(self, name, *args):
        label = QtWidgets.QLabel()
        label.setText(name)
        self.layout.addWidget(label, *args)

    # noinspection PyAttributeOutsideInit
    def base_values(self, kernel_value, clip_value, threshold_value):
        self.kernel_value_0 = kernel_value
        self.clip_value_0 = clip_value
        self.threshold_value_0 = threshold_value
        self.reset_sliders()

    def reset_sliders(self):
        self.kernel_slider.setValue(self.kernel_value_0)
        self.clip_value_slider.setValue(self.clip_value_0)
        self.threshold_slider.setValue(self.threshold_value_0)
