---
name: gen
description: "Turn a full video script into a finished LaunchBack reel: creative direction, shot list from the template library, reused or generated props, voice-over in the user's cloned voice, render, two-pass check, send — the way the Michelin reel was made, and smarter every run. Use whenever the user types /gen with a script, pastes a script and asks for a video/reel/short, or asks to make a video from a script — even if they don't say 'gen'."
---

## Always land on main
Everything this skill produces or changes (code, runs, learnings, library entries, renders, skill edits) must be
committed and pushed to `main` — not left on a side branch. Merge any work from other branches into `main` as well.

# /gen — script in, finished reel out, better every run

Everything lives in `workflows/video/` (`gen/` = this skill's code). Follow the repo rules in
`workflows/video/REQUIREMENTS.md` over anything here: one job at a time, check twice before showing, Kaggle for
renders, quote credits first, short status block at the end of every reply, original-touch picks 1/2/3/4/6.

## Models — required
Run /gen on the **latest Sonnet** (currently `claude-sonnet-5-5`) as the main model, with **Opus 5.5**
(`claude-opus-5-5`) as the creative advisor. If the session isn't on the latest Sonnet, say so and switch before
starting. Consult the advisor (an Opus 5.5 subagent via the Agent tool, `model: opus`, or `/advisor`) at the
creative decision points — don't skip them, and don't hand it the mechanical work:
- §2: sanity-check the beat sheet and any tighter script wording.
- §3: write or critique the concept, visual spine and brief.
- §4: review the shot list before the sign-off table goes to the user.
- §7: when a user note or rejected shot needs a creative read on what to change.
Sonnet does everything else (voice, scoring, assets, build, render, checks, learning). Give the advisor the script,
brief and `gen/LEARNINGS.md` as context; treat its output as advice, the decisions and the files stay Sonnet's.

## 0. Load what earlier runs learned
Read `REQUIREMENTS.md`, `ROADMAP.md`, `gen/LEARNINGS.md` and `gen/rules.json`. Name the run: `gen/runs/<name>/`; save
the script there as `script.txt`.
**The whole library is approved and auto-included** (user rule): `python3 -m gen.library` lists every shot it finds
(`library/templates/*.py`, `library/catalog.json`, bought .aep scenes in `/home/user/tpl/lib/*/templates`) and every
asset — nothing to register or tag; files added later are picked up on the next run. Then
`python3 -m gen.previews` renders (Kaggle, 540p) only the shots that have no preview yet, exactly as stored, and
describes them with CLIP (`gen.embed`). Ours land in `library/previews/` (commit them); bought scenes in
`/home/user/tpl/previews/` (private, backed up to Kaggle by the script, never git).

## 1. Voice first (if ElevenLabs is connected)
`python3 -m gen.voice gen/runs/<name>/script.txt gen/runs/<name>` -> `vo.mp3` + `words.json` (word timestamps, the
user's cloned voice from `gen/config.json`). Not connected yet -> skip; timing is estimated and retimed later.
First time: ask for the key with the secure credential form (host api.elevenlabs.io, header xi-api-key) and the
voice id. Never ask for keys in chat.

## 2. Beat sheet
`python3 -m gen.beats gen/runs/<name>/script.txt [--words gen/runs/<name>/words.json] > gen/runs/<name>/beats.json`
1–5 on-screen words per beat (text = VO), hook first, payoff last. Check the script shape: hook ≤10 words with a
curiosity gap, short setup, 3–5 punchy points, payoff. Suggest tighter wording to the user if it's weak (never rewrite
silently).

## 3. Creative direction (the Michelin way) -> `gen/runs/<name>/brief.md`
- One-line concept; **visual spine**: 2 recurring props that carry the story (e.g. tyre = money, red book = audience)
  + 1 motif (LaunchBack arrow marks); where they meet = the turn; the ending pays them off into the logo sting.
- World flips paper <-> dark every 1–3 shots; ≤3 invert flashes on world flips; camera never still; a new element
  every ≤0.5 s; kinetic type is the hero (most viewers are muted); phone-first big type and safe margins.
- Brand kit (picks): red accent, one font pairing + one caption style, arrow whip transition, logo sting, own finish.
- Brand care: commentary words only — no third-party logos, mascots or marks.

## 4. Pick ONE group, plan its exact scenes -> `gen/runs/<name>/plan.json` + selects video + sign-off
**User rule (2026-11-24): a reel is built from ONE group of scenes, never a mix.** A group = one rescened video (`python3 -m
gen.groups` lists them: `sells`, `gen`, `stop`, `psych` = our rebuild of the Psychology Trick). Use most (>= 80%, `gen/config.json`
`group.min_scene_use`) if not all of its scenes, the EXACT shots, in the ORIGINAL order, so the cuts, handoffs and transitions
between scenes come straight from the original video (mixing scenes from different videos gave bad cuts and transitions).
```bash
python3 -m gen.groups gen/runs/<name>/script.txt --out gen/runs/<name>/plan.json     # ranks groups, plans the best (--group G to force)
python3 -m gen.score gen/runs/<name>/plan.json                                       # group rules: one group, >=80% of scenes, original order, the ease
```
Ranking = text capacity vs script words + group runtime vs spoken length + share of scenes too dense to read (> 4 words/s). It is a
heuristic: the planner prints the ranking and the per-scene text allotment (first pass, flags scenes that are too fast to read);
fit the allotment to each scene's original text slots by hand, have the advisor review it, and show the user the group choice.
Only if the group has a real gap (no scene for a needed beat) fall back to `gen.shotlist` for ONE filler scene, and say so.
Between scenes keep the original handoff. If a cut or transition must be ADDED, use only the user's transitions reel set
(`library/transitions/DVR92iPjRIw/`: swipe, mask zoom, shape reveal, match cut, hard cut; difference glitch at most once).
**Ease:** every bezier ease in every scene becomes the ONE graph in `gen/config.json` `ease` (`quad_out` now; named graphs in
`library/style.py` `EASE_GRAPHS`, more to come from the user) so scenes look like one creator's. **No texturising** (user, 2026-11-24:
no texture, blend-mode or displacement passes). Then `python3 -m gen.selects gen/runs/<name>/plan.json` -> `selects.mp4`: the
group's scenes exactly as stored, in order (don't commit it if it holds bought scenes). Send it with the scene table (scene, seconds,
allotted text) and the brief. **No spend and no build before the user signs off.**

