# Milestone 0 findings

Running record of the M0 checks in `docs/V2-PLAN.md` §16. Status: **in progress** (Nov 26, 2026).

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
| Sandbox route for tools in a Project (§9.3) | Pending | Test kit sent to Terry (`o2d-m0-project-test-kit.zip`). |
| Project-knowledge size | Pending | Optional step 7 of the test kit. |

## Network seen from Claude's cloud workspace
npm registry, PyPI and GitHub raw: reachable. cdnjs and jsDelivr: blocked (403 from the proxy). Same pattern as the inbox-to-todo build, which is why `check-deck.py` serves CDN URLs from local npm copies.
