#ui\timeline_view.py
import os
import shutil

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy,
    QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton
from pydub import AudioSegment
import pygame


from core.audio_clip import AudioClip
from core.track import Track
from ui.clip_widget import ClipWidget
from ui.properties_panel import PropertiesPanel
from ui.playhead import Playhead
from storage.session_io import load_session_from_file, save_session_to_file



PIXELS_PER_SECOND = 100
INITIAL_DURATION = 60  # seconds

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

        # Populate existing clips
        for clip in self.backend_track.clips:
            widget = ClipWidget(clip, pixels_per_second=PIXELS_PER_SECOND, parent=self.clip_area)
            x = int(clip.start_time * PIXELS_PER_SECOND)
            widget.move(x, 0)
            widget.show()
            widget.mousePressEvent = self.wrap_clip_select(widget)
            self.current_x = max(self.current_x, x + widget.width())
            self.notify_duration_change(clip.start_time + clip.duration)


    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.mp3', '.wav')):
                # Use the correct sync folder path
                asset_dir = os.path.join(self.sync_path, "assets")
                os.makedirs(asset_dir, exist_ok=True)

                filename = os.path.basename(file_path)
                asset_path = os.path.join(asset_dir, filename)

                # Copy if not already in assets/
                if not os.path.exists(asset_path):
                    try:
                        shutil.copy2(file_path, asset_path)
                    except Exception as e:
                        self.label.setText(f"Copy failed: {e}")
                        return

                try:
                    clip = AudioClip(asset_path)
                    clip.source_path = asset_path  # make sure AudioClip supports this
                    clip.start_time = self.current_x / PIXELS_PER_SECOND
                    self.backend_track.add_clip(clip)

                    clip_widget = ClipWidget(clip, pixels_per_second=PIXELS_PER_SECOND, parent=self.clip_area)
                    clip_widget.move(self.current_x, 0)
                    clip_widget.show()

                    clip_widget.mousePressEvent = self.wrap_clip_select(clip_widget)

                    self.current_x += clip_widget.width()
                    self.notify_duration_change(clip.start_time + clip.duration)

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
        from ui.playhead import Playhead
        self.playhead = Playhead(parent=self.timeline_area)
        self.playhead.show()

        self.timer = None
        self.playing = False

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

    def sync_backend_from_widgets(self):
        for track_widget, backend_track in zip(self.track_widgets, self.project_timeline.tracks):
            backend_track.clips = []
            for widget in track_widget.clip_area.children():
                if isinstance(widget, ClipWidget):
                    clip = widget.backend_clip
                    clip.start_time = widget.x() / PIXELS_PER_SECOND
                    backend_track.add_clip(clip)

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
        import os

        self.playing = True

        self.mix_project_audio()
        if self.final_audio is None or len(self.final_audio) == 0:
            self.stop_playback()
            print("[ERROR] No audio to play.")
            return

        # Ensure mixer is reset to avoid file locks
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.quit()

        # Make sure temp folder exists
        if not os.path.exists("temp"):
            os.makedirs("temp")

        # Save compiled mix to file
        self.final_audio.export("temp/compiled_mixdown.wav", format="wav")

        # Start playback
        pygame.mixer.init()
        pygame.mixer.music.load("temp/compiled_mixdown.wav")
        pygame.mixer.music.play()

        self.playhead.x_pos = 0
        self.playhead.move_to(0)

        self.timer = QTimer()
        self.timer.timeout.connect(self.move_playhead)
        self.timer.start(50)


    def move_playhead(self):
        step = PIXELS_PER_SECOND / 20  # 50ms -> 1s/20
        self.playhead.x_pos += int(step)
        self.playhead.move_to(self.playhead.x_pos)

        if self.playhead.x_pos > self.timeline_area.width():
            self.stop_playback()

    def stop_playback(self):
        if self.timer:
            self.timer.stop()
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        self.playing = False


    def toggle_playback(self):
        if not self.playing:
            self.start_playback()
            self.play_button.setText("Pause")
        else:
            self.stop_playback()
            self.play_button.setText("Play")

    def mix_project_audio(self):
        """
        Create final compiled timeline from all clips.
        """

        print("Mixing project audio...")
        # Determine total length
        total_duration_ms = 0

        track_segments = []

        for track_widget in self.track_widgets:
            track_audio = AudioSegment.silent(duration=self.duration * 1000)

            # Walk each clip in the track
            for clip_widget in track_widget.clip_area.children():
                if isinstance(clip_widget, ClipWidget):
                    clip_audio = clip_widget.audio_clip

                    clip_start_sec = clip_widget.x() / PIXELS_PER_SECOND
                    clip_start_ms = int(clip_start_sec * 1000)

                    # Place clip at correct location
                    track_audio = track_audio.overlay(clip_audio, position=clip_start_ms)

                    total_duration_ms = max(total_duration_ms, clip_start_ms + len(clip_audio))

            track_segments.append(track_audio)

        if not track_segments:
            self.final_audio = None
            return

        # Mix tracks together
        final_mix = track_segments[0]
        for segment in track_segments[1:]:
            final_mix = final_mix.overlay(segment)

        # Trim to actual content length
        self.final_audio = final_mix[:total_duration_ms]
        print(f"Final compiled length: {total_duration_ms/1000:.2f} seconds")

    def save_mixdown(self):
        self.sync_backend_from_widgets()
        self.mix_project_audio()

        if self.final_audio is None or len(self.final_audio) == 0:
            print("[ERROR] No audio to export.")
            return

        if not hasattr(self, "sync_path"):
            print("No sync_path set — cannot save.")
            return

        try:
            save_path = os.path.join(self.sync_path, "compiled.wav")
            self.final_audio.export(save_path, format="wav")
            print(f"Auto-saved to {save_path}")

            save_session_to_file(self.project_timeline, self.sync_path)
            print(f"Session saved to {os.path.join(self.sync_path, 'session.json')}")

        except Exception as e:
            print(f"[ERROR] Failed to save mixdown or session: {e}")

            save_path = os.path.join(self.sync_path, "compiled.wav")
            try:
                self.final_audio.export(save_path, format="wav")
                print(f"Auto-saved to {save_path}")
            except Exception as e:
                print(f"[ERROR] Failed to save mixdown: {e}")


    def save_session_only(self):
        if not hasattr(self, "sync_path"):
            print("No sync_path set — cannot save session.")
            return
        try:
            self.sync_backend_from_widgets()
            save_session_to_file(self.project_timeline, self.sync_path)
            print(f"Session saved to {os.path.join(self.sync_path, 'session.json')}")
        except Exception as e:
            print(f"[ERROR] Failed to save session: {e}")
