#!/usr/bin/env python3
# ============================================================================
# PROTOTYPE — throwaway. Answers: "does a Python terminal TUI feel good for 2048?"
# Not production code. No tests, no error handling beyond runnability.
# Run:  python prototypes/terminal-python/game.py
# Controls: W/A/S/D or arrow keys to move, H for AI hint, Q to quit.
# ============================================================================
import random
import sys
import termios
import tty

SIZE = 4
WIN = 2048


# ---- core state machine ----------------------------------------------------
def new_board():
    b = [[None] * SIZE for _ in range(SIZE)]
    # Spec req 1: start with a random number of 2s at random cells.
    for _ in range(random.randint(2, 6)):
        spawn(b, only_two=True)
    return b


def empties(b):
    return [(r, c) for r in range(SIZE) for c in range(SIZE) if b[r][c] is None]


def spawn(b, only_two=False):
    cells = empties(b)
    if not cells:
        return False
    r, c = random.choice(cells)
    b[r][c] = 2 if only_two else random.choice([2, 2, 2, 4])  # 75% 2, 25% 4
    return True


def compress_merge(row):
    """Move + merge one row to the LEFT. Returns the new row."""
    vals = [v for v in row if v is not None]
    out, i = [], 0
    while i < len(vals):
        if i + 1 < len(vals) and vals[i] == vals[i + 1]:
            out.append(vals[i] * 2)
            i += 2
        else:
            out.append(vals[i])
            i += 1
    return out + [None] * (SIZE - len(out))


def move(b, direction):
    """direction in {'L','R','U','D'}. Returns (new_board, changed)."""
    rows = b
    if direction in ("U", "D"):
        rows = [list(col) for col in zip(*b)]  # transpose
    if direction in ("R", "D"):
        rows = [list(reversed(r)) for r in rows]

    moved = [compress_merge(r) for r in rows]

    if direction in ("R", "D"):
        moved = [list(reversed(r)) for r in moved]
    if direction in ("U", "D"):
        moved = [list(col) for col in zip(*moved)]

    changed = moved != b
    return [list(r) for r in moved], changed


def won(b):
    return any(v == WIN for row in b for v in row)


def lost(b):
    if empties(b):
        return False
    for d in "LRUD":
        _, changed = move(b, d)
        if changed:
            return False
    return True


# ---- AI suggestion (offline heuristic, no network / credentials) -----------
def score(b):
    """Reward empties + merge potential. Crude but works for a hint."""
    s = len(empties(b)) * 10
    for row in b:
        for i in range(SIZE - 1):
            if row[i] and row[i] == row[i + 1]:
                s += row[i]
    for col in zip(*b):
        for i in range(SIZE - 1):
            if col[i] and col[i] == col[i + 1]:
                s += col[i]
    return s


def suggest(b):
    best, best_s = None, -1
    for d in "LRUD":
        nb, changed = move(b, d)
        if changed and score(nb) > best_s:
            best, best_s = d, score(nb)
    return {"L": "Left", "R": "Right", "U": "Up", "D": "Down"}.get(best, "no move")


# ---- rendering + input -----------------------------------------------------
def render(b, msg=""):
    print("\033[2J\033[H", end="")  # clear
    print("  2048 — PROTOTYPE (Python TUI)\n")
    for row in b:
        print("  +------+------+------+------+")
        print("  " + "".join(f"|{('' if v is None else v):^6}" for v in row) + "|")
    print("  +------+------+------+------+")
    print(f"\n  {msg}")
    print("  [WASD/arrows] move  [H] AI hint  [Q] quit")


def read_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":  # arrow escape sequence
            ch += sys.stdin.read(2)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch


KEYMAP = {
    "a": "L", "d": "R", "w": "U", "s": "D",
    "\x1b[D": "L", "\x1b[C": "R", "\x1b[A": "U", "\x1b[B": "D",
}


def main():
    b = new_board()
    msg = ""
    while True:
        render(b, msg)
        msg = ""
        if won(b):
            print("\n  🎉 You reached 2048! (Q to quit)")
        elif lost(b):
            print("\n  💀 No moves left. Game over. (Q to quit)")

        key = read_key().lower()
        if key == "q":
            print("\033[2J\033[H", end="")
            return
        if key == "h":
            msg = f"AI suggests: {suggest(b)}"
            continue
        if key in KEYMAP:
            nb, changed = move(b, KEYMAP[key])
            if changed:
                b = nb
                spawn(b)  # req 5: new 2 or 4 after a valid move


if __name__ == "__main__":
    main()
