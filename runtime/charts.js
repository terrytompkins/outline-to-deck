/* outline-to-deck charts.js: draws <figure class="chart" data-type="bar|column|line"> from its <table>.
 * The first column holds categories; each further column is a series. The table stays in the DOM,
 * visually hidden, for screen readers. Colors come from --series-1..5; text uses the t-* classes.
 * Registers window.DeckCharts[type]. Must load before deck.js. */
(function () {
  'use strict';
  var C = window.DeckCharts = window.DeckCharts || {};
  var NS = 'http://www.w3.org/2000/svg';

  function num(s) { return parseFloat(String(s).replace(/[,%\s]/g, '')); }
  function read(fig) {
    var rows = Array.prototype.slice.call(fig.querySelectorAll('table tr'));
    var head = Array.prototype.slice.call(rows[0].children).map(function (c) { return c.textContent.trim(); });
    var data = rows.slice(1).map(function (r) {
      var cells = Array.prototype.slice.call(r.children).map(function (c) { return c.textContent.trim(); });
      return { cat: cells[0], vals: cells.slice(1).map(num), raw: cells.slice(1) };
    });
    return { series: head.slice(1), data: data };
  }
  function el(svg, tag, a, text) {
    var e = document.createElementNS(NS, tag);
    for (var k in a) e.setAttribute(k, a[k]);
    if (text != null) e.textContent = text;
    svg.appendChild(e);
    return e;
  }
  function nice(max) {
    if (max <= 0) return 1;
    var p = Math.pow(10, Math.floor(Math.log10(max))), m = max / p;
    return (m <= 1 ? 1 : m <= 2 ? 2 : m <= 2.5 ? 2.5 : m <= 5 ? 5 : 10) * p;
  }
  function color(i) { return 'var(--series-' + ((i % 5) + 1) + ')'; }
  function setup(fig, height) {
    var old = fig.querySelector(':scope > svg.chart__svg');
    if (old) old.remove();
    var t = fig.querySelector('table');
    if (t) t.classList.add('chart__data');
    if (fig.dataset.title && !fig.querySelector(':scope > .chart__title')) {
      var cap = document.createElement('p');
      cap.className = 'chart__title';
      var unit = fig.dataset.unit, title = fig.dataset.title;
      cap.textContent = title + (unit && title.toLowerCase().indexOf(unit.toLowerCase()) < 0 ? ' (' + unit + ')' : '');
      fig.insertBefore(cap, fig.firstChild);
    }
    var w = fig.clientWidth || 1000;
    var fs = parseFloat(getComputedStyle(fig).fontSize) || 24;
    var svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('class', 'chart__svg');
    svg.setAttribute('viewBox', '0 0 ' + w + ' ' + height(fs));
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label', fig.dataset.title || 'Chart');
    fig.appendChild(svg);
    return { svg: svg, w: w, h: height(fs), fs: fs };
  }
  function legend(c, series, y) {
    if (series.length < 2) return;
    var x = 0;
    series.forEach(function (s, i) {
      el(c.svg, 'rect', { x: x, y: y - c.fs * 0.7, width: c.fs * 0.7, height: c.fs * 0.7, rx: 3, style: 'fill:' + color(i) });
      var t = el(c.svg, 'text', { x: x + c.fs, y: y, 'class': 't-ink', 'font-size': c.fs * 0.9 }, s);
      x += c.fs * 1.6 + s.length * c.fs * 0.55;
      void t;
    });
  }

  C.bar = function (fig) {                       // horizontal bars, categories down the left
    var d = read(fig), n = d.data.length, k = d.series.length;
    var c = setup(fig, function (fs) { return n * (k * fs * 1.1 + fs * 0.6) + (k > 1 ? fs * 1.8 : 0) + 4; });
    var labelW = Math.min(c.w * 0.32, c.fs * 0.55 * Math.max.apply(null, d.data.map(function (r) { return r.cat.length; })) + c.fs);
    var max = nice(Math.max.apply(null, d.data.map(function (r) { return Math.max.apply(null, r.vals); })));
    var plotW = c.w - labelW - c.fs * 3.5, y = (k > 1 ? c.fs * 1.8 : 0), barH = c.fs * 1.1;
    legend(c, d.series, c.fs);
    d.data.forEach(function (r) {
      el(c.svg, 'text', { x: labelW - c.fs * 0.4, y: y + (k * barH) / 2 + c.fs * 0.32, 'text-anchor': 'end', 'class': 't-ink', 'font-size': c.fs }, r.cat);
      r.vals.forEach(function (v, i) {
        var bw = Math.max(2, plotW * v / max);
        el(c.svg, 'rect', { x: labelW, y: y + i * barH, width: bw, height: barH * 0.82, rx: 3, style: 'fill:' + color(i) });
        el(c.svg, 'text', { x: labelW + bw + c.fs * 0.3, y: y + i * barH + barH * 0.62, 'class': 't-ink', 'font-size': c.fs * 0.9 }, r.raw[i]);
      });
      y += k * barH + c.fs * 0.6;
    });
    el(c.svg, 'line', { x1: labelW, x2: labelW, y1: k > 1 ? c.fs * 1.6 : 0, y2: y - c.fs * 0.4, style: 'stroke:var(--line);stroke-width:2' });
  };

  C.column = function (fig) {                    // vertical bars, categories along the bottom
    var d = read(fig), n = d.data.length, k = d.series.length;
    var c = setup(fig, function (fs) { return fs * 14; });
    var top = (k > 1 ? c.fs * 2 : c.fs * 0.4) + c.fs, bottom = c.h - c.fs * 1.8, plotH = bottom - top;
    var max = nice(Math.max.apply(null, d.data.map(function (r) { return Math.max.apply(null, r.vals); })));
    var slot = c.w / n, barW = Math.min(slot * 0.8 / k, c.fs * 3);
    legend(c, d.series, c.fs);
    el(c.svg, 'line', { x1: 0, x2: c.w, y1: bottom, y2: bottom, style: 'stroke:var(--line);stroke-width:2' });
    d.data.forEach(function (r, j) {
      var x0 = slot * j + (slot - barW * k) / 2;
      r.vals.forEach(function (v, i) {
        var bh = Math.max(2, plotH * v / max), x = x0 + i * barW;
        el(c.svg, 'rect', { x: x, y: bottom - bh, width: barW * 0.9, height: bh, rx: 3, style: 'fill:' + color(i) });
        el(c.svg, 'text', { x: x + barW * 0.45, y: bottom - bh - c.fs * 0.3, 'text-anchor': 'middle', 'class': 't-ink', 'font-size': c.fs * 0.9 }, r.raw[i]);
      });
      el(c.svg, 'text', { x: slot * j + slot / 2, y: bottom + c.fs * 1.2, 'text-anchor': 'middle', 'class': 't-ink', 'font-size': c.fs }, r.cat);
    });
  };

  C.line = function (fig) {
    var d = read(fig), n = d.data.length;
    var c = setup(fig, function (fs) { return fs * 14; });
    var top = (d.series.length > 1 ? c.fs * 2 : c.fs * 0.4) + c.fs, bottom = c.h - c.fs * 1.8, plotH = bottom - top;
    var all = []; d.data.forEach(function (r) { all = all.concat(r.vals); });
    var max = nice(Math.max.apply(null, all)), pad = c.fs * 1.5, step = (c.w - 2 * pad) / Math.max(1, n - 1);
    legend(c, d.series, c.fs);
    el(c.svg, 'line', { x1: 0, x2: c.w, y1: bottom, y2: bottom, style: 'stroke:var(--line);stroke-width:2' });
    d.series.forEach(function (_, i) {
      var pts = d.data.map(function (r, j) { return [pad + j * step, bottom - plotH * r.vals[i] / max]; });
      el(c.svg, 'polyline', { points: pts.map(function (p) { return p.join(','); }).join(' '), style: 'fill:none;stroke:' + color(i) + ';stroke-width:5;stroke-linejoin:round' });
      pts.forEach(function (p, j) {
        el(c.svg, 'circle', { cx: p[0], cy: p[1], r: c.fs * 0.25, style: 'fill:' + color(i) });
        if (d.series.length === 1 || j === n - 1) {
          el(c.svg, 'text', { x: p[0], y: p[1] - c.fs * 0.5, 'text-anchor': 'middle', 'class': 't-ink', 'font-size': c.fs * 0.9 }, d.data[j].raw[i]);
        }
      });
    });
    d.data.forEach(function (r, j) {
      el(c.svg, 'text', { x: pad + j * step, y: bottom + c.fs * 1.2, 'text-anchor': 'middle', 'class': 't-ink', 'font-size': c.fs }, r.cat);
    });
  };
})();
