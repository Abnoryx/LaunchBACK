"""Build projects in the engine's AE-dump format (comps -> layers -> property trees).

The helpers encode the building blocks measured in the reference projects (earner.co reels),
so a video is assembled from the same parameters the creator uses in After Effects.
"""
import json

LINEAR, BEZIER, HOLD = 6612, 6613, 6614
BLEND = {"normal": 5212, "multiply": 5216, "screen": 5222, "overlay": 5226, "soft_light": 5227,
         "add": 5220, "difference": 5233, "exclusion": 5235, "stencil_alpha": 5240}
MATTE = {"alpha": 5013, "alpha_inv": 5014, "luma": 5015, "luma_inv": 5016}

# Ease presets as (out-influence of first key, in-influence of second key), speeds 0.
# Measured in the reference projects: snap-in cb(0,0,0,1), whip-out cb(1,0,1,1), reposition cb(.8,0,.2,1).
EASES = {
    "snap": (0.01, 100.0),     # fast start, long settle  (entries)
    "whip": (100.0, 0.01),     # slow start, hits the cut at full speed (exits)
    "smooth": (80.0, 80.0),    # in-shot repositions
    "ease": (33.333, 33.333),  # AE easy ease
}


def P(name, match, v=None, keys=None, expr=None):
    d = {"n": name, "m": match}
    if keys is not None:
        d["k"] = keys
    else:
        d["v"] = v
    if expr:
        d["x"] = expr
    return d


def G(name, match, *children, **extra):
    d = {"n": name, "m": match, "c": [c for c in children if c]}
    d.update(extra)
    return d


def keys(*pts, ease="linear"):
    """pts: (t, v) pairs. ease: linear | hold | snap | whip | smooth | ease, or a list per segment."""
    out = []
    n = len(pts)
    eases = ease if isinstance(ease, list) else [ease] * max(1, n - 1)
    for i, (t, v) in enumerate(pts):
        dim = len(v) if isinstance(v, (list, tuple)) else 1
        k = {"t": t, "v": list(v) if isinstance(v, (list, tuple)) else v, "in": BEZIER, "out": BEZIER,
             "ie": [[0.0, 16.667]], "oe": [[0.0, 16.667]]}
        e_out = eases[i] if i < n - 1 else None
        e_in = eases[i - 1] if i > 0 else None
        # outgoing side
        if e_out == "hold":
            k["out"] = HOLD
        elif e_out == "linear":
            t1, v1 = pts[i + 1]
            k["out"] = LINEAR
            k["oe"] = [[_speed(v, v1, t1 - t), 16.667]]
        elif e_out:
            k["oe"] = [[0.0, EASES[e_out][0]]]
        # incoming side
        if e_in == "hold":
            k["in"] = HOLD
        elif e_in == "linear":
            t0, v0 = pts[i - 1]
            k["in"] = LINEAR
            k["ie"] = [[_speed(v0, v, t - t0), 16.667]]
        elif e_in:
            k["ie"] = [[0.0, EASES[e_in][1]]]
        if dim > 1 and not _spatial_ok(v):
            k["ie"] = k["ie"] * dim
            k["oe"] = k["oe"] * dim
        out.append(k)
    return out


def _spatial_ok(v):
    return True  # multi-dim values use one shared ease (spatial/position-style)


def _speed(a, b, dt):
    if isinstance(a, (list, tuple)):
        return sum((y - x) ** 2 for x, y in zip(a, b)) ** 0.5 / dt
    return (b - a) / dt


