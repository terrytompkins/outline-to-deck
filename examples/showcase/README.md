# Showcase

One outline, built in all three styles. It uses every tag family, all eleven layouts and all three chart types, so it doubles as the visual test for styles and the runtime.

| File | What it is |
|---|---|
| `OUTLINE.md`, `BRIEF.md` | The approved outline and its brief |
| `fragments/` | The slide fragments written in Phase 2 (DECK-BUILD-SPEC.md §4) |
| `deck-base.html`, `deck-field-guide.html`, `deck-toons.html` | The same deck in each style; open any of them in a browser |
| `OUTPUT-NOTES.md` | The build notes for the Field Guide deck |

Rebuild and check a deck from the repository root (after `npm install`):

```bash
python3 tools/assemble-deck.py build --fragments examples/showcase/fragments --style toons \
  --outline examples/showcase/OUTLINE.md --out examples/showcase/deck-toons.html
python3 tools/check-deck.py examples/showcase/deck-toons.html --outline examples/showcase/OUTLINE.md --shots shots
```

The linter reports three balance warnings (W108): sections 3, 4 and 5 carry more layouts than a real talk should, because a showcase shows them all.

## Where each tag appears

| Tag or feature | Section |
|---|---|
| Main points, origin tags, audience and priority tags | every top-level section |
| `[TBD: …]` placeholder chip | 1 |
| `[UNVERIFIED]` pill, reason in the notes | 1.1, 5.1 |
| Source links and `As of` in the footer | 1, 1.3, 3, 4, 4.1, 5.1, 6, 6.2, 6.3 |
| Speaker notes | title, 1 |
| `Suggested visual:` | 1.1 |
| `Diagram:` with Mermaid | 2.1 |
| Callouts: Remember, Tip, Watch out, Under the hood, Field note | 1, 2.1, 2.2, 3.3, 5.1 |
| `[Myth vs fact]`, `[Quote]`, `[Quick check]`, `[Try it yourself]`, `[Recap]`, `[Key figure]` | 1.2, 1.3, 2.3, 2.4, 2.5, 4.1 |
| `[Backup]` (Appendix, back links) | 1.4, 6.4 |
| Layouts: process, list (numbered), matrix (axes), radial, timeline, cycle, pyramid, funnel, venn, hierarchy, columns (plain and before-after), process (steps) | 2, 3.1, 3.2, 3.3, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 5 and 5.2, 6.1 |
| Charts: column, line, bar | 5.1, 6.2, 6.3 |
| Code block | 6.4 |
| Self-guided label in the agenda | 6 |
| Sources slide | last slide |

Not shown here: the Note callout, `Image:` and `Embed:`. The test fixtures in `tools/tests/fixtures/` cover the remaining callout and every layout variant.
