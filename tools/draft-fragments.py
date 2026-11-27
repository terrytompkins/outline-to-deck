#!/usr/bin/env python3
"""draft-fragments: write first-draft slide fragments from an approved outline.

Everything the outline fully determines becomes finished markup (DECK-BUILD-SPEC.md section 4):
title, agenda in time-plan order, sections and numbers, bullets, paragraphs, tables, code,
callouts, layouts, diagrams, charts, slide types, images, embeds, footers with sources and
As of dates, speaker notes, appendix and Sources slide. What needs judgment is left as a marked
draft for Claude to finish:

  <figure class="visual" data-draft="visual">   a Suggested visual to design as inline SVG

check-deck.py fails any deck that still contains data-draft, so nothing ships half-done.
Claude then edits the drafts: designs visuals, tightens wording, adds speaker notes.

Usage:
  python3 tools/draft-fragments.py OUTLINE.md --brief BRIEF.md --out frags
      [--knowledge knowledge] [--pass 1] [--topics 2,5] [--force] [--json]

  --pass 1     title, agenda and horizontal slides only (pass 2, the default, adds vertical slides)
  --topics     only these topic files (for a partial rebuild with assemble-deck.py replace-topic)
  --force      overwrite existing fragment files

Existing files are never overwritten without --force, because Claude edits them. An existing
topic file is merged instead: every slide already in it is kept as it is, and slides it lacks are
added in outline order. So pass 1 and pass 2 are the same command with a different --pass.
Other existing files (title, agenda, appendix, sources) are kept.

Exit code 0; 2 on usage errors.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from outline_parser import load_registry, parse_outline  # noqa: E402
from render_blocks import inline, layout_html, source_links  # noqa: E402

E = html.escape
TYPES = {"Quick check": "quick-check", "Myth vs fact": "myth-vs-fact", "Recap": "recap",
         "Try it yourself": "try-it-yourself", "Quote": "quote", "Key figure": "key-figure", "Backup": "backup"}
PRIORITIES = {"Core", "Brief", "Self-guided"}
ASOF_RE = re.compile(r"\bAs of ((?:January|February|March|April|May|June|July|August|September|October|November|December)"
                     r"(?: \d{1,2},)? \d{4})")
COMPANIONS = {"Image": {"Alt", "Caption"}, "Embed": {"Caption"}}


def brief_fields(text: str) -> dict:
    """The BRIEF.md fields this tool needs, with [TBD] treated as unset."""
    out = {}
    for key, name in [("Show the presenter's name on the title slide", "show_presenter"), ("Presenter", "presenter"),
                      ("Sources slide", "sources"), ("Event or series", "series")]:
        m = re.search(r"\*\*" + re.escape(key) + r":\*\*\s*(.*)", text)
        if m and "[TBD" not in m.group(1):
            out[name] = m.group(1).strip()
    return out


def slide_text(s) -> str:
    return "\n".join(t for _, t in s.body)


def strip_asof(text: str) -> str:
    return re.sub(r"\s*\(?\s*" + ASOF_RE.pattern + r"\s*\)?\.?", "", text)


def footer(s) -> str:
    text = slide_text(s)
    links = list(dict.fromkeys(source_links(text)))
    m = ASOF_RE.search(text)
    if not links and not m:
        return ""
    parts = ([f'<span class="asof">As of {m.group(1)}</span>'] if m else []) + [f'<a href="{u}">{E(t)}</a>' for t, u in links]
    return "<footer>" + "".join(parts) + "</footer>"


def notes(s) -> str:
    out = []
    for b in s.blocks:
        if b.kind == "key" and b.key == "Speaker notes":
            out += [b.text] if b.text else []
            out += [i.text for i in b.items]
    for m in re.finditer(r"\[UNVERIFIED:\s*([^\]]+)\]", slide_text(s)):
        out.append("Unverified: " + m.group(1).strip().rstrip(".") + ".")
    if s.slide_type == "Quick check":
        out.append("Pause for answers before revealing.")
    return f'<aside class="notes">{E(" ".join(out))}</aside>' if out else ""


def items(lst) -> str:
    def one(i):
        kids = f"<ul>{items(i.children)}</ul>" if i.children else ""
        return f"<li>{inline(strip_asof(i.text))}{kids}</li>"
    return "".join(one(i) for i in lst)


def list_html(b) -> str:
    tag = "ol" if b.items and b.items[0].ordered else "ul"
    return f"<{tag}>{items(b.items)}</{tag}>"


def table_html(lines) -> str:
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in lines if ln.strip().startswith("|")]
    rows = [r for r in rows if not set("".join(r)) <= set("-: ")]
    if not rows:
        return ""
    head = "<thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in rows[0]) + "</tr></thead>"
    body = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
    return f"<table>{head}<tbody>{body}</tbody></table>"


def chart_html(b) -> str:
    kv = {}
    for ln in b.lines:
        if not ln.strip().startswith("|") and ":" in ln:
            k, v = ln.split(":", 1)
            kv[k.strip().lower()] = v.strip()
    attrs = f' data-type="{E(kv.get("type", "bar"))}"'
    if kv.get("title"):
        attrs += f' data-title="{E(kv["title"])}"'
    if kv.get("unit"):
        attrs += f' data-unit="{E(kv["unit"])}"'
    return f'<figure class="chart"{attrs}>{table_html(b.lines)}</figure>'


def callout_html(b) -> str:
    title = f' data-title="{E(b.text)}"' if b.text else ""
    paras, bullets = [], []
    for ln in b.lines:
        m = re.match(r"\s*[-*+]\s+(.*)", ln)
        if m:
            bullets.append(f"<li>{inline(m.group(1))}</li>")
        elif ln.strip():
            if bullets:
                paras.append("<ul>" + "".join(bullets) + "</ul>")
                bullets = []
            paras.append(ln.strip())
    text, merged = [], []
    for p in paras:  # join consecutive text lines into one paragraph
        if p.startswith("<ul>"):
            if text:
                merged.append(f"<p>{inline(' '.join(text))}</p>")
                text = []
            merged.append(p)
        else:
            text.append(p)
    if text:
        merged.append(f"<p>{inline(' '.join(text))}</p>")
    if bullets:
        merged.append("<ul>" + "".join(bullets) + "</ul>")
    return f'<div class="callout" data-type="{b.key.lower()}"{title}>{"".join(merged)}</div>'


def media_html(b, companions) -> str:
    cap = companions.get("Caption", "")
    figcap = f"<figcaption>{inline(cap)}</figcaption>" if cap else ""
    src = E(b.text.strip())
    if b.key == "Image":
        return f'<figure class="image"><img src="{src}" alt="{E(companions.get("Alt", ""))}">{figcap}</figure>'
    title = E(cap or "Embedded page")
    return (f'<figure class="embed"><iframe src="{src}" loading="lazy" title="{title}"></iframe>'
            f'<a class="embed-link" href="{src}">Open the page</a>{figcap}</figure>')


def visual_html(b) -> str:
    return (f'<figure class="visual" data-draft="visual">\n    <!-- Draft: replace with an inline SVG (DECK-BUILD-SPEC.md §4, Suggested visual) -->\n'
            f'    <p class="draft">Visual to design: {E(b.text)}</p>\n  </figure>')


def is_source_line(text: str) -> bool:
    rest = re.sub(r"\(\s*\[[^\]\n]+\]\(https?://[^)\s]+\)\s*\)", "", strip_asof(text))
    return not re.sub(r"[\s.,;()]", "", rest)


def body(s, reg, todos) -> str:
    keys = {b.key: b for b in s.blocks if b.kind == "key"}
    st = s.slide_type

    def k(name):
        return inline(keys[name].text) if name in keys else ""
    if st == "Myth vs fact":
        cells = "".join(f'<div class="{b.key.lower()}"><p>{inline(b.text)}</p></div>'
                        for b in s.blocks if b.kind == "key" and b.key in ("Myth", "Fact"))
        return f'<div class="myths">{cells}</div>'
    if st == "Quick check":
        opts = f'<ol class="options">{items(keys["Options"].items)}</ol>' if "Options" in keys and keys["Options"].items else ""
        return f'<p class="question">{k("Question")}</p>{opts}<div class="answer">{k("Answer")}</div>'
    if st == "Try it yourself":
        steps = items(keys["Steps"].items) if "Steps" in keys else ""
        return (f'<p class="meta">Time: {k("Time")}</p><ol class="steps">{steps}</ol>'
                f'<div class="outcome">{k("Expected outcome")}</div>')
    if st == "Recap":
        pts = items(keys["Points"].items) if "Points" in keys else ""
        return f'<ul class="checks">{pts}</ul>'
    if st == "Quote":
        ctx = f'<p class="context">{k("Context")}</p>' if "Context" in keys else ""
        return f'<blockquote class="quote"><p>{k("Quote")}</p><cite>{k("Attribution")}</cite>{ctx}</blockquote>'
    if st == "Key figure":
        ctx = f'<p class="context">{k("Context")}</p>' if "Context" in keys else ""
        return (f'<div class="key-figure"><p class="figure">{k("Figure")}</p><p class="figure-label">{k("Label")}</p>'
                f'{ctx}</div>')

    out, diagrams = [], []
    bl = s.blocks
    skip = set()
    for i, b in enumerate(bl):
        if i in skip:
            continue
        if b.kind == "layout":
            out.append(layout_html(b, reg))
        elif b.kind == "list":
            out.append(list_html(b))
        elif b.kind == "para":
            if not is_source_line(b.text):
                out.append(f"<p>{inline(strip_asof(b.text))}</p>")
        elif b.kind == "quote":
            out.append(f"<blockquote><p>{inline(b.text)}</p></blockquote>")
        elif b.kind == "table":
            out.append(table_html(b.lines))
        elif b.kind == "callout":
            out.append(callout_html(b))
        elif b.kind == "fence" and b.key == "mermaid":
            fig = '<figure class="diagram"><pre class="mermaid">\n' + "\n".join(b.lines).replace("&", "&amp;").replace("<", "&lt;") + "\n</pre></figure>"
            diagrams.append(len(out))
            out.append(fig)
        elif b.kind == "fence" and b.key == "chart":
            out.append(chart_html(b))
        elif b.kind == "fence":
            out.append('<pre class="code"><code>' + E("\n".join(b.lines)) + "</code></pre>")
        elif b.kind == "key":
            if b.key in ("Speaker notes", "Diagram") or b.key in reg.layout_fields:
                continue
            if b.key == "Main points":
                if b.items:
                    out.append(f"<ul>{items(b.items)}</ul>")
            elif b.key == "Suggested visual":
                out.append(visual_html(b))
                todos.append({"slide": s.number, "what": "visual", "detail": b.text})
            elif b.key in COMPANIONS:
                comp = {}
                for j in range(i + 1, len(bl)):
                    c = bl[j]
                    if c.kind == "key" and c.key in COMPANIONS[b.key]:
                        comp[c.key] = c.text
                        skip.add(j)
                    else:
                        break
                out.append(media_html(b, comp))
            elif b.key in ("Alt", "Caption"):
                continue
            else:
                out.append(f"<p><strong>{E(b.key)}:</strong> {inline(b.text)}</p>")
                if b.items:
                    out.append(f"<ul>{items(b.items)}</ul>")
    if len(diagrams) == 2 and diagrams[1] == diagrams[0] + 1:
        a, c = diagrams
        out[a:c + 1] = [f'<div class="diagram-pair">{out[a]}{out[c]}</div>']
    return "\n  ".join(out)


def section_html(s, reg, todos) -> str:
    tag = "h2" if s.level == 1 else f"h{s.level + 1}"
    attrs = (' class="topic"' if s.level == 1 else "") + f' data-number="{s.number}"'
    if s.slide_type in TYPES:
        attrs += f' data-type="{TYPES[s.slide_type]}"'
    if s.slide_type == "Backup" and s.parent is not None:
        attrs += f' data-backup-for="{s.parent.number}"'
    parts = [f"<{tag}>{inline(s.title)}</{tag}>", body(s, reg, todos), footer(s), notes(s)]
    return f"<section{attrs}>\n  " + "\n  ".join(p for p in parts if p) + "\n</section>"


def draft(outline_text: str, reg, brief: dict, pass_: int = 2, topics: set | None = None):
    """Return ({file name: html}, [draft items to finish])."""
    o = parse_outline(outline_text, reg)
    files, todos = {}, []
    tops = [s for s in o.slides if s.level == 1]
    want = (lambda n: n in topics) if topics else (lambda n: True)

    if not topics:
        front = next((s for s in o.sections if s.kind == "front"), None)
        fk = {}
        if front:
            for b in front.blocks:
                if b.kind == "key":
                    fk[b.key] = " ".join([b.text] + [i.text for i in b.items]).strip()
        series = fk.get("Series") or brief.get("series", "")
        presenter = ""
        if brief.get("show_presenter", "").lower().startswith("y") and brief.get("presenter"):
            presenter = f'\n    <p class="presenter">{E(brief["presenter"])}</p>'
        nt = f'\n  <aside class="notes">{E(fk["Speaker notes"])}</aside>' if fk.get("Speaker notes") else ""
        files["title.html"] = (f'<section id="title" class="cover">\n  <div class="cover__card">\n'
                               f'    <p class="series">{E(series)}</p>\n    <h1>{E(fk.get("Title", ""))}</h1>\n'
                               f'    <p class="lead">{E(fk.get("Framing line", ""))}</p>{presenter}\n  </div>{nt}\n</section>\n')

        prio = {}
        order = []
        for r in o.timeplan:
            if r["number"]:
                order.append(r["number"])
                p = [c for c in r["cells"] if c in PRIORITIES]
                if p:
                    prio[r["number"]] = p[0]
        by_num = {s.number: s for s in tops}
        ordered = [by_num[n] for n in order if n in by_num] + [s for s in tops if s.number not in order]
        lis = "\n    ".join(f'<li data-number="{s.number}"' + (' class="self-guided"' if prio.get(s.number) == "Self-guided" else "")
                             + f'><a href="#/s{s.number}">{inline(s.title)}</a></li>' for s in ordered)
        files["agenda.html"] = f'<section id="agenda" class="agenda">\n  <h2>Agenda</h2>\n  <ol class="agenda-list">\n    {lis}\n  </ol>\n</section>\n'

    backups = []
    for t in tops:
        kids = [s for s in o.slides if s.top_number == t.number and s.level > 1]
        backups += [k for k in kids if k.slide_type == "Backup"]
        if not want(t.number):
            continue
        parts = [section_html(t, reg, todos)]
        if pass_ >= 2:
            parts += [section_html(k, reg, todos) for k in kids if k.slide_type != "Backup"]
        files[f"topic-{t.number}.html"] = f'<section id="s{t.number}">\n' + "\n".join(parts) + "\n</section>\n"

    if backups and pass_ >= 2 and not topics:
        files["appendix.html"] = ('<section id="appendix">\n<section class="appendix-divider"><h2>Appendix</h2></section>\n'
                                  + "\n".join(section_html(b, reg, todos) for b in backups) + "\n</section>\n")
    if brief.get("sources", "").lower().startswith("y") and not topics:
        files["sources.html"] = '<section id="sources" class="sources" data-auto data-visibility="uncounted"><h2>Sources</h2></section>\n'
    return files, todos


SLIDE_RE = re.compile(r'<section\b[^>]*\bdata-number="([\d.]+)"[^>]*>.*?</section>', re.S)


def merge_topic(existing: str, drafted: str):
    """Keep every slide in `existing`; add drafted slides it lacks, in outline order.
    Returns (html, added numbers, numbers kept that the outline no longer has)."""
    have = {}
    for m in SLIDE_RE.finditer(existing):
        have.setdefault(m.group(1), []).append(m.group(0))
    out, added, seen = [], [], set()
    for m in SLIDE_RE.finditer(drafted):
        n = m.group(1)
        if n in have:
            out += have[n]
            seen.add(n)
        else:
            out.append(m.group(0))
            added.append(n)
    extra = [n for n in have if n not in seen]
    for n in extra:
        out += have[n]
    head = re.match(r"\s*<section\b[^>]*>", drafted).group(0).strip()
    return head + "\n" + "\n".join(out) + "\n</section>\n", added, extra


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("outline")
    ap.add_argument("--brief")
    ap.add_argument("--knowledge", default=os.path.join(os.path.dirname(HERE), "knowledge"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--pass", dest="pass_", type=int, choices=(1, 2), default=2)
    ap.add_argument("--topics", help="comma-separated top-level numbers")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        reg = load_registry(a.knowledge, a.brief)
        text = open(a.outline, encoding="utf-8").read()
        brief = brief_fields(open(a.brief, encoding="utf-8").read()) if a.brief else {}
    except OSError as e:
        print(f"draft-fragments: {e}", file=sys.stderr)
        return 2
    topics = {t.strip() for t in a.topics.split(",")} if a.topics else None
    files, todos = draft(text, reg, brief, a.pass_, topics)
    os.makedirs(a.out, exist_ok=True)
    written, kept, merged = [], [], {}
    for name, content in files.items():
        path = os.path.join(a.out, name)
        if os.path.exists(path) and not a.force:
            if not name.startswith("topic-"):
                kept.append(name)
                continue
            content, added, extra = merge_topic(open(path, encoding="utf-8").read(), content)
            if not added:
                kept.append(name)
                continue
            merged[name] = {"added": added, "not_in_outline": extra}
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(name)
    # drafts only count where the drafted markup was used
    final = "".join(open(os.path.join(a.out, n), encoding="utf-8").read() for n in files)
    slides = {}
    for m in SLIDE_RE.finditer(final):
        slides[m.group(1)] = slides.get(m.group(1), "") + m.group(0)
    todos = [t for t in todos if "data-draft" in slides.get(t["slide"], "")]
    if a.json:
        print(json.dumps({"written": written, "kept": kept, "merged": merged, "drafts": todos}, indent=2))
    else:
        print(f"Wrote {len(written)} fragment file(s) to {a.out}." + (f" Kept unchanged: {', '.join(kept)}." if kept else ""))
        for name, m in merged.items():
            print(f"  {name}: added slides {', '.join(m['added'])}"
                  + (f"; kept {', '.join(m['not_in_outline'])}, which the outline no longer has" if m["not_in_outline"] else ""))
        for t in todos:
            print(f"  draft §{t['slide']}: {t['what']}: {t['detail']}")
        if todos:
            print(f"Finish {len(todos)} draft(s) before checking; check-deck.py fails any data-draft left in the deck.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
