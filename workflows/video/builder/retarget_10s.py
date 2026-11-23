"""10-second test: retarget the creator's own comps (The Psychology Trick) to our script, red accent.

Shots (OG master time -> our time), each a time-stretched copy of their comp:
  A  S1  (WONDER/car)  0.000-3.233 -> 0.00-2.70   "Free recipes. A paid cookbook."
  B  S1b (brain/disc)  3.233-4.733 -> 2.70-3.68   "Why?"
  C  S3  (iPhone)      8.300-11.500 -> 3.68-5.95  "The Step-By-Step Chef offers both."
  D  S4  (IKEA) + wipe 11.500-15.567 -> 5.95-9.25 "...camping recipes in his book are also free on his website."
Their transition comp (lens-blur pulses, minimax smears, RGB time split, shake) is remapped with the same time map.

usage: python3 retarget_10s.py psych.json vo_words.json assets_dir out.json
"""
import colorsys
import copy
import json
import sys

SRC, WORDS, ASSETS, OUT = sys.argv[1:5]
P = json.load(open(SRC))
words = json.load(open(WORDS))
C = {c["name"]: c for c in P["comps"]}
F = 1 / 30

SEG = [  # (og_start, og_end, our_start, our_end)
    (0.000, 3.233, 0.00, 2.70),
    (3.233, 4.733, 2.70, 3.68),
    (8.300, 11.500, 3.68, 5.95),
    (11.500, 15.567, 5.95, 9.25),
]
DUR = 9.25


def omap(t):
    """OG master time -> our time (None if outside every kept segment, with 0.5 s grace at the edges)."""
    best = None
    for a, b, x, y in SEG:
        k = (y - x) / (b - a)
        if a <= t <= b:
            return x + (t - a) * k
        d = a - t if t < a else t - b
        if d <= 0.5 and (best is None or d < best[0]):
            best = (d, x + (t - a) * k)
    return best[1] if best else None


def at(word, n=0):
    k = 0
    for s, e, w in words:
        if w.lower().strip(".,?!") == word:
            if k == n:
                return s
            k += 1
    raise KeyError(word)


nid = [900000]


def new_id():
    nid[0] += 1
    return nid[0]


def walk_props(node, fn):
    fn(node)
    for c in node.get("c", []) or []:
        walk_props(c, fn)


def layer_props(L, fn):
    for p in L["props"]:
        walk_props(p, fn)


# ------------------------------------------------------------------ red accent: rotate greens to reds
def to_red(rgb):
    r, g, b = rgb[:3]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if s < 0.18 or not (0.17 <= h <= 0.50):  # only greens
        return rgb
    nh = (h - 1 / 3) % 1.0  # green (120 deg) -> red (0 deg), keeps relative hue offsets
    nl = min(0.62, l * 1.08)
    nr, ng, nb = colorsys.hls_to_rgb(nh, nl, min(1.0, s * 1.02))
    return [nr, ng, nb] + list(rgb[3:])


def is_color(v):
    return isinstance(v, list) and len(v) in (3, 4) and all(isinstance(x, (int, float)) and 0 <= x <= 1.0001 for x in v)


def recolor_all():
    def fix(node):
        m = node.get("m", "")
        colorish = "Color" in node.get("n", "") or "Color" in m or m.endswith("-0001") or m.endswith("-0002") or "Fill" in m or "Stroke" in m or "Tint" in m
        if colorish and "v" in node and is_color(node["v"]):
            node["v"] = to_red(node["v"])
        if colorish and "k" in node:
            for k in node["k"]:
                if is_color(k["v"]):
                    k["v"] = to_red(k["v"])
        if isinstance(node.get("v"), dict) and node["v"].get("_text") and node["v"].get("fill"):
            node["v"]["fill"] = to_red(node["v"]["fill"])
    for c in P["comps"]:
        for L in c["layers"]:
            t = L.get("text")
            if t:
                for k in ("fill_color", "stroke_color"):
                    if t.get(k) and is_color(t[k]):
                        t[k] = to_red(t[k])
            layer_props(L, fix)
    for f in P["footage"]:
        if f.get("color") and is_color(f["color"]):
            f["color"] = to_red(f["color"])


# ------------------------------------------------------------------ text swaps + reveal re-timing
def set_text(L, text, refit=True):
    t = L["text"]
    old = t.get("text", "")
    t["text"] = text
    if refit:
        ratio = max(0.5, min(1.5, len(old.strip()) / max(1, len(text.strip()))))
        t["font_size"] = t["font_size"] * ratio
    def fix(node):
        if node.get("m") == "ADBE Text Document":
            if "v" in node and isinstance(node["v"], dict):
                node["v"]["text"] = text
                node["v"]["size"] = t["font_size"]
            for k in node.get("k", []) or []:
                if isinstance(k["v"], dict):
                    k["v"]["text"] = text
                    k["v"]["size"] = t["font_size"]
    layer_props(L, fix)


