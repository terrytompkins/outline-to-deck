# STYLE: [Name]

How to use this template:
1. Copy it to `STYLE-[NAME].md` and fill in sections 1–2.
2. In every other section, **list only what differs from `STYLE-BASE.md`**. Anything you leave out comes from Base. Delete the example lines you don't need.
3. Ask Claude to write the style's CSS file (`[name].css`) from this guide, then build the showcase outline with it and check every slide.
4. In `BRIEF.md`, set **Active style** to this file and upload it next to `STYLE-BASE.md`.

A style changes how tags look. It never adds, removes or loosens tags; those live in `TAGS.md`.

## 1. Identity
- **Concept:** [one paragraph: the look and the idea behind it]
- **Use for:** [kinds of talks]
- **Avoid for:** [kinds of talks]

## 2. Extends
Base

## 3. Tokens
Override only the roles you change. Keep 4.5:1 contrast for text and 3:1 for icons and connectors (`STYLE-BASE.md` §3.4).

| Role | Value | Notes |
|---|---|---|
| `--accent` | `#000000` | [e.g., brand primary] |
| `--accent-tint` | `#000000` | |
| `--surface-alt` | `#000000` | |

Extra tokens this style uses (optional; Base CSS and layouts never read them):

| Token | Value | Use |
|---|---|---|
| `--brand-deep` | `#000000` | [e.g., title slide field] |

Shape and type tokens, if changed:

| Token | Value |
|---|---|
| `--radius` | |
| `--outline-width` | |
| `--shadow` | |
| `--font-heading` | |
| `--font-body` | |
| `--mermaid-look` | `classic`, or another Mermaid look |

## 4. Type and scale
[Only if different from Base. Nothing visible may go below 14px.]

## 5. Base elements
[Only the elements that change, e.g. title slide, top-level slide background, number chips, "more below" cue wording, footer.]

## 6. Callouts
[Only what changes: shape (e.g. speech bubbles), labels, icons.]

| Type | Label | Icon |
|---|---|---|
| `TIP` | [e.g., Pro tip] | [e.g., Star] |

## 7. Slide types
[Only what changes, per type, e.g. the `[Recap]` label or footer line.]

## 8. Layouts
[Only what changes, e.g. outlined items instead of filled ones.]

## 9. Degrades
Use only when this style deliberately renders a tag more simply. Every tag still renders.

| Tag | Renders as |
|---|---|
| [e.g., `[Quick check]`] | [e.g., A plain vertical slide with the question and options; the answer in speaker notes] |

## 10. Frequency and balance
[Optional. A style may tighten `TAGS.md` limits, never loosen them.]

## 11. Don'ts
[What this style must never do.]
