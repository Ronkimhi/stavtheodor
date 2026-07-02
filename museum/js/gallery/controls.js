// Movement: PointerLock + WASD on desktop, dual-zone touch + teleport strip on mobile.

import * as THREE from 'three';
import { PointerLockControls } from 'three/addons/controls/PointerLockControls.js';
import { EYE } from './room.js';

export function hasPointerLock() {
  return 'requestPointerLock' in document.body && !matchMedia('(pointer: coarse)').matches;
}

export function createControls(camera, dom, room) {
  const state = {
    locked: false,
    keys: new Set(),
    vel: new THREE.Vector3(),
    touchMove: { x: 0, y: 0 },
    yaw: room.spawn.yaw,
    pitch: 0,
    glide: null,
    usesPointerLock: hasPointerLock(),
  };

  camera.position.set(room.spawn.x, EYE, room.spawn.z);
  camera.rotation.set(0, room.spawn.yaw, 0, 'YXZ');

  let plc = null;
  if (state.usesPointerLock) {
    plc = new PointerLockControls(camera, dom);
    plc.addEventListener('lock', () => { state.locked = true; });
    plc.addEventListener('unlock', () => { state.locked = false; });
  }

  addEventListener('keydown', (e) => {
    if (e.target instanceof Element && e.target.closest('input, textarea')) return;
    state.keys.add(e.code);
    state.glide = null; // walking takes over from a strip glide
  });
  addEventListener('keyup', (e) => state.keys.delete(e.code));
  addEventListener('blur', () => state.keys.clear());

  const SPEED = 2.3, ACCEL = 14, DAMP = 8.5;
  const fwd = new THREE.Vector3(), right = new THREE.Vector3(), wish = new THREE.Vector3();

  function step(dt) {
    // glide (teleport strip): tween position + yaw, overrides free walk
    if (state.glide) {
      const g = state.glide;
      g.t = Math.min(1, g.t + dt / g.ms * 1000);
      const k = 1 - Math.pow(1 - g.t, 3);
      camera.position.lerpVectors(g.fromPos, g.toPos, k);
      const yaw = g.fromYaw + shortestAngle(g.fromYaw, g.toYaw) * k;
      if (state.usesPointerLock && plc) {
        camera.rotation.set(0, yaw, 0, 'YXZ');
      } else {
        state.yaw = yaw; state.pitch *= (1 - k * 0.5);
        camera.rotation.set(state.pitch, state.yaw, 0, 'YXZ');
      }
      if (g.t >= 1) state.glide = null;
      return;
    }

    // touch look (mobile)
    if (!state.usesPointerLock) {
      camera.rotation.set(state.pitch, state.yaw, 0, 'YXZ');
    }

    camera.getWorldDirection(fwd);
    fwd.y = 0; fwd.normalize();
    right.crossVectors(fwd, new THREE.Vector3(0, 1, 0)).normalize().negate();

    wish.set(0, 0, 0);
    if (state.keys.has('KeyW') || state.keys.has('ArrowUp')) wish.add(fwd);
    if (state.keys.has('KeyS') || state.keys.has('ArrowDown')) wish.sub(fwd);
    if (state.keys.has('KeyA') || state.keys.has('ArrowLeft')) wish.add(right);
    if (state.keys.has('KeyD') || state.keys.has('ArrowRight')) wish.sub(right);
    // virtual stick
    if (state.touchMove.x || state.touchMove.y) {
      wish.addScaledVector(fwd, -state.touchMove.y);
      wish.addScaledVector(right, -state.touchMove.x);
    }

    // keyboard-only turning (mouse-look needs pointer lock; Q/E never does)
    const TURN = 1.7;
    if (state.keys.has('KeyQ')) camera.rotation.y += TURN * dt;
    if (state.keys.has('KeyE')) camera.rotation.y -= TURN * dt;
    if (!state.usesPointerLock && (state.keys.has('KeyQ') || state.keys.has('KeyE'))) {
      state.yaw = camera.rotation.y;
    }

    if (wish.lengthSq() > 0) {
      wish.normalize().multiplyScalar(SPEED);
      state.vel.lerp(wish, Math.min(1, ACCEL * dt));
    } else {
      state.vel.multiplyScalar(Math.max(0, 1 - DAMP * dt));
    }

    camera.position.addScaledVector(state.vel, dt);
    camera.position.x = THREE.MathUtils.clamp(camera.position.x, -room.bounds.x, room.bounds.x);
    camera.position.z = THREE.MathUtils.clamp(camera.position.z, -room.bounds.z, room.bounds.z);
    camera.position.y = EYE;
  }

  function glideTo(pos, yaw, ms = 900) {
    state.glide = {
      fromPos: camera.position.clone(),
      toPos: pos.clone(),
      fromYaw: state.usesPointerLock ? camera.rotation.y : state.yaw,
      toYaw: yaw,
      t: 0, ms,
    };
  }

  return {
    state, plc, step, glideTo,
    lock: () => plc?.lock(),
    unlock: () => plc?.unlock(),
  };
}

