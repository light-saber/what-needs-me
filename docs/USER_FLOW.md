# User flow - What Needs Me

Scope: read-only frontend flows using `/api/accounts`, `/api/today`, and `/api/thread/{id}`. The client groups existing card fields; it does not change the API schema.

## Today

1. The app loads accounts and the Today deck in parallel. It shows a loading state until both requests finish.
2. The deck preserves the API's order within each tier. Specific asks appear as action cards with numbered priority labels, urgency when supplied, deadline badges, and the original sender and subject. Travel and receipt cards appear as FYI. Automated and generic response mail appears in `Also arrived` with its original subject and sender.
3. The first three action cards are visible. `Show N more priorities` reveals the remainder. The status counts all action cards, indicates how many are visible, and separately counts FYI and quiet items.
4. Clicking any card or quiet row opens its read-only thread drawer. The drawer shows the title, summary, change note when present, and recent messages. Escape, Close, or the scrim dismisses it and returns focus to the source card.
5. A failed initial load shows an error and Retry. A failed thread load keeps the drawer open with its own Retry.

## Split mode and density

Split requests the same Today endpoint with `mode=split` and groups cards by account. The three-card action cap applies across the whole deck and resets on a mode change. Zen, Compact, and Dense adjust card spacing and content while keeping the source sender and subject available. Zen additionally shows a snippet.

## The pile

When there are filed messages, the collapsed pile shows their total. Expanding it reveals category counts and latest activity without another request. When there are cards but no filed messages, it shows `Nothing else came in.` When neither cards nor pile entries exist, the deck shows `Clear for now. Nothing needs you.` and omits the pile.

Archive, dismiss, reply, mark handled, and bulk category actions are future work.
