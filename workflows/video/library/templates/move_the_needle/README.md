# Move the Needle

A silent 1.70-second portrait animation at 720 × 1280, 30 fps. Frame 0 maps to source frame 883, and frame 50 maps to source frame 933.

## Preview and render in Three.js

Requires Node.js 20 or newer and FFmpeg. Install dependencies with `npm ci`. On a machine without system Chromium, run `npx playwright install chromium` or set `CHROMIUM_PATH` to a Chromium executable.

```sh
npm run preview
npm run render -- --out move-the-needle.mp4
npm test
```

Open the local URL printed by the preview command. Pause playback or drag the scrubber to inspect a frame. The preview and encoder both call `renderFrame(frameIndex)`. To export a section, pass `--from` and `--count` in local frames. Add `--frames DIRECTORY` to keep the PNG sequence.

## Edit the shot

- In `shot.json`, change `words` for the CTA, title, watermark, and fine print.
- Adjust `layout.arm` to change the motion. Each row gives source frame, grip x/y, sleeve angle, needle angle, and the distances above and below the grip. The cutout anchor is `layout.hand.gripU` and `gripV` in normalized image coordinates.
- Each entry in `wave.white` and `wave.dark` gives source frame, left-edge x values, and right-edge x values at the y coordinates in `wave.heights`. Coordinates are pixels from the top left. Keep heights and source frames sorted and give each edge one x value per height. Positive `timing.whiteOffset` or `timing.darkOffset` delays the entire corresponding track. White edge softness and halo are under `wave`.
- Put replacement PNGs in `assets/` and update their paths in `shot.json`. Keep image basenames unique for the native renderer.

## Use with Claude’s LaunchBACK renderer

The handoff uses the `library.aeb.Project` and `build(project, name, **params)` conventions from LaunchBACK branch `claude/compassionate-faraday-nusqe9`, tested against commit `944dc4918804c1616acd3b9ab3f36deb67c7e63b`. The adapter builds native text, footage, and shape layers with independent paths for the white wave and dark wipe. It loads the same settings as Three.js and takes nested keyword overrides such as `words={"big": "Signal"}` and `timing={"whiteOffset": 2}`.

From the extracted template directory, set `VIDEO_WORKFLOW` to the absolute path to an installed LaunchBACK video workflow on that branch. Its renderer needs the workflow's npm dependencies, Playwright Chromium, and FFmpeg on the host.

```sh
VIDEO_WORKFLOW=/absolute/path/to/LaunchBACK/workflows/video
PYTHONPATH="$VIDEO_WORKFLOW" python claude/prove.py --out s9.json
node "$VIDEO_WORKFLOW/engine/render.mjs" \
  --project s9.json --footage "$PWD/assets" --comp S9 \
  --from 0 --to 1.7 --samples 1 --out s9-native.mp4
```

Claude can also import `build` from `claude/follow_needle.py` in a builder, pass its existing project, and use the returned comp. If the Python file is copied elsewhere, set `NEEDLE_TEMPLATE_DIR` to the extracted template directory. The adapter uses Node.js to evaluate the shared timeline, then writes editable native keys into the project.

The branch renderer also declares optional fonts at machine-local paths. If those assets are missing on a clean machine, disable their `/file/home/user/tpl/fonts/` declarations in a temporary copy of `engine/page.html`. This shot uses Arimo and Bodoni Moda from the workflow's npm dependencies.

The hand, background plate, logo, and pen are fresh text-prompted GPT Image 2.6 assets. The arm and plate were color-graded for the composite. The reference clip was used to measure the motion and layout.
