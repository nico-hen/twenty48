"""Tests for the pure Board core and Move enum.

The seams under test are the public ``Board`` interface: grid round-trip,
the four Moves (pinned to the worked examples in ``2048.md``), no-op
detection, read-only queries, and RNG-injected Spawn / start state.
"""

from twenty48.board import Board, Move

# The worked before-board from 2048.md, reused as the input for the Left, Right
# and Up golden fixtures (each after-board is copied verbatim from the spec).
SPEC_BEFORE: list[list[int | None]] = [
    [None, 8, 2, 2],
    [4, 2, None, 2],
    [None, None, None, None],
    [None, None, None, 2],
]


def test_move_has_the_four_directions() -> None:
    assert {m.name for m in Move} == {"LEFT", "RIGHT", "UP", "DOWN"}


def test_move_left_matches_spec_golden() -> None:
    after = Board.from_grid(SPEC_BEFORE).move(Move.LEFT).as_grid()
    assert after == [
        [8, 4, None, None],
        [4, 4, None, None],
        [None, None, None, None],
        [2, None, None, None],
    ]


def test_move_right_matches_spec_golden() -> None:
    after = Board.from_grid(SPEC_BEFORE).move(Move.RIGHT).as_grid()
    assert after == [
        [None, None, 8, 4],
        [None, None, 4, 4],
        [None, None, None, None],
        [None, None, None, 2],
    ]


def test_move_up_matches_spec_golden() -> None:
    after = Board.from_grid(SPEC_BEFORE).move(Move.UP).as_grid()
    assert after == [
        [4, 8, 2, 4],
        [None, 2, None, 2],
        [None, None, None, None],
        [None, None, None, None],
    ]


def test_move_down_matches_hand_worked_golden() -> None:
    # Down is not worked in 2048.md; this after-board is derived independently by
    # reversing each column, sliding-and-merging left, and reversing back.
    after = Board.from_grid(SPEC_BEFORE).move(Move.DOWN).as_grid()
    assert after == [
        [None, None, None, None],
        [None, None, None, None],
        [None, 8, None, 2],
        [4, 2, 2, 4],
    ]


def test_each_tile_merges_at_most_once_per_move() -> None:
    # A full row of equal Tiles yields two merges, never one triple-merge.
    assert Board.from_grid(
        [[2, 2, 2, 2], [4, 4, 4, 4], [None] * 4, [None] * 4]
    ).move(Move.LEFT).as_grid() == [
        [4, 4, None, None],
        [8, 8, None, None],
        [None, None, None, None],
        [None, None, None, None],
    ]


def test_a_freshly_merged_tile_does_not_merge_again_this_move() -> None:
    # [2,2,4] -> the merged 4 must not immediately re-merge with the trailing 4.
    assert Board.from_grid(
        [[2, 2, 4, None], [None] * 4, [None] * 4, [None] * 4]
    ).move(Move.LEFT).as_grid()[0] == [4, 4, None, None]


# A board already packed to the left: sliding LEFT changes nothing.
PACKED_LEFT: list[list[int | None]] = [
    [2, 4, None, None],
    [None, None, None, None],
    [None, None, None, None],
    [None, None, None, None],
]

# The spec's "no more moves" lose board — no equal neighbours in any direction.
STUCK: list[list[int | None]] = [
    [2, 4, 2, 4],
    [4, 2, 4, 2],
    [2, 4, 2, 4],
    [4, 2, 4, 2],
]

# The spec's win board — a 2048 Tile exists.
WON: list[list[int | None]] = [
    [4, None, None, 2],
    [2048, None, None, None],
    [4, 2, None, None],
    [4, None, None, None],
]


def test_noop_move_returns_an_equal_board() -> None:
    board = Board.from_grid(PACKED_LEFT)
    assert board.move(Move.LEFT) == board


def test_can_move_is_false_for_a_noop_direction() -> None:
    assert Board.from_grid(PACKED_LEFT).can_move(Move.LEFT) is False


