"""Procedural rigged cartoon glove hand -> animated GLB (our own asset, no external files).

A puffy cartoon glove: rounded palm, cuff, four 3-segment fingers and a 2-segment thumb, each segment a capsule on its
own node so the joints can rotate. Poses are joint angles (degrees); an animation clip interpolates between poses over
time, and the engine plays it by layer time. glTF space: y up, fingers along +y, palm facing +z (towards the camera).

usage: python3 make_hand.py   -> library/assets/glove_hand.glb (fist -> open), hand_reach.glb (open -> grasp)"""
import json, math, os, struct
import numpy as np

OUT = os.path.join(os.path.dirname(__file__), 'assets')

FINGERS = [  # name, base x, base y, segment lengths, radius, splay (deg about z when open)
    ('index', -0.34, 0.98, (0.46, 0.33, 0.27), 0.135, 7),
    ('middle', -0.115, 1.03, (0.50, 0.36, 0.28), 0.138, 1),
    ('ring', 0.115, 1.00, (0.46, 0.33, 0.26), 0.132, -5),
    ('pinky', 0.33, 0.90, (0.36, 0.26, 0.22), 0.118, -12),
]
THUMB = ('thumb', -0.46, 0.38, (0.38, 0.32), 0.145)


def capsule(L, r, seg=20, ring=8):
    """Capsule along +y from 0 to L (hemispherical caps), returns positions, normals, indices."""
    rows = []  # (y_center, angle_from_axis) along the profile
    for i in range(ring + 1):
        rows.append((r, -math.pi / 2 + (math.pi / 2) * i / ring))       # bottom cap
    for i in range(ring + 1):
        rows.append((L - r if L > 2 * r else r, (math.pi / 2) * i / ring))  # top cap
    P, N = [], []
    for yc, phi in rows:
        for j in range(seg + 1):
            th = 2 * math.pi * j / seg
            n = (math.cos(phi) * math.cos(th), math.sin(phi), math.cos(phi) * math.sin(th))
            N.append(n); P.append((r * n[0], yc + r * n[1], r * n[2]))
    I = []
    for a in range(len(rows) - 1):
        for j in range(seg):
            p, q = a * (seg + 1) + j, (a + 1) * (seg + 1) + j
            I += [p, q, p + 1, p + 1, q, q + 1]
    return np.array(P, 'f4'), np.array(N, 'f4'), np.array(I, 'u4')


def blob(sx, sy, sz, seg=28, ring=16, squareness=0.35):
    """Rounded box-ish palm: superellipsoid centred at 0."""
    P, N = [], []
    e = 1 - squareness
    sgn = lambda v, p: math.copysign(abs(v) ** p, v)
    for i in range(ring + 1):
        phi = -math.pi / 2 + math.pi * i / ring
        for j in range(seg + 1):
            th = 2 * math.pi * j / seg
            x = sx * sgn(math.cos(phi), e) * sgn(math.cos(th), e); y = sy * sgn(math.sin(phi), e); z = sz * sgn(math.cos(phi), e) * sgn(math.sin(th), e)
            P.append((x, y, z))
            n = np.array([x / sx ** 2, y / sy ** 2, z / sz ** 2]); n /= (np.linalg.norm(n) + 1e-9); N.append(tuple(n))
    I = []
    for a in range(ring):
        for j in range(seg):
            p, q = a * (seg + 1) + j, (a + 1) * (seg + 1) + j
            I += [p, q, p + 1, p + 1, q, q + 1]
    return np.array(P, 'f4'), np.array(N, 'f4'), np.array(I, 'u4')


def quat(ax_deg=0, az_deg=0, ay_deg=0):
    """Rotation X then Z then Y (applied to the child), as a glTF quaternion (x, y, z, w)."""
    def q(axis, a):
        a = math.radians(a) / 2; s = math.sin(a)
        return np.array([axis[0] * s, axis[1] * s, axis[2] * s, math.cos(a)])
    def mul(a, b):
        x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
        return np.array([w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                         w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2])
    return mul(q((0, 1, 0), ay_deg), mul(q((0, 0, 1), az_deg), q((1, 0, 0), ax_deg)))


