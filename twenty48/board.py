"""The pure heart of the game: the ``Move`` enum and the immutable ``Board``.

No I/O, no ``anthropic``, and no randomness of its own — the RNG is injected
(see ADR-0002). Every transformation returns a new ``Board``; nothing here
mutates. An empty Cell is ``None``, matching the spec's JSON ``null``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol

BOARD_SIZE = 4
WINNING_TILE = 2048

# A spawned Tile is a 4 with this probability, else a 2 (the standard 2048 mix).
SPAWN_FOUR_PROBABILITY = 0.1

# The start state always seeds this many Tiles, each a 2 or 4 via Spawn.
INITIAL_TILES = 2

Grid = list[list[int | None]]
Row = tuple[int | None, ...]


class Rng(Protocol):
    """The slice of the RNG the Board depends on; ``random.Random`` satisfies it."""

    def random(self) -> float: ...

    def randrange(self, stop: int) -> int: ...


class Move(Enum):
    """A directional action that slides every Tile and Merges equal neighbours."""

    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()


@dataclass(frozen=True)
class Board:
    """A 4x4 grid of Cells, each empty (``None``) or holding a Tile value.

    Frozen and value-comparable: two Boards with the same Cells are equal, which
    is how a no-op Move is detected (``moved == board``).
    """

    rows: tuple[Row, ...]

    @classmethod
    def from_grid(cls, grid: Grid) -> Board:
        """Build a Board from a ``null``-using matrix (rows of ints / ``None``)."""
        return cls(tuple(tuple(row) for row in grid))

    @classmethod
    def empty(cls) -> Board:
        """An all-empty Board."""
        return cls(tuple((None,) * BOARD_SIZE for _ in range(BOARD_SIZE)))

    @classmethod
    def initial(cls, rng: Rng) -> Board:
        """The start state: INITIAL_TILES Spawns (each a 2 or 4) on an empty Board."""
        board = cls.empty()
        for _ in range(INITIAL_TILES):
            board = board.spawn(rng)
        return board

    def as_grid(self) -> Grid:
        """Render the spec's ``null``-using matrix view."""
        return [list(row) for row in self.rows]

    def move(self, direction: Move) -> Board:
        """Slide and Merge every Tile in ``direction``, returning a new Board.

        Each direction reduces to a leftward slide: rows are re-oriented so the
        target direction points left, slid, then oriented back. A no-op Move
        returns an equal Board, so callers detect it with ``moved == board``.
        """
        if direction is Move.LEFT:
            return Board(tuple(_slide_left(row) for row in self.rows))
        if direction is Move.RIGHT:
            return Board(tuple(_slide_left(row[::-1])[::-1] for row in self.rows))
        if direction is Move.UP:
            columns = zip(*self.rows, strict=True)
            slid = (_slide_left(column) for column in columns)
            return Board(tuple(zip(*slid, strict=True)))
        # DOWN: like UP, but each column is reversed so "down" points left.
        columns = zip(*self.rows, strict=True)
        slid = (_slide_left(column[::-1])[::-1] for column in columns)
        return Board(tuple(zip(*slid, strict=True)))

    def can_move(self, direction: Move) -> bool:
        """Whether a Move in ``direction`` would change the Board (a legal Move)."""
        return self.move(direction) != self

    def legal_moves(self) -> tuple[Move, ...]:
        """The directions that would change the Board, in enum order."""
        return tuple(direction for direction in Move if self.can_move(direction))

    def empty_cells(self) -> tuple[tuple[int, int], ...]:
        """Row-major coordinates of the empty Cells."""
        return tuple(
            (r, c)
            for r, row in enumerate(self.rows)
            for c, cell in enumerate(row)
            if cell is None
        )

    def has_won(self) -> bool:
        """Whether a winning Tile (``2048``) exists on the Board."""
        return any(cell == WINNING_TILE for row in self.rows for cell in row)

    def is_stuck(self) -> bool:
        """Whether no legal Move remains (the lose condition)."""
        return not self.legal_moves()

    def spawn(self, rng: Rng) -> Board:
        """Place a new Tile (a 2 or a 4) on a randomly chosen empty Cell."""
        value = 4 if rng.random() < SPAWN_FOUR_PROBABILITY else 2
        return self._with_tile_at_random(rng, value)

    def _with_tile_at_random(self, rng: Rng, value: int) -> Board:
        empties = self.empty_cells()
        if not empties:
            raise ValueError("cannot place a Tile on a full Board")
        row, col = empties[rng.randrange(len(empties))]
        grid = self.as_grid()
        grid[row][col] = value
        return Board.from_grid(grid)


def _slide_left(line: Row) -> Row:
    """Compress Tiles to the left and Merge equal neighbours (each Tile once)."""
    tiles = [cell for cell in line if cell is not None]
    merged: list[int | None] = []
    skip = False
    for i, tile in enumerate(tiles):
        if skip:
            skip = False
            continue
        if i + 1 < len(tiles) and tiles[i + 1] == tile:
            merged.append(tile * 2)
            skip = True
        else:
            merged.append(tile)
    merged.extend([None] * (BOARD_SIZE - len(merged)))
    return tuple(merged)
