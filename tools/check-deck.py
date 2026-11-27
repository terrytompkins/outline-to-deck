#!/usr/bin/env python3
"""check-deck: verify every slide of a deck built by assemble-deck.py.

Checks (DECK-BUILD-SPEC.md, verification checklist):
  visible     the slide is inside the viewport when it is current
  overflow    content fits the 1280x720 frame (after autofit)
  footer      no content element overlaps the footer band
  diagrams    every pre.mermaid produced an SVG, and no node label is clipped
  console     no console errors or page errors
  tags        no outline working-aid text is visible (text inside <code> is skipped)
  tiny        no visible text smaller than 14px at 1280x720
  layouts     each .layout matches its contract; no item text is clipped
  outline     (--outline) every outline slide is in the deck, with its layouts and speaker notes

Slides are checked in final state: every fragment shown. --step adds a pass that clicks through
every fragment watching for errors.

Usage:
  pip install playwright && playwright install chromium
  python3 tools/check-deck.py deck.html [--outline OUTLINE.md] [--shots DIR] [--json]

Library files are served from local copies listed in tools/pins.json (node_modules/, after
`npm install`), so the checker works where CDNs are blocked. --no-local uses the network instead.
Exit code 0 when every check passes, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

LEAKS = ["[Seed]", "[Research]", "[Core]", "[Brief]", "[Self-guided]", "Coverage gaps", "Source reconciliation",
         "outline-only working aid", "Changes by version", "Speaker notes:", "Main points:", "Layout:", "Diagram:",
         "Suggested visual:", "[!", "[TBD", "[UNVERIFIED"]

WALK = r"""async (opts) => {
  const out = [];
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const H = Reveal.getHorizontalSlides();
  for (let h = 0; h < H.length; h++) {
    const n = Math.max(1, H[h].querySelectorAll(':scope > section').length);
    for (let v = 0; v < n; v++) {
      Reveal.slide(h, v);
      await wait(150);
      const s = Reveal.getCurrentSlide();
      if (window.deckShow) { try { await window.deckShow(s); } catch (e) {} }
      await wait(opts.settle);
      const r = s.getBoundingClientRect();
      const head = s.querySelector('h1,h2,h3,h4');
      const label = ((head && head.textContent) || s.id || '').trim().replace(/\s+/g, ' ').slice(0, 60);
      const visible = r.top > -5 && r.bottom < window.innerHeight + 5 && r.height > 100;
      const overflow = s.scrollHeight > s.clientHeight + 2;
      const ft = s.querySelector(':scope > footer');
      const limit = ft ? ft.getBoundingClientRect().top : r.bottom - 60 * Reveal.getScale();
      let collision = false;
      s.querySelectorAll(':scope > *:not(' + opts.exclude + ')').forEach(el => {
        if (el.getBoundingClientRect().bottom > limit + 1) collision = true;
      });
      // diagrams and clipped Mermaid labels
      const mm = s.querySelectorAll('pre.mermaid').length;
      const mmok = s.querySelectorAll('pre.mermaid svg').length;
      let mmClipped = 0;
      s.querySelectorAll('pre.mermaid svg foreignObject').forEach(fo => {
        const inner = fo.firstElementChild; if (!inner) return;
        const w = parseFloat(fo.getAttribute('width') || '0'), hh = parseFloat(fo.getAttribute('height') || '0');
        if (inner.scrollWidth > w + 2 || inner.scrollHeight > hh + 2) mmClipped++;
      });
      // tiny text (computed sizes are in slide coordinates, before Reveal's scaling)
      const tiny = [];
      const walker = document.createTreeWalker(s, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) {
        const t = walker.currentNode; if (!t.textContent.trim()) continue;
        const el = t.parentElement; if (!el || el.closest('aside.notes, svg, script, style, .chart__data')) continue;
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') continue;
        const px = parseFloat(cs.fontSize);
        if (px < 13.5) tiny.push(Math.round(px * 10) / 10 + 'px "' + t.textContent.trim().slice(0, 30) + '"');
      }
      // layouts: contract and clipping
      const layouts = [];
      s.querySelectorAll('.layout').forEach(lay => {
        const name = lay.dataset.layout || '';
        const shape = (opts.shapes[name] || '');
        const list = lay.querySelector(':scope > .layout__items');
        let items = list ? Array.from(list.children).filter(c => c.classList.contains('layout__item')) : [];
        let count = items.length;
        if (shape === 'tree' && list) count = list.querySelectorAll('.layout__item').length;
        if (shape === 'radial' && items[0]) count = items[0].querySelectorAll(':scope > ul > li, :scope > ol > li').length;
        const problems = [];
        if (!name) problems.push('no data-layout');
        else if (!(name in opts.shapes)) problems.push('unknown layout');
        if (!list) problems.push('no .layout__items list');
        if (lay.dataset.count && parseInt(lay.dataset.count) !== count) problems.push('data-count ' + lay.dataset.count + ' but ' + count + ' items');
        let clipped = 0;
        lay.querySelectorAll('.layout__label, .layout__detail').forEach(t => {
          if (t.scrollWidth > t.clientWidth + 1 || t.scrollHeight > t.clientHeight + 1) clipped++;
        });
        layouts.push({name, count, problems, clipped});
      });
      const clone = s.cloneNode(true);
      clone.querySelectorAll('aside.notes, code, pre.mermaid').forEach(a => a.remove());
      out.push({h, v, id: s.id || '', number: s.dataset.number || null, type: s.dataset.type || null, label, visible,
                overflow, collision, mm, mmok, mmClipped, tiny: tiny.slice(0, 5), layouts,
                notes: !!s.querySelector('aside.notes'), text: clone.textContent,
                fit: s.dataset.fit ? parseFloat(s.dataset.fit) : 1, compact: s.dataset.compact || '',
                runtimeOverflow: !!s.dataset.overflow});
    }
  }
  return out;
}"""

STEP = r"""async () => {
  let clicks = 0;
  const H = Reveal.getHorizontalSlides();
  for (let h = 0; h < H.length; h++) {
    const n = Math.max(1, H[h].querySelectorAll(':scope > section').length);
    for (let v = 0; v < n; v++) {
      Reveal.slide(h, v, -1);
      await new Promise(r => setTimeout(r, 60));
      while (Reveal.nextFragment()) { clicks++; await new Promise(r => setTimeout(r, 40)); }
    }
  }
  return clicks;
}"""

EXCLUDE = "footer,aside,.pgnum,.more,.tiy,.chrome,script,style"


def local_map(pins_path, root):
    """URL -> local file for every pinned library file that exists locally."""
    mapping = {}
    with open(pins_path, encoding="utf-8") as f:
        pins = json.load(f)
    for lib in pins["libraries"].values():
        for spec in lib["files"].values():
            path = os.path.join(root, spec["local"])
            if os.path.exists(path):
                for cdn in ("cdnjs", "jsdelivr"):
                    mapping[spec[cdn]["url"]] = path
    return mapping


def outline_expectations(outline_path):
    from outline_parser import load_registry, parse_outline
    kdir = os.path.join(ROOT, "knowledge")
    reg = load_registry(kdir, brief_path=os.path.join(os.path.dirname(os.path.abspath(outline_path)), "BRIEF.md"))
    with open(outline_path, encoding="utf-8") as f:
        o = parse_outline(f.read(), reg)
    exp = {}
    for s in o.slides:
        exp[s.number] = {
            "layouts": [b.key for b in s.blocks if b.kind == "layout"],
            "notes": any(b.kind == "key" and b.key == "Speaker notes" for b in s.blocks)
                     or any(b.kind == "list" and any(re.match(r"Speaker notes:", it.text) for it in b.items) for b in s.blocks),
            "title": s.title,
        }
    shapes = {k: v["shape"] for k, v in reg.layouts.items()}
    audience = ["[" + t + "]" for t in reg.audience]
    return exp, shapes, audience


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check every slide of a deck.")
    ap.add_argument("deck")
    ap.add_argument("--outline", help="OUTLINE.md to cross-check sections, layouts and speaker notes")
    ap.add_argument("--shots", help="folder for one PNG per slide")
    ap.add_argument("--json", action="store_true", help="print results as JSON (for OUTPUT-NOTES.md)")
    ap.add_argument("--step", action="store_true", help="also click through every fragment")
    ap.add_argument("--pins", default=os.path.join(HERE, "pins.json"))
    ap.add_argument("--local-root", default=ROOT, help="folder holding node_modules/ (default: the repo root)")
    ap.add_argument("--no-local", action="store_true", help="load libraries from the network")
    ap.add_argument("--map", nargs="*", default=[], help="extra URL=FILE pairs")
    ap.add_argument("--viewport", default="1600x900")
    ap.add_argument("--settle", type=int, default=250, help="ms to wait on each slide after rendering")
    ap.add_argument("--tags", nargs="*", default=[], help="extra text that must never be visible")
    a = ap.parse_args(argv)

    from playwright.sync_api import sync_playwright
    w, h = map(int, a.viewport.split("x"))
    mapping = {} if a.no_local else local_map(a.pins, a.local_root)
    mapping.update(dict(m.split("=", 1) for m in a.map))
    exp, shapes, audience = ({}, {}, [])
    if a.outline:
        exp, shapes, audience = outline_expectations(a.outline)
    else:
        try:
            from outline_parser import load_registry
            shapes = {k: v["shape"] for k, v in load_registry(os.path.join(ROOT, "knowledge")).layouts.items()}
        except Exception:
            pass
    deck = pathlib.Path(a.deck).resolve()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": w, "height": h})
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        def serve(body, ctype):
            return lambda route: route.fulfill(body=body, content_type=ctype,
                                               headers={"Access-Control-Allow-Origin": "*"})
        for url, f in mapping.items():
            ctype = "text/css" if url.endswith(".css") else "application/javascript"
            page.route(url, serve(pathlib.Path(f).read_bytes(), ctype))
        page.goto(deck.as_uri())
        page.wait_for_function("window.Reveal && Reveal.isReady && Reveal.isReady()", timeout=20000)
        page.evaluate("Reveal.configure({ fragments: false, transition: 'none', backgroundTransition: 'none' })")  # final state, no fades
        slides = page.evaluate(WALK, {"exclude": EXCLUDE, "shapes": shapes, "settle": a.settle})
        if a.shots:
            out = pathlib.Path(a.shots)
            out.mkdir(parents=True, exist_ok=True)
            for i, s in enumerate(slides):
                page.evaluate(f"Reveal.slide({s['h']},{s['v']})")
                page.wait_for_timeout(300)
                page.screenshot(path=str(out / f"{i + 1:03d}.png"))
        clicks = None
        if a.step:
            page.evaluate("Reveal.configure({ fragments: true })")
            clicks = page.evaluate(STEP)
        browser.close()

    problems = []
    for i, s in enumerate(slides):
        where = f"page {i + 1}" + (f" §{s['number']}" if s["number"] else "") + f" ({s['label']})"
        if not s["visible"]:
            problems.append(f"{where}: not visible")
        if s["overflow"]:
            problems.append(f"{where}: overflows the frame even at the autofit floor")
        if s["collision"]:
            problems.append(f"{where}: content overlaps the footer")
        if s["mm"] != s["mmok"]:
            problems.append(f"{where}: {s['mm'] - s['mmok']} diagram(s) not rendered")
        if s["mmClipped"]:
            problems.append(f"{where}: {s['mmClipped']} diagram label(s) clipped")
        if s["tiny"]:
            problems.append(f"{where}: text below 14px: {'; '.join(s['tiny'])}")
        for lay in s["layouts"]:
            for pr in lay["problems"]:
                problems.append(f"{where}: layout {lay['name']}: {pr}")
            if lay["clipped"]:
                problems.append(f"{where}: layout {lay['name']}: {lay['clipped']} item text(s) clipped")
        for t in LEAKS + audience + a.tags:
            if t in s["text"]:
                problems.append(f"{where}: working-aid text '{t}' is visible")
    problems += [f"console: {e}" for e in errors]

    numbers = {s["number"]: s for s in slides if s["number"]}
    if exp:
        for num, e in exp.items():
            s = numbers.get(num)
            if s is None:
                problems.append(f"outline §{num} ({e['title']}): not in the deck")
                continue
            got = [l["name"] for l in s["layouts"]]
            if sorted(got) != sorted(e["layouts"]):
                problems.append(f"outline §{num}: layouts {e['layouts']} in the outline, {got} in the deck")
            if e["notes"] and not s["notes"]:
                problems.append(f"outline §{num}: speaker notes missing from the deck")
        for num in numbers:
            if num not in exp:
                problems.append(f"deck §{num}: not in the outline")

    fitted = [{"page": i + 1, "number": s["number"], "fit": s["fit"], "compact": s["compact"]}
              for i, s in enumerate(slides) if s["fit"] < 1 or s["compact"]]
    summary = {
        "slides": len(slides),
        "diagrams": sum(s["mm"] for s in slides),
        "diagrams_rendered": sum(s["mmok"] for s in slides),
        "layouts": sum(len(s["layouts"]) for s in slides),
        "overflow": sum(1 for s in slides if s["overflow"]),
        "collisions": sum(1 for s in slides if s["collision"]),
        "console_errors": len(errors),
        "fragment_clicks": clicks,
        "autofit": fitted,
        "problems": problems,
    }
    if a.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"{summary['slides']} slides checked; {summary['overflow']} overflow; {summary['collisions']} collisions; "
              f"{summary['diagrams_rendered']} of {summary['diagrams']} diagrams rendered; {summary['layouts']} layouts; "
              f"{summary['console_errors']} console errors" + (f"; {clicks} fragment clicks" if clicks is not None else "") + ".")
        if fitted:
            print("Autofit or compaction: " + ", ".join(
                f"page {f['page']}" + (f" §{f['number']}" if f["number"] else "") + (f" {f['fit']:.2f}em" if f["fit"] < 1 else "")
                + (f" [{f['compact']}]" if f["compact"] else "") for f in fitted))
        if problems:
            print("PROBLEMS:")
            for x in problems:
                print("  - " + x)
        else:
            print("All checks passed.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
