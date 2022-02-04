import math
import subprocess
import typing
from typing import List

from PyQt5.QtCore import QLine, Qt, QEvent, QRectF, QRect, QPointF
from PyQt5.QtGui import QColor, QPen, QMouseEvent, QPainter, QPainterPath, QFont, QBrush, QFocusEvent
from PyQt5.QtWidgets import QWidget, QListWidgetItem, QGraphicsItem, QGraphicsScene, QGraphicsView, \
    QFrame, QVBoxLayout, QGraphicsTextItem, QStyleOptionGraphicsItem, \
    QGraphicsProxyWidget, QLabel, QHBoxLayout, QSizePolicy, QRadioButton, QSpacerItem, QGraphicsSceneMouseEvent
from PyQt5.uic.Compiler.qtproxies import QtGui


class DeviceType:
    input = 0
    output = 1

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        if self.value == DeviceType.input:
            return "Input"
        elif self.value == DeviceType.output:
            return "Output"
        else:
            raise ValueError("DeviceType's value must always be in range [0, 1] - Input/Output")


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
                _curr_client[0][0] = int(_curr_client[0][0])
                continue
            elif _line.replace("\t", "").split()[0].replace(" ", "").isdigit():  # if a channel is declared
                _channel = _line.replace("\t", "").replace(" ", "").split("'")  # parse a channel
                del _channel[2]
                _curr_channel = _channel
                _curr_channel[0] = int(_curr_channel[0])
                _curr_client[1].append(_channel)
                continue
            elif _line.startswith("\t"):  # if a connection is declared
                if _line.startswith("	Connected From: "):
                    _temp = _line.replace("	Connected From: ", "").replace(" ", "").split(",")
                    _conns = [_conn.split(":") for _conn in _temp]
                    _conns = [[int(_conn[0]), int(_conn[1]), DeviceType.input] for _conn in _conns]
                    _curr_channel.append(_conns)
                elif _line.startswith("	Connecting To: "):
                    _temp = _line.replace("	Connecting To: ", "").replace(" ", "").split(",")
                    _conns = [_conn.split(":") for _conn in _temp]
                    _conns = [[int(_conn[0]), int(_conn[1]), DeviceType.output] for _conn in _conns]
                    _curr_channel.append(_conns)

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
        _temp = []
        _out = []
        _curr_dev_id = 0
        _curr_ch_id = 0
        for _dev in cls.parse_device_list("l"):
            _curr_dev_id = _dev[0][0]
            for _channel in _dev[1]:
                _curr_ch_id = _channel[0]
                if len(_channel) == 3:
                    for _conn in _channel[2]:
                        if _conn[2] == DeviceType.input:  # Only outputting connections should be at index 0
                            continue
                        _out.append([[_curr_dev_id, _curr_ch_id], [_conn[0], _conn[1]]])  # [[From where], [to where]]
        return _out


class MidiDevice:
    def __init__(self, _id: int, name: str, args: str, _type: int, channels=None):
        super().__init__()
        # Setup class attributes
        if channels is None:
            channels = []
        self.id = _id
        self.name = name
        self.args = args
        self.type = DeviceType(_type)

        self.channels = channels

    def __repr__(self):
        return f"{self.id}: {self.name}, Args: {self.args}, Channels: {self.channels}, Type: {self.type}"


