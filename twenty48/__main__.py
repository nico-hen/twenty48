"""Composition root for the twenty48 game (see ADR-0002).

The one place that builds the concrete pieces and wires them together: a real
RNG, the seeded starting Board, the ``termios`` key-source, and ``stdout`` as the
writer, all handed to ``loop.run``. There is no Advisor yet (#10), so nothing
here reads the environment. This wiring is thin and verified by playing the game.
"""

import random
import sys
from typing import cast

from twenty48.board import Board, Rng
from twenty48.loop import run
from twenty48.ui import TerminalKeySource


def main() -> None:
    """Seed a starting Board and play a real game in the terminal."""
    # random.Random provides .random() and .randrange(stop) that the Rng protocol
    # needs, but its overloaded randrange signature doesn't match structurally; the
    # cast bridges that here, the one spot the concrete RNG meets the protocol.
    rng = cast(Rng, random.Random())
    board = Board.initial(rng)
    run(board, keys=TerminalKeySource(), writer=sys.stdout, rng=rng)


if __name__ == "__main__":
    main()