def retime_reveal(L, local_target):
    """Shift every key under the text animators so the first one lands on local_target."""
    keys = []
    def grab(node):
        if node.get("k"):
            keys.extend(node["k"])
    for p in L["props"]:
        if p["m"] == "ADBE Text Properties":
            for c in p["c"]:
                if c["m"] == "ADBE Text Animators":
                    walk_props(c, grab)
    if not keys:
        return
    d = local_target - min(k["t"] for k in keys)
    for k in keys:
        k["t"] += d
    L["in_point"] = min(L["in_point"], local_target)


def lay(comp, name, nth=0):
    hits = [L for L in comp["layers"] if L["name"].strip() == name.strip()]
    return hits[nth]


def shot_local(shot, T):
    """our global time -> OG time inside that shot's comp (inverse of the shot's linear stretch)."""
    a, b, x, y = SEG[shot]
    return a + (T - x) * (b - a) / (y - x)


def say(shot, comp_offset, word, n=0):
    """local comp time for a reveal that starts 2 frames before the word is spoken."""
    return shot_local(shot, at(word, n) - 2 * F) - comp_offset


# ------------------------------------------------------------------ new footage
def add_file(path, w, h):
    f = {"id": new_id(), "name": path.split("/")[-1], "width": w, "height": h, "duration": 0.0, "frame_rate": 0.0,
         "has_video": True, "pixel_aspect": 1.0, "source_type": "FileSource", "is_still": True, "loop": 1, "file": path}
    P["footage"].append(f)
    return f["id"]


BOOK = add_file(f"{ASSETS}/cut/book_closed.png", 1612, 2094)
OPEN = add_file(f"{ASSETS}/cut/book_open.png", 2248, 1534)

# ------------------------------------------------------------------ shot A + B: Comp 1 layers (S1 = 61-80, S1b = 45-60)
comp1 = C["Comp 1"]


def sub_comp(name, keep):
    c = copy.deepcopy(comp1)
    c["id"], c["name"] = new_id(), name
    c["layers"] = [L for L in c["layers"] if keep(L)]
    P["comps"].append(c)
    return c


A = sub_comp("A", lambda L: 61 <= L["i"] <= 80)
B = sub_comp("B", lambda L: 45 <= L["i"] <= 60)

# A texts: WONDER -> FREE (hero), ever -> recipes., why -> A paid, test drive -> cookbook.; drop "work so well"
set_text(lay(A, "WONDER 2"), "FREE")
retime_reveal(lay(A, "WONDER 2"), max(0.0, say(0, 0, "free")))
set_text(lay(A, "ever"), "recipes.", refit=False)
retime_reveal(lay(A, "ever"), say(0, 0, "recipes"))
set_text(lay(A, "why"), "A paid", refit=False)
retime_reveal(lay(A, "why"), say(0, 0, "a"))
set_text(lay(A, "test drive"), "cookbook.")
retime_reveal(lay(A, "test drive"), say(0, 0, "cookbook"))
lay(A, "work so well")["enabled"] = False
car = lay(A, "car.png")
car["src_id"] = BOOK
for p in car["props"]:
    if p["m"] == "ADBE Transform Group":
        for c in p["c"]:
            if c["m"] == "ADBE Anchor Point":
                c["v"] = [806, 1047, 0]
            if c["m"] == "ADBE Scale":
                c["v"] = [42, 42, 42]

# B texts: "it's called" off, Endowment -> Why, effect -> ?  (the scribble still loops the "?")
lay(B, "it’s called")["enabled"] = False
set_text(lay(B, "Endowment"), "Why", refit=False)
retime_reveal(lay(B, "Endowment"), say(1, 0, "why"))
set_text(lay(B, "effect"), "?", refit=False)
retime_reveal(lay(B, "effect"), say(1, 0, "why") + 4 * F)
set_text(lay(B, "text"), "Every camping recipe is free on his website. So why sell a cookbook?", refit=False)

# ------------------------------------------------------------------ shot C: scene 3 (local 0 = OG 8.3)
S3 = C["scene 3"]
set_text(lay(S3, "Apple"), "Chef")
retime_reveal(lay(S3, "Apple"), say(2, 8.3, "chef"))
set_text(lay(S3, "let you"), "The Step-By-Step", refit=False)
retime_reveal(lay(S3, "let you"), say(2, 8.3, "the"))
set_text(lay(S3, "use the phone"), "offers", refit=False)
retime_reveal(lay(S3, "use the phone"), say(2, 8.3, "offers"))
lay(S3, "before you")["enabled"] = False
set_text(lay(S3, "buy"), "both.", refit=False)
retime_reveal(lay(S3, "buy"), say(2, 8.3, "both"))
set_text(lay(S3, "iphone 15"), "his website", refit=False)
set_text(lay(S3, "text"), "The Step By Step Chef shares his camping recipes for free online, and sells them as a book.", refit=False)
set_text(lay(S3, "earnera.co"), "Step By Step Chef", refit=False)

