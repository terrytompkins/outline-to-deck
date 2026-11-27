import sys
sections = [
 ("Lists", [
   ("Boxes", "Layout: list", ["Research: find what the seeds miss", "Outline: write v0.1 with a time plan", "**Review: a fresh chat checks it**", "Build: one pass, then verify"]),
   ("Plain", "Layout: list; plain", ["Text is cheap to revise", "Decks are expensive to rebuild", "So revise the text"]),
   ("Numbered, six items", "Layout: list; numbered", ["Map the landscape: coverage dimensions first", "Research: authoritative sources", "Draft: v0.1 with gaps noted", "Refine: by section number", "Review: in a fresh chat", "Approve: record the gate"]),
 ]),
 ("Process", [
   ("Chevrons", "Layout: process", ["Draft: write v0.1", "Refine: revise by number", "**Review: fresh eyes**", "Approve: record it"]),
   ("Arrows", "Layout: process; arrows", ["Outline: the content", "Style: the look", "Deck: one build"]),
   ("Steps", "Layout: process; steps", ["Lint: check the outline", "Write: slide fragments", "**Assemble: one file**", "Check: every slide", "Notes: record the build"]),
 ]),
 ("Timeline", [
   ("Horizontal", "Layout: timeline", ["Week 1: brief and seeds", "Week 2: outline v0.1", "Week 3: refine and review", "**Week 4: approve**", "Week 5: build and rehearse"]),
   ("Vertical", "Layout: timeline; vertical", ["Nov 9: first workshop", "Nov 15: guided workflow", "Nov 25: v2 plan", "Dec 2026: v2 trials"]),
 ]),
 ("Columns", [
   ("Three options", "Layout: columns", [("Manual", ["You run each step", "Full control"]), ("Guided", ["Claude leads", "Fewer prompts"]), ("Plugin", ["Installed once", "Later"])]),
   ("Pros and cons", "Layout: columns; pros-cons", [("Pros", ["One source of truth", "Cheap revisions"]), ("Cons", ["Needs discipline", "An approval step"])]),
   ("Before and after", "Layout: columns; before-after", [("Before", ["Rebuild the deck", "Every change"]), ("After", ["Edit the outline", "Build once"])]),
 ]),
 ("Hierarchy", [("Top-down", "Layout: hierarchy", "TREE"), ("Left to right", "Layout: hierarchy; left-right", "TREE")]),
 ("Radial", [("Around the outline", "Layout: radial", "RADIAL")]),
 ("Matrix", [("Four kinds of tag", "Layout: matrix; axes\nX axis: Outline only → in the deck\nY axis: Inline → slide", ["Working aids: stripped from the deck", "Content markers: footers, chips, notes", "Slide types: whole designed slides", "**Callouts: boxed asides**"])]),
 ("Cycle", [("Revise until ready", "Layout: cycle", ["Draft", "Review", "**Revise**", "Lint", "Approve"])]),
 ("Pyramid and funnel", [
   ("Pyramid", "Layout: pyramid", ["Deck: what people see", "Styles: how it looks", "Tags: what each part is", "**Outline: the content**"]),
   ("Funnel", "Layout: funnel", ["Ideas: everything you could say", "Outline: what the talk covers", "Time plan: what fits live", "**Deck: what you show**"]),
 ]),
 ("Venn", [("Two sets", "Layout: venn\nOverlap: The deck", ["Content: the outline", "Look: the style"]), ("Three sets", "Layout: venn\nOverlap: A good talk", ["Accurate", "Clear", "Engaging"])]),
 ("Fit tests", [
   ("Seven long steps", "Layout: process", ["Map: list the coverage dimensions for the topic", "Research: search the authoritative sources first", "Draft: write version zero point one", "Refine: revise sections by their numbers", "Review: check it in a fresh chat", "Approve: record the gate decision", "Build: assemble and check the deck"]),
   ("Seven detailed items", "Layout: list", ["Brief: who attends, why now and how long the session runs", "Seeds: transcripts, notes and earlier outlines worth mining", "Research: official documentation and primary sources first", "Outline: numbered sections that map straight to slides", "Review: a fresh chat that isn't anchored to earlier drafts", "Approval: an explicit decision recorded in the decisions log", "Deck: one build from the approved outline, then checks"]),
 ]),
]
TREE = ["Deck", [["Title and agenda", []], ["Topics", ["Horizontal slides", "Vertical slides"]], ["**Appendix**", ["Backup slides"]]]]
out = ["# OUTLINE — Layout showcase", "", "<!-- status: version 1.0 | phase 2 | last written 2026-11-27 | approved: v1.0 | reviewed: v1.0 | deck: none -->", "",
       "**Status:** v1.0. Test fixture: every layout and variant.", "**Session:** 30 minutes", "**Facts verified:** November 27, 2026", "",
       "## Changes by version (outline-only working aid)", "- v1.0: fixture.", "", "## Central message", "Bullets become designed shapes with one line.", "", "---", "",
       "## Time plan (outline-only working aid)", "", "| # | Section | Live (min) | Priority |", "|---|---|---|---|", "| — | Title and agenda | 1 | Core |"]
for i, (name, _) in enumerate(sections, 1):
    out.append(f"| {i} | {name} | 2 | Core |")
out += ["", "---", "", "## Front matter: Title and agenda [All]", "- Title: Layout showcase", "- Series: Fixture series", ""]
def tree_lines(node, depth=0):
    label, kids = node
    lines = ["  " * depth + "- " + label]
    for k in kids:
        lines += tree_lines(k, depth + 1) if isinstance(k, list) else ["  " * (depth + 1) + "- " + k]
    return lines
for i, (name, subs) in enumerate(sections, 1):
    out += ["---", "", f"## {i}. {name} [All] [Core]", "", "Main points:"]
    pts = [f"- {s[0]} [Seed]" for s in subs]
    while len(pts) < 3: pts.append(f"- One line picks the shape ({len(pts)}) [Seed]")
    out += pts + [""]
    for j, (title, lay, data) in enumerate(subs, 1):
        out += [f"### {i}.{j} {title} [All] [Seed]", lay]
        if data == "TREE": out += tree_lines(TREE)
        elif data == "RADIAL": out += ["- **The outline**", "  - Brief", "  - Seeds", "  - Research", "  - Tags", "  - Time plan", "  - Decisions"]
        else:
            for d in data:
                if isinstance(d, tuple): out.append(f"- {d[0]}"); out += [f"  - {x}" for x in d[1]]
                else: out.append(f"- {d}")
        out.append("")
out += ["---", "", "## Coverage gaps (outline-only working aid)", "- Fixture only.", ""]
open(sys.argv[1], "w").write("\n".join(out))
