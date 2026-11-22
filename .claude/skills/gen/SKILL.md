---
name: gen
description: "Turn a full video script into a finished LaunchBack reel: creative direction, shot list from the template library, reused or generated props, voice-over in the user's cloned voice, render, two-pass check, send — the way the Michelin reel was made, and smarter every run. Use whenever the user types /gen with a script, pastes a script and asks for a video/reel/short, or asks to make a video from a script — even if they don't say 'gen'."
---

# /gen — script in, finished reel out, better every run

Everything lives in `workflows/video/` (`gen/` = this skill's code). Follow the repo rules in
`workflows/video/REQUIREMENTS.md` over anything here: one job at a time, check twice before showing, Kaggle for
renders, quote credits first, short status block at the end of every reply, original-touch picks 1/2/3/4/6.

## 0. Load what earlier runs learned
Read `REQUIREMENTS.md`, `ROADMAP.md`, `gen/LEARNINGS.md`, `gen/rules.json` and `library/catalog.json` (templates
with features + approval stats). Name the run: `gen/runs/<name>/`; save the script there as `script.txt`.

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

## 4. Shot list -> `gen/runs/<name>/plan.json` + sign-off
`python3 -m gen.shotlist gen/runs/<name>/beats.json` ranks templates per beat from features + learned stats (approved
shots rise, rejected sink, no repeats). Pick with judgement, write `plan.json`:
`{"shots":[{"template","text","seconds","world","invert","text_px","elements","assets":[...],"params":{...}}]}`,
last shot `logo_reveal`. Gaps -> `cine_scene` (data-driven) or a new template (flag it).
`python3 -m gen.score gen/runs/<name>/plan.json` must say OK (rules + everything learned). Fix, then show the user a
shot table + the brief. **No spend and no build before the user signs off.**

## 5. Assets — reuse first
For each prop: `python3 -m gen.shotlist --assets <tags>` searches `library/assets/index.json`. Reuse, re-tint or
re-light what exists. Only gaps: quote Higgsfield credits, generate in one consistent prop look (pick #4), cut out,
check (turntable for 3D: `scratch/model_turntable_all.py`), add to the index.

## 6. Build, check, render
`gen/runs/<name>/build.py` in the `scratch/michelin.py` pattern (one template build per shot -> master comp, VO
timings). Strip-check each shot with CPU stills first. Render with `python3 -m gen.render <project.json> <out.mp4>
<comps...>` (backend from `gen/config.json`; today Kaggle, ~15–45 min). Check twice: every 3rd frame + every cut at
full rate (text readable and on screen, props right, transitions clean, nothing static). Fix, re-render. Add VO +
whoosh per cut + own SFX, mix to −14 LUFS. Commit (force-add the render) and send.

## 7. Learn — automatic, EVERY run (don't skip, don't wait to be asked)
- `python3 -m gen.learn pick <name>` once the plan is built.
- Every user note: `python3 -m gen.learn note <name> "<note verbatim>" "<what I changed>"`; when it can be checked
  automatically add `--rule "<python expr over s, a shot dict>" --why "<rule>"` (e.g. `--rule "s.get('text_px',99)<80"
  --why "text too small on phone"`) so `gen.score` catches it next time.
- Verdicts: `python3 -m gen.learn shot <name> <template> approved|rejected`, then `outcome <name> approved|rejected`.
- Before keeping any change to /gen itself: `python3 -m gen.check` (all past approved plans must still pass).
- Approved new shots become library templates (add `gen` features to `library/catalog.json`); new props join the index.
- Commit + push `gen/runs/<name>/` and the updated rules, stats and learnings.

## Not built yet (say so when relevant)
ElevenLabs needs connecting (key + voice id). Music bed selection, automatic SFX library, render backends other than
Kaggle/local CPU.
