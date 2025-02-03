from PyQt6.QtWidgets import QWidget, QVBoxLayout, QComboBox, QCheckBox, QPushButton, QLabel, QSpinBox
from PyQt6.QtGui import QFont
from PyQt6.QtCore import pyqtSignal

class SettingsMenu(QWidget):
    settingsChanged = pyqtSignal(str, bool, int)  # (layout, fullscreen, clock_time)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setFixedWidth(300)

        # Layout selector
        self.resolution_label = QLabel("Select Layout:")
        self.resolution_label.setFont(QFont("Palatino", 14))
        self.layout.addWidget(self.resolution_label)

        self.resolution_combo = QComboBox()
        self.resolution_combo.setFont(QFont("Palatino", 12))
        self.resolutions = [
            "layout_1920x1440_horizontal",
            "layout_1920x1080_horizontal",
            "layout_1440x1920_vertical",
            "layout_2220x1080_horizontal",
            "layout_1080x2220_vertical"
        ]
        self.resolution_combo.addItems(self.resolutions)
        self.layout.addWidget(self.resolution_combo)

        # Clock time setting
        self.time_label = QLabel("Clock Time (minutes):")
        self.time_label.setFont(QFont("Palatino", 14))
        self.layout.addWidget(self.time_label)

        self.time_spinner = QSpinBox()
        self.time_spinner.setRange(1, 60)
        self.time_spinner.setValue(5)
        self.time_spinner.setFont(QFont("Palatino", 12))
        self.layout.addWidget(self.time_spinner)

        # Fullscreen toggle
        self.fullscreen_check = QCheckBox("Fullscreen Mode")
        self.fullscreen_check.setFont(QFont("Palatino", 14))
        self.layout.addWidget(self.fullscreen_check)

        # Apply button
        self.apply_btn = QPushButton("Apply Settings")
        self.apply_btn.setFont(QFont("Palatino", 14))
        self.apply_btn.clicked.connect(self.apply_settings)
        self.layout.addWidget(self.apply_btn)

        self.setLayout(self.layout)
        self.hide()

    def apply_settings(self):
        layout_choice = self.resolution_combo.currentText()
        fullscreen = self.fullscreen_check.isChecked()
        clock_time = self.time_spinner.value() * 60  # Convert minutes to seconds
        self.settingsChanged.emit(layout_choice, fullscreen, clock_time)
        self.hide()
