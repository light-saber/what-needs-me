# User flow — what-needs-me redesign

Scope: frontend-only flows against the existing three endpoints
(`/api/accounts`, `/api/today`, `/api/thread/{id}`). No new actions ship in this
round — everywhere a future action would slot in is called out and labelled **(later)**.

## Primary flow — Today, fused

1. **Open app** → `GET /api/accounts` + `GET /api/today?mode=fused&days=7` fire in
   parallel. Header shows a loading state; nothing about "N items" is claimed until
   data lands.
2. **Today renders as one ranked stack**, split into two visual tiers built from the
   same `cards` array (no schema change — this is a client-side grouping):
   - **Needs you** — cards with a real ask (bill/approval/personal, or anything with a
     genuine deadline and a specific verb). Full visual weight, ask-first.
   - **For your information** — informational cards (travel confirmations, receipts):
     visible, calmer accent, framed as FYI not a task.
   - Notification-flavoured cards (automated senders / generic "Reply" with no real
     deadline) do **not** get a slot in either tier — they render in a third, quiet
     "also arrived" strip directly above the pile, small and skimmable but never
     competing with real asks.
3. **User reads the top of the stack** — the biggest text on every card is the ask
   itself; sender/subject is one quiet line underneath; deadline badge (if any) sits
   at the right.
4. **Open card** → click anywhere on the card → `GET /api/thread/{threadId}` →
   drawer slides in with: thread title, one-paragraph summary, a "what changed since
   you last looked" line, then the message list (from/date/snippet per message).
5. **Back / next card** — close drawer (× or click-away) returns to the exact stack
   position. *(later)*: keyboard `j`/`k` or drawer-footer prev/next to move through
   the stack without returning to the list first.
6. Where actions would eventually slot in, **(later)**:
   - Card hover/right edge → archive / dismiss / "not mine" — **(later)**.
   - Drawer footer → reply / mark handled — **(later)**.
   - Pile item → bulk-dismiss a category — **(later)**.

## Split mode

1. **Toggle to Split** → `GET /api/today?mode=split&days=7` (mode swaps in the same
   request shape; `accountId` on each card already supports this).
2. **Lanes render per account**, each lane headed by the account chip (identity —
   colored dot + address) so a multi-account user always knows whose mail they're
   looking at. Same two/three-tier grouping applies inside each lane.
3. Rest of the flow (open card → drawer → back) is identical to fused mode.

## Pile — expand digest → trust-and-ignore path

1. **Pile renders as a standing digest block** below the stack: per-category counts
   ("47 newsletters", "42 notifications", "23 unknown", "4 receipts" from the live
   pull) with a one-line framing ("Nothing here needs you — skim if curious").
2. **Expand** (click the block) reveals the category breakdown with latest-activity
   timestamp per category — still just `pile.categories`, no new data fetched.
3. **Trust-and-ignore**: the collapsed state alone is designed to be a complete,
   confident "I've seen this and it's fine to ignore" signal — expansion is optional,
   for the curious, not required to trust the count.
4. *(later)*: click a pile category → filtered read-only list of those messages;
   bulk actions on a pile category.

## Empty states

- **No cards, no pile**: "Clear for now — nothing needs you." with no leftover UI
  chrome (no empty lane headers).
- **Pile empty, cards present**: pile block collapses to a single quiet line
  ("Nothing else came in") rather than an empty box.
- **Fetch error**: existing error surface in the status line, kept as-is functionally,
  restyled to match the new type scale.
