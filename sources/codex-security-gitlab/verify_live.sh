#!/usr/bin/env bash
set -u
BASE="https://codex-security-gitlab-riset.irfansp.here.now"
SITE="$HOME/.hermes/cache/scratch/codex-security-gitlab/site"
echo "=== status / content-type / size ==="
for p in / /index.html /index-en.html /assets/style.css /nope.html; do
  printf '%s  %s\n' "$(curl -sS -o /dev/null -w '%{http_code} %{content_type} %{size_download}' -L --max-time 30 "$BASE$p")" "$p"
done
echo "=== served vs local ==="
for f in index.html index-en.html assets/style.css; do
  curl -sS -L --max-time 30 "$BASE/$f" -o "/tmp/live_${f##*/}"
done
python3 - "$SITE" <<'PY'
import pathlib, re, sys
site = pathlib.Path(sys.argv[1])
inj = re.compile(r'^\s*<meta (property="og:|name="twitter:)')
for f in ("index.html", "index-en.html"):
    loc = (site / f).read_text().splitlines()
    live = pathlib.Path("/tmp/live_" + f).read_text().splitlines()
    inj_lines = [l for l in live if inj.match(l)]
    stripped = [l for l in live if not inj.match(l)]
    print(f"{f}: injected og/twitter meta lines = {len(inj_lines)} | rest byte-identical = {loc == stripped}")
    if loc != stripped:
        for a, b in zip(loc, stripped):
            if a != b:
                print("   first diff:\n    local:", a[:120], "\n    live :", b[:120]); break
loc = (site / "assets" / "style.css").read_bytes()
live = pathlib.Path("/tmp/live_style.css").read_bytes()
print("assets/style.css byte-identical =", loc == live)
PY
echo "=== served <title> ==="
curl -sS -L --max-time 30 "$BASE/index.html" | grep -o '<title>[^<]*</title>'
curl -sS -L --max-time 30 "$BASE/index-en.html" | grep -o '<title>[^<]*</title>'
