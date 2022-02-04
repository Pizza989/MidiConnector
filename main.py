import os
import pickle
import random
import sys
from typing import List, Optional

from PyQt5 import uic
from PyQt5.QtCore import QFile
from PyQt5.QtWidgets import QMainWindow, QApplication, QFrame, QWidget, QAction, QFileDialog

import utils

GUI_PATH = "design/node.ui"
GLOBAL_QSS_PATH = "design/style/main.qss"

SAVE_FILE_SEPARATOR = b"$NODE_ENDINGBRUHURHURUHU"


class UI(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load Graphics
        uic.loadUi(GUI_PATH, self)

        # Init components
        self.node_editor_place_holder: QFrame = self.findChild(QFrame, "nodeEditorPlaceHolder")

        self.open_action: QAction = self.findChild(QAction, "actionOpen")
        self.save_action: QAction = self.findChild(QAction, "actionSave")
        self.save_as_action: QAction = self.findChild(QAction, "actionSave_as")
        self.exit_action: QAction = self.findChild(QAction, "actionExit")

        self.open_action.triggered.connect(self.open)
        self.open_action.setStatusTip("Open a save folder")
        self.save_action.triggered.connect(self.save)
        self.save_action.setStatusTip("Save scene")
        self.save_as_action.triggered.connect(self.save_as)
        self.save_as_action.setStatusTip("Save scene to location")
        self.exit_action.triggered.connect(sys.exit)
        self.exit_action.setStatusTip("Quit?")

        self.input_devices = []
        self.output_devices = []
        self.devices = []
        self.connections = []

        self.connections_view: Optional[utils.QDMNodeEditor] = None

        self.nodes: List[utils.Node] = []

        self.current_file = None

        self.init_lists()
        self.init_node_editor()
        self.init_ui()

    def restart(self):
        self.connections_view.scene.clear()
        self.nodes.clear()
        self.node_editor_place_holder.layout().removeWidget(self.connections_view)
        self.init_node_editor()

    def open(self):
        self.nodes.clear()
        self.connections_view.scene.clear()
        self.load()

    def load(self):
        url = QFileDialog.getExistingDirectoryUrl(self).url().replace("file://", "")
        for _file in os.listdir(url):
            _data = pickle.load(open(f"{url}/{_file}", "rb"))
            self.nodes.append(utils.Node(_data[0], self.connections_view, _data[1]))

            self.update_nodes()

    def save(self):
        if self.current_file:
            pass
        else:
            self.save_as()

    def save_as(self):  # TODO: figure out how to deal with connections once they are implemented
        url = QFileDialog.getSaveFileUrl(self)[0].url().replace("file://", "")
        os.mkdir(url)
        for _each in self.nodes:
            with open(f"{url}/{_each.device.name}-{_each.device.type}", "wb") as _file:
                pickle.dump([_each.device, _each.pos()], _file)
                pickle.dump(SAVE_FILE_SEPARATOR, _file)

    def init_ui(self):
        self.show()

    def init_lists(self):
        self.input_devices = utils.AConnectionHandler.get_input_devices()
        self.output_devices = utils.AConnectionHandler.get_output_devices()
        self.connections = utils.AConnectionHandler.get_connections()

        self.devices.extend(self.input_devices)
        self.devices.extend(self.output_devices)

    def init_node_editor(self):
        self.connections_view = utils.QDMNodeEditor(self.node_editor_place_holder,
                                                    utils.QDMNodeEditorScene(25, 5, self.connections_view), self)

        for _device in self.devices:
            self.nodes.append(utils.Node(_device, self.connections_view))

        self.update_nodes()

    def update_nodes(self):
        for _each in self.nodes:
            if _each not in self.connections_view.scene.items():
                self.connections_view.scene.addItem(_each)


if __name__ == '__main__':
    # Run App
    app = QApplication(sys.argv)
    ui = UI()

    # Global Style
    file = QFile(GLOBAL_QSS_PATH)
    file.open(QFile.ReadOnly | QFile.Text)
    style_sheet = str(file.readAll(), encoding='utf-8')
    app.setStyleSheet(style_sheet)

    sys.exit(app.exec_())
