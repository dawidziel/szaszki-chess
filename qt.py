import sys
import chess
import chess.pgn
import time
import io
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox, QMenuBar
from PyQt6.QtGui import QPixmap, QPainter, QColor, QAction
from PyQt6.QtCore import Qt, QTimer
from lichess_handler import LichessHandler
from config import lichess_token

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class ChessBoardWidget(QWidget):
    def __init__(self, board, main_window, parent=None):
        super().__init__(parent)
        self.board = board
        self.main_window = main_window
        self.selected_square = None
        self.load_pieces()
        self.setEnabled(True)

    def load_pieces(self):
        self.pieces = {}
        piece_names = {
            'p': 'pawn', 'r': 'rook', 'n': 'knight', 'b': 'bishop', 'q': 'queen', 'k': 'king',
            'P': 'pawn', 'R': 'rook', 'N': 'knight', 'B': 'bishop', 'Q': 'queen', 'K': 'king'
        }
        for piece, name in piece_names.items():
            color = 'white' if piece.isupper() else 'black'
            self.pieces[piece] = QPixmap(f"pieces/{color}-{name}.png")

    def paintEvent(self, event):
        painter = QPainter(self)
        square_size = self.width() // 8

        # Draw the board
        for row in range(8):
            for col in range(8):
                color = QColor(240, 217, 181) if (row + col) % 2 == 0 else QColor(181, 136, 99)
                painter.fillRect(col * square_size, row * square_size, square_size, square_size, color)

        # Draw the pieces
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

    def highlight_square(self, painter, square, color):
        file = chess.square_file(square)
        rank = 7 - chess.square_rank(square)
        square_size = self.width() // 8
        painter.fillRect(file * square_size, rank * square_size, square_size, square_size, color)

    def highlight_legal_moves(self, painter, square):
        for move in self.board.legal_moves:
            if move.from_square == square:
                self.highlight_square(painter, move.to_square, QColor(0, 255, 0, 100))

    def mousePressEvent(self, event):
        if not self.isEnabled():
            return

        square_size = self.width() // 8
        file = int(event.position().x()) // square_size
        rank = 7 - (int(event.position().y()) // square_size)
        square = chess.square(file, rank)

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = square
        else:
            move = chess.Move(self.selected_square, square)
            if move in self.board.legal_moves and (not self.main_window.allowed_moves or move in self.main_window.allowed_moves):
                self.board.push(move)
                logging.debug(f"Player move: {move.uci()}")
                self.main_window.current_move_index += 1
                self.main_window.switch_turn()
                self.main_window.check_game_result()
                if self.main_window.playing_vs_bot:
                    self.main_window.send_move_to_bot(move)
            self.selected_square = None
        self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess")
        self.setFixedSize(800, 800)  # Set the default window size to 800x800

        self.board = chess.Board()
        self.board_widget = ChessBoardWidget(self.board, self)

        self.lichess_handler = LichessHandler(lichess_token)
        self.playing_vs_bot = False

        self.white_time = 0
        self.black_time = 0
        self.current_turn = chess.WHITE
        self.timer = QTimer(self)

        self.allowed_moves = None
        self.current_move_index = 0
        self.solution_moves = []  # Initialize solution_moves

        self.print_lichess_handler_attributes()

        self.init_ui()

    def print_lichess_handler_attributes(self):
        print(f"LichessHandler Attributes:")
        print(f"Token Session: {self.lichess_handler.session}")
        print(f"Client: {self.lichess_handler.client}")
        print(f"Game ID: {self.lichess_handler.game_id}")
        print(f"Stream: {self.lichess_handler.stream}")

    def init_ui(self):
        layout = QVBoxLayout()

        # Add bots label at the top
        self.bots_label = QLabel("Online Bots:")
        self.bots_label.setStyleSheet("background-color: white; border: 1px solid black;")
        self.bots_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.bots_label.setFixedHeight(100)
        layout.addWidget(self.bots_label)

        new_game_button = QPushButton("New Game")
        new_game_button.clicked.connect(self.new_game)
        layout.addWidget(new_game_button)

        play_vs_bot_button = QPushButton("Play vs Bot")
        play_vs_bot_button.clicked.connect(self.play_vs_bot)
        layout.addWidget(play_vs_bot_button)

        get_online_bots_button = QPushButton("Get Online Bots")
        get_online_bots_button.clicked.connect(self.get_online_bots)
        layout.addWidget(get_online_bots_button)

        undo_move_button = QPushButton("Undo Move")
        undo_move_button.clicked.connect(self.undo_move)
        layout.addWidget(undo_move_button)

        self.white_timer_label = QLabel("White: 05:00")
        self.white_timer_label.setStyleSheet("background-color: white; border: 1px solid black;")
        self.white_timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.white_timer_label)

        self.black_timer_label = QLabel("Black: 05:00")
        self.black_timer_label.setStyleSheet("background-color: black; color: white; border: 1px solid black;")
        self.black_timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.black_timer_label)

        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.close)
        layout.addWidget(quit_button)

        side_widget = QWidget()
        side_widget.setLayout(layout)
        side_widget.setFixedWidth(160)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.board_widget)
        main_layout.addWidget(side_widget)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Create menu bar
        menu_bar = self.menuBar()
        puzzles_menu = menu_bar.addMenu("Puzzles")

        # Add action for today's puzzles
        todays_puzzles_action = QAction("Today's Puzzles", self)
        todays_puzzles_action.triggered.connect(self.show_todays_puzzles)
        puzzles_menu.addAction(todays_puzzles_action)

        # Add navigation buttons
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.prev_move)
        layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_move)
        layout.addWidget(self.next_button)

    def new_game(self):
        self.board.reset()
        self.playing_vs_bot = False
        self.white_time = 300  # 5 minutes
        self.black_time = 300  # 5 minutes
        self.current_turn = chess.WHITE
        self.timer.start(1000)
        self.board_widget.setEnabled(True)
        self.board_widget.update()

    def play_vs_bot(self):
        bot_username = "stockfish"  # Example bot username
        game_id = self.lichess_handler.create_bot_game(bot_username, time_control='5+0', rated=False)
        if game_id:
            self.board.reset()
            self.playing_vs_bot = True
            self.white_time = 300  # 5 minutes
            self.black_time = 300  # 5 minutes
            self.current_turn = chess.WHITE
            self.timer.start(1000)
            self.board_widget.setEnabled(True)
            self.allowed_moves = None  # Allow all legal moves in bot game
            self.board_widget.update()
            logging.debug(f"Started bot game with ID: {game_id}")
        else:
            self.show_result("Failed to create bot game.")

    def send_move_to_bot(self, move):
        if self.lichess_handler.make_move_bot(move.uci()):
            logging.debug(f"Sent move to bot: {move.uci()}")
            self.update_bot_move()
        else:
            logging.error(f"Failed to send move to bot: {move.uci()}")

    def update_bot_move(self):
        game_state = self.lichess_handler.get_game_state()
        if game_state:
            moves = game_state['moves'].split()
            if len(moves) % 2 == 1:  # Bot's turn
                bot_move = moves[-1]
                self.board.push_uci(bot_move)
                logging.debug(f"Bot move: {bot_move}")
                self.switch_turn()
                self.board_widget.update()
                self.check_game_result()

    def get_online_bots(self):
        bots = self.lichess_handler.get_online_bots()
        self.bots_label.setText("Online Bots:\n" + "\n".join(bots[:5]))  # Show first 5 bots
        logging.debug(f"Online bots: {bots}")

    def update_timer(self):
        if self.current_turn == chess.WHITE:
            self.white_time -= 1
            if self.white_time <= 0:
                self.timer.stop()
                self.white_timer_label.setText("White: 00:00")
                self.show_result("Black wins on time!")
                self.board_widget.setEnabled(False)
                return
        else:
            self.black_time -= 1
            if self.black_time <= 0:
                self.timer.stop()
                self.black_timer_label.setText("Black: 00:00")
                self.show_result("White wins on time!")
                self.board_widget.setEnabled(False)
                return

        self.white_timer_label.setText(f"White: {self.format_time(self.white_time)}")
        self.black_timer_label.setText(f"Black: {self.format_time(self.black_time)}")

    def switch_turn(self):
        self.current_turn = not self.current_turn

    def format_time(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02}:{seconds:02}"

    def undo_move(self):
        if self.board.move_stack:
            self.board.pop()
        self.board_widget.update()

    def check_game_result(self):
        if self.board.is_checkmate():
            winner = "White" if self.board.turn == chess.BLACK else "Black"
            self.show_result(f"{winner} wins by checkmate!")
            self.board_widget.setEnabled(False)
        elif self.board.is_stalemate() or self.board.is_insufficient_material() or self.board.is_seventyfive_moves() or self.board.is_fivefold_repetition() or self.board.is_variant_draw():
            self.show_result("Draw!")
            self.board_widget.setEnabled(False)

    def show_result(self, message):
        msg_box = QMessageBox()
        msg_box.setText(message)
        msg_box.exec()

    def show_todays_puzzles(self):
        puzzle = self.lichess_handler.fetch_daily_puzzle()
        pgn = puzzle['game']['pgn']
        game = chess.pgn.read_game(io.StringIO(pgn))
        self.board = game.end().board()
        self.board_widget.board = self.board
        self.solution_moves = [chess.Move.from_uci(move) for move in puzzle['puzzle']['solution']]
        self.current_move_index = 0
        self.allowed_moves = [self.solution_moves[self.current_move_index]]
        self.board_widget.update()
        self.show_result(f"Today's Puzzle:\n{puzzle['puzzle']['id']}")

    def prev_move(self):
        if self.current_move_index > 0:
            self.current_move_index -= 1
            self.board.pop()
            self.allowed_moves = [self.solution_moves[self.current_move_index]]
            self.board_widget.update()

    def next_move(self):
        if self.current_move_index < len(self.solution_moves):
            move = self.solution_moves[self.current_move_index]
            self.board.push(move)
            self.current_move_index += 1
            if self.current_move_index < len(self.solution_moves):
                self.allowed_moves = [self.solution_moves[self.current_move_index]]
            else:
                self.allowed_moves = None
            self.board_widget.update()

    def highlight_correct_move(self):
        pass  # No longer highlighting the correct move

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())