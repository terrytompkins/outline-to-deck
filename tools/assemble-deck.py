#!/usr/bin/env python3
"""assemble-deck: build one self-contained Reveal.js deck from slide fragments.

Commands:
  build          fragments + runtime + base CSS + style CSS + CDN tags  ->  deck.html
  replace-topic  swap one topic (or title/agenda/appendix/sources) in an existing deck
  edit           exact-string replacements that must each match exactly once

  python3 assemble-deck.py build --fragments frags/ --style field-guide --out deck.html --outline OUTLINE.md
  python3 assemble-deck.py replace-topic deck.html 3 frags/topic-3.html
  python3 assemble-deck.py edit deck.html --find "old text" --replace "new text" [--find ... --replace ...]

Fragment files (written by Claude to the markup contract in DECK-BUILD-SPEC.md):
  title.html, agenda.html, topic-<N>.html for every top-level section, and optionally
  appendix.html and sources.html. Topics are placed in time-plan order when --outline is given.

Every library is loaded from its first CDN with an SRI hash; if that fails, from the second
(tools/pins.json). Everything else is inlined, including local images as data URIs, so the deck
is one file. Standard library only. Exit code 0 on success, 1 on any error (nothing is written).
"""
from __future__ import annotations

import argparse
import base64
import datetime
import json
import mimetypes
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

PARTS_BEFORE = ["title", "agenda"]
PARTS_AFTER = ["appendix", "sources"]
END = "<!-- O2D:SLIDES-END -->"
KNOWN_TYPES = {"quick-check", "myth-vs-fact", "recap", "try-it-yourself", "quote", "key-figure", "backup"}
KNOWN_CALLOUTS = {"note", "tip", "remember", "watchout", "underthehood", "fieldnote", "important", "warning", "caution"}


class BuildError(Exception):
    pass


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def cdn_tags(pins: dict, need_mermaid: bool, warnings: list) -> tuple[str, str]:
    """Return (head link tags, body script tags) from pins.json, primary CDN first."""
    head, body = [], []
    for lib_name, lib in pins["libraries"].items():
        if lib_name == "mermaid" and not need_mermaid:
            continue
        order = lib.get("order", ["cdnjs", "jsdelivr"])
        for fname, f in lib["files"].items():
            p, fb = f[order[0]], f[order[1]]
            for which, e in ((order[0], p), (order[1], fb)):
                if not e.get("sri"):
                    warnings.append(f"{lib_name} {fname}: no SRI hash for {which}; run tools/update-pins.py")
            def integ(e):
                return f' integrity="{e["sri"]}"' if e.get("sri") else ""
            if f["kind"] == "css":
                fallback_js = (f"this.onerror=null;" + (f"this.integrity='{fb['sri']}';" if fb.get("sri") else "this.removeAttribute('integrity');")
                               + f"this.href='{fb['url']}'")
                head.append(f'<link rel="stylesheet" href="{p["url"]}"{integ(p)} crossorigin="anonymous" onerror="{fallback_js}">')
            else:
                glob = f.get("global", "")
                body.append(f'<script src="{p["url"]}"{integ(p)} crossorigin="anonymous"></script>')
                body.append("<script>window.%s||document.write('<script src=\"%s\"%s crossorigin=\"anonymous\"><\\/script>')</script>"
                            % (glob, fb["url"], integ(fb).replace('"', '\\"')))
    return "\n".join(head), "\n".join(body)


def inline_images(html: str, assets: str, errors: list) -> str:
    def repl(m):
        src = m.group(2)
        if re.match(r"(https?:|data:)", src):
            return m.group(0)
        path = os.path.join(assets, src)
        if not os.path.exists(path):
            errors.append(f"image not found: {src} (looked in {assets})")
            return m.group(0)
        mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f'{m.group(1)}data:{mime};base64,{data}{m.group(3)}'
    return re.sub(r'(<img\b[^>]*?\bsrc=")([^"]+)(")', repl, html)


def check_fragment(name: str, html: str, errors: list, warnings: list, layouts: set | None):
    if re.search(r"<script\b", html, re.I):
        errors.append(f"{name}: fragments may not contain <script>; the runtime handles behavior")
    opens, closes = len(re.findall(r"<section\b", html)), len(re.findall(r"</section>", html))
    if opens != closes:
        errors.append(f"{name}: {opens} <section> tags but {closes} </section>")
    for t in re.findall(r'<section\b[^>]*\bdata-type="([^"]+)"', html):
        if t not in KNOWN_TYPES:
            warnings.append(f"{name}: unknown slide data-type '{t}'")
    for t in re.findall(r'class="callout"[^>]*data-type="([^"]+)"|data-type="([^"]+)"[^>]*class="callout"', html):
        t = (t[0] or t[1]).lower()
        if t not in KNOWN_CALLOUTS:
            warnings.append(f"{name}: unknown callout type '{t}'")
    if layouts is not None:
        for t in re.findall(r'data-layout="([^"]+)"', html):
            if t not in layouts:
                warnings.append(f"{name}: unknown layout '{t}'")


