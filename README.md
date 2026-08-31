# what needs me

An AI-native email client that replaces the chronological inbox with a ranked **"what needs me"** deck. Bills, approvals, and replies with deadlines surface as decision cards with the ask front and center; everything else files itself into a digest pile you can trust to ignore.

Working prototype (v0). Read-only by design.

## What it does

- **Today deck** — your inbox as ranked decisions, not a timeline. Each card extracts the ask: `Pay ₹14,000 by Sep 15`, `Approve by Sep 10`, `Respond by tomorrow`.
- **The pile** — newsletters, receipts, and notifications collapse into a per-category digest (`36 newsletters · 38 notifications`), framed as "nothing needs you".
- **Multi-account identities** — connect several accounts; **Fused** mode merges them into one deduplicated stream with an account chip per message, **Split** mode gives per-account lanes when you need boundaries.
- **Thread drawer** — open a card to get a one-paragraph summary, a "what changed since you last looked" line, and the raw recent messages.
- **Deterministic triage** — the classifier (bill / approval / travel / personal / notification / newsletter / receipt) runs on rules, so the product works with no external services. A Gemini API key optionally adds real thread compression.

## Stack

FastAPI + vanilla HTML/CSS/JS (no build step) + Gmail API via `google-auth`. Python 3.11+.

## Quickstart

1. Create a Google Cloud OAuth client of type **Desktop app** with the **Gmail API** enabled, then download `client_secret.json` ([console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)).
2. Authorize an account and save the resulting token JSON to a file (the token must include a `refresh_token`; any standard `gmail.readonly` OAuth flow produces one, e.g. with `google_auth_oauthlib`).
3. Point the app at it and run:

```bash
export GOOGLE_TOKEN_PATH=/absolute/path/to/token.json
make install
make run
```

Open http://127.0.0.1:8012 — you should see your Today deck.

## Tests

```bash
make test
```

Deterministic triage unit tests with fixture emails; no network required.

## Security

- **Strictly read-only against Gmail.** No sends, no label changes, no archiving, nothing ever marked read.
- The OAuth token is only ever read from `GOOGLE_TOKEN_PATH` and is gitignored — never commit it.
- Run it locally (or on a private network); the app has no multi-user story yet.

## Design

The product and visual system are documented in this repo:

- [`docs/DESIGN.md`](docs/DESIGN.md) — visual direction, color tokens, typography scale, component specs
- [`docs/USER_FLOW.md`](docs/USER_FLOW.md) — the Today / Split / Pile flows and where future actions slot in

## Roadmap

- Second-account OAuth flow (real multi-identity)
- LLM enrichment for ask extraction and thread compression (Gemini key)
- Dismiss / "not mine" local state so done cards leave the stack
- Push notifications for high-urgency asks

## License

[MIT](LICENSE)