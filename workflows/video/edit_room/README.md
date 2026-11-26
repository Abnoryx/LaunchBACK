# Edit Lab (the Edit Room page) — one shared editor for /gen AND /rescene

**Standing rule (user, 2026-11-26): every version of a /gen or /rescene render ships WITH this lab, the exact current template, until the user approves the final version.** Never ship a render without the lab link; never ship a reduced or older copy.

## Ship checklist (every render version)
1. Preview clips per scene + whole reel -> upload (Artifact `asset:true`) -> `clips.json`.
2. Build: /gen `python3 gen/runs/<run>/edit_room/build_page.py out.html` (writes room.json then calls `build.py`); /rescene `python3 edit_room/room_from_templates.py <lib/<reel>/templates> clips.json room.json "<title>"` then `python3 edit_room/build.py room.json out.html`.
3. **Test twice, both must pass:** `python3 edit_room/tests/make_fixture.py room.json <tmpdir>` then `node edit_room/tests/run.cjs <tmpdir>/page.html` (run it two separate times). It covers load, pin drop, ghosts, grouping, group cards, notes, delete/reset/undo, drag after undo, scene<->reel pins, late snapshot merge, legacy migration, echo, phone 390x664 layout, pre-db saves.
4. Publish with capabilities `db` + `assets`, to the SAME artifact URL for that run (never a new link per version). Header shows the build number.
5. Give the user the link with the render. Stop attaching the lab only after the user approves the final version.

## Working on several runs in parallel (labs never mix)
- **One artifact per run**, registered in `edit_room/labs.json` (`python3 edit_room/lab.py get|set|list`). A run's first version publishes a NEW artifact; every later version republishes to that run's URL. Never publish run B to run A's URL.
- The page data (pins, notes, words) lives in that artifact's own db, so two labs can never see each other's data. The header shows the run id so you can tell labs apart.
- Everything on disk is per run: `gen/runs/<run>/` (room.json, clips.json, work/), test fixtures in their own temp dir, `resolve_pins.py --run gen/runs/<run>` (own manifest, own free port, own engine cache `/tmp/engine-cache-<run>`), so resolvers for different runs can run side by side.
- Use a separate scratch HTML file per run when publishing (e.g. `<scratch>/<run>_lab.html`), not a shared `edit_room.html`.
- Two chat sessions on the SAME run still share one lab: last write wins per document, so coordinate or use separate runs.

## Data model (so nothing "disappears")
- ONE pin store, `pins/reel`, in reel time (+ `groups`, one note per Change). Scene clips are windows onto it: a pin dropped on a clip lands in the reel store; every view shows every pin (dim ghost away from its moment, clickable only near it).
- Old per-scene docs `pins/sNN` are folded into `pins/reel` once and marked `migrated`.
- Writes carry a client id (`by`) and are never applied back to the writer; the first update after load is merged by id (union), later ones replace only if newer and no write is in flight.
- Resolver: `python3 edit_room/resolve_pins.py <dir> --run gen/runs/<run>` reads `pins/reel` (+ legacy sNN).
