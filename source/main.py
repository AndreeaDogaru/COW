import pickle
import sys
from subprocess import Popen

import pyfakewebcam
import cv2
import threading
import os

from plugins.plugin import get_plugins, make_chain_process


class VirtualCamera:
    def __init__(self, pref_resolution=(1920, 1080)):
        self.fake_camera = None
        self.pref_resolution = pref_resolution
        self.current_resolution = self.pref_resolution
        self.stop_signal = False
        self._virtual_mapping = lambda x: x

    def start_stream(self, in_port, out_port):
        self.stop_stream()
        self.stop_signal = False
        self.open_port(out_port)
        w, h = self._compute_resolution(in_port)
        self.fake_camera = pyfakewebcam.FakeWebcam(f"/dev/video{out_port}", w, h)
        self.start_stream_thread()

    def _compute_resolution(self, in_port):
        self.camera_input = cv2.VideoCapture(in_port)
        self.camera_input.set(cv2.CAP_PROP_FRAME_WIDTH, self.pref_resolution[0])
        self.camera_input.set(cv2.CAP_PROP_FRAME_HEIGHT, self.pref_resolution[1])
        width = int(self.camera_input.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.camera_input.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.current_resolution = (width, height)
        return self.current_resolution

    def set_mapping(self, f):
        self._virtual_mapping = f

    def stream_forward(self):
        while not self.stop_signal:
            self.stream_step()

    def stream_step(self):
        try:
            _, frame = self.camera_input.read()
            frame = frame[:, :, ::-1]
            processed_frame = self._virtual_mapping(frame)
        except Exception as e:
            print(e)
        self.fake_camera.schedule_frame(processed_frame)

    def start_stream_thread(self):
        self.stream_step()
        self.thread = threading.Thread(target = self.stream_forward)
        self.thread.start()

    def stop_stream(self):
        if self.fake_camera is not None:
            self.stop_signal = True
            self.thread.join()
            self.camera_input.release()
            os.close(self.fake_camera._video_device)
            self.fake_camera = None

    def open_port(self, port):
        if not os.path.exists(f"/dev/video{port}"):
            proc = Popen(
                f'sudo -S /usr/sbin/modprobe v4l2loopback devices=1 video_nr={port} card_label="cow" exclusive_caps=1'.split())
            proc.wait()


def load_config(v_camera, path):
    if not os.path.exists(path):
        print(f"File {path} not found")
    all_config = pickle.load(open(path, "rb"))
    plugins = get_plugins([])
    for plugin in plugins:
        state = all_config.get(plugin.__class__, None)
        if state is not None:
            plugin.load(state)
    plugins.sort(key=lambda x: x.z_index)
    v_camera.set_mapping(make_chain_process(plugins))


if __name__ == "__main__":
    INPUT = 0
    OUTPUT = 20

    virtual = VirtualCamera()
    if len(sys.argv) > 0:
        load_config(virtual, sys.argv[1])
    virtual.start_stream(INPUT, OUTPUT)
