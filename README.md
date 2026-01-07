# refree_upliance
Rock–Paper–Scissors–Plus Referee 
This project is a small conversational game referee built using Google ADK.
The bot runs a short game of Rock–Paper–Scissors–Plus against the user, enforces all rules, keeps track of state across turns, and clearly explains what happens in each round.

The goal of the project is correctness and clean agent design, not UI polish.

Game rules

The game is played for 3 rounds

Valid moves:

rock

paper

scissors

bomb (can be used once per player in the entire game)

bomb beats all other moves

bomb vs bomb results in a draw

Any invalid input wastes the round

After 3 rounds, the game ends automatically and the final result is shown

How the state is handled

Game state is modeled using a Python dataclass and is managed directly by ADK through state_schema.

The state tracks:

Number of rounds played

User score

Bot score

Whether the user has already used their bomb

Whether the bot has already used its bomb

Because the state is owned by ADK:

It persists across turns

No logic depends on prompt memory

Rules like “bomb only once” are enforced reliably

Tool design

The agent uses two explicit tools, as required.

check_player_move

This tool:

Cleans and validates the user’s input

Checks whether a bomb move is still allowed

Classifies invalid inputs so the round can be wasted correctly

This keeps intent understanding separate from game logic.

play_round

This tool:

Chooses the bot’s move

Resolves the round winner

Updates scores and round count

Mutates the shared game state

All game rules live in this tool, which keeps the behavior predictable and easy to reason about.

Architecture overview

The design intentionally keeps things simple:

Intent handling → check_player_move

Game logic → play_round

State management → ADK state_schema

Response generation → Agent instruction + LLM

Execution → CLI loop using Runner

Only a single agent is used.

Why Google ADK

The solution uses Google ADK primitives throughout:

Agent for defining behavior

FunctionTool for validation and game logic

Runner for execution

InMemorySessionService for session management

No databases, external APIs, or long-running services are used.

Tradeoffs

The bot’s move selection is randomized rather than strategic

The CLI interface is minimal by design

LLM-generated explanations may vary slightly between runs

These choices were made to keep the solution focused and readable.

What I would improve with more time

Smarter bot strategy

Structured round summaries instead of free-form text

Automated tests for the game logic

A simple web or terminal UI

How to run
pip install google-adk
python referee.py
