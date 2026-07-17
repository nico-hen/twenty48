# 2048

A terminal-based 2048 game with an AI-backed move recommender. The game core is
pure and deterministic; recommending a move is a separate, swappable concern.

## Language

### Game

**Board**:
The 4×4 grid the game is played on. Composed of Cells.

**Cell**:
One position on the Board. Either empty or holding a single Tile.

**Tile**:
A numbered piece on a Cell; its value is a power of two.
_Avoid_: block, number, piece.

**Spawn**:
Placing a new Tile (a 2 or a 4) on a randomly chosen empty Cell — at game start
and after every Move that changes the Board.

**Move**:
A directional action — Left, Right, Up, or Down — that slides every Tile as far
as it can go in that direction and Merges equal neighbours. A Move that changes
nothing is not a valid Move (no Spawn follows it).

**Merge**:
Combining two equal, adjacent Tiles into one Tile of double value during a Move.
Each Tile takes part in at most one Merge per Move.

### Advising

**Advisor**:
The component that, on request, recommends the best next Move for the current
Board. A swappable seam: the game core depends on the Advisor contract, never on
a concrete implementation. The only implementation for now is Claude-backed.
_Avoid_: AI, hint engine, bot, solver.

**Suggestion**:
The Advisor's output — a recommended Move for the current Board, optionally with
a short rationale.
_Avoid_: hint (reserve "hint" for the on-screen affordance / key, not the concept).
