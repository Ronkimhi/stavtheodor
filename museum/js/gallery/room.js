// Room solver: from a list of paintings to room dimensions and wall placements.
// Units are metres. Walls: 0 = north (-z), 1 = east (+x), 2 = south (+z, entry), 3 = west (-x).

export const WALL_H = 4.2;
export const HANG_CENTER = 1.55;
export const EYE = 1.65;

const GAP = 2.1;        // wall run per painting beyond its width
const DOOR = 1.8;       // reserved door zone on the entry wall
const MIN_SIDE = 7.0;

export function paintingSize(p) {
  // Real dimensions when Wikidata had them, else normalize the long edge to 1.4m.
  let w, h;
  if (p.cm && p.cm.w >= 20 && p.cm.h >= 20) {
    w = p.cm.w / 100;
    h = p.cm.h / 100;
  } else {
    const aspect = (p.image.pxW && p.image.pxH) ? p.image.pxW / p.image.pxH : 1.3;
    if (aspect >= 1) { w = 1.4; h = 1.4 / aspect; }
    else { h = 1.4; w = 1.4 * aspect; }
  }
  // keep hangable: clamp height, preserve aspect
  const maxH = 2.6, minH = 0.55, maxW = 3.4;
  if (h > maxH) { w *= maxH / h; h = maxH; }
  if (h < minH) { w *= minH / h; h = minH; }
  if (w > maxW) { h *= maxW / w; w = maxW; }
  return { w, h };
}

export function solveRoom(paintings) {
  const sizes = paintings.map(paintingSize);
  const run = sizes.reduce((s, sz) => s + sz.w + GAP, 0);

  // Perimeter needed: run + door zone. Room aspect ~ 1.35 : 1.
  const halfPerim = Math.max(run + DOOR, 4 * MIN_SIDE) / 2;
  let W = Math.max(MIN_SIDE, halfPerim * (1.35 / 2.35));
  let D = Math.max(MIN_SIDE, halfPerim - W);
  W = Math.round(W * 10) / 10;
  D = Math.round(D * 10) / 10;

  // Wall runs (usable length per wall, corners padded 0.9m each side).
  const walls = [
    { id: 0, len: W - 1.8 },              // north
    { id: 1, len: D - 1.8 },              // east
    { id: 2, len: W - 1.8 - DOOR },       // south (entry, minus door)
    { id: 3, len: D - 1.8 },              // west
  ];

  // Distribute paintings in hang order, proportionally to wall length.
  const totalLen = walls.reduce((s, w) => s + w.len, 0);
  let idx = 0;
  const placements = [];
  for (const wall of walls) {
    const quota = wall === walls[walls.length - 1]
      ? paintings.length - idx
      : Math.min(
          paintings.length - idx,
          Math.max(0, Math.round(paintings.length * (wall.len / totalLen)))
        );
    const group = paintings.slice(idx, idx + quota);
    const groupSizes = sizes.slice(idx, idx + quota);
    idx += quota;
    if (!group.length) continue;

    const groupRun = groupSizes.reduce((s, sz) => s + sz.w, 0);
    const space = (wall.len - groupRun) / (group.length + 1);
    let cursor = -wall.len / 2;
    group.forEach((p, i) => {
      const sz = groupSizes[i];
      cursor += space + sz.w / 2;
      placements.push({
        painting: p,
        index: paintings.indexOf(p),
        wall: wall.id,
        along: cursor,          // offset along the wall from its center
        w: sz.w,
        h: sz.h,
      });
      cursor += sz.w / 2;
    });
  }

  // Convert wall-relative to world transforms.
  for (const pl of placements) {
    switch (pl.wall) {
      case 0: pl.pos = [pl.along, HANG_CENTER, -D / 2]; pl.rotY = 0; break;
      case 1: pl.pos = [W / 2, HANG_CENTER, pl.along]; pl.rotY = -Math.PI / 2; break;
      case 2: {
        // mirror so hang order runs continuously, then part around the door at x=0
        let x = -pl.along;
        x += x >= 0 ? DOOR / 2 : -DOOR / 2;
        pl.pos = [x, HANG_CENTER, D / 2];
        pl.rotY = Math.PI;
        break;
      }
      case 3: pl.pos = [-W / 2, HANG_CENTER, -pl.along]; pl.rotY = Math.PI / 2; break;
    }
  }

  return {
    W, D, H: WALL_H,
    placements,
    // spawn just inside the door on the south wall, facing into the room (-z)
    spawn: { x: 0, z: D / 2 - 1.4, yaw: 0 },
    bounds: { x: W / 2 - 0.55, z: D / 2 - 0.55 },
  };
}