## 5. Assets — generate new ones with Higgsfield for ANY part (user rule, 2026-11-25)
The scenes of a group come with the original video's assets (wallpapers, photos, B-roll, logos, icons, badges). **Do not leave them as-is, and
never leave a slot empty** (blank slots killed the scene's animation and left nothing to show). For every visible asset that is third-party,
off-topic for the script (a brain in a tyre scene), plain "og stuff", or has no personality, make a NEW one that fits the script's topic:
`gen.shotlist --assets` first (our library: `library/assets/m_*.png` tyre, book, map, toque, pump, cloche, bed, `launchback_mark.png` = the LaunchBack mark lifted from the logo sting; `needle_logo.png` is the creator's "e", NOT ours), otherwise **generate with Higgsfield** (`generate_image`, default `gpt_image_2_6`, ~0.75 credits each; a 5 s video is ~35 credits, so
prefer a generated still animated in our engine over generated video). Tips: stickers/icons on a flat magenta background, keyed out, then a white
die-cut outline; iconic wallpapers/B-roll as 9:16 stills; one consistent look per reel. Quote the total first, keep within the project budget
(hard cap 100 credits), downloads work (host allowed). Fill the exact slots the original animates (footage ids in the scene's template) so the
original animation plays on the new asset. **Handle/brand text:** the user's Instagram handle is `launch.back`: it replaces every creator
watermark/handle (`earnera.co`, post names, profile cards); the LaunchBack mark (`library/assets/launchback_mark.png`) replaces creator logos/avatars (ask the user for the original logo PNG).
UI chrome (notifications, posts, profiles) gets our badges, names and personality, never blank or third-party.

## 6. Build, check, render
Build per scene with `python3 -m extract.aep_template apply <shot_NN.json> <params.json> <out.json>`; params = `texts` (every layer showing the same
original string gets the same new text), `accent` (red), `ease` (`quad_out`, from config), `footage` swaps (blank for third-party imagery: logos,
phones, film stills, people; after swapping video footage run `rm -rf /tmp/engine-cache`, the engine caches video frames by id+time). Render each scene
over its FULL window (never trimmed), keep the original order and handoffs, no extra effects. (The older per-shot build below still describes our own code templates.)
`gen/runs/<name>/build.py` in the `scratch/michelin.py` pattern (one template build per shot -> master comp, VO
timings). Strip-check each shot with CPU stills first. Render with `python3 -m gen.render <project.json> <out.mp4>
<comps...>` (backend from `gen/config.json`; today Kaggle, ~15–45 min). Check twice: every 3rd frame + every cut at
full rate (text readable and on screen, props right, transitions clean, nothing static). Fix, re-render. Add VO +
whoosh per cut + own SFX, mix to −14 LUFS. Commit (force-add the render) and send.

## 6b. EVERY version ships with the Edit Lab (user rule, 2026-11-25/26)

**Mandatory:** the first render AND every later round come with the Edit Lab (the Edit Room page, current shared template in `workflows/video/edit_room/`, full checklist in `edit_room/README.md`) until the user approves the final version. Test it TWICE (`node edit_room/tests/run.cjs`, both runs must pass) before publishing, republish to the same artifact URL, and hand the link over with the render. Don't ask the user to describe scenes in chat, let them point.
Data model: ONE pin store in reel time (`pins/reel`); scene clips are windows onto it; nothing disappears when switching views. Pins on any view are dim ghosts away from their moment. Delete: × on every row, Delete on a change, Reset pins (two taps, undoable).
1. Cut per-scene preview clips + the whole reel, upload them (Artifact `asset:true`), write `edit_room/clips.json`, `python3 gen/runs/<run>/edit_room/build_page.py out.html` (writes room.json, then the SHARED builder `workflows/video/edit_room/build.py` + `template.html`), publish with capabilities `db` + `assets`. The same page serves /rescene (`edit_room/room_from_templates.py`). Layout: scene rail | viewer | inspector (Pins / Words / Project), transport + timeline with scene blocks and pin markers; on a phone the viewer and timeline stay pinned. Keys: Space, ←/→ frame, ⇧ 1 s, [ ] scene, P pin tool, 1/2/3 mode, Del.
2. The page has **pins** on the reel and on every scene clip. Each pin has its own mode (changeable and deletable per pin):
   - **Auto** = selects the thing under the pin (the flying guy, a text card, a badge).
   - **Precise** = exactly the tapped point, no snapping.
   - **Frame** = the whole frame (zoom, colour, pacing).
   Pins are tap-to-select, then act on the selection (action bar): set mode, **Group as one change** (letter A, B…; shared note, dashed link on the video and a span bar on the timeline), Add to an existing change, Ungroup, Delete. Select by checkbox, Shift/Ctrl-click, the Multi toggle (touch), or clicking timeline markers. A change's **+ Pin** keeps adding pins to that change until Done. Pins are draggable (selection moves together); Ctrl/Cmd+Z / Shift+Z undo and redo; G group, U ungroup, N/Shift+N next/previous pin, 1/2/3 mode, Esc clears. Pin mode is explicit (tap = play/pause otherwise); activation is on release and only if the finger didn't travel. Writes carry a client id so a saved-doc echo never overwrites newer local pins. Auto pins morph into the layer's box once resolved. Motion rule for the page: one spring (CSS `linear()`, 2% overshoot) on everything that moves, shapes morph (size/radius) instead of popping, persistent elements updated in place (never rebuilt per frame), our own morphing loader instead of the browser's grey play icon (transparent `poster`), thumbnails load two at a time after the main clip.
   A pin dropped within 0.3 s of a cut gets target chips: end of scene N / start of scene N+1 / the cut itself (transition). Reel pins are mapped to a scene by the running total of scene durations (`DATA.cuts`).
3. When the user says "apply my edits": read `pins/*` and `scenes/*` with ArtifactData (out_dir), then `python3 edit_room/resolve_pins.py <dir> --out resolved.json`. Auto pins are resolved exactly, not guessed: the engine's serve mode shows ONE layer at a time (`setOnly`, cameras and parents stay on), the top-most layer with alpha at the pin pixel wins, recursing into precomps; full-frame backdrops (>80% coverage) are skipped. Output per pin: layer chain, bbox, and the text slot / footage swap it belongs to (so the fix goes to `slots.json` / SWAP in build.py). Takes ~15 s per scene with Auto pins; Frame pins cost nothing.
4. Apply the edits, re-render ONLY scenes that have a pin or changed words, re-stitch, republish. Write `resolved:{label,bbox}` back to each pin doc (ArtifactData update) so the page shows the box.
5. Limits: Auto sees the project's layers, not baked pixels — a pin on baked footage returns "nothing owns this pixel" and is treated as Precise. The adjustment-layer shake is off during hit-testing, so boxes can be a few px off in shaky scenes. Optional pixel fallback (not built): SAM 2 on the rendered frame.
Kill the engine with `kill`, not `terminate` (it ignores SIGTERM and hangs the wait).

## 7. Learn — automatic, EVERY run (don't skip, don't wait to be asked)
Learning works through the user's notes turning into rules — never through popularity stats (they don't rank shots).
- `python3 -m gen.learn pick <name>` once the plan is built (logs the picks in the run).
- Every user note: `python3 -m gen.learn note <name> "<note verbatim>" "<what I changed>"`; when it can be checked
  automatically add `--rule "<python expr over s, a shot dict>" --why "<rule>"` (e.g. `--rule "s.get('text_px',99)<80"
  --why "text too small on phone"`) so `gen.score` catches it next time.
- Verdicts: `python3 -m gen.learn shot <name> <template> approved|rejected`, then `outcome <name> approved|rejected`
  (logged in the run; `gen.check` keeps approved plans passing).
- Before keeping any change to /gen itself: `python3 -m gen.check` (all past approved plans must still pass).
- New shots/props: just put the file in the library — the next run finds it, renders its preview and describes it.
- Commit + push `gen/runs/<name>/`, new `library/previews/`, and the updated rules and learnings.

## Not built yet (say so when relevant)
ElevenLabs needs connecting (key + voice id). Music bed selection, automatic SFX library, render backends other than
Kaggle/local CPU.