class Project:
    def __init__(self):
        self.comps, self.footage, self._id = [], [], 1000

    def nid(self):
        self._id += 1
        return self._id

    def file(self, path, w, h, still=True, duration=0.0, fps=0.0):
        f = {"id": self.nid(), "name": path.split("/")[-1], "width": w, "height": h, "duration": duration,
             "frame_rate": fps, "has_video": True, "pixel_aspect": 1.0, "source_type": "FileSource",
             "is_still": still, "loop": 1, "file": path}
        self.footage.append(f)
        return f["id"]

    def solid(self, color, w=1080, h=1920, name="Solid"):
        f = {"id": self.nid(), "name": name, "width": w, "height": h, "duration": 0.0, "frame_rate": 0.0,
             "has_video": True, "pixel_aspect": 1.0, "source_type": "SolidSource", "is_still": True, "loop": 1,
             "color": list(color)}
        self.footage.append(f)
        return f["id"]

    def comp(self, name, w=1080, h=1920, fps=30.0, dur=10.0, motion_blur=True):
        c = Comp(self, name, w, h, fps, dur, motion_blur)
        self.comps.append(c)
        return c

    def to_json(self):
        return {"ae_version": "builder", "comps": [c.to_json() for c in self.comps], "footage": self.footage}

    def save(self, path):
        with open(path, "w") as fh:
            json.dump(self.to_json(), fh)


class Comp:
    def __init__(self, proj, name, w, h, fps, dur, mb):
        self.proj, self.name, self.w, self.h, self.fps, self.dur, self.mb = proj, name, w, h, fps, dur, mb
        self.id = proj.nid()
        self.layers = []  # top first

    def to_json(self):
        return {"id": self.id, "name": self.name, "w": self.w, "h": self.h, "fps": self.fps, "dur": self.dur,
                "motion_blur": self.mb, "shutter_angle": 180, "shutter_phase": -90,
                "layers": [dict(L, i=i) for i, L in enumerate(self.layers)]}

    # -- generic layer
    def add(self, name, typ, inp, outp, *, src=None, three_d=False, parent=None, blend="normal", mb=True,
            transform=None, effects=None, masks=None, extra_props=None, adjustment=False, null=False,
            collapse=False, matte=None, matte_layer=None, text=None, below=None):
        L = {"name": name, "type": typ, "in_point": inp, "out_point": outp, "start_time": 0.0, "stretch": 100.0,
             "enabled": True, "blending_mode": BLEND[blend], "track_matte_type": 5012, "props": []}
        if src is not None:
            L["src_id"] = src
        if three_d:
            L["three_d_layer"] = True
        if parent is not None:
            L["_parent_ref"] = parent
        if mb:
            L["motion_blur"] = True
        if adjustment:
            L["adjustment_layer"] = True
        if null:
            L["null_layer"] = True
        if collapse:
            L["collapse_transformation"] = True
        if text is not None:
            L["text"] = text
        if matte:
            L["has_track_matte"] = True
            L["track_matte_type"] = MATTE[matte]
            L["_matte_ref"] = matte_layer
        if masks:
            L["props"].append(G("Masks", "ADBE Mask Parade", *masks))
        if effects:
            L["props"].append(G("Effects", "ADBE Effect Parade", *effects))
        if extra_props:
            L["props"].extend(extra_props)
        L["props"].append(transform_group(**(transform or {})))
        self.layers.append(L)
        return L

    def finalize(self):
        """Resolve parent / matte references to layer indices (top = 0)."""
        for L in self.layers:
            if "_parent_ref" in L:
                L["parent"] = self.layers.index(L.pop("_parent_ref"))
            if "_matte_ref" in L:
                ref = L.pop("_matte_ref")
                L["matte_layer"] = self.layers.index(ref)
                ref["is_track_matte"] = True


def transform_group(anchor=None, pos=None, scale=None, ori=None, rx=None, ry=None, rz=None, opacity=None):
    def item(name, m, v):
        if v is None:
            return None
        if isinstance(v, dict) and "keys" in v:
            return P(name, m, keys=v["keys"], expr=v.get("expr"))
        if isinstance(v, dict) and "expr" in v:
            return P(name, m, v=v["v"], expr=v["expr"])
        return P(name, m, v=v)
    return G("Transform", "ADBE Transform Group",
             item("Anchor Point", "ADBE Anchor Point", anchor), item("Position", "ADBE Position", pos),
             item("Scale", "ADBE Scale", scale), item("Orientation", "ADBE Orientation", ori),
             item("X Rotation", "ADBE Rotate X", rx), item("Y Rotation", "ADBE Rotate Y", ry),
             item("Z Rotation", "ADBE Rotate Z", rz), item("Opacity", "ADBE Opacity", opacity))


