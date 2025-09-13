#ui\\timeline_ruler.py
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtCore import Qt


class TimelineRuler(QWidget):
    """Displays frame numbers and elapsed time along the timeline."""

    def __init__(self, duration, pixels_per_second, frame_start=0, fps=24.0, clip_start_seconds=0.0):
        super().__init__()
        self.pixels_per_second = pixels_per_second
        self.frame_start = int(frame_start)
        self.fps = float(fps)
        self.clip_start_seconds = float(clip_start_seconds)
        self.duration = int(duration)

        self.setFixedHeight(40)
        self.setMinimumWidth(self.duration * self.pixels_per_second)

    def set_duration(self, duration):
        self.duration = int(duration)
        self.setMinimumWidth(self.duration * self.pixels_per_second)
        self.update()

    def format_time(self, seconds):
        seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(245, 245, 245))
        pen = QPen(Qt.GlobalColor.black)
        painter.setPen(pen)

        height = self.height()
        num_seconds = int(self.duration) + 1
        for sec in range(num_seconds):
            x = sec * self.pixels_per_second
            painter.drawLine(x, 0, x, height)

            frame_number = self.frame_start + int(round((self.clip_start_seconds + sec) * self.fps))
            painter.drawText(x + 2, 12, str(frame_number))

            time_value = self.clip_start_seconds + sec
            painter.drawText(x + 2, height - 2, self.format_time(time_value))

