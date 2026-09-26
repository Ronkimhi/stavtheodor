/* Smooth wheel for mouse users (fine pointer, no touch). A mouse notch is 100 px in Chromium and Edge on Windows,
   3 lines in Firefox (Lenis reads that as 50 px) and an accelerated, variable amount on macOS; each notch is
   scaled to 75% and eased over about half a second, so one notch never advances a room by more than a fifth and
   successive notches merge into one glide. Trackpad streams (dense, small deltas) pass through at full size with a
   light lerp, so the trackpad feel stays native. Touch devices never get here. */
(function () {
  if (!window.Lenis || !window.gsap || !window.ScrollTrigger) { return; }
  var fine = !!(window.matchMedia && matchMedia('(pointer: fine)').matches);
  var touch = ('ontouchstart' in window) || !!(window.matchMedia && matchMedia('(pointer: coarse)').matches);
  var reduce = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  if (!fine || touch || reduce) { return; }
  gsap.registerPlugin(ScrollTrigger);
  var NOTCH = { factor: 0.75, lerp: 0.085 }, PAD = { factor: 1, lerp: 0.6 };
  var lastWheel = 0, lenis;
  lenis = new Lenis({
    smoothWheel: true, syncTouch: false, lerp: PAD.lerp, wheelMultiplier: 1, touchMultiplier: 1,
    virtualScroll: function (d) {
      var e = d.event;
      if (!e || e.type !== 'wheel') { return true; }
      var now = performance.now(), gap = now - lastWheel; lastWheel = now;
      var notch = e.deltaMode !== 0 || (Math.abs(e.deltaY) >= 40 && gap > 50);
      var m = notch ? NOTCH : PAD;
      d.deltaY *= m.factor; d.deltaX *= m.factor;
      lenis.options.lerp = m.lerp;
      return true;
    }
  });
  lenis.on('scroll', ScrollTrigger.update);
  gsap.ticker.add(function (t) { lenis.raf(t * 1000); });
  gsap.ticker.lagSmoothing(0);
  /* in-page links (nav, footer, wordmark) glide through Lenis */
  document.addEventListener('click', function (e) {
    var a = e.target && e.target.closest ? e.target.closest('a[href^="#"]') : null;
    if (!a) { return; }
    var id = a.getAttribute('href').slice(1), el = id ? document.getElementById(id) : null;
    if (id && !el) { return; }
    e.preventDefault();
    lenis.scrollTo(el || 0, { offset: 0 });
  });
  window.__theodoraLenis = lenis;
})();
