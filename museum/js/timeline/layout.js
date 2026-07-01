// World layout: piecewise-linear time scale + period lanes + artist rows.
// All positions are world px (CSS px at zoom scale 1).

const SEGMENTS = [
  // [fromYear, pxPerYear] — denser where art history is denser
  [1180, 2.3],
  [1600, 6.0],
  [1850, 15.0],
  [1985, 8.0],
];
const END_YEAR = 2032;

const X_PAD = 90;
export const BAND_TOP = 130;
export const LANE_H = 215;
export const LANE_GAP = 26;

const bp = [];
{
  let x = X_PAD;
  for (let i = 0; i < SEGMENTS.length; i++) {
    const [y0, ppy] = SEGMENTS[i];
    const y1 = i + 1 < SEGMENTS.length ? SEGMENTS[i + 1][0] : END_YEAR;
    bp.push({ y0, y1, ppy, x0: x });
    x += (y1 - y0) * ppy;
  }
}

export function xForYear(year) {
  const y = Math.max(SEGMENTS[0][0], Math.min(END_YEAR, year));
  for (const s of bp) {
    if (y <= s.y1) return s.x0 + (y - s.y0) * s.ppy;
  }
  const last = bp[bp.length - 1];
  return last.x0 + (last.y1 - last.y0) * last.ppy;
}

export function layout(index) {
  const periods = index.periods.map((p) => {
    const x = xForYear(p.start);
    return {
      ...p,
      x,
      w: xForYear(p.end) - x,
      y: BAND_TOP + p.lane * (LANE_H + LANE_GAP),
      h: LANE_H,
    };
  });
  const byId = Object.fromEntries(periods.map((p) => [p.id, p]));

  // Artist nodes: x at active-years midpoint, rows resolve x collisions per band.
  const artists = index.artists.map((a) => {
    const home = byId[a.periods[0]];
    const mid = ((a.activeStart ?? home.start) + (a.activeEnd ?? home.end)) / 2;
    // clamp into the band before collision rows are assigned
    const x = Math.max(home.x + 26, Math.min(home.x + home.w - 26, xForYear(mid)));
    return { ...a, x, period: home };
  });

  const MIN_GAP = 132; // world px between node anchors in the same row
  const groups = new Map();
  for (const a of artists) {
    if (!groups.has(a.period.id)) groups.set(a.period.id, []);
    groups.get(a.period.id).push(a);
  }
  for (const group of groups.values()) {
    group.sort((a, b) => a.x - b.x);
    const rowEnds = [];
    for (const a of group) {
      let row = rowEnds.findIndex((end) => a.x - end >= MIN_GAP);
      if (row === -1) {
        row = rowEnds.length;
        rowEnds.push(a.x);
      } else {
        rowEnds[row] = a.x;
      }
      // 4 vertical slots fit the band; if a 5th row is ever needed, nudge the
      // anchor right instead of wrapping onto an occupied slot.
      if (row > 3) {
        a.x = rowEnds[row % 4] + MIN_GAP;
        rowEnds[row % 4] = a.x;
        rowEnds.pop();
        row = row % 4;
      }
      a.y = a.period.y + 58 + row * 40;
    }
  }

  // Year axis ticks every 50y before 1850, every 25y after.
  const ticks = [];
  for (let y = 1200; y <= 2025; y += y < 1850 ? 50 : 25) {
    ticks.push({ year: y, x: xForYear(y) });
  }

  const maxLane = Math.max(...periods.map((p) => p.lane));
  return {
    periods,
    artists,
    ticks,
    world: {
      w: xForYear(END_YEAR) + X_PAD,
      h: BAND_TOP + (maxLane + 1) * (LANE_H + LANE_GAP) + 90,
    },
  };
}
