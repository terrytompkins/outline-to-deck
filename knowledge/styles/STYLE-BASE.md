# STYLE: Base

The complete default style. It renders every tag in `TAGS.md` and every layout in `LAYOUTS.md`, and it is the plain, brand-free look on its own. **Every other style extends Base** and lists only what it changes. Its CSS is `runtime/base.css`.

Base is always uploaded, whichever style a presentation uses.

## 1. Identity
- **Concept:** clean and quiet; the content carries the deck. One blue accent, generous white space, and callouts that are told apart by color, icon and label.
- **Use for:** any talk without a brand or theme requirement; the starting point for a new style.
- **Avoid for:** nothing in particular. Pick another style when the talk would benefit from a stronger look.

## 2. Extends
None. Base is the root.

## 3. Tokens

### 3.1 Required roles
Every style supplies these, by inheriting Base or overriding it. Base CSS and every layout read only these roles.

| Role | Base value | Use |
|---|---|---|
| `--ink` | `#1F2933` | Body text |
| `--surface` | `#FFFFFF` | Vertical slide background, panels |
| `--surface-alt` | `#F4F6FA` | Top-level slide background |
| `--line` | `#DDE1E6` | Rules, table borders, layout outlines |
| `--caption` | `#5F6B76` | Footer, captions, page number |
| `--accent` | `#3B5BDB` | Heading accents, number chips, links, badges |
| `--accent-tint` | `#E8ECFB` | Panels; default fill for layout items |
| `--on-accent` | `#FFFFFF` | Text and icons on `--accent` |
| `--connector` | `#5F6B76` | Lines and arrows in layouts and diagrams |
| `--emphasis` | `#2B44A8` | The key item in a layout or diagram |
| `--on-emphasis` | `#FFFFFF` | Text on `--emphasis` |
| `--series-1` … `--series-5` | `#3B5BDB`, `#7C93E8`, `#B7791F`, `#C0392B`, `#2F855A` | Chart series, in order |

### 3.2 Callout roles
One set per canonical callout type: the color (tab and icon background), the tint (panel), and the label text color on the tint.

| Type | `--callout-<type>` | `--callout-<type>-tint` | `--callout-<type>-text` | Icon on the tab |
|---|---|---|---|---|
| `note` | `#3B5BDB` | `#E8ECFB` | `#2B44A8` | White |
| `tip` | `#B7791F` | `#FDF2DE` | `#7A5200` | `--ink` (never white) |
| `remember` | `#6741D9` | `#F0EBFC` | `#5232B8` | White |
| `watchout` | `#C0392B` | `#FBE7E4` | `#A12E22` | White |
| `underthehood` | `#4B5563` | `#EEF0F3` | `#3F4752` | White |
| `fieldnote` | `#2F855A` | `#E6F4EC` | `#22663F` | White |

### 3.3 Shape and type tokens

| Token | Base value | Use |
|---|---|---|
| `--radius` | `10px` | Panels, cards, layout items |
| `--outline-width` | `0px` | Outline on panels, cards and layout items (Base uses fills, not outlines) |
| `--shadow` | `none` | Shadow on panels, cards and layout items |
| `--font-heading` | `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` | Headings, labels, badges |
| `--font-body` | same as heading | Body text, tables, footers |
| `--font-code` | `ui-monospace, Menlo, Consolas, monospace` | Code |
| `--mermaid-look` | `classic` | Mermaid's `look` setting (D22) |

### 3.4 Contrast
All text roles meet 4.5:1 on the backgrounds they are used on (checked Nov 27, 2026). White text only on `--accent`, `--emphasis` and the callout colors other than `tip`. A style that changes colors must keep 4.5:1 for text and 3:1 for icons and connectors.

## 4. Type and scale
- Base font size 34px at 1280×720. h1 (title slide) 1.8em; h2 1.3em; h3 and h4 1.05em; body lists and paragraphs 0.7em; tables 0.6em.
- Footer, page number and the "more below" cue are a fixed 14px. **Nothing visible is smaller than 14px**, including after autofit (floor 0.62).
- Layout labels and details use body size or larger; layouts never shrink text below body size before autofit does.

