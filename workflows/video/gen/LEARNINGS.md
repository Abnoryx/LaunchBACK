# /gen learnings (read before every run; `gen.learn note` appends here automatically)

## Standing rules (from the Michelin build and research)
- Hook: <=10 words, a curiosity gap, hero word + camera move in frame 1. Shots 1.5-3 s, a new element every <=0.5 s.
- Text = VO, 1-5 words at a time; one caption style everywhere; big type, phone safe margins.
- Visual spine: 2 recurring props + 1 motif carried through the story; paper <-> dark flips every 1-3 shots;
  <=3 invert flashes; always end on the LaunchBack logo sting.
- Reuse library assets first (gen.shotlist --assets); generate only gaps, one consistent prop look; quote credits.
- Brand care: commentary words only, no third-party logos/mascots/marks.
- Time shots to the user's VO (ElevenLabs words.json) before building when it exists.

## Log
- 2026-11-23 michelin: "Change 2 3 8 12, remove them from the library; the Nike shot isn't a real shot from the library; use the better needle wave shot I gave" -> Removed brain_words, flare_script, pill_diagram, desk_flatlay from the library; replaced shots 2/3/8/12 (gen/s12, gen/s08, sells/s22, sells/s20); dropped gen/s07 (a source clip, not a scene) for gen/s01; adopted the user's move_the_needle shot.json and swapped follow_needle for needle_wave
- 2026-11-24 michelin: "Study these transitions (use less glitch) and only use these nothing else (reel DL24UePpHWN); also study the other reels and implement them as a last step" -> stitch3: only snap whip pan, macro push, hard cut from that reel; notes in research_notes/reels_2026-11-24_user_refs.md
