import sys
import os
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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

    def tearDown(self):
        self.menu.hide()

    def test_initial_values(self):
        self.assertEqual(self.menu.time_spinner.value(), 5)
        self.assertFalse(self.menu.fullscreen_check.isChecked())

    def test_settings_change_signal(self):
        signals_received = []
        def on_settings_changed(resolution, fullscreen, clock_time):
            signals_received.append((resolution, fullscreen, clock_time))
        
        self.menu.settingsChanged.connect(on_settings_changed)
        self.menu.resolution_combo.setCurrentText("layout_1920x1080_horizontal")
        self.menu.fullscreen_check.setChecked(True)
        self.menu.time_spinner.setValue(10)
        QTest.mouseClick(self.menu.apply_btn, Qt.MouseButton.LeftButton)
        
        self.assertEqual(len(signals_received), 1)
        self.assertEqual(signals_received[0], ("layout_1920x1080_horizontal", True, 600))

    def test_layout_options(self):
        expected_layouts = [
            "layout_1920x1440_horizontal",
            "layout_1920x1080_horizontal",
            "layout_1440x1920_vertical",
            "layout_2220x1080_horizontal",
            "layout_1080x2220_vertical"
        ]
        assert self.menu.resolution_combo.count() == len(expected_layouts)
        for i, text in enumerate(expected_layouts):
            assert self.menu.resolution_combo.itemText(i) == text

    def test_clock_time_limits(self):
        # Test minimum value
        self.menu.time_spinner.setValue(1)
        assert self.menu.time_spinner.value() == 1
        
        # Test maximum value
        self.menu.time_spinner.setValue(60)
        assert self.menu.time_spinner.value() == 60
        
        # Test overflow
        self.menu.time_spinner.setValue(100)
        assert self.menu.time_spinner.value() == 60

    def test_ui_elements_present(self):
        assert self.menu.resolution_combo is not None
        assert self.menu.fullscreen_check is not None
        assert self.menu.time_spinner is not None
        assert self.menu.apply_btn is not None

    def test_default_values(self):
        assert self.menu.resolution_combo.currentIndex() == 0
        assert self.menu.fullscreen_check.isChecked() is False
        assert self.menu.time_spinner.value() == 5
        assert self.menu.time_spinner.minimum() == 1
        assert self.menu.time_spinner.maximum() == 60

    def test_fullscreen_toggle(self):
        initial_state = self.menu.fullscreen_check.isChecked()
        
        # Toggle checkbox using QTest.mouseClick
        QTest.mouseClick(self.menu.fullscreen_check, Qt.MouseButton.LeftButton)
        self.assertNotEqual(self.menu.fullscreen_check.isChecked(), initial_state)
        
        # Toggle back
        QTest.mouseClick(self.menu.fullscreen_check, Qt.MouseButton.LeftButton)
        self.assertEqual(self.menu.fullscreen_check.isChecked(), initial_state)

    def test_ui_layout(self):
        self.menu.resize(400, 300)
        self.menu.show()
        QTest.qWaitForWindowExposed(self.menu)
        # Verify widget positions and sizes

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()
