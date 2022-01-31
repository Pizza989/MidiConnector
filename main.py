#! /usr/bin/python

from __future__ import annotations

import subprocess
import sys
from typing import List, Optional

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen
from PyQt5.QtWidgets import QMainWindow, QApplication, QListWidget, QListWidgetItem, QPushButton, QPlainTextEdit, \
    QLineEdit, QComboBox, QStyleFactory, QDockWidget


class DeviceType:
    input = 0
    output = 1


class AConnectionHandler:

    @classmethod
    def parse_device_list(cls, param: str) -> list:
        _stdout = subprocess.getoutput(
            "export LANG=en_EN.UTF-8; aconnect -l")  # make sure the output is a certain language

        # For some reason aconnect uses \t and spaces to indent lines
        _stdout = _stdout.replace("    ", "\t")

        _curr_client: list = []
        _curr_channel: list = []
        _out: list = []

        for _line in _stdout.splitlines():
            if _line.startswith("client"):  # if a client is declared
                if _curr_client:  # if current client is finished
                    _out.append(_curr_client)
                _curr_client = [_line.replace("client ", "").replace(":", "").replace(" ", "").split("'"),
                                []]  # parse a client
                continue
            elif _line.replace("\t", "").split()[0].replace(" ", "").isdigit():  # if a channel is declared
                _channel = _line.replace("\t", "").replace(" ", "").split("'")  # parse a channel
                del _channel[2]
                _curr_channel = _channel
                _curr_client[1].append(_channel)
                continue
            elif _line.startswith("\t"):  # if a connection is declared
                if _line.startswith("	Connected From: "):
                    _conn = [_line.replace("	Connected From: ", "").split(":"), DeviceType.input]
                    _curr_channel.append(_conn)
                elif _line.startswith("	Connecting To: "):
                    _conn = [_line.replace("	Connecting To: ", "").split(":"), DeviceType.output]
                    _curr_channel.append(_conn)

        _out.append(_curr_client)  # Also append if there is no new client coming afterwards

        return _out

    @classmethod
    def get_output_devices(cls) -> List[MidiDevice]:
        _dev_list = cls.parse_device_list("o")
        return [MidiDevice(_device[0][0], _device[0][1], _device[0][2], DeviceType.output, _device[1]) for _device in
                _dev_list]

    @classmethod
    def get_input_devices(cls) -> List[MidiDevice]:
        _dev_list = cls.parse_device_list("i")
        return [MidiDevice(_device[0][0], _device[0][1], _device[0][2], DeviceType.input, _device[1]) for _device in
                _dev_list]

    @classmethod
    def get_connections(cls):
        pass

    @classmethod
    def set_connection(cls, _in: MidiDevice, _out: MidiDevice, params: List[str]):
        subprocess.getoutput(f"aconnect {[_e for _e in params]}")


class Channel(QListWidgetItem):
    def __init__(self, _id: int, text: str, parent: MidiDevice):
        super().__init__()
        self.id = _id
        self.text = text
        self.parent = parent

        self.setText(f"{self.id}: {self.text}")
        self.setToolTip(
            f"Device: {self.parent.name}, Type: {'Output' if self.parent.type == DeviceType.output else 'Input'}")


class MidiDevice(QListWidgetItem):
    def __init__(self, _id: int, name: str, args: str, _type: int, channels=None):
        super().__init__()
        # Setup class attributes
        if channels is None:
            channels = []
        self.id = _id
        self.name = name
        self.args = args
        self.type = _type

        self.channels = channels

        # Setup QListWidgetItem look
        self.setText(self.name)
        self.setToolTip(self.__repr__())

    def __repr__(self):
        return f"{self.id}: {self.name}, Args: {self.args}, Channels: {self.channels}, Type: {self.type}"


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

        # Init AConnection
        input_devices = AConnectionHandler.get_input_devices()
        output_devices = AConnectionHandler.get_output_devices()
        print(AConnectionHandler.parse_device_list("-i"))

        # Main Setup
        [self.output_list_widget.addItem(e) for e in output_devices]
        [self.input_list_widget.addItem(e) for e in input_devices]

        self.connect_push_button.clicked.connect(self.aconnect_connect)
        self.disconnect_push_button.clicked.connect(self.aconnect_disconnect)
        self.disconnect_all_push_button.clicked.connect(self.aconnect_disconnect_all)

        self.output_list_widget.itemClicked.connect(self.select_output)
        self.input_list_widget.itemClicked.connect(self.select_input)
        self.inspector_list_widget.itemClicked.connect(self.select_channel)

        self.commandInput.returnPressed.connect(self.do_command_input)

        # Show window
        self.show()

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


if __name__ == '__main__':
    # Run App
    app = QApplication(sys.argv)
    ui = UI()
    sys.exit(app.exec())
