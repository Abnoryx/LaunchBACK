"""'Same recipes. Less hassle.' in the style of earner.co's 'The Psychology Trick'.

Run: python3 build_sbsc.py <assets_dir> <psych_footage_dir> <out.json>
"""
import json
import sys

from ae import (Project, G, P, keys, text_doc, reveal_animator, text_props, fx, fx_named, mask_rect)

ASSETS, PSYCH, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
FPS, F = 30.0, 1 / 30
W, H = 1080, 1920
DUR = 24.40

# palette (measured from The Psychology Trick)
PAPER, CREAM, WHITE, FINAL = (0.918, 0.918, 0.918), (1.0, 0.984, 0.945), (1, 1, 1), (0.969, 0.969, 0.969)
INK, LIGHT = (0.051, 0.051, 0.051), (0.92, 0.92, 0.92)
GREEN, DEEP, BAND, BOX = (0.016, 0.796, 0.0), (0.094, 0.388, 0.0), (0.027, 0.247, 0.0), (0.212, 0.682, 0.290)

words = json.load(open(f"{ASSETS}/audio/vo_edit_words.json"))


def at(word, nth=0):
    """Start time of the nth occurrence of a word in the VO (case/punct-insensitive)."""
    k = 0
    for s, e, w in words:
        if w.lower().strip(".,?!") == word.lower():
            if k == nth:
                return s
            k += 1
    raise KeyError(word)


p = Project()
main = p.comp("main", W, H, FPS, DUR, motion_blur=True)
NULL_SRC = p.solid((1, 1, 1), 100, 100, "null")
SOL = {}


def solid(color):
    key = tuple(round(c, 3) for c in color)
    if key not in SOL:
        SOL[key] = p.solid(color, W, H, f"solid {key}")
    return SOL[key]


film = p.file(f"{PSYCH}/(Footage)/7b5fa151219f73421cdf5def86583fba (1).jpg", 904, 1080)
dust = p.file(f"{PSYCH}/(Footage)/Subtle Film Dust Overlay [HD].mp4", 1920, 1080, still=False, duration=20.0, fps=30)
lensdirt = p.file(f"{PSYCH}/(Footage)/Arsacre - Lens dirt texture.png", 1920, 1080)
IMG = {n: p.file(f"{ASSETS}/cut/{n}.png", *sz) for n, sz in {
    "book_closed": (1612, 2094), "book_open": (2248, 1534), "hand": (2164, 1500), "meal": (2263, 1663),
    "mug": (1721, 1682), "page": (1570, 2143), "phone_site": (1263, 2253), "pile": (2261, 1657),
    "printer": (2130, 1716), "lantern": (1055, 2281)}.items()}

layers_by_shot = []  # list of (inp, outp, [layer builders]) appended in draw order (bottom first)


