# Design system — what-needs-me redesign

## Visual direction

Calm, editorial, Linear/Arc-grade software — one dark surface, one accent color, and
type doing almost all of the work. No card-soup, no gradients-for-decoration, no
competing colors. Every pixel of visual weight is a deliberate signal of "this needs
you" vs "this is FYI" vs "this is noise you can trust to ignore" — never decoration
for its own sake. The product should feel like the opposite of an inbox: quiet by
default, loud only where a real ask exists.

## Color tokens (dark palette, one accent)

```
--bg:        #0b0c0e   page background
--surface-1: #131418   card / panel background
--surface-2: #1a1c21   raised panel (drawer, pile, hovered card)
--border:    #24262c   hairline borders
--text:      #eef0f3   primary text
--text-muted:#8b909b   secondary text (sender/subject line, timestamps)
--text-faint:#5a5e68   tertiary text (quiet strip, pile fine print)
--accent:    #9b8cff   the one accent — brand mark, active states, links, deadline-soon
--info:      #5fb3c9   FYI / informational card accent (used sparingly, never with accent)
--danger:    #ff6a5c   overdue-only deadline color
```

Semantic color is used **only** for urgency/category scanning, never decoration:
- `--accent` = active control state + "needs you" deadline badges that are not overdue.
- `--danger` = only an overdue deadline badge.
- `--info` = only the FYI eyebrow/icon on informational cards.
- Everything else (notification strip, pile, metadata) stays in the neutral text scale.

## Typography scale (system stack)

```
font-family: -apple-system, "Segoe UI", Inter, ui-sans-serif, system-ui, sans-serif;

--text-2xl: 34px / 1.15 / -0.03em   page H1
--text-xl:  20px / 1.3  / -0.02em   card ask (Zen/Compact), drawer title
--text-lg:  17px / 1.35 / -0.01em   card ask (Dense)
--text-md:  15px / 1.5             drawer body, thread summary
--text-sm:  13px / 1.5             card metadata line, lane titles
--text-xs:  12px / 1.4             pile fine print, quiet-strip rows, timestamps
```

One family, no mixing. Weight carries hierarchy (700 for asks/H1, 600 for labels, 400
for body/meta) instead of introducing a second typeface.

## Spacing scale

`4 / 8 / 12 / 16 / 24 / 32 / 48 / 64` (px). Card internal spacing, section gaps, and
page margins all snap to this scale — no arbitrary one-off values, which is what
made v0 feel cramped despite having "padding."

## Radii & elevation

- Radius: `10px` cards/controls, `14px` panels (pile, drawer content blocks), `999px`
  pills/chips/segmented control.
- No drop shadows for their own sake. The only elevation cue is a 1px border
  (`--border`) plus a one-step-lighter background (`--surface-1` → `--surface-2`) on
  hover/open. The drawer is the one exception: a soft `0 20px 60px rgba(0,0,0,.5)` to
  read as physically in front of the page, since it overlays content.

## Component specs

### App shell / top bar
Brand mark left, account chips, then Fused/Split segmented control and density select
right-aligned. Height increases from v0's 76px to 84px with more left/right breathing
room (`--space-8` page margin minimum). Border-bottom hairline only — no shadow.

### Account chip
Dot (account color) + short label, `--text-sm`, `--text-muted`. In Split mode the same
chip becomes each lane's header, promoted to `--text-md` + `--text` so identity is
unmistakable per lane.

### Mode toggle / density control
Segmented pill control, unchanged mechanism from v0, restyled: active segment gets
`--surface-2` background + `--text`, inactive stays `--text-muted` with no border.
Density is a real select, not hidden on mobile (v0 hid it below 700px — kept visible
here since it is one of the three variants under test).

### Today card — verdict-first layout
The single biggest change. Grid: `[icon] [ask + meta] [deadline]`, but with an
explicit type-size contract:

- **Ask** (`--text-xl`, weight 700, `--text`) — always the visually dominant element
  on the card. This is the direct answer to "what does this need."
