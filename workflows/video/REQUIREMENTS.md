# Video workflow: standing requirements from the user

Read this before any video work. Every rule below came from the user; keep it current when they add more.

## Goal
- Make Instagram/TikTok reels in the exact style of "The Psychology Trick" (EarnEdits AE project, posted reel `r1.mp4`). Take most if not all inspiration from that reel.
- Our videos use a **red accent** instead of the original's green.
- Bar for "1:1": you cannot tell ours from the original side by side (blind test) and SSIM vs the reel of 0.92–0.95 on paper/text shots, 0.85+ on asset-heavy shots. A literal 1.0 is impossible and was agreed not to be the target.
- The workflow must be repeatable for as many videos as the user wants; it ends packaged as a skill.

## How to build
- **1:1 from the bought project files, then an original touch** (user rule 2026-11-21, replaces "from scratch"): the user buys the template .aep files (e.g. Earn Edits) so we may use them directly — copy layouts, timings, eases, effects and their assets for the 1:1 rebuild. Every video we make then gets an original touch (our brand, accent, props, type, motifs) chosen by the user from options. Still never commit their files/fonts/renders to git (licence: use, not redistribution) — keep them in the private template folder.
- **Earn Edits scenes may be used exactly** (user, 2026-11-21: they have permission): scenes from the Earn Edits .aep files can go into the library and our videos as-is (layouts, animation, effects, their assets), not only as reference. /rescene's "measure, never copy their pixels" applies only to reels we don't own. Files stay in the private template folder, not git.
- **Original touch picks** (user, 2026-11-21): standard on every video = (1) brand motion kit: red accent, LaunchBack arrow replaces generic marks, arrow "launch" whip transition, same end logo sting; (2) signature type: one font pairing + one caption style; (3) retime to the user's VO/beats + own SFX set; (4) own prop world in one consistent look; (6) own finish: grade, grain, film-edge variant, mild glitch. Not chosen: (5) open-loop story ending.
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
- Commit code to the session's branch and push, then fast-forward `main` to it (user rule, 2026-11-22: "merge the branch to main") so every new chat starts with the latest. Do not commit their template files, fonts or renders. Our own small generated assets may be committed so they survive the ephemeral container.
- Keep the user's personal info private.
- Higgsfield: the user approved generation spend; image generation is ~0.25 credits each. Original guidance was 50–60 credits, hard cap 100, for a project — quote anything large first.
- Remind the user of `ROADMAP.md` after a few rounds of video tweaks.
- **GPU work goes to Kaggle** (user rule, 2026-11-21): renders and anything that needs or benefits from a GPU (rescene heavy stages, AI models) run on the user's free Kaggle GPU (private notebooks, T4, ~30 h/week) via the Kaggle REST API at www.kaggle.com/api/v1 (key saved on the environment; the new CLI uses api.kaggle.com, which is not allowed). Not Higgsfield GPUs. Fall back to this CPU only if Kaggle is down or out of quota, and say so.
- **Don't ask before the next step of an agreed pipeline** (user rule, 2026-11-21): e.g. /rescene Route A steps run back to back; only stop for real blockers or the user's own decisions.
- **Render rounds** (user rule, 2026-11-22): every scene renders separately (`kgl.render --shots`), and the scenes are stitched together for the showcase. Round 1 at 540p (`--preview 540`) → ask the user for changes and also fix whatever is wrong by my own review → round 2 at 540p → changes if needed → final at full resolution. Re-render only the scenes that changed (`--only`). Round 2 takes the user's notes plus all my own review fixes unless the user excludes one (user rule, 2026-11-22). Before any round is shown, check motion and transitions per scene against the reel (every element animated like the reel, every transition as in the reel, no hard cuts) — stills/SSIM alone missed un-animated scenes in gen r1.
- **Kaggle user name** comes from the cloud environment's `KAGGLE_USER` variable (user rule, 2026-11-22); never write it into the repo.
- **Private files travel between chats via Kaggle** (user rule, 2026-11-22): at the start of any video chat, if `/home/user/tpl` is missing or empty, run `python3 -m kgl.tpl_backup restore` before anything else; at the end of each rescene step that changes `/home/user/tpl` (new reel, renders, templates, LUTs), run `python3 -m kgl.tpl_backup backup`. A finished rescene in one chat is then usable for the video rebuild in the next.
- **Say when a GPU starts** (user rule, 2026-11-22): after pushing a Kaggle job, watch its log for `STATUS running` (kgl.run prints it) and tell the user as soon as it appears; also tell them if it is still queued after 20 min.
- **Library only after the full-res final is approved** (user rule, 2026-11-22): a reel's scene templates and assets go into `library/catalog.json` (private `tpl:` references, final scores) only once the user approves the full-resolution render — never after a 540p round.
- **Two-chat workflow** (user rule, 2026-11-22): one chat runs /rescene to the end (final approved → library → Kaggle backup); a later chat rebuilds a new video from the library templates. Each chat must leave main and the Kaggle backup complete.
- **Explain in simple terms** (user preference, 2026-11-22): short, plain answers; no jargon walls. The user is often on a phone.
- **When Kaggle is queued** (2026-11-22): it can wait 30+ min for a T4. Tell the user, keep the job queued. Options already weighed: Higgsfield GPU (no queue, ~71 credits/h, quote first; the auto-mode check blocks uploading licensed template files to third-party hosts, so a box must pull from the user's private Kaggle dataset); Colab notebook pulling the same dataset (works, but the user found it too manual — don't offer it first); this container's CPU (~8 s/frame full res 1 sample, ~30 s at 4 samples); OpenRouter can't run renders. Speeds on the T4: 540p 1 sample ~0.12 s/frame (whole reel ~3 min), full res 4 samples ~3.5 s/frame (~80-100 min).
- **/gen shot choice** (user rule, 2026-11-23): everything in the library (now and anything added later) is approved and
  usable automatically, no tagging. SSIM, approval stats or anything else must not bias shot choice — only how well a
  shot fits the script beat. Before building, show the exact chosen library shots, untouched, stitched as one video
  (`gen.selects`).
