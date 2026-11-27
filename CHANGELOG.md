# Changelog

## 2.0.0 (in progress, November 2026)

A usable tool, rebuilt from the v1 workshop repository (`outline-to-deck-workshop-20261109`, tagged `v1-workshop`).

- **One tag registry** (`knowledge/TAGS.md`) replaces tags spread across the conventions and each style guide. Every style renders every tag; style switches need no mapping.
- **New tags:** `[Quote]`, `[Key figure]`, `[Backup]` slides; `Layout:`, `Diagram:`, `Image:` and `Embed:` directives; `chart` blocks.
- **SmartArt-style layouts:** list, process, timeline, columns, hierarchy, radial, matrix, cycle, pyramid, funnel and Venn, with variants, limits, compaction and a fallback ladder (`knowledge/LAYOUTS.md`).
- **Styles extend Base** and list only overrides, on shared color roles and shape tokens. Field Guide's callout labels now meet 4.5:1 contrast. Neutral became Base.
- **Releases:** pushing a version tag runs the tests and publishes `deck-tools.zip` as a GitHub release.
- **Tools:** outline linter (36 checks), fragment drafter (writes every slide the outline determines; Claude finishes visuals), assembler (CDN tags with SRI and a fallback CDN, image inlining, partial rebuilds), checker (layouts, clipped diagram labels, tiny text, outline cross-check, JSON), notes writer, tools bundle for Project chats, pin updater, reference sync, tests.
- **Shared runtime:** decorations, autofit, Mermaid, layout geometry and charts come from `runtime/`, so every build is consistent.
- **Libraries:** Reveal.js 6.0.2 and Mermaid 12.3.0 (from 5.1.0 and 11.12.0).
- **Workflow:** one `WORKFLOW.md` (merged with the guided workflow), a read map in the project instructions, and `OUTPUT-NOTES.md` for every build.
- **Fixed:** Mermaid rendering hidden slides with its default theme; v1's mismatched diagram label sizes.
