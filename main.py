#! /usr/bin/python

from __future__ import annotations

import subprocess
import sys
from typing import List, Optional

from PyQt5 import uic, QtGui
from PyQt5.QtCore import Qt, QSize, QMimeData
from PyQt5.QtGui import QPainter, QPen, QDrag
from PyQt5.QtWidgets import QMainWindow, QApplication, QListWidget, QListWidgetItem, QPushButton, QPlainTextEdit, \
    QLineEdit, QComboBox, QStyleFactory, QDockWidget, QFrame, QWidget, QGroupBox, QGraphicsEllipseItem, QGraphicsItem



class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()

        # Setup class Attributes
        self.current_output: Optional[MidiDevice] = None
        self.current_output_channel = 0
        self.current_input: Optional[MidiDevice] = None
        self.current_input_channel = 0

        self.editing_output = False

        # Load ui and style
        uic.loadUi("design/main.ui", self)
        _style_sheet = ""
        with open("design/style/main.qss", "r") as file:
            self.setStyleSheet("".join(file.readlines()))

        # Init Components
        self.output_list_widget: QListWidget = self.findChild(QListWidget, "output_list_widget")
        self.input_list_widget: QListWidget = self.findChild(QListWidget, "input_list_widget")
        self.inspector_list_widget: QListWidget = self.findChild(QListWidget, "inspector_list_widget")

        self.inspect_dock: QDockWidget = self.findChild(QDockWidget, "inspectDock")

        self.connect_push_button: QPushButton = self.findChild(QPushButton, "connectPushButton")
        self.disconnect_push_button: QPushButton = self.findChild(QPushButton, "disconnectPushButton")
        self.disconnect_all_push_button: QPushButton = self.findChild(QPushButton, "disconnectAllButton")

        self.commandOutput: QPlainTextEdit = self.findChild(QPlainTextEdit, "commandOutput")
        self.commandInput: QLineEdit = self.findChild(QLineEdit, "commandInput")

        self.connections_panel_frame: QFrame = self.findChild(QFrame, "connectionsPanelFrame")

        # Init AConnection
        self.input_devices = AConnectionHandler.get_input_devices()
        self.output_devices = AConnectionHandler.get_output_devices()
        print(AConnectionHandler.parse_device_list("-i"))

        # Main Setup
        [self.output_list_widget.addItem(e) for e in self.output_devices]
        [self.input_list_widget.addItem(e) for e in self.input_devices]

        self.connect_push_button.clicked.connect(self.aconnect_connect)
        self.disconnect_push_button.clicked.connect(self.aconnect_disconnect)
        self.disconnect_all_push_button.clicked.connect(self.aconnect_disconnect_all)

        self.output_list_widget.itemClicked.connect(self.select_output)
        self.input_list_widget.itemClicked.connect(self.select_input)
        self.inspector_list_widget.itemClicked.connect(self.select_channel)

        self.commandInput.returnPressed.connect(self.do_command_input)

        self.populate_connections_panel_frame()
        self.setAcceptDrops(True)

        # Show window
        self.show()

    def dragEnterEvent(self, a0: QtGui.QDragEnterEvent) -> None:
        a0.accept()

    def dropEvent(self, a0: QtGui.QDropEvent) -> None:
        a0.source().move(a0.pos())
        a0.accept()

    def select_channel(self, item: Channel):
        if self.editing_output:
            self.current_output_channel = item.id
        else:
            self.current_input_channel = item.id

    def select_output(self, item: MidiDevice):
        self.inspector_list_widget.clear()
        self.current_output = item
        self.inspect_dock.setWindowTitle(
            f"Inspector - {self.current_output.name}: Output")
        for _e in self.current_output.channels:
            _build = Channel(_e[0], _e[1], item)

            self.inspector_list_widget.addItem(_build)

        self.editing_output = True

    def select_input(self, item: MidiDevice):
        self.inspector_list_widget.clear()
        self.current_input = item
        self.inspect_dock.setWindowTitle(
            f"Inspector - {self.current_input.name}: Input")
        for _e in self.current_input.channels:
            _build = Channel(_e[0], _e[1], item)

            self.inspector_list_widget.addItem(_build)

        self.editing_output = False

    def aconnect_connect(self):
        if self.current_input is None or self.current_output is None:
            return self.commandOutput.appendPlainText(
                "You'll need to select an output and an input device be trying to connect something\n")
        _out = subprocess.getoutput(
            f"aconnect {self.current_input.id}:{self.current_input_channel} "
            f"{self.current_output.id}:{self.current_output_channel}")
        self.commandOutput.appendPlainText(_out + "\n" if _out else "")

    def aconnect_disconnect(self):
        if self.current_input is None or self.current_output is None:
            return self.commandOutput.appendPlainText(
                "You'll need to select an output and an input device be trying to connect something\n")
        _out = subprocess.getoutput(
            f"aconnect -d {self.current_input.id}:{self.current_input_channel}"
            f" {self.current_output.id}:{self.current_output_channel}")
        self.commandOutput.appendPlainText(_out + "\n" if _out else "")

    def aconnect_disconnect_all(self):
        _out = subprocess.getoutput(f"aconnect -x")
        self.commandOutput.appendPlainText(_out + "\n" if _out else "")

    def do_command_input(self):
        self.commandOutput.appendPlainText(subprocess.getoutput(self.commandInput.text()))
        self.commandInput.clear()

    def populate_connections_panel_frame(self):
        for each in self.input_devices:
            DevicePopUp(each, self.connections_panel_frame)


if __name__ == '__main__':
    # Run App
    app = QApplication(sys.argv)
    ui = UI()
    sys.exit(app.exec())
