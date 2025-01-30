import berserk
import logging
import time

logging.basicConfig(level=logging.DEBUG)

class LichessHandler:
    def __init__(self, token):
        self.session = berserk.TokenSession(token)
        self.client = berserk.Client(self.session)
        self.game_id = None
        self.stream = None

    def create_bot_game(self, bot_username, time_control='5+0', rated=False):
        clock_limit, clock_increment = self.parse_time_control(time_control)
        logging.debug(f"Creating bot game with {bot_username}, time control: {time_control}, rated: {rated}")
        response = self.client.challenges.create_ai(
            level=3, clock_limit=clock_limit, clock_increment=clock_increment
        )
        self.game_id = response['id']
        logging.debug(f"Created bot game with ID: {self.game_id}")
        # Retry mechanism to ensure the game is fully created
        for attempt in range(5):
            try:
                logging.debug(f"Attempting to stream game state for game ID: {self.game_id}, attempt: {attempt + 1}")
                self.stream = self.client.bots.stream_game_state(self.game_id)
                logging.debug(f"Successfully started streaming game state for game ID: {self.game_id}")
                break
            except berserk.exceptions.ResponseError as e:
                logging.error(f"Failed to stream game state for game ID: {self.game_id} - {e}")
                time.sleep(1)
        return self.game_id

    def make_move_bot(self, move):
        if self.game_id:
            for attempt in range(5):
                try:
                    logging.debug(f"Making move: {move} in game ID: {self.game_id}, attempt: {attempt + 1}")
                    self.client.bots.make_move(self.game_id, move)
                    logging.debug(f"Made move: {move} in game ID: {self.game_id}")
                    break
                except berserk.exceptions.ResponseError as e:
                    logging.error(f"Failed to make move: {move} in game ID: {self.game_id} - {e}")
                    time.sleep(1)
        else:
            logging.error("No game ID found. Cannot make move.")

    def get_game_state(self):
        if self.stream:
            for event in self.stream:
                if event['type'] == 'gameFull':
                    logging.debug(f"Received gameFull event for game ID: {self.game_id}")
                    return event['state']
                elif event['type'] == 'gameState':
                    logging.debug(f"Received gameState event for game ID: {self.game_id}")
                    return event
        return None

    def fetch_daily_puzzle(self):
        puzzle = self.client.puzzles.get_daily()
        logging.debug(f"Fetched daily puzzle: {puzzle}")
        return puzzle

    def parse_time_control(self, time_control):
        minutes, increment = map(int, time_control.split('+'))
        return minutes * 60, increment

    def get_online_bots(self):
        try:
            online_bots = self.client.bots.online()
            return [bot['username'] for bot in online_bots]
        except Exception as e:
            logging.error(f"Failed to get online bots: {e}")
            return []
