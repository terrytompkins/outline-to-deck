# TAGS

The registry of every tag an outline may use, and what Phase 2 does with each one. This file is the single source: `OUTLINE-CONVENTIONS.md` explains how an outline is structured, style guides decide how tags *look*, and `LAYOUTS.md` details the layouts named here. No other file defines a tag.

Every tag is either **stripped** (an outline-only working aid) or **rendered** by every style. Nothing is left to judgment.

Tables marked `<!-- registry: … -->` are read by `tools/lint-outline.py`. Keep their columns in the order shown.

## 1. The five forms

| Form | Syntax | Used for |
|---|---|---|
| Heading tag | `### 2.4 [Quick check] Title`: slide type right after the number. Working aids at the end: `## 3. Title [All] [Core]` | Whole-slide treatments; outline-only metadata |
| Inline marker | `[TBD: …]`, `[UNVERIFIED]`, `[Seed]`, `As of …`, `([Title](url))` inside a bullet | Facts about one statement |
| Callout | A block quote whose first line is `> [!TYPE]`, optionally followed by a title | A boxed aside inside a slide |
| Key line | `Key: value` at the start of a line or bullet | Directives (`Layout:`, `Diagram:`, `Image:` …) and the fields of slide types (`Question:` …) |
| Fenced block | ```` ```mermaid ````, ```` ```chart ```` | Structured content: diagrams Claude writes, chart data |

Square brackets are a closed vocabulary: only the tags in this file, the audience tags declared in BRIEF.md, and Markdown links (`[text](url)`). Anything else in square brackets is an error.

## 2. Rules for every tag

1. **Only registered tags.** In Phase 2, an unknown tag, an unknown key line, or a missing required field **stops that slide** and is reported. Nothing is guessed. The linter finds these in Phase 1.
2. **Fit problems never stop the build.** Too many items, long labels or overflow follow the fallback ladder in `LAYOUTS.md` and are recorded in `OUTPUT-NOTES.md`.
3. **Every style renders every rendered tag.** A style may change labels, icons, colors and shapes, tighten a limit, or declare a *degrade* (a simpler rendering it uses instead). It may not add, remove or loosen tags.
4. **Say what you added.** When Claude adds a callout, slide type, layout, diagram or visual in Phase 1, it lists it in its summary of changes, so the presenter can accept or remove it.
5. **Slide-type slides are self-contained.** A slide with a slide-type tag carries no callouts and no layouts.
6. **"Per section"** means per top-level section, including its vertical slides. **"Per slide"** means one heading and its content.
7. **Never invent content.** Missing facts stay `[TBD: …]`; quotes and figures come only from sources in the outline.

<!-- registry: limits -->
| ID | Scope | Rule | Value |
|---|---|---|---|
| `slide-types-per-heading` | heading | slide-type tags per heading | 1 |
| `callouts-per-slide` | slide | callouts per slide | 1 |
| `layouts-per-slide` | slide | layouts per slide | 2 |
| `diagrams-per-slide` | slide | `Diagram:` blocks per slide | 2 |
| `section-layout-share` | section | share of slides with a layout, at most | 0.5 |
| `deck-no-callout-share` | deck | share of vertical slides with no callout, at least | 0.5 |
| `watchout-consecutive` | deck | `WATCHOUT` on consecutive slides | no |

The layout and diagram limits per slide are **fit limits**: when two layouts or two diagrams don't fit at a readable size, Phase 2 moves the second one to a "(continued)" slide and records it in `OUTPUT-NOTES.md`. The other limits are rules the linter enforces.

## 3. Working aids (outline only; always stripped)

<!-- registry: working-aids -->
| Tag | Form | Where | Meaning |
|---|---|---|---|
| `[Seed]` | Inline marker | End of a bullet or heading | From seed files or the presenter's own input |
| `[Research]` | Inline marker | End of a bullet or heading | From Claude's research |
| Audience tags from BRIEF.md | Heading tag | End of a heading | Who the section is for, e.g. `[All]`, `[Technical]` |
| `[Core]`, `[Brief]`, `[Self-guided]` | Heading tag | End of a heading, and the time plan | Priority. Self-guided sections get a small "self-guided" label in the agenda. |
| `(outline-only working aid)` | Heading suffix | A whole section | Changes by version, Time plan, Source reconciliation, Coverage gaps. Never in the deck. |
| Header lines, Central message | Structure | Top of the outline | Title line, status comment, `**Status:**`, `**Session:**`, `**Facts verified:**`. The central message may go into the title slide's speaker notes. |
| `Main points:` | Key line (label only) | Top-level slide | The label is stripped; its bullets become the slide body. |

If a revision comes back mostly `[Seed]`, research is too thin. Every revision includes a Coverage gaps note.

## 4. Content markers (rendered)

