from plugins.plugin import Plugin, PluginAction
from utils import crop_center, get_latest_file, ToggleLink

from PyQt5 import QtWidgets

import cv2
import os
import time
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
        self.cuda = torch.cuda.is_available()
        self.preprocess = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        if self.cuda:
            self.network.cuda()
        self.scale_factor = 1 / 4
        self.path = 'plugins/plugin_data/SegmentationPlugin'
        os.makedirs(self.path, exist_ok=True)
        self.background_path = None
        self.background = np.random.randint(0, 255, (1920, 1080, 3), np.uint8)

    def toggle_display(self, window):
        self.display.flip()

    def get_actions(self):
        return [PluginAction("Active", self.toggle_display, self.display),
                PluginAction("Select background", self.select_background, False)]

    def save(self):
        return {"background_path": self.background_path,
                "display": self.display.get()}

    def load(self, plugin_state):
        self.background_path = plugin_state.get("background_path", None)
        self.display.set(plugin_state.get("display", False))

        if self.background_path is not None:
            img = cv2.imread(self.background_path)
            self.background = img[:, :, ::-1]
        else:
            self.background = np.random.randint(0, 255, (1920, 1080, 3), np.uint8)

    def select_background(self, window):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(window, "Select Image", "",
                                                             "Image Files (*.png *.jpg *.jpeg *.JPEG)")
        if file_name:
            img = cv2.imread(file_name)
            self.background_path = os.path.join(self.path, str(time.time()) + '.png')
            cv2.imwrite(self.background_path, img)
            self.background = img[:, :, ::-1]
        self.display.set(True)

    def get_mask(self, input_image):
        input_tensor = self.preprocess(input_image)
        input_batch = input_tensor.unsqueeze(0)
        if self.cuda:
            input_batch = input_batch.cuda()
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
            if self.background.shape != frame.shape:
                self.background = np.array(crop_center(Image.fromarray(self.background), *frame.shape[:2][::-1]))
            frame = np.array(Image.composite(Image.fromarray(frame), Image.fromarray(self.background), mask))
        return frame

