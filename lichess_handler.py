import berserk
import logging
import time
import traceback
import chess

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
            move_uci = move.uci() if isinstance(move, chess.Move) else str(move)
            for attempt in range(5):
                try:
                    logging.debug(f"Attempting move: {move_uci} in game {self.game_id} (attempt {attempt+1}/5)")
                    start_time = time.time()
                    self.client.bots.make_move(self.game_id, move_uci)
                    latency = int((time.time() - start_time) * 1000)
                    logging.debug(f"Successfully made move {move_uci} in {latency}ms")
                    return  # Success - exit the loop
                except berserk.exceptions.ResponseError as e:
                    error_details = {
                        'status_code': e.status_code,
                        'message': str(e),
                        'response': getattr(e, 'response', None),
                        'attempt': attempt+1,
                        'game_id': self.game_id,
                        'move': move_uci
                    }
                    logging.error("Move failed:\n" + "\n".join(
                        f"{k}: {v}" for k,v in error_details.items()
                    ))
                    logging.debug("Full traceback:\n%s", traceback.format_exc())
                    time.sleep(1)
                except Exception as e:
                    logging.error(f"Unexpected error making move {move_uci}: {str(e)}")
                    logging.debug("Full traceback:\n%s", traceback.format_exc())
                    time.sleep(1)
            logging.error(f"Permanently failed to make move {move_uci} after 5 attempts")
        else:
            logging.error("No active game ID - cannot make move")

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

    def get_next_puzzle(self):
        try:
            # Correct method for /api/puzzle/next endpoint
            return self.client.puzzles.get_daily()
        except Exception as e:
            logging.error(f"Failed to fetch next puzzle: {e}")
            return None
