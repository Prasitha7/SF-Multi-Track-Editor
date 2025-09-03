#ui\timeline_view.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QPushButton
)
from PyQt6.QtCore import Qt


from ui.properties_panel import PropertiesPanel
from ui.playhead import Playhead

from ui.timeline_widgets import TrackWidget
from ui.playback import PlaybackController, mix_project_audio
from ui.file_io import save_mixdown, save_session_only
from ui.constants import PIXELS_PER_SECOND, INITIAL_DURATION

class TimelineWidget(QWidget):
    def __init__(self, project_timeline, sync_path=None): 
        super().__init__()
        self.project_timeline = project_timeline
        self.final_audio = None
        self.duration = INITIAL_DURATION
        self.sync_path = sync_path

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
                notify_clip_selected=self.on_clip_selected,
                sync_path=self.sync_path
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
        # === Save Buttons ===
        self.save_button = QPushButton("Save Mixdown")
        self.save_button.setFixedWidth(120)
        self.save_button.clicked.connect(self.save_mixdown)

        self.session_save_button = QPushButton("Save Project")
        self.session_save_button.setFixedWidth(120)
        self.session_save_button.clicked.connect(self.save_session_only)


        # === Playhead (Red Line) ===
        self.playhead = Playhead(parent=self.timeline_area)
        self.playhead.show()

        self.playback_controller = PlaybackController(self.playhead, self.timeline_area)
        # === Layouts ===

        # Top bar 
        topbar_layout = QHBoxLayout()
        topbar_layout.addWidget(self.play_button)
        topbar_layout.addWidget(self.save_button)
        topbar_layout.addStretch()
        topbar_layout.addWidget(self.session_save_button)


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


    def toggle_playback(self):
        if self.playback_controller.playing:
            self.playback_controller.stop()
            self.play_button.setText("Play")
        else:
            self.final_audio = mix_project_audio(self.track_widgets, self.duration)
            if self.playback_controller.start(self.final_audio):
                self.play_button.setText("Pause")

    def save_mixdown(self):
        self.final_audio = mix_project_audio(self.track_widgets, self.duration)
        save_mixdown(self.final_audio, self.project_timeline, self.sync_path)

    def save_session_only(self):
        save_session_only(self.project_timeline, self.sync_path)
