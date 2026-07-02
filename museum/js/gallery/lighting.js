// Lighting rig: warm ambient + one spotlight per painting from the ceiling track.
// Shadow budget: only the few spots nearest the camera cast, re-picked on a throttle.

import * as THREE from 'three';

export function buildLighting(scene, room, placements, quality) {
  const rig = { spots: [], byIndex: new Map() };

  const hemi = new THREE.HemisphereLight(0xFFF6E8, 0x8A7A66, 0.5);
  scene.add(hemi);

  // faint ceiling bounce so the room never goes black between cones
  const amb = new THREE.AmbientLight(0xFFF2E0, 0.14);
  scene.add(amb);

  for (const pl of placements) {
    const spot = new THREE.SpotLight(0xFFE3C2);
    spot.intensity = 32 + pl.w * pl.h * 18; // scale with painting area
    spot.decay = 1.9;
    spot.penumbra = 0.55;

    const [px, py, pz] = pl.pos;
    const inward = 1.7; // track offset from the wall
    const lx = px + Math.sin(pl.rotY) * inward;
    const lz = pz + Math.cos(pl.rotY) * inward;
    spot.position.set(lx, room.H - 0.25, lz);
    // aim slightly below center so the pool reads centered on the canvas
    spot.target.position.set(px, py - 0.35, pz);
    scene.add(spot.target);

    const dist = Math.hypot(inward, room.H - 0.25 - py);
    const radius = Math.max(pl.w, pl.h) * 0.72 + 0.25;
    spot.angle = Math.min(Math.PI / 3.2, Math.atan2(radius, dist) * 1.08);

    spot.castShadow = false;
    spot.shadow.mapSize.set(quality.shadowMap, quality.shadowMap);
    spot.shadow.bias = -0.0004;
    spot.shadow.camera.near = 0.5;
    spot.shadow.camera.far = dist + 6;

    scene.add(spot);
    rig.spots.push({ spot, pos: new THREE.Vector3(px, py, pz), index: pl.index, base: spot.intensity });
    rig.byIndex.set(pl.index, rig.spots[rig.spots.length - 1]);
  }

  let lastPick = 0;
  rig.update = (camPos, t) => {
    if (t - lastPick < 500) return;
    lastPick = t;
    const sorted = [...rig.spots].sort(
      (a, b) => a.pos.distanceToSquared(camPos) - b.pos.distanceToSquared(camPos)
    );
    sorted.forEach((s, i) => {
      const want = i < quality.shadowCasters;
      if (s.spot.castShadow !== want) {
        s.spot.castShadow = want;
      }
    });
  };

  // hover glow: ease one painting's spot up 15%
  let glowing = null;
  rig.setGlow = (index) => {
    if (glowing === index) return;
    if (glowing !== null) {
      const prev = rig.byIndex.get(glowing);
      if (prev) prev.spot.intensity = prev.base;
    }
    glowing = index;
    if (index !== null) {
      const cur = rig.byIndex.get(index);
      if (cur) cur.spot.intensity = cur.base * 1.18;
    }
  };

  return rig;
}
