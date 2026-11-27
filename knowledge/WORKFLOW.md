# WORKFLOW

How a presentation moves from idea to finished deck: the two working modes, how Claude works out where things stand, the steps in order, which files to open at each step, and how progress is kept across chats.

## 1. Why the process looks like this

- **Chats don't share history.** Each chat starts with only the project instructions and the list of knowledge files, so progress must live in files: BRIEF.md, OUTLINE.md, DECISIONS.md and OUTPUT-NOTES.md.
- **Knowledge files are read on demand.** Claude sees their names, not their contents, until it opens one (`project_read`). A rule takes effect only when its file is open, so each step in §5 names the files to open.
- **Content first, deck second.** Text is cheap to write, revise and re-read; a generated deck is expensive on all three. Every "redo the deck" pays for the whole deck again.
- **An explicit gate.** Without one, Claude tends to jump to slides early. Phase 2 starts only when DECISIONS.md records approval.
- **Tools do the mechanical work.** A linter checks the outline; an assembler, a shared runtime and a checker build and verify the deck. They come in `deck-tools.zip`, attached to the chat when needed.

## 2. Setup (once per presentation)

1. Create a Claude Project. Paste PROJECT-INSTRUCTIONS.md into its instructions.
2. Upload the knowledge files:
   - **State:** BRIEF.md, OUTLINE.md, DECISIONS.md, OUTPUT-NOTES.md (the starters).
   - **Rules:** WORKFLOW.md, OUTLINE-CONVENTIONS.md, TAGS.md, LAYOUTS.md, DECK-BUILD-SPEC.md.
   - **Styles:** STYLE-BASE.md, plus the style you'll use (for example STYLE-FIELD-GUIDE.md).
   - **Optional:** `outline_parser.py` and `lint-outline.py`, so Claude can lint the outline without the bundle.
3. Upload seed inputs. Condense large or noisy ones first (§8).
4. Keep `deck-tools.zip` handy. Attach it to the chat for Phase 2, and to Phase 1 chats when you want the outline linted.
5. In the first chat, say "Use guided mode" (Claude interviews you and carries on), or use a prompt from PROMPTS.md (manual mode).

**Picking up later.** In any new chat, say "continue my deck". Claude reads the state files, says where things stand, and takes the next step (guided) or names it and does only that step (manual).

## 3. Two modes

- **Guided.** Claude leads through the steps in §5 in order, asks for what it needs, pauses at every checkpoint, and says when to start a new chat. The presenter answers questions, makes decisions and reviews files.
- **Manual.** The presenter leads with the prompts in PROMPTS.md or their own requests. Claude does exactly the step asked for, writes the state files at its checkpoints, then stops. It may name the next step in one line but never starts it.

Both modes follow the same rules, write the same files and respect the same gate.

**Picking the mode** from the presenter's first message in each chat, in this order:
1. **The message names a mode:** use it.
2. **It asks for one specific step** (a PROMPTS.md prompt, "revise 4.2"): do that step in manual mode without asking. If BRIEF.md says guided, end by offering in one line to carry on in guided mode.
3. **It is open-ended** ("continue my deck", "hi"): use BRIEF.md's **Working mode** and say so in one line ("Continuing in guided mode. Say 'manual mode' to switch."). If it isn't set, ask once and do nothing else in that message:

   > Which way would you like to work?
   > - **Guided** (recommended): I'll walk you through each step with questions, pause for your decisions, and tell you when to start a new chat.
   > - **Manual**: you run each step yourself with the prompts in PROMPTS.md.

The presenter can switch at any time. Record the choice in BRIEF.md's **Working mode** the next time BRIEF.md is written (write it now if it won't be written again soon).

## 4. Where things stand

Before acting on an open-ended request, and at the start of every guided step, read BRIEF.md, OUTLINE.md and DECISIONS.md and work out the stage:

| Check, in order | Stage | Next step |
|---|---|---|
| BRIEF.md still has `[TBD: …]` fields | A. Brief | Interview to fill them |
| OUTLINE.md is still the v0.0 starter | B. First outline | Research and write v0.1 |
| Outline v0.1 or later; status says `reviewed: no` | C. Refine | Revise until the presenter is ready for review |
| Status says `reviewed: pending`; no gate entry | D. Independent review | Run the review |
| `reviewed:` names a version; no gate entry | E. Approve | Ask for approval |
| Gate entry present; `deck: none` | F. Deck, pass 1 | Build the horizontal slides |
| `deck: pass 1` or `deck: core` | G. Deck, pass 2 | Build or finish the vertical slides |
| `deck: complete` | H. After the build | Changes, style switch, or wrap-up |