# ------------------------------------------------------------------ building blocks
class Shot:
    def __init__(self, inp, outp, enter=(0, 0, 1), exit=(0, 0, 1), off=420, drift=60):
        self.inp, self.outp = inp, outp
        self.items = []   # bottom-to-top
        # camera rig: null (snap-in / whip-out) -> camera (slow linear dolly)
        ex, ey, ez = enter
        xx, xy, xz = exit
        o = off
        start = [540 - ex * o, 960 - ey * o, -ez * o * 1.6]
        end = [540 + xx * o, 960 + xy * o, xz * o * 1.6]
        rest = [540, 960, 0]
        kp = [(inp, start), (inp + 10 * F, rest), (outp - 10 * F, rest), (outp, end)]
        self.null = main.add("rig", "AVLayer", inp, outp, src=NULL_SRC, three_d=True, null=True, mb=True,
                             transform={"anchor": [0, 0, 0], "pos": {"keys": keys(*kp, ease=["snap", "hold", "whip"])}})
        self.cam = main.add("Camera", "CameraLayer", inp, outp, parent=self.null,
                            transform={"pos": {"keys": keys((inp, [0, 0, -1050]), (outp, [0, 0, -1050 + drift]), ease="linear")}},
                            extra_props=[G("Camera Options", "ADBE Camera Options Group", P("Zoom", "ADBE Camera Zoom", 1050.0))])

    def bg(self, color):
        main.add("bg", "AVLayer", self.inp, self.outp, src=solid(color), mb=False)

    def film_edge(self, dark=False):
        # inverted Kodak Portra film strip: Tint black<->white, multiply on paper / screen on black, window masked out
        main.add("film edge", "AVLayer", self.inp, self.outp, src=film, mb=False, blend="screen" if dark else "multiply",
                 transform={"pos": [521, 938, 0], "scale": [119.469, 177.778, 100]},
                 masks=[mask_rect(106.2, 97.6, 847.6, 1015.4, inverted=True)],
                 effects=[] if dark else [fx("Tint", "ADBE Tint", _0001=[1, 1, 1, 1], _0002=[0, 0, 0, 1])])

    def glow(self, x=540, y=1000, r=520, color=(0.0, 0.596, 0.102), op=55):
        g = G("Contents", "ADBE Root Vectors Group", G("Glow", "ADBE Vector Group", G("Contents", "ADBE Vectors Group",
              G("Ellipse", "ADBE Vector Shape - Ellipse", P("Size", "ADBE Vector Ellipse Size", [r, r]), P("Position", "ADBE Vector Ellipse Position", [0, 0])),
              G("Fill", "ADBE Vector Graphic - Fill", P("Color", "ADBE Vector Fill Color", [*color, 1]), P("Opacity", "ADBE Vector Fill Opacity", 100.0)))))
        main.add("glow", "ShapeLayer", self.inp, self.outp, mb=False, blend="screen", extra_props=[g],
                 effects=[fx("Fast Box Blur", "ADBE Box Blur2", _0001=200.0)], transform={"pos": [x, y, 0], "opacity": op})

    def void_atmos(self):
        main.add("dust", "AVLayer", self.inp, self.outp, src=dust, blend="screen", mb=False,
                 transform={"pos": [540, 960, 0], "scale": [178, 178, 100], "opacity": 70})
        main.add("lens dirt", "AVLayer", self.inp, self.outp, src=lensdirt, blend="screen", mb=False,
                 transform={"pos": [540, 960, 0], "scale": [178, 178, 100], "opacity": 35})

    def word(self, text, t, x, y, z=0, size=96, font="Helvetica-Bold", color=INK, dur=10 * F, blur=10, dy=0,
             justify="left", hscale=1.0, band=None, tracking=-80, random=False, based_on=3):
        k = 1050.0 / (1050.0 + z)               # perspective scale at rest (camera z = -1050)
        x, y, size = 540 + (x - 540) / k, 960 + (y - 960) / k, size / k
        doc = text_doc(text, font, size, color, tracking, justify, hscale)
        tr = {"pos": [x, y, z]}
        if hscale != 1.0:
            tr["scale"] = [100 * hscale, 100, 100]
        anim = [reveal_animator(t - 2 * F, dur, blur=blur, dy=dy, random=random, based_on=based_on)]
        L = main.add(text, "TextLayer", max(self.inp, t - 2 * F), self.outp, three_d=True, text=doc, mb=True,
                     extra_props=[text_props(doc, anim)], transform=tr)
        if band:  # duotone ink band: same word, darker fill, visible only in a feathered strip low in the glyphs
            d2 = dict(doc, fill_color=list(band))
            main.add(text + " band", "TextLayer", max(self.inp, t - 2 * F), self.outp, three_d=True, text=d2, mb=True,
                     extra_props=[text_props(d2, [reveal_animator(t - 2 * F, dur, blur=blur, dy=dy)])], transform=dict(tr),
                     masks=[mask_rect(-size * len(text) - 200, -0.40 * size, size * len(text) + 200, -0.12 * size, feather=0.18 * size)])
        return L

    def prop(self, name, t, x, y, z=300, scale=40, rot=0, halftone=True, shadow=True, pop="snap", rise=0):
        k = 1050.0 / (1050.0 + z)
        x, y, scale = 540 + (x - 540) / k, 960 + (y - 960) / k, scale / k
        eff = []
        eff.append(fx("Tint", "ADBE Tint", _0001=[0, 0, 0, 1], _0002=[1, 1, 1, 1]))
        if halftone:
            eff.append(fx_named("BCC Halftone", "BCC Halftone", [("Cell", 4.5), ("Ink", [0.1, 0.1, 0.1, 1]), ("Paper", [0.93, 0.93, 0.93, 1])]))
        if shadow:
            eff.append(fx("Drop Shadow", "ADBE Drop Shadow", _0001=[0, 0, 0, 1], _0002=110.0, _0004=40.0, _0005=80.0))
        tin = max(self.inp, t)
        sc = {"keys": keys((tin, [scale * 0.86] * 3), (tin + 12 * F, [scale] * 3), ease="snap")} if pop else [scale] * 3
        pos = {"keys": keys((tin, [x, y + rise, z]), (tin + 12 * F, [x, y, z]), ease="snap")} if rise else [x, y, z]
        op = {"keys": keys((tin, 0.0), (tin + 4 * F, 100.0), ease="linear")}
        return main.add(name, "AVLayer", tin, self.outp, src=IMG[name], three_d=True, mb=True, effects=eff,
                        transform={"pos": pos, "scale": sc, "rz": rot, "opacity": op})

    def box(self, t, x, y, w, h, z=0, color=BOX, dur=10 * F):
        """green highlight-marker box growing from zero width (cb(.8,0,.2,1)) behind a word; x,y = left/centre."""
        k = 1050.0 / (1050.0 + z)
        x, y, w, h = 540 + (x - 540) / k, 960 + (y - 960) / k, w / k, h / k
        rect = G("Contents", "ADBE Root Vectors Group",
                 G("Box", "ADBE Vector Group", G("Contents", "ADBE Vectors Group",
                   G("Rect", "ADBE Vector Shape - Rect",
                     P("Size", "ADBE Vector Rect Size", keys=keys((t, [0, h]), (t + dur, [w, h]), ease="smooth")),
                     P("Position", "ADBE Vector Rect Position", keys=keys((t, [0, 0]), (t + dur, [w / 2, 0]), ease="smooth"))),
                   G("Fill", "ADBE Vector Graphic - Fill", P("Color", "ADBE Vector Fill Color", [*color, 1]),
                     P("Opacity", "ADBE Vector Fill Opacity", 100.0)))))
        return main.add("box", "ShapeLayer", t, self.outp, three_d=True, mb=True, extra_props=[rect],
                        transform={"pos": [x, y, z]})

    def qmark(self, t, x, y, z, scale, ori):
        """The creator's extruded 3D '?': 15 copies 4 px apart, back copies 1.25 EV darker."""
        ctrl = main.add("? ctrl", "AVLayer", t, self.outp, src=NULL_SRC, three_d=True, null=True, mb=True,
                        transform={"anchor": [0, 0, 0], "pos": [x, y, z], "scale": {"keys": keys((t, [0, 0, 0]), (t + 10 * F, [scale] * 3), ease="snap")},
                                   "ori": ori})
        for i in range(14, -1, -1):
            doc = text_doc("?", "Helvetica-Bold", 466, (0.247, 0.773, 0.0), 0, "center")
            eff = [fx("Exposure", "ADBE Exposure2", _0003=-1.25)] if i else []
            main.add(f"? {i}", "TextLayer", t, self.outp, three_d=True, text=doc, parent=ctrl, mb=True, effects=eff,
                     extra_props=[text_props(doc, [])], transform={"pos": [0, 0, i * 4]})


