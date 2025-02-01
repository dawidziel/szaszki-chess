# szaszki!chess!

szaszki!chess! is a modern chess application with Lichess integration, puzzle solving, and bot play capabilities. It is designed with e-ink screens in mind and provides a clean and intuitive interface for playing chess.

## Features

- Play against Lichess bots
- Solve daily puzzles from Lichess
- Multiple layout profiles for different screen resolutions
- Customizable settings for game play and appearance

## Requirements

- Python 3.x
- PyQt6
- berserk
- python-chess
- pytest
- pytest-qt
- pytest-xvfb

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/dawidziel/szaszki-chess.git
    cd szaszki-chess
    ```

2. Install the required Python packages:
    ```sh
    pip install -r requirements.txt
    ```

3. Install additional dependencies for Ubuntu Touch:
    ```sh
    sudo apt-get install python3-pyqt6 python3-chess python3-berserk
    ```

## Usage

1. Run the application:
    ```sh
    python3 qt.py
    ```

2. Select your preferred layout profile and start playing!

## Development

### Running Unit Tests

To run the unit tests, use the following command:
```sh
pytest