// Gallery boot: scene assembly, texture loading, render loop, interactions.

import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { loadArtist, filePathUrl, lifeDates, oneLinerOf } from '../shared/data.js';
import { solveRoom, EYE } from './room.js';
import {
  makeEnvironment, makeFloorMaterial, wallMaterial, ceilingMaterial,
  trimMaterial, frameMaterial, matteMaterial, canvasMaterial,
  benchMaterial, placeholderTexture, vignetteTexture,
} from './materials.js';
import { buildLighting } from './lighting.js';
import { createControls, initTouch, hasPointerLock } from './controls.js';
import { createInspector } from './inspect.js';
import { showListView } from './fallback.js';
import { initThemeToggle } from '../shared/theme.js';

initThemeToggle(document.getElementById('theme-btn'));

const params = new URLSearchParams(location.search);
const slug = params.get('artist') || 'claude-monet';
const DEBUG = params.get('debug'); // '1' | 'orbit' | 'badimg'

const GILT_PERIODS = new Set([
  'medieval-gothic', 'early-renaissance', 'northern-renaissance',
  'high-renaissance', 'mannerism', 'baroque', 'rococo',
]);

const quality = (() => {
  const coarse = matchMedia('(pointer: coarse)').matches;
  const weak = (navigator.hardwareConcurrency || 8) <= 4;
  return {
    mobile: coarse,
    pixelRatio: Math.min(devicePixelRatio || 1, coarse ? 1.5 : 2),
    antialias: !(coarse && weak),
    shadowCasters: coarse || weak ? 2 : 4,
    shadowMap: coarse ? 768 : 1024,
  };
})();