def cut_fx(t, strength=20):
    """cut dressing on adjustment layers: lens-blur pulse (0->peak->0 over 20 f), shake spike, 3 f horizontal smear."""
    main.add("cut blur", "AVLayer", t - 10 * F, t + 10 * F, src=solid((1, 1, 1)), adjustment=True, mb=False,
             effects=[fx_named("Camera Lens Blur", "ADBE Camera Lens Blur", [])])
    main.layers[-1]["props"][0]["c"][0]["c"] = [P("Blur Radius", "ADBE Camera Lens Blur-0001",
                                                   keys=keys((t - 10 * F, 0.0), (t, float(strength)), (t + 10 * F, 0.0), ease=["whip", "snap"]))]
    main.add("cut smear", "AVLayer", t - 1 * F, t + 2 * F, src=solid((1, 1, 1)), adjustment=True, mb=False,
             effects=[fx("Minimax", "ADBE Minimax", _0001=2.0, _0002=18.0, _0004=2.0)])
    main.add("cut shake", "AVLayer", t - 2 * F, t + 10 * F, src=solid((1, 1, 1)), adjustment=True, mb=False,
             effects=[G("Slider Control", "ADBE Slider Control",
                        P("Slider", "ADBE Slider Control-0001", keys=keys((t - 2 * F, 0.0), (t + 3 * F, 24.0), (t + 10 * F, 0.0), ease=["snap", "smooth"]))),
                      G("Transform", "ADBE Geometry2",
                        P("Position", "ADBE Geometry2-0002", v=[540, 960], expr='wiggle(9,effect("Slider Control")("Slider"))'),
                        P("Scale Height", "ADBE Geometry2-0003", v=104.0))])


