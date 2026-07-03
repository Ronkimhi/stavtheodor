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

// Mobile: bottom-left quadrant = move (stick recenters under the thumb),
// everywhere else = look drag; short tap = inspect.
export function initTouch(controlsApi, dom, onTap) {
  const root = document.getElementById('touch-root');
  root.innerHTML = '<div class="stick" id="stick"><div class="stick-knob" id="knob"></div></div>';
  const stick = document.getElementById('stick');
  const knob = document.getElementById('knob');
  const st = controlsApi.state;

  const RADIUS = 46;     // px of thumb travel for full walk speed
  const DEADZONE = 0.12; // fraction of RADIUS a resting thumb can wobble without drifting

  let movePtr = null, moveFrom = null, lookPtr = null, lookLast = null, tapInfo = null;

  // Belt and braces alongside touch-action: none on the canvas; older iOS Safari
  // still turns canvas drags into page scroll/bounce and cancels the pointer.
  const eat = (e) => e.preventDefault();
  dom.addEventListener('touchstart', eat, { passive: false });
  dom.addEventListener('touchmove', eat, { passive: false });
  dom.addEventListener('contextmenu', eat);

  dom.addEventListener('pointerdown', (e) => {
    if (e.pointerType !== 'touch') return;
    st.glide = null; // touching the world cancels a strip glide
    try { dom.setPointerCapture(e.pointerId); } catch (err) { /* pointer already gone */ }
    if (movePtr === null && e.clientX < innerWidth * 0.45 && e.clientY > innerHeight * 0.4) {
      movePtr = e.pointerId;
      moveFrom = { x: e.clientX, y: e.clientY };
      const half = stick.offsetWidth / 2 || 54;
      stick.style.left = Math.max(8, Math.min(innerWidth - half * 2 - 8, e.clientX - half)) + 'px';
      stick.style.top = Math.max(8, Math.min(innerHeight - half * 2 - 8, e.clientY - half)) + 'px';
      stick.classList.add('live');
      st.touchMove = { x: 0, y: 0 };
      knob.style.transform = '';
    } else if (lookPtr === null) {
      lookPtr = e.pointerId;
      lookLast = { x: e.clientX, y: e.clientY };
      // e.timeStamp is the input time; performance.now() here would add
      // main-thread jank and misclassify real taps as long presses
      tapInfo = { x: e.clientX, y: e.clientY, t: e.timeStamp };
    }
  });
  dom.addEventListener('pointermove', (e) => {
    if (e.pointerId === movePtr) stickFrom(e);
    else if (e.pointerId === lookPtr) {
      st.yaw -= (e.clientX - lookLast.x) * 0.005;
      st.pitch = Math.max(-1.35, Math.min(1.35, st.pitch - (e.clientY - lookLast.y) * 0.0042));
      lookLast = { x: e.clientX, y: e.clientY };
      if (tapInfo && Math.hypot(e.clientX - tapInfo.x, e.clientY - tapInfo.y) > 12) tapInfo = null;
    }
  });
  const end = (e) => {
    if (e.pointerId === movePtr) {
      movePtr = null;
      moveFrom = null;
      st.touchMove = { x: 0, y: 0 };
      stick.classList.remove('live');
      stick.style.left = '';
      stick.style.top = '';
      knob.style.transform = '';
    }
    if (e.pointerId === lookPtr) {
      lookPtr = null;
      if (tapInfo && e.timeStamp - tapInfo.t < 350) onTap(tapInfo.x, tapInfo.y);
      tapInfo = null;
    }
  };
  dom.addEventListener('pointerup', end);
  dom.addEventListener('pointercancel', end);

  function stickFrom(e) {
    let dx = (e.clientX - moveFrom.x) / RADIUS;
    let dy = (e.clientY - moveFrom.y) / RADIUS;
    let len = Math.hypot(dx, dy);
    if (len > 1) { dx /= len; dy /= len; len = 1; }
    knob.style.transform = `translate(${dx * 30}px, ${dy * 30}px)`;
    if (len < DEADZONE) {
      st.touchMove = { x: 0, y: 0 };
    } else {
      const scale = (len - DEADZONE) / (1 - DEADZONE) / len;
      st.touchMove = { x: dx * scale, y: dy * scale };
    }
  }
}
