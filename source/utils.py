import glob
import os

from PyQt5 import QtWidgets, QtCore


def crop_center(img, crop_height, crop_width):
    img_height, img_width, _ = img.shape
    width_margin = (img_width - crop_width) // 2
    height_margin = (img_height - crop_height) // 2
    return img[
           height_margin:height_margin+crop_height,
           width_margin:width_margin+crop_width]


def get_latest_file(dir_path, ext_fmt="*"):
    list_of_files = glob.glob(os.path.join(dir_path, ext_fmt))
    if len(list_of_files):
        return max(list_of_files, key=os.path.getctime)
    else:
        return None


class ObservableValue:
    def __init__(self, value=None):
        self.value = value
        self.observers = []

    def set(self, new_value):
        self.value = new_value
        for observer in self.observers:
            observer(self.value)

    def get(self):
        return self.value

    def register(self, observer):
        self.observers.append(observer)

    def unregister(self, observer):
        self.observers.remove(observer)


class ToggleLink(ObservableValue):
    def __init__(self):
        super(ToggleLink, self).__init__(False)

    def flip(self):
        self.set(not self.get())


def create_adjustment_slider(mini, maxi, step=1):
    slider = QtWidgets.QSlider()
    slider.setEnabled(True)
    slider.setMinimum(mini)
    slider.setMaximum(maxi)
    slider.setTracking(True)
    slider.setOrientation(QtCore.Qt.Horizontal)
    slider.setTickInterval(step)
    slider.setSingleStep(step)
    if step != 1:
        def reposition():
            val = slider.value()
            if (val - mini) % step != 0:
                val += step - (val - mini) % step
            slider.setValue(val)

        slider.valueChanged.connect(reposition)
    slider.setTickPosition(QtWidgets.QSlider.TickPosition(2))
    return slider
