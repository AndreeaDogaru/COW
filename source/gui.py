from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QPixmap, QImage
from subprocess import Popen, PIPE
from functools import partial
from main import VirtualCamera
import cv2
import sys
import time

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
        self.setup_menu()

    def setup_menu(self):
        self.statusBar()
        mainMenu = self.menuBar()
        cameraMenu = mainMenu.addMenu('Camera')
        cams = list(filter(lambda x: x[1] != self.out_port, list_cams())) + [("None", -1)]
        print(cams)
        for cam in cams:
            action = QAction(cam[0], self)
            action.setStatusTip('Choose this input camera')
            action.triggered.connect(partial(self.choose_camera, cam))
            cameraMenu.addAction(action)
        if len(cams) > 0:
            self.choose_camera(cams[0])

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
