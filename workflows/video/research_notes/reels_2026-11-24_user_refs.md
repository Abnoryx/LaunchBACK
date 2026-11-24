# Reference reels the user wants studied (2026-11-24)
Source: vidIQ `watch_shortform_content` walkthroughs (AI-written scene breakdowns, 10 credits each). **Frame numbers and easing
values are the tool's estimates, not measurements.** For a measured 30 fps rebuild (/rescene) the user must send the MP4 files.

## DL24UePpHWN — the TRANSITION reference ("only use these", user 2026-11-24; "use less glitch")
Texture-tutorial reel, 40.9 s, ~1.2–1.8 s per shot. Three recipes only, all clean (no glitch):
1. **Snap whip pan / push** (7x): 3–4 frames, shot slides 100% off in a direction (L/R/up/down), heavy directional motion blur
   (~40–60° shutter), incoming shot lands with fast-in / decelerating ease (~cubic-bezier(0.1,0.9,0.2,1)), swoosh SFX.
2. **Hard cut** (9x): 1 frame, between graphic cards/screencasts and the presenter, locked to phrase starts.
3. **Macro push / zoom-in** (4x): 4–5 frames, scale ~100%→250% with centred radial blur, lands at 100% on the incoming macro crop.
Also: pop-in text (0→105→100% over 3 frames), hand-drawn ring draws on in 6 frames, paper-grain textured colour cards.
Implemented in `gen/runs/michelin/stitch3.py` (xfade custom expressions: 9-tap blur, ease-out cubic, 4 frames).

## Other reels to take ideas from (user: "implement these", last step)
- **DQu3nYiCepd** (2.5D parallax, 27.5 s): Photoshop 2D scene separated into 3 planes + AE depth, linear Z dolly with slight tilt; big distressed
  serif header (cream on crimson), white caps in a red pill caption (1–3 words), hand-drawn arrows + serif labels; mostly hard cuts, ~2 s/shot.
- **DaDhDFjAysT** (Vox-style, 29.3 s): sketch/photo **match cuts at peak zoom speed** (exponential 100→250% over 24–30 f, cut on the fastest
  frame, both shots share the scale curve), Posterize Time 12 fps, newsprint paper (#EBE7DF) + red hand-drawn arrows, flat primary shapes,
  one VHS scanline freeze, bottom caption pill 1–3 words.
- **DdB21JrTK6w** (textures tutorial, 44.8 s): split screen (top art / bottom presenter) with a thin red divider, **corner-peel reveal**
  (diagonal curl bottom-right→top-left, 8–10 f), diagonal page slides, wipe-applied textures, dark rounded UI menu card with a tracking
  highlight pill, yellow-on-black headline banner with red border, 4-frame scale-up section headers.
