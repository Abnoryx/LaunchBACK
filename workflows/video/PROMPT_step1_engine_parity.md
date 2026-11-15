# Prompt: Step 1 — lock the engine to the original reel

You are working in `/home/user/LaunchBACK/workflows/video/`. Goal: make our WebGL engine reproduce the creator's own After Effects project **"The Psychology Trick"** so closely that its render matches the posted reel frame by frame. Do not touch our own video yet. This is the measuring stick everything else depends on.

## Ground truth and inputs
- Posted reel (target): `/home/user/tpl/reels/r1.mp4` (720×1280, 30 fps). It matches the project timeline with **zero offset**: all 11 cuts land on the same frames. The last 17 frames are black.
- Parsed project: `/home/user/tpl/an/json/psych.json`. Root comp = **`transition`** ("sound design" is the same plus audio). Footage and 3D models: `"/home/user/tpl/x/psych/The Psychology Trick/The Psychology Trick/(Footage)/"`.
- Research to read FIRST (do not re-derive): `/home/user/tpl/an/research/INDEX.md`, especially:
  - `engine_audit/REPORT.md`: defects D01–D29 with causes and the ordered fix list.
  - `shots_a|b|c|d/REPORT.md`: per-shot, frame-accurate ground truth (colours, sizes, eases, one-frame events, grade, cut recipes).
  - `models3d/REPORT.md`: glTF maths (U = 508 px/unit, default zoom 1500, root-node skip, rotation order, lighting).
  - `camera/SUMMARY.md` + `camera/cam_all.tsv`: per-frame camera solve.
- Engine code: `engine/engine.js` (comp/layer evaluation), `engine/gl.js` (WebGL shaders and effects), `engine/text.js` (text and selectors), `engine/anim.js` (keyframes and expressions), `engine/gltf.js` (3D models), `engine/render.mjs` (headless render driver), `engine/ssim.py` (scoring).
- Render a range: `cd engine && node render.mjs --project /home/user/tpl/an/json/psych.json --footage "<footage dir>" --comp transition --from S --to E [--fps N] --samples 1 --frames-dir <out>`.

## Already done (verify, don't redo)
These are fixed:
- D01 visible matte sources
- D02 disabled shape items
- D07 "?" depth z and text stroke
- Extract, Simple Choker and Motion Tile
- paragraph wrap
- glTF model layers via three.js: the brain, phone and sofa are placed correctly

Halftone cell is 3.7 px; environment intensity is 2.2.

## Work, in this order
Make one change at a time. After each change, re-render the affected shot and score it. Keep a change only if it improves the score or fixes a visible defect without regressing other shots.

1. **Measuring harness.** Write `engine/parity.py`:
   - render each of the 12 shots at 6 fps (samples 1);
   - align each frame to `r1.mp4` (scale both to 360×640; decode the reel colours as BT.709 via `-f rawvideo -pix_fmt rgb24`);
   - output a per-shot table of SSIM, mean absolute difference and a luma-histogram distance;
   - write a side-by-side contact sheet per shot (reel left, engine right).
   
   Save the baseline to `/home/user/tpl/an/parity/baseline.md`.
2. **Remaining cheap defects from the audit fix list.**
   - D03: Optical Flares solid must be transparent. Then draw a simple flare sprite at (1071,1380) with a horizontal streak of about 450 px, flickering every 8–12 f.
   - D04: Stencil Alpha must apply to the full frame.
   - D06: video and gif decode must keep alpha.
   - D15: box-text origin and justification.
   - D17: Character Offset ("Good Stuff !!" decode).
   - D21: true Gaussian mask feather plus mask expansion.
   - D22: Minimax ops 1↔2 are swapped.
   - D23: AE-style wiggle.
3. **Mixed text style runs.** Extend the dump (`py_aep` text document runs) and `text.js` so one text layer can mix font, size and colour. Examples: "work so / **well**" (171 px #0BC000), "with **someone**", the coloured dots in "needs ." and "imagine .", "**&** it becomes theirs", "without **selling**".
4. **Temporal RGB split.** S_TimeWarpRGB is R from t+1 frame, B from t−1 frame, G from t. Render the comp at t±1 frame and combine the channels. Drop the fixed-offset approximation. Check against cuts f114–126, f201–213, f455–467 and f967–979.
5. **Grade.**
   - Fit a 3D LUT per Magic Bullet Looks layer from reel-vs-engine pixel pairs on the dark shots (S2, S5, S7, S8b, S9).
   - Target: black #001011, whites about 245, greens −35 to 50 % saturation (S2 warm black #161613; S7 #030603).
   - Paper shots stay ungraded.
6. **Remaining effects:**
   - QCA radial fringing: about 5 px at the frame edges, inside the diamond edge-blur layers.
   - S_ScanLines: 35°, period 2.7 px, ±3 levels.
   - Color Balance (HLS) hue: the glove cuff.
   - Sharpen, Roughen Edges, Set Matte.
   - CC Page Turn: a dark flap about 5–6 f per flip, back colour #0F2C0C.
   - CC Light Sweep edge rims.
7. **3D calibration.** Match the brain (≈ #ABA8AE silver with colour halftone), the phone back panel (≈ #9D9D9D after Tint and Curves) and the sofa colours at 12.3 s (#9E6E27 / #8F5920 / #704814), using the calibration targets in `models3d/REPORT.md`. Add the bed (S5) and the second brain (S8a).
8. **Fonts.** Use real font files if the user has supplied them (look in `/home/user/tpl/fonts/`). Otherwise use the best metric-compatible free substitutes, measured per string against the reel widths in `shots_d/REPORT.md`, with vertical and horizontal scale applied.

## Acceptance criteria
- Per-shot SSIM against the reel: **≥ 0.80 on paper shots** (S1, S1b, S3, S4, S6, S8a, S10) and **≥ 0.70 on dark shots** (S2, S5, S7, S8b, S9).
- No placeholder colours, and no layer silently skipped: every layer in `psych.json` draws or is listed as unsupported in the log.
- All 11 cuts match the reel within ±1 frame in a ±6-frame strip.
- Deliver `/home/user/tpl/an/parity/final.md` (scores before and after per shot), plus a full side-by-side MP4 (reel | engine) for the user.

## Rules
- Run ONE job at a time; no parallel agents (usage limits).
- Commit engine changes to branch `claude/compassionate-faraday-nusqe9` in small, described commits, and push. Never commit template footage, models, fonts or renders.
- Don't touch `builder/` or our video until the acceptance criteria are met.
- Report progress after each numbered item: what changed, the score table, anything still failing.