If the files disagree or a field is missing, work it out from DECISIONS.md and "Changes by version", and ask if it is still unclear. Then tell the presenter where things stand in a line or two, for example: "Where we are: outline v0.3, ready for its independent review. Next: the review."

### 4.1 The gate

No Phase 2 work (slides, HTML, slide-level design, the deck file) happens until DECISIONS.md contains `- YYYY-MM-DD · Decided · Outline vX.Y approved; Phase 2 begins.` This holds in both modes and however the request is worded ("just make a few slides to see how it looks"). Otherwise reply along these lines:

> The outline hasn't been approved yet (current version: v0.4). If you'd like to approve it now, I'll record the decision and we can start on the deck.

If the outline hasn't had its independent review, add one line saying so and offer it, but leave the choice to the presenter.

**What counts as approval:** the approver named in BRIEF.md explicitly approves a specific version. "Yes, approve v0.4" counts; "looks good" in reply to something else doesn't. In guided mode Claude asks directly ("Do you approve outline v0.4 for the deck?").

**On approval:** add the gate entry to DECISIONS.md, set OUTLINE.md's status to `approved: vX.Y` and phase 2, write both files, confirm the writes by name, then hand off to a fresh chat (§6).

## 5. Steps

Each step lists the files to open, the work, what is written, and where it pauses. The matching PROMPTS.md prompt is named so the two modes stay in step.

### A. Brief (prompt 1)
- **Open:** BRIEF.md.
- Interview the presenter to fill every `[TBD: …]`, two to four questions at a time, one section per round, offering sensible defaults ("Approver: you, unless someone else signs off?").
- For seed inputs, list the project files that aren't template files and ask what each is and how far to trust it.
- Fill **Working mode** with the mode in use.
- **Done when** no `[TBD: …]` remains, or the presenter says to leave one open ("to be decided").
- **Write** BRIEF.md; summarize it in five lines. **Pause:** "Next: I'll research the topic and draft outline v0.1. Ready?"