<!-- registry: markers -->
| Marker | Syntax | Phase 2 rendering |
|---|---|---|
| Speaker notes | `Speaker notes: text` as a paragraph or bullet | `<aside class="notes">`; never visible on the slide |
| As of | `As of Month D, YYYY` | Footer "As of" label on that slide |
| Source | `([Source title](url))` | Footer source link on that slide; collected into the Sources slide if BRIEF.md asks for one |
| Unverified | `[UNVERIFIED]` or `[UNVERIFIED: reason]` | Small pill beside the claim; the reason goes to speaker notes |
| Placeholder | `[TBD: description]` | Visible chip showing the description; never replaced with invented data |

## 5. Callouts

Syntax:

```markdown
> [!TIP] Optional title
> Ask for the length you need: "bullet summary, under 200 words."
```

The type is uppercase with no spaces. Text after the type is an optional title; otherwise the style's label is used. GitHub shows its own five types (NOTE, TIP, IMPORTANT, WARNING, CAUTION) as alerts; the others appear on GitHub as plain quotes, which is fine.

<!-- registry: callouts -->
| Type | Default label | Purpose | Proposal rule | Default icon | Limit |
|---|---|---|---|---|---|
| `NOTE` | Note | Useful context | Background that helps understanding but isn't the slide's point | Info circle | 1 per slide |
| `TIP` | Tip | A shortcut or better way to do something | A practical technique that saves time or effort and stands on its own | Lightbulb | 1 per slide |
| `REMEMBER` | Remember | The one thing to keep from this slide | A slide's single most important takeaway, when the slide has several points | Bookmark | 1 per slide; ≤ 2 per section |
| `WATCHOUT` | Watch out | A hazard, common mistake, or cost trap | A mistake attendees are likely to make, or a consequence that's easy to miss | Warning triangle | 1 per slide |
| `UNDERTHEHOOD` | Under the hood | Technical depth that others can skip | A mechanism or detail that explains why, aimed at technical attendees | Gear | 1 per slide |
| `FIELDNOTE` | Field note | A real example, story, or observed result | An anonymized internal example or a published case that grounds an abstract point | Notebook | 1 per slide; ≤ 3 per section |

<!-- registry: callout-aliases -->
| Alias | Renders as |
|---|---|
| `IMPORTANT` | `REMEMBER` |
| `WARNING` | `WATCHOUT` |
| `CAUTION` | `WATCHOUT` |

An alias keeps its own word as the label unless the callout has a title.

## 6. Slide types

Put the tag in the heading, right after the number: `### 2.4 [Quick check] Which costs more?`. Fields are key lines in the slide body. A field "followed by bullets" takes the bullet or numbered list directly under it.

