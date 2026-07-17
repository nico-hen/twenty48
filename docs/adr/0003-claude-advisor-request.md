# How the ClaudeAdvisor asks Claude for a move

The `ClaudeAdvisor` sends the current board to the Messages API as the spec's
exact `null`-using JSON matrix, with a short system prompt stating the 2048 rules
and the goal (avoid game-over, maximise the chance of reaching 2048). The reply
is constrained with **structured outputs** to a fixed schema:

```
{ move: enum[LEFT, RIGHT, UP, DOWN], rationale: string }
```

The returned `move` is then validated against the board's actually-legal moves.
An illegal or no-op suggestion becomes a status-line message, never a crash —
the advisor's correctness never depends on the model behaving.

- **Model:** `claude-sonnet-5`, extended thinking **off** — chosen for
  interactive responsiveness over maximal hint quality (the H key should return
  in ~a second, not stall the game). The model id and thinking setting live in a
  single named constant in `advisor.py`; sharpening hints later (Opus, or
  thinking on) is a one-line change.
- **Rationale length** is enforced by the prompt, not the schema — structured
  outputs do not support `maxLength` on strings.

## Considered Options

- **Dynamic enum of only the legal moves** — rejected: it changes the schema
  every turn (losing schema caching), and local legal-move validation already
  guarantees we never act on an illegal suggestion.
- **Tool use with a strict enum param** — rejected: heavier machinery than a
  one-shot ask needs.
- **Plain text, parsed by us** — rejected: fragile.

## Consequences

- The fixed schema caches across turns.
- Move legality is guaranteed by our pure core, not by trusting the model.
- Swapping model or turning thinking on is a single-line change.
