"""Terminal rendering and key input — nothing else (see ADR-0002).

Two pure, tested seams: ``render`` draws a Board to an injected writer, and
``parse_key`` turns a raw key string into a Move, a Command, or ``None`` (an
unrecognised key). The raw ``termios``/``tty`` reader (``TerminalKeySource``) is
the one thin, isolated adapter here; it is verified by running the game, not
unit-tested, so all the terminal-specific fiddliness stays in one small place.
"""

from __future__ import annotations

import sys
from enum import Enum, auto
from typing import Protocol

from twenty48.board import Board, Move


class Writer(Protocol):
    """The slice of an output stream ``render`` needs; ``sys.stdout`` satisfies it."""

    def write(self, text: str, /) -> int: ...


class KeySource(Protocol):
    """A source of one keypress at a time; the loop reads through this seam."""

    def read_key(self) -> str: ...


class Command(Enum):
    """A non-Move key action: quit the game, or ask the Advisor for a hint."""

    QUIT = auto()
    HINT = auto()


# Single-letter keys are matched case-insensitively; arrows arrive as the raw
# ``ESC [ X`` sequence a terminal sends for each direction.
_LETTER_MOVES = {"w": Move.UP, "a": Move.LEFT, "s": Move.DOWN, "d": Move.RIGHT}
_ARROW_MOVES = {
    "\x1b[A": Move.UP,
    "\x1b[B": Move.DOWN,
    "\x1b[C": Move.RIGHT,
    "\x1b[D": Move.LEFT,
}

_CONTROLS = "Controls: WASD / arrow keys to move, H for a hint, Q to quit"

# Redraw in place each turn: clear the screen and home the cursor.
_CLEAR = "\x1b[2J\x1b[H"


def parse_key(key: str) -> Move | Command | None:
    """Interpret a raw key string, or return ``None`` if it means nothing."""
    if key in _ARROW_MOVES:
        return _ARROW_MOVES[key]
    lowered = key.lower()
    if lowered in _LETTER_MOVES:
        return _LETTER_MOVES[lowered]
    if lowered == "q":
        return Command.QUIT
    if lowered == "h":
        return Command.HINT
    return None


def render(board: Board, writer: Writer, *, message: str = "") -> None:
    """Draw ``board`` as a boxed 4x4 grid, then the message (if any) and controls."""
    writer.write(_CLEAR)
    writer.write(_frame(board))
    if message:
        writer.write(f"\n{message}\n")
    writer.write(f"\n{_CONTROLS}\n")


def _frame(board: Board) -> str:
    border = "+" + "+".join(["------"] * len(board.rows)) + "+\n"
    lines = [border]
    for row in board.rows:
        cells = "|".join(f" {_cell(value)} " for value in row)
        lines.append(f"|{cells}|\n")
        lines.append(border)
    return "".join(lines)


def _cell(value: int | None) -> str:
    """A tile value right-aligned to four columns, or blank for an empty Cell."""
    return f"{value:>4}" if value is not None else " " * 4


class TerminalKeySource:
    """Reads one keypress in raw mode via ``termios``/``tty``.

    The one impure adapter in this module: it flips the terminal into raw mode
    just long enough to read a single key (following an ``ESC`` with two more
    bytes so arrow keys arrive whole), then restores the previous mode. Kept
    deliberately tiny and verified by playing the game, not by unit tests.
    """

    def read_key(self) -> str:
        import termios
        import tty

        fd = sys.stdin.fileno()
        previous = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
            if key == "\x1b":
                key += sys.stdin.read(2)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, previous)
        return key
