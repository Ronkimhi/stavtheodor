/* The phone opening, v2 (2026-11-26, the phone default): "the room is already there, the brush paints the art".
   Runs only where the inline boot in templates/home.html (region phone_open) set html.open2 and
   window.THEODORA_PHONE: its phone test PHONE_MQ (a coarse pointer, a portrait screen as FIT_BELOW in
   js/home-opening.js, at most 820 px wide), unless ?open=1 asks for the old opening.

   The before photo and line 1 are real HTML in #ph-stage, painted without any script. This file waits for
   three things: the after photo decoded, its own WebGL ready, and line 1 readable for READ_MS. Then it plays
   the segment of the desktop entrance from 3.00 to 5.86 (js/home-opening.js startEntrance): line 1 fades, the
   wall stroke and the bloom paint the after photo onto the wall with the same brush, seeds and easing, line 2
   comes in, the nav appears and the page is free. The canvas sits over the before <img> with a transparent
   ground and draws only after pixels, alpha = coverage, so every before pixel on screen is the real photo.
   When the wet band has dried the canvas hands over to the real after <img>, at full device resolution.
   The house brush (layer A, the five passes) does not run here.

   Once both photos of the first room are in, the next room's two photos load one after the other (as loadNext
   in js/home-opening.js). Every photo this file loads is handed to js/home-opening.js in THEODORA_PHONE.wait
   (name -> a promise of a decoded image, or null if it failed), so the full opening never fetches them again.
   Afterwards js/home-opening.js starts on idle (THEODORA_PHONE.boot, set by its first lines) in its
   finished state (THEODORA_PHONE.skip), loads the later rooms, and sets the stage's opacity from its own scroll
   progress: the sharp photo stays on top of its canvas until the hero's cross-fade to the next room begins.

   Failure paths. No WebGL, reduced motion or an error: a plain 0.6 s cross-fade. The after photo fails, or is
   not in WATCHDOG ms after this file runs: the before photo stays, with no caption, line 1 fades and the page is
   handed over with THEODORA_PHONE.noAfter (js/home-opening.js then keeps the before room too). Escape skips; a
   scroll before the stroke starts jumps to the end state; the page is held still only while the stroke runs
   (about 2.5 s), and never longer than LOCK_MAX. */
