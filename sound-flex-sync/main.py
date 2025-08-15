bl_info = {
    "name": "Speaker Sync Bridge",
    "author": "Your Name",
    "version": (1, 1),
    "blender": (4, 2, 0),
    "location": "Properties > Object Data > Speaker",
    "description": "Links Blender Speaker objects to an external audio mixer via a sync folder",
    "category": "Object",
}


import bpy
import os
import time
from bpy.app.handlers import persistent
from bpy.props import PointerProperty, BoolProperty, FloatProperty
from bpy.types import PropertyGroup, Operator, Panel

SYNC_FOLDER = "sf-sync"

# Data container for speaker sync info
class SpeakerAudioData(PropertyGroup):
    initialized: BoolProperty(default=False)
    last_sync_time: FloatProperty(default=0.0)  # UNIX timestamp of last sync

class OBJECT_OT_sync_speaker_audio(Operator):
    bl_idname = "speaker.sync_audio"
    bl_label = "Sync From Audio Mixer"

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'SPEAKER':
            self.report({'ERROR'}, "Active object is not a speaker.")
            return {'CANCELLED'}

        speaker = obj.data

        # ensure custom prop exists
        try:
            _ = speaker.speaker_audio_data
        except Exception as e:
            self.report({'ERROR'}, f"Failed to access speaker_audio_data: {e}")
            return {'CANCELLED'}

        compiled_audio_path = bpy.path.abspath(f"//{SYNC_FOLDER}/speakers/{obj.name}/compiled.wav")

        if not os.path.isfile(compiled_audio_path):
            self.report({'WARNING'}, f"No compiled.wav found for {obj.name}")
            return {'CANCELLED'}

        try:
            abs_target = os.path.abspath(compiled_audio_path)

            # Case A: same sound already assigned -> force a disk reload
            if speaker.sound and os.path.abspath(bpy.path.abspath(speaker.sound.filepath)) == abs_target:
                try:
                    speaker.sound.reload()  # re-read from disk
                    # bump a dummy value so Blender marks depsgraph dirty
                    speaker.volume = float(speaker.volume)
                    speaker.speaker_audio_data.last_sync_time = time.time()
                    self.report({'INFO'}, f"Reloaded (from disk): {compiled_audio_path}")
                    return {'FINISHED'}
                except Exception as e:
                    # fall through to hard reload path below
                    pass

            # Case B: clean any cached datablocks that point to this file
            to_remove = []
            for snd in bpy.data.sounds:
                if os.path.abspath(bpy.path.abspath(snd.filepath)) == abs_target:
                    to_remove.append(snd)

            # clear users before removing
            for snd in to_remove:
                if speaker.sound == snd:
                    speaker.sound = None
                snd.user_clear()
                try:
                    bpy.data.sounds.remove(snd)
                except RuntimeError:
                    # if still in use somewhere else, skip removal
                    pass

            # Load fresh without reusing cache
            sound = bpy.data.sounds.load(compiled_audio_path, check_existing=False)
            speaker.sound = sound

            # optional: set last_sync_time, but we don't use it to block reloads anymore
            speaker.speaker_audio_data.last_sync_time = time.time()

            self.report({'INFO'}, f"Loaded fresh: {compiled_audio_path}")
            return {'FINISHED'}

        except Exception as e:
            self.report({'ERROR'}, f"Failed to load/reload sound: {e}")
            return {'CANCELLED'}


class OBJECT_OT_request_audio_export(Operator):
    bl_idname = "speaker.request_export"
    bl_label = "Request Export from Audio Mixer"

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'SPEAKER':
            self.report({'ERROR'}, "Active object is not a speaker.")
            return {'CANCELLED'}

        blend_path = bpy.data.filepath
        if not blend_path:
            self.report({'ERROR'}, "Save the .blend file first.")
            return {'CANCELLED'}

        base_dir = os.path.dirname(blend_path)
        speaker_dir = os.path.join(base_dir, SYNC_FOLDER, "speakers", obj.name)
        os.makedirs(speaker_dir, exist_ok=True)

        trigger_file = os.path.join(speaker_dir, "export_request.json")
        try:
            with open(trigger_file, 'w') as f:
                f.write("{\"request\": \"export\"}")
            self.report({'INFO'}, f"Export request written to {trigger_file}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to write trigger: {e}")

        return {'FINISHED'}

class OBJECT_PT_speaker_audio_panel(Panel):
    bl_label = "External Audio Mixer"
    bl_idname = "OBJECT_PT_speaker_audio_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'SPEAKER'

    def draw(self, context):
        layout = self.layout
        layout.operator("speaker.sync_audio", icon='FILE_REFRESH')
        layout.operator("speaker.request_export", icon='EXPORT')

# Auto-create speaker sync folders and initialize property
@persistent
def auto_initialize_speaker_folders(scene):
    blend_path = bpy.data.filepath
    if not blend_path:
        return

    base_dir = os.path.dirname(blend_path)
    sync_dir = os.path.join(base_dir, SYNC_FOLDER, "speakers")
    os.makedirs(sync_dir, exist_ok=True)

    for obj in scene.objects:
        if obj.type == 'SPEAKER':
            speaker = obj.data
            try:
                _ = speaker.speaker_audio_data  # Trigger init
            except:
                continue
            data = speaker.speaker_audio_data
            if not data.initialized:
                speaker_dir = os.path.join(sync_dir, obj.name)
                os.makedirs(speaker_dir, exist_ok=True)
                data.initialized = True

classes = (
    SpeakerAudioData,
    OBJECT_OT_sync_speaker_audio,
    OBJECT_OT_request_audio_export,
    OBJECT_PT_speaker_audio_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Speaker.speaker_audio_data = PointerProperty(type=SpeakerAudioData)
    bpy.app.handlers.depsgraph_update_post.append(auto_initialize_speaker_folders)

def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(auto_initialize_speaker_folders)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Speaker.speaker_audio_data

if __name__ == "__main__":
    register()
