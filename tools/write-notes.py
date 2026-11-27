#!/usr/bin/env python3
"""write-notes: write OUTPUT-NOTES.md from the linter's and checker's JSON.

    python3 tools/lint-outline.py OUTLINE.md --knowledge knowledge --json > lint.json
    python3 tools/check-deck.py deck.html --outline OUTLINE.md --json > check.json
    python3 tools/write-notes.py --outline OUTLINE.md --lint lint.json --check check.json \\
        --deck my-talk.html --style field-guide --deck-status complete \\
        --fallback "4.2|Layout process|9 steps (limit 7)|Wrapped to two rows|Merge steps 3 and 4" \\
        --previous OUTPUT-NOTES.md --rebuilt 4 --out OUTPUT-NOTES.md

--fallback rows record what Claude changed at build time (section|what|why|action|suggested
outline change). With --previous and --rebuilt, fallback rows for sections that weren't rebuilt
are kept. Standard library only.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def load(path):
    if not path:
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def previous_fallbacks(path, rebuilt):
    if not path or not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"## Fallbacks and workarounds\n\n\|[^\n]*\n\|[-| ]*\n((?:\|[^\n]*\n)*)", text)
    if not m:
        return []
    rows = []
    for line in m.group(1).strip().split("\n"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[0] != "—":
            top = cells[0].split(".")[0]
            if top not in rebuilt:
                rows.append(cells)
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="Write OUTPUT-NOTES.md from lint and check results.")
    ap.add_argument("--outline", required=True)
    ap.add_argument("--lint", help="lint-outline.py --json output")
    ap.add_argument("--check", help="check-deck.py --json output")
    ap.add_argument("--deck", required=True, help="deck file name")
    ap.add_argument("--style", required=True)
    ap.add_argument("--deck-status", default="complete", choices=["pass 1", "core", "complete"])
    ap.add_argument("--fallback", action="append", default=[], help="section|what|why|action|suggested change")
    ap.add_argument("--issue", action="append", default=[], help="an open issue to record")
    ap.add_argument("--no-tools", action="store_true", help="record that the deck was built without the tools")
    ap.add_argument("--previous", help="the previous OUTPUT-NOTES.md")
    ap.add_argument("--rebuilt", default="", help="comma-separated top-level sections rebuilt in this pass")
    ap.add_argument("--pins", default=os.path.join(HERE, "pins.json"))
    ap.add_argument("--out", default="OUTPUT-NOTES.md")
    a = ap.parse_args(argv)

    with open(a.outline, encoding="utf-8") as f:
        outline = f.read()
    m = re.search(r"<!--\s*status:\s*version\s+([\w.]+)", outline)
    version = m.group(1) if m else "?"
    lint, check = load(a.lint), load(a.check)
    with open(a.pins, encoding="utf-8") as f:
        pins = json.load(f)
    libs = ", ".join(f"{('Reveal.js' if k == 'reveal' else k.capitalize())} {v['version']}" for k, v in pins["libraries"].items())
    today = datetime.date.today().isoformat()

    rebuilt = {s.strip() for s in a.rebuilt.split(",") if s.strip()}
    rows = previous_fallbacks(a.previous, rebuilt) if rebuilt else []
    for fb in a.fallback:
        cells = [c.strip() for c in fb.split("|")]
        if len(cells) != 5:
            print(f"error: --fallback needs 5 parts separated by '|': {fb}", file=sys.stderr)
            return 1
        rows.append(cells)
    rows.sort(key=lambda r: [int(x) if x.isdigit() else 0 for x in r[0].split(".")])

    out = ["# OUTPUT NOTES", "",
           f"<!-- status: outline v{version} | deck: {a.deck_status} | built {today} | style: {a.style} -->", "",
           "Written by Claude at the end of each build pass. Replaced on every build; fallback rows for sections",
           "not rebuilt are kept.", "", "## Build summary", "",
           f"- Deck: `{a.deck}`, built from outline v{version} with the {a.style} style",
           f"- Libraries: {libs}"]
    if a.no_tools:
        out.append("- **Built without the deck tools** (bundle not attached); checks were done by hand")
    if check:
        out.append(f"- Checks: {check['slides']} slides; {check['overflow']} overflow; {check['collisions']} collisions; "
                   f"{check['diagrams_rendered']} of {check['diagrams']} diagrams rendered; {check['layouts']} layouts; "
                   f"{check['console_errors']} console errors" + (f"; {check['fragment_clicks']} fragment clicks" if check.get("fragment_clicks") is not None else ""))
    out += ["", "## Fallbacks and workarounds", "",
            "| Section | What | Why | Action taken | Suggested outline change |", "|---|---|---|---|---|"]
    out += [f"| {' | '.join(r)} |" for r in rows] or ["| — | none | | | |"]
    out += ["", "## Autofit and compaction", ""]
    fits = (check or {}).get("autofit", [])
    if fits:
        for f in fits:
            where = f"§{f['number']}" if f.get("number") else f"page {f['page']}"
            bits = []
            if f["fit"] < 1:
                bits.append(f"text reduced to {f['fit']:.2f}em")
            if f.get("compact"):
                bits.append("layout compacted (" + f["compact"] + ")")
            out.append(f"- {where}: {'; '.join(bits)}")
    else:
        out.append("- none")
    out += ["", "## Placeholders and unverified claims", ""]
    if lint:
        st = lint["stats"]
        out.append(f"- `[TBD]` chips: {len(st['tbd'])}" + (f" ({', '.join(st['tbd'])})" if st["tbd"] else ""))
        out.append(f"- `[UNVERIFIED]`: {len(st['unverified'])}" + (f" ({', '.join(st['unverified'])})" if st["unverified"] else ""))
        warnings = [i for i in lint["issues"] if i["severity"] != "note"]
        if warnings:
            out += ["", "Linter findings at build time:"]
            out += [f"- {i['code']}" + (f" §{i['section']}" if i["section"] else "") + f": {i['message']}" for i in warnings]
    else:
        out.append("- (linter not run)")
    out += ["", "## Open issues", ""]
    issues = list(a.issue) + ((check or {}).get("problems") or [])
    out += [f"- {i}" for i in issues] or ["- none"]
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"Wrote {a.out}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
