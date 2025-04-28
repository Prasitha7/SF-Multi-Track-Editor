from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy,
    QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton
import simpleaudio as sa
from pydub import AudioSegment


from core.audio_clip import AudioClip
from core.track import Track
from ui.clip_widget import ClipWidget
from ui.properties_panel import PropertiesPanel
from ui.playhead import Playhead



PIXELS_PER_SECOND = 100
INITIAL_DURATION = 60  # seconds

class TrackWidget(QFrame):
    def __init__(self, track_number, backend_track: Track, notify_duration_change, notify_clip_selected):
        super().__init__()
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
            if file_path.lower().endswith(('.mp3', '.wav')):
                clip = AudioClip(file_path)
                self.backend_track.add_clip(clip)

                clip_widget = ClipWidget(clip.audio, pixels_per_second=PIXELS_PER_SECOND, parent=self.clip_area)
                clip_widget.move(self.current_x, 0)
                clip_widget.show()

                clip_widget.mousePressEvent = self.wrap_clip_select(clip_widget)

                self.current_x += clip_widget.width()

                self.notify_duration_change(clip.duration)
            else:
                self.label.setText("Invalid file type")

    def wrap_clip_select(self, clip_widget):
        def handler(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.notify_clip_selected(clip_widget)
            ClipWidget.mousePressEvent(clip_widget, event)
        return handler

class TimelineWidget(QWidget):
    def __init__(self, project_timeline):
        super().__init__()
        self.project_timeline = project_timeline
        self.duration = INITIAL_DURATION

        # === Tracks ===
        self.track_widgets = []
        self.layout = QVBoxLayout()
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)

        for i, track in enumerate(self.project_timeline.tracks):
            track_widget = TrackWidget(
                i + 1,
                track,
                notify_duration_change=self.extend_if_needed,
                notify_clip_selected=self.on_clip_selected
            )
            self.track_widgets.append(track_widget)
            self.layout.addWidget(track_widget)

        self.layout.addStretch()

        self.timeline_area = QWidget()
        self.timeline_area.setLayout(self.layout)
        self.timeline_area.setMinimumWidth(self.duration * PIXELS_PER_SECOND)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.timeline_area)

        # === Properties Panel ===
        self.properties_panel = PropertiesPanel()
        self.properties_panel.hide()

        # === Play Button ===
        self.play_button = QPushButton("Play")
        self.play_button.setFixedWidth(100)
        self.play_button.clicked.connect(self.toggle_playback)

        # === Playhead (Red Line) ===
        from ui.playhead import Playhead
        self.playhead = Playhead(parent=self.timeline_area)
        self.playhead.show()

        self.timer = None
        self.playing = False

        # === Layouts ===

        # Top bar with Play Button
        topbar_layout = QHBoxLayout()
        topbar_layout.addWidget(self.play_button)
        topbar_layout.addStretch()

        # Timeline and Properties side-by-side
        timeline_with_props = QHBoxLayout()
        timeline_with_props.addWidget(self.scroll)
        timeline_with_props.addWidget(self.properties_panel)

        # Full Layout
        full_layout = QVBoxLayout()
        full_layout.addLayout(topbar_layout)          # First row
        full_layout.addLayout(timeline_with_props)    # Second row

        self.setLayout(full_layout)



    def extend_if_needed(self, clip_duration):
        required_duration = int(clip_duration) + 5
        if required_duration > self.duration:
            self.duration = required_duration
            self.timeline_area.setMinimumWidth(self.duration * PIXELS_PER_SECOND)

    def on_clip_selected(self, clip_widget):
        self.selected_clip = clip_widget
        props = clip_widget.get_properties()
        self.properties_panel.update_fields(props)
        self.properties_panel.show()

        try:
            self.properties_panel.save_button.clicked.disconnect()
        except TypeError:
            pass

        self.properties_panel.save_button.clicked.connect(self.apply_properties)


    def apply_properties(self):
        if not hasattr(self, 'selected_clip'):
            return

        inputs = self.properties_panel.get_inputs()

        # Update ClipWidget
        self.selected_clip.start_time_offset = inputs["start_offset"]
        self.selected_clip.end_time_offset = inputs["end_offset"]

        self.selected_clip.move(int(inputs["position_sec"] * PIXELS_PER_SECOND), self.selected_clip.y())
        self.selected_clip.update_audio_clip()

        # Refresh property panel to reflect true values after update
        props = self.selected_clip.get_properties()
        self.properties_panel.update_fields(props)

    def start_playback(self):
        if self.playing:
            return
        from PyQt6.QtCore import QTimer
        self.playing = True
        self.playhead.x_pos = 0
        self.playhead.move_to(0)

        self.timer = QTimer()
        self.timer.timeout.connect(self.move_playhead)
        self.timer.start(50)  # Move every 50ms (~20 fps)

    def move_playhead(self):
        step = PIXELS_PER_SECOND / 20  # 50ms -> 1s/20
        self.playhead.x_pos += int(step)
        self.playhead.move_to(self.playhead.x_pos)

        if self.playhead.x_pos > self.timeline_area.width():
            self.stop_playback()

    def stop_playback(self):
        if self.timer:
            self.timer.stop()
        self.playing = False

    def toggle_playback(self):
        if not self.playing:
            self.start_playback()
            self.play_button.setText("Pause")
        else:
            self.stop_playback()
            self.play_button.setText("Play")

