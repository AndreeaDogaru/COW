from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPixmap, QImage
from subprocess import Popen, PIPE
from functools import partial
import cv2
import os
import sys
import time
from source.main import VirtualCamera
from source.plugins.plugin import get_plugins
import pickle


class MainWindow(QMainWindow):

    def __init__(self, out_port=20, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.video_size = QSize(640, 480)
        self.capture = None
        self.out_port = out_port
        self.in_port = -1
        self.virtual_camera = VirtualCamera()

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.setup_ui()
        self.menu = self.setup_menu()
        self.plugins = self.setup_plugins()

    def setup_menu(self):
        self.statusBar()
        main_menu = self.menuBar()
        _ = self.create_file_actions(main_menu)
        camera_menu = main_menu.addMenu('Camera')
        cams = list(filter(lambda x: x[1] != self.out_port, list_cams())) + [("None", -1)]
        print(cams)
        for cam in cams:
            action = QAction(cam[0], self)
            action.setStatusTip('Choose this input camera')
            action.triggered.connect(partial(self.choose_camera, cam))
            camera_menu.addAction(action)
        if len(cams) > 0:
            self.choose_camera(cams[0])
        return main_menu

    def create_file_actions(self, main_menu):
        file_menu = main_menu.addMenu("File")

        save_action = QAction("Save", self)
        save_action.setStatusTip("Save current configuration")
        save_action.triggered.connect(self.save_configuration)
        file_menu.addAction(save_action)

        load_action = QAction("Load", self)
        load_action.setStatusTip("Load a saved configuration")
        load_action.triggered.connect(partial(self.load_configuration, False))
        file_menu.addAction(load_action)

        load_action = QAction("Load latest", self)
        load_action.setStatusTip("Load the last used configuration")
        load_action.triggered.connect(partial(self.load_configuration, True))
        file_menu.addAction(load_action)

        return file_menu

    def save_configuration(self, latest=True):
        all_config = {plugin.__class__: plugin.save() for plugin in self.plugins}
        if latest:
            pickle.dump(all_config, open("latest.conf", "wb"))
            return
        file_name, _ = QFileDialog.getSaveFileName(self, "Save configuration to file", "",
                                                   "Config File (*.conf);")
        if file_name:
            pickle.dump(all_config, open(file_name, "wb"))

    def load_configuration(self, latest=True):
        if latest:
            file_name = "latest.conf"
        else:
            file_name, _ = QFileDialog.getOpenFileName(self, "Select configuration", "",
                                                       "Config File (*.conf)")
        if not os.path.exists(file_name):
            return
        all_config = pickle.load(open(file_name, "rb"))
        for plugin in self.plugins:
            state = all_config.get(plugin.__class__, None)
            if state is not None:
                plugin.load(state)

    def setup_plugins(self):
        plugin_groups = get_plugins([])
        plugins = []
        for name, group in plugin_groups.items():
            group_menu = self.menu.addMenu(name)
            for plugin in group:
                plugins.append(plugin)
                plugin_menu = group_menu.addMenu(plugin.plugin_name)
                for p_action in plugin.get_actions():
                    q_action = QAction(p_action.name, self)
                    q_action.setStatusTip(plugin.plugin_name)
                    q_action.triggered.connect(partial(p_action.function, self))
                    q_action.setCheckable(p_action.toggle)
                    plugin_menu.addAction(q_action)
        plugins.sort(key=lambda x: x.z_index)
        self.virtual_camera.set_mapping(self.plugin_process)
        return plugins

    def plugin_process(self, frame):
        out = frame
        for plugin in self.plugins:
            out = plugin.process(out)
        return out

    def choose_camera(self, cam):
        self.release_camera()
        if cam[1] != -1:
            self.virtual_camera.stop_stream()
        if valid_camera(cam):
            self.setup_camera(cam)
        else:
            print("Invalid input camera")

    def setup_ui(self):
        """Initialize widgets.
        """
        self.image_label = QLabel()
        self.image_label.setFixedSize(self.video_size)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.image_label)

        self.central.setLayout(self.main_layout)

    def setup_camera(self, cam):
        """Initialize camera.
        """
        self.in_port = cam[1]
        if self.in_port == -1:
            return False
        self.virtual_camera.start_stream(self.in_port, self.out_port)

        self.capture = cv2.VideoCapture(self.out_port)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.video_size.width())
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.video_size.height())

        self.video_size = QSize(*self.virtual_camera.current_resolution)
        self.image_label.setFixedSize(self.video_size)

        self.timer = QTimer()
        self.timer.timeout.connect(self.display_video_stream)
        self.timer.start(30)

    def release_camera(self):
        if self.capture is not None:
            self.timer.stop()
            self.capture.release()
            self.capture = None
            print("Stopped")

    def display_video_stream(self):
        """Read frame from camera and repaint QLabel widget.
        """
        _, frame = self.capture.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.flip(frame, 1)
        image = QImage(frame, frame.shape[1], frame.shape[0],
                       frame.strides[0], QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(image))

    def closeEvent(self, event):
        self.save_configuration(latest=True)
        print("Shutting down")
        self.release_camera()
        self.virtual_camera.stop_stream()
        event.accept()


def list_cams():
    cmd = ["/usr/bin/v4l2-ctl", "--list-devices"]
    out, err = Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
    out, err = out.strip(), err.strip()
    out = out.decode()
    cams = []
    for l in [i.split("\n\t") for i in out.split("\n\n")]:
        cam_name = l[0]
        cam_id = int(min(l[1:])[len("/dev/video"):])
        cams.append((cam_name, cam_id))
    return sorted(cams, key=lambda x: x[1])


def valid_camera(cam):
    if cam[1] == -1:
        return True
    camera = cv2.VideoCapture(int(cam[1]))
    if not camera.isOpened():
        return False
    else:
        is_reading, img = camera.read()
        return is_reading


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
