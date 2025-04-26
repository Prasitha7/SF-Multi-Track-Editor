import sys

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QScrollArea,
    QStatusBar, QApplication
)
from PyQt6.QtCore import Qt
from core.project import Project
from core.timeline import Timeline
from core.track import Track
from ui.timeline_view import TimelineWidget  # Unified ruler + tracks

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyAudioEditor")
        self.resize(1200, 800)

        # Set up backend
        self.project = Project("Untitled")
        self.timeline = Timeline("Main Timeline")
        for _ in range(8):
            self.timeline.add_track(Track())
        self.project.add_timeline(self.timeline)

        # Timeline widget (unified ruler + tracks)
        self.timeline_widget = TimelineWidget(self.timeline)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.timeline_widget)

        self.setCentralWidget(scroll)
        self.setStatusBar(QStatusBar())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
