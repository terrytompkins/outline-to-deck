# OUTLINE CONVENTIONS

How `OUTLINE.md` is laid out and how its structure maps onto the deck. The outline is written to map directly onto slides, so every rule here has a matching rule in Phase 2.

Related files:
- **`TAGS.md`**: every tag, marker, callout, slide type, directive and block, and what Phase 2 does with each.
- **`LAYOUTS.md`**: the layouts that `Layout:` can name.
- **`WORKFLOW.md`**: versions, the status comment, the approval gate, and how files are written.

## 1. Parts of the outline

In this order:

| Part | Form | In the deck? |
|---|---|---|
| Title line | `# OUTLINE — Title` | No |
| Status comment | `<!-- status: … -->` (fields in `WORKFLOW.md`) | No |
| Header lines | `**Status:**`, `**Session:**`, `**Facts verified:**` | No |
| Changes by version | `## Changes by version (outline-only working aid)` | No |
| Central message | `## Central message`: one or two sentences every section supports | No; may go into the title slide's speaker notes |
| Time plan | `## Time plan (outline-only working aid)` (§4) | Drives the agenda and build order |
| Front matter | `## Front matter: Title and agenda [All]` | Title slide and agenda |
| Topic sections | `## 1. Title` and below (§2) | Yes: the slides |
| Source reconciliation | `## Source reconciliation (outline-only working aid)`: a table of conflicts and resolutions | No |
| Coverage gaps | `## Coverage gaps (outline-only working aid)`: what is missing or thin, and the research that would fill it | No |

Separate the major parts with `---` lines. Any heading marked "(outline-only working aid)" is always stripped, whatever its name.

**Front matter** holds key lines: `Title:`, `Series:`, an optional `Framing line:`, and optional `Speaker notes:`. The agenda links to every top-level section in live order and is generated from the time plan.

## 2. Sections and slides

| Heading | Becomes |
|---|---|
| `## 3. Title` | A **horizontal** slide: one topic |
| `### 3.1 Title` | A **vertical** slide under its topic: an example, detail or exercise |
| `#### 3.1.1 Title` | Another vertical slide, placed right after its parent (Reveal.js has only two dimensions) |

- **Deeper headings aren't allowed.** Split the material or use a layout.
- **Top-level slides start with `Main points:`** followed by 3–5 bullets. Walking only the top-level slides must give a complete introduction to the talk.
- **Tags in headings:** a slide-type tag goes right after the number (`### 2.4 [Quick check] Title`); working-aid tags go at the end (`## 3. Title [All] [Core]`). See `TAGS.md`.
- **`[Backup]` slides** keep their number where they sit, but Phase 2 moves them to the Appendix.

## 3. Numbering

- **Numbers are IDs, not slide order.** Hierarchical: 1, 1.1, 1.1.1.
- **v0.1 may renumber** while the structure settles. **From v0.2 on, numbering is frozen:** a new section gets the next unused number at its level, and the time plan places it. Removed numbers are not reused.
- Refer to sections by number across chats: "revise 4.2", "add a subsection under 6".

## 4. Time plan

Rows in live presentation order:

```markdown
| # | Section | Full (min) | Live (min) | Priority |
|---|---|---|---|---|
| — | Title and agenda | 1 | 1 | Core |
| 1 | Why outline first | 6 | 3 | Core |
| 2 | Phase 1: the outline | 10 | 5 | Core |
| 4 | Phase 2: the deck | 5 | 0 | Self-guided |
| — | Q&A | — | 5 | |
| | **Total** | 22 | 14 | |
```

- **Full** is the time to cover everything in the section; **Live** is the time it gets in the session. The Full column is optional for short talks.
- **Priority** is `Core`, `Brief` or `Self-guided`, matching the section's priority tag. Live time 0 means the section stays in the hosted deck only.
- The time plan sets the **agenda order** and the **build order** in Phase 2. Every top-level section appears in it exactly once.
- The Live total must fit the session length in `BRIEF.md`.

## 5. What goes in a slide

A slide's body is the content under its heading, up to the next heading. It may hold:

- **Bullets**, including nested bullets one level deep.
- **Inline markers** inside bullets: sources, `As of`, `[TBD: …]`, `[UNVERIFIED]`, origin tags.
- **Key lines**: directives such as `Suggested visual:` and slide-type fields such as `Question:`. A key line may be written as its own paragraph or as a bullet, **except `Layout:` and `Diagram:`, which must be their own lines**: `Layout:` directly above the list it governs, and `Diagram:` directly above Claude's Mermaid block.
- **Callouts** (`> [!TYPE]` block quotes).
- **Fenced blocks** (`mermaid`, `chart`) and ordinary Markdown **tables**.
- **`Speaker notes:`**, as a paragraph or bullet.

Recommended order: main content, then any callout, then speaker notes last.

## 6. Writing for slides

- **One idea per slide.** If a slide needs two headlines, it is two slides.
- **Bullets are short:** about 25 words at most, and usually 3–6 bullets per slide. Long explanations go into speaker notes.
- **Facts carry their evidence:** a source link for anything checkable, `As of` for anything volatile (prices, versions, statistics, policies), `[UNVERIFIED]` for what couldn't be checked, `[TBD: …]` for what only the presenter knows.
- **No names of individuals**, in the outline or the deck: not transcript speakers, not authors of internal material, not anyone else. Describe internal input generically. The exceptions are the presenter on the title slide (if `BRIEF.md` says so) and authors inside published-source citations.
- **Mark origins:** every content bullet carries `[Seed]`, `[Research]`, or both. If a revision comes back mostly `[Seed]`, research is too thin.

## 7. Example

```markdown
## 3. Why code reviews stall [All] [Core]

Main points:
- Large pull requests wait longest for a first review. [Seed] [Research]
- Review guidance recommends small, focused changes. ([Example guide](https://example.com/review-guide)) As of November 2, 2026
- Our median wait for a first review: [TBD: median hours to first review]

> [!REMEMBER]
> One change per pull request.

Speaker notes: Ask the room how long their oldest open pull request has waited.

### 3.1 How a review moves [All]
Layout: process
- Open: the author opens a pull request
- Wait: it sits in the queue
- **Review: a reviewer reads it**
- Merge: changes land

### 3.2 [Quick check] Which gets reviewed first? [All]
Question: One 1,200-line pull request, or four 300-line ones?
Answer: Usually the small ones: each is quick to read, so reviewers start sooner.
```

Section 3 becomes a horizontal slide with three points, a Remember callout and a speaker note. Below it, 3.1 is a vertical slide showing the four steps as a process with "Review" emphasized, and 3.2 is a quiz slide whose answer appears on the next click.