## 5. Base elements
- **Title slide:** `--surface` background; a short `--accent` rule above the series name (`--caption`); the title in `--ink` at h1; the framing line and date below. The presenter's name only if `BRIEF.md` says so.
- **Agenda:** a numbered list of top-level sections in live order, each linking to its slide. Self-guided sections carry a small "self-guided" label in `--caption`.
- **Top-level slide:** `--surface-alt` background. The heading starts with a number chip: section number in `--on-accent` on `--accent`.
- **Vertical slide:** `--surface` background. Number chip: `--accent` text on `--accent-tint`.
- **"More below" cue:** top-right on top-level slides with vertical slides below, `--caption`, a down chevron and "more below".
- **Footer:** bottom-left, 14px. "As of" in `--accent` bold; sources in `--caption` with dotted underlines; several sources separated by " · ".
- **Page number:** bottom-right, left of the navigation arrows, `--caption`, tabular figures. Appendix slides are not counted.
- **`[TBD: …]` chip:** dashed 2px `--callout-watchout` border, `--callout-watchout-tint` fill, `--callout-watchout-text` text, "TBD: description".
- **`[UNVERIFIED]` pill:** `--callout-underthehood-tint` fill, `--callout-underthehood-text` text, "Unverified".
- **Tables:** header text `--accent`, 2px `--accent` rule under the header, `--line` row rules, no vertical rules.
- **Code:** `--font-code` on `--surface-alt`, `--radius` corners.
- **Links:** `--accent`, underlined.
- **Charts:** series in `--series-1` … `--series-5` order; axis labels `--caption`; gridlines `--line` or off; values labeled directly where there is room.
- **Mermaid:** `theme: 'base'`, `look` from `--mermaid-look`, `layout: 'dagre'`. Theme variables: `primaryColor` = `--surface`, `primaryBorderColor` = `--accent`, `primaryTextColor` = `--ink`, `lineColor` = `--connector`, font family = `--font-body`. Emphasis classes: `key` (fill `--emphasis`, text `--on-emphasis`), `good` (fill `--callout-fieldnote-tint`, stroke `--callout-fieldnote`), `warn` (fill `--callout-watchout-tint`, stroke `--callout-watchout`).
- **`Suggested visual:` SVGs:** drawn with role colors only; the caption "Illustrative, not measured data" in `--caption` unless drawn from outline numbers.
- **`Embed:` frame:** 1px `--line` border, `--radius` corners; the caption below in `--caption`. The link card (print, offline, or framing refused) is a `--accent-tint` panel with the page title and URL.
- **`Image:` figure:** fits the space under the heading without cropping; `--radius` corners; caption below in `--caption`.
- **Appendix:** a divider slide titled "Appendix", then `[Backup]` slides. The parent slide's link reads "Backup: title" in `--caption`; the backup slide's link reads "Back".
- **Sources slide** (when `BRIEF.md` asks): titled "Sources", every footer source once, grouped by section, in `--caption` links.

## 6. Callouts
Syntax and types are in `TAGS.md` §5. Every callout renders as a `--callout-<type>-tint` panel with `--radius` corners and a tab on the left in `--callout-<type>`, holding the icon. The label (or title) is bold in `--callout-<type>-text`, then the text in `--ink`. The tab is part of the panel's shape, not a decorative stripe. Labels and icons come from `TAGS.md`. An alias (`IMPORTANT`, `WARNING`, `CAUTION`) uses its canonical type's colors and icon with its own word as the label.

## 7. Slide types
Structure is in `TAGS.md` §6. Base specifics:
- **`[Try it yourself]`:** top-right badge on `--accent` with a compass icon and "Try it yourself" in `--on-accent`. Steps are numbered circles in `--accent` joined by a `--line` line; the outcome panel is `--callout-fieldnote-tint`.
- **`[Quick check]`:** "Quick check" label in `--accent` with a question-mark icon. Options as `--surface` cards with a 1px `--line` border; the answer in a `--accent-tint` panel.
- **`[Myth vs fact]`:** myth cards in `--callout-watchout-tint` with an ×; fact cards in `--callout-fieldnote-tint` with a ✓.
- **`[Recap]`:** label "Recap"; points as a checklist with `--callout-fieldnote` check icons; footer line "Next: [section title]".
- **`[Quote]`:** the quotation at 1.1em in `--ink` with a large `--accent` opening quotation mark; attribution in `--caption` below.
- **`[Key figure]`:** the figure at 3em in `--accent`, the label at body size under it, context in `--caption`.
- **`[Backup]`:** as a normal vertical slide, with the "Back" link top-right.

## 8. Layouts
Names, data shapes and fallbacks are in `LAYOUTS.md`. Base renders every layout with the roles above:
- **Items:** `--accent-tint` fill, `--ink` text, `--radius` corners, `--outline-width` outline in `--line`, `--shadow`.
- **The emphasized item** (a fully bold bullet): `--emphasis` fill, `--on-emphasis` text.
- **Labels** bold; **details** regular, on the line below the label.
- **Connectors and arrows:** `--connector`, 2px.
- **Numbers** (process steps, `numbered`): `--accent` circles with `--on-accent` digits.
- **Axis titles** (matrix): `--caption`, small caps.

## 9. Degrades
None. Base renders every tag fully.

## 10. Frequency and balance
The limits in `TAGS.md` apply unchanged.

## 11. Don'ts
- No gradients, no decorative stripes, no drop shadows (other styles may add shadows through `--shadow`).
- No stock photos or clip art; icons are simple line drawings in one stroke weight.
- Color identifies meaning (callout type, emphasis, series). Don't color body text for decoration.
- Nothing visible below 14px.
