# Plan: better "video in → everything extracted → rebuilt from scratch"

## Where we are (honest)
- r1 was rebuilt mostly from **their AE project** (exact keyframes, camera, eases, fonts). A new reel won't come with a
  project, so that path doesn't repeat.
- r2–r6 were read **by eye**: contact sheets, frame diffs, luma, k-means palettes → hand-written notes. Good for a
  shot vocabulary, but no measured motion curves, no eases, guessed fonts, no layer separation.
- Eyeballing frames is slow and burns tokens. Timing and ease errors (the "feel") are what the user notices most, and
  those are exactly what we don't measure.
- Known traps: frames saved as BT.601 JPG skew greens/reds; VFR reels (r6 = 17 fps); text fonts guessed.

## Goal
One command turns a reel into a **breakdown file per shot** (elements, keyframes, eases, camera, text + fonts,
colours, transitions, audio cues), then a template is matched or scaffolded from it and auto-fitted until it scores.
The agent reads numbers and tables; it looks at images only for the final judgement.

## Pipeline (`workflows/video/extract/`, each stage writes JSON/TSV + a small proof image)
0. **Ingest**: ffprobe, true frame times (VFR map), lossless PNG frames decoded as BT.709, mono WAV.
1. **Cuts + transitions**: frame diff + histogram + SSIM per frame → cut list; classify each transition by its
   signature (luma spike = flash/invert, sharpness drop = lens blur, strong one-way flow = whip, moving edge = wipe,
   channel offset = RGB split). Map each to our transition kit.
2. **Camera**: dense optical flow (OpenCV DIS, CPU) → per-frame similarity/homography → pan, zoom, roll curves;
   flow-layer clustering to tell 3D parallax from 2D slides.
3. **Elements**: OCR boxes per frame (RapidOCR/PaddleOCR on CPU) → when each word appears, how (blur-in, rise,
   type-on), position/scale over time. Non-text elements: camera-compensated difference + connected components;
   hard shots get SAM 2 masks (GPU only, optional).
4. **Curves → keyframes → eases** (the biggest gap): split each tracked property into segments (dynamic
   programming), fit a cubic bezier ease per segment on normalised time, snap to our library eases (linear, quad,
   cubic, expo, overshoot) when the error is small, else keep the fitted bezier. Output in `aeb.K(...)` form.
5. **Typography**: crop each word, identify the font with the open DINOv2 Google-Fonts classifier (top-5, free
   fonts only), measure size, tracking, leading and colour from glyph boxes.
6. **Colour + finish**: BT.709 palette, accent, paper/dark worlds, grain, blur, fringing, vignette, film edge.
7. **Audio**: Whisper word timings (VO = on-screen text check, cut sync), music/VO/SFX split (Demucs), onset → SFX
   cue table, LUFS.
8. **Props/3D**: flag objects that rotate in depth (flow pattern) → "needs 3D model"; source or generate ours.
9. **Breakdown + storyboard**: `breakdown/<shot>.json` + one annotated sheet per shot (boxes, curve plots).
10. **Template match / scaffold + auto-fit**: match the breakdown to an existing template (element/motion
    features); if none fits, generate a new template skeleton with the extracted keys. Then a fit loop: 360p preview
    render → compare (SSIM, element box error, curve timing error) → adjust a few parameters (Nelder–Mead / CMA-ES)
    → repeat. Cheap previews make this affordable.
11. **Scorecard**: cut error (frames), keyframe time error, ease match, camera error, text box overlap, SSIM per shot.

## Upgrades over the basic pipeline (v2 of this plan)
- **Fit by rendering, not just by measuring.** Our engine draws this style exactly, so the real extractor is the fit
  loop: guess the shot from the measurements, render it, compare to the reel, adjust, repeat. The measurements in
  stages 1–8 are only the starting guess. This beats any measuring tool on its own.
- **Recognise before measuring.** First classify each shot against our archetypes (the 40 from r2–r6 + our
  templates); then only a handful of parameters need fitting. Unknown shots fall back to the generic pipeline.
- **Free perfect training data.** Render thousands of random shots from our own templates (known keys, eases,
  fonts, cuts) to test and tune every stage, and to train small classifiers (shot type, transition, ease) on CPU.
- **Best source copy.** Fetch the highest-quality upload; compression smears small text and ease detail.
- **One cheap approval step.** The user signs off the breakdown storyboard before any build.
- **Every reel makes it smarter.** Each approved breakdown adds to the archetype library and the ease/transition stats.
- Limits that stay: AI imagery and 3D props are regenerated as ours, never extracted; taste is judged by the user.

## Validation (why r1 matters)
r1 has the real AE project, so it is **ground truth**: run the extractor on r1.mp4 alone and compare against the
project's real cuts, keyframes, eases and camera. Targets: cuts exact; keyframe times within 1 frame; ease class
right on ≥80 % of keyed properties; camera within a few px; fonts top-5 hit. Then a blind test on r2 (no project).

## Phases (one job at a time)
- **P1** (cheapest, biggest win): stages 0–4 + 9 on CPU, validated on r1.
- **P2**: fonts, colour/finish, audio (5–7).
- **P3**: template match/scaffold + auto-fit loop (10–11).
- **P4**: layer separation (SAM 2 / omnimatte) and 3D for hard shots: needs a GPU.

## Constraints / decisions
- Container: 4 CPUs, no GPU, no torch. P1–P3 run on CPU (torch CPU install ≈ 200 MB for Whisper/fonts).
  P4 needs a GPU: Higgsfield GPU rental (credits, quote first) or the user's machine.
- Runs after the current render finishes (shared CPU).
- Their reels stay reference only: the extractor measures, it never copies their pixels/assets into our videos.

## Research notes (Nov 2026)
- No ready tool turns a video into editable AE/Lottie keyframes; existing "video → Lottie" converters embed frames.
  So keyframe + ease extraction is ours to build (stage 4).
- Point tracking (CoTracker3, TAPNext) is GPU-oriented; CPU works for small jobs. Dense flow (OpenCV) is enough for
  flat motion-graphics layers.
- Layer decomposition: Generative Omnimatte (CVPR 2025), EasyOmnimatte (Dec 2025, code listed) – GPU, P4 only.
- Fonts: DINOv2 + LoRA on Google Fonts (arXiv 2602.13889) reports 99 % top-1 with released models; general VLMs
  are poor at font ID (arXiv 2503.23768).
