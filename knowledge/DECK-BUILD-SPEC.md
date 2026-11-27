# DECK BUILD SPEC (Phase 2)

How to turn the approved `OUTLINE.md` into a deck. Tags are defined in `TAGS.md`, layouts in `LAYOUTS.md`, looks in the style guides. This file covers the build: output, tools, the markup Claude writes, and the checks.

## 1. Output

- **One self-contained HTML file**, named in `BRIEF.md`, that opens from a `file://` URL or any static web server.
- **Libraries come only from the CDNs pinned in `tools/pins.json`**, each with an SRI hash and a fallback CDN. `assemble-deck.py` writes these tags; never write them by hand or use "latest".
- **Everything else is inlined** by the assembler: `runtime/base.css`, the style's CSS, `runtime/deck.js`, and local images as data URIs.
- Don't use Claude's Slides artifact type, PowerPoint, or any other format for the deck.

## 2. Build steps

The tools come in `deck-tools.zip`, attached to the chat (see its `README-BUNDLE.md`). Unzip it, run `npm install` there, and copy `OUTLINE.md` and `BRIEF.md` into the folder exactly as `project_read` returns them.

1. **Confirm** the pinned library versions, the style, and anything the linter reports.
2. **Lint:** `python3 tools/lint-outline.py OUTLINE.md --knowledge knowledge`. Errors (E codes) stop the affected slide; fix them with the presenter first.
3. **Write fragments** to a `frags/` folder, following §4: `title.html`, `agenda.html`, `topic-N.html` for each top-level section, and `appendix.html` / `sources.html` when needed.
4. **Assemble:** `python3 tools/assemble-deck.py build --fragments frags --style STYLE --outline OUTLINE.md --out DECK.html` (add `--build on` if `BRIEF.md` turns build animations on).
5. **Check:** `python3 tools/check-deck.py DECK.html --outline OUTLINE.md --shots shots --json`. Fix fit problems with the fallback ladder (`LAYOUTS.md` §5), re-assemble, re-check.
6. **Look** at the screenshots: spacing, contrast, placement.
7. **Write `OUTPUT-NOTES.md`** from the checker's JSON, and set `deck:` in `OUTLINE.md`'s status comment.

Pass 1 builds the title, agenda and every horizontal slide; pass 2 adds vertical slides by priority. Later changes: `assemble-deck.py replace-topic DECK.html N frags/topic-N.html`, and `assemble-deck.py edit` for exact-string fixes (each must match exactly once).

**If the bundle isn't attached,** ask for it. If the presenter can't attach it, write the deck following §4 by hand with the CSS and runtime from the style guides, and run the §7 checks yourself; note in `OUTPUT-NOTES.md` that the tools weren't used.

## 3. Mapping from the outline

| Outline | Deck |
|---|---|
| Front matter | `title.html` and `agenda.html` |
| `## N. Title` | `<section id="sN">` stack in `topic-N.html`; its first child is `<section class="topic" data-number="N">` |
| `### N.M`, `#### N.M.K` | Further `<section data-number="N.M">` children in the same stack, in numeric order |
| `[Backup]` subsection | A section in `appendix.html` with `data-backup-for` = its parent's number |
| Time plan | Agenda order and build order |
| Working aids, outline-only sections | Nothing (stripped) |

Keep slides sparse: detail goes to speaker notes. Never shrink text below the autofit floor; split instead.

## 4. Markup contract

Write only this markup. The runtime adds everything in §5; don't write those parts yourself.

```html
<!-- title.html -->
<section id="title" class="cover">
  <div class="cover__card">
    <p class="series">Series</p><h1>Title</h1><p class="lead">Framing line</p>
    <p class="presenter">Presenter, if BRIEF.md says so</p>
  </div>
  <aside class="notes">…</aside>
</section>

<!-- agenda.html: one <li> per top-level section, in time-plan order -->
<section id="agenda" class="agenda"><h2>Agenda</h2>
  <ol class="agenda-list">
    <li data-number="1"><a href="#/s1">Section title</a></li>
    <li data-number="4" class="self-guided"><a href="#/s4">Section title</a></li>
  </ol>
</section>

<!-- topic-3.html -->
<section id="s3">
  <section class="topic" data-number="3"><h2>Title</h2> … </section>
  <section data-number="3.1"><h3>Title</h3> … </section>
</section>
```

Inside a slide:

| Element | Markup |
|---|---|
| Bullets, paragraphs, tables | Plain `<ul>`, `<ol>`, `<p>`, `<table>` |
| Code | `<pre class="code"><code>…</code></pre>`; inline `<code>` |
| `[TBD: x]` | `<span class="tbd">TBD: x</span>` |
| `[UNVERIFIED: why]` | `<span class="unverified">Unverified</span>`, and the reason in the notes |
| Sources and As of | `<footer><span class="asof">As of Month D, YYYY</span><a href="…">Title</a></footer>` (one footer per slide) |
| Speaker notes | One `<aside class="notes">` per slide, holding every `Speaker notes:` line |
| Callout | `<div class="callout" data-type="tip" data-title="Optional title"><p>…</p></div>` (type in lowercase; aliases allowed) |
| Layout | As `LAYOUTS.md` §4 |
| Diagram | `<figure class="diagram"><pre class="mermaid">…source from the outline…</pre></figure>`; two on one slide go in `<div class="diagram-pair">` |
| Chart | `<figure class="chart" data-type="bar" data-title="…" data-unit="…"><table>…the outline's table…</table></figure>` |
| Suggested visual | `<figure class="visual"><svg viewBox=… role="img" aria-label="…">…</svg><figcaption>Illustrative, not measured data.</figcaption></figure>`; colors only through role variables, e.g. `stroke="var(--accent)"`, text classes `t-ink`, `t-cap`, `t-accent`, `t-warn` |
| Image | `<figure class="image"><img src="file.png" alt="…"><figcaption>…</figcaption></figure>` |
| Embed | `<figure class="embed"><iframe src="https://…" loading="lazy" title="…"></iframe><a class="embed-link" href="https://…">Open the page</a></figure>` |

