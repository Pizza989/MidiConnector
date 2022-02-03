import sys

from PyQt5 import uic
from PyQt5.QtCore import QFile
from PyQt5.QtWidgets import QMainWindow, QApplication, QFrame, QWidget

import utils

GUI_PATH = "design/node.ui"
GLOBAL_QSS_PATH = "design/style/main.qss"


class UI(QMainWindow):
    def __init__(self):
        super().__init__()

        # Load Graphics
        uic.loadUi(GUI_PATH, self)
        file = QFile(GLOBAL_QSS_PATH)
        file.open(QFile.ReadOnly | QFile.Text)
        style_sheet = str(file.readAll(), encoding='utf-8')
        self.setStyleSheet(style_sheet)

        self.node_editor_place_holder: QFrame = self.findChild(QFrame, "nodeEditorPlaceHolder")

        self.input_devices = []
        self.output_devices = []
        self.devices = []
        self.connections = []

        self.connections_view = None
        self.connections_graphics_scene = None

        self.init_lists()
        self.init_node_editor()
        self.init_ui()

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

        for each in self.devices:
            self.connections_view.scene.addItem(utils.Node(each, self.connections_view))


if __name__ == '__main__':
    # Run App
    app = QApplication(sys.argv)
    ui = UI()
    sys.exit(app.exec())
