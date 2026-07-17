"""Composition root for the twenty48 game (see ADR-0002).

The one place that builds the concrete pieces and wires them together: a real
RNG, the seeded starting Board, the ``termios`` key-source, ``stdout`` as the
writer, and — when a credential is present — the Claude-backed Advisor.

This is also the **only** place that reads the environment and touches secrets
(ADR-0001), so there is exactly one spot to audit for credential handling.
Precedence follows ADR-0001 and research note #4: ``ANTHROPIC_API_KEY`` wins (the
SDK sends it as ``x-api-key``); otherwise ``CLAUDE_CODE_OAUTH_TOKEN`` is sent as
``Authorization: Bearer`` plus the ``anthropic-beta: oauth-2025-04-20`` header.
With neither set, one startup notice prints and hints are disabled — the game is
fully playable and H is a no-op. This wiring is thin and verified by playing; the
credential *choice* is factored into the pure ``select_credential`` so it can be.
"""

from __future__ import annotations

import os
import random
import sys
from collections.abc import Mapping
from enum import Enum, auto
from typing import cast

from twenty48.advisor import Advisor, ClaudeAdvisor, Client
from twenty48.board import Board, Rng
from twenty48.loop import run
from twenty48.ui import TerminalKeySource

# A slow hint should degrade to a status-line message, not hang the turn-based
# loop, so the injected client carries a bounded request timeout (ADR-0001).
REQUEST_TIMEOUT_SECONDS = 10.0

# The OAuth beta header for a CLAUDE_CODE_OAUTH_TOKEN. Harmless where unneeded and
# future-proof against endpoint changes (research note #4).
_OAUTH_BETA_HEADER = {"anthropic-beta": "oauth-2025-04-20"}

_HINTS_DISABLED_NOTICE = (
    "Hints are disabled: set ANTHROPIC_API_KEY or CLAUDE_CODE_OAUTH_TOKEN to "
    "enable Claude hints. The game is fully playable without them."
)


class Credential(Enum):
    """Which credential the game found, and thus how the client authenticates.

    ``API_KEY`` is sent as ``x-api-key``; ``OAUTH`` as ``Authorization: Bearer``
    plus the OAuth beta header (ADR-0001).
    """

    API_KEY = auto()
    OAUTH = auto()


def select_credential(env: Mapping[str, str]) -> tuple[Credential, str] | None:
    """Pick the credential from ``env``, or ``None`` if neither is set.

    ``ANTHROPIC_API_KEY`` takes precedence over ``CLAUDE_CODE_OAUTH_TOKEN`` so the
    two are never combined on one client (which would send both auth headers and
    be rejected). Pure and env-in-hand, so precedence is unit-testable.
    """
    api_key = env.get("ANTHROPIC_API_KEY")
    if api_key:
        return (Credential.API_KEY, api_key)
    oauth_token = env.get("CLAUDE_CODE_OAUTH_TOKEN")
    if oauth_token:
        return (Credential.OAUTH, oauth_token)
    return None


def build_advisor(env: Mapping[str, str] = os.environ) -> Advisor | None:
    """Detect a credential and build the Claude Advisor, or ``None`` if neither is set.

    ``anthropic`` is imported only once a credential is found, so the
    no-credential game never depends on the SDK being installed.
    """
    selected = select_credential(env)
    if selected is None:
        return None
    kind, token = selected

    import anthropic

    if kind is Credential.API_KEY:
        client = anthropic.Anthropic(api_key=token, timeout=REQUEST_TIMEOUT_SECONDS)
    else:
        client = anthropic.Anthropic(
            auth_token=token,
            default_headers=_OAUTH_BETA_HEADER,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    # anthropic.Anthropic satisfies the advisor's structural Client contract (it
    # exposes messages.create); the cast bridges the nominal gap, mirroring the
    # RNG cast below — this is the one spot the concrete SDK meets the protocol.
    return ClaudeAdvisor(cast(Client, client))


def main() -> None:
    """Seed a starting Board and play a real game in the terminal."""
    advisor = build_advisor()
    # With no credential, seed the first frame's status line with the notice (a
    # pre-run print would be wiped by render's screen-clear on the first frame).
    notice = _HINTS_DISABLED_NOTICE if advisor is None else ""

    # random.Random provides .random() and .randrange(stop) that the Rng protocol
    # needs, but its overloaded randrange signature doesn't match structurally; the
    # cast bridges that here, the one spot the concrete RNG meets the protocol.
    rng = cast(Rng, random.Random())
    board = Board.initial(rng)
    run(
        board,
        keys=TerminalKeySource(),
        writer=sys.stdout,
        rng=rng,
        advisor=advisor,
        message=notice,
    )


if __name__ == "__main__":
    main()