- **End every reply with a short status block** (user rule, 2026-11-21): only what is happening right now (no recap of finished things) — current task + state, what is rendering/running and its time left.

- **Transitions: only the user's transitions reel** (user, 2026-11-24, reel DVR92iPjRIw, NOT DL24UePpHWN): swipe (foreground occlusion), mask zoom, shape reveal, momentum match cut, shape morph, difference glitch (use less glitch: one per reel), hard cut. Nothing else. Shots render to their FULL length (never trimmed to estimated beat times), each held long enough to read, script line burned in as caption. The other four reels are lessons, not style: DQu3nYiCepd = 2.5D camera movement, DL24UePpHWN + DdB21JrTK6w = texturising, DaDhDFjAysT = box/match cuts; implement them last. Notes: `research_notes/reels_2026-11-24_user_refs.md`.

- **/gen builds from ONE group of scenes** (user, 2026-11-24): each group is one rescened video; use most if not all of its scenes, the exact shots, in the original order, so cuts/handoffs/transitions come from the original (the Michelin mix-of-reels video was scrapped because its cuts and transitions looked bad). `python3 -m gen.groups`. Never mix groups except one filler scene for a real gap.
- **One ease family** (user, 2026-11-24): every bezier ease in the scenes becomes the graph in `gen/config.json` `ease` (quad_out now; more graphs later in `library/style.py` EASE_GRAPHS) so scenes from different reels look like one creator's. Done by `extract.aep_template apply` (`ease` param).
- **No texturising** (user, 2026-11-24): /gen never applies texture, blend-mode or displacement passes. (The tutorial notes stay as knowledge only.)

- **Assets are generated, not og** (user, 2026-11-25): in /gen, replace the group's original assets with new Higgsfield-generated (or library) ones that fit the script, in the exact slots the original animates; never blank. Handle = `launch.back` (replaces creator watermarks/post names), LaunchBack mark = `library/assets/launchback_mark.png` (lifted from the logo sting; `needle_logo.png` is the creator's 'e', not ours). Higgsfield: 0.75 credits/image, ~35/5 s video; downloads from the CDN work now.

## Known blockers / asks
- Sells step 8 (original touch) waits on the user's content: new text, images/logo, and the brand red hex.
- (resolved 2026-11-25) Higgsfield CDN downloads work from this environment.
- Fonts: user supplied Coolvetica (regular cuts only; Heavy cuts are paid). Kokila, Didot, Bradley Hand, Times, Helvetica still wanted from the user's own PC/Mac.
- Music: decision pending (their bed is an Artlist screen recording — not licensed for us).
- After Effects: user will buy later when they have a capable computer; templates should stay portable to AE edit lists.

- **Edit Room pins (2026-11-25):** after the first render of a /gen reel, publish the Edit Room with pins; each pin has its own mode (Auto = layer under pin, Precise = exact point, Frame = whole frame), deletable per pin; pins at a cut carry a target (end of N / start of N+1 / the cut). See /gen §6b.
- **Edit Room is one shared editor (2026-11-25):** `workflows/video/edit_room/` serves /gen AND /rescene; pro-editor layout (rail, viewer, timeline, inspector), pins can be grouped into one Change, pins morph between Auto/Precise/Frame shapes.
- **Edit Lab on EVERY version (2026-11-26):** every /gen or /rescene render version (first pass and each round) ships with the current Edit Lab (`workflows/video/edit_room/`, checklist in its README), tested twice (`node edit_room/tests/run.cjs`), published to the same artifact URL, until the user approves the final version. One pin store in reel time; pins never vanish; Delete/Reset visible.
- **REAL assets first (2026-11-28):** /gen must use real-world screenshots (Instagram page/posts/profile, phone and app UI) and real B-roll/photos whenever any is available (own real pages, user files, public-domain/CC0/free-licence footage with credit); generated assets are a last resort and never imitate a real screenshot or real footage. Fetch real assets early and slowly (Wikimedia rate-limits this machine); if none can be fetched, ask the user instead of falling back silently. See /gen §5.
- **No same reel twice in a row (2026-11-28):** /gen never reuses the previous run's source reel (group of scenes); a reel is blocked for 7 days after use (ledger `gen/usage.json`, `python3 -m gen.usage`; `gen.groups` enforces it; record each delivered run). Michelin used `gen` on 2026-11-25, so `gen` is free again on 2026-12-02.
