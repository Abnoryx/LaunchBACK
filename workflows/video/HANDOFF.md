# Handoff for a new chat (read with REQUIREMENTS.md, ROADMAP.md, extract/LEARNINGS.md)

Repo is video-only (old Apify actor removed 2026-11-22); work from `main`.

In git (safe): rules (REQUIREMENTS.md), plan (ROADMAP.md), /rescene skill (.claude/skills/rescene), /gen skill
(.claude/skills/gen + gen/: script -> reel, learns every run), extractor +
lessons (extract/), Kaggle GPU runner (kgl/: `python3 -m kgl.render <project.json> <out.mp4> <comps...>`),
templates (library/templates/), our props (library/assets/z_*, m_*), Michelin + Zeigarnik builds (scratch/), renders.

NOT in git — redo in a new container:
1. `/home/user/tpl/` (the bought template fonts, reels, zips): the engine loads Helvetica Real, Kokila, Didot and
   Coolvetica from /home/user/tpl/fonts by absolute path. Restore it from the private Kaggle backup:
   `cd workflows/video && KAGGLE_USER=<name> python3 -m kgl.tpl_backup restore` (fonts, reels, zips, analysis notes;
   unzip zips/ into x/ if the unpacked projects are needed). Without it renders silently fall back to other fonts.
2. Kaggle username for kgl/: ask the user, then `export KAGGLE_USER=<name>` (the API key itself is already saved on
   the environment for www.kaggle.com). Allowed hosts for Kaggle are already on the environment.
3. The Zeigarnik reel video (uploads are per chat): ask for it again if reworking that reel.

Where things stand (2026-11-22):
- Stop ("Stop Trying to Please Everyone", Earn Edits, Route A): steps 1-7 done in chat "Please everyone rescene".
  Private files: /home/user/tpl/lib/stop/ (stop.json dump, assets/ incl. luts.json with the measured Colorama LUT,
  templates/shot_NN.json, shots.json, parity_shots.json, r1/ r2/ final/ renders, parity/ scores). Renders need
  `--footage /home/user/tpl/lib/stop/assets --extra "... --luts footage/luts.json"`. Round 2 at 540p: mean SSIM 0.908;
  user said "looks good, no fixes" -> full-res final rendered for approval; then step 7b (library) and backup.
  Known open gaps (user accepted): s01 glow too big/bright, s06 'Something' glow white (Colorama on shapes, no LUT),
  s11 edge vignette/pill glow, CC Glass shine, stand-in fonts (InkFree, HelveticaNowText-Black, SF Pro).

Earlier (2026-11-21):
- Michelin v2 (quad eases) done: renders/michelin_v2_quad_1080p.mp4. Waiting on the user's ElevenLabs VO to retime.
- Zeigarnik rebuild v2 is weak (SSIM 0.555, video-only guesses). The user will buy the .aep project files
  (Earn Edits) -> rebuild 1:1 from them (allowed now), then apply the original-touch picks in REQUIREMENTS.md.
- Renders run on Kaggle (~0.44 s/frame at 1080p, ~15-45 min per reel incl. queue).
- Reply rule: end every reply with a short status block (current things only).
