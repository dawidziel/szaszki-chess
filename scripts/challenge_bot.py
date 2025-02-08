#!/usr/bin/env python3
import sys
import berserk

def parse_time_control(time_control: str) -> (int, int):
    """
    Parse a time control string like "5+0" into (clock_limit, clock_increment).
    Clock limit is expressed in seconds.
    """
    try:
        minutes, increment = map(int, time_control.split('+'))
        return minutes * 60, increment
    except Exception:
        raise ValueError("Time control must be in the format 'minutes+increment' e.g. '5+0'.")

def create_challenge_with_bot(api_token: str, opponent: str = "chessosity", time_control: str = "5+0", rated: bool = False):
    """
    Create a challenge game against the specified opponent (default 'chessosity').

    :param api_token: Your Lichess API token.
    :param opponent: Opponent's ID (default: "chessosity")
    :param time_control: Time control as string (e.g. "5+0")
    :param rated: Whether the game is rated.
    :return: The challenge response (a dict).
    """
    session = berserk.TokenSession(api_token)
    client = berserk.Client(session=session)
    
    clock_limit, clock_increment = parse_time_control(time_control)
    
    # The challenge endpoint for a specific opponent is
    # POST /api/challenge/{id} with parameters such as rated, clock_limit, clock_increment.
    # Berserk exposes this via client.challenges.create(opponent, ...).
    response = client.challenges.create(
        opponent, 
        rated=rated,
        clock_limit=clock_limit,
        clock_increment=clock_increment,
    )
    return response

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: challenge_bot.py <YOUR_API_TOKEN> [opponent] [time_control] [rated]")
        sys.exit(1)
    
    token = sys.argv[1]
    # Optional parameters:
    opponent = sys.argv[2] if len(sys.argv) > 2 else "chessosity"
    time_control = sys.argv[3] if len(sys.argv) > 3 else "5+0"
    rated_arg = sys.argv[4].lower() if len(sys.argv) > 4 else "false"
    rated = True if rated_arg in ("true", "1", "yes") else False
    
    try:
        res = create_challenge_with_bot(token, opponent, time_control, rated)
        print("Challenge created successfully:")
        print(res)
    except Exception as e:
        print(f"Error creating challenge: {e}") 