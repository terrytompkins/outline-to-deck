# LAYOUTS

SmartArt-style layouts: an ordinary bullet list, rendered as a designed shape. Authors write bullets; one `Layout:` line picks the shape. This file lists every layout, the data shape it expects, its limits, when Claude proposes it, and what happens when content doesn't fit. `TAGS.md` registers the `Layout:` directive itself.

Tables marked `<!-- registry: … -->` are read by `tools/lint-outline.py`. Keep their columns in the order shown.

## 1. Syntax

```markdown
Layout: process; chevron
- Pilot: two teams build a real deck
- **Template: publish the style guide**
- Train: run a workshop
- Scale: open it to everyone [TBD: target date]
```

- **The `Layout:` line** goes on its own line. Layout fields such as `X axis:` may follow it; then comes the bullet list it governs, with no blank paragraph between.
- **Options** follow semicolons, in any order: a variant from the catalog, `build`, `numbered`. An unknown option is ignored and noted; an unknown layout name stops the slide.
- **Label and detail.** An item splits at its first `: ` when the text before it is five words or fewer and holds no link, code or other markup. Otherwise the whole item is the label. Write `\:` to keep a colon from splitting. The linter lists every split.
- **Emphasis.** A fully bold item (`**…**`) is the emphasized one. At most one per layout.
- **Inline markers.** `[TBD: …]` becomes a chip inside the item and `[UNVERIFIED]` a pill; source links move to the footer; origin tags are stripped. `Speaker notes:` can't sit inside a layout list; put it after the list.
- **With `Main points:`.** A `Layout:` line may follow `Main points:`. The bullets are still the main points.
- **Per slide:** up to two layouts (a fit limit; see §5). Slide-type slides carry no layouts.

## 2. Catalog

<!-- registry: layouts -->
| Name | Shape | Items | Label words | Detail words | Variants | Fields | Fallback | Renderer |
|---|---|---|---|---|---|---|---|---|
| `list` | list | 2–7 | 6 | 20 | boxes, plain | — | split | html |
| `process` | ordered | 3–7 | 4 | 12 | chevron, arrows, steps | — | list | html |
| `timeline` | dated | 3–8 | 4 | 12 | horizontal, vertical | — | list | html |
| `columns` | columns | 2–4 | 5 | 12 | plain, pros-cons, before-after | — | split | html |
| `hierarchy` | tree | 2–12 | 4 | 0 | top-down, left-right | — | list | html |
| `radial` | radial | 3–8 | 4 | 8 | — | — | list | svg |
| `matrix` | quad | 4–4 | 5 | 15 | plain, axes | X axis, Y axis | list | html |
| `cycle` | ordered | 3–6 | 4 | 10 | — | — | process | svg |
| `pyramid` | ordered | 3–5 | 5 | 10 | — | — | list | html |
| `funnel` | ordered | 3–5 | 5 | 10 | — | — | process | html |
| `venn` | sets | 2–3 | 4 | 8 | — | Overlap | columns | svg |

The first variant listed is the default. The word limits are **starting values**, to be tuned in testing; going over them is a fit warning, not an error.

**Shapes:**
- **list:** label/detail items; each may have one level of sub-bullets.
- **ordered:** label/detail items in order. Sub-bullets aren't allowed.
- **dated:** like ordered, but each label is a date or period ("Q1 2027", "Week 2").
- **columns:** each top-level bullet is a column header; its sub-bullets (1–5) are the column. "Items" counts columns.
- **tree:** exactly one top-level bullet (the root); nesting up to three levels below it. "Items" counts all nodes. Labels only: details are moved to speaker notes.
- **radial:** exactly one top-level bullet (the center); its sub-bullets are the spokes. "Items" counts spokes.
- **quad:** exactly four items in reading order (top-left, top-right, bottom-left, bottom-right). With the `axes` variant, `X axis:` and `Y axis:` lines name the axes; keep each to about three words, such as `Effort: low → high`.
- **sets:** one item per circle. An optional `Overlap:` line labels the shared middle.

**Renderer:** `html` layouts are HTML and CSS; `svg` layouts draw their frame in SVG, positioned by the deck runtime, with the labels kept as HTML text on top.

## 3. When Claude proposes a layout

<!-- registry: layout-proposals -->
| Name | Propose when |
|---|---|
| `list` | 2–7 points of equal weight that read better as separate panels than as plain bullets |
| `process` | 3–7 bullets describe steps in order |
| `timeline` | Bullets start with dates or periods |
| `columns` | 2–4 options compared on the same points, or before-and-after, or pros and cons |
| `hierarchy` | Bullets nest to show parts of a whole or reporting lines |
| `radial` | One central idea with 3–8 related parts of equal weight |
| `matrix` | Four items that fall on two axes |
| `cycle` | Steps where the last leads back to the first |
| `pyramid` | Levels that build on each other, most fundamental at the bottom |
| `funnel` | Stages that narrow, such as a pipeline or a filter |
| `venn` | Two or three groups whose overlap is the point |

Rules:
- Propose a layout only when the bullets already fit its shape. Never rewrite bullets just to fit a layout without saying so.
- Prefer a layout to a diagram when content is bullet-shaped. Use a `Diagram:` for branches, decisions and loops a layout can't show.
- Respect `BRIEF.md`'s layout setting (encourage / sparingly / off) and the balance limit in `TAGS.md`: at most half of a section's slides carry a layout.
- List every proposed layout in the summary of changes.

## 4. Markup contract

Claude writes semantic markup; `runtime/base.css`, the style's CSS and `runtime/deck.js` do the rest. Class names are fixed so `tools/check-deck.py` can verify them.

```html
<div class="layout layout--process" data-layout="process" data-variant="chevron" data-count="4">
  <ol class="layout__items">
    <li class="layout__item"><span class="layout__label">Pilot</span><span class="layout__detail">two teams build a real deck</span></li>
    <li class="layout__item is-key"><span class="layout__label">Template</span><span class="layout__detail">publish the style guide</span></li>
    …
  </ol>
</div>
```

- The wrapper has `class="layout layout--NAME"`, `data-layout`, `data-variant` (the default if none was given) and `data-count` (the item count as the linter counts it).
- Items use `<ol>` for ordered, dated, tree and radial shapes, `<ul>` otherwise. Nested shapes nest `<ul>`/`<ol>` inside the item.
- `is-key` marks the emphasized item. Options become attributes on the wrapper: `data-build` (items appear one click at a time; `data-build="off"` overrides a deck-wide default) and `data-numbered`.
- Layout fields become attributes: `data-x-axis`, `data-y-axis`, `data-overlap`.
- Inline markers render inside `.layout__label` or `.layout__detail` as usual (`.tbd`, `.unverified`).

## 5. Fit and fallback

Applied in order, stopping at the first step that fits:

1. **Render normally,** with autofit shrinking text down to its floor (0.62).
2. **Compact:** the runtime tightens gaps and wraps (a process to two rows, columns to stacked rows).
3. **Fall back** to the layout in the catalog's Fallback column, or `split` into a "(continued)" slide.
4. **Last resort:** a plain bullet list.

Never truncate silently, never reword, never go below the floor. Every step past 1 is recorded in `OUTPUT-NOTES.md` with a suggested outline change. The linter predicts most of these in Phase 1 from item counts and word counts.

Two layouts on one slide follow the same rule: if they don't fit together, the second moves to a "(continued)" slide.
