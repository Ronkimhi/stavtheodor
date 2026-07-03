// Pan/zoom camera for the infinite canvas.
// Camera = {x, y, s}: world point (x, y) sits at screen (0, 0), scale s.

export class Viewport {
  constructor(stage, world, worldSize, { onZoomTier, onChange } = {}) {
    this.stage = stage;
    this.world = world;
    this.size = worldSize;
    this.cam = { x: 0, y: 0, s: 1 };
    this.onZoomTier = onZoomTier;
    this.onChange = onChange;
    this.tier = -1;
    this.pointers = new Map();
    this.vel = { x: 0, y: 0 };
    this.samples = [];
    this.lastMove = 0;
    this.inertiaRaf = 0;
    this.tween = null;
    this.moved = false;

    stage.addEventListener('pointerdown', (e) => this.down(e));
    stage.addEventListener('pointermove', (e) => this.move(e));
    stage.addEventListener('pointerup', (e) => this.up(e));
    stage.addEventListener('pointercancel', (e) => this.up(e));
    stage.addEventListener('wheel', (e) => this.wheel(e), { passive: false });
    stage.addEventListener('dblclick', (e) => {
      this.flyTo(this.toWorld(e.clientX, e.clientY), this.cam.s * 1.7, 420);
    });
    this.userMoved = false;
    stage.addEventListener('pointerdown', () => { this.userMoved = true; }, { once: true });
    stage.addEventListener('wheel', () => { this.userMoved = true; }, { once: true });
    // ResizeObserver instead of window resize: also fires when the page starts
    // hidden/collapsed (0×0) and later gets its real size.
    new ResizeObserver(() => {
      if (!this.userMoved) this.fitAll();
      else { this.clamp(); this.apply(); }
    }).observe(stage);
  }

  fitAll(pad = 60) {
    const vw = Math.max(320, innerWidth), vh = Math.max(320, innerHeight);
    // The page title floats fixed over the canvas; fit the world into the
    // clear area beneath it so the map never renders under the heading.
    // Capped so short landscape viewports still keep most of the height.
    const head = document.querySelector('.canvas-head');
    const top = head
      ? Math.min(head.getBoundingClientRect().bottom + 16, vh * 0.45)
      : 0;
    const availH = vh - top;
    const s = Math.max(0.02, Math.min((vw - pad * 2) / this.size.w, (availH - pad * 2) / this.size.h));
    this.sMin = s * 0.85;
    this.sMax = 7;
    this.cam.s = s;
    this.cam.x = this.size.w / 2 - vw / 2 / s;
    this.cam.y = this.size.h / 2 - (top + availH / 2) / s;
    this.apply();
  }

  toWorld(sx, sy) {
    return { x: this.cam.x + sx / this.cam.s, y: this.cam.y + sy / this.cam.s };
  }

  down(e) {
    this.stopMotion();
    // A press on an artist node stays a tap until it travels: the pointer is
    // tracked but not engaged, so the node's click still fires. Past a small
    // threshold (see move) it engages and becomes a normal pan.
    const onNode = !!e.target.closest('.artist-node');
    this.pointers.set(e.pointerId, {
      x: e.clientX, y: e.clientY,
      startX: e.clientX, startY: e.clientY,
      engaged: !onNode,
    });
    this.moved = false;
    this.vel = { x: 0, y: 0 };
    this.samples = [];
    if (this.pointers.size === 2) {
      const [a, b] = [...this.pointers.values()];
      this.pinch = {
        d: Math.hypot(a.x - b.x, a.y - b.y),
        s: this.cam.s,
        cx: (a.x + b.x) / 2, cy: (a.y + b.y) / 2,
      };
      // a pinch is never a tap: engage both pointers immediately
      for (const [id, p] of this.pointers) this.engage(id, p);
    } else if (!onNode) {
      this.engage(e.pointerId, this.pointers.get(e.pointerId));
    }
    this.stage.classList.add('dragging');
  }

  // Capturing to the stage retargets the eventual click there, which is what
  // cancels the artist-node tap once a press has turned into a drag.
  engage(id, p) {
    p.engaged = true;
    try { this.stage.setPointerCapture(id); } catch (err) { /* pointer already gone */ }
  }

  move(e) {
    const p = this.pointers.get(e.pointerId);
    if (!p) return;
    if (!p.engaged) {
      if (Math.hypot(e.clientX - p.startX, e.clientY - p.startY) < 7) return;
      this.engage(e.pointerId, p);
    }
    const dx = e.clientX - p.x, dy = e.clientY - p.y;
    if (Math.abs(dx) + Math.abs(dy) > 3) this.moved = true;

    if (this.pointers.size === 2) {
      p.x = e.clientX; p.y = e.clientY;
      const [a, b] = [...this.pointers.values()];
      const d = Math.hypot(a.x - b.x, a.y - b.y);
      const cx = (a.x + b.x) / 2, cy = (a.y + b.y) / 2;
      // two-finger pan: follow the centroid, then zoom about it
      this.cam.x -= (cx - this.pinch.cx) / this.cam.s;
      this.cam.y -= (cy - this.pinch.cy) / this.cam.s;
      this.pinch.cx = cx; this.pinch.cy = cy;
      this.zoomAt(cx, cy, (this.pinch.s * d / this.pinch.d) / this.cam.s);
      return;
    }
    p.x = e.clientX; p.y = e.clientY;
    this.cam.x -= dx / this.cam.s;
    this.cam.y -= dy / this.cam.s;
    const now = performance.now();
    this.lastMove = now;
    // fling velocity comes from ~100ms of samples, not one event delta
    // (coalesced touch events make single deltas wildly noisy on phones)
    this.samples.push({ t: now, x: e.clientX, y: e.clientY });
    while (this.samples.length > 2 && now - this.samples[0].t > 100) this.samples.shift();
    this.clamp();
    this.apply();
  }

