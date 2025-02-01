import sys
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from settings_menu import SettingsMenu

class TestSettingsMenu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    def setUp(self):
        self.menu = SettingsMenu()
        self.menu.show()

    def test_initial_values(self):
        self.assertEqual(self.menu.time_spinner.value(), 5)
        self.assertFalse(self.menu.fullscreen_check.isChecked())

    def test_settings_change_signal(self):
        signals_received = []
        def on_settings_changed(resolution, fullscreen, clock_time):
            signals_received.append((resolution, fullscreen, clock_time))

        self.menu.settingsChanged.connect(on_settings_changed)
        self.menu.resolution_combo.setCurrentText("1920x1080")
        self.menu.fullscreen_check.setChecked(True)
        self.menu.time_spinner.setValue(10)
        QTest.mouseClick(self.menu.apply_btn, Qt.MouseButton.LeftButton)

        self.assertEqual(len(signals_received), 1)
        self.assertEqual(signals_received[0], ("1920x1080", True, 600))

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()
