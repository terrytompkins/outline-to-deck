/* outline-to-deck layouts.js: geometry and compaction for the layouts in knowledge/LAYOUTS.md.
 * Registers window.DeckLayouts[name] = { render(el), compact(el, step) -> bool }.
 * deck.js calls render when a slide is first shown, and compact (steps 1..3) before autofit.
 * Must load before deck.js. */
(function () {
  'use strict';
  var L = window.DeckLayouts = window.DeckLayouts || {};
  var SVGNS = 'http://www.w3.org/2000/svg';

  function items(lay) { return Array.prototype.slice.call(lay.querySelectorAll(':scope > .layout__items > .layout__item')); }
  function add(lay, cls) { if (lay.classList.contains(cls)) return false; lay.classList.add(cls); return true; }
  function variant(lay, v) { return (lay.dataset.variant || '') === v; }
  function frame(lay) {
    var old = lay.querySelector(':scope > .layout__frame');
    if (old) old.remove();
    var w = lay.offsetWidth, h = lay.offsetHeight;
    var svg = document.createElementNS(SVGNS, 'svg');
    svg.setAttribute('class', 'layout__frame chrome');
    svg.setAttribute('viewBox', '0 0 ' + w + ' ' + h);
    svg.setAttribute('aria-hidden', 'true');
    lay.insertBefore(svg, lay.firstChild);
    return { svg: svg, w: w, h: h };
  }
  function node(svg, tag, attrs) {
    var e = document.createElementNS(SVGNS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    svg.appendChild(e);
    return e;
  }
  function place(el, xPct, yPct) { el.style.left = xPct + '%'; el.style.top = yPct + '%'; }
  function ring(n, i, rx, ry) {          // position i of n around an ellipse, starting at the top
    var a = -Math.PI / 2 + 2 * Math.PI * i / n;
    return { x: 50 + rx * Math.cos(a), y: 50 + ry * Math.sin(a), a: a };
  }
  function simple(steps) {               // compaction: is-compact, then is-wrapped when allowed
    return function (lay, step) {
      if (step === 1) return add(lay, 'is-compact');
      if (step === 2 && steps(lay)) return add(lay, 'is-wrapped');
      return false;
    };
  }

  L.list = {
    render: function (lay) { if (lay.hasAttribute('data-numbered')) lay.classList.add('is-numbered'); },
    compact: simple(function (lay) { return items(lay).length <= 4; })
  };
  L.process = { compact: simple(function (lay) { return items(lay).length >= 4; }) };
  L.timeline = { compact: simple(function (lay) { return !variant(lay, 'vertical'); }) };
  L.columns = { compact: simple(function (lay) { return items(lay).length >= 3; }) };
  L.hierarchy = { compact: simple(function (lay) { return !variant(lay, 'left-right'); }) };
  L.matrix = { compact: simple(function () { return false; }) };

  function trapezoids(lay, widening) {
    var its = items(lay), n = its.length;
    var W = its.map(function (_, i) { var t = n > 1 ? i / (n - 1) : 1; return widening ? 40 + 60 * t : 100 - 60 * t; });
    its.forEach(function (it, i) {
      var lab = it.querySelector(':scope > .layout__label');
      if (!lab) return;
      var other = widening ? (i > 0 ? W[i - 1] : W[0] * 0.35) : (i < n - 1 ? W[i + 1] : W[i] * 0.6);
      var inset = Math.max(0, (W[i] - other) / (2 * W[i]) * 100).toFixed(1) + '%';
      lab.style.setProperty('--w', W[i] + '%');
      lab.style.setProperty('--clip', widening
        ? 'polygon(' + inset + ' 0, calc(100% - ' + inset + ') 0, 100% 100%, 0 100%)'
        : 'polygon(0 0, 100% 0, calc(100% - ' + inset + ') 100%, ' + inset + ' 100%)');
    });
  }
  L.pyramid = { render: function (lay) { trapezoids(lay, true); }, compact: simple(function () { return false; }) };
  L.funnel = { render: function (lay) { trapezoids(lay, false); }, compact: simple(function () { return false; }) };

  L.radial = {
    render: function (lay) {
      var root = items(lay)[0];
      if (!root) return;
      var spokes = Array.prototype.slice.call(root.querySelectorAll(':scope > ul > li, :scope > ol > li'));
      var f = frame(lay), n = spokes.length;
      spokes.forEach(function (s, i) {
        var p = ring(n, i, 38, 40);
        place(s, p.x, p.y);
        node(f.svg, 'line', { x1: f.w / 2, y1: f.h / 2, x2: f.w * p.x / 100, y2: f.h * p.y / 100 });
      });
      var c = root.querySelector(':scope > .layout__label');
      if (c) place(c, 50, 50);
    },
    compact: function (lay, step) { if (step === 1 && add(lay, 'is-compact')) { L.radial.render(lay); return true; } return false; }
  };

  L.cycle = {
    render: function (lay) {
      var its = items(lay), n = its.length, f = frame(lay);
      var rx = 36, ry = 38;
      its.forEach(function (it, i) { var p = ring(n, i, rx, ry); place(it, p.x, p.y); });
      var cx = f.w / 2, cy = f.h / 2, Rx = f.w * rx / 100, Ry = f.h * ry / 100;
      node(f.svg, 'ellipse', { cx: cx, cy: cy, rx: Rx, ry: Ry, style: 'stroke:var(--connector);stroke-width:2;fill:none' });
      for (var i = 0; i < n; i++) {            // an arrowhead halfway to the next item, pointing along the ring
        var a = -Math.PI / 2 + 2 * Math.PI * (i + 0.5) / n;
        var x = cx + Rx * Math.cos(a), y = cy + Ry * Math.sin(a);
        var tx = -Rx * Math.sin(a), ty = Ry * Math.cos(a), len = Math.sqrt(tx * tx + ty * ty);
        var ux = tx / len, uy = ty / len, s = 9;
        var pts = [[x + ux * s, y + uy * s], [x - ux * s - uy * s * 0.8, y - uy * s + ux * s * 0.8], [x - ux * s + uy * s * 0.8, y - uy * s - ux * s * 0.8]];
        node(f.svg, 'polygon', { 'class': 'arrow', points: pts.map(function (p) { return p[0].toFixed(1) + ',' + p[1].toFixed(1); }).join(' ') });
      }
    },
    compact: function (lay, step) { if (step === 1 && add(lay, 'is-compact')) { L.cycle.render(lay); return true; } return false; }
  };

  // Circle centers, label points and the overlap point, in units of the radius from the layout's center.
  var VENN = {
    2: { r: 0.46, c: [[-0.62, 0], [0.62, 0]], labels: [[-1.0, 0], [1.0, 0]], overlap: [0, 0] },
    3: { r: 0.35, c: [[-0.58, -0.36], [0.58, -0.36], [0, 0.62]], labels: [[-1.12, -0.7], [1.12, -0.7], [0, 1.22]], overlap: [0, 0.02] }
  };
  var FILLS = ['--accent-tint', '--callout-remember-tint', '--callout-fieldnote-tint'];
  L.venn = {
    render: function (lay) {
      var its = items(lay), spec = VENN[its.length] || VENN[3];
      var f = frame(lay), r = Math.min(f.h * spec.r, f.w * 0.2), cx = f.w / 2, cy = f.h / 2;
      function pct(p) { return [(cx + p[0] * r) / f.w * 100, (cy + p[1] * r) / f.h * 100]; }
      spec.c.slice(0, its.length).forEach(function (c, i) {
        node(f.svg, 'circle', { 'class': 'venn-set', cx: cx + c[0] * r, cy: cy + c[1] * r, r: r,
          style: 'fill:var(' + FILLS[i] + ');fill-opacity:.85;mix-blend-mode:multiply' });
      });
      its.forEach(function (it, i) { var p = spec.labels[i]; if (p) { p = pct(p); place(it, p[0], p[1]); } });
      var ov = lay.querySelector(':scope > .venn-overlap');
      if (!ov && lay.dataset.overlap) {
        ov = document.createElement('div');
        ov.className = 'venn-overlap';
        ov.textContent = lay.dataset.overlap;
        lay.appendChild(ov);
      }
      if (ov) { var o = pct(spec.overlap); place(ov, o[0], o[1]); }
    },
    compact: function (lay, step) { if (step === 1 && add(lay, 'is-compact')) { L.venn.render(lay); return true; } return false; }
  };
})();