# poses: per finger (base, mid, tip) curl angles about x, splay scale; thumb (base about z/x, tip curl)
POSES = {
    'open': {'curl': (0, 0, 0), 'splay': 1.0, 'thumb': (0, 0, 0), 'wrist': 0},
    'spread': {'curl': (-8, -5, -3), 'splay': 2.2, 'thumb': (-10, 0, 0), 'wrist': 0},
    'fist': {'curl': (95, 100, 70), 'splay': 0.2, 'thumb': (40, 55, 50), 'wrist': 0},
    'grasp': {'curl': (55, 60, 40), 'splay': 0.7, 'thumb': (25, 35, 30), 'wrist': 0},
    'pinch': {'curl': (22, 30, 22), 'splay': 0.6, 'thumb': (20, 30, 25), 'wrist': 0},
}


def joint_rots(pose):
    p = POSES[pose]; out = {}
    for name, bx, by, lens, r, splay in FINGERS:
        c = p['curl']
        out[f'{name}0'] = quat(c[0], splay * p['splay']); out[f'{name}1'] = quat(c[1]); out[f'{name}2'] = quat(c[2])
    t = p['thumb']
    out['thumb0'] = quat(t[1] * 0.6, 48 - t[0], -t[1] * 0.4); out['thumb1'] = quat(t[2])
    return out


