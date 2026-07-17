# twenty48

A terminal-based [2048](https://play2048.co) game with an optional,
Claude-backed move Advisor. The game core is pure and deterministic; asking
Claude for a hint is a separate, swappable concern that never gets in the way of
playing.

## Quick start

Zero configuration — clone, set up, play:

```sh
git clone git@github.com:nico-hen/2048.git
cd 2048
task setup   # create the virtualenv and install the package
task run     # play
```

Requires Python ≥ 3.11 and [Task](https://taskfile.dev). The game is fully
playable with no credentials; hints are optional (see below).

> Terminal only, Unix-only: input uses `termios`, so Linux and macOS work;
> Windows is not supported.

## Controls

| Key                      | Action                        |
| ------------------------ | ----------------------------- |
| `W` `A` `S` `D` / arrows | Move up / left / down / right |
| `H`                      | Ask Claude for a hint         |
| `Q`                      | Quit                          |

Slide the tiles to merge equal neighbours and build toward a 2048 tile. A move
that changes nothing is rejected; after any move that changes the board, a new
`2` or `4` spawns on a random empty cell.

## Hints (optional)

Pressing `H` asks Claude for the best next move and shows it with a short
rationale. Hints need a credential; set **one** of these before `task run`:

```sh
export ANTHROPIC_API_KEY=sk-ant-api-...        # a standard Anthropic API key
# or
export CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat-...  # a Claude Code / subscription OAuth token
```

`ANTHROPIC_API_KEY` takes precedence when both are set. With neither set, a
one-line notice prints at startup and `H` is a no-op — the game plays normally.
Any hint failure (no credential, network error, rejected credential, rate limit,
or an unusable suggestion) degrades to a brief status-line message; a hiccup
never crashes the game.

> `CLAUDE_CODE_OAUTH_TOKEN` is a subscription credential: tokens are short-lived
> (an expired one degrades to a "re-authenticate" message) and subject to
> subscription rate limits. `ANTHROPIC_API_KEY` is the first-class path. See
> [ADR-0001](docs/adr/0001-optional-claude-only-advisor.md) for details.

## Development

Common tasks (run `task --list` for all of them):

| Command          | What it does                                    |
| ---------------- | ----------------------------------------------- |
| `task setup`     | Create the virtualenv and install with dev deps |
| `task run`       | Launch the game                                 |
| `task test`      | Run the test suite (pytest)                     |
| `task lint`      | Lint with ruff                                  |
| `task format`    | Format with ruff                                |
| `task typecheck` | Type-check with mypy (strict)                   |
| `task check`     | Lint + typecheck + test                         |
| `task package`   | Build the wheel and sdist into `dist/`          |
| `task publish`   | Publish `dist/*` as a GitHub Release            |

### Packaging & publishing

`task package` builds a distributable wheel and sdist into `dist/`.

`task publish` builds those artifacts and publishes them as a **GitHub Release**
tagged `v<version>` (the version comes from `twenty48/__init__.py`), via the
[`gh`](https://cli.github.com) CLI. It needs `gh` installed and authenticated
with push access to the repository. This project does **not** publish to PyPI.

## Architecture

A single flat `twenty48` package, layered by distance from pure logic:
`board` (pure game core) → `advisor` (the swappable Advisor seam, tested against
a fake so it never imports `anthropic`) → `ui` (terminal render + input) →
`loop` (the turn cycle) → `__main__` (the composition root — the only module
that reads the environment, imports `anthropic`, and builds the credentialed
client). See the
[ADRs](docs/adr/) and [`CONTEXT.md`](CONTEXT.md) for the design and vocabulary.

## License

[MIT](LICENSE)