# ------------------------------------------------------------------ text
def text_doc(text, font="Helvetica-Bold", size=90, fill=(0.05, 0.05, 0.05), tracking=-80, justify="left",
             hscale=1.0, vscale=1.0):
    return {"text": text, "font": font, "font_size": size, "fill_color": list(fill), "tracking": tracking,
            "justification": {"left": 7413, "right": 7414, "center": 7415}[justify],
            "horizontal_scale": hscale, "vertical_scale": vscale}


def reveal_animator(t0, dur=10 / 30, based_on=3, blur=10, dy=0, shape=2, ease_low=100, ease_high=47, random=False):
    """The creator's standard word reveal: Range Selector (words, ramp up) Offset -100 -> 100 linear,
    animating Opacity 0 + Blur (and optionally Position y)."""
    sel = G("Range Selector 1", "ADBE Text Selector",
            P("Offset", "ADBE Text Percent Offset", keys=keys((t0, -100.0), (t0 + dur, 100.0), ease="linear")),
            G("Advanced", "ADBE Text Range Advanced",
              P("Based On", "ADBE Text Range Type2", 3 if based_on == 3 else based_on),
              P("Shape", "ADBE Text Range Shape", shape),
              P("Ease High", "ADBE Text Levels Max Ease", ease_high),
              P("Ease Low", "ADBE Text Levels Min Ease", ease_low),
              P("Randomize Order", "ADBE Text Randomize Order", 1.0 if random else 0.0)))
    props = [P("Opacity", "ADBE Text Opacity", 0.0), P("Blur", "ADBE Text Blur", [blur, blur])]
    if dy:
        props.append(P("Position", "ADBE Text Position 3D", [0, dy, 0]))
    return G("Animator 1", "ADBE Text Animator", G("Selectors", "ADBE Text Selectors", sel),
             G("Properties", "ADBE Text Animator Properties", *props))


def text_props(doc, animators):
    return G("Text", "ADBE Text Properties",
             P("Source Text", "ADBE Text Document", {"_text": 1, "text": doc["text"], "font": doc["font"],
                                                     "size": doc["font_size"], "fill": doc["fill_color"],
                                                     "tracking": doc["tracking"]}),
             G("Animators", "ADBE Text Animators", *animators))


# ------------------------------------------------------------------ effects
def fx(name, match, **params):
    """params: suffix -> value, e.g. fx('Tint','ADBE Tint', _0001=[...])."""
    kids = []
    for k, v in params.items():
        if k.startswith("_"):
            kids.append(P(k[1:], f"{match}-{k[1:]}", v=v))
        else:
            kids.append(P(k.replace("_", " "), f"{match}-{k}", v=v))
    return G(name, match, *kids)


def fx_named(name, match, items):
    """items: list of (param name, value or {'keys':..}) matched by name in the engine."""
    kids = []
    for n, v in items:
        if isinstance(v, dict) and "keys" in v:
            kids.append(P(n, f"{match}-{n}", keys=v["keys"], expr=v.get("expr")))
        else:
            kids.append(P(n, f"{match}-{n}", v=v))
    return G(name, match, *kids)


def mask_rect(x0, y0, x1, y1, feather=0, inverted=False, mode=6813):
    sh = {"_shape": 1, "closed": True, "vtx": [[x1, y0], [x0, y0], [x0, y1], [x1, y1]],
          "in": [[0, 0]] * 4, "out": [[0, 0]] * 4}
    kids = [P("Mask Path", "ADBE Mask Shape", sh)]
    if feather:
        kids.append(P("Mask Feather", "ADBE Mask Feather", [feather, feather]))
    m = G("Mask 1", "ADBE Mask Atom", *kids, mode=mode)
    if inverted:
        m["inv"] = True
    return m