# ------------------------------------------------------------------ shots  (cuts sit in VO pauses)
CUT = [0.0, 1.30, 2.70, 3.55, 5.95, 9.20, 10.90, 12.60, 15.70, 17.85, 20.30, 21.85, DUR]

# S1 paper: FREE / recipes.
s = Shot(CUT[0], CUT[1], enter=(0, 0, 1), exit=(1, 0, 0), drift=70)
s.bg(PAPER); s.film_edge()
s.prop("page", 0.0, 760, 1300, z=420, scale=24, rot=8)
s.word("FREE", at("free"), 150, 1010, z=-120, size=430, font="Coolvetica-HeavyComp", color=GREEN, tracking=0, hscale=1.25, band=DEEP)
s.word("recipes.", at("recipes"), 160, 1170, z=-260, size=118)

# S2 void: A paid / cookbook.
s = Shot(CUT[1], CUT[2], enter=(1, 0, 0), exit=(0, 1, 0), drift=90)
s.bg((0, 0, 0)); s.void_atmos()
s.prop("book_closed", CUT[1], 660, 1400, z=520, scale=28, rot=-9)
s.glow(y=1420); s.word("A paid", at("a"), 160, 820, z=-180, size=104, color=LIGHT)
s.word("cookbook.", at("cookbook"), 150, 1010, z=-320, size=200, font="Kokila-BoldItalic", color=GREEN, band=BAND)

# S3 paper: Why?  + two extruded green question marks
s = Shot(CUT[2], CUT[3], enter=(0, 1, 0), exit=(-1, 0, 0), drift=80)
s.bg(WHITE); s.film_edge()
s.qmark(CUT[2] + 2 * F, 300, 1430, 120, 55, [325.2, 311.6, 329.4])
s.qmark(CUT[2] + 5 * F, 860, 300, 700, 60, [349.6, 16.6, 19.0])
s.word("Why?", at("why"), 540, 1060, z=-200, size=330, color=INK, justify="center", dur=6 * F)

# S4 cream: The Step-By-Step Chef / offers / both.
s = Shot(CUT[3], CUT[4], enter=(-1, 0, 0), exit=(0, 0, 1), drift=110)
s.bg(CREAM); s.film_edge()
s.prop("phone_site", CUT[3] + 4 * F, 330, 1330, z=380, scale=33, rot=-7, halftone=False, rise=120)
s.prop("book_closed", CUT[3] + 8 * F, 780, 1330, z=430, scale=24, rot=8, rise=120)
s.word("The Step-By-Step Chef", at("the"), 150, 720, z=-60, size=80)
s.word("offers", at("offers"), 150, 870, z=-120, size=150, font="Kokila-BoldItalic", color=DEEP)
s.box(at("both") - 4 * F, 560, 832, 330, 150, z=-120)
s.word("both.", at("both"), 585, 870, z=-120, size=140, color=INK)

