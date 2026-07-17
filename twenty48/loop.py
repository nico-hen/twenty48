"""The turn cycle: wiring the pure Board through the ui (see ADR-0002).

``run`` is the game's highest, primary seam. Every side effect is injected — the
key-source, the writer, and the RNG — so a scripted key-source plus a capturing
writer drive whole-game behaviour deterministically. There is no Advisor yet
(#10): the hint key is recognised but only notes its own absence.
"""

from __future__ import annotations

from twenty48.board import Board, Move, Rng
from twenty48.ui import Command, KeySource, Writer, parse_key, render

WIN_MESSAGE = "You reached 2048! You win."
LOSE_MESSAGE = "No moves left — game over."
NO_HINT_MESSAGE = "No hint available yet."


def run(board: Board, *, keys: KeySource, writer: Writer, rng: Rng) -> Board:
    """Play from ``board`` until a win, a loss, or a quit; return the final Board.

    Each turn draws the Board, then either ends on a win/loss or reads one key.
    A Move that changes the Board is followed by a Spawn; a no-op Move is rejected
    with no Spawn. Q quits, H notes the missing Advisor, and any other key is
    ignored.
    """
    message = ""
    while True:
        if board.has_won():
            render(board, writer, message=WIN_MESSAGE)
            return board
        if board.is_stuck():
            render(board, writer, message=LOSE_MESSAGE)
            return board

        render(board, writer, message=message)
        message = ""

        action = parse_key(keys.read_key())
        if action is Command.QUIT:
            return board
        if action is Command.HINT:
            message = NO_HINT_MESSAGE
        elif isinstance(action, Move):
            moved = board.move(action)
            if moved != board:
                board = moved.spawn(rng)