(function () {
  var P = window.THEODORA_PHONE;
  if (!P || P.started) { return; }
  P.started = true;
  P.wait = P.wait || {};
  var READ_MS = 900;       /* line 1 is readable at least this long before the stroke starts */
  var RATE = 1.1;          /* the segment plays at 1.1x the unslowed timeline (2.53 s to unlock); the desktop runs at 1/1.3 */
  var WATCHDOG = 8000;     /* as in js/home-opening.js: an after photo not in by then counts as failed */
  var LOCK_MAX = 4000;     /* the stroke holds the page about 2.5 s; whatever happens, never longer than this */
  var SEED = 3.7;          /* PAIRS[0].seed in js/home-opening.js (room p3) */
  var LAND = { w: 1800, h: 1200, rect: [0.554, 0.139, 0.709, 0.515], fx: 0.63, fy: 0.40, from: 'right' }; /* PAIRS[0].land */
  var FIRST = ['pairs/p3_before.webp', 'pairs/p3_after.webp'];  /* PAIRS[0]: the 1800 px files (a coarse pointer never takes HI_MQ) */
  var NEXT = ['pairs/p4_before.webp', 'pairs/p4_after.webp'];   /* PAIRS[1], loaded as loadNext does */
  var R = document.documentElement, dbg = P.dbg = { state: 'boot' };
  var clamp = function (x, a, b) { return Math.min(b, Math.max(a, x)); };
  var now = function () { return performance.now(); };

  function whenParsed(fn) { if (document.getElementById('page') || document.readyState !== 'loading') { fn(); } else { setTimeout(function () { whenParsed(fn); }, 25); } }
  whenParsed(function () { try { init(); } catch (e) { dbg.err = String(e); if (P.fail) { P.fail(); } } });

  function init() {
    var body = document.body, $ = function (s) { return document.querySelector(s); };
    var stage = $('#ph-stage'), room = stage && stage.querySelector('.ph-room');
    var imgB = room && room.querySelector('.ph-b'), imgA = room && room.querySelector('.ph-a'), scrimEl = stage && stage.querySelector('.ph-scrim');
    var line1 = $('#l1'), line2 = $('#l2'), cap = $('#cap'), cue = $('.cue');
    if (!stage || !imgA || !imgB || !line1 || !line2) { if (P.fail) { P.fail(); } return; }
    var glMode = body.classList.contains('gl');
    var reduce = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
    var state = 'wait', booted = false, afterOk = false, afterDone = false, beforeOk = false;
    dbg.state = state;
    function ok(im) { return !!(im && im.complete && im.naturalWidth); }
    /* the after photo is known to be missing: it failed, or the watchdog gave up on it */
    function noArt() { return afterDone && !afterOk; }

    /* ---- line 1 and the Write link sit under the room's measured bottom (css/theme.css, --ph-rb) ---- */
    function pin() {
      if ((window.pageYOffset || 0) > 1 || getComputedStyle(stage).position !== 'fixed') { return; }
      var rb = room.getBoundingClientRect().bottom;
      if (rb > 0) { R.style.setProperty('--ph-rb', rb.toFixed(2) + 'px'); R.classList.add('ph-rb'); dbg.rb = rb; }
    }
    pin();
    window.addEventListener('load', pin);

    /* ---- the end of the opening, whichever way it comes ---- */
    function showEnd(d, missing) {
      if (!missing) { whenLoaded(imgA, function () { if (!P.noAfter) { fade(imgA, 1, d); capOn(); } }); }
      fade(line1, 0, Math.min(d, 0.35)); fade(line2, 0, Math.min(d, 0.35)); scrim(0);
      if (cue) { fade(cue, 1, 0.5); }
      body.classList.remove('ph-hold'); lock(false);
    }
    /* a jump before the after photo has arrived: it fades in (with its caption) when it lands, never pops */
    function whenLoaded(im, fn) { if (ok(im)) { fn(); } else { im.addEventListener('load', fn, { once: true }); } }
    function fade(el, op, d) {
      if (!el) { return; }
      el.style.transition = d ? 'opacity ' + d + 's ease' : 'none';
      el.style.opacity = op;
    }
    /* the caption names the art: only ever with the after photo on screen */
    function capOn() { if (!cap || !ok(imgA) || P.noAfter) { return; } cap.setAttribute('data-show', 'p3'); fade(cap, 1, 0.2); }
    function scrim(v) { if (scrimEl) { scrimEl.style.transition = 'none'; scrimEl.style.opacity = v; } }
    function finish(d, quick, missing) {
      if (state === 'end') { return; }
      state = dbg.state = 'end'; P.done = true; dbg.end = now();
      if (missing) { P.noAfter = dbg.noAfter = true; }
      clearTimeout(watchdog); clearTimeout(safety);
      stopTimeline(); dropGl();
      showEnd(d, missing);
      /* hand the opacities back to js/home-opening.js (GSAP) without a CSS transition in the way */
      setTimeout(function () { [cap, cue, line1, line2].forEach(function (el) { if (el) { el.style.transition = ''; } }); }, 700);
      release(!!quick);
    }
    /* hand js/home-opening.js the page: it boots already finished. On idle after a played entrance, at once after a jump. */
    function release(quick) {
      if (booted) { return; } booted = true;
      P.hold = false; P.skip = true;
      var go = function () { window.removeEventListener('scroll', go); if (dbg.boot) { return; } dbg.boot = now(); if (P.boot) { var b = P.boot; P.boot = null; b(); } };
      if (quick || !window.requestIdleCallback) { setTimeout(go, quick ? 0 : 200); } else { requestIdleCallback(go, { timeout: 1200 }); }
      /* a visitor who scrolls before that moment gets the full opening at once, so the rooms follow the scroll */
      window.addEventListener('scroll', go, { passive: true });
    }

    /* ---- the page is held still only while the stroke runs ---- */
    var KEYS = { ' ': 1, PageUp: 1, PageDown: 1, Home: 1, End: 1, ArrowUp: 1, ArrowDown: 1 }, locked = false, lockT = 0;
    function hold(e) { if (locked && (e.type !== 'keydown' || KEYS[e.key])) { e.preventDefault(); } }
    ['wheel', 'touchmove', 'keydown'].forEach(function (t) { window.addEventListener(t, hold, { passive: false }); });
    function lock(on) {
      locked = on; dbg.locked = on; clearTimeout(lockT);
      if (on) { lockT = setTimeout(function () { dbg.lockMax = true; lock(false); body.classList.remove('ph-hold'); }, LOCK_MAX); }
    }
    window.addEventListener('keydown', function (e) { if (e.key === 'Escape' && state !== 'end') { finish(0.3, true, noArt()); } });
    /* a visitor who scrolls before the stroke starts gets the end state at once */
    window.addEventListener('scroll', function () { if (state === 'wait' && (window.pageYOffset || 0) > 2) { dbg.jumped = true; finish(0.3, true, noArt()); } }, { passive: true });
    window.addEventListener('resize', function () {
      pin();
      if (state !== 'end' && window.matchMedia && !matchMedia('(max-aspect-ratio: 9/10)').matches) { dbg.rotated = true; finish(0, true, noArt()); }
    });
    var safety = 0, watchdog = 0;
    if ((window.pageYOffset || 0) > 2) { dbg.jumped = true; finish(0, true, false); }

    /* ---- no WebGL in this layout, reduced motion: the plain cross-fade ---- */
    var gl = null, canvas = null, L = {}, tex = null, U = { bh: 0, bw: 1, bloom: 0 }, raf = 0, t0gl = now(), V = derive(LAND);
    if (state === 'wait' && glMode && !reduce) { try { gl = setupGl(); } catch (e) { gl = null; dbg.err = String(e).slice(0, 300); } }
    /* the full opening will run (WebGL here, no reduced motion): only then is the next room ever drawn */
    var glOk = !!gl;
    function crossfade() { if (state !== 'wait') { return; } finish(0.6); }

    /* ---- the gate: after photo decoded, WebGL ready, line 1 read ---- */
    var decoded = (imgA.decode ? imgA.decode() : new Promise(function (res, rej) { whenLoaded(imgA, res); imgA.addEventListener('error', rej, { once: true }); }))
      .catch(function () { return ok(imgA) ? null : Promise.reject(new Error('after photo')); })
      .then(function () { afterOk = dbg.after = afterDone = true; dbg.afterAt = now(); return imgA; },
            function (e) { afterDone = true; throw e; });
    /* the before photo and line 1 are both on screen for READ_MS: counted from the later of the first contentful
       paint (line 1) and the before photo's first frame, so a slow photo still gets its moment before the brush */
    var beforeShown = (imgB.decode ? imgB.decode() : Promise.resolve()).then(function () { beforeOk = true; }, function () { beforeOk = ok(imgB); })
      .then(function () { dbg.beforeOk = beforeOk; return beforeOk ? imgB : null; });
    /* js/home-opening.js gets its own decoded copies, from the memory cache (no new request): the stage's <img> elements
       follow their <source> media, so a turn to landscape empties them, and a texture must never be read from one */
    function copy(im) {
      if (!im) { return null; }
      return new Promise(function (res) {
        var c = new Image(), done = function () { res(c.naturalWidth ? c : null); };
        c.onload = function () { if (c.decode) { c.decode().then(done, done); } else { done(); } }; c.onerror = function () { res(null); };
        c.src = im.currentSrc || im.src;
      });
    }
    P.wait[FIRST[0]] = beforeShown.then(copy);
    P.wait[FIRST[1]] = decoded.then(copy, function () { return null; });
    var read = beforeShown.then(function () { return new Promise(function (res) {
      requestAnimationFrame(function () { requestAnimationFrame(function () {
        var fcp = (performance.getEntriesByName && performance.getEntriesByName('first-contentful-paint')[0]) || null;
        var t1 = Math.max(fcp ? fcp.startTime : 0, dbg.before = now());
        dbg.fcp = fcp ? fcp.startTime : null; setTimeout(res, Math.max(0, READ_MS - (now() - t1)));
      }); });
    }); });
    /* the next room, as loadNext in js/home-opening.js: once both photos of the first room are in, one after the other,
       and only where the full opening will draw it (the static figures never show the next room's before photo) */
    var nextGo = Promise.all([decoded, beforeShown]).then(function (r) { return !!r[1] && glOk; }, function () { return false; });
    var prev = nextGo;
    NEXT.forEach(function (name) {
      var mine = prev.then(function (go) {
        if (!go) { return null; }
        return new Promise(function (res) {
          var im = new Image(); if ('fetchPriority' in im) { im.fetchPriority = 'low'; }
          im.onload = function () { if (im.decode) { im.decode().then(function () { res(im); }, function () { res(im); }); } else { res(im); } };
          im.onerror = function () { res(null); };
          im.src = '/images/home2/' + name;
        });
      });
      /* a first room that never completes: js/home-opening.js loads the next room itself */
      P.wait[name] = nextGo.then(function (go) { return go ? mine : undefined; });
      prev = mine.then(function () { return true; });
    });
    if (state !== 'wait') { return; }
    /* a photo that never comes: the nav and the Write to Stav link appear anyway, the page has been free all along */
    safety = setTimeout(function () { if (state === 'wait') { dbg.timeout = true; body.classList.remove('ph-hold'); } }, 6000);
    /* the watchdog: the after photo not in by now counts as failed (the before room stays, no caption); the after photo
       in but not the before photo: the plain cross-fade to the after photo */
    watchdog = setTimeout(function () {
      if (state !== 'wait') { return; }
      dbg.watchdog = afterOk ? 'before' : 'after';
      if (afterOk) { crossfade(); } else { afterDone = true; finish(0.3, true, true); }
    }, WATCHDOG);
    Promise.all([decoded, read]).then(function () {
      if (state !== 'wait') { return; }
      if (!gl || !beforeOk) { crossfade(); return; }
      try { uploadAfter(); play(); } catch (e) { dbg.err = String(e); dropGl(); crossfade(); }
    }, function () { dbg.err = 'after photo'; if (state === 'wait') { finish(0.3, false, true); } });

    /* ---- WebGL: the wall stroke and the bloom, after pixels only ---- */
    function derive(v) { /* deriveStroke in js/home-opening.js, verbatim in effect */
      var r = v.rect, h = r[3] - r[1], cy = (r[1] + r[3]) / 2, rad = Math.min(0.62 * h, 0.32);
      var x0 = v.from === 'left' ? r[0] - 0.5 * rad : r[2] + 0.5 * rad;
      var x1 = v.from === 'left' ? r[2] + 0.6 * rad : r[0] - 0.6 * rad;
      var o = { b0: [x0, cy + 0.015 * h], b1: [x1, cy - 0.015 * h], rad: rad, bo: [(r[0] + r[2]) / 2, cy], aspect: v.w / v.h, fx: v.fx, fy: v.fy };
      var dx = o.b1[0] - o.b0[0], dy = o.b1[1] - o.b0[1]; o.len = Math.hypot(dx, dy); o.dir = [dx / o.len, dy / o.len];
      return o;
    }
    function setupGl() {
      canvas = document.createElement('canvas');
      canvas.className = 'ph-gl';
      var opts = { alpha: true, premultipliedAlpha: true, antialias: false, depth: false, stencil: false, preserveDrawingBuffer: false };
      var g = canvas.getContext('webgl', opts) || canvas.getContext('experimental-webgl', opts);
      if (!g) { return null; }
      var VS = 'attribute vec2 p; void main(){ gl_Position = vec4(p, 0.0, 1.0); }';
      /* hash, noise, fbm3, coverUV and paintSeg are copied unchanged from the FS in js/home-opening.js */
      var FS = [
        '#ifdef GL_FRAGMENT_PRECISION_HIGH', 'precision highp float;', '#else', 'precision mediump float;', '#endif',
        'uniform vec2 uRes; uniform float uTime; uniform sampler2D tAfter; uniform vec2 uFocal; uniform float uImgAspect;',
        'uniform vec2 uB0; uniform vec2 uBD; uniform float uBL; uniform float uBH; uniform float uBW; uniform float uBRad; uniform float uBSeed;',
        'uniform vec2 uBloomO; uniform float uBloomR; uniform vec2 uBloomBias; uniform float uBloomSeed;',
        'float hash(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }',
        'float noise(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f*f*(3.0-2.0*f);',
        '  return mix(mix(hash(i), hash(i+vec2(1.0,0.0)), f.x), mix(hash(i+vec2(0.0,1.0)), hash(i+vec2(1.0,1.0)), f.x), f.y); }',
        'float fbm3(vec2 p){ float v = 0.0; float a = 0.5; for (int i = 0; i < 3; i++){ v += a*noise(p); p = p*2.03 + vec2(17.1, 9.3); a *= 0.5; } return v; }',
        'vec2 coverUV(vec2 td, float aspect, float ia, vec2 f){',
        '  if (aspect > ia){ float vr = ia/aspect; float v0 = clamp(f.y - 0.5*vr, 0.0, 1.0 - vr); return vec2(td.x, v0 + td.y*vr); }',
        '  float ur = aspect/ia; float u0 = clamp(f.x - 0.5*ur, 0.0, 1.0 - ur); return vec2(u0 + td.x*ur, td.y); }',
        'float paintSeg(vec2 p, vec2 a, vec2 dir, float len, float head, float wf, float rad, float seed, float ragged, float style, inout float wet, inout float wetU, inout float wetB){',
        '  if (head <= 0.0) return 0.0;',
        '  float t = dot(p - a, dir); float hd = min(head, len); float u = clamp(t, 0.0, hd);',
        '  float d = length(p - (a + dir*u));',
        '  if (d > rad*1.35) return 0.0;',
        '  float v = dot(p - a, vec2(-dir.y, dir.x));',
        '  float bristle = noise(vec2(v*90.0 + seed, u*3.0))*0.35;',
        '  float m = 0.0; float edge = rad;',
        '  if (style < 0.5){',
        '    edge = rad*(0.80 + bristle*0.6 + ragged*0.5 + (noise(vec2(u*36.0 + seed, v*5.0)) - 0.5)*0.05);',
        '    m = 1.0 - smoothstep(edge - 0.004, edge + 0.004, d);',
        '    float lead = (noise(vec2(v*120.0 + seed, 5.0)) - 0.5)*0.16 + (noise(vec2(v*420.0 + seed, 9.0)) - 0.5)*0.06;',
        '    float front = hd + lead*rad;',
        '    m *= 1.0 - smoothstep(front - 0.012, front + 0.008, t);',
        '    float streaks = smoothstep(0.30, 0.62, noise(vec2(v*140.0 + seed, u*2.0)));',
        '    m *= mix(1.0, streaks, 0.85*smoothstep(front - 0.22*rad, front - 0.02*rad, t));',
        '    float lines = smoothstep(0.35, 0.60, noise(vec2(v*160.0 + seed, u*1.6)));',
        '    m *= mix(1.0, lines, 0.8*smoothstep(edge - 0.16*rad, edge - 0.02*rad, d));',
        '  } else {',
        '    edge = rad*(0.72 + bristle + ragged + (noise(vec2(u*48.0 + seed, v*6.0)) - 0.5)*0.07);',
        '    m = 1.0 - smoothstep(edge - 0.0035, edge + 0.0035, d);',
        '    float lead = (noise(vec2(v*70.0 + seed, 3.0)) - 0.5)*0.6 + (noise(vec2(v*230.0 + seed, 7.0)) - 0.5)*0.25;',
        '    float front = hd + lead*rad;',
        '    m *= 1.0 - smoothstep(front - 0.02 - ragged*0.2, front + 0.012, t);',
        '  }',
        '  float w = m * (1.0 - smoothstep(0.0, 0.10, hd - u)) * wf;',
        '  if (w > wet){ wet = w; wetU = u; wetB = bristle; }',
        '  return m; }',
        /* the main of js/home-opening.js without layer A, the scrim (CSS, .ph-scrim), the cross-fade and the fade:
           the room fills this canvas, so td runs 0..1 across it; the output is the after photo, premultiplied, at
           alpha = coverage, with the wet band on it exactly as there */
        'void main(){',
        '  vec2 fragN = gl_FragCoord.xy / uRes; vec2 td = vec2(fragN.x, 1.0 - fragN.y);',
        '  vec2 uv = coverUV(td, uRes.x / uRes.y, uImgAspect, uFocal);',
        '  float wet = 0.0; float wetU = 0.0; float wetB = 0.17;',
        '  float ragB = fbm3(uv*14.0 + uBSeed)*0.18;',
        '  float maskB = paintSeg(uv, uB0, uBD, uBL, uBH, uBW, uBRad, uBSeed, ragB, 1.0, wet, wetU, wetB);',
        '  float bloom = 0.0;',
        '  if (uBloomR > 0.0){ vec2 dv = uv - uBloomO; float d = length(dv*vec2(1.0, 0.6)) + max(0.0, dot(dv, uBloomBias));',
        '    d += (fbm3(uv*6.0 + uBloomSeed) - 0.44)*0.25; bloom = 1.0 - smoothstep(uBloomR - 0.02, uBloomR + 0.02, d); }',
        '  float a = max(maskB, bloom);',
        '  if (a <= 0.0){ gl_FragColor = vec4(0.0); return; }',
        '  vec3 col = texture2D(tAfter, uv).rgb;',
        '  wet *= (0.85 + 0.15*noise(vec2(wetU*40.0, uTime*0.4)));',
        '  col += wet*0.08*vec3(1.0, 0.97, 0.92);',
        '  col *= 1.0 + (wetB - 0.17)*0.16*wet;',
        '  gl_FragColor = vec4(clamp(col, 0.0, 1.0)*a, a); }'
      ].join('\n');
      var sh = function (type, src) { var s = g.createShader(type); g.shaderSource(s, src); g.compileShader(s); if (!g.getShaderParameter(s, g.COMPILE_STATUS)) { throw new Error(g.getShaderInfoLog(s)); } return s; };
      var prog = g.createProgram(); g.attachShader(prog, sh(g.VERTEX_SHADER, VS)); g.attachShader(prog, sh(g.FRAGMENT_SHADER, FS)); g.linkProgram(prog);
      if (!g.getProgramParameter(prog, g.LINK_STATUS)) { throw new Error(g.getProgramInfoLog(prog)); }
      g.useProgram(prog);
      var buf = g.createBuffer(); g.bindBuffer(g.ARRAY_BUFFER, buf);
      g.bufferData(g.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), g.STATIC_DRAW);
      var pl = g.getAttribLocation(prog, 'p'); g.enableVertexAttribArray(pl); g.vertexAttribPointer(pl, 2, g.FLOAT, false, 0, 0);
      ['uRes', 'uTime', 'tAfter', 'uFocal', 'uImgAspect', 'uB0', 'uBD', 'uBL', 'uBH', 'uBW', 'uBRad', 'uBSeed', 'uBloomO', 'uBloomR', 'uBloomBias', 'uBloomSeed'].forEach(function (n) { L[n] = g.getUniformLocation(prog, n); });
      g.uniform1i(L.tAfter, 0);
      canvas.addEventListener('webglcontextlost', function (e) { e.preventDefault(); if (state === 'run' && gl) { dbg.err = 'context lost'; dropGl(); finish(0.6); } });
      room.appendChild(canvas);
      return g;
    }
    function sizeCanvas() {
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      var w = Math.max(1, Math.round(room.clientWidth * dpr)), h = Math.max(1, Math.round(room.clientHeight * dpr));
      if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    }
    function uploadAfter() {
      tex = gl.createTexture(); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, imgA); /* the full 1800 px photo, no downscale */
      sizeCanvas();
    }
    function draw() {
      sizeCanvas();
      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
      if (U.bh <= 0 && U.bloom <= 0) { return; }
      gl.uniform2f(L.uRes, canvas.width, canvas.height); gl.uniform1f(L.uTime, (now() - t0gl) / 1000);
      gl.uniform2f(L.uFocal, V.fx, V.fy); gl.uniform1f(L.uImgAspect, V.aspect);
      gl.uniform2f(L.uB0, V.b0[0], V.b0[1]); gl.uniform2f(L.uBD, V.dir[0], V.dir[1]); gl.uniform1f(L.uBL, V.len);
      gl.uniform1f(L.uBH, U.bh * V.len); gl.uniform1f(L.uBW, U.bw); gl.uniform1f(L.uBRad, V.rad); gl.uniform1f(L.uBSeed, SEED);
      gl.uniform2f(L.uBloomO, V.bo[0], V.bo[1]); gl.uniform1f(L.uBloomR, U.bloom); gl.uniform2f(L.uBloomBias, 0, 0); gl.uniform1f(L.uBloomSeed, SEED * 1.7);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    }
    function dropGl() {
      if (raf) { cancelAnimationFrame(raf); raf = 0; }
      if (!gl) { return; }
      var g = gl; gl = null;
      setTimeout(function () { try { var x = g.getExtension('WEBGL_lose_context'); if (x) { x.loseContext(); } } catch (e) {} if (canvas && canvas.parentNode) { canvas.parentNode.removeChild(canvas); } }, 400);
      if (canvas) { canvas.style.transition = 'opacity .3s ease'; canvas.style.opacity = 0; }
    }

    /* ---- the timeline: the desktop's 3.00 to 5.86, in its own units (t - 3.00), at RATE ---- */
    var E = { /* GSAP's power eases: power2 is cubic, power3 quartic */
      p2in: function (t) { return t * t * t; },
      p2out: function (t) { return 1 - Math.pow(1 - t, 3); },
      p2io: function (t) { return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; },
      p3io: function (t) { return t < 0.5 ? 8 * t * t * t * t : 1 - Math.pow(-2 * t + 2, 4) / 2; }
    };
    var steps = [], tStart = 0;
    function tw(at, dur, ease, from, to, set) { steps.push({ at: at, d: dur, e: ease, a: from, b: to, set: set, done: false }); }
    function call(at, fn) { steps.push({ at: at, fn: fn, done: false }); }
    function stopTimeline() { (steps || []).forEach(function (s) { s.done = true; }); }
    function styleOp(el) { return function (v) { el.style.transition = 'none'; el.style.opacity = v; }; }
    function split(el) { /* letters of both languages, as SplitText does for the active one on the desktop */
      var out = [];
      Array.prototype.forEach.call(el.querySelectorAll('[data-l]'), function (span) {
        var txt = span.textContent; span.textContent = '';
        for (var i = 0; i < txt.length; i++) {
          var c = txt.charAt(i);
          if (c === ' ') { span.appendChild(document.createTextNode(' ')); continue; }
          var ch = document.createElement('span'); ch.className = 'ch'; ch.textContent = c;
          ch.style.opacity = 0; ch.style.transform = 'translateY(10px)';
          span.appendChild(ch); out.push({ el: ch, lang: span.getAttribute('data-l'), i: 0 });
        }
      });
      var n = { en: 0, he: 0 }; out.forEach(function (o) { o.i = n[o.lang] = (n[o.lang] || 0) + 1; o.i -= 1; });
      return out;
    }
    function play() {
      state = dbg.state = 'run';
      var chars = split(line2);
      line2.style.opacity = 1;
      lock(true);
      tw(0.00, 0.35, E.p2in, 1, 0, styleOp(line1));
      tw(0.00, 0.35, E.p2in, 1, 0, function (v) { scrim(v); });
      call(0.30, capOn);
      tw(0.30, 1.10, E.p3io, 0, 1, function (v) { U.bh = v; });
      tw(1.40, 1.20, E.p2io, 1, 0, function (v) { U.bw = v; });
      tw(1.20, 1.00, E.p2io, 0, 1.6, function (v) { U.bloom = v; });
      tw(1.20, 0.40, E.p2out, 0, 1, function (v) { scrim(v); });
      chars.forEach(function (c) {
        tw(1.30 + c.i * 0.03, 0.70, E.p2out, 0, 1, function (v) { c.el.style.opacity = v; c.el.style.transform = 'translateY(' + (10 * (1 - v)).toFixed(2) + 'px)'; });
      });
      /* the wet band is dry at 2.60: the after <img> goes under the canvas, the canvas fades out over it */
      call(2.60, function () { fade(imgA, 1, 0); dropGl(); dbg.handoff = now(); });
      tw(2.40, 0.35, E.p2in, 1, 0, styleOp(line2));
      tw(2.40, 0.35, E.p2in, 1, 0, function (v) { scrim(v); });
      call(2.78, function () { body.classList.remove('ph-hold'); lock(false); dbg.free = now(); });
      if (cue) { tw(2.86, 0.50, E.p2out, 0, 1, styleOp(cue)); }
      call(3.36, function () { finish(0); });
      tStart = now(); dbg.t0 = tStart;
      var frame = function () {
        raf = 0;
        try {
          var t = (now() - tStart) / 1000 * RATE;
          for (var i = 0; i < steps.length; i++) {
            var s = steps[i];
            if (s.done || t < s.at) { continue; }
            if (s.fn) { s.done = true; s.fn(); continue; }
            var k = clamp((t - s.at) / s.d, 0, 1);
            s.set(s.a + (s.b - s.a) * s.e(k));
            if (k >= 1) { s.done = true; }
          }
          if (gl) { draw(); }
        } catch (e) { dbg.err = String(e); dropGl(); finish(0.3, true); return; }
        if (state === 'run') { raf = requestAnimationFrame(frame); }
      };
      raf = requestAnimationFrame(frame);
    }
  }
})();
