# Design system - What Needs Me

## Current direction

The shipped interface uses a light, quiet Today deck. A pale gray page holds white cards and panels, with violet for active controls and action order, green for FYI, amber for a near deadline, and red for an overdue deadline. Color supports meaning; it does not substitute for text. Source sender and subject stay visible on cards, and Zen density also shows a snippet.

## CSS tokens

`app/static/style.css` is the source of truth. Its current palette is:

| Token | Value | Use |
| --- | --- | --- |
| `--bg` | `#f7f7f8` | Page and drawer summary background |
| `--surface-1` | `#ffffff` | Cards, toolbar controls, drawer |
| `--surface-2` | `#f2f2f5` | Neutral controls and hover |
| `--border` | `#e6e6ea` | Hairline separation |
| `--text` | `#24242b` | Main copy |
| `--text-muted` | `#62626e` | Secondary copy |
| `--text-faint` | `#70707c` | Source metadata and quiet mail |
| `--accent` | `#5b51e8` | Brand, controls, action order |
| `--info` | `#167568` | FYI |
| `--amber` | `#8a580d` | Due soon |
| `--danger` | `#b63736` | Overdue |

The system font stack is used throughout. The spacing tokens are 4, 8, 12, 16, 24, 32, 48, and 64 px. Cards use a 16 px radius; larger drawer surfaces use 20 px. Borders and restrained shadows distinguish layers.

## Today deck

The existing API delivers cards in ranked order. The client preserves that order within the action tier and labels visible action cards `Priority 1`, `Priority 2`, and so on. Urgent API items say `Urgent`; deadlines show `Due` or `Overdue` with a date. There is no client score.

The first three real action cards are visible initially. A `Show N more priorities` button reveals the remaining action cards. The status reports the total action count, how many are shown, and counts for FYI and quiet mail. The same three-card cap applies across accounts in Split mode. Switching mode resets the disclosure.

Travel and receipt cards appear in a calmer FYI tier. Automated mail and generic response asks appear in `Also arrived` as compact rows with original subject and sender. The read-only thread drawer opens from every card or quiet row. An empty deck shows one plain sentence. A populated deck with an empty pile shows `Nothing else came in.`; a populated pile can expand to its category counts.

## Controls and recovery

Fused and Split buttons and the density select have a minimum 44 px target height. Zen shows one snippet line and more space; Compact keeps source metadata; Dense compresses spacing and hides the icon. The layout adapts at 700 px so cards and the full-width mobile drawer fit narrow screens.

Initial fetch failure shows a visible error and Retry button. Thread fetch failure keeps the dialog open with its own Retry button. The dialog is labelled by its title, uses `aria-modal`, and makes the page inert while open. Tab and Shift+Tab cycle through its visible controls. Escape, close, or the scrim dismisses it and restores focus to the source card. Reduced-motion settings disable nonessential transitions and shimmer.
