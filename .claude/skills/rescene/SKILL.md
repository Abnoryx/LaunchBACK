---
name: rescene
description: Reverse-engineer a short-form motion-graphics reel (Instagram/TikTok/After Effects style: kinetic text, camera pushes and whips, 3D props, flashy transitions) from the video alone and rebuild it from scratch as parameterised templates in our WebGL engine. Use this whenever the user gives or names a reel/video and wants it broken down, measured, copied in style, "extracted", "rebuilt", turned into templates, or asks for the cuts, transitions, eases, camera moves, fonts or text timing of a video — even if they don't say "rescene". Also use it to improve the extractor itself (it learns from every run).
---

# /rescene — reel in, breakdown out, rebuilt from scratch, smarter every run

Code: `workflows/video/extract/` (Python, CPU). Plan + research: `workflows/video/EXTRACT_PLAN.md`,
`workflows/video/reports/Reel reverse engineering methods.md`. Standing video rules: `workflows/video/REQUIREMENTS.md`
(read it first; they apply here too — one job at a time, check twice, save outputs to git, their reels are
reference only: measure, never copy their pixels/assets into our videos).

## 0. Read what earlier runs learned
Read `workflows/video/extract/LEARNINGS.md` before anything else. It holds the rules found the hard way (thresholds,
failure modes, user corrections). Follow them over the code defaults when they disagree, then fold them into the code.

## 1. Run the extractor
```bash
cd workflows/video && python3 -m extract.run <video> <name>        # add --no-text for a fast pass
```
Writes `extract/runs/<name>/`: `info.json`, `frames.npy` (BT.709 analysis stack, not committed), `measure.json`
(signals, cuts, transitions, camera), `ocr.json`, `breakdown.json`, `storyboard.jpg`, and `score.json` when ground
truth exists (`extract/gt/<name>.json`). Stages are cached; delete a file to redo that stage.
Typical CPU cost for a 30–60 s reel: ingest ~5 s, measure ~15 s, OCR several minutes (the slow part).

What each stage gives (and why it's done this way):
- **Cuts + transitions** (`measure.py`): histogram jump *and* the shots either side must differ, so snap zooms and
  flashes inside a shot don't count as cuts. Transition tags (flash_white, dip_black, invert, blur, whip,
  zoom_punch, rgb_split, hard_cut) come from per-frame signatures judged against each side's own level.
- **Camera** (`measure.py`): DIS optical flow + RANSAC similarity per frame → pan/zoom/roll curves in 1080 px.
- **Eases** (`eases.py`): dynamic programming finds the keyframes, each segment gets the best library ease
  (quad/cubic/expo/our AE eases...) or a free bezier when none fits. Timing comes from measurement, never from a VLM:
  VLMs reproduce looks but get timing wrong.
- **Text** (`text.py`): RapidOCR word boxes on changed frames, linked into word tracks with their own move keys.

## 2. Check the breakdown with the user (cheap, before any build)
Send `storyboard.jpg` and a short shot table (shot, frames, transition in, camera move + ease, words). Ask what's
wrong. Every correction is saved — see step 5. Don't build before this sign-off: fixing a breakdown costs seconds,
fixing a built shot costs a render.

## 3. Match archetypes, then build
For each shot pick the closest template in `workflows/video/library/templates/` (catalog: `library/catalog.json`) by
its features: world (paper vs dark, from luma), camera move, transition, word count/sizes, props. Fill the template
with the breakdown's timings and eases (`aeb.K((frame/30, value, ease_tuple), ...)`); the ease tuples come straight
from `breakdown.json`. No template fits → note it as a new archetype and scaffold one from the breakdown.

## 4. Fit by rendering (only the few params still off)
Render 360p previews (`engine/render.mjs --preview 1 --every 3`), compare to the reel frames for that shot, adjust
the handful of parameters that are off (positions, sizes, key times). Measure first and fit last: a black-box render
is ~0.5–5 s/frame, so blind search over many parameters is too slow (a 6-parameter CMA-ES fit ≈ 30 min/segment).
Then follow REQUIREMENTS.md: check twice, render, send, commit.

## 5. Learn from the run (do this every time — it's how /rescene gets better)
1. **Corrections → tests.** Write what the user corrected to `extract/runs/<name>/corrections.json`, e.g.
   `{"cuts_add":[97], "cuts_remove":[602], "transitions":{"455":["rgb_split"]}}`. These become permanent checks.
2. **Fix the code** for the cause (not the one reel), then run the gate:
   ```bash
   python3 -m extract.check --remeasure     # ease benchmark + every run with gt/corrections vs extract/baseline.json
   ```
   Keep the change only if nothing got worse; then `python3 -m extract.check --accept` to raise the baseline.
3. **Write the lesson** in `LEARNINGS.md` (date, reel, problem, fix, score change).
4. **Grow the priors**: approved shots go into the template catalog with their measured eases and timings.
5. Commit `extract/` changes, `runs/<name>/` (breakdown, storyboard, score, corrections — not frames.npy) and push.

## Ground truth and benchmarks
- `extract/gt/r1.json`: the r1 reel's real cuts, transitions and camera from its AE project — the yardstick.
- `python3 -m extract.bench_eases [n] [noise_px]`: synthetic ease/keyframe benchmark (perfect labels for free).
- Add ground truth whenever a reel's real values become known (e.g. our own renders: the scene JSON is the truth).

## Not built yet (say so when relevant)
Font ID (DINOv2 Google-Fonts classifier → render-and-compare shortlist), colour/finish measurement, audio (VO word
timing, stems, SFX onsets), archetype auto-matcher, automatic fit loop, layer masks (SAM 2 / omnimatte need a GPU).
Order and choices: `EXTRACT_PLAN.md` phases P2–P4 and the research report's ranked list.
