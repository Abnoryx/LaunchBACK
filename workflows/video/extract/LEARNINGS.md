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

## 2026-11-21 — Route A step 3 on Sells: harvest
- 125 footage files linked, 0 missing once zip `#UXXXX` names are decoded. Fonts: .aep PostScript names
  `Helvetica`, `Helvetica-Bold(Oblique)` now map to the real Helvetica files (was the Inter stand-in; only our own
  templates' `HelvReal-*` names got the real font). r1 check: no frame worse, f30 SSIM 0.836 -> 0.882.
- Still stand-ins: HelveticaNowText-Black/Bold (3 comps), Coolvetica Heavy (paid), SF Pro -> Inter Tight, InkFree -> Patrick Hand.

## 2026-11-21 — Route A steps 4–5 on Sells
- Shots: 23, time offset 0; detector whip cuts +2 f, crossfades ±5 f, shot 22's momentum-matched whip not detected.
- Templates: 23 private JSONs (13 MB); shot 1 template renders pixel-identical to the full project. Accent = hue band
  100–170 (green family, measured from non-default colours); apply() rotates that band to the new hue. Images/footage
  keep their own colours (logos, UI screenshots) — tell the user when the accent lives in pictures.

## 2026-11-21 — engine: 3D sort for parallel layers (Sells shot 18)
- Text floating 16 px in front of a tilting card vanished: sorting by centre depth put it behind the card. Parallel
  layers are now ordered by their offset along the shared normal (coplanar = layer order). r1: no frame changed.

## 2026-11-21 — engine: expression selectors (Sells shot 18)
- Small text never appeared: bounce selectors with Based On = Words used the character index as textIndex (huge
  delays), and every selector was combined by Add. Now textIndex follows Based On, and an Expression Selector
  intersects (AE default) with the selectors above it. r1 sample frames unchanged.

## 2026-11-22 — Sells step 6: engine gaps found by render rounds (mean SSIM 0.844 -> 0.868 full res)
- Seeks past a clip's end (and any seek in short GIFs) wrote no frame -> ENOENT crash: decode all frames once, take the
  frame at t, hold the last.
- Shape Gradient Fill/Stroke were not implemented (21 uses in Sells): linear + radial with alpha stops.
- Zero-width strokes drew 1 px (canvas ignores lineWidth 0): skip them (faint green rings on the pebbles).
- Merge Paths was ignored (iMessage bubbles came out as rectangles): all five modes.
- S_Gradient ran reversed at a fixed 60%: now Start->End colour multiply (dark grid tops, emoji shading).
- Text animators whose only property sits at its default (red Fill Color) were skipped as `syn` filler: when an
  animator has no real property, all its properties count.
- readPixels read RGBA16F targets as UNSIGNED_BYTE (invalid in WebGL2) -> every large-feather mask crossing the layer
  edge came back empty (Exposure vignettes, masked blurs did nothing). Read as FLOAT.
- LUT fitting from pixel pairs learns nonsense where geometry differs (inverted grid lines): keep a LUT only if luma
  SSIM improves. A spatial falloff is never a LUT's job.
- `extract.aep_coverage` only checks effects/expressions — shape items (G-Fill, Merge) slipped through; check those too.
- Route B: same-palette hard cuts (light page -> light page) fail the window-histogram test; a pixel-difference spike
  rule found Sells f1232 (cut recall 0.86 -> 0.91). Cuts inside white flashes are still found ~5 f off.
- Known open gaps: s09 'Why' faces 0.50, s16 'People don't care' 0.57, s22 camera runs ahead 0.72; scene 5 glow too
  big; box blur sigma (0.6 R) likely too small; s01 underline should be red, bills out of sync.

## 2026-11-22 — Stop ("Stop Trying to Please Everyone"), Route A steps 1–5 + engine gaps
- Which render is the target: the posted reel (`tpl/reels/stop_ig.mp4`) == the project's later render `7th reel_1.mp4`
  (luma diff 0.7 at offset 0) == the saved .aep. The old breakdown's "0–10.6 s differs" note was about `7th reel.mp4`.
  Always compare the posted reel against every render in the footage folder before trusting the project.
- Harvest: zip tools store astral characters (emoji) as `#LXXXXXX` (6 hex), not `#UXXXX`: 1 missing clip -> 0.
- Fonts: `Coolvetica-Cram` is the free regular Crammed cut the user supplied -> real font (was League Gothic).
- Coverage now also checks shape items (Sells lesson); Stop needs none.
- **Effect masks** (Compositing Options > Mask Reference): masks an effect references limit only that effect and do
  not cut the layer. The engine cut the layer -> Stop's centre logo coin vanished (its shine masks hid it). Now the
  layer skips referenced masks and the effect's result is mixed in inside them (x Effect Opacity). psych scene 8
  SSIM +0.004/+0.005 on 3 frames; Sells s01 f30 0.904 -> 0.899 (its LUT was fitted to the old look; refit if Sells
  is re-rendered).
- New effects: Optics Compensation (reverse off; barrel with unit centre scale, source r = tan(r*FOV/2)/(FOV/2) in
  half-width units, edge-clamped; checked by eye on f790), 4-Color Gradient (inverse-distance, replaces colour), Grid
  (blending mode 1 = None: lines only — the grid comp is then filled and multiplied, so Normal-over hid the lines).
- Pass-through for now: Echo (1.3 ms echo time, invisible), CC Glass (frosted cards in ui scene look too light),
  APC Colorama (custom Output Cycle not decodable by py_aep: the "Something" glow shows white instead of dim
  olive, ui-scene background too cyan). Needs a measured palette per layer (fit from reel pixels), not a frame LUT.
- Debug recipe that found the logo bug in minutes: render the precomp alone, then log per-layer content alpha
  (readPixels FLOAT) + mask presence from drawLayer via console.warn (render.mjs only forwards warnings/errors).
- Round 1 (540p, Kaggle 13 min): mean SSIM 0.863; 11/17 at the bar. Found by the render: shape/text adjustment layers
  applied their effects to the whole frame (s10 ui scene blurred all over) -> now only inside the layer's own drawn
  alpha (masks/opacity included). Coverage skipped `ADBE AudSpect` as an audio effect (regex `^ADBE Aud`) -> the
  Audio Spectrum solid drew as a grey slab over s17; regex now excludes AudSpect/AudWave.
- User round-1 notes (2026-11-22): "last scene doesn't exist" (s17 grey slab), "Get to know has no contrast" (s12),
  "text blurry where the cursor ticks" (s10). Causes + fixes:
  - s12: Compound Blur used the layer's own luma as the blur map, so white text got the MAXIMUM blur. Now the map is
    the referenced layer's source (a hidden scratch png / dust video — AE uses it even when hidden), stretched.
  - s17: Audio Spectrum implemented (renderer serves /pcm/<file> as 22.05 kHz mono f32; Hann DFT per band). AE's
    maths is undocumented: fitted on this reel (78 bars x 51 frames) -> window centred one window length after the
    frame, height = maxH * 0.0404 * amp^0.5 (log-corr 0.24 -> 0.74), min bar = thickness (dotted baseline).
  - s17 black border: a Transform adjustment shrinks the frame to 95% and AE fills the edge from the 166% background
    beyond the frame; we only have the frame, so adjustment Transform now repeats edge pixels.
  - s10: shape adjustment layers fixed (see round 1). Colorama: palette not in the .aep (py_aep and the raw RIFX cdat
    hold nothing) -> measured LUT `colorama|<comp>|<layer>` in the reel's luts.json, fitted from the analytic 4-Color
    input vs reel / (our post-Colorama gain): frame MAE 32.8 -> 4.4. Generic hook; the fit itself was by hand.
- Round 2 (6 scenes re-rendered, 6 min GPU): mean SSIM 0.863 -> 0.908; s17 0.484 -> 0.940, s10 0.550 -> 0.834,
  s12 0.728 -> 0.745 (looks matched by eye: the random film-dust overlay on black dominates SSIM there).
