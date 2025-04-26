from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QSizePolicy
from PyQt6.QtGui import QPainter, QPen, QFont
from PyQt6.QtCore import Qt
from core.audio_clip import AudioClip
from core.track import Track
from ui.waveform_widget import WaveformWidget

PIXELS_PER_SECOND = 100
INITIAL_DURATION = 60  # in seconds

class Ruler(QWidget):
    def __init__(self, duration=INITIAL_DURATION, parent=None):
        super().__init__(parent)
        self.duration = duration
        self.setMinimumHeight(30)
        self.setMinimumWidth(self.duration * PIXELS_PER_SECOND)

    def update_duration(self, duration):
        self.duration = duration
        self.setMinimumWidth(self.duration * PIXELS_PER_SECOND)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        pen = QPen(Qt.GlobalColor.black)
        painter.setPen(pen)
        font = QFont("Arial", 8)
        painter.setFont(font)

        height = self.height()
        for second in range(self.duration + 1):
            x = second * PIXELS_PER_SECOND
            painter.drawLine(x, 0, x, height)
            painter.drawText(x + 2, height // 2 + 5, f"{second}s")

class TrackWidget(QFrame):
    def __init__(self, track_number, backend_track: Track, notify_duration_change):
        super().__init__()
        self.track_number = track_number
        self.backend_track = backend_track
        self.notify_duration_change = notify_duration_change

        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.Shape.Box)
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.label = QLabel(f"Track {track_number}", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.mp3', '.wav')):
                clip = AudioClip(file_path)
                self.backend_track.add_clip(clip)
                self.label.setText(f"Dropped: {file_path.split('/')[-1]}")

                self.notify_duration_change(clip.duration)
                waveform = WaveformWidget(clip.audio, pixels_per_second=PIXELS_PER_SECOND)
                self.layout.addWidget(waveform)
            else:
                self.label.setText("Invalid file type")

class TimelineWidget(QWidget):
    def __init__(self, project_timeline):
        super().__init__()
        self.project_timeline = project_timeline
        self.duration = INITIAL_DURATION

        self.layout = QVBoxLayout()
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)

        self.ruler = Ruler(duration=self.duration)
        self.layout.addWidget(self.ruler)

        self.track_widgets = []
        for i, track in enumerate(self.project_timeline.tracks):
            track_widget = TrackWidget(i + 1, track, self.extend_if_needed)
            self.track_widgets.append(track_widget)
            self.layout.addWidget(track_widget)

        self.layout.addStretch()
        self.setLayout(self.layout)
        self.setMinimumWidth(self.duration * PIXELS_PER_SECOND)

    def extend_if_needed(self, clip_duration):
        required_duration = int(clip_duration) + 5
        if required_duration > self.duration:
            self.duration = required_duration
            self.setMinimumWidth(self.duration * PIXELS_PER_SECOND)
            self.ruler.update_duration(self.duration)
