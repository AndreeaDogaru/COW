from source.plugins.plugin import Plugin, PluginAction
import numpy as np
import cv2

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QDialog


class AdjustmentsPlugin(Plugin):
    def __init__(self, slider_limit=100):
        super().__init__("Adjustments", "Misc")
        self.dlg: AdjustmentsDialog = None
        self.slider_limit = slider_limit

    def get_actions(self):
        return [PluginAction("Image Tuning", self.show_dialog, False)]

    def show_dialog(self, window):
        if not self.dlg:
            self.dlg = AdjustmentsDialog(self.slider_limit, window)
        if self.dlg.isHidden():
            pw = self.dlg.parent().geometry().width()
            ph = self.dlg.parent().geometry().height()
            dx = self.dlg.parent().geometry().x()
            dy = self.dlg.parent().geometry().y()
            h = self.dlg.height()
            self.dlg.move(dx + pw, dy + (ph - h) // 2)
            self.dlg.show()

    def process(self, frame):
        if self.dlg:
            frame = frame.astype(np.int)
            delta_brightness = self.dlg.brightness_slider.value()
            delta_contrast = (self.dlg.contrast_slider.value() + self.slider_limit) / self.slider_limit
            delta_saturation = self.dlg.saturation_slider.value()
            frame = delta_contrast * frame + delta_brightness
            frame = np.clip(frame, 0, 255).astype(np.uint8)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            frame[:, :, 1] = (frame[:, :, 1].astype(np.int) + delta_saturation).clip(0, 255).astype(np.uint8)
            frame = cv2.cvtColor(frame, cv2.COLOR_HSV2RGB)
        return frame


class AdjustmentsDialog(QDialog):
    def __init__(self, slider_limit, args, **kwargs):
        super(AdjustmentsDialog, self).__init__(args, **kwargs)
        self.slider_limit = slider_limit
        self.setup_ui()

    # noinspection PyAttributeOutsideInit
    def setup_ui(self):
        self.setWindowTitle("Image Tuning")

        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        self.brightness_slider = self.create_adjustment_slider()
        self.layout.addWidget(self.brightness_slider, 1, 1, 1, 1)

        self.brightness_label = QtWidgets.QLabel()
        self.brightness_label.setText("Brightness")
        self.layout.addWidget(self.brightness_label, 1, 0, 1, 1)

        self.saturation_slider = self.create_adjustment_slider()
        self.layout.addWidget(self.saturation_slider, 3, 1, 1, 1)

        self.contrast_label = QtWidgets.QLabel()
        self.contrast_label.setText("Contrast")
        self.layout.addWidget(self.contrast_label, 2, 0, 1, 1)

        self.saturation_label = QtWidgets.QLabel()
        self.saturation_label.setText("Saturation")
        self.layout.addWidget(self.saturation_label, 3, 0, 1, 1)

        self.contrast_slider = self.create_adjustment_slider()
        self.layout.addWidget(self.contrast_slider, 2, 1, 1, 1)

        self.push_button = QtWidgets.QPushButton()
        self.push_button.setText("Reset")
        self.push_button.clicked.connect(self.reset_sliders)
        self.layout.addWidget(self.push_button, 5, 1, 1, 1, QtCore.Qt.AlignRight)

    def reset_sliders(self):
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(0)
        self.saturation_slider.setValue(0)

    def create_adjustment_slider(self):
        slider = QtWidgets.QSlider()
        slider.setEnabled(True)
        slider.setMinimum(-self.slider_limit)
        slider.setMaximum(self.slider_limit)
        slider.setTracking(True)
        slider.setOrientation(QtCore.Qt.Horizontal)
        slider.setTickInterval(self.slider_limit)
        slider.setTickPosition(QtWidgets.QSlider.TickPosition(2))
        return slider

