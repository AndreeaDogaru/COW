from plugin import Plugin, PluginAction
import numpy as np

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDialog
import cv2


class TextPlugin(Plugin):
    def __init__(self):
        super().__init__("Add Text", "High Level", z_index=110)
        self.dlg: TextInputDialog = None
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 1
        self.font_color = (255, 255, 255)
        self.thickness = 1
        self.line_type = 2
        self.current_text = ""
        self.text_overlay = None

    def get_actions(self):
        return [PluginAction("Write Text", self.show_dialog, False)]

    def show_dialog(self, window):
        if not self.dlg:
            self.dlg = TextInputDialog(window)
        if self.dlg.isHidden():
            pw = self.dlg.parent().geometry().width()
            ph = self.dlg.parent().geometry().height()
            dx = self.dlg.parent().geometry().x()
            dy = self.dlg.parent().geometry().y()
            h = self.dlg.height()
            self.dlg.move(dx + pw, dy + (ph - h) // 2)
            self.dlg.show()

    def process(self, frame):
        self.get_overlay(frame.shape)
        if self.text_overlay is None:
            return frame
        y_offset = 20
        y = frame.shape[0] - self.text_overlay.shape[0] - y_offset
        x = frame.shape[1] // 2 - self.text_overlay.shape[1] // 2
        frame[y:y+self.text_overlay.shape[0], x:x+self.text_overlay.shape[1]] = self.text_overlay
        return frame

    def get_overlay(self, frame_shape, text_pad=15, bg_gray=127):
        if self.dlg is None or self.current_text == self.dlg.written_text:
            return
        self.current_text = self.dlg.written_text.strip()
        if len(self.current_text) < 1:
            self.text_overlay = None
            return
        text_width, text_height = cv2.getTextSize(self.current_text, self.font, self.font_scale, self.thickness)[0]
        text_height += text_pad
        self.text_overlay = np.ones((min(text_height, frame_shape[0]),
                                     min(text_width, frame_shape[1]), 3), dtype=np.uint8)
        self.text_overlay *= bg_gray
        cv2.putText(self.text_overlay, self.current_text, (0, int(text_height*0.75)), self.font,
                    self.font_scale, self.font_color, self.thickness, self.line_type)


class TextInputDialog(QDialog):
    def __init__(self, args, **kwargs):
        super(TextInputDialog, self).__init__(args, **kwargs)
        self.written_text = ""
        self.setup_ui()

    # noinspection PyAttributeOutsideInit
    def setup_ui(self):
        self.setWindowTitle("Text")

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.create_text_input())
        self.setLayout(self.layout)

    # noinspection PyAttributeOutsideInit
    def create_text_input(self):
        self.text_area = QtWidgets.QLineEdit()
        self.text_area.textChanged.connect(self.text_changed)
        return self.text_area

    def text_changed(self):
        text = self.text_area.text().strip()
        self.written_text = text
