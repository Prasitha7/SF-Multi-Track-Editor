#ui\project_sync.py
import os
import json

class ProjectSyncManager:
    def __init__(self):
        self.sync_path = None
        self.speakers = {}

    def set_sync_folder(self, path):
        self.sync_path = path
        self.reload_speakers()

    def reload_speakers(self):
        self.speakers = {}
        if not self.sync_path:
            return

        speakers_dir = os.path.join(self.sync_path, "speakers")
        if not os.path.exists(speakers_dir):
            return

        for name in os.listdir(speakers_dir):
            speaker_path = os.path.join(speakers_dir, name)
            if os.path.isdir(speaker_path):
                compiled = os.path.join(speaker_path, "compiled.wav")
                request = os.path.join(speaker_path, "export_request.json")
                self.speakers[name] = {
                    "name": name,
                    "path": speaker_path,
                    "compiled": compiled,
                    "request_file": request,
                    "needs_export": os.path.exists(request),
                    "has_audio": os.path.exists(compiled),
                }

    def get_speaker_list(self):
        return list(self.speakers.values())
