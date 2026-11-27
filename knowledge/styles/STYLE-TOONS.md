# STYLE: Toons

An original classic-cartoon look. It uses no characters, logos, title cards, or catchphrases from any studio.

## 1. Identity
- **Concept:** a hand-inked Saturday-morning cartoon. Thick black outlines, flat saturated color, hard offset shadows, sunburst and halftone backgrounds. Callouts are speech bubbles, so the audience learns who is "talking" at a glance. The deck can be dense without feeling heavy, because the look carries the fun and the text stays plain.
- **Use for:** internal learning sessions, workshops, team events, any talk where a light tone helps a mostly non-technical audience relax.
- **Avoid for:** executive readouts, customer-facing material, and brand-controlled corporate decks. Do not use any studio's characters, logos, or catchphrases.

## 2. Extends
Base

## 3. Tokens

| Role | Value | Notes |
|---|---|---|
| `--ink` | `#1A1A1A` | Body text, every outline and hard shadow |
| `--surface` | `#FFF8E7` | Paper: vertical slide background |
| `--surface-alt` | `#FFD93D` | Yellow: top-level slide background |
| `--line` | `#CDBB86` | Table rules |
| `--caption` | `#4A4A4A` | |
| `--accent` | `#1B5FC4` | Blue: links, badges, labels |
| `--accent-tint` | `#DCEAFF` | |
| `--connector` | `#1A1A1A` | |
| `--emphasis` | `#1B5FC4` | |
| `--series-1` … `--series-5` | `#D4271F`, `#1B5FC4`, `#FFD93D` (ink outline), `#17792F`, `#6B3FB5` | Lines 5px |

Callout roles:

| Type | Color | Tint | Label text | Icon on the tab |
|---|---|---|---|---|
| `note` | `#4A4A4A` | `#EFEAE0` | `#333333` | White |
| `tip` | `#FFD93D` (yellow) | `#FFF1B0` | `#7A5200` | `--ink` (never white) |
| `remember` | `#1B5FC4` (blue) | `#DCEAFF` | `#12479A` | White |
| `watchout` | `#D4271F` (red) | `#FFE3DF` | `#A3160F` | White |
| `underthehood` | `#6B3FB5` (purple) | `#EDE3FA` | `#54308F` | White |
| `fieldnote` | `#17792F` (green) | `#DDF4E3` | `#136B30` | White |

Extra tokens:

| Token | Value | Use |
|---|---|---|
| `--red` | `#D4271F` | Section badges, bullets, progress bar, step circles |
| `--orange` | `#FF7A1A` | Cover rays only (decoration, never behind text) |

Shape and type:

| Token | Value |
|---|---|
| `--radius` | `14px` |
| `--outline-width` | `3px` |
| `--outline-color` | `#1A1A1A` |
| `--shadow` | `4px 4px 0 #1A1A1A` (hard, no blur) |
| `--font-heading` | `"Marker Felt", "Chalkboard SE", "Comic Sans MS", "Comic Neue", system-ui, sans-serif` (700) |
| `--font-body` | `"Avenir Next", "Segoe UI", system-ui, sans-serif` (400), so long text stays plain |
| `--mermaid-look` | `classic` |

Contrast: white text only on `--red`, `--accent`, the purple and green callout colors, and `--ink`. Ink text on yellow, paper and every tint. Never white on yellow or orange; never `--accent` text on yellow.

## 4. Type and scale
h2 1.32em. Otherwise as Base.

## 5. Base elements
- **Title slide:** `--red` field with sunburst rays (alternating `--red` and `--orange`, a conic gradient). The text sits on one cream card with a 5px ink outline, a 12px hard shadow and rounded corners. Series name in a yellow pill with an ink outline; title in ink with a yellow hard text shadow; date line in ink.
- **Top-level slide:** a faint halftone dot tile in a slightly darker yellow over `--surface-alt`. The number chip is a **starburst badge**: the section number in white on `--red`, a 12-point star with an ink outline.
- **Vertical slide:** number chip in ink on yellow, 2.5px ink outline, 2px hard shadow.
- **"More below" cue:** ink, a down chevron with "More below!".
- **"As of" label:** ink bold.
- **`[UNVERIFIED]` pill:** `#ECECEC` fill, `#555555` text.
- **`[Try it yourself]` steps:** red circles with white numbers, joined by a line.
- **Tables:** 3px ink rule under the header.
- **Mermaid:** `primaryBorderColor` ink; node outlines 2.5px.
- **`Embed:` frame:** 4px ink outline, rounded corners, 6px hard shadow.
- **Motion:** none beyond Reveal's fade and click-to-reveal fragments.

## 6. Callouts
Every callout is a **speech bubble**: the Base panel with the Toons outline and shadow, plus a small tail pointing up from the top edge toward the slide's heading, as if the heading is speaking. On top-level slides the panel is white; on vertical slides it is the tint.

## 7. Slide types
- **`[Quick check]`:** options are outlined cards with a hard shadow; the answer panel is outlined too.
- **`[Recap]`:** label "Quick recap"; footer line "Up next: [section title]".

## 8. Layouts
- **Items:** white panels with the ink outline and hard shadow (instead of the accent tint), so they stand out on both yellow and paper.
- **The emphasized item:** `--emphasis` fill, white text, same outline and shadow.

## 9. Degrades
None.

## 10. Frequency and balance
As `TAGS.md`. Bubbles and hard shadows carry the style; when every slide has a bubble, none of them stand out.

## 11. Don'ts
- No studio characters, logos, title cards, or catchphrases, and no look-alikes of them.
- No stock photos or clip art; icons are simple line drawings in one stroke weight.
- No blur, gradients (except the cover's rays), or soft shadows. Shadows are hard and offset.
- No animation, wiggle, or bounce.
- Don't use the comic heading font for body text, tables, or footers. It stays on headings, badges and labels.
- Don't color body text with callout colors; color identifies callout type only.
