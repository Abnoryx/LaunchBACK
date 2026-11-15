# Roadmap (agreed with the user; remind them after a few rounds of video tweaks)

Done so far: engine reproduces their project at SSIM 0.86 (11/12 shots), all cuts exact — proves the engine can draw this style.
Now: rebuild from scratch, template-first.

1. **Style system** (`library/style/`): paper, film edge, palette (green original / red ours), fonts and text styles, eases, grade, edge blur + fringing, transition kit (whip, minimax flash, lens blur, RGB split, wipes), camera moves, SFX rules. Every template pulls from it.
2. **12 OG shots as templates** (`library/templates/`), each filled with the original's content, auto-fitted and checked against the reel until it passes. Asset-heavy shots judged on layout/motion where our assets differ.
3. **Our video** ("Same recipes. Less hassle.") composed from the templates with our words, props, red accent; user notes; fixes go into templates, not one-offs.
4. **Expand the library** from the creator's other reels (r2–r6: ~40 shot types, 18 transitions), each proven the same way; plus fonts, assets, SFX.
5. **Cold test**: a new script first try, no hand edits; must pass the scorecard + blind test + user approval within one round of notes.
6. **Package the skill**: script → shot plan → templates → assets → render → critic check → score; library grows after every approved video.

Guardrails: library additions need user approval; separate critic before every render; asset pipeline needs the Higgsfield CDN host allowed (from a computer).
