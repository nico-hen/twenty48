"""Tests for the turn cycle at its highest seam: ``loop.run``.

All I/O is injected — a scripted key-source and a capturing writer — and the RNG
is injected, so one seam drives whole-game behaviour deterministically. Render is
exercised indirectly through the captured output. ``run`` returns the final Board
so Move/Spawn outcomes can be asserted directly rather than scraped from text.
"""

import io

from twenty48.board import Board
from twenty48.loop import LOSE_MESSAGE, WIN_MESSAGE, run


class ScriptedKeys:
    """A deterministic key-source that yields a fixed list of raw keys in order."""

    def __init__(self, keys: list[str]) -> None:
        self._keys = list(keys)

    def read_key(self) -> str:
        return self._keys.pop(0)


class ScriptedRng:
    """A deterministic stand-in for the injected RNG (mirrors the Board tests)."""

    def __init__(self, *, randrange: list[int], random: list[float]) -> None:
        self._randrange = list(randrange)
        self._random = list(random)

    def randrange(self, stop: int) -> int:
        value = self._randrange.pop(0)
        assert 0 <= value < stop
        return value

    def random(self) -> float:
        return self._random.pop(0)


def no_rng() -> ScriptedRng:
    """An RNG for tests that expect no Spawn — any draw would raise IndexError."""
    return ScriptedRng(randrange=[], random=[])


def _tiles(board: Board) -> list[int]:
    return [cell for row in board.as_grid() for cell in row if cell is not None]


EMPTY_ROWS: list[list[int | None]] = [[None, None, None, None] for _ in range(3)]
TWO_TWOS: list[list[int | None]] = [[2, 2, None, None], *EMPTY_ROWS]
PACKED_LEFT: list[list[int | None]] = [[2, 4, None, None], *EMPTY_ROWS]


def test_a_move_that_changes_the_board_merges_then_spawns() -> None:
    # LEFT merges the two 2s into a 4; the spawn (random=2, first empty) adds a 2.
    board = Board.from_grid(TWO_TWOS)
    keys = ScriptedKeys(["a", "q"])
    rng = ScriptedRng(randrange=[0], random=[0.5])
    final = run(board, keys=keys, writer=io.StringIO(), rng=rng)
    assert final.as_grid()[0] == [4, 2, None, None]


def test_a_noop_move_is_rejected_with_no_spawn() -> None:
    # LEFT changes nothing on an already-packed row, so no tile is spawned. The
    # empty RNG would raise IndexError if a spawn were attempted.
    board = Board.from_grid(PACKED_LEFT)
    keys = ScriptedKeys(["a", "q"])
    final = run(board, keys=keys, writer=io.StringIO(), rng=no_rng())
    assert final == board


def test_quit_ends_the_game_immediately() -> None:
    board = Board.from_grid(PACKED_LEFT)
    writer = io.StringIO()
    final = run(board, keys=ScriptedKeys(["q"]), writer=writer, rng=no_rng())
    assert final == board
    assert "Controls" in writer.getvalue()


def test_reaching_2048_wins_and_announces_it() -> None:
    # LEFT merges the two 1024s into 2048; the loop then detects the win.
    board = Board.from_grid([[1024, 1024, None, None], *EMPTY_ROWS])
    writer = io.StringIO()
    final = run(
        board, keys=ScriptedKeys(["a"]), writer=writer, rng=ScriptedRng(randrange=[0], random=[0.5])
    )
    assert final.has_won()
    assert WIN_MESSAGE in writer.getvalue()


def test_a_stuck_board_loses_and_announces_it() -> None:
    # A checkerboard with no equal neighbours: no legal Move remains.
    stuck: list[list[int | None]] = [
        [2, 4, 2, 4],
        [4, 2, 4, 2],
        [2, 4, 2, 4],
        [4, 2, 4, 2],
    ]
    board = Board.from_grid(stuck)
    writer = io.StringIO()
    final = run(board, keys=ScriptedKeys([]), writer=writer, rng=no_rng())
    assert final == board
    assert LOSE_MESSAGE in writer.getvalue()


def test_a_hint_key_is_accepted_and_leaves_the_board_unchanged() -> None:
    # With no Advisor yet (#10), H is recognised but only notes its absence.
    board = Board.from_grid(PACKED_LEFT)
    writer = io.StringIO()
    final = run(
        board,
        keys=ScriptedKeys(["h", "q"]),
        writer=writer,
        rng=no_rng(),
    )
    assert final == board


def test_an_unrecognised_key_is_ignored() -> None:
    board = Board.from_grid(PACKED_LEFT)
    keys = ScriptedKeys(["x", "q"])
    final = run(board, keys=keys, writer=io.StringIO(), rng=no_rng())
    assert final == board


def test_successive_moves_each_spawn_a_tile() -> None:
    # Two changing moves in a row: each should add exactly one spawned tile.
    board = Board.from_grid([[2, None, None, 2], *EMPTY_ROWS])
    keys = ScriptedKeys(["a", "s", "q"])
    # LEFT merges to a single 4 (1 tile), spawn -> 2 tiles; DOWN moves, spawn -> 3.
    rng = ScriptedRng(randrange=[0, 0], random=[0.5, 0.5])
    final = run(board, keys=keys, writer=io.StringIO(), rng=rng)
    assert len(_tiles(final)) == 3
