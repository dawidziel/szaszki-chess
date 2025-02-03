from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtGui import QScreen, QGuiApplication, QFont

class LayoutManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.current_profile = None
        self.settings_button = None  # Store reference to settings button
        self.layouts = {
            'layout_1920x1440_horizontal': {
                'window_size': (1920, 1440),
                'board_size': (1300, 1300),
                'history_size': (520, 1000),
                'button_size': (250, 80),
                'clock_size': (250, 120),
                'margin': (20, 80, 20, 20),
                'top_bar_visible': True,        # <-- new key
                'create_layout': self.create_horizontal_layout
            },
            'layout_1920x1080_horizontal': {
                'window_size': (1920, 1080),
                'board_size': (1000, 1000),
                'history_size': (860, 700),
                'button_size': (400, 80),
                'clock_size': (400, 120),
                'margin': (20, 40, 20, 20),
                'top_bar_visible': False,       # <-- new key (no top bar)
                'create_layout': self.create_horizontal_layout
            },
            'layout_1440x1920_vertical': {
                'window_size': (1440, 1920),
                'board_size': (1300, 1300),
                'history_size': (640, 380),
                'button_size': (310, 80),
                'clock_size': (600, 220),
                'margin': (20, 80, 20, 20),
                'top_bar_visible': True,        # <-- new key
                'create_layout': self.create_vertical_layout
            },
            'layout_2220x1080_horizontal': {
                'window_size': (2220, 1080),
                'board_size': (960, 960),
                'history_size': (1160, 600),
                'button_size': (250, 60),
                'clock_size': (560, 200),
                'margin': (20, 10, 20, 20),
                'top_bar_visible': True,        # <-- adjust as needed
                'create_layout': self.create_horizontal_layout
            },
            'layout_1080x2220_vertical': {
                'window_size': (1080, 2220),
                'board_size': (1000, 1000),
                'history_size': (1000, 400),
                'button_size': (250, 45),
                'clock_size': (480, 180),
                'margin': (20, 10, 20, 20),
                'top_bar_visible': True,        # <-- new key
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
            # Compute scale factor based on window baseline
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
        margin = tuple(int(m * scale_factor) for m in profile['margin'])

        self.main_window.resize(*ws)
        self.main_window.setFixedSize(*ws)

        self.main_window.board_widget.setFixedSize(*bs)
        self.main_window.move_history.setFixedSize(*hs)

        for btn_widget in [self.main_window.prev_button, self.main_window.next_button]:
            btn_widget.setFixedSize(*btn)

        self.main_window.white_clock.setFixedSize(*clk)
        self.main_window.black_clock.setFixedSize(*clk)

        # Update margins in layout creation methods if needed
        if self.current_profile.endswith('vertical'):
            self.create_vertical_layout()
        else:
            self.create_horizontal_layout()

    def create_top_buttons(self):
        # Create buttons in a single row
        buttons = []
        button_configs = [
            ("New Game", 250, 60),
            ("Play vs Bot", 250, 60),
            ("Puzzles", 250, 60),
            ("Settings", 250, 60)
        ]

        for text, width, height in button_configs:
            btn = QPushButton(text)
            btn.setFixedSize(width, height)
            btn.setFont(QFont("Palatino", 28))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 2px dashed black;
                    padding: 5px;
                    margin: 0px 10px;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                }
            """)
            if text == "Settings":
                self.settings_button = btn
            buttons.append(btn)

        # Connect button signals
        buttons[0].clicked.connect(self.main_window.new_game)
        buttons[1].clicked.connect(self.main_window.play_vs_bot)
        buttons[2].clicked.connect(self.main_window.show_todays_puzzles)
        buttons[3].clicked.connect(self.main_window.show_settings)

        return buttons

    def get_settings_button(self):
        return self.settings_button

    def create_horizontal_layout(self):
        container = QWidget()
        profile = self.layouts[self.current_profile]
        main_wrapper = QHBoxLayout()
        main_wrapper.setContentsMargins(*profile['margin'])
        main_wrapper.setSpacing(20)

        # Left side: Board widget
        main_wrapper.addWidget(self.main_window.board_widget, stretch=2)

        # Right panel: top menu buttons arranged horizontally at the top right,
        # then player info, move history, navigation, and clocks.
        right_panel = QVBoxLayout()
        right_panel.setSpacing(20)
        # NEW: Add horizontal top menu
        top_menu = QHBoxLayout()
        top_menu.addStretch()
        for btn in self.create_top_buttons():
            top_menu.addWidget(btn)
        right_panel.addLayout(top_menu)
        # Existing controls below the menu
        right_panel.addWidget(self.main_window.player_info)
        right_panel.addWidget(self.main_window.move_history)
        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self.main_window.prev_button)
        nav_layout.addWidget(self.main_window.next_button)
        right_panel.addLayout(nav_layout)
        clock_layout = QHBoxLayout()
        clock_layout.addWidget(self.main_window.white_clock)
        clock_layout.addWidget(self.main_window.black_clock)
        right_panel.addLayout(clock_layout)

        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        main_wrapper.addWidget(right_widget, stretch=1)

        container.setLayout(main_wrapper)
        self.main_window.setCentralWidget(container)

    def create_vertical_layout(self):
        container = QWidget()
        profile = self.layouts[self.current_profile]
        # NEW: Use a horizontal split: left panel for board & move history,
        # right panel contains top menu (horizontally) and player info.
        main_wrapper = QHBoxLayout()
        main_wrapper.setContentsMargins(*profile['margin'])
        main_wrapper.setSpacing(20)

        # Left vertical panel: board and move history with navigation and clocks.
        left_panel = QVBoxLayout()
        left_panel.setSpacing(20)
        left_panel.addWidget(self.main_window.board_widget, stretch=2)
        left_panel.addWidget(self.main_window.move_history, stretch=1)
        nav_layout = QHBoxLayout()
        for btn in [self.main_window.prev_button, self.main_window.next_button]:
            btn.setFixedSize(480, 80)
            nav_layout.addWidget(btn)
        left_panel.addLayout(nav_layout)
        clock_layout = QHBoxLayout()
        for clock in [self.main_window.white_clock, self.main_window.black_clock]:
            clock_layout.addWidget(clock)
        left_panel.addLayout(clock_layout)

        # Right panel: top menu (horizontal) at the top-right and player info below.
        right_panel = QVBoxLayout()
        right_panel.setSpacing(20)
        top_menu = QHBoxLayout()
        top_menu.addStretch()
        for btn in self.create_top_buttons():
            top_menu.addWidget(btn)
        right_panel.addLayout(top_menu)
        right_panel.addWidget(self.main_window.player_info)

        main_wrapper.addLayout(left_panel, stretch=2)
        main_wrapper.addLayout(right_panel, stretch=1)

        container.setLayout(main_wrapper)
        self.main_window.setCentralWidget(container)