- **Meta** (`--text-sm`, `--text-muted`) — one line: `sender · subject`, truncated,
  never wraps to more than one line, never shares size with the ask.
- **Snippet** — dropped from the default card entirely (it duplicates what the drawer
  shows and was the single biggest source of visual noise in v0). Zen density may show
  one truncated snippet line at `--text-xs`/`--text-faint`; Compact/Dense never do.
- **Deadline badge** — pill, right-aligned, `--accent` background unless overdue
  (`--danger`), else absent entirely (no empty deadline slot rendered, unlike v0's
  always-reserved column).

Rationale: an "ask = biggest text" contract is what makes the 3-second scan promise
in the brief actually true — everything else on the card is supporting metadata, sized
and colored to say so.

### FYI card (informational tier)
Same grid, `--info` icon instead of category icon, an explicit `FYI` eyebrow above the
headline (`--text-xs`, `--info`, letter-spaced), and the headline text swapped from the
raw extracted `ask` to a calmer restatement where the source category is known-passive
(e.g. `travel` → "Booking confirmed" instead of "Review travel details"). Slightly
reduced weight (600 not 700) versus an action card's ask — present, legible, but never
mistakable for a task.

### Quiet/notification strip
Not cards at all — a dense list (icon-less, one line each: subject · sender ·
relative time, all `--text-xs`/`--text-faint`) sitting between the stack and the pile,
under a small `Also arrived` label. This is where automated/notification-flavoured
mail that still slipped past classification into `cards` gets demoted to, so it's
visible (nothing is hidden) but structurally can never compete with the stack above it.

### Pile digest block
Promoted to a real component: `--surface-1` panel, `--text-lg` headline ("Nothing here
needs you" / "N messages, filed"), then a per-category row list (label + count +
latest-activity relative time), each row is the expand target. Collapsed state alone
must be legible as "safe to ignore" per the flow doc — expansion is progressive
disclosure, not a requirement to trust the number.

### Thread drawer
Wider (520px vs v0's 460px) with the same `--space-8` internal margin as the page body
so it doesn't feel like a cramped afterthought. Title at `--text-xl`, summary at
`--text-md`/1.6 line-height, "what changed" as an `--accent` inline note (not a full
line of shouting color), then messages as bordered rows with `--text-sm` sender bold,
`--text-xs` timestamp, `--text-sm`/`--text-muted` snippet.

### Empty states
Centered, `--text-muted`, no icon-soup — one line stating the state plainly ("Clear
for now — nothing needs you.") per the flow doc.

## Density variants

Density changes **type scale and rhythm**, not just box padding (the v0 mistake).

| | Zen | Compact (default) | Dense |
|---|---|---|---|
| Card vertical padding | 28px | 18px | 12px |
| Card gap | 16px | 10px | 4px |
| Ask size | `--text-xl` (20px) | `--text-xl` (20px) | `--text-lg` (17px) |
| Meta line | shown | shown | shown |
| Snippet line | shown (1 line, faint) | hidden | hidden |
| Icon column | shown | shown | hidden (icon folded into ask line as a small glyph) |

## Rationale summary

- **Verdict-first card** = ask is the biggest element, sender/snippet secondary,
  account chip tertiary → answers "what needs me" without reading the whole card.
- **Three-tier stack (needs-you / FYI / quiet-strip)**, all derived client-side from
  the same `cards` array → fixes fake-action-cards and ambiguous-cards without any
  backend change, because the truth ("is this really actionable") is a presentation
  judgment the UI was previously failing to make.
- **One accent, semantic color only for urgency** → keeps the palette restrained so
  color remains meaningful (a purple badge always means "real deadline") instead of
  decorative.
- **Pile as a real component, not a footnote** → makes "safe to ignore" a designed,
  confident state instead of something the user has to notice on their own.
- **Density changes type/rhythm, not just padding** → the three variants become
  meaningfully different, not the same cramped content in a bigger box.
