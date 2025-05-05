from pydub import AudioSegment

class AudioClip:
    def __init__(self, file_path: str, start_time: float = 0.0, duration: float = None):
        self.file_path = file_path
        self.source_path = file_path
        self.start_time = start_time
        self.audio = AudioSegment.from_file(file_path)
        self.duration = duration if duration else len(self.audio) / 1000.0  # in seconds

    def trim(self, start: float, end: float):
        start_ms = int(start * 1000)
        end_ms = int(end * 1000)
        self.audio = self.audio[start_ms:end_ms]
        self.start_time = 0.0
        self.duration = (end - start)

    def export(self, output_path: str):
        self.audio.export(output_path, format="wav")

    def to_dict(self):
        return {
            "file_path": self.file_path,
            "start_time": self.start_time,
            "duration": self.duration
        }

    @staticmethod
    def from_dict(data):
        return AudioClip(data["file_path"], data["start_time"], data["duration"])
