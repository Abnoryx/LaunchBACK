# forty_hours — brief (advisor: Opus 5.5; decisions: Sonnet)

**Group:** psych (14 scenes, original order, ~34.8 s). No VO yet (ElevenLabs not connected) so timing is estimated; reel ~35 s, not the 26 s in the script labels.
**Concept:** the clean 8 seconds is only the label on 40 messy hours — and the hours are what gets paid for.
**Visual spine:** Prop A = a finished LaunchBack reel frame (clean). Prop B = a stack of layers / version files (v7, v8, v9_FINAL_final). Motif = red playhead + timecode (40:00:00 vs 00:00:08); needle scenes' needle becomes the playhead.
**Colour:** every green -> red; paper/dark flips come from the original scenes.
**Brand care:** remove KODAK PORTRA 400 on film edges, earnera.co, Apple, IKEA, Casper marks; footer = launch.back.

## Script wording suggestions (not applied, user decides)
- Hook says "took forty hours / eight seconds" but reel runs ~35 s: use "This eight-second shot took forty hours." or "The clean part took forty hours."
- "One rebuilt from scratch at two in the morning because the audio changed length by half a second." is long: "One rebuilt at 2am because the audio moved half a second."
- Payoff "build it" has an unclear "it": "...the one who can show it / who did it."

## Scenes (words per slot -> asset)
1 hero_word: what you're watching / FORTY / took / hours / you'll see / it / ? -> Prop A frame; 3D "?" -> red "40h"
2 disc_brain: in about / EIGHT / seconds -> stopwatch 0:08 in red circle
3 word_panel: here's / the same / thing / BEFORE -> red glow
4 hand_flame: it got / CLEAN -> keep hand+flame, red rim
5 word_prop_pop: FORTY / layers / v9_FINAL_final / nine versions / four / deleted -> layer stack (Prop B) replaces iPhone
6 brand_box: ONE / rebuilt / from scratch / at two / in the morning / 2:00 AM -> alarm clock at 02:00
7 calendar_flip: the audio / changed length / by / half / a second -> counter 0.0 -> 0.5 s, waveform strip
8 statement_flip: nobody bought / forty hours / they bought / 8 seconds -> Prop A reveal on the dark flip
9 dark_docs: those hours / made possible / your / expertise -> blurred version-file list, waveform
10 brain_collage: & / runs the same way / ... -> brain = expertise; spinning years -> timecodes
11 flythrough_words: the messy part / is the thing / worth / paying for
12 follow_needle: you just / have to / be the / One -> needle = red playhead, LaunchBack mark
13 needle_solo: who can / Build it.
14 share_card: Send this / SEND / to / someone / who / builds / it. -> then logo sting
Cut points snapped to VO lines: 3.2 / 5.0 / 6.92 / 8.08 / 10.38 / 14.23 / 17.31 / 21.15 / 23.4 / 25.0 / 28.46 / 30.38 / 32.7 (+share_card to ~35).

## Assets: real first
Real/safe: frames of our own launch.back reels; screenshots of our own pipeline (plan.json, runs/ folder, version files). NOT real: After Effects/Premiere panels (Adobe UI) -> generic flat bars + red playhead, no app chrome. Alarm clock/stopwatch: real licensed stock if fetchable, else generated sticker (never screenshot-like). Generated last resort: red "40h", layer-stack cards, waveform. Library: hand, fist, brain.

## Run notes (2026-11-28, user sign-off)
- Wording fixes applied (hook "This eight-second shot took forty hours", "One rebuilt at 2am because the audio moved half a second", payoff "...who can show it").
- Placeholder VO: Higgsfield seed_audio, voice Grady (preset), 3 credits -> vo.mp3. Balance before: 64.47 credits.
- Real-asset candidates (Wikimedia Commons, rate-limited 429 after ~4 queries; retry slowly): alarm clock photos "Classic alarm clock 20180513.jpg" (CC BY-SA 4.0), "Mechanical Alarm Clock.jpg" (CC BY-SA 4.0), "Old alarm clock on the bookshelf - 50233824038.jpg" (CC BY 2.0, credit needed). Stopwatch and clock video searches pending. Mixkit/Coverr free clips = custom licences, check terms before use.
- Credit: alarm_clock.png = cutout of "Classic alarm clock 20180513.jpg", Wikimedia Commons, CC BY-SA 4.0 (author per file page); library/assets/fh_alarm_clock.png. Fetch pattern that works: upload.wikimedia.org/.../thumb/<h>/<hh>/<File>/1280px-<File> (Special:FilePath fails through the proxy); API search is rate limited after ~4 calls.
- Round 1 (540p, Kaggle, placeholder VO mixed -14 LUFS): r1/forty_r1_540_vo.mp4. Own review (pass 1 every 0.5 s): marks gone (KODAK/earnera replaced via build post-process + film_edge pngs restamped LAUNCH.BACK 400), greens -> red, real alarm-clock photo (CC BY-SA 4.0, Wikimedia) in S6/S7. Known issues: S8 scan card mark overlaps the words; S6 'ONE' overlaps itself ('ONENE'); S2 prop is a blank generic phone; no logo sting (logo PNGs missing, see HANDOFF); Prop A is a flat generated card (no real launch.back reel frame supplied); film-edge restamp changes library/assets film_edge*.png for every template.
