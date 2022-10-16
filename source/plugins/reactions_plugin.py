from typing import List

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QPixmap, QIcon

from plugin import Plugin, PluginAction
import numpy as np

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QDialog, QPushButton
from PIL import Image
from PIL.ImageQt import ImageQt
from pathlib import Path
import json
import fuzzyset


class ReactionsPlugin(Plugin):
    def __init__(self):
        super().__init__("Reactions", "High Level", z_index=100)
        self.dlg: ReactionsDialog = None
        self.icon_size = (72, 72)
        self.reactions = {0: Image.fromarray(np.zeros(self.icon_size + (4,), dtype=np.uint8))}
        for i, file in enumerate(sorted(Path('plugin_data/ReactionsPlugin/emoji').iterdir()), 1):
            self.reactions[i] = Image.open(file).convert("RGBA")
        self.icon_padding = 25
        self.icon_position = (slice(self.icon_padding, self.icon_size[0] + self.icon_padding),
                              slice(-(self.icon_size[1] + self.icon_padding), -self.icon_padding))
        self.current_reaction = 0

    def get_actions(self):
        return [PluginAction("Choose Reaction", self.show_dialog, False)]

    def show_dialog(self, window):
        if not self.dlg:
            self.dlg = ReactionsDialog(self.reactions, self.current_reaction, window)
        if self.dlg.isHidden():
            pw = self.dlg.parent().geometry().width()
            ph = self.dlg.parent().geometry().height()
            dx = self.dlg.parent().geometry().x()
            dy = self.dlg.parent().geometry().y()
            h = self.dlg.height()
            self.dlg.move(dx + pw, dy + (ph - h) // 2)
            self.dlg.show()

    def process(self, frame):
        self.get_reaction()
        icon = np.array(self.reactions[self.current_reaction])
        corner = frame[self.icon_position[0], self.icon_position[1]]
        mask = icon[:, :, 3:] / 255.0
        corner = corner * (1 - mask) + icon[:, :, :3] * mask
        corner = corner.round().astype(np.uint8)
        frame[self.icon_position[0], self.icon_position[1]] = corner
        return frame

    def save(self):
        return {"selected_reaction": self.current_reaction}

    def load(self, plugin_state):
        self.current_reaction = plugin_state["selected_reaction"]
        self.set_reaction()

    def get_reaction(self):
        if self.dlg is not None:
            self.current_reaction = self.dlg.selected_reaction

    def set_reaction(self):
        if self.dlg is not None:
            self.dlg.selected_reaction = self.current_reaction


class ReactionsDialog(QDialog):
    def __init__(self, icons, initial_reaction, args, **kwargs):
        super(ReactionsDialog, self).__init__(args, **kwargs)
        self.icons = icons
        self.icons_per_row = 6
        self.selected_reaction = initial_reaction
        self.load_metadata()
        self.selection = list(range(len(self.icons)))
        self.setup_ui()

    # noinspection PyAttributeOutsideInit
    def load_metadata(self, rel_sim_cutoff=0.5):
        self.fuzzy_set = fuzzyset.FuzzySet(gram_size_lower=3, use_levenshtein=False, rel_sim_cutoff=rel_sim_cutoff)
        self.indexer = {}
        with open('plugin_data/ReactionsPlugin/openmoji.json', 'r') as f:
            self.metadata: List[dict] = json.load(f)
        self.metadata = sorted(self.metadata, key=lambda el: el['hexcode'] + ".png")
        # self.metadata.insert(0, {'tags': 'none', 'openmoji_tags': '', 'annotation': "", 'hexcode': '0'})
        for ind, item in enumerate(self.metadata, start=1):
            # key = f"{item['tags']}".replace(',', '')
            key = f"{item['tags']} {item['openmoji_tags']} {item['annotation']}".replace(',', '')
            self.fuzzy_set.add(key)
            self.indexer[key] = ind

    # noinspection PyAttributeOutsideInit
    def setup_ui(self):
        self.setWindowTitle("Emoji")

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.create_search_bar())
        self.scroll_area = QtWidgets.QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area_content = QtWidgets.QWidget()
        self.grid_layout = QtWidgets.QGridLayout(self.scroll_area_content)
        self.scroll_area.setWidget(self.scroll_area_content)
        self.scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.layout.addWidget(self.scroll_area)
        self.setLayout(self.layout)
        self.set_grid_buttons()

    def set_grid_buttons(self):
        for i, ind in enumerate(self.selection):
            button = QPushButton()
            button.setIcon(QIcon(QPixmap.fromImage(ImageQt(self.icons[ind]))))
            button.setIconSize(QSize(35, 35))
            button.setStyleSheet('border: 2px solid gray;')
            button.clicked.connect(self.button_clicked)
            self.grid_layout.addWidget(button, i // self.icons_per_row, i % self.icons_per_row)

    # noinspection PyAttributeOutsideInit
    def create_search_bar(self):
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.textChanged.connect(self.search_changed)
        return self.search_bar

    def search_changed(self):
        query = self.search_bar.text().strip()
        if len(query) == 0:
            # indexes = list(range(len(self.icons)))
            return
        else:
            matches = self.fuzzy_set.get(query, default=[])
            indexes = [self.indexer[match] for score, match in matches]
        self.selection = [0, *indexes]
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)
        self.set_grid_buttons()

    def button_clicked(self):
        button = self.sender()
        self.selected_reaction = self.selection[self.grid_layout.indexOf(button)]
