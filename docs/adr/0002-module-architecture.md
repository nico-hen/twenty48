# Module architecture: one flat package, layered by purity

The game is a single flat package, `twenty48`, split into five small modules
ordered by how far each sits from pure logic:

- `board.py` — the `Move` enum and the immutable `Board` value object. Pure, no
  I/O, no randomness of its own (RNG is injected). Holds the tested heart.
- `advisor.py` — the `Advisor` protocol and its one `ClaudeAdvisor`
  implementation. The only module that imports `anthropic`.
- `ui.py` — terminal rendering and key input, nothing else.
- `loop.py` — the turn cycle, wiring board + ui + advisor together.
- `__main__.py` — the composition root: the **only** place that reads
  environment variables, detects the credential, and builds the advisor.

Nothing above the `advisor` line knows Claude exists; nothing but `__main__`
touches the environment.

## Considered Options

- **`src/` layout** — rejected: marginally more correct for packaging, but adds
  ceremony out of proportion to a small terminal game.
- **`advisor/` as a package** — deferred: it stays a single module until a
  second advisor implementation actually exists (see ADR-0001). No speculative
  directory.

## Consequences

- The package is named `twenty48`, not `2048` — a module name cannot start with
  a digit (`import 2048` is a syntax error).
- Secret/credential handling is confined to `__main__.py`, so there is exactly
  one place to audit for "does this leak a key?"
- The test suite concentrates on `board.py`, which is pure and deterministic.
