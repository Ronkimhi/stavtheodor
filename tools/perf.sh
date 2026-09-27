#!/usr/bin/env bash
# Lighthouse on the built tree, served locally: mobile and desktop, for the homepage, the New Jersey
# landing page and one post. Writes JSON reports and prints score, LCP, CLS and TBT per run.
#
#   tools/perf.sh [label] [more paths...]        label names the report set (default: the date)
#   BASE=https://stavtheodor.com tools/perf.sh live   run against production instead of the local tree
#
# Needs node, the global Playwright install (npm i -g playwright; npx playwright install chromium) and
# npx (it downloads lighthouse on first use). Lighthouse attaches to a Chromium that Playwright launches
# (--port): letting Lighthouse launch Chrome or Chromium itself stopped painting on this machine
# (NO_FCP, 2026-09-26), while Playwright's launch flags keep rendering in the background.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="${1:-$(date +%Y-%m-%d)}"; shift || true
PAGES=("/" "/art-curator-new-jersey/" "/radar/soho-lerma-ackermann/" "$@")
OUT="$ROOT/.perf/$LABEL"; mkdir -p "$OUT"
freeport() { python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()'; }
CDP_PORT="$(freeport)"
NODE_PATH="$(npm root -g)" node -e "
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--remote-debugging-port=$CDP_PORT'] });
  const bye = () => b.close().then(() => process.exit(0));
  process.on('SIGTERM', bye); process.on('SIGINT', bye);
  setInterval(() => {}, 1000);
})();
" &
BROWSER_PID=$!
SERVER_PID=""
if [ -z "${BASE:-}" ]; then
  PORT="$(freeport)"
  (cd "$ROOT" && exec python3 -m http.server "$PORT" --bind 127.0.0.1 >/dev/null 2>&1) &
  SERVER_PID=$!
  BASE="http://127.0.0.1:$PORT"
fi
trap 'kill $BROWSER_PID $SERVER_PID 2>/dev/null || true' EXIT
sleep 3
printf '%-34s %-8s %6s %8s %7s %8s\n' page form score LCP_s CLS TBT_ms
for p in "${PAGES[@]}"; do
  for form in mobile desktop; do
    name="$(echo "${p#/}" | tr '/' '-' | sed 's/^$/home/; s/-$//')-$form"
    if [ "$form" = desktop ]; then preset="--preset=desktop"; else preset="--form-factor=mobile"; fi
    npx -y lighthouse "$BASE$p" --quiet --port="$CDP_PORT" --only-categories=performance \
      $preset --output=json --output-path="$OUT/$name.json" >/dev/null 2>&1 || { echo "$p $form: lighthouse failed"; continue; }
    python3 -c "import json,sys; r=json.load(open(sys.argv[1])); e=r.get('runtimeError'); sys.exit(1 if e else 0)" "$OUT/$name.json" || { echo "$p $form: $(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['runtimeError']['code'])" "$OUT/$name.json")"; continue; }
    python3 - "$OUT/$name.json" "$p" "$form" <<'PY'
import json, sys
r = json.load(open(sys.argv[1])); a = r['audits']
score = round(r['categories']['performance']['score'] * 100)
print(f"{sys.argv[2]:<34} {sys.argv[3]:<8} {score:6d} {a['largest-contentful-paint']['numericValue']/1000:8.2f} {a['cumulative-layout-shift']['numericValue']:7.3f} {a['total-blocking-time']['numericValue']:8.0f}")
PY
  done
done
echo "reports: $OUT"
