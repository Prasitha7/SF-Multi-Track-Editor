#ui\properties_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton

class PropertiesPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(200)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.fields = {}
        for label in ["Start Offset (s)", "End Offset (s)", "Position (s)", "Duration (s)"]:
            l = QLabel(label)
            e = QLineEdit()
            e.setReadOnly(label == "Duration (s)")
            self.layout.addWidget(l)
            self.layout.addWidget(e)
            self.fields[label] = e

        self.save_button = QPushButton("Apply Changes")
        self.layout.addWidget(self.save_button)

    def update_fields(self, props):
        self.fields["Start Offset (s)"].setText(str(props["start_time_offset"]))
        self.fields["End Offset (s)"].setText(str(props["end_time_offset"]))
        self.fields["Position (s)"].setText(str(props["position_sec"]))
        self.fields["Duration (s)"].setText(str(props["duration_sec"]))

    def get_inputs(self):
        return {
            "start_offset": float(self.fields["Start Offset (s)"].text()),
            "end_offset": float(self.fields["End Offset (s)"].text()),
            "position_sec": float(self.fields["Position (s)"].text()),
        }
