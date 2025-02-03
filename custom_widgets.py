from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPainter, QPen, QFont, QColor
from PyQt6.QtCore import Qt, QRect, QTimer, pyqtSignal
import time

class ClockWidget(QLabel):
    time_expired = pyqtSignal()

    def __init__(self, is_white=True, parent=None):
        super().__init__(parent)
        self.is_white = is_white
        self.seconds_remaining = 300  # 5 minutes
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.setFixedSize(250, 120)
        self.setFont(QFont("Palatino", 32))
        self.time_format = "mm:ss"
        self._active = False
        self.last_update = None

    def start(self):
        self._active = True
        self.last_update = time.time()
        self.timer.start(100)  # Update more frequently for accuracy

    def stop(self):
        self._active = False
        self.timer.stop()
        self.last_update = None

    def reset(self, seconds=300):
        self.seconds_remaining = seconds
        self.update()

    def update_time(self):
        if self._active and self.seconds_remaining > 0:
            current_time = time.time()
            if self.last_update:
                elapsed = current_time - self.last_update
                self.seconds_remaining = max(0, self.seconds_remaining - elapsed)
            self.last_update = current_time
            self.update()

            if self.seconds_remaining <= 0:
                self.stop()
                self.time_expired.emit()

    @property
    def time_str(self):
        if self.seconds_remaining <= 0:
            return "00:00"
        minutes = int(self.seconds_remaining // 60)
        seconds = int(self.seconds_remaining % 60)
        return f"{minutes:02d}:{seconds:02d}"  # Changed format to always show 2 digits

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background
        bg_color = Qt.GlobalColor.white if self.is_white else Qt.GlobalColor.black
        painter.fillRect(self.rect(), bg_color)

        # Draw border
        border_color = Qt.GlobalColor.black if self.is_white else Qt.GlobalColor.white
        painter.setPen(QPen(border_color, 2))
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))

        # Set text color
        text_color = Qt.GlobalColor.black if self.is_white else Qt.GlobalColor.white
        painter.setPen(text_color)

        # Draw time
        font = QFont("Palatino", 32)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.time_str)
