import pytest
from PyQt6.QtWidgets import QApplication
import sys

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    app.quit()
