import sys
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from custom_widgets import ClockWidget

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app

@pytest.fixture
def clock_widget(qapp):
    widget = ClockWidget(is_white=True)
    yield widget
    widget.deleteLater()

def test_clock_widget_init(clock_widget):
    assert clock_widget.seconds_remaining == 300
    assert clock_widget.is_white is True
    assert clock_widget.time_str == "05:00"

def test_clock_widget_reset(clock_widget):
    clock_widget.reset(60)  # Reset to 1 minute
    assert clock_widget.seconds_remaining == 60
    assert clock_widget.time_str == "01:00"

def test_clock_widget_start_stop(clock_widget, qtbot):
    clock_widget.start()
    assert clock_widget._active is True

    # Wait for 2 seconds
    with qtbot.waitSignal(clock_widget.timer.timeout, timeout=2500):
        pass

    assert clock_widget.seconds_remaining < 300

    clock_widget.stop()
    assert clock_widget._active is False
    initial_seconds = clock_widget.seconds_remaining

    # Wait another second to ensure time is stopped
    qtbot.wait(1000)
    assert clock_widget.seconds_remaining == initial_seconds

def test_clock_widget_time_expired_signal(clock_widget, qtbot):
    clock_widget.reset(1)  # Set to 1 second

    with qtbot.waitSignal(clock_widget.time_expired, timeout=2000):
        clock_widget.start()

    assert clock_widget.seconds_remaining == 0

def test_clock_widget_time_format(clock_widget):
    test_times = [
        (300, "05:00"),
        (60, "01:00"),
        (45, "00:45"),
        (0, "00:00"),
        (599, "09:59"),
    ]

    for seconds, expected in test_times:
        clock_widget.reset(seconds)
        assert clock_widget.time_str == expected