def topic_order(fragments: str, outline_path: str | None) -> list[str]:
    found = {}
    for fn in os.listdir(fragments):
        m = re.fullmatch(r"topic-(\d+)\.html", fn)
        if m:
            found[m.group(1)] = fn
    order = sorted(found, key=int)
    if outline_path:
        from outline_parser import load_registry, parse_outline
        reg = load_registry(os.path.join(ROOT, "knowledge"))
        o = parse_outline(read(outline_path), reg)
        plan = [r["number"] for r in o.timeplan if r["number"]]
        missing = [n for n in plan if n not in found]
        if missing:
            raise BuildError(f"no fragment for section(s) {', '.join(missing)} (expected topic-N.html)")
        order = plan + [n for n in order if n not in plan]
    return order


def outline_meta(outline_path):
    if not outline_path:
        return {}, {}
    from outline_parser import load_registry, parse_outline
    reg = load_registry(os.path.join(ROOT, "knowledge"))
    o = parse_outline(read(outline_path), reg)
    titles = {s.number: s.title for s in o.sections if s.is_slide and s.level == 1}
    title = next((s.title.replace("OUTLINE — ", "").replace("OUTLINE - ", "") for s in o.sections if s.kind == "title"), "")
    return {"title": title, "version": o.status.get("version", "")}, titles


def find_style(style: str) -> str:
    if os.path.exists(style):
        return style
    for cand in (os.path.join(ROOT, "knowledge", "styles", f"{style}.css"),
                 os.path.join(ROOT, "knowledge", "styles", f"{style.lower().replace('style-', '')}.css")):
        if os.path.exists(cand):
            return cand
    if style.lower() in ("base", "style-base"):
        return ""
    raise BuildError(f"style CSS not found: {style}")


def cmd_build(a) -> int:
    errors, warnings = [], []
    pins = json.loads(read(a.pins))
    runtime_dir = a.runtime
    base_css = read(os.path.join(runtime_dir, "base.css")) + "\n" + read(os.path.join(runtime_dir, "layouts.css"))
    deck_js = "\n".join(read(os.path.join(runtime_dir, f)) for f in ("layouts.js", "charts.js", "deck.js"))
    style_path = find_style(a.style)
    style_css = read(style_path) if style_path else ""
    style_name = os.path.splitext(os.path.basename(style_path))[0] if style_path else "base"
    layouts = None
    try:
        from outline_parser import load_registry
        layouts = set(load_registry(os.path.join(ROOT, "knowledge")).layouts)
    except Exception:
        pass

    order = topic_order(a.fragments, a.outline)
    meta, titles = outline_meta(a.outline)
    parts = []
    for name in PARTS_BEFORE:
        path = os.path.join(a.fragments, f"{name}.html")
        if not os.path.exists(path):
            errors.append(f"missing {name}.html")
            continue
        html = read(path).strip()
        check_fragment(f"{name}.html", html, errors, warnings, layouts)
        parts.append(f"<!-- {name.upper()} -->\n{html}")
    for n in order:
        html = read(os.path.join(a.fragments, f"topic-{n}.html")).strip()
        check_fragment(f"topic-{n}.html", html, errors, warnings, layouts)
        if f'id="s{n}"' not in html:
            errors.append(f"topic-{n}.html: the topic stack needs id=\"s{n}\"")
        title = titles.get(n) or re.sub(r"<[^>]+>", "", (re.search(r"<h2[^>]*>(.*?)</h2>", html, re.S) or [None, ""])[1]).strip()
        parts.append(f"<!-- TOPIC {n}: {title} -->\n{html}")
    for name in PARTS_AFTER:
        path = os.path.join(a.fragments, f"{name}.html")
        if os.path.exists(path):
            html = read(path).strip()
            check_fragment(f"{name}.html", html, errors, warnings, layouts)
            parts.append(f"<!-- {name.upper()} -->\n{html}")
    slides = "\n".join(parts)
    slides = inline_images(slides, a.assets or a.fragments, errors)
    need_mermaid = {"on": True, "off": False}.get(a.mermaid, 'class="mermaid"' in slides)
    head_tags, body_tags = cdn_tags(pins, need_mermaid, warnings)

    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print("Nothing written.", file=sys.stderr)
        return 1

    versions = " | ".join(f"{k} {v['version']}" for k, v in pins["libraries"].items() if k != "mermaid" or need_mermaid)
    title = a.title or meta.get("title") or "Deck"
    stamp = (f"outline-to-deck v2 | built {datetime.date.today().isoformat()} | style {style_name} | {versions}"
             + (f" | outline v{meta['version']}" if meta.get("version") else ""))
    doc = f"""<!DOCTYPE html>
<html lang="{a.lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<!-- {stamp} -->
{head_tags}
<style>
/* ---- runtime/base.css + runtime/layouts.css ---- */
{base_css}
/* ---- style: {style_name} ---- */
{style_css}
</style>
</head>
<body>
<div class="reveal" data-build="{a.build}"><div class="slides">
<!-- O2D:SLIDES-START -->
{slides}
{END}
</div></div>
{body_tags}
<script>
/* ---- runtime/layouts.js + charts.js + deck.js ---- */
{deck_js}
</script>
</body>
</html>
"""
    write(a.out, doc)
    print(f"Wrote {a.out}: {len(order)} topic(s), style {style_name}, {'with' if need_mermaid else 'without'} Mermaid, {len(doc):,} bytes.")
    return 0