# S5 white -> black: He says the camping recipes / in his book / are also / free / on his website.
s = Shot(CUT[4], CUT[5], enter=(0, 0, 1), exit=(1, 0, 0), drift=140)
flip = at("are")
main.add("bg white", "AVLayer", CUT[4], flip, src=solid(WHITE), mb=False)
s.film_edge()
s.prop("book_open", CUT[4] + 3 * F, 560, 1380, z=520, scale=27, rot=-4)
s.word("He says the camping recipes", at("he"), 150, 720, z=-40, size=62)
s.word("in his", at("in"), 150, 870, z=-120, size=96)
s.word("book", at("book"), 420, 880, z=-160, size=170, font="Kokila-BoldItalic", color=DEEP)
# black half: the website
main.add("bg black", "AVLayer", flip, CUT[5], src=solid((0, 0, 0)), mb=False)
s2 = s
s.prop("phone_site", flip, 700, 1420, z=260, scale=36, rot=6, halftone=False, rise=160)
s.word("are also", at("are"), 160, 640, z=-200, size=96, color=LIGHT)
s.box(at("free", 1) - 4 * F, 150, 780, 380, 190, z=-260)
s.word("free", at("free", 1), 175, 830, z=-260, size=200, font="Kokila-BoldItalic", color=INK)
s.word("on his website.", at("on"), 160, 970, z=-200, size=84, color=LIGHT)

# S6 void: So why offer / the book?
s = Shot(CUT[5], CUT[6], enter=(1, 0, 0), exit=(0, -1, 0), drift=100)
s.bg((0, 0, 0)); s.void_atmos()
s.prop("book_closed", CUT[5] + 2 * F, 560, 1400, z=600, scale=30, rot=0)
s.glow(y=1420); s.word("So why offer", at("so"), 160, 760, z=-160, size=104, color=LIGHT)
s.word("the book?", at("the", 2), 150, 950, z=-320, size=190, font="Kokila-BoldItalic", color=GREEN, band=BAND)

# S7 paper: Because you can get them / all together  (pages fly into the open book)
s = Shot(CUT[6], CUT[7], enter=(0, -1, 0), exit=(0, 0, 1), drift=90)
s.bg(PAPER); s.film_edge()
s.prop("book_open", CUT[6] + 2 * F, 540, 1380, z=480, scale=28)
for i, (x0, y0, r) in enumerate([(-500, 600, -30), (1500, 900, 25), (-400, 1700, 15), (1500, 1500, -20)]):
    t0 = at("all") - 8 * F + i * 3 * F
    main.add("flying page", "AVLayer", CUT[6], CUT[7], src=IMG["page"], three_d=True, mb=True,
             effects=[fx("Tint", "ADBE Tint", _0001=[0, 0, 0, 1], _0002=[1, 1, 1, 1]),
                      fx_named("BCC Halftone", "BCC Halftone", [("Cell", 4.5)]),
                      fx("Drop Shadow", "ADBE Drop Shadow", _0002=90.0, _0004=30.0, _0005=60.0)],
                     transform={"pos": {"keys": keys((t0, [x0, y0, 200]), (t0 + 14 * F, [540, 1290, 470]), ease="snap")},
                                "scale": {"keys": keys((t0, [20, 20, 20]), (t0 + 14 * F, [9, 9, 9]), ease="snap")},
                                "rz": {"keys": keys((t0, r), (t0 + 14 * F, 0.0), ease="snap")},
                                "opacity": {"keys": keys((t0 + 12 * F, 100.0), (t0 + 15 * F, 0.0), ease="linear")}})
