/* Before and after (2026-09-28). Drives every .ba figure (site_chrome.before_after): the figure pins (CSS sticky,
   css/theme.css Part 3) and, as the reader scrolls, --p runs from 0 to 1 and the after is brushed over the before.
   The reveal starts when the figure is in view (at once for a hero already on screen when the page opens) and ends
   when the pin lets go. The two images of a pair are pixel-aligned and differ only where the artwork hangs, so the
   brush crosses just that stretch of wall (data-art), and every scrolled pixel changes what the reader sees: no dead
   zone. Only custom properties change (--p the progress, --e and --er the brush's edge from the left and from the
   right, in stage widths); the stylesheet turns them into two transforms. With reduced motion the stylesheet shows a still pair and this
   script does nothing. No library. */
(function () {
  var figs = Array.prototype.slice.call(document.querySelectorAll('.ba'));
  if (!figs.length || !window.requestAnimationFrame) { return; }
  var motion = window.matchMedia ? matchMedia('(prefers-reduced-motion: reduce)') : null;
  var NAV = 84;           /* the fixed nav's height: the pinned figure never slides under it */
  var START = 0.62;       /* a figure further down starts when its top reaches 62% of the viewport */
  var Z = 0.3;            /* the brush's soft edge, in stage widths (the wipe layer is 1.3 stage widths wide) */
  var M = 0.03;           /* a little wall on either side of the artwork, for its frame and shadow */
  var items = figs.map(function (f) {
    var a = (f.getAttribute('data-art') || '0 1 0.5 3 2').split(' ').map(Number);
    return { el: f, pin: f.querySelector('.ba-pin'), stage: f.querySelector('.ba-stage'), x0: a[0], x1: a[1], fx: a[2], ar: a[3] / a[4],
             p: -1, top: 0, pinTop: NAV, dist: 0, span: [0, 1], spanR: [0, 1] };
  });
  var queued = false;

  function ease(t) { return t * t * (3 - 2 * t); }

  function measure() {
    var vh = window.innerHeight || document.documentElement.clientHeight;
    var y = window.pageYOffset || document.documentElement.scrollTop || 0;
    items.forEach(function (it) {
      var ph = it.pin.offsetHeight;
      it.pinTop = Math.max(NAV, Math.round((vh - ph) / 2));
      it.el.style.setProperty('--pin-top', it.pinTop + 'px');
      it.dist = Math.max(1, it.el.offsetHeight - ph);   /* the pinned distance: the spacer under the pin (.ba::after) */
      it.top = it.el.getBoundingClientRect().top + y;   /* the figure's place in the document */
      it.start = Math.min(vh * START, it.top);          /* already on screen at the top of the page: start at once */
      /* the artwork's edges in stage widths, after object-fit: cover and object-position crop the image */
      var sw = it.stage.offsetWidth, sh = it.stage.offsetHeight || 1;
      var vf = Math.min(1, (sw / sh) / it.ar), crop = it.fx * (1 - vf);
      var l = (it.x0 - crop) / vf, r = (it.x1 - crop) / vf;
      it.span = [Math.max(l - M - Z, -Z), Math.min(r + M, 1)];
      it.spanR = [Math.max((1 - r) - M - Z, -Z), Math.min((1 - l) + M, 1)];
      it.p = -1;
    });
    update();
  }

  function update() {
    queued = false;
    if (motion && motion.matches) { return; }
    var y = window.pageYOffset || document.documentElement.scrollTop || 0;
    items.forEach(function (it) {
      var r = it.top - y;                                  /* the figure's top in the viewport */
      var end = it.pinTop - it.dist;
      var t = (it.start - r) / Math.max(1, it.start - end);
      t = t < 0 ? 0 : t > 1 ? 1 : t;
      var p = Math.round(ease(t) * 1000) / 1000;
      if (p !== it.p) {
        it.p = p;
        var st = it.el.style;
        st.setProperty('--p', p);
        st.setProperty('--e', (it.span[0] + p * (it.span[1] - it.span[0])).toFixed(4));
        st.setProperty('--er', (it.spanR[0] + p * (it.spanR[1] - it.spanR[0])).toFixed(4));
      }
    });
  }

  function queue() { if (!queued) { queued = true; requestAnimationFrame(update); } }

  window.addEventListener('scroll', queue, { passive: true });
  window.addEventListener('resize', function () { requestAnimationFrame(measure); });
  window.addEventListener('load', measure);
  if (motion && motion.addEventListener) { motion.addEventListener('change', measure); }
  /* images and fonts can move the figure after the first measure */
  if (window.ResizeObserver) { new ResizeObserver(function () { requestAnimationFrame(measure); }).observe(document.body); }
  measure();
})();
