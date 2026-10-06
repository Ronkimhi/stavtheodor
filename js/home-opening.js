/* The opening. Ported from the approved "Same Room" concept: a house brush paints the room out of the
   dark, a wall stroke brushes the art onto the wall, a bloom finishes it, the wet band dries. Then four
   scroll chapters, each the same gesture on another room. Falls back to static figures without WebGL. */
(function () {
  var $ = function (s) { return document.querySelector(s); };
  var clamp = function (x, a, b) { return Math.min(b, Math.max(a, x)); };
  var ss = function (a, b, x) { var t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
  var body = document.body;
  var canvas = $('#gl'), hero = $('#hero'), chain = $('#chain'), intro = $('#intro'), page = $('#page');
  var markIn = $('.mark-in'), cue = $('.cue'), cap = $('#cap'), band = $('.band'), introH1 = $('#intro-h1');
  var line1 = $('#l1'), line2 = $('#l2');
  var SLOW = 1.3; /* the entrance runs at 1/SLOW speed: same order, same easing, 1.3x longer */
  var reduce = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  var forceNoGl = location.hash === '#nogl' || /[?&]nogl=1/.test(location.search);
  var touch = !!((window.matchMedia && matchMedia('(pointer: coarse)').matches) || ('ontouchstart' in window));
  var dbg = window.__theodoraBrush = { mode: 'boot', t0: 0, done: false, touch: touch };

  var tl = null, st = null, glDead = false;
  function goStatic() {
    if (body.classList.contains('static')) { return; }
    glDead = true; dbg.mode = 'static';
    if (tl) { tl.kill(); tl = null; }
    if (st) { st.kill(); st = null; }
    if (window.gsap) { gsap.killTweensOf([markIn, cue, line1, line2, cap]); }
    [markIn, cue, line1, line2, introH1, band].forEach(function (el) { if (el) { el.style.opacity = ''; el.style.transform = ''; } });
    body.classList.remove('gl', 'entering');
    if (chain) { chain.style.height = ''; }
    body.classList.add('static');
    if (reduce) { body.classList.add('reduced'); }
    if (window.ScrollTrigger) { ScrollTrigger.refresh(); }
  }
  if (!window.gsap || !window.ScrollTrigger || !window.SplitText || reduce || forceNoGl || !body.classList.contains('gl')) { goStatic(); return; }
  gsap.registerPlugin(ScrollTrigger, SplitText);
  ScrollTrigger.config({ ignoreMobileResize: true });

  var gl = null;
  try {
    var opts = { alpha: false, antialias: false, depth: false, stencil: false, powerPreference: 'high-performance', preserveDrawingBuffer: false };
    gl = canvas.getContext('webgl', opts) || canvas.getContext('experimental-webgl', opts);
  } catch (e) { gl = null; }
  if (!gl) { goStatic(); return; }

  var VS = 'attribute vec2 p; void main(){ gl_Position = vec4(p, 0.0, 1.0); }';
  var FS = [
  '#ifdef GL_FRAGMENT_PRECISION_HIGH', 'precision highp float;', '#else', 'precision mediump float;', '#endif',
  'uniform vec2 uRes; uniform float uTime;',
  'uniform sampler2D tBefore; uniform sampler2D tAfter; uniform sampler2D tNext;',
  'uniform vec2 uFocal; uniform float uImgAspect; uniform vec2 uNextFocal; uniform float uNextAspect; uniform vec3 uBg;',
  'uniform float uFade;',
  'uniform int uLayerA;',
  'uniform vec2 uA0[5]; uniform vec2 uAD[5]; uniform float uAL[5]; uniform float uAH[5]; uniform float uAW[5];',
  'uniform float uARad; uniform float uASeed; uniform float uASpread;',
  'uniform vec2 uB0; uniform vec2 uBD; uniform float uBL; uniform float uBH; uniform float uBW; uniform float uBRad; uniform float uBSeed;',
  'uniform vec2 uBloomO; uniform float uBloomR; uniform vec2 uBloomBias; uniform float uBloomSeed;',
  'uniform float uScrim; uniform float uXfade;',
  'uniform float uFit; uniform vec4 uRect; uniform float uRectAspect;',
  'float hash(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }',
  'float noise(vec2 p){ vec2 i = floor(p); vec2 f = fract(p); f = f*f*(3.0-2.0*f);',
  '  return mix(mix(hash(i), hash(i+vec2(1.0,0.0)), f.x), mix(hash(i+vec2(0.0,1.0)), hash(i+vec2(1.0,1.0)), f.x), f.y); }',
  'float fbm3(vec2 p){ float v = 0.0; float a = 0.5; for (int i = 0; i < 3; i++){ v += a*noise(p); p = p*2.03 + vec2(17.1, 9.3); a *= 0.5; } return v; }',
  /* cover crop of an image of aspect ia into a viewport of aspect `aspect`, keeping the focal point */
  'vec2 coverUV(vec2 td, float aspect, float ia, vec2 f){',
  '  if (aspect > ia){ float vr = ia/aspect; float v0 = clamp(f.y - 0.5*vr, 0.0, 1.0 - vr); return vec2(td.x, v0 + td.y*vr); }',
  '  float ur = aspect/ia; float u0 = clamp(f.x - 0.5*ur, 0.0, 1.0 - ur); return vec2(u0 + td.x*ur, td.y); }',
  /* one painted segment: bristle streaks along the tangent, ragged edge, torn rounded front, wet band behind the head */
  'float paintSeg(vec2 p, vec2 a, vec2 dir, float len, float head, float wf, float rad, float seed, float ragged, float style, inout float wet, inout float wetU, inout float wetB){',
  '  if (head <= 0.0) return 0.0;',
  '  float t = dot(p - a, dir); float hd = min(head, len); float u = clamp(t, 0.0, hd);',
  '  float d = length(p - (a + dir*u));',
  '  if (d > rad*1.35) return 0.0;',
  '  float v = dot(p - a, vec2(-dir.y, dir.x));',
  '  float bristle = noise(vec2(v*90.0 + seed, u*3.0))*0.35;',
  '  float m = 0.0; float edge = rad;',
  '  if (style < 0.5){',
  /* style 0, the house brush: rounded front, bristle streaks trailing at the head, dry-brush lines on both side edges */
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
  /* style 1, the wall stroke: each bristle lane leads or lags, so the head is a torn comb, never a straight wipe */
  '    edge = rad*(0.72 + bristle + ragged + (noise(vec2(u*48.0 + seed, v*6.0)) - 0.5)*0.07);',
  '    m = 1.0 - smoothstep(edge - 0.0035, edge + 0.0035, d);',
  '    float lead = (noise(vec2(v*70.0 + seed, 3.0)) - 0.5)*0.6 + (noise(vec2(v*230.0 + seed, 7.0)) - 0.5)*0.25;',
  '    float front = hd + lead*rad;',
  '    m *= 1.0 - smoothstep(front - 0.02 - ragged*0.2, front + 0.012, t);',
  '  }',
  '  float w = m * (1.0 - smoothstep(0.0, 0.10, hd - u)) * wf;',
  '  if (w > wet){ wet = w; wetU = u; wetB = bristle; }',
  '  return m; }',
  'void main(){',
  '  vec2 fragN = gl_FragCoord.xy / uRes; vec2 td = vec2(fragN.x, 1.0 - fragN.y);',
  '  float aspect = uRes.x / uRes.y;',
  /* portrait fit: the room is drawn whole inside uRect (x, y, w, h in viewport fractions, top down), the rest is ground */
  '  if (uFit > 0.5){ td = (td - uRect.xy) / uRect.zw; aspect = uRectAspect;',
  '    if (td.x < 0.0 || td.x > 1.0 || td.y < 0.0 || td.y > 1.0){ gl_FragColor = vec4(uBg, 1.0); return; } }',
  '  vec2 uv = coverUV(td, aspect, uImgAspect, uFocal);',
  '  vec3 before = texture2D(tBefore, uv).rgb; vec3 after = texture2D(tAfter, uv).rgb;',
  '  float wet = 0.0; float wetU = 0.0; float wetB = 0.17; float maskA = 1.0;',
  '  if (uLayerA > 0){',
  '    vec2 pA = aspect >= 1.0 ? vec2(td.x*aspect, td.y) : vec2(td.x, td.y/aspect);',
  '    float ragA = fbm3(pA*14.0 + uASeed)*0.18; maskA = 0.0;',
  '    for (int i = 0; i < 5; i++){',
  '      maskA = max(maskA, paintSeg(pA, uA0[i], uAD[i], uAL[i], uAH[i], uAW[i], uARad*uASpread, uASeed + float(i)*7.0, ragA, 0.0, wet, wetU, wetB)); } }',
  '  float ragB = fbm3(uv*14.0 + uBSeed)*0.18;',
  '  float maskB = paintSeg(uv, uB0, uBD, uBL, uBH, uBW, uBRad, uBSeed, ragB, 1.0, wet, wetU, wetB);',
  '  float bloom = 0.0;',
  '  if (uBloomR > 0.0){ vec2 dv = uv - uBloomO; float d = length(dv*vec2(1.0, 0.6)) + max(0.0, dot(dv, uBloomBias));',
  '    d += (fbm3(uv*6.0 + uBloomSeed) - 0.44)*0.25; bloom = 1.0 - smoothstep(uBloomR - 0.02, uBloomR + 0.02, d); }',
  '  vec3 col = mix(uBg, before, maskA);',
  '  col = mix(col, after, max(maskB, bloom));',
  '  wet *= (0.85 + 0.15*noise(vec2(wetU*40.0, uTime*0.4)));',
  '  col += wet*0.08*vec3(1.0, 0.97, 0.92);',
  '  col *= 1.0 + (wetB - 0.17)*0.16*wet;',
  '  if (uXfade > 0.0) col = mix(col, texture2D(tNext, coverUV(td, aspect, uNextAspect, uNextFocal)).rgb, uXfade);',
  '  col = mix(col, uBg, (1.0 - smoothstep(0.0, 0.42, fragN.y))*0.85*uScrim);',
  '  col = mix(col, uBg, uFade);',
  '  gl_FragColor = vec4(col, 1.0); }'
  ].join('\n');

  function compile(type, src) {
    var sh = gl.createShader(type); gl.shaderSource(sh, src); gl.compileShader(sh);
    if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) { console.error(gl.getShaderInfoLog(sh)); return null; }
    return sh;
  }
  var vs = compile(gl.VERTEX_SHADER, VS), fs = compile(gl.FRAGMENT_SHADER, FS);
  if (!vs || !fs) { goStatic(); return; }
  var prog = gl.createProgram(); gl.attachShader(prog, vs); gl.attachShader(prog, fs); gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) { console.error(gl.getProgramInfoLog(prog)); goStatic(); return; }
  gl.useProgram(prog);
  var buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  var pLoc = gl.getAttribLocation(prog, 'p'); gl.enableVertexAttribArray(pLoc); gl.vertexAttribPointer(pLoc, 2, gl.FLOAT, false, 0, 0);
  var L = {};
  ['uRes', 'uTime', 'tBefore', 'tAfter', 'tNext', 'uFocal', 'uImgAspect', 'uNextFocal', 'uNextAspect', 'uBg', 'uFade', 'uLayerA', 'uA0', 'uAD', 'uAL', 'uAH', 'uAW', 'uARad', 'uASeed', 'uASpread',
   'uB0', 'uBD', 'uBL', 'uBH', 'uBW', 'uBRad', 'uBSeed', 'uBloomO', 'uBloomR', 'uBloomBias', 'uBloomSeed', 'uScrim', 'uXfade', 'uFit', 'uRect', 'uRectAspect'].forEach(function (n) { L[n] = gl.getUniformLocation(prog, n); });
  gl.uniform1i(L.tBefore, 0); gl.uniform1i(L.tAfter, 1); gl.uniform1i(L.tNext, 2);
  gl.uniform3f(L.uBg, 15 / 255, 15 / 255, 20 / 255);

  /* textures: 1800 px wide webp (about 130 to 210 KB each, 2026-09-26); touch devices upload at a 1600 px long edge */
  var placeholder = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, placeholder);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([15, 15, 20, 255]));
  var imgs = {}, loading = {}, texCache = {};
  function texSource(img) {
    if (!touch) { return img; }
    var w = img.naturalWidth, h = img.naturalHeight, m = Math.max(w, h);
    if (m <= 1600) { return img; }
    var s = 1600 / m, c = document.createElement('canvas');
    c.width = Math.round(w * s); c.height = Math.round(h * s);
    c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
    return c;
  }
  function makeTex(img) {
    var t = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, texSource(img));
    return t;
  }
  function loadImg(name) {
    if (imgs[name]) { return Promise.resolve(imgs[name]); }
    if (loading[name]) { return loading[name]; }
    loading[name] = new Promise(function (res) {
      var im = new Image();
      im.onload = function () { var done = function () { imgs[name] = im; dirty(); res(im); };
        if (im.decode) { im.decode().then(done, done); } else { done(); } };
      im.onerror = function () { res(null); };
      im.src = '/images/home2/' + name;
    });
    return loading[name];
  }
  function getTex(name) {
    if (!name) { return placeholder; }
    if (texCache[name]) { return texCache[name]; }
    if (imgs[name]) { texCache[name] = makeTex(imgs[name]); return texCache[name]; }
    loadImg(name);
    return placeholder;
  }
  function pruneTex(keep) {
    Object.keys(texCache).forEach(function (n) {
      if (keep.indexOf(n) < 0) { gl.deleteTexture(texCache[n]); delete texCache[n]; }
    });
  }

  /* the rooms. rect is the artwork in the after image (u0, v0, u1, v1), from the pairs manifest;
     fx, fy the cover focal points; `from` the side of the artwork with more wall, where the brush lands.
     A pair may carry a `port` variant for portrait and phone screens; none does at present. hi: the room has
     2400 px twins of both images (below). */
  var PAIRS = [
    { id: 'p3', cap: 'p3',   seed: 3.7,  land: { b: 'pairs/p3_before.webp', a: 'pairs/p3_after.webp', w: 1800, h: 1200, rect: [0.554, 0.139, 0.709, 0.515], fx: 0.63, fy: 0.40, from: 'right', hi: 1 } },
    { id: 'p4', cap: 'p4',   seed: 11.3, land: { b: 'pairs/p4_before.webp', a: 'pairs/p4_after.webp', w: 1800, h: 1180, rect: [0.828, 0.204, 0.987, 0.513], fx: 0.86, fy: 0.38, from: 'left', hi: 1 } },
    { id: 'p5', cap: 'p5',   seed: 19.9, land: { b: 'pairs/p5_before.webp', a: 'pairs/p5_after.webp', w: 1800, h: 1201, rect: [0.026, 0.000, 0.200, 0.593], fx: 0.15, fy: 0.35, from: 'right', hi: 1 } },
    { id: 'p1', cap: 'p1',   seed: 27.1, land: { b: 'pairs/p1_before.webp', a: 'pairs/p1_after.webp', w: 1800, h: 1201, rect: [0.842, 0.152, 0.977, 0.528], fx: 0.85, fy: 0.40, from: 'left', hi: 1 } }
  ];
  /* a buyer variant's own rooms (2026-09-27): build-home.py sets window.THEODORA_ROOMS on a variant page whose
     content/variants/<id>.json has "rooms", one { slot, b, a, w, h, rect, fx, fy, from, seed } per room it
     replaces (slot 0 is the first fold). The room takes over the slot's land fields and seed, and drops any
     portrait variant, which belongs to the homepage's room; the slot keeps its cap key, and the build has put
     the room's caption under that key in #cap. No list, nothing changes. */
  var ROOMS = window.THEODORA_ROOMS;
  if (Array.isArray(ROOMS)) {
    ROOMS.forEach(function (r) {
      var p = r && PAIRS[r.slot];
      if (!p) { return; }
      ['b', 'a', 'w', 'h', 'rect', 'fx', 'fy', 'from', 'hi'].forEach(function (k) { p.land[k] = r[k]; });
      if (typeof r.seed === 'number') { p.seed = r.seed; }
      delete p.port;
    });
    /* rooms_rest "drop" (the default beside rooms, 2026-09-28): the opening ends with the variant's last room instead
       of going on through the homepage's, and the scroll spacer shrinks to match (50vh, then 55vh a chapter) */
    if (window.THEODORA_ROOMS_ONLY && ROOMS.length) {
      PAIRS.length = Math.min(PAIRS.length, ROOMS.length);
      chain.style.height = (50 + 55 * (PAIRS.length - 1)) + 'vh';
    }
  }
  /* 2400 px textures (2026-10-06): a room with hi has a <name>-2400.webp twin of both images (same room, same crop,
     same shape). They load only where the canvas is wider than about 2000 device px on a fine pointer (HI_MQ; DPR is
     capped at 2 there, see sizeCanvas). Phones and touch screens stay on the 1800 px files: their DPR is capped at
     1.5 and texSource draws their textures at 1600 px at most. build-home.py puts this same query (read from this
     line) on the preload links, so the first pair is fetched once, at the size used here. */
  var HI_MQ = '(pointer: fine) and (not (any-pointer: coarse)) and ((width > 2000px) or ((width > 1600px) and (resolution >= 1.25dppx)) or ((width > 1333px) and (resolution >= 1.5dppx)) or ((width > 1000px) and (resolution >= 2dppx)))';
  var hiRes = dbg.hi = !touch && !!(window.matchMedia && matchMedia(HI_MQ).matches);
  if (hiRes) {
    PAIRS.forEach(function (p) {
      [p.land, p.port].forEach(function (v) {
        if (v && v.hi) { v.b = v.b.replace(/\.webp$/, '-2400.webp'); v.a = v.a.replace(/\.webp$/, '-2400.webp'); }
      });
    });
  }
  /* the wall stroke runs across the artwork's vertical centre, lands half a radius outside the rect on the
     wall side and ends 0.6 radius past the far edge; radius 0.62 x rect height, capped for the tall canvases;
     the bloom opens from the rect centre */
  function deriveStroke(v) {
    var r = v.rect, h = r[3] - r[1], cy = (r[1] + r[3]) / 2, rad = Math.min(0.62 * h, 0.32);
    var x0 = v.from === 'left' ? r[0] - 0.5 * rad : r[2] + 0.5 * rad;
    var x1 = v.from === 'left' ? r[2] + 0.6 * rad : r[0] - 0.6 * rad;
    v.b0 = [x0, cy + 0.015 * h]; v.b1 = [x1, cy - 0.015 * h];
    var dx = v.b1[0] - v.b0[0], dy = v.b1[1] - v.b0[1];
    v.len = Math.hypot(dx, dy); v.dir = [dx / v.len, dy / v.len];
    v.rad = rad; v.bo = [(r[0] + r[2]) / 2, cy]; v.aspect = v.w / v.h;
  }
  PAIRS.forEach(function (p) { deriveStroke(p.land); if (p.port) { deriveStroke(p.port); } });
  dbg.pairs = PAIRS.length;
  function portrait() { return canvas.clientHeight > canvas.clientWidth; }
  function vr(p) { return (p.port && portrait()) ? p.port : p.land; }

  /* portrait fit (2026-09-27): below FIT_BELOW (width / height) a cover fit showed about a third of each
     room and the wall stroke started and ended off screen, so the room is drawn whole instead: FIT_W of the
     screen width, FIT_ASPECT (the rooms are 3:2), centred, on the ground colour. Every brush then works inside
     that rectangle exactly as it does on a desktop screen of the same shape. Landscape keeps the cover fit. */
  var FIT_BELOW = 0.9, FIT_ASPECT = 1.5, FIT_W = 1.0;
  var fit = dbg.fit = { on: false, x: 0, y: 0, w: 1, h: 1, aspect: 1 };
  function computeFit() {
    var W = Math.max(1, canvas.width), H = Math.max(1, canvas.height);
    fit.on = canvas.clientWidth / Math.max(1, canvas.clientHeight) <= FIT_BELOW; /* matches max-aspect-ratio: 9/10 in theme.css */
    if (!fit.on) { fit.x = 0; fit.y = 0; fit.w = 1; fit.h = 1; fit.aspect = W / H; return; }
    var rw = Math.round(W * FIT_W), rh = Math.round(rw / FIT_ASPECT);
    if (rh > H) { rh = H; rw = Math.round(rh * FIT_ASPECT); }
    fit.x = Math.round((W - rw) / 2) / W; fit.y = Math.round((H - rh) / 2) / H;
    fit.w = rw / W; fit.h = rh / H; fit.aspect = rw / rh;
  }

  /* the house painter's zigzag, viewport fractions (or fit-rectangle fractions), top down */
  var DT = [[-0.05, 0.12, 1.05, 0.19], [1.05, 0.54, -0.05, 0.46], [-0.05, 0.81, 1.05, 0.87]];
  var PH = [[-0.05, 0.07, 1.05, 0.09], [1.05, 0.30, -0.05, 0.28], [-0.05, 0.49, 1.05, 0.51], [1.05, 0.72, -0.05, 0.70], [-0.05, 0.91, 1.05, 0.93]];
  var passes = [], spreadMin = 1.25, spreadMax = 1.45;
  function buildPasses() {
    var aspect = fit.on ? fit.aspect : canvas.clientWidth / Math.max(1, canvas.clientHeight);
    var fr = aspect < 1 ? PH : DT;
    spreadMin = aspect < 1 ? 1.5 : 1.25; spreadMax = aspect < 1 ? 1.9 : 1.45;
    var toU = function (x, y) { return aspect >= 1 ? [x * aspect, y] : [x, y / aspect]; };
    passes = fr.map(function (s) {
      var a = toU(s[0], s[1]), b = toU(s[2], s[3]); var dx = b[0] - a[0], dy = b[1] - a[1]; var len = Math.hypot(dx, dy);
      return { a: a, d: [dx / len, dy / len], len: len };
    });
  }

  /* uniforms as plain numbers so GSAP can tween them */
  var U = { layerA: 1, spread: 1.25, h0: 0, h1: 0, h2: 0, h3: 0, h4: 0, w0: 1, w1: 1, w2: 1, w3: 1, w4: 1,
            bh: 0, bw: 1, bloom: 0, scrim: 0, xfade: 0, fade: 0, pair: PAIRS[0], next: PAIRS[1] || null };
  var dirtyFlag = true, t0 = performance.now(), covered = false;
  function dirty() { dirtyFlag = true; }
  function texNames() { var v = vr(U.pair), n = U.next ? vr(U.next) : null; return { b: v.b, a: v.a, n: n ? n.b : null }; }
  function wetAlive() {
    if (U.bw > 0.001 && U.bh > 0) { return true; }
    for (var i = 0; i < 5; i++) { if (U['w' + i] > 0.001 && U['h' + i] > 0 && U.layerA > 0) { return true; } }
    return false;
  }
  var A0 = new Float32Array(10), AD = new Float32Array(10), AL = new Float32Array(5), AH = new Float32Array(5), AW = new Float32Array(5);
  function draw() {
    dirtyFlag = false;
    var p = U.pair, v = vr(p), nv = U.next ? vr(U.next) : v;
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.uniform2f(L.uRes, canvas.width, canvas.height);
    gl.uniform1f(L.uTime, (performance.now() - t0) / 1000);
    gl.uniform2f(L.uFocal, v.fx, v.fy); gl.uniform1f(L.uImgAspect, v.aspect);
    gl.uniform2f(L.uNextFocal, nv.fx, nv.fy); gl.uniform1f(L.uNextAspect, nv.aspect);
    gl.uniform1f(L.uFade, U.fade);
    gl.uniform1i(L.uLayerA, U.layerA);
    for (var i = 0; i < 5; i++) {
      var s = passes[i];
      if (s) { A0[i * 2] = s.a[0]; A0[i * 2 + 1] = s.a[1]; AD[i * 2] = s.d[0]; AD[i * 2 + 1] = s.d[1]; AL[i] = s.len; AH[i] = U['h' + i] * s.len; AW[i] = U['w' + i]; }
      else { A0[i * 2] = 0; A0[i * 2 + 1] = 0; AD[i * 2] = 1; AD[i * 2 + 1] = 0; AL[i] = 0; AH[i] = 0; AW[i] = 0; }
    }
    gl.uniform2fv(L.uA0, A0); gl.uniform2fv(L.uAD, AD); gl.uniform1fv(L.uAL, AL); gl.uniform1fv(L.uAH, AH); gl.uniform1fv(L.uAW, AW);
    gl.uniform1f(L.uARad, 0.19); gl.uniform1f(L.uASeed, 5.3); gl.uniform1f(L.uASpread, U.spread);
    gl.uniform2f(L.uB0, v.b0[0], v.b0[1]); gl.uniform2f(L.uBD, v.dir[0], v.dir[1]); gl.uniform1f(L.uBL, v.len);
    gl.uniform1f(L.uBH, U.bh * v.len); gl.uniform1f(L.uBW, U.bw); gl.uniform1f(L.uBRad, v.rad); gl.uniform1f(L.uBSeed, p.seed);
    gl.uniform2f(L.uBloomO, v.bo[0], v.bo[1]); gl.uniform1f(L.uBloomR, U.bloom); gl.uniform2f(L.uBloomBias, 0, 0); gl.uniform1f(L.uBloomSeed, p.seed * 1.7);
    gl.uniform1f(L.uScrim, U.scrim); gl.uniform1f(L.uXfade, U.xfade);
    gl.uniform1f(L.uFit, fit.on ? 1 : 0); gl.uniform4f(L.uRect, fit.x, fit.y, fit.w, fit.h); gl.uniform1f(L.uRectAspect, fit.aspect);
    var n = texNames();
    gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, getTex(n.b));
    gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, getTex(n.a));
    gl.activeTexture(gl.TEXTURE2); gl.bindTexture(gl.TEXTURE_2D, getTex(n.n));
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }
  function sizeCanvas() {
    var dpr = Math.min(window.devicePixelRatio || 1, touch ? 1.5 : 2);
    var w = Math.round(canvas.clientWidth * dpr), h = Math.round(canvas.clientHeight * dpr);
    if (canvas.width === w && canvas.height === h) { return; }
    canvas.width = w; canvas.height = h; dirty();
  }
  sizeCanvas(); computeFit(); buildPasses();
  window.addEventListener('resize', function () { sizeCanvas(); computeFit(); buildPasses(); dirty(); });
  gsap.ticker.add(function () { if (glDead || covered) { return; } if (dirtyFlag || wetAlive()) { draw(); } });
  canvas.addEventListener('webglcontextlost', function (e) { e.preventDefault(); goStatic(); });

  /* caption for the proposal: one line per room (data-cap = the pair id), visible whenever any after pixel is on screen, bilingual twins follow the switch */
  var capKey = '', capOn = false;
  function capSet(key) {
    if (key === null) { if (capOn) { capOn = false; gsap.to(cap, { opacity: 0, duration: 0.2, overwrite: true }); } return; }
    if (key !== capKey) { capKey = key; cap.setAttribute('data-show', key); }
    if (!capOn) { capOn = true; gsap.to(cap, { opacity: 1, duration: 0.2, overwrite: true }); }
  }
  var canvasOp = 1;
  function canvasOpacity(op) {
    if (op === canvasOp) { return; } canvasOp = op;
    canvas.style.opacity = op; canvas.style.visibility = op > 0 ? 'visible' : 'hidden';
  }

  /* wet paint while the finger moves, dries 1.2 s after it stops */
  var dryCall = null, dryTween = null;
  function killDry() { if (dryCall) { dryCall.kill(); } if (dryTween) { dryTween.kill(); } dryCall = null; dryTween = null; }
  function startDry() { dryTween = gsap.to(U, { bw: 0, duration: 0.9, ease: 'power2.inOut', onUpdate: dirty }); }
  function wetTouch() {
    if (dryTween) { dryTween.kill(); dryTween = null; }
    U.bw = 1;
    if (dryCall) { dryCall.restart(true); } else { dryCall = gsap.delayedCall(0.3, startDry); }
  }

  /* scroll: hero out over the first 50vh, three chapters of 55vh on the 215vh spacer, then the intro block's own
     100svh: the block slides over the fixed canvas while the canvas fades to the page ground and the h1 settles in.
     One smoothed progress for all of it. */
  var CH = PAIRS.length - 1;
  var entranceDone = false, skipping = false, lastP = -1;
  function applyScroll(P) {
    if (glDead || st === null) { return; }
    var total = Math.max(1, st.end - st.start), heroDist = Math.max(1, hero.offsetHeight * 0.5);
    var chainDist = Math.max(1, chain.offsetHeight - heroDist), blockDist = Math.max(1, total - heroDist - chainDist);
    var y = P * total, q = clamp(y / heroDist, 0, 1), cp = clamp((y - heroDist) / chainDist, 0, 1), a = clamp((y - heroDist - chainDist) / blockDist, 0, 1);
    dbg.progress = P; dbg.y = y;
    markIn.style.opacity = 1 - ss(0, 0.4, q);
    canvasOpacity(1);
    if (cp <= 0) {
      U.pair = PAIRS[0]; U.next = PAIRS[1] || null;
      if (entranceDone && !skipping) { U.layerA = 0; U.bh = 1; U.bloom = 1.6; U.scrim = 0; U.bw = 0; killDry(); }
      U.xfade = PAIRS[1] ? ss(0.4, 1, q) : 0; U.fade = 0;
      if (entranceDone) { capSet(U.xfade < 1 ? PAIRS[0].cap : null); }
    } else {
      var idx = CH > 0 ? Math.min(CH - 1, Math.floor(cp * CH)) : -1, local = CH > 0 ? cp * CH - idx : 1;
      var pr = PAIRS[idx + 1], nx = PAIRS[idx + 2] || null;
      U.pair = pr; U.next = nx; U.layerA = 0; U.scrim = 0;
      U.bh = ss(0, 0.80, local);
      U.bloom = ss(0.50, 0.84, local) * 1.6;
      U.xfade = nx ? ss(0.84, 1, local) : 0;
      /* the last room is seen whole, then the canvas fades to the ground as the intro block rises over it */
      U.fade = ss(0, 0.55, a);
      capSet((U.bh > 0 && U.xfade < 1 && a < 0.3) ? pr.cap : null);
      if (P !== lastP && local < 0.9 && a <= 0) { wetTouch(); }
    }
    band.style.opacity = 1 - U.fade;
    var r = ss(0.35, 0.95, a);
    introH1.style.opacity = 0.5 + 0.5 * r;
    introH1.style.transform = 'translateY(' + (22 * (1 - r)).toFixed(2) + 'px)';
    var n = texNames(); pruneTex([n.b, n.a, n.n]);
    lastP = P; dirty();
  }
  var prox = { p: 0 };
  st = ScrollTrigger.create({
    trigger: hero, start: 'top top', endTrigger: intro, end: 'bottom bottom', scrub: 1.0,
    animation: gsap.to(prox, { p: 1, ease: 'none', duration: 1, onUpdate: function () { applyScroll(prox.p); } }),
    onRefresh: function () { applyScroll(prox.p); }
  });
  /* once the intro block has slid over the canvas the canvas is hidden and stops drawing */
  ScrollTrigger.create({ trigger: page, start: 'top top',
    onEnter: function () { covered = true; dbg.covered = true; canvasOpacity(0); },
    onLeaveBack: function () { covered = false; dbg.covered = false; canvasOpacity(1); dirty(); } });

  /* the entrance */
  var wantSkip = false, started = false;
  function finishDom(d) {
    gsap.to([line1, line2], { opacity: 0, duration: d, ease: 'power2.out', overwrite: true });
    gsap.to(cue, { opacity: 1, duration: d, ease: 'power2.out', overwrite: true });
    body.classList.remove('entering');
  }
  function skipEntrance() {
    if (entranceDone || skipping) { return; }
    if (!started) { wantSkip = true; return; }
    skipping = true;
    if (tl) { tl.kill(); }
    var fin = { spread: spreadMax, bh: 1, bloom: 1.6, scrim: 0, bw: 0 };
    for (var i = 0; i < 5; i++) { fin['h' + i] = 1; fin['w' + i] = 0; }
    gsap.killTweensOf(U);
    gsap.to(U, Object.assign(fin, { duration: 0.3, ease: 'power2.out', onUpdate: dirty,
      onComplete: function () { skipping = false; entranceDone = true; dbg.done = true; U.layerA = 0; dirty(); applyScroll(prox.p); } }));
    finishDom(0.3);
    capSet(PAIRS[0].cap);
  }
  /* touch, wheel, pointer and scroll no longer skip the entrance (2026-09-27): it runs to its end and the boot script in
     templates/home.html holds the page still meanwhile. Escape is the one deliberate skip. */
  window.addEventListener('keydown', function onEsc(e) {
    if (e.key !== 'Escape') { return; }
    window.removeEventListener('keydown', onEsc); skipEntrance();
  });

  function startEntrance() {
    started = true; dbg.mode = 'gl';
    computeFit(); buildPasses();
    U.spread = spreadMin;
    U.pair = PAIRS[0]; U.next = PAIRS[1] || null;
    /* a page that opens already scrolled (restored position, a #hash link) skips straight to the end */
    if (wantSkip || (window.pageYOffset || document.documentElement.scrollTop) > 2) { skipEntrance(); return; }
    var lang = body.classList.contains('lang-he') ? 'he' : 'en';
    var e1 = line1.querySelector('[data-l="' + lang + '"]') || line1, e2 = line2.querySelector('[data-l="' + lang + '"]') || line2;
    var n = passes.length, durA = (2.0 + (n - 1) * 0.08) / n;
    var s1 = new SplitText(e1, { type: 'chars', charsClass: 'ch' });
    var s2 = new SplitText(e2, { type: 'chars', charsClass: 'ch' });
    gsap.set(s1.chars.concat(s2.chars), { opacity: 0, y: 10 });
    gsap.set([line1, line2], { opacity: 1 });
    tl = gsap.timeline({ paused: true, onComplete: function () { entranceDone = true; dbg.done = true; U.layerA = 0; dirty(); applyScroll(prox.p); } });
    for (var i = 0; i < n; i++) {
      var t = 0.30 + i * (durA - 0.08);
      tl.to(U, { ['h' + i]: 1, duration: durA, ease: 'power2.inOut', onUpdate: dirty }, t);
      tl.to(U, { ['w' + i]: 0, duration: 1.2, ease: 'power2.inOut', onUpdate: dirty }, t + durA);
    }
    tl.to(U, { spread: spreadMax, duration: 1.2, ease: 'power2.inOut', onUpdate: dirty }, 0.8);
    tl.to(U, { scrim: 1, duration: 0.4, ease: 'power2.out', onUpdate: dirty }, 1.5);
    tl.to(s1.chars, { opacity: 1, y: 0, duration: 0.7, ease: 'power2.out', stagger: 0.03 }, 1.60);
    tl.to(line1, { opacity: 0, duration: 0.35, ease: 'power2.in' }, 3.00);
    tl.to(U, { scrim: 0, duration: 0.35, ease: 'power2.in', onUpdate: dirty }, 3.00);
    tl.call(function () { capSet(PAIRS[0].cap); }, null, 3.30);
    tl.to(U, { bh: 1, duration: 1.1, ease: 'power3.inOut', onUpdate: dirty }, 3.30);
    tl.to(U, { bw: 0, duration: 1.2, ease: 'power2.inOut', onUpdate: dirty }, 4.40);
    tl.to(U, { bloom: 1.6, duration: 1.0, ease: 'power2.inOut', onUpdate: dirty }, 4.20);
    tl.to(U, { scrim: 1, duration: 0.4, ease: 'power2.out', onUpdate: dirty }, 4.20);
    tl.to(s2.chars, { opacity: 1, y: 0, duration: 0.7, ease: 'power2.out', stagger: 0.03 }, 4.30);
    tl.to(line2, { opacity: 0, duration: 0.35, ease: 'power2.in' }, 5.40);
    tl.to(U, { scrim: 0, duration: 0.35, ease: 'power2.in', onUpdate: dirty }, 5.40);
    tl.call(function () { body.classList.remove('entering'); }, null, 5.78);
    tl.to(cue, { opacity: 1, duration: 0.5, ease: 'power2.out' }, 5.86);
    tl.timeScale(1 / SLOW);
    dbg.t0 = performance.now();
    tl.play();
  }

  var fontsReady = Promise.race([(document.fonts && document.fonts.ready) || Promise.resolve(), new Promise(function (r) { setTimeout(r, 900); })]);
  var first = vr(PAIRS[0]);
  Promise.all([loadImg(first.b), loadImg(first.a), fontsReady]).then(function () {
    if (glDead) { return; }
    startEntrance();
    var rest = [];
    PAIRS.slice(1).forEach(function (p) { var v = vr(p); rest.push(v.b, v.a); });
    (function next() { var nm = rest.shift(); if (nm) { loadImg(nm).then(next); } })();
  });
})();
