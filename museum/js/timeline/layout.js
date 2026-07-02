// World layout: piecewise-linear time scale + period lanes + artist rows.
// All positions are world px (CSS px at zoom scale 1).

// One muted, gallery-grade accent per period. Used for band tint/border,
// band label, artist dots and filter swatches.
export const PERIOD_COLORS = {
  'prehistoric-art':        '#6B5442', // cave umber
  'mesopotamia':            '#8F6F2E', // ziggurat clay gold
  'ancient-egypt':          '#2E8074', // faience teal
  'aegean':                 '#3E6B9E', // aegean blue
  'etruscan':               '#96522E', // etruscan red
  'archaic-greece':         '#B07437', // amphora terracotta
  'classical-greece':       '#77705C', // pentelic marble
  'late-classical-greece':  '#8A5A64', // rosso antico
  'hellenistic':            '#5E7D5A', // bronze patina
  'republican-rome':        '#6A5D50', // travertine
  'imperial-rome':          '#6D4A72', // imperial purple
  'medieval-gothic':        '#8A6A3B', // byzantine gold
  'early-renaissance':      '#A85F44', // terracotta
  'northern-renaissance':   '#6E7B4F', // moss green
  'high-renaissance':       '#9C4038', // venetian red
  'mannerism':              '#7D5470', // plum
  'baroque':                '#5C4632', // deep umber
  'rococo':                 '#B87D88', // powdered rose
  'neoclassicism':          '#5C6E8C', // slate blue
  'romanticism':            '#3F6E71', // storm teal
  'realism':                '#77693C', // field olive
  'impressionism':          '#5B7FA6', // plein-air blue
  'post-impressionism':     '#A87621', // sunflower ochre
  'symbolism-art-nouveau':  '#8A6796', // mauve
  'expressionism':          '#B4472F', // vermilion
  'cubism':                 '#726A5E', // faceted taupe
  'early-abstraction':      '#3F5DA8', // cobalt
  'surrealism':             '#3E8577', // sea green
  'abstract-expressionism': '#4A4440', // dripped charcoal
  'pop-art':                '#C24E7B', // magenta
  'contemporary':           '#5F7D86', // steel cyan
};

export function periodColor(id) {
  return PERIOD_COLORS[id] || '#A0815C';
}

export function withAlpha(hex, a) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`;
}

// mix toward ink for text-safe contrast on ivory
export function inked(hex, k = 0.25) {
  const n = parseInt(hex.slice(1), 16);
  const ink = [28, 26, 23];
  const c = [(n >> 16) & 255, (n >> 8) & 255, n & 255]
    .map((v, i) => Math.round(v * (1 - k) + ink[i] * k));
  return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
}

const SEGMENTS = [
  // [fromYear, pxPerYear] — denser where art history is denser
  [-38000, 0.006], // deep prehistory, heavily compressed
  [-10000, 0.03],  // the neolithic approach
  [-3500, 0.32],   // bronze-age civilizations
  [-750, 2.4],     // the Greek centuries earn their room
  [-100, 1.3],     // Rome
  [330, 0.32],     // late antiquity to the Gothic dawn
  [1180, 2.2],
  [1400, 4.2],   // the Renaissance centuries earn their room
  [1600, 6.0],
  [1850, 15.0],
  [1985, 8.0],
];
const END_YEAR = 2032;

const X_PAD = 90;
export const BAND_TOP = 130;
export const LANE_H = 242;   // 4 label rows + the summary line at the bottom
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
    const s = a.activeStart ?? home.start;
    const e = a.activeEnd ?? home.end;
    // blend career midpoint with the midpoint of the years actually spent
    // inside the movement, so long careers don't pile on the band edge
    const careerMid = (s + e) / 2;
    const inS = Math.max(s, home.start), inE = Math.min(e, home.end);
    const inMid = inS <= inE ? (inS + inE) / 2 : careerMid;
    const x = Math.max(home.x + 26, Math.min(home.x + home.w - 26,
      xForYear(0.45 * careerMid + 0.55 * inMid)));
    return { ...a, x, period: home };
  });

  // Row packing that models real label footprints: text extends right of the
  // dot, or LEFT when the node is flipped near the band's right edge.
  // Tier-1 shows compact names, so 130 world px covers the worst zoom.
  const EXTENT = 130;
  const PAD = 10;
  const ROWS = 4;
  const groups = new Map();
  for (const a of artists) {
    // text must stay inside the band: flip if the flipped label fits (keeps
    // the dot on the true year); in bands narrower than a label, pull the
    // dot inward instead.
    const L = a.period.x, R = a.period.x + a.period.w;
    a.flip = false;
    if (a.x + EXTENT > R - 14) {
      if (a.x - EXTENT >= L + 14) a.flip = true;
      else a.x = Math.max(L + 14, R - 14 - EXTENT);
    }
    if (!groups.has(a.period.id)) groups.set(a.period.id, []);
    groups.get(a.period.id).push(a);
  }
  for (const group of groups.values()) {
    group.sort((a, b) => a.x - b.x);
    const rowEnds = []; // rightmost occupied world x per row
    const spanOf = (a) => (a.flip
      ? [a.x - EXTENT, a.x + 16]
      : [a.x - 16, a.x + EXTENT]);
    for (const a of group) {
      let row = rowEnds.findIndex((end) => spanOf(a)[0] >= end + PAD);
      if (row === -1 && rowEnds.length < ROWS) {
        row = rowEnds.length;
        rowEnds.push(-Infinity);
      }
      if (row === -1) {
        // all rows blocked: slide right of the least-crowded row if the band
        // allows, else accept the row where the intrusion is smallest
        row = rowEnds.indexOf(Math.min(...rowEnds));
        const slid = rowEnds[row] + PAD + (a.flip ? EXTENT : 16);
        const maxX = a.period.x + a.period.w - 26;
        if (slid <= maxX) a.x = slid;
        else {
          a.x = maxX;
          a.flip = true;
          row = rowEnds.reduce((best, end, i) =>
            end < rowEnds[best] ? i : best, 0);
        }
      }
      rowEnds[row] = spanOf(a)[1];
      a.y = a.period.y + 56 + row * 39;
    }
  }

  // Year axis ticks: per-segment step chosen so labels sit >= ~110 world px
  // apart, from 20,000-year strides in deep prehistory down to 25-year ones
  // in the modern era. Year 0 does not exist and is skipped.
  const TICK_STEPS = [25, 50, 100, 250, 500, 1000, 2000, 5000, 10000, 20000];
  const ticks = [];
  const seenTick = new Set();
  for (const s of bp) {
    const step = TICK_STEPS.find((st) => st * s.ppy >= 110)
      ?? TICK_STEPS[TICK_STEPS.length - 1];
    const last = Math.min(s.y1, 2025);
    for (let y = Math.ceil(s.y0 / step) * step; y <= last; y += step) {
      if (y === 0 || seenTick.has(y)) continue;
      seenTick.add(y);
      ticks.push({ year: y, x: xForYear(y) });
    }
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
