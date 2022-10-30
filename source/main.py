import pickle
import sys
from subprocess import Popen

import pyfakewebcam
import cv2
import threading
import os

from plugin import get_plugins, make_chain_process


class VirtualCamera:
    def __init__(self, pref_resolution=(1920, 1080)):
        self.fake_camera = None
        self.camera_input = None
        self.pref_resolution = pref_resolution
        self.current_resolution = self.pref_resolution
        self.stop_signal = False
        self._virtual_mapping = lambda x: x

    def start_stream(self, in_port, out_port, resolution):
        self.stop_stream()
        self.stop_signal = False
        self.open_port(out_port)
        self.camera_input = cv2.VideoCapture(in_port)
        self.current_resolution = self.set_resolution(*resolution)
        self.fake_camera = pyfakewebcam.FakeWebcam(f"/dev/video{out_port}", *self.current_resolution)
        self.start_stream_thread()

    def set_resolution(self, fmt, w, h):
        cap = self.camera_input
        fourcc = cv2.VideoWriter_fourcc(*fmt)
        cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return width, height

    def set_mapping(self, f):
        self._virtual_mapping = f

    def stream_forward(self):
        while not self.stop_signal:
            self.stream_step()

    def stream_step(self):
        try:
            _, frame = self.camera_input.read()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.flip(frame, 1)  # Mirror
            processed_frame = self._virtual_mapping(frame)
            processed_frame = cv2.flip(processed_frame, 1)  # Mirror back
        except Exception as e:
            print(e)
        self.fake_camera.schedule_frame(processed_frame)

    def start_stream_thread(self):
        self.stream_step()
        self.thread = threading.Thread(target=self.stream_forward)
        self.thread.start()

    def stop_stream(self):
        if self.fake_camera is not None:
            self.stop_signal = True
            self.thread.join()
            self.camera_input.release()
            os.close(self.fake_camera._video_device)
            self.fake_camera = None

    def open_port(self, port):
        Popen("sudo -S modprobe -r v4l2loopback".split()).wait()
        if not os.path.exists(f"/dev/video{port}"):
            proc = Popen(
                f'sudo -S /usr/sbin/modprobe v4l2loopback devices=1 video_nr={port} card_label="cow" exclusive_caps=1'.split())
            proc.wait()


def get_available_resolutions(port):
    if port == -1:
        return []
    try:
        cap = cv2.VideoCapture(port)
        formats = ['YUYV', 'MJPG']
        resolutions = [(1920, 1080), (1280, 720), (800, 600), (640, 480), (320, 240)]
        good = []
        for fmt in formats:
            fourcc = cv2.VideoWriter_fourcc(*fmt)
            cap.set(cv2.CAP_PROP_FOURCC, fourcc)
            for w, h in resolutions:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

                if (fmt, width, height) not in good:
                    good.append((fmt, width, height))
        return good
    except:
        return []


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
    if len(sys.argv) > 1:
        load_config(virtual, sys.argv[1])
    virtual.start_stream(INPUT, OUTPUT)
