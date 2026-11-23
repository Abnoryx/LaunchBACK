"""Build the recreated Move the Needle cue as native LaunchBACK layers."""
import json
import os
from pathlib import Path
import struct
import subprocess

from library.aeb import CENTER, EXCLUSION, HOLD, LEFT, P, gaussian, hexc

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
FONT_NAMES = {"Arimo Bold": "Arimo-Bold", "Bodoni Moda Bold Italic": "Didot-BoldItalic"}
# Arimo is metrically compatible with Arial. Fractional em advances support the
# delayed second part of the subtitle while keeping both words independent.
ARIMO_ADVANCES = dict(zip(
    "abcdefghijklmnopqrstuvwxyz ",
    (556,611,556,611,556,333,611,611,278,278,556,278,889,
     611,611,611,611,389,556,333,611,556,778,556,556,500,278),
))


def _keys(values, fps, interpolation=HOLD):
    """Use exact frame times so a shape key cannot round into the next frame."""
    return [
        {"t": i / fps, "v": value, "in": interpolation, "out": interpolation,
         "ie": [[0, 16.667]] * (len(value) if isinstance(value, list) else 1),
         "oe": [[0, 16.667]] * (len(value) if isinstance(value, list) else 1)}
        for i, value in enumerate(values)
    ]


def _key_property(prop, values, fps, interpolation=HOLD):
    if any(value != values[0] for value in values[1:]):
        prop["k"] = _keys(values, fps, interpolation)
    return prop


def _path(points):
    zeros = [[0, 0] for _ in points]
    return {"_shape": 1, "closed": True, "vtx": points, "in": zeros, "out": zeros}


def _shape(comp, samples, fps, suffix="", opacity_scale=1, blur_field=None, blur_factor=1):
    style = samples[0]
    closed = [_path(sample["points"]) for sample in samples]
    path = _key_property(P("Path", "ADBE Vector Shape", v=closed[0]), closed, fps)
    layer = comp.shape(style["id"] + suffix, 0, comp.dur, [
        P("Shape 1", "ADBE Vector Group", children=[
            P("Contents", "ADBE Vectors Group", children=[
                P("Path 1", "ADBE Vector Shape - Group", children=[path]),
                P("Fill 1", "ADBE Vector Graphic - Fill", children=[
                    P("Color", "ADBE Vector Fill Color", v=hexc(style["color"])),
                ]),
            ]),
        ]),
    ])
    # Native transforms default to comp centre. The authored path is already
    # in measured screen coordinates, so make that origin explicit.
    _attach_transform(comp, layer, {
        "pos": [[0, 0]] * len(samples),
        "anchor": [[0, 0]] * len(samples),
        "op": [
            100 * sample["opacity"] * opacity_scale * (not suffix or sample.get("halo", 0) > 0)
            for sample in samples
        ],
    }, fps)
    if blur_field:
        values = [sample.get(blur_field, 0) * blur_factor for sample in samples]
        effect = gaussian(values[0])
        _key_property(effect["c"][0], values, fps)
        comp.effects(layer, effect)
    return layer


def _png_size(path):
    with path.open("rb") as image:
        header = image.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Claude footage must be a PNG. Got {path}")
    return struct.unpack(">II", header[16:24])


def _attach_transform(comp, layer, transforms, fps):
    if not transforms:
        return
    settings = {name: values[0] for name, values in transforms.items()}
    comp.transform(layer, **settings)
    properties = {
        "pos": "ADBE Position", "anchor": "ADBE Anchor Point",
        "scale": "ADBE Scale", "rot": "ADBE Rotate Z", "op": "ADBE Opacity",
    }
    group = next(p for p in layer["props"] if p["m"] == "ADBE Transform Group")
    for name, values in transforms.items():
        _key_property(next(p for p in group["c"] if p["m"] == properties[name]), values, fps)


def _footage(project, comp, samples, fps, root):
    style = samples[0]
    path = root / style["asset"]
    width, height = _png_size(path)
    layer = comp.footage(project.still(path.name, width, height), 0, comp.dur)
    layer["name"] = style["id"]
    def anchor(sample):
        x, y = sample.get("anchor", [.5, .5])
        return [width * x, height * y]
    _attach_transform(comp, layer, {
        "pos": [[sample["x"], sample["y"]] for sample in samples],
        "anchor": [anchor(sample) for sample in samples],
        "scale": [[100 * sample["width"] / width, 100 * sample["height"] / height] for sample in samples],
        "rot": [sample.get("angle", 0) for sample in samples],
        "op": [100 * sample["opacity"] for sample in samples],
    }, fps)


def _glyph_offset(style):
    text = style.get("after", "")
    spacing = style.get("tracking", 0)
    return style["size"] * sum(ARIMO_ADVANCES.get(ch.lower(), 556) + spacing for ch in text) / 1000


def _text(comp, samples, fps):
    style = samples[0]
    if not style["text"]:
        return
    opts = {"blend": EXCLUSION} if style.get("blend") == "exclusion" else {}
    layer = comp.text(style["id"], style["text"], 0, comp.dur,
                      FONT_NAMES.get(style["font"], style["font"]), style["size"], style["color"],
                      tracking=style.get("tracking", 0), justify=CENTER if style["align"] == "center" else LEFT, **opts)
    _attach_transform(comp, layer, {
        "pos": [[sample["x"] + _glyph_offset(sample), sample["y"]] for sample in samples],
        "rot": [sample["angle"] for sample in samples],
        "op": [100 * sample["opacity"] for sample in samples],
    }, fps)


def build(project, name="follow_needle", **params):
    """Append and return the editable comp, accepting the shared shot.json overrides."""
    root = Path(os.environ.get("NEEDLE_TEMPLATE_DIR", DEFAULT_ROOT)).resolve()
    completed = subprocess.run(
        ["node", str(root / "src" / "claude-data.mjs")],
        input=json.dumps(params), text=True, capture_output=True, check=True,
    )
    shot = json.loads(completed.stdout)
    fps, count = shot["fps"], shot["frameCount"]
    comp = project.comp(name, w=shot["width"], h=shot["height"], fps=fps, dur=count / fps)
    # LaunchBACK appends front to back. Three.js samples arrive back to front.
    for samples in reversed(list(zip(*shot["frames"]))):
        style = samples[0]
        kind = style["kind"]
        if kind == "text":
            _text(comp, samples, fps)
        elif kind == "image":
            _footage(project, comp, samples, fps, root)
        else:
            _shape(comp, samples, fps, blur_field="feather" if kind == "wave" else None, blur_factor=.67)
            if any(sample.get("halo", 0) > 0 for sample in samples):
                _shape(comp, samples, fps, suffix=" halo", opacity_scale=.16, blur_field="halo")
    return comp.finalize()