<!-- registry: slide-types -->
| Tag | Purpose | Proposal rule | Required fields | Optional fields | Limit |
|---|---|---|---|---|---|
| `[Try it yourself]` | A hands-on exercise that also works self-guided | A skill attendees should practice, with a result they can see | `Time:`; `Steps:` followed by numbered single actions; `Expected outcome:` | — | — |
| `[Quick check]` | A fast, low-stakes question to the room | After a section's key concept, when there's a common misconception or a surprising answer | `Question:`; `Answer:` | `Options:` followed by 2–4 bullets | 1 per section |
| `[Myth vs fact]` | Correct common misconceptions directly | When research or seeds surface wrong beliefs the audience likely holds | 1–3 pairs of `Myth:` and `Fact:` lines | — | 2 per deck |
| `[Recap]` | A short recap closing a section | The last vertical slide of a Core section with four or more subsections | `Points:` followed by 3–4 bullets | — | 1 per section |
| `[Quote]` | A sourced quotation worth showing word for word | When a published source states a point more memorably than a paraphrase | `Quote:` (verbatim, ≤ 40 words); `Attribution:` (a role or a publication; never a private individual's name); a source link | `Context:` one sentence | 2 per deck |
| `[Key figure]` | One number that carries the section | A single verified figure central to the section's argument | `Figure:` (number and unit); `Label:` (≤ 8 words); a source link; `As of` | `Context:` one sentence | 1 per section |
| `[Backup]` | Detail held back for questions | Material likely to be asked about but not worth live time | — | — | — |

Phase 2 rendering, in every style:

- **`[Try it yourself]`:** a badge (top-right by default), the time under the heading, numbered steps, and an outcome panel labeled "You should see".
- **`[Quick check]`:** a "Quick check" label, the question large, options as cards, and the answer on the next click. Speaker notes get "Pause for answers before revealing."
- **`[Myth vs fact]`:** two columns; each fact appears on a click.
- **`[Recap]`:** the points as a checklist, and a footer line naming the next section from the time plan.
- **`[Quote]`:** the quotation large, the attribution and context below, the source in the footer. A quote that can't be checked against its source carries `[UNVERIFIED]`.
- **`[Key figure]`:** the figure very large, the label under it, the context line, source and "As of" in the footer. `Figure:` may be `[TBD: …]`.
- **`[Backup]`:** built into an **Appendix** stack after the last section, not counted in page numbers (`data-visibility="uncounted"`). Its parent slide gets a small "Backup: title" link, and the backup slide gets a "Back" link. Numbering stays where the heading sits in the outline.

Reserved: `[Demo]` arrives in v2.1. Until then the linter reports it as unknown.

## 7. Directives (key lines)

<!-- registry: directives -->
| Key | Value | Scope | Companions | Proposal rule | Phase 2 |
|---|---|---|---|---|---|
| `Layout:` | A layout name, then optional `; option` parts | The bullet list directly below | Layout fields such as `X axis:` (see `LAYOUTS.md`) | Bullets already fit a layout's shape (see `LAYOUTS.md`) | The list rendered as that layout |
| `Diagram:` | One plain-language sentence describing the diagram | Slide | A ```` ```mermaid ```` block directly below, written by Claude | Content with branches, decisions, loops or interactions that a layout can't show | The diagram, rendered with the style's Mermaid settings |
| `Suggested visual:` | A description | Slide | — | An illustration would explain faster than words | An inline SVG Claude designs; captioned "Illustrative, not measured data" unless drawn from numbers in the outline |
| `Embed:` | An `https://` URL | Slide | Optional `Caption:` | Only when the presenter asks to show a live page | A framed live page; when printed, offline, or if the site refuses framing, a link card |
| `Image:` | A file name from project knowledge or the chat, or an `https://` URL | Slide | Required `Alt:`; optional `Caption:` and a source link | Only for images the presenter supplies | The picture; local files embedded in the deck |

Notes:

- **`Layout:`** sits on its own line directly above an ordinary bullet list; `LAYOUTS.md` lists the names, options, data shapes, limits and fallbacks.
- **`Diagram:`** is the author-facing part. Presenters never write Mermaid: to change a diagram they edit the sentence or ask in words, and Claude rewrites the block. Limits: about 9 nodes, labels ≤ 6 words, emphasis only through the classes `key`, `good` and `warn`. Two diagrams may share a slide when seeing them side by side is the point (a before-and-after, say); keep each to about 5 nodes.
- **`Suggested visual:`** is for illustrations. For real numbers, use a `chart` block instead, so the data is checkable.
- **`Image:`** Claude never downloads images from the web for a deck. Every image needs `Alt:` text.

## 8. Fenced blocks

<!-- registry: blocks -->
| Block | Written by | Placement | Phase 2 |
|---|---|---|---|
| `mermaid` | Claude only | Directly under a `Diagram:` line | Rendered by Mermaid on first view of the slide |
| `chart` | The presenter or Claude, from numbers in the outline | Anywhere in a slide body | An SVG chart drawn by the deck runtime in the style's series colors |
| any other language, or none | The presenter or Claude | Anywhere in a slide body | A code block, shown as written in `--font-code`; keep it to about 12 lines |

**Chart blocks.** `key: value` lines, then a Markdown table. The first column holds categories, each further column is a series.

````markdown
```chart
type: bar
title: Hours to first review, by pull-request size
unit: hours
| Size | Hours |
| Under 100 lines | 4 |
| 100–500 lines | 11 |
| Over 500 lines | 30 |
```
````

- `type:` is `bar` (horizontal), `column` or `line`. `title:` is required; `unit:` is optional.
- At most 12 categories and 5 series. Every cell is a number; no `[TBD]` inside a chart. If data is missing, use `[TBD: …]` in a bullet instead of the chart.
- The slide still needs a source link and, for volatile data, `As of`.

## 9. Deck-level options (in BRIEF.md)

Not tags; set once per presentation.

| Option | Values | Default |
|---|---|---|
| Sources slide | yes / no | no |
| Layout use | encourage / sparingly / off | encourage |
| Build animations | on / off (items appear one click at a time) | off |

## 10. Example

```markdown
## 3. Why code reviews stall [All] [Core]

Main points:
Layout: process
- Open: the author opens a pull request [Seed]
- Wait: it sits in the queue [Research]
- **Review: a reviewer reads it**
- Merge: changes land

> [!REMEMBER]
> One change per pull request.

Speaker notes: Ask the room how long their oldest open pull request has waited.

### 3.1 [Key figure] How long large pull requests wait
Figure: 30 hours
Label: Median wait for a first review, over 500 lines
Context: Under 100 lines, the wait was 4 hours.
([Example study](https://example.com/review-study)) As of November 2, 2026

### 3.2 [Quick check] Which gets reviewed first?
Question: One 1,200-line pull request, or four 300-line ones?
Answer: Usually the small ones: each is quick to read, so reviewers start sooner.
```

In the deck, `[All]`, `[Core]`, `[Seed]` and `[Research]` disappear; the main points render as a four-step process with "Review" emphasized; the callout becomes a styled Remember box; the speaker note goes to the notes view; 3.1 becomes a big-number slide with its source and date in the footer; and 3.2 becomes a quiz slide whose answer appears on the next click.
