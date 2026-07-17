"""Tests for the twenty48 package metadata and the credential choice.

The composition root ``main`` wires real terminal I/O and is verified by playing
the game (like the ``termios`` adapter), not unit-tested; the turn cycle it wires
is covered at the ``loop.run`` seam in ``test_loop.py``. The credential
*precedence* — the one bit of real logic in the root, and the thing ADR-0001 says
to audit — is factored into the pure ``select_credential`` and pinned here.
"""

import twenty48
from twenty48.__main__ import Credential, select_credential


def test_version_is_defined() -> None:
    assert twenty48.__version__ == "0.1.0"


def test_no_credential_disables_hints() -> None:
    assert select_credential({}) is None


def test_api_key_is_used_when_present() -> None:
    assert select_credential({"ANTHROPIC_API_KEY": "sk-ant-api-x"}) == (
        Credential.API_KEY,
        "sk-ant-api-x",
    )


def test_oauth_token_is_used_when_no_api_key() -> None:
    assert select_credential({"CLAUDE_CODE_OAUTH_TOKEN": "sk-ant-oat-x"}) == (
        Credential.OAUTH,
        "sk-ant-oat-x",
    )


def test_api_key_wins_when_both_are_set() -> None:
    selected = select_credential(
        {"ANTHROPIC_API_KEY": "sk-ant-api-x", "CLAUDE_CODE_OAUTH_TOKEN": "sk-ant-oat-x"}
    )
    assert selected == (Credential.API_KEY, "sk-ant-api-x")


def test_an_empty_api_key_falls_through_to_the_oauth_token() -> None:
    # An env var set to the empty string is treated as absent, not a credential.
    selected = select_credential(
        {"ANTHROPIC_API_KEY": "", "CLAUDE_CODE_OAUTH_TOKEN": "sk-ant-oat-x"}
    )
    assert selected == (Credential.OAUTH, "sk-ant-oat-x")