### B. First outline (prompt 2)
- **Open:** OUTLINE-CONVENTIONS.md, TAGS.md, LAYOUTS.md (§1–3), the active style guide, OUTLINE.md, DECISIONS.md, and the seed files.
- If something in the brief would change the structure and is unclear, ask up to three questions first.
- Map the coverage dimensions, research (seeds are leads, not the scope), and write v0.1: time plan, origin tags, Coverage gaps, source reconciliation.
- Add tags where they genuinely fit, following their proposal rules and limits: callouts, slide types, layouts (§3 of LAYOUTS.md and BRIEF.md's layout setting), diagrams (`Diagram:` plus the Mermaid you write), charts from real numbers.
- **Lint** if the tools are available (§7).
- **Write** OUTLINE.md (v0.1, `reviewed: no`) and DECISIONS.md.
- **Report** the sections with live minutes, the tags and layouts added, the main coverage gaps, and the `[TBD: …]` facts only the presenter can supply. **Pause:** ask what to change; offer to go straight to review.

### C. Refine (prompt 3)
- **Open:** as in B (the style guide and TAGS.md when tags change).
- Loop: apply the presenter's changes by section number, bump the version, record each under "Changes by version". Numbering is frozen from v0.2.
- Offer the open `[TBD: …]` facts to confirm; record confirmed ones under "Facts to present" in DECISIONS.md.
- **Write** at checkpoints; lint at the end of each round when the tools are available.
- **Exit** when the presenter says it's ready for review: set `reviewed: pending`, write OUTLINE.md, go to D. If the chat has grown long, recommend a fresh one.

### D. Independent review (prompt 4), fresh chat recommended
- **Open:** BRIEF.md, OUTLINE.md, DECISIONS.md, TAGS.md, LAYOUTS.md, the style guide.
- Hand off first (§6): a fresh chat isn't anchored to earlier drafting choices. If the presenter stays, review here and say once that it may miss more.
- Lint, then propose a ranked change list: gaps by value to attendees, tags and layouts that break their rules, claims needing `As of` or `[UNVERIFIED]`. **Write nothing until the presenter approves the list.**
- Apply exactly the approved changes, bump the version, set `reviewed:` to the new version, write. Other changes first? Set `reviewed: no`, write, back to C.

### E. Approve (prompt 5)
- **Open:** OUTLINE.md, DECISIONS.md.
- Show in a few lines what approval locks in: the version, the `[TBD: …]` items that will show as chips, the number of `[UNVERIFIED]` claims (from the linter when available), and small edits since the review.
- Ask "Do you approve outline vX.Y for the deck?" and follow "On approval" (§4.1). More changes instead: back to C. Offer a second review only if the structure changed.

### F. Deck, pass 1 (prompt 6), fresh chat recommended
- **Open:** DECK-BUILD-SPEC.md, LAYOUTS.md §4, the style guide, OUTLINE.md, OUTPUT-NOTES.md. Ask for `deck-tools.zip` if it isn't attached.
- Confirm the pinned libraries, the style, and anything the linter says can't be rendered. Pause only for a decision.
- Build pass 1 (title, agenda, every horizontal slide): draft the fragments with `draft-fragments.py --pass 1`, finish them, assemble, check, send the file, set `deck: pass 1`, write OUTLINE.md (status only) and OUTPUT-NOTES.md.
- **Pause:** "Open it in a browser; the in-chat preview can't load the slide library. Tell me what to adjust, or say 'go' for pass 2."

### G. Deck, pass 2 (prompt 7), same chat
- Draft the Core sections' vertical slides (`draft-fragments.py --topics …`; existing slides are kept), finish them, assemble, send an interim file, set `deck: core`; carry on with Brief and Self-guided unless asked to stop.
- Run every check in DECK-BUILD-SPEC.md §7, report the results as numbers, write OUTPUT-NOTES.md, set `deck: complete`, write OUTLINE.md. **Pause:** offer H.

### H. After the build (prompts 8 and 9)
- **Content change:** propose it; once approved, update OUTLINE.md first (bump the version, add a Decided entry), re-draft only the affected topics (`draft-fragments.py --topics N --force`), finish them, `replace-topic`, re-check, update OUTPUT-NOTES.md (`--previous`, `--rebuilt`), send the deck.
- **Style switch:** set the style in BRIEF.md, open the new style guide, lint for degrade warnings, rebuild with the new style. Every style renders every tag, so no tag mapping is needed.
- **Wrap-up:** summarize the deck file, the outline version it was built from, placeholder chips still showing, and where BRIEF.md says it will be hosted.

**The deck file across chats.** The deck is a file in a chat, not a state file. If a Phase 2 step runs in a chat without the latest deck, ask the presenter to attach it (and the fragments, if they kept them). Don't rebuild from scratch unless they ask.

## 6. Pauses and handoffs

- **One thing at a time.** A message that asks for a decision ends there.
- **Every pause ends with a "Next:" line** saying what Claude will do when the presenter replies.
- **Write before handing off** (§9). If the writes failed, use the fallback in §9 and say the next chat will need the Recovery prompt.
- **Recommend a fresh chat** before the review (D), before Phase 2 (F), and when a chat has grown long:

  > **Next step: start a new chat.** Everything is saved in the project files.
  > In a new chat in this project, type: **continue my deck**

- If the presenter stays in the same chat anyway, carry on. Mention the advice at most once per chat.

## 7. Tools

`deck-tools.zip` holds the tools; its README-BUNDLE.md has the commands. Unzip it in the sandbox, run `npm install` there for Phase 2, and copy OUTLINE.md and BRIEF.md into the folder, and the active style guide into `knowledge/styles/`, exactly as `project_read` returns them.

| Tool | Use |
|---|---|
| `lint-outline.py` | Phase 1 checkpoints, the review, approval counts, and before Phase 2 |
| `draft-fragments.py` | Draft the slide fragments from the outline; Claude finishes visuals and wording |
| `assemble-deck.py` | Build the deck from fragments; `replace-topic` and `edit` for changes |
| `check-deck.py` | Verify every slide; screenshots; JSON for the notes |
| `write-notes.py` | Write OUTPUT-NOTES.md |

Without the bundle: in Phase 1, copy `outline_parser.py` and `lint-outline.py` from project knowledge if they're there (they also need TAGS.md and LAYOUTS.md beside them), or check the outline by reading TAGS.md. In Phase 2, ask for the bundle; if it can't be attached, follow DECK-BUILD-SPEC.md §2's fallback.

## 8. Status fields

OUTLINE.md's status comment carries the stage:

`<!-- status: version 0.3 | phase 1 | last written 2026-11-15 | approved: no | reviewed: no | deck: none -->`

| Field | Values | Set when |
|---|---|---|
| `approved` | `no`, or the approved version (`v0.4`) | The gate entry is recorded |
| `reviewed` | `no`; `pending`; or the version the review's changes produced | `pending`: ready for review (C). The version: D's changes are written |
| `deck` | `none`, `pass 1`, `core`, `complete` | Steps F and G finish |

Keep the plain-language `**Status:**` line in step with these fields. OUTPUT-NOTES.md has its own status comment, written by `write-notes.py`.

## 9. Writing the state files

The state files are BRIEF.md, OUTLINE.md, DECISIONS.md and OUTPUT-NOTES.md. Claude writes them directly in project knowledge; the presenter shouldn't have to paste anything.

**When:** at checkpoints, not after every message: a finished section or revision, a recorded decision, an approval, a build pass, the end of the chat. Each write makes the project reload its knowledge.

**How:**
1. Re-read the file from project knowledge immediately before writing; another chat may have written since.
2. Apply only the intended changes to that latest version.
3. Update its status comment: version or revision, phase, date (and OUTLINE.md's `approved`, `reviewed`, `deck`).
4. Replace the file at its existing path. Never create a copy with a new name.
5. Report what changed by section number; for a large change, a short list the presenter can check.

**Precise edits:** change exact strings and confirm each matched exactly once; an edit that matches zero or several places must fail loudly. Afterward, check for stale version strings, stray names and broken heading numbers (the linter catches the numbering).

**Fallback:** if the chat can't write to project knowledge, end with "Updates for OUTLINE.md" (complete revised sections, ready to paste) and "Updates for DECISIONS.md" (new entries), and say the files were not updated. A fresh chat can recover them with the Recovery prompt.

Versions: OUTLINE.md uses v0.1, v0.2, v0.2.1 and so on; BRIEF.md and DECISIONS.md use a revision number.

## 10. Seed inputs

- **Trust varies by type.** A practitioner transcript reflects real concerns but may misstate facts; another LLM's outline gives breadth, but its claims need verifying. Record each seed's trust level in BRIEF.md.
- **Condense large or noisy inputs** before uploading. A good condensed file has a header (source type, how to attribute it generically, what still needs verifying), the content organized as an outline, and a separate, labeled "Observations" section.

## 11. Chat hygiene

- **One job per chat.** Start a fresh chat for the review, for Phase 2, or when a chat has grown long; every message resends the whole chat.
- **Hand off with files, not memory.** Make sure the state files are written before switching.
- **Missed a chat switch?** Nothing breaks; "continue my deck" picks up anywhere.
- **Ask Claude to ask first** on anything substantial: "Before you start, ask me up to three questions whose answers would change the result."

## 12. Lessons from earlier runs

- **Name the presenter.** A first-person prompt ("I am presenting…") makes Claude assume whoever is chatting is the presenter.
- **Say outright that seeds are leads.** Calling inputs "the material" leads Claude to polish them rather than research.
- **Rules that apply across sections get their own section.** Attribution was once silently dropped when a neighboring section was rewritten. When revising instructions, ask for the complete merged text and compare it.
- **Every working-aid tag needs a strip rule,** or it leaks onto slides. TAGS.md and the checker now enforce this.
- **Follow the change list, not superseded drafts.** Apply exactly the approved list and flag any differences.
- **Claude's in-chat preview can't load CDN scripts,** so a deck that looks broken there may be fine. Use the checker or a real browser.
- **Rules only apply when their file is open.** Open the files each step names (§5); don't work from memory of an earlier chat.

## 13. Collaboration (future)

This process is written for a single author. Several people working on one outline from their own chats raises problems this version doesn't solve: stale copies and simultaneous writes. Stable section IDs, add-only decisions and a version line in each state file are designed so a multi-author version can build on them.