s.word("Because you can get them", at("because"), 150, 700, z=-60, size=66)
s.word("all together", at("all"), 150, 880, z=-200, size=160, font="Kokila-BoldItalic", color=GREEN, band=DEEP)

# S8 paper -> void: without printing / every recipe / yourself.
s = Shot(CUT[7], CUT[8], enter=(0, 0, 1), exit=(-1, 0, 0), drift=160)
flip = at("yourself") - 3 * F
main.add("bg", "AVLayer", CUT[7], flip, src=solid(WHITE), mb=False)
s.film_edge()
s.prop("printer", CUT[7] + 2 * F, 560, 1360, z=460, scale=27)
s.prop("pile", at("every") - 3 * F, 560, 1560, z=300, scale=26, rise=200)
s.word("without", at("without"), 150, 700, z=-60, size=96)
s.word("printing", at("printing"), 150, 900, z=-220, size=200, font="Kokila-BoldItalic", color=DEEP, band=BAND)
s.word("every recipe", at("every"), 160, 1040, z=-120, size=96)
main.add("bg black", "AVLayer", flip, CUT[8], src=solid((0, 0, 0)), mb=False)
s.word("yourself.", at("yourself"), 540, 980, z=-260, size=210, font="Kokila-BoldItalic", color=GREEN, justify="center", band=BAND)

# S9 void + dust: The information's / already there.
s = Shot(CUT[8], CUT[9], enter=(-1, 0, 0), exit=(0, 0, 1), drift=120)
s.bg((0, 0, 0)); s.void_atmos()
s.glow(y=960); s.word("The information's", at("information's"), 540, 900, z=-80, size=96, color=LIGHT, justify="center", dur=18 * F)
s.word("already there.", at("already"), 540, 1060, z=-200, size=130, color=GREEN, justify="center", font="Kokila-BoldItalic")

# S10 paper: The book changes / how you / use it.
s = Shot(CUT[9], CUT[10], enter=(0, 0, 1), exit=(1, 0, 0), drift=100)
s.bg(CREAM); s.film_edge()
s.prop("meal", CUT[9] + 3 * F, 620, 1420, z=420, scale=26, rot=-5)
s.prop("book_open", CUT[9] + 6 * F, 420, 1290, z=640, scale=24, rot=6)
s.word("The book changes", at("the", 4), 150, 700, z=-60, size=90)
s.word("how you", at("how"), 150, 860, z=-120, size=110)
s.box(at("use") - 4 * F, 560, 830, 360, 160, z=-120)
s.word("use it.", at("use"), 585, 870, z=-120, size=150, font="Kokila-BoldItalic", color=INK)

# S11 void: SAME / recipes.
s = Shot(CUT[10], CUT[11], enter=(1, 0, 0), exit=(0, 0, 1), drift=80)
s.bg((0, 0, 0)); s.void_atmos()
s.glow(); s.word("SAME", at("same"), 540, 1030, z=-120, size=470, font="Coolvetica-HeavyComp", color=GREEN, tracking=0, justify="center", band=BAND)
s.word("recipes.", at("recipes", 2), 540, 1180, z=-260, size=118, color=LIGHT, justify="center")

# S12 final card: Less / hassle.
s = Shot(CUT[11], CUT[12], enter=(0, 0, 1), exit=(0, 0, 0), drift=60)
s.bg(FINAL); s.film_edge()
s.prop("lantern", CUT[11] + 4 * F, 800, 1420, z=500, scale=20, rot=6)
s.word("Less", at("less") - 6 * F, 540, 900, z=-80, size=150, justify="center")
s.word("hassle.", at("hassle") + 2 * F, 540, 1110, z=-220, size=260, font="Kokila-BoldItalic", color=GREEN, justify="center", band=DEEP)

for t in CUT[1:-1]:
    cut_fx(t, strength=16)

# The engine draws bottom-to-top from the highest index: we appended bottom-first, so reverse to top-first.
main.layers.reverse()
for c in p.comps:
    c.finalize()
p.save(OUT)
print("layers:", len(main.layers), "->", OUT)
