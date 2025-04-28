from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtCore import Qt

class Playhead(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.x_pos = 0
        self.setMinimumHeight(1000)  # long enough to cover tracks

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(Qt.GlobalColor.red)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawLine(0, 0, 0, self.height())

    def move_to(self, x):
        self.move(x, 0)
        self.update()
