import json
from typing import List
from .timeline import Timeline

class Project:
    def __init__(self, name: str):
        self.name = name
        self.timelines: List[Timeline] = []

    def add_timeline(self, timeline: Timeline):
        self.timelines.append(timeline)

    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def load(self, path: str):
        with open(path, 'r') as f:
            data = json.load(f)
            self.name = data["name"]
            self.timelines = [Timeline.from_dict(tl) for tl in data["timelines"]]

    def to_dict(self):
        return {
            "name": self.name,
            "timelines": [tl.to_dict() for tl in self.timelines]
        }
