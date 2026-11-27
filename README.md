# outline-to-deck

Turn an idea into a presentation with Claude: a researched, numbered Markdown outline first, then one self-contained Reveal.js deck built from it. You revise cheap text, approve it, and build the deck once.

- **Tag what content is, not how it looks.** Callouts, quizzes, recaps, key figures, quotes and backup slides are tags in the outline; the style decides their look.
- **SmartArt-style layouts from bullets.** One line (`Layout: process`) turns a list into a process, timeline, matrix, cycle, pyramid, Venn and more: eleven layouts in all.
- **Three styles, every tag in each.** Base, Field Guide and Toons; make your own from a template.
- **Tools do the mechanical work.** A linter checks the outline; a drafter writes the slide markup; an assembler builds the deck; a checker verifies every slide.

See [the showcase](examples/showcase/) for one outline built in all three styles.

## Quick start

1. **Create a Claude Project.** Paste the text under the line in [PROJECT-INSTRUCTIONS.md](PROJECT-INSTRUCTIONS.md) into its instructions.
2. **Upload the knowledge files** from `knowledge/`: BRIEF.md, OUTLINE.md, DECISIONS.md, OUTPUT-NOTES.md, WORKFLOW.md, OUTLINE-CONVENTIONS.md, TAGS.md, LAYOUTS.md, DECK-BUILD-SPEC.md, `styles/STYLE-BASE.md`, and the style you'll use (for example `styles/STYLE-FIELD-GUIDE.md`). Optionally add `tools/outline_parser.py` and `tools/lint-outline.py`.
3. **Add your seed files** (notes, transcripts, earlier outlines). They're leads, not the scope.
4. **Get the tools bundle:** download `deck-tools.zip` from the [latest release](https://github.com/terrytompkins/outline-to-deck/releases), or build it with `python3 tools/make-bundle.py` (it writes `dist/deck-tools.zip`). Attach it to the chat when you build the deck (and in outline chats if you want linting).
5. **Start a chat:** "Use guided mode. Take me from my idea to a finished deck." In any later chat: "Continue my deck."

Claude interviews you for the brief, researches and drafts the outline, revises it with you, has it reviewed in a fresh chat, asks for your approval, then builds and checks the deck. Prefer to drive each step yourself? Use the prompts in [PROMPTS.md](PROMPTS.md).

## What's in the repository

| Path | What it is |
|---|---|
| `PROJECT-INSTRUCTIONS.md` | The Project's instructions |
| `PROMPTS.md` | Prompts for manual mode |
| `knowledge/` | State-file starters, the rules, and the styles |
| `runtime/` | CSS and JavaScript inlined into every deck |
| `tools/` | Linter, fragment drafter, assembler, checker, notes writer, bundle builder, library pins, tests |
| `examples/showcase/` | One outline built in all three styles |
| `docs/REFERENCE.md` | The complete reference: how everything works and why |
| `docs/V2-PLAN.md`, `docs/M0-FINDINGS.md`, `docs/history/` | The v2 plan, test findings and earlier designs |
| `teaching/` | Material from the v1 workshops |

## Working on the tools

```bash
npm install                                   # local Reveal.js and Mermaid for the checker
pip install playwright && playwright install chromium
python3 -m unittest discover tools/tests      # all tests
python3 tools/sync-reference.py               # after editing TAGS.md or LAYOUTS.md
```

The deck loads Reveal.js 6.0.2 and Mermaid 12.3.0 from CDNs pinned in `tools/pins.json` with SRI hashes; `python3 tools/update-pins.py` refreshes them. Decks need a current browser (Mermaid 12 requires ES2024 and Safari 17.4 or later).

## Licenses

Code (`tools/`, `runtime/`, CSS) is under the [MIT License](LICENSE). Documents (`knowledge/`, `docs/`, `examples/`, `teaching/`, prompts and instructions) are under [CC BY 4.0](LICENSE-docs.md).
