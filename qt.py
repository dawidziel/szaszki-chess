import sys
import chess
import chess.pgn
import time
import os
import io
import logging
from PyQt6.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton, QMessageBox, QLabel  # Added QLabel
from PyQt6.QtGui import QPixmap, QPainter, QColor, QScreen, QGuiApplication, QFont
from PyQt6.QtCore import QUrl, QTimer, Qt, QMetaObject, QThread, QObject, pyqtSignal, pyqtSlot  # Added QTimer, Qt, and QMetaObject
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

        # Check if it's our turn based on board state
        if self.main_window.playing_as_white != self.board.turn:
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
            if self.main_window.solving_puzzle:
                if move in self.board.legal_moves:
                    if self.main_window.allowed_moves and move in self.main_window.allowed_moves:
                        # Valid move: update board and history
                        self.board.push(move)
                        self.main_window.move_list.append(f"Puzzle move: {move.uci()}")
                        self.main_window.game_states.append(self.board.fen())
                    else:
                        self.main_window.chat_box.appendPlainText(
                            f"Incorrect move. Puzzle rating: {self.main_window.puzzle_rating}. Please try again."
                        )
                        self.main_window.puzzle_failed = True
                        if self.main_window.layout_manager.next_puzzle_button:
                            self.main_window.layout_manager.next_puzzle_button.setVisible(True)
                # else: ignore illegal move
            else:
                if move in self.board.legal_moves and (not self.main_window.allowed_moves or move in self.main_window.allowed_moves):
                    self.board.push(move)
                    logging.debug(f"Player move: {move.uci()}")
                    self.main_window.game_moves.append(move)
                    self.main_window.current_move_pointer = len(self.main_window.game_moves)
                    self.main_window.game_states.append(self.board.fen())
                    self.main_window.switch_turn()
                    self.main_window.check_game_result()
                    if self.main_window.playing_vs_bot and not self.main_window.solving_puzzle:
                        self.main_window.send_move_to_bot(move)
            self.selected_square = None
        self.update()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess")

        # Remove layout selector and just initialize components
        self.playing_as_white = True  # Default value, will be updated when game starts
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
        self.next_puzzle_button = None  # Add this
        logging.debug("MainWindow initialized.")

    # NEW: Add a method to debug-print the widget tree
    def debug_print_widget_tree(self, widget, indent=""):
        logging.debug(f"{indent}{widget.__class__.__name__}")
        for child in widget.findChildren(QWidget):
            self.debug_print_widget_tree(child, indent + "  ")

    def auto_apply_layout(self):
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        if screen:
            geometry = screen.geometry()
            # Always use the default layout and let it scale
            self.layout_manager.apply_layout("layout_1920x1440_horizontal")

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

    def init_ui_elements(self):
        # Create clocks
        self.white_clock = ClockWidget(is_white=True)
        self.black_clock = ClockWidget(is_white=False)

        # Create navigation buttons with size policy for responsiveness.
        self.prev_button = QPushButton("Previous")
        self.hint_button = QPushButton("Ask for Hint")  # Changed from "Next" to "Ask for Hint"
        for btn in [self.prev_button, self.hint_button]:
            btn.setFont(QFont("Palatino", 32))
            btn.setFixedHeight(80)  # Keep height fixed if necessary
            btn.setSizePolicy(btn.sizePolicy().horizontalPolicy(), btn.sizePolicy().verticalPolicy())
            btn.setStyleSheet("border: 2px dashed black; background-color: white;")

        # NEW: Use QPlainTextEdit for move history with small font and scrollable area
        from PyQt6.QtWidgets import QPlainTextEdit
        self.move_history = QPlainTextEdit()
        self.move_history.setReadOnly(True)
        self.move_history.setFont(QFont("Palatino", 10))

        # NEW: Widget for player names and rankings
        self.player_info = QLabel("White: PlayerA (1500)   Black: PlayerB (1480)")
        self.player_info.setFont(QFont("Palatino", 10))
        self.player_info.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # NEW: Add chat box for user feedback
        self.chat_box = QPlainTextEdit()
        self.chat_box.setReadOnly(True)
        self.chat_box.setFont(QFont("Palatino", 12))
        self.chat_box.setPlaceholderText("Chat messages...")

        # Set window background to white
        self.setStyleSheet("QMainWindow { background-color: white; }")

        # Connect signals
        self.prev_button.clicked.connect(self.prev_move)
        self.hint_button.clicked.connect(self.ask_for_hint)  # Changed from next_move to ask_for_hint

        # Navigation buttons
        self.prev_button = QPushButton("Previous")
        self.prev_button.setFont(QFont("Palatino", 32))
        self.prev_button.setFixedHeight(80)
        self.prev_button.setStyleSheet("border: 2px dashed black; background-color: white;")
        self.prev_button.clicked.connect(self.prev_move)

        self.next_button = QPushButton("Next")
        self.next_button.setFont(QFont("Palatino", 32))
        self.next_button.setFixedHeight(80)
        self.next_button.setStyleSheet("border: 2px dashed black; background-color: white;")
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
        logging.debug("new_game() called.")
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
        self.move_history.setPlainText("New game started\nWhite to move")
        self.solving_puzzle = False  # Reset puzzle mode
        self.allowed_moves = None  # Reset allowed moves for new game

    def play_vs_bot(self):
        bot_username = "chessosity"  # Example bot username
        game_id = self.lichess_handler.create_bot_game(bot_username, time_control='5+0', rated=False)
        if game_id:
            # Set some initial game parameters
            self.playing_vs_bot = True
            self.white_time = 300  # 5 minutes
            self.black_time = 300  # 5 minutes
            self.timer.start(1000)
            self.board_widget.setEnabled(True)
            self.allowed_moves = None  # Allow all legal moves in bot game
            logging.debug(f"Started bot game with ID: {game_id}")
            self.solving_puzzle = False  # Ensure puzzle mode is off

            # Start streaming game events and processing them via handle_game_event()
            self.lichess_handler.run_game_stream(self.handle_game_event)
        else:
            self.show_result("Failed to create bot game.")

    def send_move_to_bot(self, move):
        """Send move to bot in a separate thread"""
        from PyQt6.QtCore import QThread, QObject, pyqtSignal

        class BotWorker(QObject):
            finished = pyqtSignal()

            def __init__(self, handler, game_id, move):
                super().__init__()
                self.handler = handler
                self.game_id = game_id
                self.move = move

            def run(self):
                try:
                    self.handler.make_move_bot(self.move)
                except Exception as e:
                    logging.error(f"Error sending move to bot: {e}")
                finally:
                    self.finished.emit()

        self.bot_thread = QThread()
        self.bot_worker = BotWorker(self.lichess_handler, self.lichess_handler.game_id, move)
        self.bot_worker.moveToThread(self.bot_thread)
        self.bot_thread.started.connect(self.bot_worker.run)
        self.bot_worker.finished.connect(self.bot_thread.quit)
        self.bot_worker.finished.connect(self.bot_worker.deleteLater)
        self.bot_thread.finished.connect(self.bot_thread.deleteLater)
        self.bot_thread.start()

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
            self.update_move_history()

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
        self.move_history.setPlainText(f"{message}\n\n" + "\n".join(self.move_list))

    def show_result(self, message):
        msg_box = QMessageBox()
        msg_box.setText(message)
        msg_box.exec()

    def show_todays_puzzles(self):
        puzzle = self.lichess_handler.fetch_daily_puzzle()
        if not puzzle:
            return

        self.puzzle_rating = puzzle['puzzle']['rating']
        pgn = puzzle['game']['pgn']
        game = chess.pgn.read_game(io.StringIO(pgn))
        self.board = game.end().board()
        self.board_widget.board = self.board
        self.solution_moves = [chess.Move.from_uci(move) for move in puzzle['puzzle']['solution']]
        self.current_move_index = 0
        self.allowed_moves = [self.solution_moves[self.current_move_index]]
        self.solving_puzzle = True
        self.puzzle_failed = False
        self.board_widget.update()
        self.move_history.setPlainText("Today's Puzzle\nMake your move!")
        self.layout_manager.next_puzzle_button.setVisible(False)  # Reset visibility

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

    def ask_for_hint(self):
        if self.solving_puzzle and hasattr(self, "solution_moves") and self.solution_moves:
            if self.current_move_index < len(self.solution_moves):
                hint_move = self.solution_moves[self.current_move_index]
                self.chat_box.appendPlainText(f"Hint: Try {hint_move.uci()}")
            else:
                self.chat_box.appendPlainText("No more hints available. Puzzle solved!")
        else:
            self.chat_box.appendPlainText("Hints are only available in puzzle mode.")

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
        logging.debug(f"Key pressed: {event.key()}")
        if event.key() == Qt.Key.Key_Escape and self.is_fullscreen:
            logging.debug("Exiting fullscreen.")
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

    def format_move_history(self):
        pgn = ""
        for i in range(0, len(self.move_list), 2):
            move_num = i // 2 + 1
            white_move = self.move_list[i].split(":")[-1].strip()
            if i + 1 < len(self.move_list):
                black_move = self.move_list[i+1].split(":")[-1].strip()
                pgn += f"{move_num}. {white_move} {black_move} "
            else:
                pgn += f"{move_num}. {white_move} "
        return pgn.strip()

    def update_move_history(self):
        # NEW: Update the move history display in PGN format
        self.move_history.setPlainText(self.format_move_history())

    def auto_play_next_move(self):
        """
        Automatically plays the next move in puzzle mode if available.
        """
        if self.solving_puzzle and self.allowed_moves:
            auto_move = self.allowed_moves[0]
            if auto_move in self.board.legal_moves:
                self.board.push(auto_move)
                self.move_list.append(
                    f"{'White' if self.board.turn == chess.BLACK else 'Black'}: {auto_move.uci()}"
                )
                self.game_states.append(self.board.fen())
                self.current_move_index += 1
                if self.current_move_index < len(self.solution_moves):
                    self.allowed_moves = [self.solution_moves[self.current_move_index]]
                else:
                    self.allowed_moves = None
                self.board_widget.update()

    def load_next_puzzle(self):
        try:
            # Run blocking network call in a thread
            from PyQt6.QtCore import QThread, QObject, pyqtSignal, pyqtSlot

            class PuzzleLoader(QObject):
                loaded = pyqtSignal(object)
                error = pyqtSignal(str)

                @pyqtSlot()
                def load(self):
                    try:
                        puzzle = self.handler.get_next_puzzle()
                        self.loaded.emit(puzzle)
                    except Exception as e:
                        self.error.emit(str(e))

            self.puzzle_loader = QThread()
            self.loader_worker = PuzzleLoader()
            self.loader_worker.handler = self.lichess_handler
            self.loader_worker.moveToThread(self.puzzle_loader)
            self.puzzle_loader.started.connect(self.loader_worker.load)
            self.loader_worker.loaded.connect(self.handle_puzzle_loaded)
            self.loader_worker.error.connect(lambda e: self.chat_box.appendPlainText(f"Error: {e}"))
            self.loader_worker.loaded.connect(self.puzzle_loader.quit)
            self.loader_worker.error.connect(self.puzzle_loader.quit)
            self.puzzle_loader.start()

        except Exception as e:
            logging.error(f"Puzzle loading failed: {e}")
            self.chat_box.appendPlainText("Error loading puzzle. Please try again.")

    def handle_puzzle_loaded(self, puzzle):
        """Handle loaded puzzle data in main thread"""
        if not puzzle:
            return

        self.puzzle_rating = puzzle['puzzle']['rating']
        pgn = puzzle['game']['pgn']
        game = chess.pgn.read_game(io.StringIO(pgn))
        self.board = game.end().board()
        self.board_widget.board = self.board
        self.solution_moves = [chess.Move.from_uci(move) for move in puzzle['puzzle']['solution']]
        self.current_move_index = 0
        self.allowed_moves = [self.solution_moves[self.current_move_index]]
        self.solving_puzzle = True
        self.puzzle_failed = False
        self.board_widget.update()
        self.move_history.setPlainText("Today's Puzzle\nMake your move!")
        self.layout_manager.next_puzzle_button.setVisible(False)  # Reset visibility

    def safe_timer_start(self, interval, callback):
        """Thread-safe timer initialization"""
        QMetaObject.invokeMethod(
            QTimer(self),
            'singleShot',
            Qt.ConnectionType.QueuedConnection,
            QMetaObject.ArgumentList([interval, callback])
        )

    def handle_game_event(self, event):
        """
        Thread-safe callback to handle each event from the game stream.
        Uses QTimer.singleShot to post the event processing onto the main (GUI) thread.
        """
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: self._handle_game_event(event))

    def _handle_game_event(self, event):
        event_type = event.get('type')
        logging.debug(f"Handling game event type: {event_type}")

        if event_type == 'gameFull':
            # Get player information
            white_info = event.get('white', {})
            black_info = event.get('black', {})

            # Determine player color and get ratings
            self.playing_as_white = white_info.get('id') == self.lichess_handler.get_user_id()
            player_color = 'White' if self.playing_as_white else 'Black'
            opponent_type = 'AI' if 'aiLevel' in (black_info if self.playing_as_white else white_info) else 'Human'

            # Get ratings
            player_rating = white_info.get('rating') if self.playing_as_white else black_info.get('rating')
            ai_level = (black_info if self.playing_as_white else white_info).get('aiLevel', 'Unknown')

            # Display game info in chat
            game_info = (
                f"Game started!\n"
                f"You are playing as {player_color}\n"
                f"Your rating: {player_rating or 'Unrated'}\n"
                f"Opponent: {opponent_type} Level {ai_level}"
            )
            self.chat_box.appendPlainText(game_info)

            # Set board orientation
            self.board_widget.flip_board = not self.playing_as_white
            self.board_widget.update()
            logging.debug(f"Board orientation: {'Flipped' if self.board_widget.flip_board else 'Normal'}")

            # Set the board FEN from the event
            new_fen = event.get('state', {}).get('fen') or event.get('initialFen')
            if new_fen == "startpos":
                new_fen = chess.STARTING_FEN
            if new_fen:
                self.board.set_fen(new_fen)
                self.board_widget.update()
                logging.debug(f"Board updated with FEN: {new_fen}")

            # Process any initial moves
            initial_state = event.get('state', {})
            if 'moves' in initial_state and initial_state['moves']:
                self._process_moves(initial_state['moves'])

            # Enable board only if it's our turn
            is_our_turn = (self.board.turn == self.playing_as_white)
            self.board_widget.setEnabled(is_our_turn)
            logging.debug(f"Board enabled: {is_our_turn}")

        elif event_type == 'gameState':
            new_fen = event.get('fen')
            if new_fen:
                self.board.set_fen(new_fen)
                self.board_widget.update()
                logging.debug(f"Game state updated: {new_fen}")
            if 'moves' in event:
                moves = event['moves'].split()
                self.move_history.setPlainText("\n".join(moves))
        else:
            logging.debug(f"Unhandled game event: {event}")

    def _process_moves(self, moves_str: str):
        """
        Process a space-separated string of moves, update the board and move history.
        """
        if not moves_str:
            return

        moves = moves_str.split()
        logging.debug(f"Processing moves: {moves}")

        # Reset board to starting position
        self.board.reset()

        # Apply all moves
        formatted_moves = []
        for i, move in enumerate(moves):
            try:
                chess_move = chess.Move.from_uci(move)
                self.board.push(chess_move)
                # Format move for move history (e.g. "1. e4 e5")
                if i % 2 == 0:
                    formatted_moves.append(f"{i//2 + 1}. {move}")
                else:
                    formatted_moves[-1] = f"{formatted_moves[-1]} {move}"
            except ValueError as e:
                logging.error(f"Invalid move {move}: {e}")

        # Update UI
        self.board_widget.update()
        move_history_text = "\n".join(formatted_moves)
        self.move_history.setPlainText(move_history_text)
        # Scroll to bottom of move history
        self.move_history.verticalScrollBar().setValue(
            self.move_history.verticalScrollBar().maximum()
        )
        logging.debug(f"Board and move history updated with moves: {moves}")
        logging.debug(f"Move history text:\n{move_history_text}")

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
    logging.debug("MainWindow shown.")
    # NEW: Print the widget tree for debugging
    window.debug_print_widget_tree(window)
    logging.debug("Widget tree printed.")

    return app.exec()

if __name__ == "__main__":
    sys.exit(main())