# Video workflow: standing requirements from the user

Read this before any video work. Every rule below came from the user; keep it current when they add more.

## Goal
- Make Instagram/TikTok reels in the exact style of "The Psychology Trick" (EarnEdits AE project, posted reel `r1.mp4`). Take most if not all inspiration from that reel.
- Our videos use a **red accent** instead of the original's green.
- Bar for "1:1": you cannot tell ours from the original side by side (blind test) and SSIM vs the reel of 0.92–0.95 on paper/text shots, 0.85+ on asset-heavy shots. A literal 1.0 is impossible and was agreed not to be the target.
- The workflow must be repeatable for as many videos as the user wants; it ends packaged as a skill.

## How to build
- **From scratch.** Their reel is the only reference: measure it. Do not render, copy or ship their project files, footage, models, images, music or SFX in the rebuild or in our videos. Our own code, our own assets (generated or drawn), free/user-supplied fonts, our own sound.
- **Template-first.** Each shot is built once as a parameterised template, proven 1:1 against the reel with their content, then reused with our content. No throwaway one-off scenes.
- **Library of everything**, not only shots: shot templates, transitions, camera moves, text styles and font pairings, fonts, palettes, eases, finishes (paper, film edge, grade, edge blur, fringing), assets (props, textures, overlays, 3D models), SFX and music cues. See `library/`.
- Library grows after every video, but **only with the user's approval** (scorecard pass + a yes on a short clip).
- **Check before rendering.** Before any real render: render key stills, compare them full-size with the reel, be critical, and fix every visual flaw first — invisible/cut-off text, wrong or missing font, wrong colour/size/position, missing elements. Use a separate critic pass as well as self-review.
- **Examine everything twice before rendering or showing it** (user rule after the Michelin v0 flatlay): two
  separate full passes over the shot/video — a frame strip every ~3 frames plus every cut at full frame rate — looking
  at every detail: text readable and fully on screen, props right size/colour/position, nothing covering what
  matters, **transitions clean** between every pair of shots (no hard jumps, no leftovers from the previous shot),
  and **nothing that just cuts in or sits still** — every element arrives with motion (reveal, pop, slide, draw) and
  the camera keeps moving. Fix every problem found before the render; say what was checked in the report.
- **Save anything important where it can't be lost.** The container is temporary: finished renders, side-by-sides,
  contact sheets, scene JSONs and generated assets go into git (force-add past .gitignore if needed, or Git LFS for
  big files) and/or get sent to the user right away. Never leave the only copy in the scratchpad or `out/`.
- AutoAE preset renders can't be used: their downloads carry a watermark and we don't remove watermarks.
- Measure everything: per-shot SSIM vs reel, cut timing, sharpness, plus the style scorecard for our own videos.

## Working rules
- Run **one job at a time**; do not spawn many agents in parallel (usage limits). Opus for agents; Fable only as advisor.
- Take it slow, think before answering; research when useful.
- Report outcomes honestly (scores, what failed, what was approximated).
- Commit code to branch `claude/compassionate-faraday-nusqe9` and push. Do not commit their template files, fonts or renders. Our own small generated assets may be committed so they survive the ephemeral container.
- Keep the user's personal info private.
- Higgsfield: the user approved generation spend; image generation is ~0.25 credits each. Original guidance was 50–60 credits, hard cap 100, for a project — quote anything large first.
- Remind the user of `ROADMAP.md` after a few rounds of video tweaks.
- **GPU work goes to Kaggle** (user rule, 2026-11-21): renders and anything that needs or benefits from a GPU (rescene heavy stages, AI models) run on the user's free Kaggle GPU (private notebooks, T4, ~30 h/week) via the Kaggle REST API at www.kaggle.com/api/v1 (key saved on the environment; the new CLI uses api.kaggle.com, which is not allowed). Not Higgsfield GPUs. Fall back to this CPU only if Kaggle is down or out of quota, and say so.
- **End every reply with a status block** (user rule, 2026-11-21): what I am working on and its current state, what is rendering or running (where: Kaggle/CPU) and estimated time left for each.

## Known blockers / asks
- Higgsfield downloads need host `d8j0ntlcm91z4.cloudfront.net` allowed in this environment's network settings (user must do it from a computer). Until then the user sends generated images in chat.
- Fonts: user supplied Coolvetica (regular cuts only; Heavy cuts are paid). Kokila, Didot, Bradley Hand, Times, Helvetica still wanted from the user's own PC/Mac.
- Music: decision pending (their bed is an Artlist screen recording — not licensed for us).
- After Effects: user will buy later when they have a capable computer; templates should stay portable to AE edit lists.