function shortestAngle(a, b) {
  let d = (b - a) % (Math.PI * 2);
  if (d > Math.PI) d -= Math.PI * 2;
  if (d < -Math.PI) d += Math.PI * 2;
  return d;
}

// Mobile: left half = move stick, right half = look; short tap = inspect.
export function initTouch(controlsApi, dom, onTap) {
  const root = document.getElementById('touch-root');
  root.innerHTML = '<div class="stick" id="stick"><div class="stick-knob" id="knob"></div></div>';
  const stick = document.getElementById('stick');
  const knob = document.getElementById('knob');
  const st = controlsApi.state;

  let movePtr = null, lookPtr = null, lookLast = null, tapInfo = null;

  dom.addEventListener('pointerdown', (e) => {
    if (e.pointerType !== 'touch') return;
    st.glide = null; // touching the world cancels a strip glide
    if (e.clientX < innerWidth * 0.45 && e.clientY > innerHeight * 0.4 && movePtr === null) {
      movePtr = e.pointerId;
      stickFrom(e);
    } else if (lookPtr === null) {
      lookPtr = e.pointerId;
      lookLast = { x: e.clientX, y: e.clientY };
      tapInfo = { x: e.clientX, y: e.clientY, t: performance.now() };
    }
  });
  dom.addEventListener('pointermove', (e) => {
    if (e.pointerId === movePtr) stickFrom(e);
    else if (e.pointerId === lookPtr) {
      st.yaw -= (e.clientX - lookLast.x) * 0.0042;
      st.pitch = Math.max(-1.35, Math.min(1.35, st.pitch - (e.clientY - lookLast.y) * 0.0038));
      lookLast = { x: e.clientX, y: e.clientY };
      if (tapInfo && Math.hypot(e.clientX - tapInfo.x, e.clientY - tapInfo.y) > 12) tapInfo = null;
    }
  });
  const end = (e) => {
    if (e.pointerId === movePtr) {
      movePtr = null;
      st.touchMove = { x: 0, y: 0 };
      knob.style.transform = '';
    }
    if (e.pointerId === lookPtr) {
      lookPtr = null;
      if (tapInfo && performance.now() - tapInfo.t < 260) onTap(tapInfo.x, tapInfo.y);
      tapInfo = null;
    }
  };
  dom.addEventListener('pointerup', end);
  dom.addEventListener('pointercancel', end);

  function stickFrom(e) {
    const r = stick.getBoundingClientRect();
    const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
    let dx = (e.clientX - cx) / (r.width / 2);
    let dy = (e.clientY - cy) / (r.height / 2);
    const len = Math.hypot(dx, dy);
    if (len > 1) { dx /= len; dy /= len; }
    st.touchMove = { x: dx, y: dy };
    knob.style.transform = `translate(${dx * 30}px, ${dy * 30}px)`;
  }
}
