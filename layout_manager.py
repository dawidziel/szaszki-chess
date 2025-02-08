from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QScrollArea, QSizePolicy
from PyQt6.QtGui import QScreen, QGuiApplication, QFont

class LayoutManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.current_profile = None
        self.settings_button = None  # For settings menu access
        self.new_game_button = None
        self.play_vs_bot_button = None
        self.puzzles_button = None
        self.next_puzzle_button = None
        # Define your layout profiles (others omitted for brevity)
        self.layouts = {
            'layout_1920x1440_horizontal': {
                'window_size': (1920, 1440),
                'board_size': (1300, 1300),
                'history_size': (520, 1000),
                'button_size': (250, 80),
                'clock_size': (250, 120),
                'margin': (20, 80, 20, 20),
                'top_bar_visible': True,  # Top menu is visible
                'create_layout': self.create_horizontal_layout
            },
            'layout_1920x1080_horizontal': {
                'window_size': (1920, 1080),
                'board_size': (1000, 1000),
                'history_size': (800, 600),
                'button_size': (400, 80),
                'clock_size': (400, 120),
                'margin': (20, 40, 20, 20),
                'top_bar_visible': False,
                'create_layout': self.create_horizontal_layout
            },
            'layout_1440x1920_vertical': {
                'window_size': (1440, 1920),
                'board_size': (1300, 1300),
                'history_size': (640, 380),
                'button_size': (310, 80),
                'clock_size': (600, 220),
                'margin': (20, 80, 20, 20),
                'top_bar_visible': True,
                'create_layout': self.create_vertical_layout
            },
            'layout_2220x1080_horizontal': {
                'window_size': (2220, 1080),
                'board_size': (960, 960),
                'history_size': (1160, 600),
                'button_size': (250, 60),
                'clock_size': (560, 200),
                'margin': (20, 10, 20, 20),
                'top_bar_visible': True,
                'create_layout': self.create_horizontal_layout
            },
            'layout_1080x2220_vertical': {
                'window_size': (1080, 2220),
                'board_size': (1000, 1000),
                'history_size': (1000, 400),
                'button_size': (250, 45),
                'clock_size': (480, 180),
                'margin': (20, 10, 20, 20),
                'top_bar_visible': True,
                'create_layout': self.create_vertical_layout
            }
        }

    def apply_layout(self, profile_name):
        # Use default layout if detected profile is not defined.
        if profile_name not in self.layouts:
            profile = self.layouts["layout_1920x1440_horizontal"]
            self.current_profile = "layout_1920x1440_horizontal"
        else:
            profile = self.layouts[profile_name]
            self.current_profile = profile_name

        # Compute relative scale factor
        from PyQt6.QtGui import QGuiApplication
        screen = QGuiApplication.primaryScreen()
        if screen:
            geometry = screen.geometry()
            scale_factor = min(
                geometry.width() / profile['window_size'][0],
                geometry.height() / profile['window_size'][1]
            )
        else:
            scale_factor = 1.0

        # Apply scaled sizes
        ws = tuple(int(dim * scale_factor) for dim in profile['window_size'])
        bs = tuple(int(dim * scale_factor) for dim in profile['board_size'])
        hs = tuple(int(dim * scale_factor) for dim in profile['history_size'])
        btn = tuple(int(dim * scale_factor) for dim in profile['button_size'])
        clk = tuple(int(dim * scale_factor) for dim in profile['clock_size'])
        margin = tuple(max(20, int(m * scale_factor)) for m in profile['margin'])

        self.main_window.resize(*ws)
        # Respect the current window mode setting:
        if self.main_window.isFullScreen():
            self.main_window.showFullScreen()
        else:
            self.main_window.showNormal()

        if hasattr(self.main_window.board_widget, "setFixedSize"):
            self.main_window.board_widget.setFixedSize(*bs)
        else:
            logging.warning("board_widget does not support setFixedSize")

        self.main_window.move_history.setFixedSize(*hs)

        for btn_widget in [self.main_window.prev_button, self.main_window.hint_button]:
            btn_widget.setFixedSize(*btn)

        self.main_window.white_clock.setFixedSize(*clk)
        self.main_window.black_clock.setFixedSize(*clk)

        if self.current_profile.endswith('vertical'):
            self.create_vertical_layout()
        else:
            self.create_horizontal_layout()

    def create_top_buttons(self):
        buttons = []
        # Add navigation buttons styled with dotted borders
        buttons.append(self.main_window.prev_button)
        buttons.append(self.main_window.next_button)
        # ...existing buttons...
        if not self.new_game_button:
            self.new_game_button = QPushButton("New Game")
            self.new_game_button.setFont(QFont("Palatino", 14))
            self.new_game_button.clicked.connect(self.main_window.new_game)
            self.new_game_button.setStyleSheet("border: 2px dashed black; background-color: white;")
            self.new_game_button.setMinimumHeight(60)
            self.new_game_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        buttons.append(self.new_game_button)

        if not self.play_vs_bot_button:
            self.play_vs_bot_button = QPushButton("Play vs Bot")
            self.play_vs_bot_button.setFont(QFont("Palatino", 14))
            self.play_vs_bot_button.clicked.connect(self.main_window.play_vs_bot)
            self.play_vs_bot_button.setStyleSheet("border: 2px dashed black; background-color: white;")
            self.play_vs_bot_button.setMinimumHeight(60)
            self.play_vs_bot_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        buttons.append(self.play_vs_bot_button)

        if not self.puzzles_button:
            self.puzzles_button = QPushButton("Puzzles")
            self.puzzles_button.setFont(QFont("Palatino", 14))
            self.puzzles_button.clicked.connect(self.main_window.show_todays_puzzles)
            self.puzzles_button.setStyleSheet("border: 2px dashed black; background-color: white;")
            self.puzzles_button.setMinimumHeight(60)
            self.puzzles_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        buttons.append(self.puzzles_button)

        if not self.settings_button:
            self.settings_button = QPushButton("Settings")
            self.settings_button.setFont(QFont("Palatino", 14))
            self.settings_button.clicked.connect(self.main_window.show_settings)
            self.settings_button.setStyleSheet("border: 2px dashed black; background-color: white;")
            self.settings_button.setMinimumHeight(60)
            self.settings_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        buttons.append(self.settings_button)

        # Add Next Puzzle button
        if not self.next_puzzle_button:
            self.next_puzzle_button = QPushButton("Next Puzzle")
            self.next_puzzle_button.setFont(QFont("Palatino", 14))
            self.next_puzzle_button.setStyleSheet("border: 2px dashed black; background-color: white;")
            self.next_puzzle_button.setVisible(False)  # Hidden by default
            self.next_puzzle_button.clicked.connect(self.main_window.load_next_puzzle)
        buttons.append(self.next_puzzle_button)

        return buttons

    def get_settings_button(self):
        return self.settings_button

    def create_horizontal_layout(self):
        container = QWidget()
        profile = self.layouts[self.current_profile]
        main_wrapper = QHBoxLayout()
        main_wrapper.setContentsMargins(*profile['margin'])
        main_wrapper.setSpacing(20)

        # Left panel: Chess board only.
        left_panel = QVBoxLayout()
        left_panel.addWidget(self.main_window.board_widget)
        main_wrapper.addLayout(left_panel, stretch=2)

        # Right panel: Contains top menu, then move history with navigation buttons and chat & info.
        right_panel = QVBoxLayout()

        # --- Top Menu (extra buttons except navigation) ---
        menu_layout = QHBoxLayout()
        # Exclude prev/next buttons from top menu now.
        for btn in self.create_top_buttons()[2:]:
            menu_layout.addWidget(btn)
        right_panel.addLayout(menu_layout)

        # --- Move History with Navigation Buttons ---
        history_container = QHBoxLayout()
        # Move History widget takes available horizontal space.
        history_container.addWidget(self.main_window.move_history, stretch=1)

        # Navigation buttons container (square buttons)
        nav_buttons = QVBoxLayout()
        # Set fixed square size (example: 80x80)
        self.main_window.prev_button.setFixedSize(80, 80)
        self.main_window.next_button.setFixedSize(80, 80)
        nav_buttons.addWidget(self.main_window.prev_button)
        nav_buttons.addWidget(self.main_window.next_button)
        history_container.addLayout(nav_buttons)
        right_panel.addLayout(history_container)

        # --- Chat Box (below move history) ---
        right_panel.addWidget(self.main_window.chat_box, stretch=0)

        # --- Player Info ---
        right_panel.addWidget(self.main_window.player_info)

        # --- Clocks at Bottom (flat layout) ---
        clocks_layout = QHBoxLayout()
        clocks_layout.setSpacing(20)
        clocks_layout.addWidget(self.main_window.white_clock)
        clocks_layout.addWidget(self.main_window.black_clock)
        right_panel.addLayout(clocks_layout)

        # Add Next Puzzle button at bottom right
        button_container = QHBoxLayout()
        button_container.addStretch()
        button_container.addWidget(self.next_puzzle_button)
        right_panel.addLayout(button_container)

        main_wrapper.addLayout(right_panel, stretch=1)
        container.setLayout(main_wrapper)
        self.main_window.setCentralWidget(container)

    def create_vertical_layout(self):
        container = QWidget()
        profile = self.layouts[self.current_profile]
        main_wrapper = QVBoxLayout()
        main_wrapper.setContentsMargins(*profile['margin'])
        main_wrapper.setSpacing(20)

        # Chess board on top.
        main_wrapper.addWidget(self.main_window.board_widget, stretch=2)

        # Middle section with horizontal split.
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(20)

        # Left column: Move history and chat.
        text_container = QVBoxLayout()
        text_container.addWidget(self.main_window.move_history)
        text_container.addWidget(self.main_window.chat_box)
        middle_layout.addLayout(text_container, stretch=2)

        # Right column: Top menu, player info, then clocks.
        right_column = QVBoxLayout()
        menu_layout = QHBoxLayout()
        menu_layout.addStretch()
        for btn in self.create_top_buttons():
            menu_layout.addWidget(btn)
        right_column.addLayout(menu_layout)
        right_column.addWidget(self.main_window.player_info)
        clocks_layout = QHBoxLayout()
        clocks_layout.addWidget(self.main_window.white_clock)
        clocks_layout.addWidget(self.main_window.black_clock)
        right_column.addLayout(clocks_layout)

        # Add Next Puzzle button at bottom right
        button_container = QHBoxLayout()
        button_container.addStretch()
        button_container.addWidget(self.next_puzzle_button)
        right_column.addLayout(button_container)

        middle_layout.addLayout(right_column, stretch=1)
        main_wrapper.addLayout(middle_layout, stretch=1)

        container.setLayout(main_wrapper)
        self.main_window.setCentralWidget(container)
