import sys
import unittest
import chess
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtTest import QTest

class TestChessBoard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)

    def setUp(self):
        from qt import ChessBoardWidget
        self.board = chess.Board()
        
        class MockMainWindow:
            def __init__(self):
                self.solving_puzzle = False
                self.allowed_moves = None
                self.move_list = []
                self.game_states = []
                self.game_moves = []
                self.current_move_index = 0
            
            def switch_turn(self):
                # Stub method to simulate switching turn.
                pass
        
        self.main_window = MockMainWindow()
        self.widget = ChessBoardWidget(self.board, self.main_window)
        self.widget.show()

    def test_square_selection(self):
        square_size = self.widget.width() // 8
        QTest.mouseClick(self.widget, Qt.MouseButton.LeftButton, 
                        pos=QPoint(4 * square_size, 6 * square_size))
        self.assertEqual(self.widget.selected_square, chess.E2)

    def test_legal_move(self):
        # Move e2 to e4
        square_size = self.widget.width() // 8
        QTest.mouseClick(self.widget, Qt.MouseButton.LeftButton, pos=QPoint(4 * square_size, 6 * square_size))
        QTest.mouseClick(self.widget, Qt.MouseButton.LeftButton, pos=QPoint(4 * square_size, 4 * square_size))
        self.assertEqual(self.board.piece_at(chess.E4).symbol(), 'P')

    def test_illegal_move(self):
        # Try to move e2 to e5
        square_size = self.widget.width() // 8
        initial_position = self.board.fen()
        QTest.mouseClick(self.widget, Qt.MouseButton.LeftButton, pos=QPoint(4 * square_size, 6 * square_size))
        QTest.mouseClick(self.widget, Qt.MouseButton.LeftButton, pos=QPoint(4 * square_size, 3 * square_size))
        self.assertEqual(self.board.fen(), initial_position)

    def tearDown(self):
        self.board.reset()
        self.widget.close()

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()
