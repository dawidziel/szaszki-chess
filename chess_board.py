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

    def get_white_tinted_pixmap(self, symbol):
        if not hasattr(self, '_white_tinted'):
            self._white_tinted = {}
        if symbol not in self._white_tinted:
            orig = self.pieces[symbol].copy()
            painter = QPainter(orig)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(orig.rect(), Qt.GlobalColor.white)
            painter.end()
            self._white_tinted[symbol] = orig
        return self._white_tinted[symbol]

    def paintEvent(self, event):
        painter = QPainter(self)
        square_size = self.width() // 8

        # Draw the board with black and white squares
        for row in range(8):
            for col in range(8):
                color = Qt.GlobalColor.white if (row + col) % 2 == 0 else Qt.GlobalColor.black
                painter.fillRect(col * square_size, row * square_size, square_size, square_size, color)

        # Draw pieces with isolation for black pieces on black squares
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                file = chess.square_file(square)
                rank = 7 - chess.square_rank(square)
                x = file * square_size
                y = rank * square_size
                # Determine if the tile is black
                tile_black = ((rank + file) % 2 == 1)
                # If piece is black and tile is black, draw white isolation
                if not piece.color and tile_black:
                    tinted = self.get_white_tinted_pixmap(piece.symbol())
                    offsets = [(-1,0), (1,0), (0,-1), (0,1)]
                    for dx, dy in offsets:
                        painter.drawPixmap(x + dx, y + dy, square_size, square_size, tinted)
                painter.drawPixmap(x, y, square_size, square_size, self.pieces[piece.symbol()])

        # Highlight selected square and legal moves
        if self.selected_square is not None:
            self.highlight_square(painter, self.selected_square, QColor(255, 255, 0, 100))
            self.highlight_legal_moves(painter, self.selected_square)
