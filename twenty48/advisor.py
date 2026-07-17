"""The swappable Advisor seam and its one Claude-backed implementation.

Given a Board, ``ClaudeAdvisor`` asks Claude for the best next Move and returns a
``Suggestion`` (a Move plus a short rationale) — or, on *any* failure, a
``Degraded`` result carrying a short status-line message. It **never throws into
the game loop** (ADR-0001): network errors, timeouts, refusals, a rejected
credential, a rate limit, or a suggestion that isn't a legal Move all become a
``Degraded`` and play continues.

The ``anthropic`` client is *injected*, not built here (that is the composition
root's job, #10, which builds it with a ~10s request timeout so a slow call
degrades rather than hanging the game loop — ADR-0001): this module depends only
on the small structural ``Client`` contract below, so it never imports
``anthropic`` and stays testable against a fake. The request shape follows
ADR-0003 — the Board is sent as the spec's
``null``-using matrix under a short rules-and-goal system prompt, and the reply
is constrained to a fixed schema with structured outputs.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from twenty48.board import Board, Move


@dataclass(frozen=True)
class ModelConfig:
    """The model id and thinking setting, in one place (ADR-0003).

    Sharpening hints later — a stronger model, or extended thinking on — is a
    one-line change here.
    """

    model: str
    thinking: dict[str, str]


# claude-sonnet-5 with extended thinking off: the H key should return in about a
# second, not stall the game (ADR-0003).
MODEL_CONFIG = ModelConfig(model="claude-sonnet-5", thinking={"type": "disabled"})

# A short reply is plenty for one Move plus a one-sentence rationale.
MAX_TOKENS = 256

# The fixed structured-output schema the reply is constrained to (ADR-0003). The
# enum names match the ``Move`` members. Rationale *brevity* is prompted, not
# schema-enforced — structured outputs cannot cap string length.
SUGGESTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "move": {"type": "string", "enum": ["LEFT", "RIGHT", "UP", "DOWN"]},
        "rationale": {"type": "string"},
    },
    "required": ["move", "rationale"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = (
    "You are advising a player of 2048 on a 4x4 board. The board arrives as a "
    "JSON matrix of rows; each cell is a tile's value (a power of two) or null "
    "for an empty cell. A move — LEFT, RIGHT, UP, or DOWN — slides every tile as "
    "far as it can go that way and merges equal neighbours. Recommend the single "
    "move that best avoids game-over and maximises the chance of reaching 2048. "
    "Choose a move that actually changes the board. Keep the rationale to one "
    "short sentence."
)

# Short status-line messages for each way the advice can degrade. A rejected
# credential and a rate limit are surfaced distinctly (ADR-0001): the first asks
# the player to re-authenticate, the second to retry.
_UNAVAILABLE = "Advisor unavailable — could not reach Claude."
_UNAUTHENTICATED = "Advisor unavailable — credential rejected; re-authenticate."
_RATE_LIMITED = "Advisor unavailable — rate limited; try again shortly."
_DECLINED = "Advisor declined to suggest a move."
_UNREADABLE = "Advisor returned an unreadable suggestion."
_INVALID = "Advisor suggested a move that isn't legal here."


@dataclass(frozen=True)
class Suggestion:
    """The Advisor's recommendation: a legal Move and a short rationale."""

    move: Move
    rationale: str


@dataclass(frozen=True)
class Degraded:
    """A failed request, reduced to a short status-line ``reason``. Never raised."""

    reason: str


# The Advisor's output: a Suggestion on success, a Degraded on any failure.
Advice = Suggestion | Degraded


@runtime_checkable
class Advisor(Protocol):
    """Recommends the best next Move for a Board. The game core depends on this,
    never on a concrete implementation (ADR-0001)."""

    def suggest(self, board: Board) -> Advice: ...


class _ResponseBlock(Protocol):
    @property
    def type(self) -> str: ...

    @property
    def text(self) -> str: ...


class _Response(Protocol):
    @property
    def stop_reason(self) -> str | None: ...

    @property
    def content(self) -> Sequence[_ResponseBlock]: ...


class _Messages(Protocol):
    def create(self, /, **request: Any) -> _Response: ...


class Client(Protocol):
    """The slice of ``anthropic.Anthropic`` the advisor calls. Injected, so this
    module never imports ``anthropic`` (ADR-0002). Members are read-only — the
    advisor only reads the reply — which keeps a plain fake structurally valid."""

    @property
    def messages(self) -> _Messages: ...


class ClaudeAdvisor:
    """Asks an injected Claude client for a Move, degrading on any failure."""

    def __init__(self, client: Client) -> None:
        self._client = client

    def suggest(self, board: Board) -> Advice:
        try:
            response = self._client.messages.create(**self._request(board))
        except Exception as error:  # never throws into the game loop (ADR-0001)
            return _degrade_for(error)
        return self._interpret(response, board)

    def _request(self, board: Board) -> dict[str, Any]:
        return {
            "model": MODEL_CONFIG.model,
            "thinking": MODEL_CONFIG.thinking,
            "max_tokens": MAX_TOKENS,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": json.dumps(board.as_grid())}],
            "output_config": {
                "format": {"type": "json_schema", "schema": SUGGESTION_SCHEMA}
            },
        }

    def _interpret(self, response: _Response, board: Board) -> Advice:
        if response.stop_reason == "refusal":
            return Degraded(_DECLINED)
        try:
            text = next(b.text for b in response.content if b.type == "text")
            payload = json.loads(text)
            move = Move[payload["move"]]
            rationale = str(payload["rationale"])
        except Exception:  # malformed, truncated, or off-schema reply
            return Degraded(_UNREADABLE)
        if move not in board.legal_moves():
            return Degraded(_INVALID)
        return Suggestion(move=move, rationale=rationale)


def _degrade_for(error: Exception) -> Degraded:
    """Map a client-call exception to a status-line message. Reads ``status_code``
    duck-typed so the module needn't import ``anthropic``'s error types."""
    status = getattr(error, "status_code", None)
    if status == 401:
        return Degraded(_UNAUTHENTICATED)
    if status == 429:
        return Degraded(_RATE_LIMITED)
    return Degraded(_UNAVAILABLE)
