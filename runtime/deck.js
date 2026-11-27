/* outline-to-deck deck.js: the shared deck runtime, inlined into every deck by assemble-deck.py.
 *
 * Claude writes semantic markup (DECK-BUILD-SPEC.md). This script adds what is the same in every deck:
 * number chips, slide-type labels and icons, callout tabs, "more below" cues, page numbers,
 * backup links, the sources slide, Mermaid rendering with the style's colors, layout geometry,
 * charts, and autofit. Labels and colors come from CSS custom properties, so a style changes
 * them in its CSS file alone.
 *
 * It sets data attributes that tools/check-deck.py reads: data-fit (autofit scale), data-overflow,
 * data-compact (layout compaction steps). window.deckReport() returns them for every slide.
 */
(function () {
  'use strict';

  var ICONS = {
    note: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5v.5"/>',
    tip: '<path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.7.6 1.1 1.4 1.1 2.2h5c0-.8.4-1.6 1.1-2.2A6 6 0 0 0 12 3z"/>',
    remember: '<path d="M6 3h12v18l-6-4-6 4z"/>',
    watchout: '<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.5"/>',
    underthehood: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
    fieldnote: '<rect x="5" y="3" width="14" height="18" rx="1.5"/><path d="M9 8h6M9 12h6M9 16h3M3 7h3M3 12h3M3 17h3"/>',
    compass: '<circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2 5-5 2 2-5z"/>',
    question: '<circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6v.6M12 17v.5"/>',
    check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    x: '<path d="M6 6l12 12M18 6L6 18"/>',
    down: '<path d="M6 9l6 6 6-6"/>'
  };
  var ALIASES = { important: 'remember', warning: 'watchout', caution: 'watchout' };
  var TYPE_ICONS = { 'quick-check': 'question', 'myth-vs-fact': 'x', 'recap': 'check' };
  var FLOOR = 0.62;

  function $(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function cssVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
  function label(name, fallback) {
    var v = cssVar('--label-' + name).replace(/^["']|["']$/g, '');
    return v || fallback || name;
  }
  function icon(name) {
    return '<svg class="ic" viewBox="0 0 24 24" aria-hidden="true">' + (ICONS[name] || '') + '</svg>';
  }
  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }
  function heading(slide) { return slide.querySelector(':scope > h2, :scope > h3, :scope > h4'); }
  function textOf(h) {
    if (!h) return '';
    var c = h.cloneNode(true);
    $('.marker, .num', c).forEach(function (n) { n.remove(); });
    return c.textContent.trim();
  }
  function slideId(s) {
    if (!s.id) s.id = 'n' + (s.dataset.number || Math.random().toString(36).slice(2, 7)).replace(/\./g, '-');
    return s.id;
  }

  /* ------------------------------------------------------------ enhance (before Reveal starts) */
  function enhanceNumbers() {
    $('.reveal .slides section[data-number]').forEach(function (s) {
      var h = heading(s);
      if (!h || h.querySelector('.marker, .num')) return;
      var chip = el('span', s.classList.contains('topic') ? 'marker' : 'num', s.dataset.number);
      h.insertBefore(chip, h.firstChild);
    });
    $('.reveal ol.agenda-list > li[data-number]').forEach(function (li) {
      var a = li.querySelector('a') || li;
      if (!a.querySelector('.marker')) a.insertBefore(el('span', 'marker', li.dataset.number), a.firstChild);
      if (li.classList.contains('self-guided') && !li.querySelector('.sg')) a.appendChild(el('span', 'sg', label('self-guided')));
    });
  }

  function enhanceCallouts() {
    $('.reveal .callout[data-type]').forEach(function (c) {
      if (c.querySelector('.callout__tab')) return;
      var raw = c.dataset.type.toLowerCase();
      var type = ALIASES[raw] || raw;
      c.classList.add('callout--' + type);
      var body = el('div', 'callout__body');
      var lab = el('b', 'callout__label');
      lab.textContent = c.dataset.title || label(raw);
      body.appendChild(lab);
      while (c.firstChild) body.appendChild(c.firstChild);
      c.appendChild(el('div', 'callout__tab', icon(type)));
      c.appendChild(body);
    });
  }

  function enhanceSlideTypes() {
    $('.reveal .slides section[data-type]').forEach(function (s) {
      var t = s.dataset.type, h = heading(s);
      if (TYPE_ICONS[t] && h && !s.querySelector(':scope > .st-label')) {
        var lab = el('p', 'st-label', icon(TYPE_ICONS[t]));
        lab.appendChild(document.createTextNode(label(t)));
        s.insertBefore(lab, h);
      }
      if (t === 'quick-check') {
        $('.answer', s).forEach(function (a) {
          if (!a.querySelector('.answer__label')) a.insertBefore(el('span', 'answer__label', label('answer')), a.firstChild);
          a.classList.add('fragment');
        });
      }
      if (t === 'myth-vs-fact') {
        $('.myth', s).forEach(function (m) { if (!m.querySelector('.ic')) m.insertAdjacentHTML('afterbegin', icon('x')); });
        $('.fact', s).forEach(function (f) {
          if (!f.querySelector('.ic')) f.insertAdjacentHTML('afterbegin', icon('check'));
          f.classList.add('fragment');
        });
      }
      if (t === 'recap') {
        $('ul.checks > li', s).forEach(function (li) { if (!li.querySelector('.ic')) li.insertAdjacentHTML('afterbegin', icon('check')); });
        if (!s.querySelector('.next')) {
          var next = nextSectionTitle(s);
          if (next) s.appendChild(el('p', 'next chrome', label('recap-next') + ' ' + next));
        }
      }
      if (t === 'try-it-yourself') {
        if (!s.querySelector(':scope > .tiy')) {
          var b = el('div', 'tiy', icon('compass'));
          b.appendChild(document.createTextNode(label('try-it-yourself')));
          s.insertBefore(b, s.firstChild);
        }
        $('.outcome', s).forEach(function (o) {
          if (!o.querySelector('.outcome__label')) o.insertBefore(el('span', 'outcome__label', label('outcome')), o.firstChild);
        });
      }
    });
  }

  function nextSectionTitle(slide) {
    var stack = slide.closest('.slides > section');
    var items = $('.reveal ol.agenda-list > li');
    var ids = items.map(function (li) { var a = li.querySelector('a'); return a ? (a.getAttribute('href') || '').replace('#/', '') : ''; });
    var i = stack ? ids.indexOf(stack.id) : -1;
    if (i < 0 || i + 1 >= items.length) return '';
    var a = items[i + 1].querySelector('a');
    return textOf(a);
  }

  function enhanceCues() {
    $('.reveal .slides > section').forEach(function (stack) {
      if (stack.id === 'appendix') return;
      var kids = $(':scope > section', stack);
      if (kids.length > 1 && !kids[0].querySelector(':scope > .more')) {
        var cue = el('div', 'more chrome', icon('down'));
        cue.appendChild(document.createTextNode(label('more')));
        kids[0].appendChild(cue);
      }
    });
  }

  function enhanceBackups() {
    $('.reveal section[data-backup-for]').forEach(function (b) {
      b.setAttribute('data-visibility', 'uncounted');
      var parent = document.querySelector('.reveal .slides section[data-number="' + b.dataset.backupFor + '"]');
      if (!parent) return;
      var n = $(':scope > .backup-link', parent).length;
      var link = el('a', 'backup-link chrome');
      link.href = '#/' + slideId(b);
      link.textContent = label('backup') + ' ' + textOf(heading(b));
      link.style.bottom = (48 + 22 * n) + 'px';
      parent.appendChild(link);
      if (!b.querySelector(':scope > .back-link')) {
        var back = el('a', 'back-link chrome');
        back.href = '#/' + slideId(parent);
        back.textContent = label('back');
        b.appendChild(back);
      }
    });
    $('.reveal #appendix section').forEach(function (s) { s.setAttribute('data-visibility', 'uncounted'); });
  }

  function enhanceSources() {
    var target = document.querySelector('.reveal section.sources[data-auto]');
    if (!target || target.querySelector('.sources-list')) return;
    var groups = [], seen = {};
    $('.reveal .slides > section').forEach(function (stack) {
      if (stack === target || stack.id === 'appendix') return;
      var title = textOf(stack.querySelector('section.topic > h2, :scope > h2')) || '';
      var links = [];
      $('footer a[href]', stack).forEach(function (a) {
        if (seen[a.href]) return;
        seen[a.href] = 1;
        links.push('<li><a href="' + a.href + '">' + a.textContent + '</a></li>');
      });
      if (links.length) groups.push('<h4>' + title + '</h4><ul>' + links.join('') + '</ul>');
    });
    if (!target.querySelector('h2')) target.appendChild(el('h2', '', 'Sources'));
    target.appendChild(el('div', 'sources-list', groups.join('')));
  }

  function enhanceBuild() {
    var deckDefault = (document.querySelector('.reveal').dataset.build || 'off') === 'on';
    $('.reveal .layout').forEach(function (lay) {
      var on = lay.hasAttribute('data-build') ? lay.dataset.build !== 'off' : deckDefault;
      if (on) $(':scope > .layout__items > .layout__item', lay).forEach(function (it) { it.classList.add('fragment'); });
    });
  }

  function pageNumbers() {
    var counted = $('.reveal .slides section').filter(function (s) {
      return !s.querySelector(':scope > section') && s.id !== 'title' && s.getAttribute('data-visibility') !== 'uncounted';
    });
    counted.forEach(function (s, i) {
      if (!s.querySelector(':scope > .pgnum')) s.appendChild(el('div', 'pgnum chrome', (i + 1) + ' / ' + counted.length));
    });
  }

  /* ------------------------------------------------------------ layouts and charts (extended in M3/M4) */
  var Layouts = window.DeckLayouts = window.DeckLayouts || {};   // name -> { render(el), compact(el, step) -> bool }
  var Charts = window.DeckCharts = window.DeckCharts || {};      // type -> render(figure)

  function renderLayouts(root) {
    $('.layout[data-layout]', root).forEach(function (lay) {
      var impl = Layouts[lay.dataset.layout];
      if (impl && impl.render && !lay.dataset.rendered) { impl.render(lay); lay.dataset.rendered = '1'; }
    });
    $('figure.chart[data-type]', root).forEach(function (fig) {
      var impl = Charts[fig.dataset.type];
      if (impl && !fig.dataset.rendered) { impl(fig); fig.dataset.rendered = '1'; }
    });
  }

  /* ------------------------------------------------------------ fit */
  var CHROME = ':scope > *:not(footer):not(aside):not(.pgnum):not(.more):not(.tiy):not(.chrome)';

  function tooTall(s) {
    if (s.scrollHeight > s.clientHeight + 2) return true;
    var ft = s.querySelector(':scope > footer');
    var limit = ft ? ft.offsetTop - 6 : s.clientHeight - 64;
    var kids = s.querySelectorAll(CHROME);
    for (var i = 0; i < kids.length; i++) { if (kids[i].offsetTop + kids[i].offsetHeight > limit) return true; }
    return false;
  }

  function fitSlide(s) {
    if (!s || s.querySelector(':scope > section')) return;
    s.style.fontSize = '';
    s.removeAttribute('data-fit');
    s.removeAttribute('data-overflow');
    // 1. let layouts compact themselves before the whole slide shrinks
    var steps = [];
    $('.layout[data-layout]', s).forEach(function (lay) {
      var impl = Layouts[lay.dataset.layout];
      if (!impl || !impl.compact) return;
      for (var step = 1; step <= 3 && tooTall(s); step++) {
        if (impl.compact(lay, step)) steps.push(lay.dataset.layout + ':' + step); else break;
      }
    });
    if (steps.length) s.dataset.compact = steps.join(' ');
    // 2. shrink text down to the floor
    var f = 1;
    while (tooTall(s) && f > FLOOR + 0.001) { f = Math.max(FLOOR, f - 0.03); s.style.fontSize = f + 'em'; }
    if (f < 1) s.dataset.fit = f.toFixed(2);
    if (tooTall(s)) s.dataset.overflow = '1';
  }

  /* ------------------------------------------------------------ Mermaid */
  var mermaidReady = false;
  function setupMermaid() {
    if (!window.mermaid || mermaidReady) return;
    mermaidReady = true;
    var look = cssVar('--mermaid-look').replace(/["']/g, '') || 'classic';
    window.mermaid.initialize({
      startOnLoad: false, securityLevel: 'strict', theme: 'base', look: look, layout: 'dagre',
      flowchart: { curve: 'basis', htmlLabels: true, useMaxWidth: true, nodeSpacing: 34, rankSpacing: 60, padding: 14 },
      themeVariables: {
        fontFamily: cssVar('--font-body'), fontSize: '20px',
        primaryColor: cssVar('--surface'), primaryBorderColor: cssVar('--mermaid-border') || cssVar('--accent'),
        primaryTextColor: cssVar('--ink'), lineColor: cssVar('--connector'), edgeLabelBackground: cssVar('--surface')
      }
    });
  }
  function classDefs() {
    var sw = cssVar('--mermaid-stroke-width');
    var lines = [
      'classDef key fill:' + cssVar('--emphasis') + ',stroke:' + (cssVar('--mermaid-border') || cssVar('--emphasis')) + ',color:' + cssVar('--on-emphasis'),
      'classDef good fill:' + cssVar('--callout-fieldnote-tint') + ',stroke:' + cssVar('--callout-fieldnote') + ',color:' + cssVar('--ink'),
      'classDef warn fill:' + cssVar('--callout-watchout-tint') + ',stroke:' + cssVar('--callout-watchout') + ',color:' + cssVar('--ink')
    ];
    if (sw) lines.push('classDef default stroke-width:' + sw);
    return '\n' + lines.join('\n') + '\n';
  }
  function renderDiagrams(slide) {
    if (!window.mermaid || !slide) return Promise.resolve();
    if (slide._diagrams) return slide._diagrams;          // a render is already running or done: share it
    var nodes = $('pre.mermaid:not([data-processed])', slide);
    if (!nodes.length) return Promise.resolve();
    setupMermaid();
    nodes.forEach(function (n) {
      if (!n.dataset.styled && /^\s*(flowchart|graph)\b/.test(n.textContent)) { n.textContent += classDefs(); n.dataset.styled = '1'; }
    });
    var fonts = document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve();
    slide._diagrams = fonts.then(function () { return window.mermaid.run({ nodes: nodes }); })
      .catch(function (err) { console.error('Mermaid:', err); })
      .then(function () { fitSlide(slide); });
    return slide._diagrams;
  }

  /* ------------------------------------------------------------ start */
  function show(slide) { renderLayouts(slide); fitSlide(slide); return renderDiagrams(slide); }

  setupMermaid();      // at once: Mermaid otherwise auto-renders every diagram on load, in hidden slides
  enhanceNumbers();
  enhanceCallouts();
  enhanceSlideTypes();
  enhanceCues();
  enhanceBackups();
  enhanceSources();
  enhanceBuild();
  pageNumbers();

  window.deckReport = function () {
    return $('.reveal .slides section').filter(function (s) { return !s.querySelector(':scope > section'); }).map(function (s) {
      return { id: s.id, number: s.dataset.number || null, fit: s.dataset.fit ? parseFloat(s.dataset.fit) : 1,
               overflow: !!s.dataset.overflow, compact: s.dataset.compact || '' };
    });
  };
  window.deckShow = show;   // used by check-deck.py to render and fit a slide on demand

  Reveal.initialize({
    width: 1280, height: 720, margin: 0.04, minScale: 0.2, maxScale: 1.6,
    center: false, hash: true, controls: true, progress: true,
    slideNumber: false, transition: 'fade', transitionSpeed: 'fast',
    plugins: window.RevealNotes ? [window.RevealNotes] : []
  });
  Reveal.on('ready', function (e) { show(e.currentSlide); });
  Reveal.on('slidechanged', function (e) { show(e.currentSlide); });
  window.addEventListener('resize', function () { fitSlide(Reveal.getCurrentSlide()); });
})();
