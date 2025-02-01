import sys
import unittest
import chess
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

class TestChessBoard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    def setUp(self):
        from chess_board import ChessBoardWidget
        self.board = chess.Board()
        self.main_window = None  # Mock main window
        self.widget = ChessBoardWidget(parent=None)  # Initialize without board
        self.widget.board = self.board  # Set board after initialization
        self.widget.show()

    def test_square_selection(self):
        # Click on e2 pawn
        square_size = self.widget.width() // 8
        QTest.mouseClick(self.widget, Qt.MouseButton.LeftButton, pos=(4 * square_size, 6 * square_size))
        self.assertEqual(self.widget.selected_square, chess.E2)

    def test_legal_move(self):
        # Move e2 to e4
        square_size = self.widget.width() // 8
        QTest.mouseClick(self.widget, Qt.MouseButton.LeftButton, pos=(4 * square_size, 6 * square_size))
        QTest.mouseClick(self.widget, Qt.MouseButton.LeftButton, pos=(4 * square_size, 4 * square_size))
        self.assertEqual(self.board.piece_at(chess.E4).symbol(), 'P')

    def test_illegal_move(self):
        # Try to move e2 to e5
        square_size = self.widget.width() // 8
        initial_position = self.board.fen()
        QTest.mouseClick(self.widget, Qt.MouseButton.LeftButton, pos=(4 * square_size, 6 * square_size))
        QTest.mouseClick(self.widget, Qt.MouseButton.LeftButton, pos=(4 * square_size, 3 * square_size))
        self.assertEqual(self.board.fen(), initial_position)

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()
