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

## 2026-11-22 — Route A steps 1–3 on The Generation Effect (gen)
- The uploaded "gen" mp4 was the Stop Trying to Please Everyone reel (caption "Broad messages disappear…"); its run is
  saved as `extract/runs/stop`. Always compare a contact sheet of the reel with the project's own render before step 4.
- Step 4 assumed the mp4 and the project share a frame rate. gen is 18 fps, posted reels are 30 fps: aep_shots now
  converts mp4 cuts to project frames (Sells output unchanged).
- Coverage: added blend modes linear burn, (classic) color burn, lighten, lighter color; effects Twirl, CC Radial Fast
  Blur, Noise, Heatwave (approx), CC Jaws, Keylight (colour-difference approx), Corner Pin (homography), BCC LED
  (approx), Magic Bullet Film (LUT if fitted, else exposure + grain); TimeSlice/Noise Alpha/Optics Comp no-ops at the
  values used. Fonts: Montserrat, Barlow Condensed, Space Grotesk, Bitcount Prop Single now real (fontsource).
  `.ai` footage needs ghostscript in the container (ImageMagick rasterises through it) — install it first.
- First look vs Comp 1_2.mp4 (the creator's own render): Jaws letterbox matches; radial blur fitted (amount/1000);
  twirl radius fitted (50 = layer diagonal) but still too weak mid-ramp; scene 5 XP wallpaper (alpha-matted by the
  `notepad` precomp) is hidden in ours but shows as a large rect in AE — open engine gap, not yet explained.
- Engine (gen s04/s05 crash): a second Merge Paths in the same shape group gets the first merge's result as a part;
  fillMerged now recurses (clip uses the parts' union outline).
- Engine (gen s04 phone blurred): AE limits an adjustment layer to its own alpha. Shape/text/footage adjustment layers
  now adjust only inside their content (drawn without effects); solid adjustment layers keep the comp-rect + masks
  path. Sells/r1 have no such layers (unchanged); Stop has 17.
- CPU render speed here (4 cores, 540p, 1 sample): 12 s/frame on light scenes, 25–32 s/frame on heavy ones.

## 2026-11-23 — gen round 1 review → round 2 fixes (user: EMOTION/story not animated/transitioned; bubbles low contrast)
- The posted reel is the FINAL comp ("sound design"): it re-imports the creator's render of Comp 1 and adds overlays
  (a bokeh flash into the football shot). extract/aep_relink.py swaps such re-imported renders back to the live comp;
  render the final comp as root. Missing that made cut 215 a hard cut in ours.
- Footage Loop = 1 means play once (was treated as "loop forever": a light leak wrapped to its bright first frame).
- Video frames: AE shows the source frame that started at or before t (floor); ffmpeg -ss returns the next one.
- .ai/.pdf/.eps via ghostscript pngalpha (ImageMagick gave opaque, slightly-lifted black: Extract keys then missed).
- Twirl: radius = % of the larger layer side, angle falloff linear (1-d/r) — matches the reel's spiral frame by frame.
  CC Radial Fast Blur amount/300. Earlier fits were made against frames past the effect peak: fit at the key frame.
- Grade: pixel-pair LUT regression lifts sharp dark text to grey when ours is sharper than the reel. fit_luts.py
  `quantile` mode = one luma tone curve shared by R,G,B + per-channel mean gain (no hue shift, darks kept).
- Motion/transition check (new rule): run extract.run on our render too and compare transitions per cut, then look at
  every disputed cut as a ±3-frame strip. Automatic tags alone are noisy (same cut tagged hard_cut vs whip).
- Open: scene 5 XP wallpaper — AE ignores its alpha matte (matte off: SSIM 0.40 -> 0.55); general rule unknown.
  EMOTION/STORY need the real font (Round 8 by atipo, all-caps); the tracking animation itself is already there.

## 2026-11-23 — gen before the final (user: shapes lack depth/shadows; EMOTION/STORY still not animated/transitioned)
- AE Layer Styles were ignored by the engine. Now drawn: Drop Shadow, Inner Shadow, Inner Glow (edge), Outer Glow, in
  layer space after effects; Size -> Gaussian sigma 0.5x; modes multiply/screen/normal. Gives scene 1's pillow shapes.
- Simple Choker is not pixels: value / 4 px matched the gen reel (computer outline + Jordan sticker, both -70).
- Text animator Tracking Amount is in layer px, not 1/1000 em (character-panel tracking stays em). The AE-layout text
  path ignored animator tracking entirely; now EMOTION/STORY widths match the reel to ±5 px on every frame.
  (IKEA/Game looked like counter-evidence but both were mid-reveal or past the animation: check what a frame tests.)
- ROUND8-FOUR (Round 8 by atipo, all-caps) -> Anton drawn in caps until the real font arrives.
- Sapphire TimeSlice (Slice Number 1): one centre cut; the start side of Slice Direction shows the previous frame.
  Kept from the previous rendered frame (re-rendering an earlier time missed preloaded video frames). First frame of
  the effect has no previous frame: 1-frame difference at gen f354.
