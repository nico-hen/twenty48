# The AI Advisor is an optional, Claude-only seam

The move recommender ("Advisor") is a single interface with one implementation,
Claude-backed; the prototype's local heuristic is dropped. The Advisor is
**optional** — the game is fully playable without it — and it **never throws
into the game loop**: every failure (missing credential, network error, refusal,
or a suggestion that isn't a legal move) becomes a short status-line message and
play continues. The game core depends only on the Advisor contract, never on the
`anthropic` package.

## Considered Options

- **Keep the heuristic as a local fallback** — rejected: the user wants Claude
  only for now and doesn't want to maintain a second recommender. The seam is
  kept so a fallback can be re-added later without touching the game core.
- **Make the AI mandatory (refuse to start without a credential)** — rejected:
  the repo must run with zero setup for anyone who clones it (graders included),
  and the brief says "do not submit with any credentials."

## Consequences

- The seam has exactly one implementation today. That is deliberate — an
  extension point, not speculative generality.
- Authentication accepts **either** `ANTHROPIC_API_KEY` (sent as `x-api-key`;
  read automatically by the SDK) **or** `CLAUDE_CODE_OAUTH_TOKEN` (an OAuth
  token, sent as `Authorization: Bearer` **plus** the `anthropic-beta:
  oauth-2025-04-20` header). `ANTHROPIC_API_KEY` takes precedence when both are
  set. The `ClaudeAdvisor` branches its client construction on which is present.
- The OAuth-token path against the Messages API is **verified working**
  ([#4](https://github.com/nico-hen/2048/issues/4); research note
  [0004](../research/0004-claude-code-oauth-token-messages-api.md)): an
  `sk-ant-oat…` token sent as `Authorization: Bearer` returns a live `200` from
  `POST /v1/messages`. The verification surfaced three caveats, all absorbed by
  the "never throws into the game loop" policy above:
  - **Subscription-tier limits.** A `CLAUDE_CODE_OAUTH_TOKEN` is a Claude
    subscription credential, governed by subscription rate limits rather than
    per-org API tiers. In testing `claude-haiku-4-5` succeeded but
    `claude-opus-4-8` returned `429`. The Advisor must not hardcode a model the
    OAuth tier may rate-limit; a `429` degrades to a status-line message.
  - **Short-lived tokens.** OAuth access tokens expire within hours and the
    Advisor cannot refresh them. A stale token returns `401`, which degrades to
    a status-line message rather than a crash. A static `CLAUDE_CODE_OAUTH_TOKEN`
    env var can therefore go stale between sessions.
  - **Terms of Service (unresolved).** Using a Claude Code / subscription OAuth
    token for general Messages API traffic is a gray area; no primary source was
    found permitting or forbidding it. `ANTHROPIC_API_KEY` remains the clean,
    first-class credential, and OAuth is a convenience for developers already
    logged into Claude Code — not the path a grader is expected to use.
  - The `anthropic-beta: oauth-2025-04-20` header was **not** strictly required
    against `/v1/messages` in testing, but the `ClaudeAdvisor` sends it anyway:
    harmless where unneeded, and future-proof against endpoint changes.
