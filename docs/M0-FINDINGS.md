# Milestone 0 findings

Running record of the M0 checks in `docs/V2-PLAN.md` §16. Status: **complete** (Nov 27, 2026).

| Check | Status | Result |
|---|---|---|
| Tag v1 in the old repo | Done | `v1-workshop` tag on `outline-to-deck-workshop-20261109` (Terry, Nov 26) |
| Create the new repo | Done | `terrytompkins/outline-to-deck` (Terry, Nov 26) |
| Reveal.js 6.0.2 script-tag build | Done | `dist/reveal.js` is still a UMD build that sets the `Reveal` global; `dist/plugin/notes.js` still sets `RevealNotes`. npm ships no `.min` files; cdnjs serves its own `reveal.min.js` and `plugin/notes.min.js`. |
| v1 demo on the new libraries | Done | The v1 Field Guide demo, with only the five library URLs changed, passes every v1 check (17 slides, 1 diagram, 0 console errors) on Reveal 6.0.2 + Mermaid 12.3.0, both with the new Mermaid look and with `look: 'classic', layout: 'dagre'`. Only the diagram slide changes visibly; other differences are a few pixels in Reveal's controls. |
| Mermaid look for Field Guide (D16) | Done | The new look adds drop shadows to diagram nodes. STYLE-FIELD-GUIDE says "No gradients and no drop shadows on panels", so **Field Guide uses `look: 'classic'`**. Mermaid's look becomes a per-style setting; Base starts with classic (decision D22). |
| Mermaid label sizes | Done | In v1 (Mermaid 11.12.0) the first two node labels on the diagram slide render larger than the rest, consistent with the font-measurement mismatch suspected from the inbox-to-todo build. Mermaid 12.3.0 renders all labels at the same size. The runtime still renders after `document.fonts.ready`. |
| Pins file and SRI hashes | Done | All 10 URLs (cdnjs and jsDelivr for 5 files) download; sha384 hashes stored in `tools/pins.json` (Terry, Nov 26). jsDelivr files are byte-identical to npm. cdnjs serves its own minified builds of Reveal's `reveal.css`, `reveal.min.js` and `plugin/notes.min.js` (sizes differ from npm); its `reset.css` and Mermaid file match npm. |
| cdnjs has Mermaid 12.3.0 `mermaid.min.js`? | Done | Yes, 5,537,838 bytes, identical to npm. |
| CDN order | Done | Reveal: jsDelivr first, cdnjs fallback. Mermaid: cdnjs first, jsDelivr fallback (D23). Every file a deck loads first is then byte-identical to what `check-deck.py` tests. |
| Sandbox route for tools in a Project (§9.3) | Done | Route C chosen (D24). Details below. |
| Project-knowledge size | Replaced | The test showed knowledge files are read through a tool, not preloaded (below). A follow-up check in a real Project replaces the size measurement. |

## Project sandbox test (Nov 27, 2026)
Run by Terry in a throwaway Project with the four kit files as project knowledge and `spike-bundle.zip` attached to the chat. Every hash and marker Claude reported matches the originals.

| Route | Result |
|---|---|
| A. Project knowledge on disk | **No.** No kit file anywhere on disk. `/mnt/project/` exists but holds only an empty `.in_memory` file (the Project's own placeholder, not part of the kit). |
| B. Claude copies a file it can read | **Yes, exact.** `spike-base.css` (10,742 bytes) and `spike-runtime.js` (2,723 bytes) written by hand matched the originals' SHA-256. |
| C. Zip attached to the chat | **Yes.** Found under `/mnt/user-data/uploads/`, unzipped and ran; bundle marker correct. |

Other results from the Project sandbox:
- **Knowledge files were not in Claude's context.** Claude saw only their names and fetched each file with a project-read tool (it came back complete). Rules in knowledge files therefore reach Claude only when it reads them; see the follow-up check below.
- Python 3.13, Node 22.23.5, npm 10.9, and Playwright with Chromium all work, so `check-deck.py` can run inside a Project.
- npm registry, PyPI and GitHub raw are reachable; cdnjs and jsDelivr are blocked (403). Library copies for checking come from npm, which matches the jsDelivr-first choice for Reveal (D23).

**Follow-up check (done, Nov 27):** in Terry's v1 workshop Project (Markdown knowledge only), a new chat also could not see `OUTLINE-CONVENTIONS.md` without opening it. Claude had only the document names and the project instructions, plus three tools:
- `project_read`: reads one document by path. Short text comes back inline; longer text is saved to a file in the sandbox.
- `project_search`: returns matching snippets with their source paths.
- `project_info`: the Project's name, instructions, document list and stats.

Consequences for v2 (D25):
1. **Knowledge files are never preloaded.** A rule takes effect only when Claude opens the file that holds it. `PROJECT-INSTRUCTIONS.md` must carry a **read map** (which files to open at each workflow step) and keep the always-on rules in the instructions themselves.
2. **Small, single-purpose files are an advantage**, not just a context saving: Claude opens only what a step needs. The v2 split (TAGS, LAYOUTS, one style, build spec) fits this.
3. **The Nov 15 retrieval-mode worry no longer applies** in its old form; knowledge size costs nothing until a file is opened.
4. **Possible cheaper route B:** because `project_read` saves long documents to a sandbox file, a long script in project knowledge may reach disk without Claude retyping it. Test in M2 with the real linter (check the saved file's hash).

## Network seen from Claude's cloud workspace
npm registry, PyPI and GitHub raw: reachable. cdnjs and jsDelivr: blocked (403 from the proxy). Same pattern as the inbox-to-todo build, which is why `check-deck.py` serves CDN URLs from local npm copies.
