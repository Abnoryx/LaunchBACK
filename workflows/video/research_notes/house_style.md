# House style: make every video look like it came from the same people (research 2026-11-21)

Problem: we rebuild scenes 1:1 from different Earn Edits projects (psych, stop, sells, gen, Zeigarnik), each with
its own look. Copied as-is they look like 5 different creators. A house-style layer must sit on top of every one.

What the research agrees on (brand motion systems, creator brand kits, sonic branding):
- Recognition comes from a small set of rules repeated every time, not from assets: type, colour, easing,
  timing, transitions, sound. Motion guides (GitHub, Atlassian, Zalando, Morningstar) lock easing + duration as tokens
  and treat the ease curve as the brand's "personality". Never linear.
- Keep it to one short reference (one file / one page), plus reusable templates that enforce it.
- Sonic identity: a 1–3 s sound logo, a fixed SFX palette and loudness spec, used the same way every time.

What we lock (library/style/house.json, read by every template, overrides the source project's values):
1. Palette: paper/dark bases + red accent; every colour in a scene gets remapped to the nearest house colour.
2. Type: one headline font + one body/caption font + one caption style (size, tracking, highlight word in red).
3. Motion: 2 signature eases (one "arrive" overshoot-free cubic, one snappy "punch") + a duration scale
   (e.g. 6/10/16 frames). Template eases are snapped to the nearest house ease.
4. Transitions: the arrow "launch" whip is the signature; max 2 other transitions from the kit.
5. Camera: always moving, same slow-push speed range.
6. Finish: one grade/LUT, grain amount, film-edge variant, mild glitch — applied last to every frame, so differing
   source projects converge.
7. Sound: sound logo on the end sting, fixed SFX set (whoosh, pop, click, riser), VO-led, −14 LUFS.
8. Structure: hook text in the first 1 s, same end logo sting, same safe-zone grid.

Enforce it: a "same creator" check in the scorecard — measure each new video (palette, eases, fonts, loudness, finish
stats) against house.json and against our previous videos; flag drift before render.
