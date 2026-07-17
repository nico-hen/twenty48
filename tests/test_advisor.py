"""Tests for the ClaudeAdvisor behind the Advisor seam.

The advisor is exercised in isolation against an injected *fake* ``anthropic``
client — no network, no real SDK. Two things are pinned: the request the advisor
builds (model/thinking constant, board-as-``null``-matrix, structured-output
schema), and that *every* failure mode degrades rather than raising into the
caller (ADR-0001, ADR-0003).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from twenty48.advisor import (
    MODEL_CONFIG,
    SUGGESTION_SCHEMA,
    ClaudeAdvisor,
    Degraded,
    Suggestion,
)
from twenty48.board import Board, Move

# A board already packed to the left: LEFT is a no-op, RIGHT and DOWN are legal,
# UP is illegal. Lets us drive both "legal move" and "illegal/no-op" cases.
PACKED_LEFT: list[list[int | None]] = [
    [2, 4, None, None],
    [None, None, None, None],
    [None, None, None, None],
    [None, None, None, None],
]


@dataclass
class FakeBlock:
    """A stand-in for an ``anthropic`` content block."""

    type: str
    text: str


@dataclass
class FakeResponse:
    """A stand-in for the Messages API response the advisor reads."""

    content: list[FakeBlock]
    stop_reason: str | None = "end_turn"


class FakeMessages:
    """Records the request and returns a canned response (or raises a canned error)."""

    def __init__(
        self, response: FakeResponse | None = None, error: Exception | None = None
    ) -> None:
        self._response = response
        self._error = error
        self.requests: list[dict[str, Any]] = []

    def create(self, **request: Any) -> FakeResponse:
        self.requests.append(request)
        if self._error is not None:
            raise self._error
        assert self._response is not None
        return self._response


@dataclass
class FakeClient:
    """A stand-in for ``anthropic.Anthropic`` — just enough for the advisor."""

    messages: FakeMessages


def _reply(move: str, rationale: str = "keeps the board open") -> FakeResponse:
    """A well-formed structured-output reply naming ``move``."""
    return FakeResponse(
        content=[FakeBlock("text", json.dumps({"move": move, "rationale": rationale}))]
    )


def _advisor_returning(response: FakeResponse) -> tuple[ClaudeAdvisor, FakeMessages]:
    messages = FakeMessages(response=response)
    return ClaudeAdvisor(FakeClient(messages)), messages


def _advisor_raising(error: Exception) -> ClaudeAdvisor:
    return ClaudeAdvisor(FakeClient(FakeMessages(error=error)))


# --- Happy path -------------------------------------------------------------


def test_suggest_returns_the_models_move_and_rationale() -> None:
    advisor, _ = _advisor_returning(_reply("RIGHT", "merges the pair"))
    advice = advisor.suggest(Board.from_grid(PACKED_LEFT))
    assert advice == Suggestion(move=Move.RIGHT, rationale="merges the pair")


# --- The request the advisor builds ----------------------------------------


def test_request_uses_the_model_and_thinking_constant() -> None:
    advisor, messages = _advisor_returning(_reply("RIGHT"))
    advisor.suggest(Board.from_grid(PACKED_LEFT))
    (request,) = messages.requests
    assert request["model"] == MODEL_CONFIG.model
    assert request["thinking"] == MODEL_CONFIG.thinking


def test_request_sends_the_board_as_the_spec_null_matrix() -> None:
    advisor, messages = _advisor_returning(_reply("RIGHT"))
    board = Board.from_grid(PACKED_LEFT)
    advisor.suggest(board)
    (request,) = messages.requests
    (message,) = request["messages"]
    assert message["role"] == "user"
    assert json.loads(message["content"]) == board.as_grid()


def test_request_constrains_the_reply_to_the_fixed_schema() -> None:
    advisor, messages = _advisor_returning(_reply("RIGHT"))
    advisor.suggest(Board.from_grid(PACKED_LEFT))
    (request,) = messages.requests
    assert request["output_config"] == {
        "format": {"type": "json_schema", "schema": SUGGESTION_SCHEMA}
    }


# --- Illegal / no-op suggestions become an "invalid suggestion" degrade -----


def test_an_illegal_move_becomes_an_invalid_suggestion() -> None:
    # UP does not change PACKED_LEFT, so it is not a legal Move.
    advisor, _ = _advisor_returning(_reply("UP"))
    advice = advisor.suggest(Board.from_grid(PACKED_LEFT))
    assert isinstance(advice, Degraded)


def test_a_noop_move_becomes_an_invalid_suggestion() -> None:
    # LEFT is a no-op on the already-packed board (no Spawn would follow).
    advisor, _ = _advisor_returning(_reply("LEFT"))
    advice = advisor.suggest(Board.from_grid(PACKED_LEFT))
    assert isinstance(advice, Degraded)


# --- Every failure degrades; the advisor never raises into its caller -------


def test_a_network_error_degrades() -> None:
    advice = _advisor_raising(ConnectionError("no route to host")).suggest(
        Board.from_grid(PACKED_LEFT)
    )
    assert isinstance(advice, Degraded)


def test_a_timeout_degrades() -> None:
    advice = _advisor_raising(TimeoutError("timed out")).suggest(Board.from_grid(PACKED_LEFT))
    assert isinstance(advice, Degraded)


class _HttpError(Exception):
    """A stand-in for an ``anthropic`` API error carrying an HTTP status code."""

    def __init__(self, status_code: int) -> None:
        super().__init__(f"HTTP {status_code}")
        self.status_code = status_code


def test_an_authentication_failure_degrades() -> None:
    advice = _advisor_raising(_HttpError(401)).suggest(Board.from_grid(PACKED_LEFT))
    assert isinstance(advice, Degraded)


def test_a_rate_limit_degrades() -> None:
    advice = _advisor_raising(_HttpError(429)).suggest(Board.from_grid(PACKED_LEFT))
    assert isinstance(advice, Degraded)


def test_a_refusal_degrades() -> None:
    refusal = FakeResponse(content=[], stop_reason="refusal")
    advisor, _ = _advisor_returning(refusal)
    advice = advisor.suggest(Board.from_grid(PACKED_LEFT))
    assert isinstance(advice, Degraded)


def test_an_unreadable_reply_degrades() -> None:
    garbled = FakeResponse(content=[FakeBlock("text", "not json at all")])
    advisor, _ = _advisor_returning(garbled)
    advice = advisor.suggest(Board.from_grid(PACKED_LEFT))
    assert isinstance(advice, Degraded)


def test_a_reply_missing_the_move_degrades() -> None:
    no_move = FakeResponse(content=[FakeBlock("text", json.dumps({"rationale": "hmm"}))])
    advisor, _ = _advisor_returning(no_move)
    advice = advisor.suggest(Board.from_grid(PACKED_LEFT))
    assert isinstance(advice, Degraded)


def test_an_unexpected_error_degrades_rather_than_raising() -> None:
    advice = _advisor_raising(RuntimeError("boom")).suggest(Board.from_grid(PACKED_LEFT))
    assert isinstance(advice, Degraded)


# Distinct failures should carry distinct status-line messages, so the player
# can tell "rate limited, retry" from "re-authenticate".
def test_degrade_reasons_distinguish_the_failure() -> None:
    board = Board.from_grid(PACKED_LEFT)
    rate_limited = _advisor_raising(_HttpError(429)).suggest(board)
    unauthenticated = _advisor_raising(_HttpError(401)).suggest(board)
    assert isinstance(rate_limited, Degraded)
    assert isinstance(unauthenticated, Degraded)
    assert rate_limited.reason != unauthenticated.reason
