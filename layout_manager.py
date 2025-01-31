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
                'create_layout': self.create_horizontal_layout
            },
            'layout_1920x1080_horizontal': {
                'window_size': (1920, 1080),
                'board_size': (1000, 1000),
                'history_size': (860, 700),
                'button_size': (400, 80),
                'clock_size': (400, 120),
                'margin': (20, 40, 20, 20),
                'create_layout': self.create_horizontal_layout
            },
            'layout_1440x1920_vertical': {
                'window_size': (1440, 1920),
                'board_size': (1300, 1300),
                'history_size': (640, 380),
                'button_size': (310, 80),
                'clock_size': (600, 220),
                'margin': (20, 80, 20, 20),
                'create_layout': self.create_vertical_layout
            },
            'layout_2220x1080_horizontal': {
                'window_size': (2220, 1080),
                'board_size': (960, 960),
                'history_size': (1160, 600),
                'button_size': (250, 60),
                'clock_size': (560, 200),
                'margin': (20, 10, 20, 20),
                'create_layout': self.create_horizontal_layout
            },
            'layout_1080x2220_vertical': {
                'window_size': (1080, 2220),
                'board_size': (1000, 1000),
                'history_size': (1000, 400),
                'button_size': (250, 45),
                'clock_size': (480, 180),
                'margin': (20, 10, 20, 20),
                'create_layout': self.create_vertical_layout
            }
        }

    def apply_layout(self, profile_name):
        if profile_name not in self.layouts:
            profile_name = 'layout_1920x1440_horizontal'

        profile = self.layouts[profile_name]
        self.current_profile = profile_name

        # Apply window size
        self.main_window.resize(*profile['window_size'])
        self.main_window.setFixedSize(*profile['window_size'])

        # Apply widget sizes
        self.main_window.board_widget.setFixedSize(*profile['board_size'])
        self.main_window.move_history.setFixedSize(*profile['history_size'])

        for btn in [self.main_window.prev_button, self.main_window.next_button]:
            btn.setFixedSize(*profile['button_size'])

        self.main_window.white_clock.setFixedSize(*profile['clock_size'])
        self.main_window.black_clock.setFixedSize(*profile['clock_size'])

        # Create the layout using the profile
        if profile_name.endswith('vertical'):
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
        main_wrapper = QHBoxLayout()  # Changed to HBox for 1920x1080
        main_wrapper.setContentsMargins(*profile['margin'])
        main_wrapper.setSpacing(20)

        # Only show top panel for non-1920x1080 layouts
        if self.current_profile != 'layout_1920x1080_horizontal':
            top_wrapper = QVBoxLayout()
            top_panel = QHBoxLayout()
            top_panel.setSpacing(20)
            top_panel.setContentsMargins(40, 10, 40, 10)
            for btn in self.create_top_buttons():
                top_panel.addWidget(btn)
            top_panel.addStretch()
            top_wrapper.addLayout(top_panel)
            top_wrapper.addWidget(self.main_window.board_widget)
            main_wrapper.addLayout(top_wrapper)
        else:
            # For 1920x1080, add board directly to main wrapper
            main_wrapper.addWidget(self.main_window.board_widget)

        # Right side panel
        right_panel = QVBoxLayout()
        right_panel.setSpacing(20)

        # Only add menu buttons on right for 1920x1080
        if self.current_profile == 'layout_1920x1080_horizontal':
            menu_panel = QVBoxLayout()
            menu_panel.setSpacing(10)
            for btn in self.create_top_buttons():
                btn.setFixedSize(200, 50)  # Smaller buttons for right side
                menu_panel.addWidget(btn)
            right_panel.addLayout(menu_panel)

        right_panel.addWidget(self.main_window.move_history)

        # Navigation and clocks
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
        main_wrapper.addWidget(right_widget)

        container.setLayout(main_wrapper)
        self.main_window.setCentralWidget(container)

    def create_vertical_layout(self):
        container = QWidget()
        profile = self.layouts[self.current_profile]
        main_wrapper = QVBoxLayout()
        main_wrapper.setContentsMargins(*profile['margin'])
        main_wrapper.setSpacing(20)

        # Top panel with single row of buttons
        top_panel = QHBoxLayout()
        top_panel.setSpacing(20)
        top_panel.setContentsMargins(20, 10, 20, 10)

        # Add buttons in single row
        for btn in self.create_top_buttons():
            btn.setFixedSize(250, 60)
            btn.setFont(QFont("Palatino", 28))
            top_panel.addWidget(btn)

        # Main content
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)

        # Chess board
        content_layout.addWidget(self.main_window.board_widget)

        # Move history
        content_layout.addWidget(self.main_window.move_history)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(40)
        for btn in [self.main_window.prev_button, self.main_window.next_button]:
            btn.setFixedSize(480, 80)
            nav_layout.addWidget(btn)
        content_layout.addLayout(nav_layout)

        # Clocks
        clock_layout = QHBoxLayout()
        clock_layout.setSpacing(40)
        for clock in [self.main_window.white_clock, self.main_window.black_clock]:
            clock_layout.addWidget(clock)
        content_layout.addLayout(clock_layout)

        # Assemble
        main_wrapper.addLayout(top_panel)
        main_wrapper.addLayout(content_layout)
        container.setLayout(main_wrapper)
        self.main_window.setCentralWidget(container)
