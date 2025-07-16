import os
import shutil
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QSizePolicy
from PyQt6.QtCore import Qt

from core.audio_clip import AudioClip
from ui.clip_widget import ClipWidget
from ui.constants import PIXELS_PER_SECOND


class TrackWidget(QFrame):
    def __init__(self, track_number, backend_track, notify_duration_change, notify_clip_selected, sync_path):
        super().__init__()
        self.sync_path = sync_path
        self.track_number = track_number
        self.backend_track = backend_track
        self.notify_duration_change = notify_duration_change
        self.notify_clip_selected = notify_clip_selected

        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.Shape.Box)
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.label = QLabel(f"Track {track_number}", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        self.track_layout = QVBoxLayout()
        self.track_layout.addWidget(self.label)

        self.clip_area = QWidget()
        self.clip_area.setMinimumHeight(80)
        self.clip_area.setStyleSheet("background-color: #eee;")
        self.clip_area.setLayout(QVBoxLayout())
        self.clip_area.layout().setContentsMargins(0, 0, 0, 0)

        self.track_layout.addWidget(self.clip_area)
        self.setLayout(self.track_layout)

        self.current_x = 0

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith((".mp3", ".wav")):
                asset_dir = os.path.join(self.sync_path, "assets")
                os.makedirs(asset_dir, exist_ok=True)

                filename = os.path.basename(file_path)
                asset_path = os.path.join(asset_dir, filename)

                if not os.path.exists(asset_path):
                    try:
                        shutil.copy2(file_path, asset_path)
                    except Exception as e:
                        self.label.setText(f"Copy failed: {e}")
                        return

                try:
                    clip = AudioClip(asset_path)
                    clip.source_path = asset_path
                    self.backend_track.add_clip(clip)

                    clip_widget = ClipWidget(clip.audio, pixels_per_second=PIXELS_PER_SECOND, parent=self.clip_area)
                    clip_widget.move(self.current_x, 0)
                    clip_widget.show()

                    clip_widget.mousePressEvent = self.wrap_clip_select(clip_widget)

                    self.current_x += clip_widget.width()
                    self.notify_duration_change(clip.duration)

                except Exception as e:
                    self.label.setText(f"Failed to load clip: {e}")
            else:
                self.label.setText("Invalid file type")

    def wrap_clip_select(self, clip_widget):
        def handler(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.notify_clip_selected(clip_widget)
            ClipWidget.mousePressEvent(clip_widget, event)
        return handler