async function boot() {
  let artist;
  try {
    artist = await loadArtist(slug);
  } catch (e) {
    document.getElementById('entry-name').textContent = 'Room not found';
    document.getElementById('entry-sub').textContent = 'This gallery does not exist. Return to the timeline.';
    document.getElementById('entry-btn').textContent = '← Back to the timeline';
    const btn = document.getElementById('entry-btn');
    btn.disabled = false;
    btn.addEventListener('click', () => location.href = '/museum/');
    return;
  }

  document.title = `${artist.name} · The Museum · THEODORA`;
  document.getElementById('entry-name').textContent = artist.name;
  document.getElementById('entry-sub').textContent =
    [oneLinerOf(artist), lifeDates(artist)].filter(Boolean).join(', ');
  document.getElementById('list-link').addEventListener('click', (e) => {
    e.preventDefault();
    showListView(artist);
  });

  if (!artist.hasGallery || !artist.paintings.length) {
    showListView(artist);
    return;
  }
  if (matchMedia('(prefers-reduced-motion: reduce)').matches && !DEBUG) {
    showListView(artist);
    return;
  }

  // WebGL support probe
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: quality.antialias, powerPreference: 'high-performance' });
  } catch (e) {
    showListView(artist);
    return;
  }

  renderer.setPixelRatio(quality.pixelRatio);
  renderer.setSize(innerWidth, innerHeight);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.12;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  document.body.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xF2EEE5);
  makeEnvironment(renderer, scene);

  const camera = new THREE.PerspectiveCamera(68, innerWidth / innerHeight, 0.05, 80);
  const room = solveRoom(artist.paintings);

  // ---------- room shell ----------
  const shell = new THREE.Group();
  const { W, D, H } = room;
  const floor = new THREE.Mesh(
    new THREE.PlaneGeometry(W, D),
    makeFloorMaterial(Math.min(8, renderer.capabilities.getMaxAnisotropy()))
  );
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  shell.add(floor);

  const ceiling = new THREE.Mesh(new THREE.PlaneGeometry(W, D), ceilingMaterial());
  ceiling.rotation.x = Math.PI / 2;
  ceiling.position.y = H;
  shell.add(ceiling);

  const wMat = wallMaterial();
  const wallDefs = [
    { w: W, x: 0, z: -D / 2, ry: 0 },
    { w: D, x: W / 2, z: 0, ry: -Math.PI / 2 },
    { w: W, x: 0, z: D / 2, ry: Math.PI },
    { w: D, x: -W / 2, z: 0, ry: Math.PI / 2 },
  ];
  for (const d of wallDefs) {
    const wall = new THREE.Mesh(new THREE.PlaneGeometry(d.w, H), wMat);
    wall.position.set(d.x, H / 2, d.z);
    wall.rotation.y = d.ry;
    wall.receiveShadow = true;
    shell.add(wall);
  }

  // baseboard + crown trim (thin boxes hugging each wall)
  const tMat = trimMaterial();
  for (const d of wallDefs) {
    for (const [ty, th] of [[0.09, 0.18], [H - 0.07, 0.14]]) {
      const trim = new THREE.Mesh(new THREE.BoxGeometry(d.w, th, 0.04), tMat);
      trim.position.set(d.x, ty, d.z);
      trim.rotation.y = d.ry;
      trim.translateZ(0.021);
      shell.add(trim);
    }
  }

  // ceiling light track (one run per wall, parented so rotations compose cleanly)
  const trackGeo = new THREE.CylinderGeometry(0.035, 0.035, 1, 10);
  const trackMat = new THREE.MeshStandardMaterial({ color: 0x3A342C, roughness: 0.5, metalness: 0.6 });
  for (const d of wallDefs) {
    const holder = new THREE.Group();
    holder.position.set(d.x, H - 0.22, d.z);
    holder.rotation.y = d.ry;
    const track = new THREE.Mesh(trackGeo, trackMat);
    track.rotation.z = Math.PI / 2;   // lie along the holder's local X
    track.scale.y = d.w - 2.4;
    track.position.z = 1.7;           // inward from the wall
    holder.add(track);
    shell.add(holder);
  }

  // central bench
  const bMat = benchMaterial();
  const bench = new THREE.Group();
  const seat = new THREE.Mesh(new THREE.BoxGeometry(2.1, 0.09, 0.55), bMat);
  seat.position.y = 0.46;
  seat.castShadow = true;
  bench.add(seat);
  for (const sx of [-0.85, 0.85]) {
    const leg = new THREE.Mesh(new THREE.BoxGeometry(0.09, 0.44, 0.5), bMat);
    leg.position.set(sx, 0.22, 0);
    leg.castShadow = true;
    bench.add(leg);
  }
  shell.add(bench);

  // artist-name vignette above the door (south wall, inside)
  const vig = new THREE.Mesh(
    new THREE.PlaneGeometry(3.4, 1.7),
    new THREE.MeshBasicMaterial({
      map: vignetteTexture(artist.name, [oneLinerOf(artist), lifeDates(artist)].filter(Boolean).join(' · ')),
      toneMapped: false,
    })
  );
  vig.position.set(0, 2.55, D / 2 - 0.01);
  vig.rotation.y = Math.PI;
  shell.add(vig);
  scene.add(shell);

  // ---------- paintings ----------
  const texLoader = new THREE.TextureLoader();
  texLoader.crossOrigin = 'anonymous';
  const pickables = [];
  let loadedCount = 0;
  const progressEl = document.getElementById('entry-progress');
  const bumpProgress = () => {
    loadedCount++;
    progressEl.style.width = Math.round(loadedCount / artist.paintings.length * 100) + '%';
  };

  function loadPaintingTexture(p, i) {
    let url = p.image.thumb640;
    if (DEBUG === 'badimg' && i === 0) url = 'https://upload.wikimedia.org/nonexistent.jpg';
    return new Promise((resolve) => {
      const tryLoad = (u, next) => texLoader.load(u,
        (t) => { t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; resolve(t); },
        undefined,
        next);
      tryLoad(url, () =>
        tryLoad(filePathUrl(p.image.file, 640), () =>
          resolve(placeholderTexture(p.title))));
    }).then((t) => { bumpProgress(); return t; });
  }

  const gilt = artist.periods.some((pd) => GILT_PERIODS.has(pd));
  const fMat = frameMaterial(gilt);
  const mMat = matteMaterial();
  const FRAME = 0.07, FDEPTH = 0.075, MATTE = 0.035;

  const texturesReady = Promise.all(artist.paintings.map((p, i) => loadPaintingTexture(p, i)))
    .then((textures) => {
      room.placements.forEach((pl) => {
        const t = textures[pl.index];
        const g = new THREE.Group();
        const [x, y, z] = pl.pos;
        g.position.set(x, y, z);
        g.rotation.y = pl.rotY;

        // frame: four box segments merged into one geometry (one draw call)
        const fw = pl.w + (MATTE + FRAME) * 2;
        const fh = pl.h + (MATTE + FRAME) * 2;
        const seg = (bw, bh, bx, by) => {
          const box = new THREE.BoxGeometry(bw, bh, FDEPTH);
          box.translate(bx, by, FDEPTH / 2);
          return box;
        };
        const frameGeo = mergeGeometries([
          seg(fw, FRAME, 0, fh / 2 - FRAME / 2),
          seg(fw, FRAME, 0, -fh / 2 + FRAME / 2),
          seg(FRAME, fh - FRAME * 2, -fw / 2 + FRAME / 2, 0),
          seg(FRAME, fh - FRAME * 2, fw / 2 - FRAME / 2, 0),
        ]);
        const frame = new THREE.Mesh(frameGeo, fMat);
        frame.castShadow = true;
        g.add(frame);

        // matte board, slightly proud of the wall
        const matte = new THREE.Mesh(
          new THREE.BoxGeometry(pl.w + MATTE * 2, pl.h + MATTE * 2, 0.02), mMat);
        matte.position.z = 0.025;
        g.add(matte);

        // the canvas itself
        const canvas = new THREE.Mesh(new THREE.PlaneGeometry(pl.w, pl.h), canvasMaterial(t));
        canvas.position.z = 0.037;
        canvas.userData.paintingIndex = pl.index;
        canvas.userData.title = pl.painting.title;
        g.add(canvas);
        pickables.push(canvas);

        scene.add(g);
        pl.group = g;
      });
    });

  // ---------- lighting ----------
  const rig = buildLighting(scene, room, room.placements, quality);

  // ---------- controls ----------
  const controls = createControls(camera, renderer.domElement, room);
  const hud = document.getElementById('hud');
  const crosshair = document.getElementById('crosshair');
  const tooltip = document.getElementById('tooltip');

  const inspector = createInspector(artist, {
    onOpen: () => { controls.unlock(); tooltip.hidden = true; },
    onClose: () => { if (!quality.mobile && DEBUG !== 'orbit') setTimeout(() => controls.lock(), 60); },
  });

  // ---------- raycasting ----------
  const raycaster = new THREE.Raycaster();
  raycaster.far = 14;
  const center = new THREE.Vector2(0, 0);
  let hovered = null;

  function pick(nx, ny) {
    raycaster.setFromCamera(new THREE.Vector2(nx, ny), camera);
    const hits = raycaster.intersectObjects(pickables, false);
    return hits.length ? hits[0].object : null;
  }

  function updateHover() {
    if (inspector.isOpen()) return;
    const obj = pick(0, 0);
    const idx = obj ? obj.userData.paintingIndex : null;
    if (idx !== (hovered?.userData.paintingIndex ?? null)) {
      hovered = obj;
      rig.setGlow(idx);
      crosshair.classList.toggle('on-target', !!obj);
      if (obj) {
        tooltip.textContent = obj.userData.title;
        tooltip.hidden = false;
      } else {
        tooltip.hidden = true;
      }
    }
  }

  renderer.domElement.addEventListener('click', () => {
    if (quality.mobile || DEBUG === 'orbit' || inspector.isOpen()) return;
    if (!controls.state.locked) { controls.lock(); return; }
    if (hovered) inspector.open(hovered.userData.paintingIndex);
  });

  // mobile: tap to inspect + teleport strip
  if (quality.mobile) {
    initTouch(controls, renderer.domElement, (sx, sy) => {
      if (inspector.isOpen()) return;
      const obj = pick((sx / innerWidth) * 2 - 1, -(sy / innerHeight) * 2 + 1);
      if (obj) inspector.open(obj.userData.paintingIndex);
    });
    buildStrip();
  }

  function buildStrip() {
    const strip = document.createElement('div');
    strip.className = 'strip';
    artist.paintings.forEach((p, i) => {
      const img = document.createElement('img');
      img.src = p.image.thumb640;
      img.alt = p.title;
      img.addEventListener('click', () => walkTo(i));
      strip.appendChild(img);
    });
    hud.appendChild(strip);
  }

  function walkTo(index) {
    const pl = room.placements.find((x) => x.index === index);
    if (!pl) return;
    const [x, y, z] = pl.pos;
    const dist = Math.max(1.6, Math.min(3.2, pl.w * 1.25 + 0.8));
    const tx = x + Math.sin(pl.rotY) * dist;
    const tz = z + Math.cos(pl.rotY) * dist;
    controls.glideTo(new THREE.Vector3(tx, EYE, tz), pl.rotY + Math.PI);
  }

  // ---------- entry ----------
  const entry = document.getElementById('entry');
  const entryBtn = document.getElementById('entry-btn');
  if (!hasPointerLock()) {
    document.getElementById('entry-help').innerHTML =
      'Left thumb to walk · right thumb to look · tap a painting to inspect';
  }

  await texturesReady;
  entryBtn.disabled = false;
  entryBtn.textContent = 'Enter the gallery →';
  const start = () => {
    entry.classList.add('leaving');
    setTimeout(() => entry.remove(), 700);
    hud.hidden = false;
    if (!quality.mobile && DEBUG !== 'orbit') controls.lock();
  };
  entryBtn.addEventListener('click', start);
  if (DEBUG === 'orbit') start();

  // ---------- loop ----------
  addEventListener('resize', () => {
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight);
  });

  const timer = new THREE.Timer();
  const fps = { frames: 0, t0: performance.now(), value: 0 };
  let orbitT = 0;

  renderer.setAnimationLoop(() => {
    timer.update();
    const dt = Math.min(0.05, timer.getDelta());
    if (DEBUG === 'orbit') {
      orbitT += dt * 0.12;
      const r = Math.min(W, D) * 0.27;
      camera.position.set(Math.sin(orbitT) * r, EYE, Math.cos(orbitT) * r);
      camera.lookAt(Math.sin(orbitT + 1.6) * W * 0.4, 1.55, Math.cos(orbitT + 1.6) * D * 0.4);
    } else {
      controls.step(dt);
    }
    rig.update(camera.position, performance.now());
    updateHover();
    renderer.render(scene, camera);
    fps.frames++;
    const now = performance.now();
    if (now - fps.t0 > 1000) {
      fps.value = fps.frames * 1000 / (now - fps.t0);
      fps.frames = 0;
      fps.t0 = now;
    }
  });

  if (DEBUG) {
    window.__museum = { renderer, scene, camera, room, rig, artist, inspector, fps, walkTo, controls };
  }
}

boot().catch((err) => {
  console.error(err);
  document.getElementById('entry-sub').textContent = 'Something went wrong loading this room.';
});