def test_can_move_is_true_for_a_changing_direction() -> None:
    assert Board.from_grid(PACKED_LEFT).can_move(Move.RIGHT) is True


def test_legal_moves_lists_only_changing_directions() -> None:
    legal = set(Board.from_grid(PACKED_LEFT).legal_moves())
    assert legal == {Move.RIGHT, Move.DOWN}


def test_empty_cells_are_row_major_coordinates() -> None:
    assert Board.from_grid(SPEC_BEFORE).empty_cells() == (
        (0, 0),
        (1, 2),
        (2, 0),
        (2, 1),
        (2, 2),
        (2, 3),
        (3, 0),
        (3, 1),
        (3, 2),
    )


def test_has_won_detects_the_2048_tile() -> None:
    assert Board.from_grid(WON).has_won() is True
    assert Board.from_grid(SPEC_BEFORE).has_won() is False


def test_is_stuck_when_no_legal_move_remains() -> None:
    assert Board.from_grid(STUCK).is_stuck() is True
    assert Board.from_grid(SPEC_BEFORE).is_stuck() is False


class ScriptedRng:
    """A deterministic stand-in for the injected RNG, returning scripted draws."""

    def __init__(self, *, randrange: list[int], random: list[float]) -> None:
        self._randrange = list(randrange)
        self._random = list(random)

    def randrange(self, stop: int) -> int:
        value = self._randrange.pop(0)
        assert 0 <= value < stop
        return value

    def random(self) -> float:
        return self._random.pop(0)


def _tiles(board: Board) -> list[int]:
    return [cell for row in board.as_grid() for cell in row if cell is not None]


EMPTY_GRID: list[list[int | None]] = [[None] * 4 for _ in range(4)]

# Full but for the last two Cells — two empties, at (3, 2) and (3, 3).
NEAR_FULL: list[list[int | None]] = [
    [2, 4, 2, 4],
    [4, 2, 4, 2],
    [2, 4, 2, 4],
    [4, 2, None, None],
]


def test_spawn_places_a_tile_on_the_rng_chosen_empty_cell() -> None:
    board = Board.from_grid(NEAR_FULL)
    # Two empties (row-major): (3, 2) then (3, 3); randrange picks index 1.
    spawned = board.spawn(ScriptedRng(randrange=[1], random=[0.5]))
    assert spawned.as_grid()[3] == [4, 2, None, 2]


def test_spawn_is_immutable() -> None:
    board = Board.from_grid(EMPTY_GRID)
    board.spawn(ScriptedRng(randrange=[0], random=[0.5]))
    assert board.empty_cells() == tuple((r, c) for r in range(4) for c in range(4))


def test_spawn_yields_a_four_below_the_probability_and_a_two_otherwise() -> None:
    board = Board.from_grid(EMPTY_GRID)
    four = board.spawn(ScriptedRng(randrange=[0], random=[0.05]))
    two = board.spawn(ScriptedRng(randrange=[0], random=[0.5]))
    assert _tiles(four) == [4]
    assert _tiles(two) == [2]


def test_initial_places_exactly_two_starting_tiles() -> None:
    # Two Spawns on an empty Board; each draws a value then a cell.
    board = Board.initial(ScriptedRng(randrange=[0, 0], random=[0.5, 0.5]))
    assert len(_tiles(board)) == 2


def test_initial_tiles_follow_the_two_four_distribution() -> None:
    # First Spawn draws 0.05 (< 0.1) -> a 4; second draws 0.5 -> a 2.
    board = Board.initial(ScriptedRng(randrange=[0, 0], random=[0.05, 0.5]))
    assert sorted(_tiles(board)) == [2, 4]


def test_from_grid_as_grid_round_trips_with_nulls() -> None:
    grid: list[list[int | None]] = [
        [None, 8, 2, 2],
        [4, 2, None, 2],
        [None, None, None, None],
        [None, None, None, 2],
    ]
    assert Board.from_grid(grid).as_grid() == grid