class QDMNodeEditor(QGraphicsView):
    def __init__(self, place_holder: QFrame, node_scene: "QDMNodeEditorScene", main_class):
        super().__init__()
        place_holder.layout().addWidget(self)

        self.scene = node_scene
        self.main_class = main_class

        self.setScene(self.scene)
        self.setRenderHints(
            QPainter.Antialiasing | QPainter.HighQualityAntialiasing | QPainter.TextAntialiasing |
            QPainter.SmoothPixmapTransform)

        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.middleMouseButtonPress(event)
        elif event.button() == Qt.LeftButton:
            self.rightMouseButtonPress(event)
        elif event.button() == Qt.RightButton:
            self.rightMouseButtonPress(event)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.middleMouseButtonRelease(event)
        elif event.button() == Qt.LeftButton:
            self.leftMouseButtonRelease(event)
        elif event.button() == Qt.RightButton:
            self.rightMouseButtonRelease(event)
        else:
            super().mouseReleaseEvent(event)

    def middleMouseButtonPress(self, event):
        releaseEvent = QMouseEvent(QEvent.MouseButtonRelease, event.localPos(), event.screenPos(),
                                   Qt.LeftButton, Qt.NoButton, event.modifiers())
        super().mouseReleaseEvent(releaseEvent)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        fakeEvent = QMouseEvent(event.type(), event.localPos(), event.screenPos(),
                                Qt.LeftButton, event.buttons() | Qt.LeftButton, event.modifiers())
        super().mousePressEvent(fakeEvent)

    def middleMouseButtonRelease(self, event):
        fakeEvent = QMouseEvent(event.type(), event.localPos(), event.screenPos(),
                                Qt.LeftButton, event.buttons() & ~Qt.LeftButton, event.modifiers())
        super().mouseReleaseEvent(fakeEvent)
        self.setDragMode(QGraphicsView.NoDrag)

    def leftMouseButtonPress(self, event):
        return super().mousePressEvent(event)

    def leftMouseButtonRelease(self, event):
        return super().mouseReleaseEvent(event)

    def rightMouseButtonPress(self, event):
        return super().mousePressEvent(event)

    def rightMouseButtonRelease(self, event):
        return super().mouseReleaseEvent(event)


class QDMNodeEditorScene(QGraphicsScene):
    def __init__(self, grid_size: int, grid_squares: int, parent: QGraphicsView):
        super().__init__(parent)
        self.parent = parent

        self.grid_size = grid_size
        self.grid_squares = grid_squares

        self._color_background = QColor("#31363b")
        self._color_light = QColor("#2f2f2f")
        self._color_dark = QColor("#232629")

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


