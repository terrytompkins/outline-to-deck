# STYLE: Field Guide

## 1. Identity
- **Concept:** a trail guide for an unfamiliar subject. Each top-level topic is a trail with a numbered trail marker. A small, consistent set of margin callouts tells the reader what kind of information they're looking at: a note, a tip, something to remember, a hazard, a look under the hood, a real-world field note. The audience learns to read the callouts at a glance, so the deck can be dense without feeling dense.
- **Use for:** teaching sessions, workshops, onboarding, how-to talks; anything attendees will revisit on their own.
- **Avoid for:** executive readouts and brand-controlled corporate decks (use the organization's brand style).

## 2. Extends
Base

## 3. Tokens

| Role | Value | Notes |
|---|---|---|
| `--ink` | `#1E2B2E` | |
| `--surface-alt` | `#E6F0EC` | Moss: top-level slide background |
| `--line` | `#D5DDD9` | |
| `--caption` | `#5C6B67` | |
| `--accent` | `#1F5C4F` | Spruce |
| `--accent-tint` | `#E6F0EC` | Moss |
| `--connector` | `#5C6B67` | |
| `--emphasis` | `#1F5C4F` | Spruce |
| `--series-1` … `--series-5` | `#1F5C4F`, `#2F6F9F`, `#E0A21B`, `#C8501F`, `#4B5563` | Spruce, sky, sun, signal, slate |
| `--outline-color` | `#D5DDD9` | |

Callout roles:

| Type | Color | Tint | Label text | Icon on the tab |
|---|---|---|---|---|
| `note` | `#1F5C4F` | `#E6F0EC` | `#1F5C4F` | White |
| `tip` | `#E0A21B` (sun) | `#FDF3DC` | `#7A5200` | `--ink` (never white) |
| `remember` | `#2F6F9F` (sky) | `#E4EEF6` | `#25597F` | White |
| `watchout` | `#C8501F` (signal) | `#FBE6DD` | `#A63F14` | White |
| `underthehood` | `#4B5563` (slate) | `#EEF0F3` | `#4B5563` | White |
| `fieldnote` | `#3E7D3A` (fern) | `#E7F2E4` | `#2F6A2C` | White |

Label colors are darker than v1's so every label meets 4.5:1 on its tint (v1's Tip, Watch out and Field note labels did not).

Extra tokens:

| Token | Value | Use |
|---|---|---|
| `--spruce-deep` | `#16443A` | Title slide field |

Shape and type:

| Token | Value |
|---|---|
| `--font-heading` | `"Avenir Next", Avenir, "Segoe UI", system-ui, sans-serif` (700) |
| `--font-body` | same stack (400) |
| `--mermaid-look` | `classic` (the new Mermaid look adds node shadows, which this style forbids) |

## 4. Type and scale
h2 1.32em. Otherwise as Base.

## 5. Base elements
- **Title slide:** full-bleed `--spruce-deep` with a faint topographic contour pattern (inline SVG, white lines at 8% opacity). Series name small in `--accent-tint`; title and date line in white.
- **Top-level slide:** the number chip is a **trail marker**: the section number in white on `--accent`, in a rounded rectangle with a small notch, like a painted trail blaze.
- **"More below" cue:** `--accent`, a down chevron with "more on this trail".
- **`[Try it yourself]` steps:** a numbered trail: circles joined by a line.

## 6. Callouts
As Base. Labels and icons as `TAGS.md`.

## 7. Slide types
- **`[Quick check]`:** the answer panel is `--callout-remember-tint`.
- **`[Recap]`:** label "Trail recap"; footer line "Next trail: [section title]".

## 8. Layouts
As Base.

## 9. Degrades
None.

## 10. Frequency and balance
As `TAGS.md`.

## 11. Don'ts
- No stock photos or clip art; icons are simple line drawings in one stroke weight.
- No gradients and no drop shadows on panels.
- Don't color body text with callout colors; color identifies callout type only.
