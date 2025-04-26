from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QMouseEvent, QCursor
from PyQt6.QtCore import Qt
import numpy as np
from pydub import AudioSegment

class ClipWidget(QWidget):
    RESIZE_MARGIN = 10

    def __init__(self, audio_segment: AudioSegment, pixels_per_second=100, parent=None):
        super().__init__(parent)
        self.original_audio = audio_segment
        self.start_time_offset = 0.0  # seconds
        self.end_time_offset = 0.0  # seconds
        self.pixels_per_second = pixels_per_second

        self.dragging = False
        self.resizing_left = False
        self.resizing_right = False

        self.update_audio_clip()
        self.setMinimumHeight(80)

    def update_audio_clip(self):
        start_ms = int(self.start_time_offset * 1000)
        end_ms = len(self.original_audio) - int(self.end_time_offset * 1000)
        self.audio_clip = self.original_audio[start_ms:end_ms]
        self.duration = len(self.audio_clip) / 1000.0
        self.samples = self.extract_samples(self.audio_clip)
        self.setFixedWidth(int(self.duration * self.pixels_per_second))
        self.update()

    def extract_samples(self, segment):
        samples = np.array(segment.get_array_of_samples())
        if segment.channels == 2:
            samples = samples.reshape((-1, 2))
            samples = samples.mean(axis=1)
        downsample_factor = max(1, int(len(samples) / (self.duration * self.pixels_per_second)))
        samples = samples[::downsample_factor]
        samples = samples / np.max(np.abs(samples)) if samples.max() != 0 else samples
        return samples

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.fillRect(self.rect(), QColor(220, 220, 220))
        pen = QPen(Qt.GlobalColor.black)
        painter.setPen(pen)

        mid_y = self.height() // 2
        width = self.width()
        height = self.height()

        if len(self.samples) > 0:
            step = width / len(self.samples)
            for i, sample in enumerate(self.samples):
                x = int(i * step)
                y = int(sample * (height // 2))
                painter.drawLine(x, mid_y - y, x, mid_y + y)

        # Resize handles
        painter.fillRect(0, 0, self.RESIZE_MARGIN, self.height(), QColor(180, 180, 180))
        painter.fillRect(self.width() - self.RESIZE_MARGIN, 0, self.RESIZE_MARGIN, self.height(), QColor(180, 180, 180))

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.pos().x() <= self.RESIZE_MARGIN:
                self.resizing_left = True
            elif event.pos().x() >= self.width() - self.RESIZE_MARGIN:
                self.resizing_right = True
            else:
                self.dragging = True
            self.drag_start_pos = event.globalPosition().toPoint()
            self.start_geometry = self.geometry()

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.pos()
        global_pos = event.globalPosition().toPoint()

        if pos.x() <= self.RESIZE_MARGIN or pos.x() >= self.width() - self.RESIZE_MARGIN:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        else:
            self.setCursor(Qt.CursorShape.OpenHandCursor)

        delta = global_pos - self.drag_start_pos

        if self.dragging:
            new_x = self.start_geometry.x() + delta.x()
            self.move(new_x, self.y())

        if self.resizing_left:
            seconds_trimmed = delta.x() / self.pixels_per_second
            new_start = self.start_time_offset + seconds_trimmed
            if new_start >= 0 and new_start < (len(self.original_audio) / 1000.0 - self.end_time_offset - 1):
                self.start_time_offset = new_start
                self.update_audio_clip()

        if self.resizing_right:
            seconds_trimmed = delta.x() / self.pixels_per_second
            new_end = self.end_time_offset - seconds_trimmed
            if new_end >= 0 and new_end < (len(self.original_audio) / 1000.0 - self.start_time_offset - 1):
                self.end_time_offset = new_end
                self.update_audio_clip()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.dragging = False
        self.resizing_left = False
        self.resizing_right = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