def build(name, keys, glove=(0.58, 0.58, 0.56), cuff=(0.10, 0.50, 0.22), rough=0.55, outline=0.022, ink=(0.02, 0.02, 0.02)):
    """keys: [(time_s, pose_name), ...] -> animated GLB."""
    bin_, views, accs = bytearray(), [], []

    def add(arr, target=None, kind=None):
        nonlocal bin_
        while len(bin_) % 4: bin_ += b'\0'
        off = len(bin_); bin_ += arr.tobytes()
        views.append({'buffer': 0, 'byteOffset': off, 'byteLength': arr.nbytes, **({'target': target} if target else {})})
        acc = {'bufferView': len(views) - 1, 'count': int(arr.shape[0]),
               'componentType': 5125 if arr.dtype == np.uint32 else 5126,
               'type': kind or {1: 'SCALAR', 2: 'VEC2', 3: 'VEC3', 4: 'VEC4'}[arr.shape[1] if arr.ndim > 1 else 1]}
        if kind == 'VEC3' and target == 34962 and len(accs) % 3 == 0:
            acc['min'] = arr.min(0).tolist(); acc['max'] = arr.max(0).tolist()
        accs.append(acc)
        return len(accs) - 1

    meshes, nodes = [], []
    mats = [{'name': 'glove', 'pbrMetallicRoughness': {'baseColorFactor': [*glove, 1], 'metallicFactor': 0, 'roughnessFactor': rough}},
            {'name': 'cuff', 'pbrMetallicRoughness': {'baseColorFactor': [*cuff, 1], 'metallicFactor': 0, 'roughnessFactor': rough}},
            {'name': 'ink', 'pbrMetallicRoughness': {'baseColorFactor': [*ink, 1], 'metallicFactor': 0, 'roughnessFactor': 1}, 'emissiveFactor': list(ink)}]

    def mesh(P, N, I, mat):
        a = add(P, 34962, 'VEC3')
        accs[a]['min'] = P.min(0).tolist(); accs[a]['max'] = P.max(0).tolist()
        n = add(N, 34962, 'VEC3'); i = add(I, 34963, 'SCALAR')
        prims = [{'attributes': {'POSITION': a, 'NORMAL': n}, 'indices': i, 'material': mat}]
        if outline:  # cartoon ink line: inverted hull (fattened along normals, back faces only)
            Ph = (P + N * outline).astype('f4'); ah = add(Ph, 34962, 'VEC3')
            accs[ah]['min'] = Ph.min(0).tolist(); accs[ah]['max'] = Ph.max(0).tolist()
            nh = add((-N).astype('f4'), 34962, 'VEC3'); ih = add(I.reshape(-1, 3)[:, ::-1].copy().reshape(-1), 34963, 'SCALAR')
            prims.append({'attributes': {'POSITION': ah, 'NORMAL': nh}, 'indices': ih, 'material': 2})
        meshes.append({'primitives': prims})
        return len(meshes) - 1

    def node(nm, t=(0, 0, 0), m=None, children=None):
        nd = {'name': nm, 'translation': list(map(float, t))}
        if m is not None: nd['mesh'] = m
        if children: nd['children'] = children
        nodes.append(nd)
        return len(nodes) - 1

    rest = joint_rots(keys[0][1])
    root_children = []
    root_children.append(node('palm', (0, 0.50, 0), mesh(*blob(0.50, 0.55, 0.21), 0)))
    root_children.append(node('cuff', (0, -0.36, 0), mesh(*capsule(0.80, 0.40, 28, 8), 1)))
    root_children[-1] and nodes[root_children[-1]].update({'scale': [1.08, 0.5, 0.62]})
    for fname, bx, by, lens, r, splay in FINGERS:
        prev = None
        for k in range(len(lens) - 1, -1, -1):  # build tip first so parents can list children
            ch = [prev] if prev is not None else None
            t = (bx, by, 0) if k == 0 else (0, lens[k - 1] - r * 0.6, 0)
            prev = node(f'{fname}{k}', t, mesh(*capsule(lens[k], r * (1 - 0.06 * k)), 0), ch)
        root_children.append(prev)
    tn, tx, ty, tl, tr = THUMB
    tip = node('thumb1', (0, tl[0] - tr * 0.6, 0), mesh(*capsule(tl[1], tr * 0.94), 0))
    root_children.append(node('thumb0', (tx, ty, 0.06), mesh(*capsule(tl[0], tr), 0), [tip]))
    for nd in nodes:
        if nd['name'] in rest: nd['rotation'] = rest[nd['name']].tolist()
    root = node('hand', (0, 0, 0), None, root_children)

    # animation: one sampler per joint
    times = np.array([[k[0]] for k in keys], 'f4')
    ti = add(times, None, 'SCALAR'); accs[ti]['min'] = [float(times.min())]; accs[ti]['max'] = [float(times.max())]
    chans, samps = [], []
    poses = [joint_rots(k[1]) for k in keys]
    for idx, nd in enumerate(nodes):
        if nd['name'] not in poses[0]: continue
        q = np.array([p[nd['name']] for p in poses], 'f4')
        oi = add(q, None, 'VEC4')
        samps.append({'input': ti, 'output': oi, 'interpolation': 'LINEAR'})
        chans.append({'sampler': len(samps) - 1, 'target': {'node': idx, 'path': 'rotation'}})
    gl = {'asset': {'version': '2.0', 'generator': 'LaunchBACK make_hand.py'}, 'scene': 0, 'scenes': [{'nodes': [root]}],
          'nodes': nodes, 'meshes': meshes, 'materials': mats, 'accessors': accs, 'bufferViews': views,
          'buffers': [{'byteLength': len(bin_)}], 'animations': [{'name': 'pose', 'channels': chans, 'samplers': samps}]}
    js = json.dumps(gl).encode()
    js += b' ' * ((4 - len(js) % 4) % 4)
    while len(bin_) % 4: bin_ += b'\0'
    glb = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(bin_), 0x004E4942) + bytes(bin_)
    open(os.path.join(OUT, name), 'wb').write(glb)
    return name


def ease_keys(seq, steps=6):
    """Smooth (ease in-out) between consecutive poses by inserting blended keys is not possible with named poses,
    so the clip stays piecewise linear; callers pace it with timing."""
    return seq


if __name__ == '__main__':
    # S3: white cartoon glove, green cuff: fist, then opens wide (palm up is done by the layer rotation)
    build('glove_hand.glb', [(0.0, 'fist'), (0.9, 'fist'), (1.25, 'open'), (1.45, 'spread'), (1.6, 'open')])
    # S2b: dark hand reaching for the flame, fingers closing round it then holding
    # S2b: dark silhouette hand with a thin green rim (OG: tinted footage + light-sweep edge), reaching up and closing round the flame
    build('hand_reach.glb', [(0.0, 'spread'), (0.4, 'open'), (1.1, 'pinch'), (2.0, 'pinch')], glove=(0.008, 0.010, 0.008),
          cuff=(0.008, 0.010, 0.008), rough=1.0, outline=0.010, ink=(0.30, 0.70, 0.28))
    print('ok')
