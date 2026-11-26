---
name: rescene
description: "Reverse-engineer a short-form motion-graphics reel (Instagram/TikTok/After Effects style: kinetic text, camera pushes and whips, 3D props, flashy transitions) and rebuild it as parameterised per-shot templates in our WebGL engine — from its After Effects .aep project when we own it (exact copy, all assets harvested), else from the video alone. Use this whenever the user gives or names a reel/video or an .aep/template project and wants it broken down, measured, copied in style, 'extracted', 'rebuilt', turned into templates, or asks for the cuts, transitions, eases, camera moves, fonts or text timing of a video — even if they don't say 'rescene'. Also use it to improve the extractor itself (it learns from every run)."
---

## Always land on main
Everything this skill produces or changes (code, runs, learnings, library entries, renders, skill edits) must be
committed and pushed to `main` — not left on a side branch. Merge any work from other branches into `main` as well.

# /rescene — reel (+ .aep) in, per-shot templates out, smarter every run

**Pick the route first:**
- **Route A — .aep route** (default whenever we have the project, e.g. Earn Edits): exact scenes, all assets,
  one template per shot, scored against the mp4. See "Route A" below. **Not built yet** — say so, and offer to build it.
- **Route B — video-only route** (reels we don't own): steps 0–5 below. Measure, never copy their pixels.

Code: `workflows/video/extract/` (Python, CPU). Plan + research: `workflows/video/EXTRACT_PLAN.md`,
`workflows/video/reports/Reel reverse engineering methods.md`. Standing video rules: `workflows/video/REQUIREMENTS.md`
(read it first; they apply here too — one job at a time, check twice, save outputs to git). Earn Edits .aep scenes
may be used exactly (user has permission); other reels are reference only. Their files never go into git.

## Route B — video only

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
Heavy stages (OCR, future GPU models) and every render run on the user's Kaggle GPU (REQUIREMENTS.md rule; runner: `workflows/video/kgl/run.py`).

What each stage gives (and why it's done this way):
- **Cuts + transitions** (`measure.py`): histogram jump *and* the shots either side must differ, so snap zooms and
  flashes inside a shot don't count as cuts. Transition tags (flash_white, dip_black, invert, blur, whip,
  zoom_punch, rgb_split, hard_cut) come from per-frame signatures judged against each side's own level.
- **Camera** (`measure.py`): DIS optical flow + RANSAC similarity per frame → pan/zoom/roll curves in 1080 px.
- **Eases** (`eases.py`): dynamic programming finds the keyframes, each segment gets the best library ease
  (quad/cubic/expo/our AE eases...) or a free bezier when none fits. Timing comes from measurement, never from a VLM:
  VLMs reproduce looks but get timing wrong.
- **Text** (`text.py`): RapidOCR word boxes on changed frames, linked into word tracks with their own move keys.

## 1b. Save the transitions as separate assets (user rule, 2026-11-24)
Every rescene run also exports each DISTINCT transition on its own, with a preview video the user can watch:
```bash
cd workflows/video && python3 -m extract.transitions_export <name>     # reads extract/runs/<name>/measure.json
```
Per transition type it writes `library/transitions/<name>/<tag>.json` (spec: tag, frames, params, how many uses, the cut
frames where the reel uses it, `params_source`) and `<tag>.mp4` (the move on two neutral cards, A paper / B dark, once at real
speed and then 4x slow, so the move itself can be judged — never the reel's pixels), and adds a `draft` entry to
`library/catalog.json` `transitions`. Recipes live in `library/transitions.py` (hard_cut, whip, zoom_punch, flash_white,
dip_black, invert, blur, rgb_split); a tag with no recipe is listed as skipped — add the recipe, don't drop it. Params are
per-tag defaults until measured per use (say so). **Send the preview mp4s to the user in the same message as the
storyboard (step 2)**; their corrections (direction, frames, strength, "less glitch") are saved as notes/rules and fix the
recipe. Commit the previews (small, neutral cards) and push to `main`. For Route A (owned .aep) the project's own layer keys
give exact frames/eases: pass them as `params` to `transitions.export()` instead of the defaults.

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
**Score every shot against the reel** with `python3 -I engine/parity.py <frames_dir> <reel.mp4> 30 <out_dir> <label>`
(per-shot SSIM, mean abs diff, histogram distance + side-by-side sheets). Pass bar (REQUIREMENTS.md): SSIM 0.92–0.95 on
paper/text shots, 0.85+ on asset-heavy shots, and you can't tell them apart side by side. A shot below the bar goes back
to fitting; report the scores to the user. Then follow REQUIREMENTS.md: check twice, render, send, commit.

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

## Route A — .aep route (steps 1–5 built; 6–8 planned — build in order)
**Run the steps back to back without asking the user between them** (user rule 2026-11-21); stop only for a real
blocker or a decision that is theirs (missing files, licence, taste). Report at the end, or at long waits.
Input: `<project>.aep` (+ its footage folder) and the posted mp4. Output: `library/templates/<project>/<shot>` per shot,
assets in `/home/user/tpl/lib/<project>/`, scores per shot. Read LEARNINGS.md first, as in Route B.

0. **Get the project** (user rule, 2026-11-22) — every .aep project zip is pulled from the user's MEGA folder
   https://mega.nz/folder/InRm3CQT#xF_C5lxUl2l7TzSSyA_IzQ by its file name:
   `python3 -m extract.aep_fetch "<zip name>"` (`--list` shows the folder; uses `/home/user/tpl/zips` first; needs
   `apt-get install -y megatools`, and `ghostscript` for `.ai` footage). Unzip into `/home/user/tpl/src/<project>/`.
   Then check the posted reel is the same video: contact sheet of the reel next to the project's own render
   (often in its footage folder) before step 4 — the reel caption/file name can belong to another project.
1. **Dump** — BUILT: `python3 -m extract.aep_dump <project.aep> /home/user/tpl/lib/<project>/<project>.json`
   (needs `pip install py_aep`; ~6 s). Everything the engine reads: comps, precomps, layers, parenting, keyframes + eases,
   expressions, effects, masks/mattes, mixed-style text runs, fonts, 3D layers, cameras, lights, markers, audio layers.
   → checked 2026-11-21: psych re-dump renders identical to the old dump (8 frames, mean diff ≤ 0.002).
2. **Coverage report before any render** — BUILT: `python3 -m extract.aep_coverage <dump.json> [out.json]` (uses the
   engine's own effect list and expression classifier). Then render 5 frames of the opening shot at 360p on CPU and
   look at them next to the reel before going further: it caught a reversed fold and a trim bug in Sells. (cheap): list every effect match-name, expression and layer feature in the
   dump; flag what the engine doesn't support yet (`engine.js` effect switch). Gaps get fixed in the engine first —
   one fix serves every project. Saves wasted Kaggle renders.
3. **Harvest assets** — BUILT: `python3 -m extract.aep_harvest <dump.json> <project folder> <name>` (hard links, so no
   extra disk; zip names like `#U2026` are decoded). Fonts the engine would draw with a stand-in are listed as missing. Into `/home/user/tpl/lib/<project>/` with `manifest.json` (path, sha1, type, used-by shots).
   Missing footage/fonts are listed for the user — never silently substituted. Then refresh the Kaggle backup
   (`kgl.tpl_backup`) so nothing lives only in the container.
4. **Split into shots** — BUILT: run Route B first (`python3 -m extract.run <reel> <name> --no-text`, ~25 s), then
   `python3 -m extract.aep_shots <dump.json> "<root comp>" <name> <out shots.json>`. Whip cuts land 2 frames late in the
   detector, crossfades ±5; a momentum-matched whip may not be detected at all — the project wins. Split from the project's own structure (top comp's layer in/out points + precomp boundaries),
   cross-checked against the mp4 cut detector (Route B measure). Mismatch > 1 frame → the mp4 was trimmed/retimed:
   find the offset/stretch by aligning cut times, store it as the shot's time map.
5. **Templates** — BUILT: `python3 -m extract.aep_template make <dump.json> <shots.json> <tpl dir>` and
   `... apply <shot_NN.json> <params.json> <out.json>` (params: texts by "<comp>/<layer i>", accent hex, footage by id).
   Times stay as in the project (render the template's `window` with --from/--to). Checked on Sells shot 1: template
   render == full-project render, pixel-identical. Not yet: shared-precomp dedupe, time-scale param. Each shot → a self-contained template that reproduces the scene exactly. Auto-expose as params:
   text layers (string, font, size), fills matching the accent colour, image/footage layers (props), global time
   scale; everything else locked. Precomps reused across shots become one shared template. Catalog entry gets the
   features Route B measures (world, camera move, transition, word count, props) so it can be matched later.
   → check: template filled with the original content == dumped shot, pixel-identical render.
6. **Render + score on Kaggle** (`kgl.render`), then `engine/parity.py` vs the mp4 using the time map. Bar: 0.92 on
   paper/text, 0.85 on asset-heavy. Below the bar = engine gap → fix in engine, log in LEARNINGS, never a per-shot hack.
   Check twice (REQUIREMENTS.md) before showing anything.
   **Render rounds (user rule, 2026-11-22):** every scene renders separately (`kgl.render ... --shots
   parity_shots.json`), and the scenes are stitched together for the showcase. Round 1 at 540p (`--preview 540 --samples 1`)
   → send the showcase beside the reel and ask the user for changes, and also fix whatever is wrong by my own review →
   round 2 at 540p, re-rendering only the changed scenes (`--only s06,s09`) → changes if needed → final at full
   resolution. Never full-res before the final; never re-render unchanged scenes.
   **Round 2 scope (user rule, 2026-11-22):** the user's round-1 notes AND every fix from my own review both go into
   round 2, unless the user says to leave one out. Never wait for a separate yes on my own fixes.
   **Motion + transition check before showing any round (user rule, 2026-11-22; missed in gen r1 on EMOTION/story):**
   SSIM and still sheets don't catch missing animation. For every scene, compare motion against the reel: a strip of
   every frame across each cut (±6 frames) and a per-scene motion curve (mean abs frame-to-frame difference, ours vs
   reel). Flag any element that sits still or pops in where the reel animates it, any keyframed move/twirl/wipe that
   is weaker or missing, and any cut that is hard in ours but transitioned in the reel. Zero hard cuts that the reel
   doesn't have. Fix these before sending the round; list what was checked in the report.
7. **Free ground truth for Route B**: write `extract/gt/<reel>.json` (cuts, transitions, camera, eases, text timing)
   from the dump, run `python3 -m extract.check --remeasure`, and fix Route B wherever it misses. Every owned project
   makes the video-only route better.
7b. **Into the library first** (user rule, 2026-11-22): after the final render is approved, register every scene template
   (`library/catalog.json` templates `<reel>/sNN`: private `tpl:` path, window, slots, parity score, status proven if
   it meets the bar, else draft) and every harvested asset (`assets` `<reel>/<file>`, use-only licence). Only then is
   anything customised. The files stay in the private template folder + Kaggle dataset; the catalog only points to them.
   **Also save the review videos (user rule, 2026-11-23):** in the same step, the approved final render's scene mp4s
   (`<out>/sNN.mp4`, already one per scene) become the library previews that `/gen` ranks and the user reviews:
   scale each to 540p, then `gen.previews.keep(mp4, entry)` (moves it to `/home/user/tpl/previews/<reel>/sNN.mp4`
   and makes the 3-frame `sNN.jpg`), then `python3 -m gen.embed` and `python3 -m kgl.tpl_backup backup`. Private: never
   in git (bought scenes). No re-render needed; if a scene is missing, `python3 -m gen.previews` renders it.
8. **Original touch** (REQUIREMENTS.md picks 1–4, 6) is applied through the exposed params when a template is used in
   our videos — never by editing the template itself.

First test project: "Stop Trying to Please Everyone" (zip + old dump `tpl/an/json/stop.json` already restored). Then
sells, gen, Zeigarnik when bought. Which reel in `tpl/reels/names.txt` matches stop/sells/gen: confirm with the user.

## Ground truth and benchmarks
- `extract/gt/r1.json`: the r1 reel's real cuts, transitions and camera from its AE project — the yardstick.
- `python3 -m extract.bench_eases [n] [noise_px]`: synthetic ease/keyframe benchmark (perfect labels for free).
- Add ground truth whenever a reel's real values become known (e.g. our own renders: the scene JSON is the truth).

## Not built yet (say so when relevant)
Route A steps 3–8 (see above). Font ID (DINOv2 Google-Fonts classifier → render-and-compare shortlist), colour/finish measurement, audio (VO word
timing, stems, SFX onsets), archetype auto-matcher, automatic fit loop, layer masks (SAM 2 / omnimatte need a GPU).
Order and choices: `EXTRACT_PLAN.md` phases P2–P4 and the research report's ranked list.


## EVERY version ships with the Edit Lab (user rule, 2026-11-26)
Every rescene deliverable (first pass and every revision) comes with the Edit Lab until the user approves the final version: the same shared page as /gen (`workflows/video/edit_room/`, checklist in `edit_room/README.md`). Render previews, upload clips (`asset:true`), `python3 workflows/video/edit_room/room_from_templates.py <lib/<reel>/templates> clips.json room.json "<title>"`, `python3 workflows/video/edit_room/build.py room.json page.html`, run `node workflows/video/edit_room/tests/run.cjs` TWICE (both must pass), publish with `db` + `assets` to the same artifact URL, give the link with the render. Read pins with ArtifactData (`pins/reel`) and resolve with `gen/runs/michelin_gen/edit_room/resolve_pins.py` (see /gen §6b).
