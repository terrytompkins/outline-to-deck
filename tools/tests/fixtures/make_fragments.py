"""Generate fragments from an outline using render_blocks (fixture helper)."""
import os, sys, html
sys.path.insert(0, "tools")
from outline_parser import load_registry, parse_outline
from render_blocks import layout_html, inline
outline, outdir = sys.argv[1], sys.argv[2]
reg = load_registry("knowledge")
o = parse_outline(open(outline).read(), reg)
os.makedirs(outdir, exist_ok=True)
title = next(s.title for s in o.sections if s.kind == "title").replace("OUTLINE — ", "")
open(f"{outdir}/title.html", "w").write(f'<section id="title" class="cover"><div class="cover__card"><p class="series">Fixture series</p><h1>{html.escape(title)}</h1></div></section>\n')
tops = [s for s in o.slides if s.level == 1]
lis = "".join(f'<li data-number="{s.number}"><a href="#/s{s.number}">{html.escape(s.title)}</a></li>' for s in tops)
open(f"{outdir}/agenda.html", "w").write(f'<section id="agenda" class="agenda"><h2>Agenda</h2><ol class="agenda-list">{lis}</ol></section>\n')
def body(s):
    parts = []
    for b in s.blocks:
        if b.kind == "layout": parts.append(layout_html(b, reg))
        elif b.kind == "key" and b.key == "Main points" and b.items:
            parts.append("<ul>" + "".join(f"<li>{inline(i.text)}</li>" for i in b.items) + "</ul>")
        elif b.kind == "list":
            parts.append("<ul>" + "".join(f"<li>{inline(i.text)}</li>" for i in b.items) + "</ul>")
    return "\n  ".join(parts)
for t in tops:
    kids = [s for s in o.slides if s.top_number == t.number and s.level > 1]
    h = [f'<section id="s{t.number}">', f'<section class="topic" data-number="{t.number}">\n  <h2>{html.escape(t.title)}</h2>\n  {body(t)}\n</section>']
    for k in kids:
        h.append(f'<section data-number="{k.number}">\n  <h{k.level + 1}>{html.escape(k.title)}</h{k.level + 1}>\n  {body(k)}\n</section>')
    h.append("</section>")
    open(f"{outdir}/topic-{t.number}.html", "w").write("\n".join(h) + "\n")
print("fragments:", len(tops), "topics")
