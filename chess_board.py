from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QPixmap
from PyQt6.QtCore import Qt
import chess
import os

class ChessBoardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.board = chess.Board()
        self.selected_square = None
        self.load_pieces()
        self.setEnabled(True)

    # ...existing initialization code...

    def paintEvent(self, event):
        painter = QPainter(self)
        square_size = self.width() // 8

        # Draw the board with black and white squares
        for row in range(8):
            for col in range(8):
                color = Qt.GlobalColor.white if (row + col) % 2 == 0 else Qt.GlobalColor.black
                painter.fillRect(col * square_size, row * square_size, square_size, square_size, color)

        # Draw pieces
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                x = chess.square_file(square) * square_size
                y = (7 - chess.square_rank(square)) * square_size
                painter.drawPixmap(x, y, square_size, square_size, self.pieces[piece.symbol()])

        # Highlight selected square and legal moves
        if self.selected_square is not None:
            self.highlight_square(painter, self.selected_square, QColor(255, 255, 0, 100))
            self.highlight_legal_moves(painter, self.selected_square)
