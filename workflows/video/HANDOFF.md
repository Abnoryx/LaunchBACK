# Handoff for a new chat (read with REQUIREMENTS.md, ROADMAP.md, extract/LEARNINGS.md)

In git (safe): rules (REQUIREMENTS.md), plan (ROADMAP.md), /rescene skill (.claude/skills/rescene), extractor +
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

Where things stand (2026-11-21):
- Michelin v2 (quad eases) done: renders/michelin_v2_quad_1080p.mp4. Waiting on the user's ElevenLabs VO to retime.
- Zeigarnik rebuild v2 is weak (SSIM 0.555, video-only guesses). The user will buy the .aep project files
  (Earn Edits) -> rebuild 1:1 from them (allowed now), then apply the original-touch picks in REQUIREMENTS.md.
- Renders run on Kaggle (~0.44 s/frame at 1080p, ~15-45 min per reel incl. queue).
- Reply rule: end every reply with a short status block (current things only).
