# Overnight plan (autopilot, one job at a time)

Rules followed: REQUIREMENTS.md (from scratch, check stills critically before every real render, one job at a time, commit + push).
Note: Higgsfield downloads are blocked (CDN host not allowed), so tonight favours shots built from type, shapes and drawn assets.

## Targets for the morning
1. **S1 `hero_word` finished**: full render scored; fix the top issues found in the still check. Target full-shot SSIM **≥ 0.75** (was 0.708), every word crisp and visible, side-by-side clip in `out/`.
2. **Element fitter v2** (measures each element's box in the reel by colour, solves position/size directly). Validated on S1: it must not make any checked frame worse.
3. **S10 `share_card` template** (the "Share this / SHARE pill / with someone" end card): paper, film edge, pill with drop shadow, user's Coolvetica Condensed, wave wipe in, scale bounce. Target **≥ 0.85**, side-by-side clip.
4. **S2 type section `word_panel`** ("Once" → "something" → dark panel rise with "feels like it's" → YOURS rise): target **≥ 0.80** on the frames without the hand/flame footage.
5. **Library/catalog updated** with every new template, transition, text style and asset (status draft until you approve).
6. **Morning report** at the bottom of this file: scores, clips, what failed, what needs you.

## Morning report
- S1 `hero_word`: full shot **0.716** (target 0.75 not yet met). Fixes: crisp big text (8x raster), edge blur from sharpness grid, thinner near-camera extrusion. Clip: out/s1_template_sbs.mp4.
- S10 `share_card`: **0.882 — target met** (frames 0.89-0.94; card-shrink transition f968-971 weak). Clip: out/s10_template_sbs.mp4. Style fix found here: film-edge print now sits above the edge blur on every paper shot.
- S2 type section `word_panel`: **0.928 — target met** (frames 0.95-0.99; f181-184 between the two wipes weak). Panel words now matted to the panel, mint outline rim on the big word. Clip: out/s2_word_panel_sbs.mp4.
