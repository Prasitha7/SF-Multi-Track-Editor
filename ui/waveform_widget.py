from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtCore import Qt
import numpy as np
from pydub import AudioSegment

class WaveformWidget(QWidget):
    def __init__(self, audio_segment: AudioSegment, pixels_per_second=100, parent=None):
        super().__init__(parent)
        self.audio_segment = audio_segment
        self.duration = len(audio_segment) / 1000.0  # in seconds
        self.pixels_per_second = pixels_per_second
        self.samples = self.extract_samples(audio_segment)

        self.setMinimumHeight(60)
        self.setMinimumWidth(int(self.duration * self.pixels_per_second))

    def extract_samples(self, segment):
        samples = np.array(segment.get_array_of_samples())
        if segment.channels == 2:
            samples = samples.reshape((-1, 2))
            samples = samples.mean(axis=1)
        downsample_factor = max(1, int(len(samples) / (self.duration * self.pixels_per_second)))
        samples = samples[::downsample_factor]
        samples = samples / np.max(np.abs(samples))  # Normalize
        return samples

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen(Qt.GlobalColor.black)
        pen.setWidth(1)
        painter.setPen(pen)

        mid_y = self.height() // 2
        width = self.width()
        height = self.height()

        if len(self.samples) == 0:
            return

        step = width / len(self.samples)
        for i, sample in enumerate(self.samples):
            x = int(i * step)
            y = int(sample * (height // 2))
            painter.drawLine(x, mid_y - y, x, mid_y + y)
