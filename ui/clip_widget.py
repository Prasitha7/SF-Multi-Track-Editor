#ui\clip_widget.py
from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QColor, QMouseEvent, QKeyEvent
from PyQt6.QtCore import Qt
import numpy as np
from pydub import AudioSegment
from core.audio_clip import AudioClip


class ClipWidget(QWidget):
    RESIZE_MARGIN = 10

    def __init__(self, clip: AudioClip, pixels_per_second=100, parent=None):
        super().__init__(parent)
        self.backend_clip = clip
        self.original_audio = AudioSegment.from_file(clip.source_path)
        self.start_time_offset = clip.trim_start
        self.end_time_offset = clip.trim_end
        self.pixels_per_second = pixels_per_second

        self.selected = False
        self.selected_side = None  # 'left', 'right', or None

        self.update_audio_clip()
        self.setMinimumHeight(80)

        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)


    def update_audio_clip(self):
        start_ms = int(self.start_time_offset * 1000)
        end_ms = len(self.original_audio) - int(self.end_time_offset * 1000)
        self.audio_clip = self.original_audio[start_ms:end_ms]
        self.duration = len(self.audio_clip) / 1000.0
        self.samples = self.extract_samples(self.audio_clip)
        self.setFixedWidth(int(self.duration * self.pixels_per_second))
        self.backend_clip.audio = self.audio_clip
        self.backend_clip.trim_start = self.start_time_offset
        self.backend_clip.trim_end = self.end_time_offset
        self.backend_clip.duration = self.duration
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

        if self.selected:
            painter.fillRect(self.rect(), QColor(200, 200, 255))  # Selected background
        else:
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

        # Draw left and right handles
        if self.selected_side == 'left':
            painter.fillRect(0, 0, self.RESIZE_MARGIN, self.height(), QColor(255, 100, 100))
        else:
            painter.fillRect(0, 0, self.RESIZE_MARGIN, self.height(), QColor(180, 180, 180))

        if self.selected_side == 'right':
            painter.fillRect(self.width() - self.RESIZE_MARGIN, 0, self.RESIZE_MARGIN, self.height(), QColor(255, 100, 100))
        else:
            painter.fillRect(self.width() - self.RESIZE_MARGIN, 0, self.RESIZE_MARGIN, self.height(), QColor(180, 180, 180))

    def mousePressEvent(self, event: QMouseEvent):
        if event.pos().x() <= self.RESIZE_MARGIN:
            self.selected_side = 'left'
        elif event.pos().x() >= self.width() - self.RESIZE_MARGIN:
            self.selected_side = 'right'
        else:
            self.selected_side = None

        if self.selected:
            self.selected = False
            self.clearFocus()
        else:
            self.selected = True
            self.setFocus()

        self.update()

    def keyPressEvent(self, event: QKeyEvent):
        if not self.selected:
            return

        if self.selected_side is None:
            return

        # How much to trim
        small_step = 0.1
        large_step = 1.0
        step = large_step if event.modifiers() == Qt.KeyboardModifier.ShiftModifier else small_step

        if self.selected_side == 'left':
            if event.key() == Qt.Key.Key_Left:
                self.start_time_offset += step
                self.update_audio_clip()
            elif event.key() == Qt.Key.Key_Right:
                if self.start_time_offset - step >= 0:
                    self.start_time_offset -= step
                    self.update_audio_clip()

        if self.selected_side == 'right':
            if event.key() == Qt.Key.Key_Left:
                if self.end_time_offset - step >= 0:
                    self.end_time_offset -= step
                    self.update_audio_clip()
            elif event.key() == Qt.Key.Key_Right:
                self.end_time_offset += step
                self.update_audio_clip()

    def get_properties(self):
        return {
            "start_time_offset": round(self.start_time_offset, 2),
            "end_time_offset": round(self.end_time_offset, 2),
            "position_sec": round(self.x() / self.pixels_per_second, 2),
            "duration_sec": round(self.duration, 2)
        }
