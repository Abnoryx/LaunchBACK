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

| # | Target | Result |
|---|---|---|
| 1 | S1 `hero_word` ≥ 0.75 | **0.728** — not met (was 0.708). Every word crisp and visible; clip `out/s1_template_sbs.mp4` |
| 2 | Element fitter v2 | **Done.** First pass improved every checked frame (+0.01–0.02); a second pass made all frames worse, so it was reverted — position fitting has converged for S1 |
| 3 | S10 `share_card` ≥ 0.85 | **0.882 — met.** Clip `out/s10_template_sbs.mp4` |
| 4 | S2 type section `word_panel` ≥ 0.80 | **0.928 — met.** Clip `out/s2_word_panel_sbs.mp4` |
| 5 | Library/catalog updated | **Done** (3 templates, new text style, dark film-edge asset, scores and weak spots logged) |

**Fixes found along the way that help every shot:** big near-camera words were rendering soft (raster cap 4x → 8x); the film-edge print was being washed out by the edge blur (now prints on top, crisp); text horizontal/vertical scale and paragraph boxes now work.

**What's holding S1 below 0.75 (needs you):**
- The car: ours is a different model from the reel's rounded long-hood coupe. A closer generation (0.25 credits) would help — send it here like last time.
- WONDER's font: the reel uses Coolvetica *Heavy Comp*; your free pack only has regular weights, so Anton stands in.

**Still blocked:** Higgsfield downloads (allow `d8j0ntlcm91z4.cloudfront.net` from a computer) — needed for the asset-heavy shots (phone, hand, flame, sofa, brain, calendar). Music decision. Kokila/Didot/Helvetica font files.

**Next (pending your OK):** remaining OG shots as templates (S1b, S3–S9 need props), then our video from the templates.
