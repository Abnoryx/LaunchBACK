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
- 2026-11-21 zeigarnik (first run, 25 shots; user said "you figure it out", so I checked the frames myself):
  a blur-to-white dissolve (485-492) fired a cut at its onset and another after the white peak (499) -> one real cut
  at the white peak (493). Saved as corrections.json. Fix to do: when a short segment is a monotonic ramp to
  white/black, merge it into the cut at the ramp's peak. Short 0.5-0.8 s shots (568, 933, 1217) are real: keep them.
  Camera keys at the first 1-3 frames of a shot that opens with a whip are transition motion, not camera: drop them.
- 2026-11-21 zeigarnik OCR (ran on Kaggle CPU, ~20 min incl. setup): the creator's handle (@SepticVisuals) is read
  in almost every shot -> treat a word seen in >50 % of shots as a watermark and drop it from the shot text. Small
  print on props (Figure1, CALENDER, dates) mixes with the spoken-text words: rank words by box height; the big
  ones are the kinetic text. Kaggle outputs download from www.kaggleusercontent.com (now allowed).
- 2026-11-21 zeigarnik rebuild (cine_scene, auto text + measured camera, Kaggle renders ~15 min): SSIM v1 0.556,
  v2 0.555 (3/23 pass). Measured camera keys at shot ends are whip/flash, not camera: clamp and skip the last 4
  frames. Auto hero-font guess (big = serif) was wrong for this reel: pick fonts per reel. With only the video (no
  project files) and our own props, SSIM is capped by prop/layout differences: score layout/timing, not pixels.

## 2026-11-21 — Route A step 1: .aep dumper (extract/aep_dump.py)
- The original dump script was never saved; rebuilt on py_aep 0.19. Same format the engine reads. Psych re-dump renders
  identical to the old dump (8 sample frames, mean abs diff <= 0.002).
- Gains over the old dumps: text layout (per-glyph advances) for projects whose old dump lacked it (sells: 110 layers),
  mixed-style text runs, box text position, spatial tangents (in_st/out_st, used by anim.js), gradients, markers, curves.
- Layers py_aep can't decode `enabled` for are dumped as disabled (same as before: engine needs enabled === true).
  Earlier note (stop): such a layer can be the one actually rendered — check against the mp4 when a shot is missing.

## 2026-11-21 — Route A step 2 on Sells: coverage + engine gaps
- Coverage found 16 effects + 2 expressions missing. Added: Gradient Ramp, Fractal Noise (fbm stand-in), Find Edges,
  Radial Blur, Roughen Edges, Turbulent Displace, Noise HLS, S_Glow, Compound Blur, CC Cylinder, CC Page Turn (flat
  fold), Bezier Warp (corners only), Posterize Time (adjustment re-render); Levels/Displacement Map no-ops at the values
  used; typewriter text + blinking cursor expressions; Pseudo/ effects are controls.
- Engine bug found by the first 5-frame look: a Trim Paths at a shape layer's root must also trim its child groups
  (AE behaviour). Fixing it also corrected r1 f510 ("100" now drawn like the reel; old render showed "1").
- Still approximate on Sells: overall grade (needs fitted LUTs, step 6), CC Cylinder money bill too small, page fold
  ignores curl radius.