# ------------------------------------------------------------------ shot D: scene 4 + Comp 1 green wipe
S4 = C["scene 4"]
for nm in ("IKEA", "IKEA 2"):
    set_text(lay(S4, nm), "FREE", refit=False)
    retime_reveal(lay(S4, nm), say(3, 11.5, "free", 1))
set_text(lay(S4, "Good Stuff !!"), "camping recipes", refit=False)
retime_reveal(lay(S4, "Good Stuff !!"), say(3, 11.5, "camping"))
set_text(lay(S4, "invites you to"), "in his book", refit=False)
retime_reveal(lay(S4, "invites you to"), say(3, 11.5, "in"))
set_text(lay(S4, "Sit"), "also", refit=False)
retime_reveal(lay(S4, "Sit"), say(3, 11.5, "also"))
set_text(lay(S4, "touch"), "on his", refit=False)
retime_reveal(lay(S4, "touch"), say(3, 11.5, "on"))
set_text(lay(S4, "imagine ."), "website .", refit=False)
retime_reveal(lay(S4, "imagine ."), say(3, 11.5, "website"))
for nm, tx in (("soft sofa", "free online"), ("top ratted", "in the book"), ("lovely bed", "no printing")):
    set_text(lay(S4, nm), tx, refit=False)
set_text(lay(S4, "text"), "Every recipe from the book is also on his website, free to read and print.", refit=False)
# sofa model card -> open cookbook card (same transform/animation)
for L in S4["layers"]:
    if L["name"] == "chsir" and L.get("enabled"):
        L["src_id"] = OPEN
        for p in L["props"]:
            if p["m"] == "ADBE Transform Group":
                for c in p["c"]:
                    if c["m"] == "ADBE Anchor Point":
                        c["v"] = [1124, 767, 0]
                    if c["m"] == "ADBE Scale" and "v" in c:
                        c["v"] = [c["v"][0] * 0.42, c["v"][1] * 0.42, 100]
                    if c["m"] == "ADBE Scale" and "k" in c:
                        for k in c["k"]:
                            k["v"] = [k["v"][0] * 0.42, k["v"][1] * 0.42, 100]
D = sub_comp("D", lambda L: L["name"] in ("Shape Layer 5",) or (L.get("src") == "scene 4"))
for L in D["layers"]:
    L["start_time"] = L.get("start_time", 0)

# ------------------------------------------------------------------ root comp
root = {"id": new_id(), "name": "test", "w": 1080, "h": 1920, "fps": 30.0, "dur": DUR, "motion_blur": True,
        "shutter_angle": 180, "shutter_phase": -90, "layers": []}
P["comps"].append(root)


def precomp_layer(name, comp, shot):
    a, b, x, y = SEG[shot]
    st = (y - x) / (b - a)
    tr = {"n": "Transform", "m": "ADBE Transform Group", "c": [
        {"n": "Anchor Point", "m": "ADBE Anchor Point", "v": [540, 960, 0]},
        {"n": "Position", "m": "ADBE Position", "v": [540, 960, 0]}]}
    return {"name": name, "type": "AVLayer", "src_id": comp["id"], "in_point": x, "out_point": y,
            "start_time": x - a * st, "stretch": 100 * st, "enabled": True, "blending_mode": 5212,
            "track_matte_type": 5012, "motion_blur": True, "props": [tr]}


shots = [precomp_layer("A", A, 0), precomp_layer("B", B, 1), precomp_layer("C", S3, 2), precomp_layer("D", D, 3)]
# shot C/D comps are scene comps whose local 0 = OG 8.3 / 11.5
shots[2]["start_time"] = SEG[2][2]
shots[2]["stretch"] = 100 * (SEG[2][3] - SEG[2][2]) / (SEG[2][1] - SEG[2][0])

# transition comp layers remapped onto our cuts
T = copy.deepcopy(C["transition"])
fx = []
for L in T["layers"]:
    if L.get("src") == "Comp 1" or not L.get("adjustment_layer"):
        continue
    i0, i1 = omap(L["in_point"]), omap(L["out_point"])
    if i0 is None and i1 is None:
        continue
    L["in_point"], L["out_point"] = max(0.0, i0 if i0 is not None else 0.0), min(DUR, i1 if i1 is not None else DUR)
    if L["out_point"] - L["in_point"] < F / 2:
        continue
    def remap(node):
        if node.get("k"):
            ks = [k for k in node["k"] if omap(k["t"]) is not None]
            for k in ks:
                k["t"] = omap(k["t"])
            node["k"] = ks or node["k"][:1]
    layer_props(L, remap)
    fx.append(L)

root["layers"] = fx + shots
for i, L in enumerate(root["layers"]):
    L["i"] = i
    L.pop("parent", None)

recolor_all()
json.dump(P, open(OUT, "w"))
print("root layers:", len(root["layers"]), "| transition fx kept:", [L["name"] for L in fx])
