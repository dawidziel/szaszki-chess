import sys
import chess
import chess.pgn
import time
import os
import io
import logging
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QMessageBox, QLabel  # Added QLabel
from PyQt6.QtGui import QPixmap, QPainter, QColor, QScreen, QGuiApplication, QFont
from PyQt6.QtCore import QUrl, QTimer, Qt  # Added QTimer and Qt
from PyQt6.QtQml import QQmlApplicationEngine
from lichess_handler import LichessHandler
from config import lichess_token
from layout_manager import LayoutManager
from custom_widgets import ClockWidget
from layout_selector import LayoutSelector
from settings_menu import SettingsMenu

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
        import os
        self.pieces = {}
        piece_names = {
            'p': 'pawn', 'r': 'rook', 'n': 'knight', 'b': 'bishop', 'q': 'queen', 'k': 'king',
            'P': 'pawn', 'R': 'rook', 'N': 'knight', 'B': 'bishop', 'Q': 'queen', 'K': 'king'
        }
        # Get the absolute path to the pieces directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        pieces_dir = os.path.join(current_dir, "pieces")

        for piece, name in piece_names.items():
            color = 'white' if piece.isupper() else 'black'
            piece_path = os.path.join(pieces_dir, f"{color}-{name}.png")
            pixmap = QPixmap(piece_path)
            if pixmap.isNull():
                print(f"Failed to load piece image: {piece_path}")
            self.pieces[piece] = pixmap

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
                # NEW: Track moves for navigation if not in puzzle mode
                if not self.main_window.solving_puzzle:
                    self.main_window.game_moves.append(move)
                    self.main_window.current_move_pointer = len(self.main_window.game_moves)
                    # NEW: Save board state
                    self.main_window.game_states.append(self.board.fen())
                self.main_window.current_move_index += 1
                self.main_window.switch_turn()
                self.main_window.check_game_result()
                # Only send moves to bot if we're in a bot game and not solving puzzles
                if self.main_window.playing_vs_bot and not self.main_window.solving_puzzle:
                    self.main_window.send_move_to_bot(move)
            self.selected_square = None
        self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess")

        # Show layout selector
        self.selected_layout = self.show_layout_selector()

        # Initialize components
        self.board = chess.Board()
        self.board_widget = ChessBoardWidget(self.board, self)
        self.lichess_handler = LichessHandler(lichess_token)
        self.init_ui_elements()
        self.init_game_state()

        self.layout_manager = LayoutManager(self)
        # Auto-detect screen resolution and apply scalable layout
        self.auto_apply_layout()

        # Setup orientation monitoring
        self.orientation_timer = QTimer()
        self.orientation_timer.timeout.connect(self.check_orientation)
        self.orientation_timer.start(1000)  # Check every second
        self.current_orientation = None

        self.settings_menu = SettingsMenu(self)
        self.settings_menu.settingsChanged.connect(self.apply_settings)
        self.is_fullscreen = False

    def auto_apply_layout(self):
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        if screen:
            geometry = screen.geometry()
            orientation = "vertical" if geometry.height() > geometry.width() else "horizontal"
            profile = f"layout_{geometry.width()}x{geometry.height()}_{orientation}"
            self.layout_manager.apply_layout(profile)

    def init_game_state(self):
        self.playing_vs_bot = False
        self.manual_game = False
        self.white_time = 300  # 5 minutes
        self.black_time = 300
        self.current_turn = chess.WHITE
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_clock)
        self.move_list = []
        self.solving_puzzle = False  # Add this line
        self.allowed_moves = None  # Initialize allowed_moves
        self.current_move_index = 0  # Add this for puzzle moves tracking
        self.clock_time = 300  # Default 5 minutes
        # NEW: Initialize game move tracking for full game navigation
        self.game_moves = []          # List of all moves in the game
        self.current_move_pointer = 0 # Pointer for current move position
        self.game_states = [self.board.fen()]  # NEW: Track board states

    def update_clock(self):
        if self.manual_game:
            if self.current_turn == chess.WHITE:
                self.white_time = max(0, self.white_time - 1)
                if self.white_time <= 0:
                    self.game_over("Black wins on time!")
                self.white_clock.seconds_remaining = self.white_time
            else:
                self.black_time = max(0, self.black_time - 1)
                if self.black_time <= 0:
                    self.game_over("White wins on time!")
                self.black_clock.seconds_remaining = self.black_time

            self.white_clock.update()
            self.black_clock.update()

    def show_layout_selector(self):
        selector = LayoutSelector(self)
        if selector.exec():
            return selector.get_selected_layout()
        return "layout_1920x1440_horizontal"

    def init_ui_elements(self):
        # Create clocks
        self.white_clock = ClockWidget(is_white=True)
        self.black_clock = ClockWidget(is_white=False)

        # Create navigation buttons with size policy for responsiveness.
        self.prev_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        for btn in [self.prev_button, self.next_button]:
            btn.setFont(QFont("Palatino", 32))
            btn.setFixedHeight(80)  # Keep height fixed if necessary
            btn.setSizePolicy(btn.sizePolicy().horizontalPolicy(), btn.sizePolicy().verticalPolicy())
            btn.setStyleSheet("border: 2px dashed black; background-color: white;")

        # Create move history panel
        self.move_history = QLabel("Move History")
        self.move_history.setFont(QFont("Palatino", 32))
        self.move_history.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set window background to white
        self.setStyleSheet("QMainWindow { background-color: white; }")

        # Connect signals
        self.prev_button.clicked.connect(self.prev_move)
        self.next_button.clicked.connect(self.next_move)

    def setup_timer_labels(self):
        for label in [self.white_timer_label, self.black_timer_label]:
            label.setFont(QFont("Palatino", 32))
            label.setFixedHeight(120)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Fixed alignment flag

        self.white_timer_label.setStyleSheet("background-color: white; color: black; border: 2px solid black;")
        self.black_timer_label.setStyleSheet("background-color: black; color: white; border: 2px solid white;")

    def resizeEvent(self, event):
        # Disable automatic resizing
        pass

    def new_game(self):
        self.board.reset()
        self.manual_game = True
        self.playing_vs_bot = False
        self.white_time = self.clock_time
        self.black_time = self.clock_time
        self.current_turn = chess.WHITE
        self.move_list = []
        self.solving_puzzle = False

        # Reset and start clocks
        self.white_clock.reset(self.clock_time)
        self.black_clock.reset(self.clock_time)
        self.white_clock.start()
        self.black_clock.stop()

        # Start main timer
        self.timer.start(1000)

        self.board_widget.setEnabled(True)
        self.board_widget.update()
        self.move_history.setText("New game started\nWhite to move")
        self.solving_puzzle = False  # Reset puzzle mode
        self.allowed_moves = None  # Reset allowed moves for new game

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
            self.solving_puzzle = False  # Ensure puzzle mode is off
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
        if bots:
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Online Bots")
            msg_box.setText("Available bots:\n" + "\n".join(bots[:10]))  # Show first 10 bots
            msg_box.exec()
        else:
            self.show_result("Failed to fetch online bots.")

    def update_timer(self):
        # Update clock widgets instead of labels
        if self.current_turn == chess.WHITE:
            self.white_clock.time = self.format_time(self.white_time)
        else:
            self.black_clock.time = self.format_time(self.black_time)
        self.white_clock.update()
        self.black_clock.update()

    def switch_turn(self):
        self.current_turn = not self.current_turn
        if self.manual_game and not self.solving_puzzle:
            if self.current_turn == chess.WHITE:
                self.white_clock.start()
                self.black_clock.stop()
            else:
                self.black_clock.start()
                self.white_clock.stop()

        # Update move history
        if self.board.move_stack:
            last_move = self.board.move_stack[-1]
            move_text = f"{'White' if not self.current_turn else 'Black'}: {last_move.uci()}"
            self.move_list.append(move_text)
            self.move_history.setText("\n".join(self.move_list))

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
            self.game_over(f"{winner} wins by checkmate!")
        elif (self.board.is_stalemate() or self.board.is_insufficient_material() or
              self.board.is_seventyfive_moves() or self.board.is_fivefold_repetition() or
              self.board.is_variant_draw()):
            self.game_over("Draw!")

    def game_over(self, message):
        self.timer.stop()
        self.white_clock.stop()
        self.black_clock.stop()
        self.board_widget.setEnabled(False)
        self.move_history.setText(f"{message}\n\n" + "\n".join(self.move_list))

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
        self.allowed_moves = [self.solution_moves[self.current_move_index]]  # Set initial allowed move
        self.solving_puzzle = True  # Set puzzle mode
        self.board_widget.update()
        self.move_history.setText(f"Today's Puzzle\nMake your move!")
        # Stop and hide clocks during puzzles
        self.white_clock.stop()
        self.black_clock.stop()
        self.white_clock.hide()
        self.black_clock.hide()

    def prev_move(self):
        if self.solving_puzzle and hasattr(self, "solution_moves") and self.solution_moves:
            if self.current_move_index > 0:
                self.current_move_index -= 1
                self.board.pop()
                self.allowed_moves = [self.solution_moves[self.current_move_index]]
        else:
            if self.current_move_pointer > 0:
                self.current_move_pointer -= 1
                # NEW: Revert to previous board state using saved FEN
                fen = self.game_states[self.current_move_pointer]
                self.board = chess.Board(fen)
                self.board_widget.board = self.board
                if self.move_list:
                    self.move_list.pop()
                self.update_move_history()
        self.board_widget.update()

    def next_move(self):
        if self.solving_puzzle and hasattr(self, "solution_moves") and self.solution_moves:
            if self.current_move_index < len(self.solution_moves):
                move = self.solution_moves[self.current_move_index]
                self.board.push(move)
                self.current_move_index += 1
                if self.current_move_index < len(self.solution_moves):
                    self.allowed_moves = [self.solution_moves[self.current_move_index]]
                else:
                    self.allowed_moves = None
        else:
            if self.current_move_pointer < len(self.game_states) - 1:
                self.current_move_pointer += 1
                fen = self.game_states[self.current_move_pointer]
                self.board = chess.Board(fen)
                self.board_widget.board = self.board
                # Optionally update move_list here if desired.
                self.update_move_history()
        self.board_widget.update()

    def highlight_correct_move(self):
        pass  # No longer highlighting the correct move

    def show_settings(self):
        if self.settings_menu.isHidden():
            # Position the menu below the settings button
            button = self.layout_manager.get_settings_button()
            pos = button.mapToGlobal(button.rect().bottomLeft())
            self.settings_menu.move(pos)
            self.settings_menu.show()
        else:
            self.settings_menu.hide()

    def apply_settings(self, resolution, fullscreen, clock_time):
        # Store new clock time
        self.clock_time = clock_time

        # Handle fullscreen
        if fullscreen != self.is_fullscreen:
            self.is_fullscreen = fullscreen
            if fullscreen:
                self.showFullScreen()
            else:
                self.showNormal()

        # Handle resolution change
        if resolution:
            width, height = map(int, resolution.split('x'))
            orientation = "vertical" if height > width else "horizontal"
            new_layout = f"layout_{width}x{height}_{orientation}"
            self.layout_manager.apply_layout(new_layout)

    def keyPressEvent(self, event):
        # Add ESC key to exit fullscreen
        if event.key() == Qt.Key.Key_Escape and self.is_fullscreen:
            self.showNormal()
            self.is_fullscreen = False
            self.settings_menu.fullscreen_check.setChecked(False)
        super().keyPressEvent(event)

    def check_orientation(self):
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        if screen:
            geometry = screen.geometry()
            orientation = "vertical" if geometry.height() > geometry.width() else "horizontal"
            # Always generate a profile from current geometry.
            profile = f"layout_{geometry.width()}x{geometry.height()}_{orientation}"
            self.layout_manager.apply_layout(profile)

    def update_move_history(self):
        # NEW: Update the move history label based on the move_list
        self.move_history.setText("\n".join(self.move_list))

def main():
    import os
    # If running unit tests, set headless environment variables.
    if "PYTEST_CURRENT_TEST" in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        if "XDG_RUNTIME_DIR" not in os.environ:
            os.environ["XDG_RUNTIME_DIR"] = "/tmp"
    # Only set the offscreen platform if running under pytest
    if "PYTEST_CURRENT_TEST" in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"

    app = QApplication(sys.argv)

    # Set Ubuntu style
    app.setStyle("Ubuntu")

    # Set environment variables for Ubuntu SDK
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Ubuntu"
    os.environ["UBUNTU_PLATFORM_API"] = "touch"

    # Initialize main window
    window = MainWindow()
    window.show()

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())