/* Before and after (2026-09-28; plays by itself since 2026-11-26). Drives every .ba figure (site_chrome.before_after).
   The figure no longer pins and no longer follows the scroll: on a phone the reader had to scroll a long, careful
   stretch to see the after. Now, once a quarter of the figure is on screen (at once for a hero already on screen when
   the page opens), the after is brushed over the before by itself, in about 2.2 seconds, once. Then a handle appears
   on the brush's edge: drag it (or the image sideways, or use the arrow keys on it) to compare the two again. The two
   images of a pair are pixel-aligned and differ only where the artwork hangs, so the play crosses just that stretch
   of wall (data-art). Only custom properties change (--p and --pr the progress, --e and --er the brush's edge from
   the left and from the right in stage widths, --hx and --hxr the handle's place); the stylesheet turns them into
   transforms. With reduced motion nothing plays: the after shows at once and the handle works. No library. */
(function () {
  var figs = Array.prototype.slice.call(document.querySelectorAll('.ba'));
  if (!figs.length || !window.requestAnimationFrame) { return; }
  var motion = window.matchMedia ? matchMedia('(prefers-reduced-motion: reduce)') : null;
  var Z = 0.3;            /* the brush's soft edge, in stage widths (the wipe layer is 1.3 stage widths wide) */
  var M = 0.03;           /* a little wall on either side of the artwork, for its frame and shadow */
  var DUR = 2200;         /* the play, in ms */
  var HOLD = 300;         /* the before stays a moment first, so the reader sees what changes */
  var n = 0;
  /* the handle is made here, not in the page: without this script there is nothing to drag. Its name in both
     languages, as everywhere on the site (data-l twins, the stylesheet shows the active one). */
  var LABEL = ['Drag to compare the space before and after', '\u05d2\u05e8\u05e8\u05d5 \u05db\u05d3\u05d9 \u05dc\u05d4\u05e9\u05d5\u05d5\u05ea \u05d0\u05ea \u05d4\u05d7\u05dc\u05dc \u05dc\u05e4\u05e0\u05d9 \u05d5\u05d0\u05d7\u05e8\u05d9'];
  function makeHandle(stage) {
    var h = document.createElement('div');
    h.className = 'ba-handle';
    h.setAttribute('role', 'slider');
    h.setAttribute('tabindex', '0');
    h.setAttribute('aria-orientation', 'horizontal');
    h.setAttribute('aria-valuemin', '0');
    h.setAttribute('aria-valuemax', '100');
    n += 1;
    var g = document.createElement('span'); g.className = 'ba-grip'; h.appendChild(g);
    var l = document.createElement('span'); l.className = 'vh'; l.id = 'ba-lbl-' + n;
    var en = document.createElement('span'); en.setAttribute('data-l', 'en'); en.setAttribute('lang', 'en'); en.textContent = LABEL[0];
    var he = document.createElement('span'); he.setAttribute('data-l', 'he'); he.setAttribute('lang', 'he'); he.setAttribute('dir', 'rtl'); he.textContent = LABEL[1];
    l.appendChild(en); l.appendChild(he); h.appendChild(l);
    h.setAttribute('aria-labelledby', l.id);
    stage.appendChild(h);
    return h;
  }
  var items = figs.map(function (f) {
    var a = (f.getAttribute('data-art') || '0 1 0.5 3 2').split(' ').map(Number);
    return { el: f, stage: f.querySelector('.ba-stage'), handle: makeHandle(f.querySelector('.ba-stage')),
             after: f.querySelector('.ba-after img'), x0: a[0], x1: a[1], fx: a[2], ar: a[3] / a[4],
             p: 0, x: null, played: false, playing: false, span: [0, 1], spanR: [0, 1] };
  });

  function still() { return !!(motion && motion.matches); }
  function clamp(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }
  function ease(t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; }
  function rtl() { return document.body.classList.contains('lang-he'); }

  function measure(it) {
    /* the artwork's edges in stage widths, after object-fit: cover and object-position crop the image */
    var sw = it.stage.offsetWidth, sh = it.stage.offsetHeight || 1;
    var vf = Math.min(1, (sw / sh) / it.ar), crop = it.fx * (1 - vf);
    var l = (it.x0 - crop) / vf, r = (it.x1 - crop) / vf;
    it.span = [Math.max(l - M - Z, -Z), Math.min(r + M, 1)];
    it.spanR = [Math.max((1 - r) - M - Z, -Z), Math.min((1 - l) + M, 1)];
    paint(it);
  }

  /* Two ways to say where the brush is: it.p, the play's progress across the artwork's wall, or it.x, where the
     reader put the handle (0 the stage's left edge, 1 its right). The brush's feathered edge always holds the handle. */
  function paint(it) {
    var e, er, p, pr;
    if (it.x === null) {
      p = pr = it.p;
      e = it.span[0] + p * (it.span[1] - it.span[0]);
      er = it.spanR[0] + p * (it.spanR[1] - it.spanR[0]);
    } else {
      e = -Z + it.x * (1 + Z);
      er = -Z + (1 - it.x) * (1 + Z);
      p = clamp((e - it.span[0]) / Math.max(0.001, it.span[1] - it.span[0]));
      pr = clamp((er - it.spanR[0]) / Math.max(0.001, it.spanR[1] - it.spanR[0]));
    }
    var hx = clamp((e + Z) / (1 + Z)), hxr = clamp(1 - (er + Z) / (1 + Z));
    var st = it.el.style;
    st.setProperty('--p', p.toFixed(3));
    st.setProperty('--pr', pr.toFixed(3));
    st.setProperty('--e', e.toFixed(4));
    st.setProperty('--er', er.toFixed(4));
    st.setProperty('--hx', hx.toFixed(4));
    st.setProperty('--hxr', hxr.toFixed(4));
    it.hxNow = rtl() ? hxr : hx;
    if (it.handle) { it.handle.setAttribute('aria-valuenow', String(Math.round(it.hxNow * 100))); }
  }

  function ready(it) {
    it.played = true;
    it.el.classList.add('ba-ready');
  }

  function play(it) {
    if (it.played || it.playing) { return; }
    if (still()) { it.p = 1; paint(it); ready(it); return; }
    it.playing = true;
    var go = function () {
      setTimeout(function () {
        var t0 = null;
        function frame(now) {
          if (!it.playing) { return; }                 /* the reader took the handle */
          if (t0 === null) { t0 = now; }
          var t = clamp((now - t0) / DUR);
          it.p = ease(t);
          paint(it);
          if (t < 1) { requestAnimationFrame(frame); } else { it.playing = false; ready(it); }
        }
        requestAnimationFrame(frame);
      }, HOLD);
    };
    /* never brush in an after that has not arrived: wait for it (a broken image plays anyway) */
    var img = it.after;
    if (!img || (img.complete && img.naturalWidth)) { go(); return; }
    var once = false;
    var start = function () { if (!once) { once = true; go(); } };
    img.addEventListener('load', start);
    img.addEventListener('error', start);
    if (img.loading === 'lazy') { img.loading = 'eager'; }
  }

  /* the handle: a pointer drag on it or sideways across the image, the arrow keys on it */
  function bind(it) {
    var drag = null;
    function at(cx) { var r = it.stage.getBoundingClientRect(); return clamp((cx - r.left) / Math.max(1, r.width)); }
    function take(x) { it.playing = false; if (!it.played) { ready(it); } it.x = x; paint(it); }
    it.stage.addEventListener('pointerdown', function (ev) {
      if (ev.button !== undefined && ev.button !== 0) { return; }
      var onHandle = !!(ev.target.closest && ev.target.closest('.ba-grip'));   /* the grip: a finger drags at once */
      drag = { id: ev.pointerId, sx: ev.clientX, sy: ev.clientY, on: onHandle || ev.pointerType === 'mouse', moved: false };
      if (drag.on) {
        try { it.stage.setPointerCapture(ev.pointerId); } catch (e) {}
        if (onHandle) { ev.preventDefault(); }
      }
    });
    it.stage.addEventListener('pointermove', function (ev) {
      if (!drag || ev.pointerId !== drag.id) { return; }
      var dx = ev.clientX - drag.sx, dy = ev.clientY - drag.sy;
      if (!drag.on) {
        /* a finger on the image: a sideways drag takes the handle, an upright one stays a page scroll */
        if (Math.abs(dx) < 8 || Math.abs(dx) < Math.abs(dy)) { return; }
        drag.on = true;
        try { it.stage.setPointerCapture(ev.pointerId); } catch (e) {}
      }
      if (Math.abs(dx) > 2) { drag.moved = true; }
      if (drag.moved) { take(at(ev.clientX)); }
    });
    function end(ev) {
      if (!drag || ev.pointerId !== drag.id) { return; }
      /* a mouse click on the image moves the handle there */
      if (ev.type === 'pointerup' && drag.on && !drag.moved && ev.pointerType === 'mouse') { take(at(ev.clientX)); }
      drag = null;
    }
    it.stage.addEventListener('pointerup', end);
    it.stage.addEventListener('pointercancel', end);
    if (it.handle) {
      it.handle.addEventListener('keydown', function (ev) {
        var k = ev.key, cur = it.x === null ? (it.hxNow || 0) : it.x;
        var x = k === 'ArrowLeft' || k === 'ArrowDown' ? cur - 0.05 : k === 'ArrowRight' || k === 'ArrowUp' ? cur + 0.05
              : k === 'Home' ? 0 : k === 'End' ? 1 : null;
        if (x === null) { return; }
        ev.preventDefault();
        take(clamp(x));
      });
    }
  }

  items.forEach(function (it) { bind(it); measure(it); });
  if (still() || !window.IntersectionObserver) {
    items.forEach(play);
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting && en.intersectionRatio >= 0.24) {
          var it = items.filter(function (i) { return i.stage === en.target; })[0];
          if (it) { io.unobserve(en.target); play(it); }
        }
      });
    }, { threshold: [0.25] });
    items.forEach(function (it) { io.observe(it.stage); });
  }

  function remeasure() { requestAnimationFrame(function () { items.forEach(measure); }); }
  window.addEventListener('resize', remeasure);
  if (motion && motion.addEventListener) {
    motion.addEventListener('change', function () {
      if (still()) { items.forEach(function (it) { it.playing = false; it.p = 1; paint(it); ready(it); }); }
    });
  }
  /* images and fonts can resize the stage after the first measure; the language switch moves the handle's side */
  if (window.ResizeObserver) { new ResizeObserver(remeasure).observe(document.body); }
  if (window.MutationObserver) {
    new MutationObserver(function () { items.forEach(paint); }).observe(document.body, { attributes: true, attributeFilter: ['class'] });
  }
})();
