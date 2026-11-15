#!/usr/bin/env bash
# Render the OG project at N fps in 3 parallel chunks and score it against the reel.
# usage: parity_render.sh <label> [fps=2] [from=0] [to=33.067]
set -u
LABEL=$1; FPS=${2:-2}; FROM=${3:-0}; TO=${4:-33.067}
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=/home/user/tpl/an/parity
FR=$OUT/frames_$LABEL
FT="/home/user/tpl/x/psych/The Psychology Trick/The Psychology Trick"
mkdir -p "$FR"
python3 - "$FROM" "$TO" > /tmp/parity_chunks.txt <<'EOF'
import sys
a,b=float(sys.argv[1]),float(sys.argv[2]); n=3; d=(b-a)/n
for i in range(n): print(f"{a+i*d:.4f} {a+(i+1)*d:.4f}")
EOF
while read s e; do
  (cd "$HERE" && timeout 7000 node render.mjs --project /home/user/tpl/an/json/psych.json --footage "$FT" --comp transition \
     --from "$s" --to "$e" --fps "$FPS" --samples 1 --cache /tmp/ec-par-$s --frames-dir "$FR" > "$FR/log_$s.txt" 2>&1) &
done < /tmp/parity_chunks.txt
wait
python3 -I "$HERE/parity.py" "$FR" /home/user/tpl/reels/r1.mp4 30 "$OUT" "$LABEL"
