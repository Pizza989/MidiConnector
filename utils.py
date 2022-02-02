import math
import subprocess
from typing import List

from PyQt5.QtCore import QLine, Qt, QEvent
from PyQt5.QtGui import QColor, QPen, QMouseEvent
from PyQt5.QtWidgets import QWidget, QListWidgetItem, QMainWindow, QGraphicsItem, QGraphicsScene, QGraphicsView, \
    QGraphicsSceneMouseEvent


class DeviceType:
    input = 0
    output = 1


class AConnectionHandler:

    @classmethod
    def parse_device_list(cls, param: str) -> list:
        _stdout = subprocess.getoutput(
            f"export LANG=en_EN.UTF-8; aconnect -{param}")  # make sure the output is a certain language

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
    def get_output_devices(cls) -> List["MidiDevice"]:
        _dev_list = cls.parse_device_list("o")
        return [MidiDevice(_device[0][0], _device[0][1], _device[0][2], DeviceType.output, _device[1]) for _device in
                _dev_list]

    @classmethod
    def get_input_devices(cls) -> List["MidiDevice"]:
        _dev_list = cls.parse_device_list("i")
        return [MidiDevice(_device[0][0], _device[0][1], _device[0][2], DeviceType.input, _device[1]) for _device in
                _dev_list]

    @classmethod
    def get_connections(cls):
        _dev_list = cls.parse_device_list("l")

    @classmethod
    def set_connection(cls, _in: "MidiDevice", _out: "MidiDevice", params: List[str]):
        subprocess.getoutput(f"aconnect {[_e for _e in params]}")


class Channel(QListWidgetItem):
    def __init__(self, _id: int, text: str, parent: "MidiDevice"):
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

        self.setText(self.name)
        self.setToolTip(self.__repr__())

    def __repr__(self):
        return f"{self.id}: {self.name}, Args: {self.args}, Channels: {self.channels}, Type: {self.type}"


class MidiDeviceItem(QGraphicsItem):
    def __init__(self, device: MidiDevice):
        super().__init__()
        self._device = device
        self.id = device.id
        self.name = device.name
        self.args = device.args
        self.type = device.type

        self.channel = device.channels

        self.setToolTip(self.__repr__())
        self.setFlag(QGraphicsItem.ItemIsMovable)

    def __repr__(self):
        return self._device.__repr__()


class DevicePopUp(QWidget):
    def __init__(self, device: MidiDevice, win: QMainWindow):
        super().__init__(win)
        self.win = win
        self.device = device
        self.setStyleSheet("	background-color: rgb(255, 0, 0); border: 2px;")

        self.setWindowTitle(self.device.name)
        self.setToolTip(self.device.__repr__())


class QDMNodeEditor(QGraphicsView):
    @classmethod
    def from_graphics_view(cls, graphics_view: QGraphicsView):
        # This will be enough for now
        super().setGeometry(graphics_view.geometry())
        super().setToolTip(graphics_view.toolTip())
        super().setParent(graphics_view.parentWidget())
        return cls


class QDMNodeEditorScene(QGraphicsScene):
    def __init__(self, grid_size: int, grid_squares: int, parent: QGraphicsView):
        super().__init__(parent)
        self.parent = parent

        self.grid_size = grid_size
        self.grid_squares = grid_squares

        self._color_background = QColor("#393939")
        self._color_light = QColor("#2f2f2f")
        self._color_dark = QColor("#292929")

        self._pen_light = QPen(self._color_light)
        self._pen_light.setWidth(1)
        self._pen_dark = QPen(self._color_dark)
        self._pen_dark.setWidth(2)

        self.scene_width, self.scene_height = 64000, 64000
        self.setSceneRect(-self.scene_width // 2, -self.scene_height // 2, self.scene_width, self.scene_height)

        self.setBackgroundBrush(self._color_background)

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)

        left = int(math.floor(rect.left()))
        right = int(math.ceil(rect.right()))
        top = int(math.floor(rect.top()))
        bottom = int(math.ceil(rect.bottom()))

        first_left = left - (left % self.grid_size)
        first_top = top - (top % self.grid_size)

        lines_light, lines_dark = [], []
        for x in range(first_left, right, self.grid_size):
            if x % (self.grid_size * self.grid_squares) != 0:
                lines_light.append(QLine(x, top, x, bottom))
            else:
                lines_dark.append(QLine(x, top, x, bottom))

        for y in range(first_top, bottom, self.grid_size):
            if y % (self.grid_size * self.grid_squares) != 0:
                lines_light.append(QLine(left, y, right, y))
            else:
                lines_dark.append(QLine(left, y, right, y))

        painter.setPen(self._pen_light)
        painter.drawLines(*lines_light)

        painter.setPen(self._pen_dark)
        painter.drawLines(*lines_dark)
