from plugin import Plugin, PluginAction
from utils import crop_center, get_latest_file, ToggleLink

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox

import cv2
import os
import time
import shutil
from PIL import Image
import numpy as np

import torch
import torchvision
from torchvision import transforms


class SegmentationPlugin(Plugin):
    def __init__(self):
        super().__init__("Segmentation", "Misc", z_index=-1)
        self.network = torchvision.models.segmentation.deeplabv3_resnet50(pretrained=True).eval()
        self.display = ToggleLink()
        self.use_cuda = ToggleLink()
        self.preprocess = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        self.scale_factor = 1 / 4
        self.path = 'plugin_data/SegmentationPlugin'
        os.makedirs(self.path, exist_ok=True)
        self.background_path = None
        self.background = np.random.randint(0, 255, (1920, 1080, 3), np.uint8)
        self.device_mapping = {True: "cuda", False: "cpu"}

    def toggle_display(self, window):
        self.display.flip()

    def change_device(self, window):
        if not self.use_cuda and not torch.cuda.is_available():
            mbox = QMessageBox(window)
            mbox.setText("No CUDA compatible device available")
            mbox.setWindowTitle(self.plugin_name)
            mbox.setIcon(QMessageBox.Warning)
            mbox.show()
        else:
            self.use_cuda.flip()

    def get_actions(self):
        return [PluginAction("Active", self.toggle_display, self.display),
                PluginAction("Use GPU acceleration", self.change_device, self.use_cuda),
                PluginAction("Select background", self.select_background, False)]

    def save(self):
        return {"background_path": self.background_path,
                "display": self.display.get(),
                "use_cuda": self.use_cuda.get()}

    def load(self, plugin_state):
        self.background_path = plugin_state.get("background_path", None)
        self.display.set(plugin_state.get("display", False))
        self.use_cuda.set(plugin_state.get("use_cuda", False) and torch.cuda.is_available())

        self.load_background(self.background_path)

    def load_background(self, file_path):
        if file_path is not None:
            img = cv2.imread(file_path)
            if img is not None:
                self.background = img
                return True
            else:
                video = cv2.VideoCapture(file_path)
                if video.isOpened():
                    self.background = video
                    return True
        self.background = np.random.randint(0, 255, (1920, 1080, 3), np.uint8)
        return False

    def get_background_frame(self):
        if isinstance(self.background, cv2.VideoCapture):
            ret, frame = self.background.read()
            if ret:
                return frame
            else:
                self.load_background(self.background_path)
                return self.get_background_frame()
        else:
            return self.background

    def select_background(self, window):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(window, "Select Image or Video", "")
        if self.load_background(file_name):
            self.background_path = os.path.join(self.path, str(time.time()) + os.path.splitext(file_name)[1])
            shutil.copy(file_name, self.background_path)
        self.display.set(True)

    def get_mask(self, input_image):
        input_tensor = self.preprocess(input_image)
        device = self.device_mapping[self.use_cuda.get()]
        self.network.to(device)
        input_batch = input_tensor.unsqueeze(0).to(device)
        with torch.no_grad():
            output = self.network(input_batch)['out'][0]
        output_predictions = output.argmax(0).byte().cpu().numpy()
        mask = output_predictions == 15
        return mask

    def process(self, frame):
        if self.display.get():
            input_image = cv2.resize(frame, None, fx=self.scale_factor, fy=self.scale_factor)
            input_image = Image.fromarray(input_image)
            mask = self.get_mask(input_image)
            mask = cv2.resize((mask * 255).astype(np.uint8), frame.shape[:2][::-1], interpolation=cv2.INTER_CUBIC)
            kernel = np.ones((7, 7), np.uint8)
            mask = cv2.erode(mask, kernel, iterations=1)
            kernel = kernel / kernel.sum()
            mask = cv2.filter2D(mask, -1, kernel)
            mask = Image.fromarray(mask)
            background = self.get_background_frame()[:, ::-1, ::-1]
            if background.shape != frame.shape:
                background = np.array(crop_center(Image.fromarray(background), *frame.shape[:2][::-1]))
            frame = np.array(Image.composite(Image.fromarray(frame), Image.fromarray(background), mask))
        return frame