  up(e) {
    this.pointers.delete(e.pointerId);
    if (this.pointers.size === 1) {
      // pinch over: the surviving finger continues as a clean pan
      this.pinch = null;
      this.samples = [];
    }
    if (this.pointers.size === 0) {
      this.stage.classList.remove('dragging');
      if (this.moved) this.startInertia();
    }
  }

  startInertia() {
    const n = this.samples.length;
    let last = performance.now();
    if (n < 2 || last - this.samples[n - 1].t > 90) return;
    const a = this.samples[0], b = this.samples[n - 1];
    const span = b.t - a.t;
    if (span < 8) return;
    let vx = (b.x - a.x) / span, vy = (b.y - a.y) / span; // screen px/ms
    const v = Math.hypot(vx, vy), vmax = 2.2;
    if (v > vmax) { vx *= vmax / v; vy *= vmax / v; }
    this.vel = { x: -vx / this.cam.s, y: -vy / this.cam.s };
    const step = (t) => {
      const dt = t - last;
      last = t;
      this.vel.x *= Math.pow(0.994, dt);
      this.vel.y *= Math.pow(0.994, dt);
      this.cam.x += this.vel.x * dt;
      this.cam.y += this.vel.y * dt;
      this.clamp();
      this.apply();
      if (Math.hypot(this.vel.x, this.vel.y) * this.cam.s > 0.004) {
        this.inertiaRaf = requestAnimationFrame(step);
      }
    };
    this.inertiaRaf = requestAnimationFrame(step);
  }

  wheel(e) {
    e.preventDefault();
    this.stopMotion();
    const discrete = Math.abs(e.deltaY) >= 60 && e.deltaX === 0 && e.deltaMode === 0;
    if (e.ctrlKey || e.metaKey || discrete || e.deltaMode === 1) {
      const k = Math.exp(-e.deltaY * (e.ctrlKey ? 0.012 : 0.0022));
      this.zoomAt(e.clientX, e.clientY, k);
    } else {
      this.cam.x += e.deltaX / this.cam.s;
      this.cam.y += e.deltaY / this.cam.s;
      this.clamp();
      this.apply();
    }
  }

  zoomAt(sx, sy, k) {
    const w = this.toWorld(sx, sy);
    this.cam.s = Math.max(this.sMin, Math.min(this.sMax, this.cam.s * k));
    this.cam.x = w.x - sx / this.cam.s;
    this.cam.y = w.y - sy / this.cam.s;
    this.clamp();
    this.apply();
  }

  zoomCenter(k) {
    this.zoomAt(innerWidth / 2, innerHeight / 2, k);
  }

  clamp() {
    const vw = innerWidth / this.cam.s, vh = innerHeight / this.cam.s;
    const mx = Math.max(160 / this.cam.s, vw * 0.5);
    const my = Math.max(160 / this.cam.s, vh * 0.5);
    this.cam.x = Math.max(-mx, Math.min(this.size.w + mx - vw, this.cam.x));
    this.cam.y = Math.max(-my, Math.min(this.size.h + my - vh, this.cam.y));
  }

  stopMotion() {
    cancelAnimationFrame(this.inertiaRaf);
    if (this.tween) { cancelAnimationFrame(this.tween); this.tween = null; }
  }

  // Fly the camera so that world point `center` is centered at scale `s`.
  flyTo(center, s, ms = 650) {
    this.stopMotion();
    s = Math.max(this.sMin, Math.min(this.sMax, s));
    const from = { ...this.cam };
    const to = {
      x: center.x - innerWidth / 2 / s,
      y: center.y - innerHeight / 2 / s,
      s,
    };
    const t0 = performance.now();
    const ease = (t) => 1 - Math.pow(1 - t, 3);
    const step = (t) => {
      const k = ease(Math.min(1, (t - t0) / ms));
      // interpolate zoom in log space so it feels linear
      this.cam.s = from.s * Math.pow(to.s / from.s, k);
      this.cam.x = from.x + (to.x - from.x) * k;
      this.cam.y = from.y + (to.y - from.y) * k;
      this.apply();
      if (k < 1) this.tween = requestAnimationFrame(step);
      else { this.tween = null; this.clamp(); this.apply(); }
    };
    this.tween = requestAnimationFrame(step);
  }

  flyToRect(x, y, w, h, pad = 90) {
    const vw = Math.max(320, innerWidth), vh = Math.max(320, innerHeight);
    const s = Math.min((vw - pad * 2) / w, (vh - pad * 2) / h);
    this.flyTo({ x: x + w / 2, y: y + h / 2 }, s);
  }

  apply() {
    const { x, y, s } = this.cam;
    this.world.style.transform = `translate(${-x * s}px, ${-y * s}px) scale(${s})`;
    // Counter-scale for constant-size type; clamped so labels shrink a little
    // when zoomed far out instead of ballooning.
    this.world.style.setProperty('--inv', String(1 / Math.max(s, 0.55)));
    // Past the deepest tier the artist nodes grow gently with the zoom
    // (up to ~2.2x) instead of staying pinned at one screen size, so deep
    // zoom actually brings you closer to the people.
    const grow = Math.min(2.2, Math.pow(Math.max(1, s / 1.55), 0.55));
    this.world.style.setProperty('--grow', String(grow));
    const tier = s < 0.82 ? 0 : s < 1.55 ? 1 : 2;
    if (tier !== this.tier) {
      this.tier = tier;
      this.onZoomTier?.(tier);
    }
    this.onChange?.(this.cam);
  }
}
