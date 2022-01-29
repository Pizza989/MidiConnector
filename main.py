from __future__ import annotations

from typing import List

from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QPushButton, QScrollArea
from PyQt5 import uic
import sys
import subprocess


class Loader:
    @classmethod
    def get_device_list(cls) -> List[MidiDevice]:
        stdout = subprocess.getoutput("aconnect -l").split("client ")
        stdout = [e.replace(":", "").replace("'", "") for e in stdout]
        del stdout[0]

        for device in stdout:
            for i in range(len(device)):
                _id = device[i]

    @classmethod
    def get_connections(cls):
        pass


class MidiDevice:
    def __init__(self, _id: int, name: str, channels=None):
        if channels is None:
            channels = []
        self.id = _id
        self.name = name

        self.channels = channels


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()

        # Load UI
        uic.loadUi("design/main.ui", self)

        # Init Components
        self.scroll_area: QScrollArea = self.findChild(QScrollArea, "scrollArea")

        # Show window
        self.show()


if __name__ == '__main__':
    # Initialize
    device_list = Loader.get_device_list()
    connections = Loader.get_connections()

    # Run GUI
    app = QApplication(sys.argv)
    ui = UI()
    sys.exit(app.exec())
