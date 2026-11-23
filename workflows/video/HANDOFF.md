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

Where things stand (2026-11-23):
- /gen v2 (2026-11-23): whole library auto-included (gen/library.py), previews of every shot rendered once
  (gen/previews.py -> library/previews/, bought scenes -> /home/user/tpl/previews/, private), CLIP descriptions
  (gen/embed.py; ONNX model from Kaggle kernel 'clip-export', cached in ~/.cache/launchback/clip, fetched automatically),
  fit-only ranking + MMR (gen/shotlist.py), selects video before any build (gen/selects.py). First preview render was
  started 2026-11-23; if library/previews/ is still missing shots, run `python3 -m gen.previews`.
  Michelin dry run: gen/runs/michelin_dry/ (script + beats reconstructed from scratch/michelin.py).
- Stop ("Stop Trying to Please Everyone", Earn Edits, Route A): steps 1-7 done in chat "Please everyone rescene".
  Private files: /home/user/tpl/lib/stop/ (stop.json dump, assets/ incl. luts.json with the measured Colorama LUT,
  templates/shot_NN.json, shots.json, parity_shots.json, r1/ r2/ final/ renders, parity/ scores). Renders need
  `--footage /home/user/tpl/lib/stop/assets --extra "... --luts footage/luts.json"`. Round 2 at 540p: mean SSIM 0.908;
  user said "looks good, no fixes". Full-res final (final/stop_final.mp4; s01/s07/s12 re-rendered locally after the
  text-size fix, Kaggle originals in final/kaggle_orig/) mean SSIM 0.908, APPROVED 2026-11-23. DONE: 17 templates
  stop/s01-s17 + 86 assets in library/catalog.json, tpl backed up to Kaggle.
  Known open gaps (user accepted): s01 glow too big/bright, s06 'Something' glow white (Colorama on shapes, no LUT),
  s11 edge vignette/pill glow, CC Glass shine, stand-in fonts (InkFree, HelveticaNowText-Black, SF Pro).

Earlier (2026-11-21):
- Michelin v2 (quad eases) done: renders/michelin_v2_quad_1080p.mp4. Waiting on the user's ElevenLabs VO to retime.
- Zeigarnik rebuild v2 is weak (SSIM 0.555, video-only guesses). The user will buy the .aep project files
  (Earn Edits) -> rebuild 1:1 from them (allowed now), then apply the original-touch picks in REQUIREMENTS.md.
- Renders run on Kaggle (~0.44 s/frame at 1080p, ~15-45 min per reel incl. queue).
- Reply rule: end every reply with a short status block (current things only).

### /gen v2 dry run (Michelin) — state
- Previews done on CPU: 18 ours (library/previews, committed), 23 sells (private). **stop (17) not rendered yet** — run `python3 -m gen.previews` (CPU, ~1-2 h); until then stop shots rank on words only and float up on short beats.
- Checks: hook -> hero_word OK; no repeats OK; selects.mp4 plays (51 s, 540x960, not committed: contains bought scenes).
- FAIL: "Michelin sells tyres, since 1900." -> desk_flatlay, because that template's stored words were written for the Michelin reel (text match ~6 z). Raising fit.number to 4 does not flip it. Standalone "1900" -> stop shots (no previews). Re-check after stop previews exist; consider giving desk_flatlay neutral default words.

### Library site (`/site`, Vercel)
Built and tested against a mock GitHub API (list, delete template/asset, edit notes, upload, login, path guard). Needs the user's Vercel import + env vars (see README). `zz_site_test` is a throw-away template to delete from the site as the first end-to-end test. Catalog edits are done on the text so the file stays byte-identical except the changed entry.

### /gen Michelin run (2026-11-23, run `gen/runs/michelin/`) — state + lessons
- Plan v3 (23 shots) built by `gen/runs/michelin/build.py` (our templates + bought scenes via `extract.aep_template apply`: text, red accent,
  footage swaps to blank.png for third-party imagery). Rendered on CPU with `render_local.py` (Kaggle was stuck queued; `kgl/render_multi.py`
  renders many projects in one Kaggle job when the queue is free). Stitch: `stitch.py`. Round 2 at 540p: `renders/michelin_gen_r2_540p.mp4`. Not approved yet.
- Lessons: (1) the Kaggle backup lacks `lib/stop` (stop/* shots unusable until re-harvested) and the harvested footage of gen/sells
  (rebuild: unzip zips/*.zip into tpl/x/<reel>, `python3 -m extract.aep_harvest lib/<reel>/<reel>.json x/<reel> <reel>`, copy luts.json into assets/).
  (2) The engine caches video frames in /tmp/engine-cache by footage id+time: `rm -rf /tmp/engine-cache` after swapping video footage.
  (3) `library/assets/logo/*.png` (incl. launchback_src.png) are git-ignored and missing: logo_reveal renders black; the logo sting for shot 23
  was cut from renders/michelin_v2_quad_1080p.mp4. Force-add the logo PNGs once the user re-sends them. (4) gen.previews of bought scenes made
  before the footage was harvested are degraded (missing textures). (5) ElevenLabs key was declined: no VO, timings estimated, no SFX/music yet.