class QDMGraphicsSocket(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.radius = 6.0
        self.outline_width = 1.0
        self._color_background = QColor("#FFFF7700")
        self._color_outline = QColor("#FF000000")

        self._pen = QPen(self._color_outline)
        self._pen.setWidthF(self.outline_width)
        self._brush = QBrush(self._color_background)

    def paint(self, painter: QtGui.QPainter, option: 'QStyleOptionGraphicsItem',
              widget: typing.Optional[QWidget] = ...) -> None:
        # painting circle
        painter.setBrush(self._brush)
        painter.setPen(self._pen)
        painter.drawEllipse(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)

    def boundingRect(self):
        return QRectF(
            - self.radius - self.outline_width,
            - self.radius - self.outline_width,
            2 * (self.radius + self.outline_width),
            2 * (self.radius + self.outline_width),
        )


class QDMChannelWidget(QWidget):
    def __init__(self, channel, node: "Node"):
        super().__init__()

        self.channel = channel
        self.node = node

        self.setLayout(QHBoxLayout())
        print(self.node.width)
        self.text: QLabel = QLabel(f"{self.channel[0]}: {self.channel[1]}")
        self.text.setFont(QFont("Ubuntu", 10))
        self.text.setGeometry(self.node.width, self.node.channel_height, 0, 0)

        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.text)

        self.spacer = QSpacerItem(20, 20, QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
        self.layout().addItem(self.spacer)

        self.socket_button = QRadioButton()
        self.layout().addWidget(self.socket_button)

        self.setStyleSheet("QRadioButton{ background-color: " + self.node.bg_color + "; }")
        self.setMaximumWidth(self.node.width - 10)

    def focusInEvent(self, event: QFocusEvent) -> None:
        self.node.setZValue(1)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        self.node.setZValue(-1)


class QDMNodeContentWidget(QWidget):
    def __init__(self, node: "Node"):
        super().__init__()

        self.node = node
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.setStyleSheet("QWidget{ background-color: transparent; }")

        self.init_ui()

    def init_ui(self):
        _i = 0
        for _each in self.node.device.channels:
            _y = _i * self.node.channel_height + self.node.title_height
            self.layout().addWidget(
                QDMChannelWidget(_each, self.node))
            _i += 1


class Node(QGraphicsItem):
    def __init__(self, device: MidiDevice, parent: QDMNodeEditor, pos=None):
        super().__init__()

        if pos is None:
            pos = QPointF(0, 0)

        self._title_color = Qt.white
        self._title_font = QFont("Ubuntu", 10)

        self.base_width = 180
        self.base_height = 25
        self.channel_height = 35
        self.edge_size = 10.0
        self.title_height = 24.0
        self.padding = 4.0

        self._pen_default = QPen(QColor("#7F000000"))
        self._pen_selected = QPen(QColor("#999999"))

        self._brush_title = QBrush(QColor("#FF313131"))
        self.bg_color = "#E3212121"
        self._brush_background = QBrush(QColor(self.bg_color))

        self.title = QGraphicsTextItem(self)
        self.channels_text_objects = []
        self.socket_positions = []
        self.gr_content = QGraphicsProxyWidget(self)

        self.device = device
        self.parent = parent

        self.height = len(self.device.channels) * self.channel_height + self.base_height
        self.width = self.title.textWidth() + self.padding + self.base_width

        self.init_title()
        self.init_contents()

        self.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsFocusable)
        self.setPos(pos.x(), pos.y())

    def remove(self):
        self.parent.main_class.nodes.remove(self)
        self.parent.scene.removeItem(self)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == Qt.Key_Delete:
            self.remove()

    def focusInEvent(self, event: QFocusEvent) -> None:
        self.setZValue(1)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        self.setZValue(-1)

    def boundingRect(self):
        return QRectF(
            0,
            0,
            self.width,
            self.height
        ).normalized()

    def init_title(self):
        self.title.setDefaultTextColor(self._title_color)
        self.title.setFont(self._title_font)
        self.title.setPos(self.padding, 0)
        self.title.setPlainText(f"{self.device.name} - {self.device.type}")

    def init_contents(self):
        """
            _i = 0
            for _each in self.device.channels:
            _y = _i * self.channel_height + self.title_height
            _temp = QGraphicsTextItem(self)
            _temp.setPlainText(f"{_each[0]}: {_each[1]}")

            _temp.setY(_y)
            self.channels_text_objects.append(_temp)
            self.socket_positions.append([self.x() + self.width, _y])
            _i += 1

        """
        self.gr_content.setWidget(QDMNodeContentWidget(self))
        self.gr_content.setPos(self.padding, self.title_height + self.padding)

    def paint(self, painter, q_style_option_graphics_item, widget=None):
        # set values
        self.height = len(self.device.channels) * self.channel_height + self.base_height
        self.width = self.title.textWidth() + self.padding + self.base_width

        # draw sockets

        # title
        path_title = QPainterPath()
        path_title.setFillRule(Qt.WindingFill)
        path_title.addRoundedRect(0, 0, self.width, self.title_height, self.edge_size, self.edge_size)
        path_title.addRect(0, self.title_height - self.edge_size, self.edge_size, self.edge_size)
        path_title.addRect(self.width - self.edge_size, self.title_height - self.edge_size, self.edge_size,
                           self.edge_size)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._brush_title)
        painter.drawPath(path_title.simplified())

        # content
        path_content = QPainterPath()
        path_content.setFillRule(Qt.WindingFill)
        path_content.addRoundedRect(0, self.title_height, self.width, self.height - self.title_height, self.edge_size,
                                    self.edge_size)
        path_content.addRect(0, self.title_height, self.edge_size, self.edge_size)
        path_content.addRect(self.width - self.edge_size, self.title_height, self.edge_size, self.edge_size)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self._brush_background)
        painter.drawPath(path_content.simplified())

        # outline
        path_outline = QPainterPath()
        path_outline.addRoundedRect(0, 0, self.width, self.height, self.edge_size, self.edge_size)
        painter.setPen(self._pen_default if not self.isSelected() else self._pen_selected)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path_outline.simplified())
