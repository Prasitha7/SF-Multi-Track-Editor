import os
from storage.session_io import save_session_to_file


def save_mixdown(final_audio, project_timeline, sync_path):
    if final_audio is None or len(final_audio) == 0:
        print("[ERROR] No audio to export.")
        return
    if not sync_path:
        print("No sync_path set — cannot save.")
        return
    try:
        save_path = os.path.join(sync_path, "compiled.wav")
        final_audio.export(save_path, format="wav")
        print(f"Auto-saved to {save_path}")
        save_session_to_file(project_timeline, sync_path)
        print(f"Session saved to {os.path.join(sync_path, 'session.json')}")
    except Exception as e:
        print(f"[ERROR] Failed to save mixdown or session: {e}")


def save_session_only(project_timeline, sync_path):
    if not sync_path:
        print("No sync_path set — cannot save session.")
        return
    try:
        save_session_to_file(project_timeline, sync_path)
        print(f"Session saved to {os.path.join(sync_path, 'session.json')}")
    except Exception as e:
        print(f"[ERROR] Failed to save session: {e}")
