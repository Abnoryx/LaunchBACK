# Library

Everything reusable for the style, not only shots: `catalog.json` indexes templates, transitions, camera moves,
text styles, fonts, palettes, eases, finishes, assets, SFX and music, each with its source, status and score.

- `aeb.py` — authoring layer (scenes in the engine's format, eases as cubic-beziers).
- `style.py` — the style system every template pulls from.
- `templates/` — parameterised shots (`build(project, name, **params)`), proven against the reel with original content.
- `transitions.py` + `transitions/` — each transition saved as its own asset: spec `.json` + `.mp4` preview on neutral A/B cards (`python3 -m extract.transitions_export <run>`).
- `assets/` — our own assets (drawn or generated); `make_assets.py` makes them.
- Proving a template: `scratch/prove_<name>.py` fills it with the original content → render/fit (`scratch/fit.py`) → visual check → score.
- Additions need the user's approval (see ../REQUIREMENTS.md).
