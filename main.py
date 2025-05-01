import sys
import os
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QListWidget, QListWidgetItem,
    QLabel, QStatusBar, QSizePolicy, QScrollArea
)

from core.project import Project
from core.timeline import Timeline
from core.track import Track
from ui.timeline_view import TimelineWidget
from ui.project_sync import ProjectSyncManager
from pydub import AudioSegment

class CompiledAudioStatusWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.status_label = QLabel("No compiled audio loaded.")
        self.layout.addWidget(self.status_label)
        self.setLayout(self.layout)

    def update_status(self, speaker_data):
        if not speaker_data:
            self.status_label.setText("No speaker selected.")
            return

        path = speaker_data.get("compiled")
        if not path or not os.path.exists(path):
            self.status_label.setText("Compiled audio not found.")
            return

        size = os.path.getsize(path) / (1024 ** 2)
        modified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(path)))
        self.status_label.setText(f"Compiled: {os.path.basename(path)} | Size: {size:.2f} MB | Last updated: {modified}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyAudioEditor")
        self.resize(1200, 800)

        # Project Sync Logic
        self.sync_manager = ProjectSyncManager()

        # === Speaker Sidebar ===
        self.speaker_list = QListWidget()
        self.speaker_list.setFixedWidth(140)
        self.speaker_list.itemClicked.connect(self.load_timeline_for_speaker)

        # === Timeline Display ===
        self.timeline_area = QWidget()
        self.timeline_layout = QVBoxLayout()
        self.timeline_area.setLayout(self.timeline_layout)

        self.timeline_widgets = {}
        self.audio_status_widget = CompiledAudioStatusWidget()

        # === Top bar ===
        topbar = QWidget()
        topbar_layout = QHBoxLayout()
        topbar.setLayout(topbar_layout)

        self.sync_label = QLabel("Sync Folder: (none)")
        btn_pick_folder = QPushButton("Set Sync Folder")
        btn_pick_folder.clicked.connect(self.pick_sync_folder)

        btn_reload = QPushButton("Reload Speakers")
        btn_reload.clicked.connect(self.reload_speakers)

        topbar_layout.addWidget(btn_pick_folder)
        topbar_layout.addWidget(btn_reload)
        topbar_layout.addStretch()
        topbar_layout.addWidget(self.sync_label)

        # === Layout ===
        main_split = QHBoxLayout()
        main_split.addWidget(self.speaker_list)
        main_split.addWidget(self.timeline_area)

        central = QWidget()
        central_layout = QVBoxLayout()
        central_layout.addWidget(topbar)
        central_layout.addLayout(main_split)
        central.setLayout(central_layout)
        self.setCentralWidget(central)
        self.setStatusBar(QStatusBar())

    def pick_sync_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Sync Folder")
        if folder:
            self.sync_manager.set_sync_folder(folder)
            self.sync_label.setText(f"Sync Folder: {os.path.basename(folder)}")
            self.reload_speakers()

    def reload_speakers(self):
        self.speaker_list.clear()
        self.timeline_widgets.clear()
        for i in reversed(range(self.timeline_layout.count())):
            widget = self.timeline_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        if not self.sync_manager.sync_path:
            self.statusBar().showMessage("No sync folder selected.", 5000)
            return

        self.sync_manager.reload_speakers()

        if not self.sync_manager.speakers:
            self.statusBar().showMessage("No speakers found in sync folder.", 5000)
            return

        for speaker in self.sync_manager.get_speaker_list():
            item = QListWidgetItem(f"🔊 {speaker['name']}")
            item.setData(1, speaker["name"])
            self.speaker_list.addItem(item)

        self.statusBar().showMessage(f"Loaded {len(self.sync_manager.speakers)} speakers.", 3000)

    def load_timeline_for_speaker(self, item):
        speaker_name = item.data(1)
        speaker_data = self.sync_manager.speakers.get(speaker_name)

        if speaker_name not in self.timeline_widgets:
            timeline = Timeline(speaker_name)
            for _ in range(8):
                timeline.add_track(Track())
            twidget = TimelineWidget(timeline)
            twidget.sync_path = speaker_data["path"]  # for export use
            self.timeline_widgets[speaker_name] = twidget

            # Export compiled.wav automatically
            def export_to_compiled():
                twidget.mix_project_audio()
                final = twidget.final_audio
                if final:
                    final.export(os.path.join(twidget.sync_path, "compiled.wav"), format="wav")

            export_to_compiled()

        else:
            twidget = self.timeline_widgets[speaker_name]

        for i in reversed(range(self.timeline_layout.count())):
            w = self.timeline_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        self.timeline_layout.addWidget(twidget)
        self.audio_status_widget.update_status(speaker_data)
        self.timeline_layout.addWidget(self.audio_status_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
