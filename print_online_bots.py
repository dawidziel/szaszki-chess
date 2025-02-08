#!/usr/bin/env python3
import sys
import berserk
from config import lichess_token

def print_online_bots(api_token: str, limit: int | None = None) -> None:
    """
    Print available bots (online) to the terminal using Lichess Bot Online API.
    This calls the /api/bot/online endpoint via the berserk client.

    :param api_token: Your Lichess API token.
    :param limit: Optional limit for the number of bots (parameter 'nb').
    """
    # Create a session with your token
    session = berserk.TokenSession(api_token)
    client = berserk.Client(session=session)

    # Get the online bots (each bot is returned as a dict with user details)
    online_bots = client.bots.get_online_bots(limit)

    # Convert the iterator into a list so we can check if there are any bots
    online_bots = list(online_bots)
    if not online_bots:
        print("No bots online.")
        return

    print("Online Bots:")
    for bot in online_bots:
        # Assuming the bot data has keys: id, username, and possibly title.
        bot_id = bot.get("id", "N/A")
        username = bot.get("username", bot_id)
        title = bot.get("title", "")
        print(f" - {username} (ID: {bot_id}) {('- ' + title) if title else ''}")

if __name__ == "__main__":
    token = lichess_token

    print_online_bots(token)