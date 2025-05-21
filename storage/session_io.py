#storage\session_io.py
import os
import json
from core.timeline import Timeline
from core.track import Track
from core.audio_clip import AudioClip


def save_session_to_file(timeline: Timeline, speaker_path: str):
    session_data = {
        "tracks": []
    }

    sync_root = os.path.abspath(os.path.join(speaker_path, os.pardir, os.pardir))
    asset_folder = os.path.join(sync_root, "assets")
    os.makedirs(asset_folder, exist_ok=True)

    for track in timeline.tracks:
        track_data = {"clips": []}
        for clip in track.clips:
            source_path = getattr(clip, "source_path", None) or getattr(clip, "path", None)
            if not source_path:
                continue
            source_path = os.path.abspath(source_path)
            filename = os.path.basename(source_path)
            asset_path = os.path.join(asset_folder, filename)

            # Copy audio file if not already in assets
            if not os.path.exists(asset_path):
                try:
                    with open(source_path, 'rb') as src_file, open(asset_path, 'wb') as dst_file:
                        dst_file.write(src_file.read())
                except Exception as e:
                    print(f"[ERROR] Failed to copy asset: {e}")

            rel_path = os.path.relpath(asset_path, speaker_path)

            clip_data = {
                "file": rel_path.replace('\\', '/'),
                "start_time": clip.start_time,
                "trim_start": clip.trim_start,
                "trim_end": clip.trim_end
            }
            track_data["clips"].append(clip_data)
        session_data["tracks"].append(track_data)

    session_path = os.path.join(speaker_path, "session.json")
    with open(session_path, 'w') as f:
        json.dump(session_data, f, indent=2)


def load_session_from_file(session_path: str) -> Timeline:
    if not os.path.exists(session_path):
        raise FileNotFoundError(f"Session file not found: {session_path}")

    with open(session_path, 'r') as f:
        data = json.load(f)

    speaker_name = os.path.basename(os.path.dirname(session_path))
    timeline = Timeline(speaker_name)

    for track_data in data.get("tracks", []):
        track = Track()
        for clip_data in track_data.get("clips", []):
            try:
                file_path = os.path.join(os.path.dirname(session_path), clip_data["file"])
                file_path = os.path.abspath(file_path)
                clip = AudioClip(
                    file_path,
                    start_time=clip_data.get("start_time", 0.0),
                    trim_start=clip_data.get("trim_start", 0.0),
                    trim_end=clip_data.get("trim_end", None)
                )
                clip.source_path = file_path
                track.add_clip(clip)
            except Exception as e:
                print(f"[ERROR] Failed to load clip {clip_data['file']}: {e}")
        timeline.add_track(track)

    return timeline
