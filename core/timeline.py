from typing import List
from .track import Track

class Timeline:
    def __init__(self, name: str):
        self.name = name
        self.tracks: List[Track] = []

    def add_track(self, track: Track):
        self.tracks.append(track)

    def to_dict(self):
        return {
            "name": self.name,
            "tracks": [track.to_dict() for track in self.tracks]
        }

    @staticmethod
    def from_dict(data):
        timeline = Timeline(data["name"])
        for track_data in data["tracks"]:
            timeline.add_track(Track.from_dict(track_data))
        return timeline