def part_bounds(doc: str, which: str) -> tuple[int, int]:
    if which.isdigit():
        starts = [m.start() for m in re.finditer(rf"<!-- TOPIC {which}: ", doc)]
    else:
        starts = [m.start() for m in re.finditer(rf"<!-- {which.upper()} -->", doc)]
    if len(starts) != 1:
        raise BuildError(f"expected exactly one marker for '{which}', found {len(starts)}")
    start = starts[0]
    nxt = re.search(r"<!-- (TOPIC \d+: |TITLE -->|AGENDA -->|APPENDIX -->|SOURCES -->|O2D:SLIDES-END)", doc[start + 5:])
    end = start + 5 + nxt.start() if nxt else len(doc)
    return start, end


def cmd_replace(a) -> int:
    errors, warnings = [], []
    doc = read(a.deck)
    html = read(a.fragment).strip()
    check_fragment(os.path.basename(a.fragment), html, errors, warnings, None)
    if a.part.isdigit() and f'id="s{a.part}"' not in html:
        errors.append(f"the fragment needs id=\"s{a.part}\"")
    html = inline_images(html, a.assets or os.path.dirname(os.path.abspath(a.fragment)), errors)
    try:
        start, end = part_bounds(doc, a.part)
    except BuildError as e:
        errors.append(str(e))
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if errors:
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        print("Nothing written.", file=sys.stderr)
        return 1
    marker = doc[start:doc.index("-->", start) + 3]
    doc = doc[:start] + marker + "\n" + html + "\n" + doc[end:]
    write(a.deck, doc)
    print(f"Replaced {'topic ' + a.part if a.part.isdigit() else a.part} in {a.deck}.")
    return 0


def cmd_edit(a) -> int:
    if len(a.find) != len(a.replace):
        print("error: give one --replace for every --find", file=sys.stderr)
        return 1
    doc = read(a.deck)
    for f, r in zip(a.find, a.replace):
        n = doc.count(f)
        if n != 1:
            print(f"error: '{f[:60]}' matches {n} times (must be exactly 1). Nothing written.", file=sys.stderr)
            return 1
        doc = doc.replace(f, r)
    write(a.deck, doc)
    print(f"Applied {len(a.find)} edit(s) to {a.deck}.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build one self-contained Reveal.js deck from fragments.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="assemble a deck")
    b.add_argument("--fragments", required=True, help="folder with title.html, agenda.html, topic-N.html ...")
    b.add_argument("--style", default="base", help="style name (field-guide, toons) or a CSS file path")
    b.add_argument("--out", required=True)
    b.add_argument("--outline", help="OUTLINE.md: orders topics by the time plan and fills title and version")
    b.add_argument("--title", help="browser tab title (default: from the outline)")
    b.add_argument("--build", choices=["on", "off"], default="off", help="layouts appear one item at a time by default")
    b.add_argument("--mermaid", choices=["auto", "on", "off"], default="auto")
    b.add_argument("--assets", help="folder for local images (default: the fragments folder)")
    b.add_argument("--lang", default="en")
    b.add_argument("--pins", default=os.path.join(HERE, "pins.json"))
    b.add_argument("--runtime", default=os.path.join(ROOT, "runtime"))
    r = sub.add_parser("replace-topic", help="replace one topic, or title/agenda/appendix/sources")
    r.add_argument("deck")
    r.add_argument("part", help="a top-level section number, or title, agenda, appendix, sources")
    r.add_argument("fragment")
    r.add_argument("--assets")
    e = sub.add_parser("edit", help="exact-string replacements; each must match exactly once")
    e.add_argument("deck")
    e.add_argument("--find", action="append", default=[])
    e.add_argument("--replace", action="append", default=[])
    a = ap.parse_args(argv)
    try:
        return {"build": cmd_build, "replace-topic": cmd_replace, "edit": cmd_edit}[a.cmd](a)
    except BuildError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
