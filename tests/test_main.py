"""Tests for the twenty48 package skeleton and entry point."""

import pytest

import twenty48
from twenty48.__main__ import main


def test_version_is_defined() -> None:
    assert twenty48.__version__ == "0.1.0"


def test_main_prints_placeholder(capsys: pytest.CaptureFixture[str]) -> None:
    main()
    assert "twenty48" in capsys.readouterr().out
