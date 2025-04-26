from typing import List
from .audio_clip import AudioClip

class Track:
    def __init__(self):
        self.clips: List[AudioClip] = []

    def add_clip(self, clip: AudioClip):
        self.clips.append(clip)

    def to_dict(self):
        return {"clips": [clip.to_dict() for clip in self.clips]}

    @staticmethod
    def from_dict(data):
        track = Track()
        for clip_data in data["clips"]:
            track.add_clip(AudioClip.from_dict(clip_data))
        return track
