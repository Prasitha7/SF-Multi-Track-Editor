import os
import pygame
from PyQt6.QtCore import QTimer
from pydub import AudioSegment

from ui.clip_widget import ClipWidget
from ui.constants import PIXELS_PER_SECOND


def mix_project_audio(track_widgets, duration):
    """Compile all clips from the provided track widgets."""
    total_duration_ms = 0
    track_segments = []

    for track_widget in track_widgets:
        track_audio = AudioSegment.silent(duration=duration * 1000)
        for clip_widget in track_widget.clip_area.children():
            if isinstance(clip_widget, ClipWidget):
                clip_audio = clip_widget.audio_clip
                clip_start_sec = clip_widget.x() / PIXELS_PER_SECOND
                clip_start_ms = int(clip_start_sec * 1000)
                track_audio = track_audio.overlay(clip_audio, position=clip_start_ms)
                total_duration_ms = max(total_duration_ms, clip_start_ms + len(clip_audio))
        track_segments.append(track_audio)

    if not track_segments:
        return None

    final_mix = track_segments[0]
    for segment in track_segments[1:]:
        final_mix = final_mix.overlay(segment)

    return final_mix[:total_duration_ms]


class PlaybackController:
    def __init__(self, playhead, timeline_area):
        self.playhead = playhead
        self.timeline_area = timeline_area
        self.timer = None
        self.playing = False
        self.x_pos = 0

    def start(self, audio_segment):
        if self.playing or audio_segment is None or len(audio_segment) == 0:
            return False

        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            pygame.mixer.quit()

        if not os.path.exists("temp"):
            os.makedirs("temp")

        audio_segment.export("temp/compiled_mixdown.wav", format="wav")

        pygame.mixer.init()
        pygame.mixer.music.load("temp/compiled_mixdown.wav")
        pygame.mixer.music.play()

        self.x_pos = 0
        self.playhead.move_to(0)

        self.timer = QTimer()
        self.timer.timeout.connect(self.move_playhead)
        self.timer.start(50)
        self.playing = True
        return True

    def move_playhead(self):
        step = PIXELS_PER_SECOND / 20  # 50ms -> 1s/20
        self.x_pos += int(step)
        self.playhead.move_to(self.x_pos)

        if self.x_pos > self.timeline_area.width():
            self.stop()

    def stop(self):
        if self.timer:
            self.timer.stop()
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        self.playing = False
