---
name: gen
description: "Turn a full video script into a finished LaunchBack reel: creative direction, shot list from the template library, reused or generated props, voice-over in the user's cloned voice, render, two-pass check, send — the way the Michelin reel was made, and smarter every run. Use whenever the user types /gen with a script, pastes a script and asks for a video/reel/short, or asks to make a video from a script — even if they don't say 'gen'."
---

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

## 4. Shot list -> `gen/runs/<name>/plan.json` + selects video + sign-off
`python3 -m gen.shotlist gen/runs/<name>/beats.json [--world dark|paper] [--plan gen/runs/<name>/draft.json]` ranks
EVERY library shot per beat **by fit to the script only**: CLIP similarity of the beat text to the shot's preview frames
and to its words/notes, a role match (hook / number / payoff prompts) and fit rules (words fit its text slots, digits ->
a shot that shows numbers, prop wanted -> a shot with a prop). Picks use MMR (relevance minus similarity to shots
already picked; `select.mmr_lambda` in `gen/config.json`) and never repeat a shot. **SSIM, approval stats and status
never affect the choice** (user rule). The ranked list is the menu: the brief still decides world flips and the spine;
pick with judgement and write `plan.json`:
`{"shots":[{"template","text","seconds","world","invert","text_px","elements","assets":[...],"params":{...}}]}`,
last shot `logo_reveal`. Gaps -> `cine_scene` (data-driven) or a new template (flag it).
`python3 -m gen.score gen/runs/<name>/plan.json` must say OK (rules + everything learned).
Then `python3 -m gen.selects gen/runs/<name>/plan.json` -> `selects.mp4`: the chosen library shots exactly as stored,
trimmed to each beat, in order, with the beat text burned small at the bottom. Send it with the shot table (it prints
one) and the brief. Don't commit a selects video that contains bought scenes (licence). **No spend and no build before
the user signs off.**

## 5. Assets — reuse first
For each prop: `python3 -m gen.shotlist --assets <tags>` searches every asset in the library (`library/assets/**`
and bought .aep libraries in `/home/user/tpl/lib/*/assets`, private: use, never commit), found fresh every run. Reuse, re-tint or
re-light what exists. Only gaps: quote Higgsfield credits, generate in one consistent prop look (pick #4), cut out,
check (turntable for 3D: `scratch/model_turntable_all.py`), add to the index.

## 6. Build, check, render
`gen/runs/<name>/build.py` in the `scratch/michelin.py` pattern (one template build per shot -> master comp, VO
timings). Strip-check each shot with CPU stills first. Render with `python3 -m gen.render <project.json> <out.mp4>
<comps...>` (backend from `gen/config.json`; today Kaggle, ~15–45 min). Check twice: every 3rd frame + every cut at
full rate (text readable and on screen, props right, transitions clean, nothing static). Fix, re-render. Add VO +
whoosh per cut + own SFX, mix to −14 LUFS. Commit (force-add the render) and send.

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
