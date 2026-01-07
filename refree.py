# upliance.ai – Rock–Paper–Scissors–Plus Referee
# Google ADK based conversational agent
# Install: pip install google-adk
# Run: python referee.py

import random
import re
from dataclasses import dataclass
from typing import Dict, Any, Annotated

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool


# -----------------------------
# Persistent Game State
# -----------------------------
@dataclass
class RPSGameState:
    round_index: int = 0
    user_points: int = 0
    bot_points: int = 0
    user_used_bomb: bool = False
    bot_used_bomb: bool = False


# -----------------------------
# Tool: Parse & Validate Move
# -----------------------------
def check_player_move(
    state: Annotated[RPSGameState, "Shared game state"],
    raw_input: str
) -> Dict[str, Any]:
    cleaned = re.sub(r"[^a-zA-Z]", "", raw_input).lower().strip()

    if cleaned in ("rock", "paper", "scissors"):
        return {"ok": True, "move": cleaned, "bomb": False}

    if cleaned == "bomb" and not state.user_used_bomb:
        return {"ok": True, "move": "bomb", "bomb": True}

    # Anything else is treated as invalid and wastes the round
    return {"ok": False, "move": "invalid", "bomb": False}


# -----------------------------
# Tool: Play & Resolve Round
# -----------------------------
def play_round(
    state: Annotated[RPSGameState, "Shared game state"],
    player_move: str,
    bomb_used: bool
) -> Dict[str, Any]:

    if state.round_index >= 3:
        return {"note": "Match already finished."}

    # Decide bot move
    if not state.bot_used_bomb and random.random() < 0.3:
        bot_move = "bomb"
        state.bot_used_bomb = True
    else:
        bot_move = random.choice(["rock", "paper", "scissors"])

    if bomb_used:
        state.user_used_bomb = True

    # Determine winner
    if player_move == "invalid":
        result = "bot"
    elif player_move == bot_move:
        result = "draw"
    elif player_move == "bomb" or bot_move == "bomb":
        if player_move == bot_move == "bomb":
            result = "draw"
        elif player_move == "bomb":
            result = "user"
        else:
            result = "bot"
    else:
        win_map = {
            "rock": "scissors",
            "scissors": "paper",
            "paper": "rock"
        }
        result = "user" if win_map[player_move] == bot_move else "bot"

    # Update counters
    state.round_index += 1
    if result == "user":
        state.user_points += 1
    elif result == "bot":
        state.bot_points += 1

    return {
        "round": state.round_index,
        "user_move": player_move,
        "bot_move": bot_move,
        "winner": result,
        "score": f"User {state.user_points} – Bot {state.bot_points}",
        "finished": state.round_index == 3
    }


# -----------------------------
# Agent Definition
# -----------------------------
referee_agent = Agent(
    name="RPSPlusReferee",
    model=LiteLlm("gemini-2.0-flash-exp"),
    instruction="""
You are the referee for a Rock–Paper–Scissors–Plus game.

Flow:
1. Validate the player's input using the validation tool.
2. Resolve the round using the game logic tool.
3. Clearly explain:
   - Round number
   - Moves played
   - Round winner
   - Current score
4. After three rounds, announce the final outcome and stop.
""",
    tools=[
        FunctionTool(check_player_move),
        FunctionTool(play_round),
    ],
)

# Let ADK manage state lifecycle
referee_agent.state_schema = RPSGameState


# -----------------------------
# Command-Line Game Loop
# -----------------------------
def main():
    runner = Runner(referee_agent)
    session_store = InMemorySessionService()
    session_id = session_store.new_session()

    print(
        "Rock–Paper–Scissors–Plus\n"
        "- Best of 3 rounds\n"
        "- Moves: rock, paper, scissors, bomb (once per player)\n"
        "- Bomb defeats everything; bomb vs bomb is a draw\n"
        "- Invalid input costs you the round\n"
    )

    while True:
        player_input = input("Your move: ").strip()

        events = runner.run_sync(
            session_id=session_id,
            contents=[{"role": "user", "parts": [player_input]}],
        )

        for evt in events:
            for part in evt.get("parts", []):
                if "text" in part:
                    print(part["text"])

        # Check ADK-managed state
        session = session_store.get_session(session_id)
        game_state: RPSGameState = session.state

        if game_state.round_index >= 3:
            print("\nFinal Score:")
            if game_state.user_points > game_state.bot_points:
                print("🎉 You win the match!")
            elif game_state.bot_points > game_state.user_points:
                print("🤖 Bot wins the match!")
            else:
                print("🤝 The match ends in a draw.")
            break


if __name__ == "__main__":
    main()
