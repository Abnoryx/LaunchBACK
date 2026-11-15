# Roadmap to a perfect clone of the style (saved at the user's request: remind after a few video-generation tweaks)

Ranked by how much each closes the gap with the original reel.

1. **Lock the engine to the original (biggest win).** Render their unmodified project, compare with the reel, fix, and repeat until every shot scores 0.80+ on paper scenes and 0.70+ on dark scenes (now 0.62). Prompt: `PROMPT_step1_engine_parity.md`.
   - Real fonts: Coolvetica (free), plus Kokila, Didot, Bradley Hand, Times and Helvetica from the user's Windows PC and Mac.
   - True one-frame RGB split: red a frame ahead, blue a frame behind.
   - The dark-scene grade as a fitted LUT: black #001011, whites ~245, greens desaturated. Paper scenes stay ungraded.
   - Small effects: glove colour shift, edge fringing, scanlines, optical flare, the "Good Stuff" scramble, page turn, mixed-font words.
2. **Real 3D props.** Cookbook (closed and open, with our cover and engraving), paper stack, mug and skillet built in code. Printer and lantern via image-to-3D (quoted first). Turn the phone so its screen faces the camera at its key moment.
3. **Fit the script to their shots.**
   - Match beats by structure: one hero word, 2–3 helpers, a prop and one gag per shot. For example, "without printing every recipe" goes on the page-turn counter, "information's already there" on the dark flare scene, and "Same recipes. Less hassle." on the SHARE-style end card.
   - Tighten the narration to ≥ 85 % speech, with no pause over 0.6 s.
   - Hero words 230+ px, bleeding off the frame and overlapping a prop.
4. **Sound.** Their music bed or a licensed match (bass-heavy, ~118 BPM, 12 dB under the voice, no ducking, playing over the end). One effect per event, landing 0–3 f before the visual, following their cue sheet.
5. **Repeatable workflow (toward the skill).**
   - Speed: half-resolution previews with 1–2 blur samples, cached 3D renders, full quality only for finals, and a GPU machine later.
   - A shot library: their 12 shots as templates with named slots, plus the 40 shot types and 18 transitions from the other reels.
   - The variety rule: the style stays fixed; content, shot order, props and accent colour change per video.

**Needed from the user:** font files; timestamped notes on each render; a music decision; more of this creator's project files if available.
**Order:** engine-to-original loop and fonts, then 3D props, then script fit and sound, then the shot library and the skill.