Slide types put `data-type` on the `<section>`:

| Tag | Section | Body |
|---|---|---|
| `[Quick check]` | `data-type="quick-check"` | `<p class="question">…</p>`, optional `<ol class="options"><li>…</li></ol>`, `<div class="answer">…</div>`; notes: "Pause for answers before revealing." |
| `[Myth vs fact]` | `data-type="myth-vs-fact"` | `<div class="myths">` holding `<div class="myth"><p>…</p></div><div class="fact"><p>…</p></div>` pairs |
| `[Recap]` | `data-type="recap"` | `<ul class="checks"><li>…</li></ul>` |
| `[Try it yourself]` | `data-type="try-it-yourself"` | `<p class="meta">Time: …</p>`, `<ol class="steps"><li>…</li></ol>`, `<div class="outcome">…</div>` |
| `[Quote]` | `data-type="quote"` | `<blockquote class="quote"><p>…</p><cite>Attribution</cite><p class="context">…</p></blockquote>` and the footer source |
| `[Key figure]` | `data-type="key-figure"` | `<div class="key-figure"><p class="figure">30 hours</p><p class="figure-label">…</p><p class="context">…</p></div>` and the footer |
| `[Backup]` | `data-type="backup" data-backup-for="N"` in `appendix.html` | Ordinary content |

```html
<!-- appendix.html (only when the outline has [Backup] slides) -->
<section id="appendix">
  <section class="appendix-divider"><h2>Appendix</h2></section>
  <section data-number="1.4" data-type="backup" data-backup-for="1"><h3>Title</h3> … </section>
</section>

<!-- sources.html (only when BRIEF.md asks for a Sources slide) -->
<section id="sources" class="sources" data-auto data-visibility="uncounted"><h2>Sources</h2></section>
```

Rules: no `<script>` or `<style>` elements in fragments (the assembler refuses scripts); inline `style` attributes only for one-off positioning inside a visual; every top-level stack has `id="sN"`.

## 5. What the runtime adds (don't write these)

Number chips and trail markers from `data-number`; slide-type labels and icons; the answer label and click-to-reveal; myth and fact icons; recap checks and the "Next" line; the Try-it badge and the outcome label; callout tabs, icons and labels; the "more below" cue; page numbers (Appendix and Sources aren't counted); backup and back links; the Sources list; layout geometry and compaction; charts; Mermaid configuration and the `key`, `good` and `warn` classes from the style; autofit; and Reveal's configuration. Labels come from the style's CSS (`--label-*`).

## 6. Fit

- Autofit shrinks a slide's text in `em`, never below 0.62, and never lets content touch the footer. Layouts compact first. The results land in `data-fit` and `data-compact`, which the checker reports.
- If a slide still doesn't fit, use the fallback ladder in `LAYOUTS.md` §5: compact, fall back, split into "N.M (continued)", or plain bullets. Never truncate silently or reword.
- Fixed chrome (footer, page number, cues, badges) stays at 14px or more.

## 7. Verification

`check-deck.py` automates 1–8 and 10–11. Report results as numbers, and copy them into `OUTPUT-NOTES.md`.

1. Visible when current.
2. No overflow of the 1280×720 frame.
3. No footer collision.
4. Every diagram rendered; no clipped diagram labels.
5. No console errors.
6. Every `.layout` matches its contract; no item text clipped.
7. No visible text below 14px.
8. Every slide with outline speaker notes has a notes block.
9. Tag audit: no working-aid text visible; every `[TBD]` shows as a chip; **no individual names** in visible text or notes except the presenter on the title slide (if `BRIEF.md` says so) and authors in source citations. Names are checked by eye.
10. Final state and click-through both clean (`--step`).
11. Outline cross-check (`--outline`): every outline slide is in the deck with its layouts.
12. Screenshots reviewed for spacing, contrast and placement.

## 8. Known pitfalls

1. **Never set `position` on `.reveal .slides section`.** Reveal positions slides itself; a rule like `position: relative` stacks later slides below the viewport, with no console error.
2. **Mermaid must be configured before the page finishes loading,** or it renders every diagram at load, inside hidden slides, with its default theme. The runtime does this; don't add your own Mermaid setup.
3. **Reveal's built-in slide number collides with the arrows.** The runtime draws its own page numbers.
4. **Slide-level rules lose to the generic section rule.** Write `.reveal .slides section.cover`, not `.reveal .cover`. Reveal sets `display: block` on the current slide, so lay out inside a wrapper, not on the slide.
5. **Claude's in-chat preview doesn't load CDN scripts,** so a correct deck can look broken there. Use the checker or a real browser.
6. **Screenshots during a fade show two slides.** The checker turns transitions off; do the same for any manual screenshots.
