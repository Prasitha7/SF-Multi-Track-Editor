#core\audio_clip.py
from pydub import AudioSegment


class AudioClip:
    def __init__(
        self,
        file_path: str,
        start_time: float = 0.0,
        duration: float = None,
        trim_start: float = 0.0,
        trim_end: float = 0.0,
    ):
        self.file_path = file_path
        self.source_path = file_path
        self.start_time = start_time
        self.audio = AudioSegment.from_file(file_path)
        self.trim_start = trim_start
        self.trim_end = trim_end
        total_length = len(self.audio) / 1000.0
        self.duration = (
            duration if duration is not None else total_length - trim_start - trim_end
        )

    def trim(self, start: float, end: float):
        total_length = len(self.audio) / 1000.0
        start_ms = int(start * 1000)
        end_ms = int(end * 1000)
        self.audio = self.audio[start_ms:end_ms]
        self.start_time = 0.0
        self.trim_start = start
        self.trim_end = total_length - end
        self.duration = end - start

    def export(self, output_path: str):
        self.audio.export(output_path, format="wav")

    def to_dict(self):
        return {
            "file_path": self.file_path,
            "start_time": self.start_time,
            "duration": self.duration,
            "trim_start": self.trim_start,
            "trim_end": self.trim_end,
        }

    @staticmethod
    def from_dict(data):
        return AudioClip(
            data["file_path"],
            data.get("start_time", 0.0),
            data.get("duration"),
            data.get("trim_start", 0.0),
            data.get("trim_end", 0.0),
        )

