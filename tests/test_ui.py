"""Tests for terminal rendering and key parsing.

The seams under test are the pure ``parse_key`` (raw key string -> Move /
Command / ``None``) and ``render`` (draws a Board to an injected writer,
exercised here through a capturing ``io.StringIO``). The raw ``termios``/``tty``
key adapter is deliberately not unit-tested; it is verified by running the game.
"""

import io

from twenty48.board import Board, Move
from twenty48.ui import Command, parse_key, render

SPEC_BEFORE: list[list[int | None]] = [
    [None, 8, 2, 2],
    [4, 2, None, 2],
    [None, None, None, None],
    [None, None, None, 2],
]


def test_wasd_keys_map_to_moves() -> None:
    assert parse_key("w") is Move.UP
    assert parse_key("a") is Move.LEFT
    assert parse_key("s") is Move.DOWN
    assert parse_key("d") is Move.RIGHT


def test_wasd_keys_are_case_insensitive() -> None:
    assert parse_key("W") is Move.UP
    assert parse_key("D") is Move.RIGHT


def test_arrow_escape_sequences_map_to_moves() -> None:
    assert parse_key("\x1b[A") is Move.UP
    assert parse_key("\x1b[B") is Move.DOWN
    assert parse_key("\x1b[C") is Move.RIGHT
    assert parse_key("\x1b[D") is Move.LEFT


def test_q_parses_as_quit_and_h_as_hint() -> None:
    assert parse_key("q") is Command.QUIT
    assert parse_key("Q") is Command.QUIT
    assert parse_key("h") is Command.HINT
    assert parse_key("H") is Command.HINT


def test_unrecognised_key_parses_to_none() -> None:
    assert parse_key("x") is None
    assert parse_key("\x1b") is None


def test_render_draws_every_tile_value() -> None:
    writer = io.StringIO()
    render(Board.from_grid(SPEC_BEFORE), writer)
    output = writer.getvalue()
    assert "8" in output
    assert "4" in output
    assert "2" in output


def test_render_shows_the_2048_tile_in_full() -> None:
    won: list[list[int | None]] = [
        [2048, None, None, None],
        [None, None, None, None],
        [None, None, None, None],
        [None, None, None, None],
    ]
    writer = io.StringIO()
    render(Board.from_grid(won), writer)
    assert "2048" in writer.getvalue()


def test_render_shows_the_controls_affordance_including_hint() -> None:
    writer = io.StringIO()
    render(Board.empty(), writer)
    output = writer.getvalue()
    assert "H" in output
    assert "Q" in output


def test_render_includes_a_message_when_given_one() -> None:
    writer = io.StringIO()
    render(Board.empty(), writer, message="You reached 2048! You win.")
    assert "You reached 2048" in writer.getvalue()
