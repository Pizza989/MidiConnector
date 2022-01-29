#! /usr/bin/python

from __future__ import annotations

from typing import List, Optional

from PyQt5.QtWidgets import QMainWindow, QApplication, QListWidget, QListWidgetItem, QPushButton, QPlainTextEdit, \
    QLineEdit
from PyQt5 import uic
import sys
import subprocess


class DeviceType:
    output = 0
    input = 1


class AConnectionHandler:
    @classmethod
    def parse_device_list(cls, param: str) -> list:
        """

        :param param: either _i or o for input/output
        :return:
        """
        _out = []

        _stdout = subprocess.getoutput(f"aconnect -{param}").split("client ")
        del _stdout[0]

        for device in _stdout:
            _dump = device.splitlines()

            # Construct List[device_id, device_name, device_args]
            _dump = [each.replace(" ", "") for each in _dump]
            _temp = _dump[0].split(":")
            _temp.extend(_temp[1].split("'"))
            del _temp[1], _temp[1], _dump[0]
            _dump.insert(0,
                         _temp)  # Where does the type error come from
            # PycharmCE2021.2 on linux, python 3.9, standard settings

            # Construct Lists[channel_id, channel_str]
            _temp_next = []
            for _i in range(1, len(_dump)):
                _temp = _dump[_i].split("'")
                del _temp[-1]
                _temp_next.append(_temp)

            for _i in range(1, len(_dump)):
                del _dump[-1]

            _dump.append(_temp_next)

            _out.append(_dump)

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
        self.current_input: Optional[MidiDevice] = None

        # Load UI
        uic.loadUi("design/main.ui", self)

        # Init Components
        self.output_list_widget: QListWidget = self.findChild(QListWidget, "output_list_widget")
        self.input_list_widget: QListWidget = self.findChild(QListWidget, "input_list_widget")

        self.connectPushButton: QPushButton = self.findChild(QPushButton, "connectPushButton")
        self.disconnectPushButton: QPushButton = self.findChild(QPushButton, "disconnectPushButton")

        self.commandOutput: QPlainTextEdit = self.findChild(QPlainTextEdit, "commandOutput")
        self.commandInput: QLineEdit = self.findChild(QLineEdit, "commandInput")

        # Init AConnection
        input_devices = AConnectionHandler.get_input_devices()
        output_devices = AConnectionHandler.get_output_devices()

        # Main Setup
        [self.output_list_widget.addItem(e) for e in output_devices]
        [self.input_list_widget.addItem(e) for e in input_devices]

        self.connectPushButton.clicked.connect(self.aconnect_connect)
        self.disconnectPushButton.clicked.connect(self.aconnect_disconnect)

        self.output_list_widget.itemClicked.connect(self.register_output)
        self.input_list_widget.itemClicked.connect(self.register_input)

        self.commandInput.returnPressed.connect(self.do_command_input)

        # Show window
        self.show()

    def register_output(self, item):
        self.current_output = item

    def register_input(self, item):
        self.current_input = item

    def aconnect_connect(self):
        if self.current_input is None or self.current_output is None:
            return self.commandOutput.insertPlainText(
                "Two Midi devices one Output one Input must be highlighted in the ConnectionPanel\n")
        self.commandOutput.insertPlainText(
            subprocess.getoutput(f"aconnect {self.current_input.id} {self.current_output.id}") + "\n")

    def aconnect_disconnect(self):
        if self.current_input is None or self.current_output is None:
            return self.commandOutput.insertPlainText(
                "Two Midi devices one Output one Input must be highlighted in the ConnectionPanel\n")
        self.commandOutput.insertPlainText(
            subprocess.getoutput(f"aconnect -d {self.current_input.id} {self.current_output.id}") + "\n")

    def do_command_input(self):
        self.commandOutput.insertPlainText(subprocess.getoutput(self.commandInput.text()) + "\n")
        self.commandInput.clear()


if __name__ == '__main__':
    # Run GUI
    app = QApplication(sys.argv)
    ui = UI()
    sys.exit(app.exec())
