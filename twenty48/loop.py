"""The turn cycle: wiring the pure Board through the ui and Advisor (ADR-0002).

``run`` is the game's highest, primary seam. Every side effect is injected — the
key-source, the writer, the RNG, and the optional Advisor — so a scripted
key-source, a capturing writer, and a fake Advisor drive whole-game behaviour
deterministically.

The hint is synchronous and never blocks play (ADR-0001): pressing **H** repaints
the status line to "Asking Claude…", makes the call, then shows the Suggestion or
a one-line failure message. With no Advisor, H is a no-op that only notes hints
are disabled. The Advisor never throws into this loop, so nothing here catches.
"""

from __future__ import annotations

from twenty48.advisor import Advisor, Suggestion
from twenty48.board import Board, Move, Rng
from twenty48.ui import Command, KeySource, Writer, parse_key, render

WIN_MESSAGE = "You reached 2048! You win."
LOSE_MESSAGE = "No moves left — game over."
ASKING_MESSAGE = "Asking Claude…"
HINTS_DISABLED_MESSAGE = "Hints are disabled — no credential set."


def format_suggestion(suggestion: Suggestion) -> str:
    """The status line for a Suggestion: the Move name and its short rationale."""
    return f"Claude suggests {suggestion.move.name}: {suggestion.rationale}"


def run(
    board: Board,
    *,
    keys: KeySource,
    writer: Writer,
    rng: Rng,
    advisor: Advisor | None = None,
    message: str = "",
) -> Board:
    """Play from ``board`` until a win, a loss, or a quit; return the final Board.

    Each turn draws the Board, then either ends on a win/loss or reads one key.
    A Move that changes the Board is followed by a Spawn; a no-op Move is rejected
    with no Spawn. Q quits, H asks the Advisor for a hint (or notes its absence),
    and any other key is ignored. An optional ``message`` seeds the first frame's
    status line — used to surface the "hints disabled" notice past render's
    screen-clear, so a pre-``run`` ``print`` isn't wiped by the first frame.
    """
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
            message = _hint(board, writer, advisor)
        elif isinstance(action, Move):
            moved = board.move(action)
            if moved != board:
                board = moved.spawn(rng)


def _hint(board: Board, writer: Writer, advisor: Advisor | None) -> str:
    """Ask the Advisor for a Move, returning the status line to show next turn.

    With no Advisor, hints are disabled and this is a no-op notice. Otherwise the
    status line repaints to "Asking Claude…" before the (synchronous) call, whose
    result — a Suggestion or a Degraded reason — becomes the next status line.
    """
    if advisor is None:
        return HINTS_DISABLED_MESSAGE
    render(board, writer, message=ASKING_MESSAGE)
    advice = advisor.suggest(board)
    if isinstance(advice, Suggestion):
        return format_suggestion(advice)
    return advice.reason
