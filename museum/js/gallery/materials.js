// PBR materials, procedural wood floor, env map, placeholder canvases.

import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

export function makeEnvironment(renderer, scene) {
  const pmrem = new THREE.PMREMGenerator(renderer);
  const env = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environment = env;
  scene.environmentIntensity = 0.32;
  pmrem.dispose();
}

// ---- procedural oak floor (keeps the repo free of binary textures) ----

function woodCanvases(size = 1024, planks = 7) {
  const diff = document.createElement('canvas');
  diff.width = diff.height = size;
  const rough = document.createElement('canvas');
  rough.width = rough.height = size;
  const dctx = diff.getContext('2d');
  const rctx = rough.getContext('2d');

  const pw = size / planks;
  let seed = 7;
  const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;

  for (let i = 0; i < planks; i++) {
    // warm oak, slight per-plank variation
    const l = 46 + rnd() * 10;
    const hue = 28 + rnd() * 6;
    const sat = 26 + rnd() * 8;
    dctx.fillStyle = `hsl(${hue}, ${sat}%, ${l}%)`;
    dctx.fillRect(i * pw, 0, pw, size);
    rctx.fillStyle = `hsl(0, 0%, ${58 + rnd() * 8}%)`;
    rctx.fillRect(i * pw, 0, pw, size);

    // grain: sinuous vertical strands
    const strands = 26;
    for (let g = 0; g < strands; g++) {
      const gx = i * pw + rnd() * pw;
      const dark = rnd() < 0.25;
      dctx.strokeStyle = `hsla(${hue - 4}, ${sat + 6}%, ${l - (dark ? 16 : 8)}%, ${0.16 + rnd() * 0.2})`;
      dctx.lineWidth = 0.6 + rnd() * 1.8;
      dctx.beginPath();
      let x = gx;
      dctx.moveTo(x, 0);
      for (let y = 0; y <= size; y += size / 14) {
        x += (rnd() - 0.5) * 7;
        dctx.lineTo(x, y);
      }
      dctx.stroke();
      rctx.strokeStyle = `hsla(0, 0%, ${40 + rnd() * 20}%, 0.25)`;
      rctx.lineWidth = dctx.lineWidth;
      rctx.stroke();
    }

    // occasional knot
    if (rnd() < 0.6) {
      const kx = i * pw + pw * (0.25 + rnd() * 0.5);
      const ky = size * rnd();
      const kr = 4 + rnd() * 9;
      const grad = dctx.createRadialGradient(kx, ky, 1, kx, ky, kr);
      grad.addColorStop(0, `hsla(${hue - 8}, ${sat}%, ${l - 24}%, 0.8)`);
      grad.addColorStop(1, 'transparent');
      dctx.fillStyle = grad;
      dctx.fillRect(kx - kr, ky - kr, kr * 2, kr * 2);
    }

    // plank seams
    dctx.fillStyle = 'rgba(30, 20, 12, 0.55)';
    dctx.fillRect(i * pw - 1, 0, 2, size);
    rctx.fillStyle = 'rgba(255, 255, 255, 0.5)'; // seams rougher
    rctx.fillRect(i * pw - 1, 0, 2, size);
    // butt joints
    const joints = 2 + Math.floor(rnd() * 2);
    for (let j = 0; j < joints; j++) {
      const jy = size * rnd();
      dctx.fillStyle = 'rgba(30, 20, 12, 0.4)';
      dctx.fillRect(i * pw, jy, pw, 1.6);
    }
  }
  return { diff, rough };
}

export function makeFloorMaterial(anisotropy) {
  const { diff, rough } = woodCanvases();
  const map = new THREE.CanvasTexture(diff);
  const roughMap = new THREE.CanvasTexture(rough);
  for (const t of [map, roughMap]) {
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.repeat.set(3, 3);
    t.anisotropy = anisotropy;
  }
  map.colorSpace = THREE.SRGBColorSpace;
  return new THREE.MeshStandardMaterial({
    map,
    roughnessMap: roughMap,
    roughness: 0.38,
    metalness: 0.0,
    envMapIntensity: 0.55,
  });
}

export const wallMaterial = () => new THREE.MeshStandardMaterial({
  color: 0xF6F2EA, roughness: 0.92, metalness: 0, envMapIntensity: 0.25,
});

export const ceilingMaterial = () => new THREE.MeshStandardMaterial({
  color: 0xFBF9F4, roughness: 0.95, metalness: 0,
});

export const trimMaterial = () => new THREE.MeshStandardMaterial({
  color: 0xEFE9DD, roughness: 0.6, metalness: 0, envMapIntensity: 0.3,
});

export function frameMaterial(gilt = false) {
  return gilt
    ? new THREE.MeshPhysicalMaterial({
        color: 0xA0815C, metalness: 0.85, roughness: 0.34,
        clearcoat: 0.5, clearcoatRoughness: 0.3, envMapIntensity: 0.9,
      })
    : new THREE.MeshPhysicalMaterial({
        color: 0x241E17, metalness: 0.05, roughness: 0.42,
        clearcoat: 0.35, clearcoatRoughness: 0.25, envMapIntensity: 0.7,
      });
}

export const matteMaterial = () => new THREE.MeshStandardMaterial({
  color: 0xF7F3EA, roughness: 0.85, metalness: 0,
});

export function canvasMaterial(texture) {
  return new THREE.MeshStandardMaterial({
    map: texture, roughness: 0.62, metalness: 0, envMapIntensity: 0.18,
  });
}

export const benchMaterial = () => new THREE.MeshPhysicalMaterial({
  color: 0x2A241D, roughness: 0.35, metalness: 0.1,
  clearcoat: 0.4, clearcoatRoughness: 0.3, envMapIntensity: 0.6,
});

// Ivory placeholder with the painting's title, for images that fail to load.
export function placeholderTexture(title) {
  const c = document.createElement('canvas');
  c.width = 640; c.height = 480;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#F4F0E7';
  ctx.fillRect(0, 0, 640, 480);
  ctx.strokeStyle = 'rgba(28,26,23,0.25)';
  ctx.strokeRect(24, 24, 592, 432);
  ctx.fillStyle = '#4A463F';
  ctx.font = 'italic 30px "Cormorant Garamond", Georgia, serif';
  ctx.textAlign = 'center';
  const words = String(title || 'Untitled').split(' ');
  const lines = [];
  let line = '';
  for (const w of words) {
    if ((line + ' ' + w).trim().length > 30) { lines.push(line.trim()); line = w; }
    else line += ' ' + w;
  }
  lines.push(line.trim());
  lines.slice(0, 5).forEach((l, i) => ctx.fillText(l, 320, 210 + i * 40));
  ctx.font = '17px "Cormorant Garamond", Georgia, serif';
  ctx.fillStyle = '#A0815C';
  ctx.fillText('image unavailable', 320, 420);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

// Wall vignette: artist name by the door, drawn once on a canvas.
export function vignetteTexture(name, sub) {
  const c = document.createElement('canvas');
  c.width = 1024; c.height = 512;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#F6F2EA';
  ctx.fillRect(0, 0, 1024, 512);
  ctx.fillStyle = '#1C1A17';
  ctx.textAlign = 'center';
  ctx.font = '500 72px "Cormorant Garamond", Georgia, serif';
  const upper = String(name).toUpperCase().split('').join(' ');
  ctx.fillText(upper, 512, 230, 940);
  ctx.fillStyle = '#A0815C';
  ctx.font = 'italic 34px "Cormorant Garamond", Georgia, serif';
  ctx.fillText(sub || '', 512, 300, 900);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
