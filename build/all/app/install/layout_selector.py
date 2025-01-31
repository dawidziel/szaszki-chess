from PyQt6.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QPushButton, QLabel
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class LayoutSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Layout Profile")
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Header
        header = QLabel("Select your screen resolution:")
        header.setFont(QFont("Palatino", 14))
        layout.addWidget(header)

        # Layout options with clear descriptions
        self.layouts = {
            "Desktop (1920x1440)": "layout_1920x1440_horizontal",
            "Widescreen (1920x1080)": "layout_1920x1080_horizontal",
            "Tablet/Portrait (1440x1920)": "layout_1440x1920_vertical"
        }

        self.radio_buttons = {}
        for label, layout_id in self.layouts.items():
            rb = QRadioButton(label)
            rb.setFont(QFont("Palatino", 12))
            self.radio_buttons[layout_id] = rb
            layout.addWidget(rb)

        # Default selection
        self.radio_buttons["layout_1920x1440_horizontal"].setChecked(True)

        # Confirm button
        confirm_btn = QPushButton("Start Game")
        confirm_btn.setFont(QFont("Palatino", 12))
        confirm_btn.clicked.connect(self.accept)
        layout.addWidget(confirm_btn)

        self.setLayout(layout)

    def get_selected_layout(self):
        for layout_id, button in self.radio_buttons.items():
            if button.isChecked():
                return layout_id
        return "layout_1920x1440_horizontal"
