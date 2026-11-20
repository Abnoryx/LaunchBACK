# /rescene learnings (read first, append after every run)

Each entry: date, reel, what went wrong or what the user corrected, the fix, and the scorecard change.
Rules here override defaults in the code until they are folded into it.

## Standing rules
- Colours: decode with BT.709 (ingest does). Never sample colours from JPG frame dumps (BT.601 skews greens/reds).
- Cuts: a frame-to-frame histogram jump alone over-fires on snap zooms, invert flashes and letter shuffles inside a
  shot; require the shots either side to differ (window distance >= 0.33). Extra "cuts" inside one AE comp are often
  real visual sub-beats: keep them as sub-shots, don't force-merge.
- Transitions: judge flash/dip/blur against each side's own level, never against a mixed median across the cut.
  Ignore optical flow on the cut frame itself.
- Eases: segment with dynamic programming over library eases (BIC-style penalty), then free-fit only segments that
  stay above noise. Greedy key-finding + merging failed badly (ease accuracy 9-30 %).
- Timing and eases come from tracking + fitting, never from a VLM (Animation2Code: VLMs get timing wrong).

## Log
- 2026-11-20 r1 (first run, ground truth from the AE project; baseline stored in extract/baseline.json):
  cuts recall 1.0, precision 0.61 (extras = S2 sub-beats, S6 invert flashes); transition tags 0.73; camera error
  median 0.28 px (4.5 px on moving frames, p90 5.8 px); zoom 0.2 %. Ease benchmark 100 % @0.3 px, 97 % @1 px,
  89 % @2 px. Runtime: measure 14 s, OCR ~10 min on a busy CPU (shared with a render).
- OCR text: exact-text linking split one word into many tracks (WONDER/VONDER/NONDER misreads) -> link by place +
  fuzzy text, name by the most common reading, treat ~5 px box jitter as noise. 902 -> 578 tracks.
- Next fixes (known): word moves are in screen space (subtract the camera to get layer motion); cut precision
  (classify sub-beats vs cuts); text reveal style (blur-in / per-letter) not measured yet.
