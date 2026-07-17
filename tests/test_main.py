"""Tests for the twenty48 package metadata.

The composition root ``main`` wires real terminal I/O and is verified by playing
the game (like the ``termios`` adapter), not unit-tested; the turn cycle it wires
is covered at the ``loop.run`` seam in ``test_loop.py``.
"""

import twenty48


def test_version_is_defined() -> None:
    assert twenty48.__version__ == "0.1.0"
