# Reference reels from the user (2026-11-24) — what each is FOR
Source: vidIQ `watch_shortform_content` walkthroughs (AI-written, 10 credits each). **Frame counts, ease values and settings are the tool's
estimates, not measurements.** For a measured 30 fps rebuild (/rescene) the user must send the MP4 files.
(First pass was wrong: DL24UePpHWN was treated as the transitions reel. It is a texture tutorial.)

## DVR92iPjRIw — TRANSITIONS reference ("only use these, nothing else; less glitch")
"Top 5 transitions for motion designers" tutorial. Moves (saved as assets with previews in `library/transitions/DVR92iPjRIw/`):
- **swipe** (foreground-object occlusion): dark shape crosses right->left (slanted), ~12 f, fast-in/fast-out (peak mid), ~25 px directional blur; the shot changes while the screen is fully covered.
- **mask_zoom** (negative space): camera pushes into a hole in the outgoing shot; the incoming shot grows through it 20% -> 100% while the frame scales >800%; ~16 f, ease cubic-bezier(0.7,0,0.3,1).
- **shape_reveal**: a triangle scales 0 -> 2500% from the centre as an alpha matte onto the next shot; ~16-24 f, ease-in-out.
- **match_cut** (momentum): outgoing accelerates 5 f, cut at peak speed, incoming decelerates 10 f (1:2 ratio) with matching scale/position.
- **diff_glitch**: Difference-blend white solids strobing 1-2 f pulses over ~8 f, then the next shot. Glitchy: ONE use per reel at most.
- **shape morph** (UI card morph): needs element-level morphing, not a whole-shot transition; not built yet.
- hard cut (plain 1-frame cut) is used for angle switches.
Michelin stitch (`gen/runs/michelin/stitch4.py`) uses only these.

## DQu3nYiCepd — 2.5D: camera movement that makes flat art feel 3D
Technique: split the flat scene into depth planes (extreme foreground blur, foreground props, midground subject, background, sky/birds);
put them on different Z; one 3D camera (35 mm-ish lens, depth of field ON, high blur, focus on the hero plane) driven by a controller.
Depth illusion = (1) **parallax**: near planes move faster than far ones, (2) **occlusion/reveal**: foreground slides across and uncovers
the background, (3) **shallow DoF**: foreground and far plane soft. Moves: Z **dolly/push-in** (near objects leave frame fast), X/Y **truck/pan**,
subtle **tilt**. Key rule: **scale-compensate** every layer when it is moved in Z so the first frame looks identical to the flat design
(the `Depth` script's "Disperse" does that). Mistakes: no scale compensation, no bleed past the frame edges, planes too close in Z (no parallax).
Engine how-to: plane at z with size = 2*tan(fov/2)*(camZ - z)*aspect (compensation), `depthWrite:false`, camera dolly/truck with easing, DoF blur per plane by |z - focus|.

## DL24UePpHWN + DdB21JrTK6w — TEXTURISING
Source textures from texturelabs.org / texturefabrik.com; combine a broad surface (faded newspaper) with a tight one (macro paper grain).
**Do not lower opacity** (washes out contrast). Instead: stack texture layers above the graphic with a blend mode, remap luminance with
**Curves/Levels** on the texture, and add **Displacement Map** (luminance for H and V, ~2-5 px) on the graphic so its edges follow the paper fibres.
Blend mode by texture type (DdB21): **Darken group** (Multiply/Darken/Color Burn) for textures on WHITE (halftone, newsprint) — white drops out;
**Lighten group** (Screen/Add/Dodge) for textures on BLACK (dust, scratches, fold lines) — black drops out; **Contrast group** (Overlay/Soft Light/Hard Light/Pin Light)
for textures around 50% grey (concrete, plaster, grain) — grey is neutral; **Difference group** (Difference/Exclusion) for holographic/iridescent foil (inverted, chromatic).
Prep: crush paper white to pure 1.0 before Multiply, black to 0.0 before Screen, neutral grey to 0.5 before Overlay. Mistakes: Screen on white (blows out), Multiply on black (crushes), dirty edges.
Engine how-to: per-shot texture pass = displace graphic UVs by texture luma (0.003-0.008), curve the texture, then the matching blend formula
(Multiply `b*t`, Screen `1-(1-b)(1-t)`, Overlay piecewise, Pin Light, Difference `|b-t|`) at full strength, intensity set by the curve, not opacity.

## DaDhDFjAysT — BOX / MATCH CUTS ("cutting the curve")
Two shots aligned on the same focal point share ONE scale curve; cut on the frame of **peak velocity** so the eye follows the move, not the swap.
Method: align focal points -> animate Scale on shot 1 (100% -> ~153% over ~19-22 f) -> Speed Graph: steep bell curve (strong ease, peak >1500 %/s) ->
**parent** shot 2 to shot 1 so it inherits the identical scale/position -> trim out/in exactly at the speed apex (~frame 14 of 19) ->
optional **Posterize Time** at 12 fps over both for the editorial feel. Bad version: cut on a slow/linear part or with unlinked curves.
Engine how-to: one shared scale function `s(t)=1+0.53*steepEase(t/D)`, show A before the apex frame and B after, both at the same `s(t)` and anchor; quantise time to 1/12 s for the stepped look.
(Implemented as the `match_cut` transition recipe; a full A/B asset-pair version with real shared anchors is still to build.)

## To implement (user: "as a last step")
2.5D camera shots (plane stack + Z dolly + DoF), texture pass for our shots (curves + displacement + blend by texture type), real match-cut shot pairs, Posterize 12 fps finish.
