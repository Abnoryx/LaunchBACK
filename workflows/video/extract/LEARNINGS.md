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
- 2026-11-20 r1 (first run, ground truth from the AE project): see runs/r1/score.json. Cuts recall 11/11 (one 2 f
  early), precision ~0.6 (extras are sub-beats + S6 flashes). Ease benchmark 100 % @0.3 px, 97 % @1 px, 89 % @2 px.
