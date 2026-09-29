"""
Placeholder props for "Miami: Walking Through Time".

Every prop is a low-poly stand-in with an `asset_tag`, so a BlenderKit model in
a collection named LIB_<tag> can replace it (see mt_common.swap_proxies).
Suggested BlenderKit searches are in PART01_SHOTLIST.md.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from mt_common import (bm_box, bm_cyl, bm_ellipsoid, bm_hull, ground_height, mesh_from_bm,
                       new_object, tag)

_CACHE = {}


def _cached(key, builder):
    me = _CACHE.get(key)
    if me is None or me.name not in bpy.data.meshes:
        me = builder()
        _CACHE[key] = me
    return me


def reset_cache():
    _CACHE.clear()


# ---------------------------------------------------------------------------
# Plants
# ---------------------------------------------------------------------------

def mesh_sabal_palm(pal, variant=0):
    def build():
        rng = random.Random(100 + variant)
        bm = bmesh.new()
        h = rng.uniform(6.0, 9.5)
        top = Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), h))
        bm_cyl(bm, (0, 0, -0.3), top, 0.22, 0.17, seg=8, mat=0)
        for i in range(16):
            a = 2 * math.pi * i / 16 + rng.uniform(-0.12, 0.12)
            droop = rng.uniform(-0.45, 0.5)
            ln = rng.uniform(1.4, 2.1)
            d = Vector((math.cos(a) * math.cos(droop), math.sin(a) * math.cos(droop), math.sin(droop)))
            bm_cyl(bm, top, top + d * ln, 0.04, 0.02, seg=4, mat=1)
            bm_ellipsoid(bm, top + d * (ln + 0.35), (0.6, 0.6, 0.07), subdiv=1, mat=1)
        return mesh_from_bm(f"MTP_sabal_palm_{variant}", bm, [pal.palm_trunk, pal.frond])
    return _cached(("palm", variant), build)


def mesh_mangrove(pal, variant=0):
    def build():
        rng = random.Random(200 + variant)
        bm = bmesh.new()
        base_z = 1.4
        for i in range(9):
            a = 2 * math.pi * i / 9 + rng.uniform(-0.2, 0.2)
            r = rng.uniform(1.2, 2.4)
            bm_cyl(bm, (r * math.cos(a), r * math.sin(a), -0.8),
                   (0.35 * math.cos(a), 0.35 * math.sin(a), base_z), 0.05, 0.07, seg=5, mat=0)
        bm_cyl(bm, (0, 0, base_z - 0.2), (0.2, 0.1, 3.2), 0.12, 0.08, seg=6, mat=0)
        for _ in range(3):
            c = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(3.0, 3.8)))
            bm_ellipsoid(bm, c, (rng.uniform(1.8, 2.6), rng.uniform(1.8, 2.6), rng.uniform(1.0, 1.5)), mat=1)
        return mesh_from_bm(f"MTP_mangrove_{variant}", bm, [pal.bark, pal.mangrove_leaf], smooth=True)
    return _cached(("mangrove", variant), build)


def mesh_seagrape(pal, variant=0):
    def build():
        rng = random.Random(300 + variant)
        bm = bmesh.new()
        bm_cyl(bm, (0, 0, -0.2), (0, 0, 1.0), 0.08, 0.06, seg=5, mat=0)
        for _ in range(4):
            c = Vector((rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8), rng.uniform(0.8, 1.6)))
            r = rng.uniform(0.7, 1.2)
            bm_ellipsoid(bm, c, (r, r, r * 0.8), mat=1)
        return mesh_from_bm(f"MTP_sea_grape_{variant}", bm, [pal.bark, pal.frond], smooth=True)
    return _cached(("seagrape", variant), build)


def mesh_saw_palmetto(pal, variant=0):
    def build():
        rng = random.Random(400 + variant)
        bm = bmesh.new()
        for i in range(11):
            a = 2 * math.pi * i / 11 + rng.uniform(-0.2, 0.2)
            up = rng.uniform(0.3, 0.9)
            d = Vector((math.cos(a) * math.cos(up), math.sin(a) * math.cos(up), math.sin(up)))
            base = Vector((0, 0, 0.05))
            bm_cyl(bm, base, base + d * 0.8, 0.02, 0.015, seg=4, mat=0)
            bm_ellipsoid(bm, base + d * 1.05, (0.35, 0.35, 0.04), subdiv=1, mat=0)
        return mesh_from_bm(f"MTP_saw_palmetto_{variant}", bm, [pal.frond])
    return _cached(("palmetto", variant), build)


def mesh_slash_pine(pal, variant=0):
    def build():
        rng = random.Random(500 + variant)
        bm = bmesh.new()
        h = rng.uniform(13, 18)
        bm_cyl(bm, (0, 0, -0.3), (rng.uniform(-0.4, 0.4), 0, h), 0.26, 0.11, seg=8, mat=0)
        for _ in range(5):
            c = Vector((rng.uniform(-1.5, 1.5), rng.uniform(-1.5, 1.5), rng.uniform(h - 3.5, h + 0.5)))
            r = rng.uniform(1.4, 2.4)
            bm_ellipsoid(bm, c, (r, r, r * 0.55), mat=1)
        return mesh_from_bm(f"MTP_slash_pine_{variant}", bm, [pal.bark, pal.pine_needle], smooth=True)
    return _cached(("pine", variant), build)


def mesh_coontie(pal):
    def build():
        bm = bmesh.new()
        for i in range(8):
            a = 2 * math.pi * i / 8
            d = Vector((math.cos(a) * 0.6, math.sin(a) * 0.6, 0.55))
            bm_cyl(bm, (0, 0, 0), d, 0.015, 0.01, seg=4, mat=0)
            bm_ellipsoid(bm, d * 1.1, (0.18, 0.18, 0.05), subdiv=1, mat=0)
        return mesh_from_bm("MTP_coontie", bm, [pal.frond])
    return _cached(("coontie", 0), build)


PLANTS = {
    "sabal_palm": mesh_sabal_palm,
    "mangrove": mesh_mangrove,
    "sea_grape": mesh_seagrape,
    "saw_palmetto": mesh_saw_palmetto,
    "slash_pine": mesh_slash_pine,
}


def place(coll, name, me, pos, asset_tag, rot_z=0.0, scale=1.0, z=None, jitter=True):
    x, y = pos[0], pos[1]
    if z is None:
        z = max(-1.0, ground_height(x, y))
    ob = new_object(name, me, coll, loc=(x, y, z), rot=(0, 0, rot_z), scale=(scale, scale, scale))
    return tag(ob, asset_tag, jitter=jitter)


def scatter(coll, pal, kind, count, sampler, seed=1, variants=4, scale=(0.8, 1.2)):
    rng = random.Random(seed)
    obs = []
    tries = 0
    while len(obs) < count and tries < count * 60:
        tries += 1
        p = sampler(rng)
        if p is None:
            continue
        me = PLANTS[kind](pal, rng.randrange(variants))
        obs.append(place(coll, f"{kind}_{len(obs):03d}", me, p, kind,
                         rot_z=rng.uniform(0, 2 * math.pi), scale=rng.uniform(*scale)))
    return obs


# ---------------------------------------------------------------------------
# Tequesta
# ---------------------------------------------------------------------------

def mesh_tequesta_house(pal, w=4.4, d=3.4, eave=2.1, ridge=3.7):
    """Open-sided palmetto-thatch house on posts. The form is a design guess."""
    def build():
        bm = bmesh.new()
        for x in (-w / 2, 0, w / 2):
            for y in (-d / 2, d / 2):
                bm_cyl(bm, (x, y, -0.4), (x, y, eave), 0.08, 0.07, seg=6, mat=0)
        for x in (-w / 2, w / 2):
            bm_cyl(bm, (x, 0, -0.4), (x, 0, ridge), 0.08, seg=6, mat=0)
        bm_cyl(bm, (-w / 2 - 0.3, 0, ridge), (w / 2 + 0.3, 0, ridge), 0.07, seg=6, mat=0)
        hd = d / 2 + 0.6
        rise = ridge - eave + 0.35
        ln = math.hypot(hd, rise)
        ang = math.atan2(rise, hd)
        for side in (1, -1):
            rot = Matrix.Rotation(-ang * side, 3, "X")
            bm_box(bm, (0, side * hd / 2, ridge - rise / 2 + 0.1), (w + 0.9, ln, 0.22), rot=rot, mat=1)
        bm_box(bm, (0, -d / 2, eave * 0.45), (w, 0.05, eave * 0.9), mat=2)
        bm_box(bm, (0.6, 0.3, 0.45), (2.0, 1.4, 0.08), mat=2)   # sleeping platform mat
        for x in (-0.3, 1.5):
            for y in (-0.3, 0.9):
                bm_cyl(bm, (x, y, -0.2), (x, y, 0.42), 0.05, seg=5, mat=0)
        return mesh_from_bm("MTP_tequesta_house", bm, [pal.log_wood, pal.thatch, pal.mat_weave])
    return _cached(("teq_house", 0), build)


def build_miami_circle(coll, pal, center, radius=5.79, posts=24):
    """Round thatched structure over the 38-ft ring of post holes.
    The ring is documented; the building on it is a reconstruction guess."""
    cx, cy = center
    gz = ground_height(cx, cy)
    bm = bmesh.new()
    for i in range(posts):
        a = 2 * math.pi * i / posts
        x, y = radius * math.cos(a), radius * math.sin(a)
        bm_cyl(bm, (x, y, -0.6), (x, y, 2.6), 0.11, 0.09, seg=6, mat=0)
    bm_cyl(bm, (0, 0, -0.6), (0, 0, 5.2), 0.14, 0.12, seg=8, mat=0)
    me = mesh_from_bm("MTP_miami_circle_posts", bm, [pal.log_wood])
    posts_ob = tag(new_object("MiamiCircle_Posts", me, coll, loc=(cx, cy, gz)), "miami_circle_posts", jitter=False)
    bm = bmesh.new()
    ret = bmesh.ops.create_cone(bm, cap_ends=False, cap_tris=False, segments=28, radius1=radius + 0.9,
                                radius2=0.25, depth=3.1)
    bmesh.ops.translate(bm, vec=(0, 0, 1.55), verts=ret["verts"])
    me = mesh_from_bm("MTP_miami_circle_roof", bm, [pal.thatch])
    roof = tag(new_object("MiamiCircle_Roof", me, coll, loc=(cx, cy, gz + 2.5)), "miami_circle_roof", jitter=False)
    # shell-and-limestone footing ring so the post holes read on the ground
    bm = bmesh.new()
    ret = bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=radius + 0.35)
    bmesh.ops.translate(bm, vec=(0, 0, 0.03), verts=ret["verts"])
    me = mesh_from_bm("MTP_miami_circle_floor", bm, [pal.stone])
    floor = new_object("MiamiCircle_Floor", me, coll, loc=(cx, cy, gz))
    return posts_ob, roof, floor


def mesh_dugout(pal, length=6.0, width=0.75, depth=0.42):
    def build():
        bm = bmesh.new()
        bm_hull(bm, length, width, depth, open_top=True, mat=0)
        return mesh_from_bm(f"MTP_dugout_{length:.0f}", bm, [pal.charred], smooth=True)
    return _cached(("dugout", length), build)


def build_dugout(coll, pal, name, loc, heading_deg, length=6.0):
    ob = new_object(name, mesh_dugout(pal, length), coll, loc=loc, rot=(0, 0, math.radians(heading_deg)))
    return tag(ob, "dugout_canoe", jitter=False)


def build_drying_rack(coll, pal, name, pos, face_deg=0):
    bm = bmesh.new()
    for x in (-1.2, 1.2):
        bm_cyl(bm, (x, -0.5, -0.2), (x, 0, 1.7), 0.04, seg=5, mat=0)
        bm_cyl(bm, (x, 0.5, -0.2), (x, 0, 1.7), 0.04, seg=5, mat=0)
    bm_cyl(bm, (-1.4, 0, 1.6), (1.4, 0, 1.6), 0.035, seg=5, mat=0)
    for i in range(9):
        x = -1.0 + i * 0.25
        bm_ellipsoid(bm, (x, 0, 1.3), (0.05, 0.02, 0.22), subdiv=1, mat=1)
    me = mesh_from_bm(f"MTP_drying_rack_{name}", bm, [pal.log_wood, pal.fish])
    x, y = pos
    return tag(new_object(name, me, coll, loc=(x, y, ground_height(x, y)), rot=(0, 0, math.radians(face_deg))),
               "fish_drying_rack", jitter=False)


def build_fire(coll, pal, name, pos):
    """Stone ring, logs, glowing embers, a flickering light and a smoke column."""
    x, y = pos
    gz = ground_height(x, y)
    bm = bmesh.new()
    for i in range(9):
        a = 2 * math.pi * i / 9
        bm_ellipsoid(bm, (0.55 * math.cos(a), 0.55 * math.sin(a), 0.06), (0.14, 0.11, 0.09), subdiv=1, mat=0)
    for i in range(4):
        a = math.pi * i / 4
        bm_cyl(bm, (0.5 * math.cos(a), 0.5 * math.sin(a), 0.05), (-0.5 * math.cos(a), -0.5 * math.sin(a), 0.2),
               0.05, seg=5, mat=1)
    bm_ellipsoid(bm, (0, 0, 0.08), (0.3, 0.3, 0.06), subdiv=1, mat=2)
    me = mesh_from_bm(f"MTP_fire_{name}", bm, [pal.stone, pal.charred, pal.ember])
    fire = tag(new_object(name, me, coll, loc=(x, y, gz)), "campfire", jitter=False)
    ld = bpy.data.lights.new(f"MT_{name}_Light", "POINT")
    ld.energy = 180.0
    ld.color = (1.0, 0.55, 0.25)
    ld.shadow_soft_size = 0.3
    light = new_object(f"{name}_Light", ld, coll, loc=(0, 0, 0.5), parent=fire)
    bm = bmesh.new()
    ret = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12, radius1=0.5, radius2=1.6, depth=9.0)
    bmesh.ops.translate(bm, vec=(0, 0, 4.5), verts=ret["verts"])
    me = mesh_from_bm(f"MTP_smoke_{name}", bm, [pal.smoke])
    smoke = new_object(f"{name}_Smoke", me, coll, loc=(0, 0, 0.3), parent=fire)
    return fire, light, smoke


def flicker(light_ob, f0, f1, base=180.0, amount=60.0):
    from mt_common import add_noise
    light_ob.data.energy = base
    light_ob.data.keyframe_insert("energy", frame=f0)
    add_noise(light_ob.data, "energy", 0, amount, 3.0, f0, f1, blend_in=1, blend_out=1)


def build_midden(coll, pal, name, pos, radius=3.2, height=0.7):
    x, y = pos
    bm = bmesh.new()
    rng = random.Random(9)
    bm_ellipsoid(bm, (0, 0, 0), (radius, radius * 0.8, height), subdiv=3, mat=0)
    for _ in range(40):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0, radius * 0.9)
        bm_ellipsoid(bm, (r * math.cos(a), r * 0.8 * math.sin(a), height * (1 - (r / radius) ** 2) ** 0.5),
                     (0.08, 0.06, 0.04), subdiv=1, mat=0)
    me = mesh_from_bm(f"MTP_midden_{name}", bm, [pal.shell], smooth=True)
    return tag(new_object(name, me, coll, loc=(x, y, ground_height(x, y) - 0.1)), "shell_midden", jitter=False)


def mesh_basket(pal):
    def build():
        bm = bmesh.new()
        ret = bmesh.ops.create_cone(bm, cap_ends=False, cap_tris=False, segments=14, radius1=0.2,
                                    radius2=0.28, depth=0.3)
        bmesh.ops.translate(bm, vec=(0, 0, 0.15), verts=ret["verts"])
        return mesh_from_bm("MTP_basket", bm, [pal.mat_weave])
    return _cached(("basket", 0), build)


def mesh_shell_cup(pal):
    def build():
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=18, v_segments=10, radius=0.075)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 0.006], context="VERTS")
        bmesh.ops.scale(bm, vec=(1.25, 0.9, 0.7), verts=bm.verts)
        return mesh_from_bm("MTP_shell_cup", bm, [pal.shell], smooth=True)
    return _cached(("shell_cup", 0), build)


def mesh_pestle(pal):
    def build():
        bm = bmesh.new()
        bm_cyl(bm, (0, 0, -0.35), (0, 0, 0.35), 0.035, seg=6)
        return mesh_from_bm("MTP_pestle", bm, [pal.log_wood])
    return _cached(("pestle", 0), build)


def mesh_mortar(pal):
    def build():
        bm = bmesh.new()
        bm_cyl(bm, (0, 0, -0.1), (0, 0, 0.35), 0.22, 0.2, seg=10)
        return mesh_from_bm("MTP_mortar", bm, [pal.log_wood])
    return _cached(("mortar", 0), build)


def mesh_pole(pal, length=3.2, radius=0.025, name="MTP_pole"):
    def build():
        bm = bmesh.new()
        bm_cyl(bm, (0, 0, -length / 2), (0, 0, length / 2), radius, seg=6)
        return mesh_from_bm(name, bm, [pal.log_wood])
    return _cached((name, length), build)


# ---------------------------------------------------------------------------
# Spanish
# ---------------------------------------------------------------------------

def mesh_nao(pal):
    """16th-century Spanish ship stand-in (hull, castles, three masts, square sails)."""
    def build():
        bm = bmesh.new()
        loops = bm_hull(bm, 24.0, 7.0, 3.6, open_top=False, stations=20, arc=10, mat=0)
        del loops
        bmesh.ops.translate(bm, vec=(0, 0, 1.8), verts=list(bm.verts))
        bm_box(bm, (-9.0, 0, 3.0), (6.5, 6.0, 2.6), mat=0)
        bm_box(bm, (9.5, 0, 2.6), (4.0, 4.6, 1.6), mat=0)
        for x, h, sw, sh in ((1.0, 21.0, 9.5, 8.5), (8.0, 16.0, 7.0, 6.0), (-7.5, 14.0, 0, 0)):
            bm_cyl(bm, (x, 0, 1.5), (x, 0, h), 0.22, 0.14, seg=8, mat=2)
            if sw:
                bm_box(bm, (x + 0.3, 0, h - sh / 2 - 1.5), (0.08, sw, sh), mat=1)
                bm_cyl(bm, (x, -sw / 2 - 0.4, h - 1.4), (x, sw / 2 + 0.4, h - 1.4), 0.08, seg=6, mat=2)
        tri = [bm.verts.new(v) for v in ((-7.5, 0, 13.5), (-7.5, 0, 5.0), (-12.5, 0, 5.5))]
        f = bm.faces.new(tri)
        f.material_index = 1
        bm_cyl(bm, (13.0, 0, 3.5), (17.0, 0, 6.0), 0.12, 0.08, seg=6, mat=2)   # bowsprit
        return mesh_from_bm("MTP_nao", bm, [pal.ship_wood, pal.canvas, pal.log_wood])
    return _cached(("nao", 0), build)


def mesh_longboat(pal):
    def build():
        bm = bmesh.new()
        bm_hull(bm, 7.0, 1.9, 0.8, open_top=True, wall=0.06, mat=0)
        for x in (-1.8, 0, 1.8):
            bm_box(bm, (x, 0, -0.25), (0.25, 1.6, 0.05), mat=0)
        return mesh_from_bm("MTP_longboat", bm, [pal.ship_wood], smooth=True)
    return _cached(("longboat", 0), build)


def build_stockade(coll, pal, name, center, radius, gate_deg, gate_width=3.2, seed=3):
    """Ring palisade with shape keys "Buried" (logs underground) and "Decayed"."""
    rng = random.Random(seed)
    cx, cy = center
    bm = bmesh.new()
    groups = []
    circ = 2 * math.pi * radius
    n = int(circ / 0.34)
    gate = math.radians(gate_deg)
    half_gate = (gate_width / 2) / radius
    for i in range(n):
        a = 2 * math.pi * i / n
        da = (a - gate + math.pi) % (2 * math.pi) - math.pi
        if abs(da) < half_gate:
            continue
        x, y = radius * math.cos(a), radius * math.sin(a)
        gz = ground_height(cx + x, cy + y)
        h = rng.uniform(3.3, 4.1)
        r = rng.uniform(0.13, 0.18)
        base = Vector((x, y, gz - 0.6))
        top = Vector((x + rng.uniform(-0.05, 0.05), y + rng.uniform(-0.05, 0.05), gz + h))
        vs = list(bm_cyl(bm, base, top, r, r * 0.92, seg=6, mat=0))
        vs += list(bm_cyl(bm, top, top + Vector((0, 0, 0.35)), r * 0.92, 0.02, seg=6, mat=0))
        groups.append((vs, base, h))
    for side in (1, -1):   # gate posts and lintel
        a = gate + side * (half_gate + 0.02)
        x, y = radius * math.cos(a), radius * math.sin(a)
        gz = ground_height(cx + x, cy + y)
        base = Vector((x, y, gz - 0.8))
        vs = list(bm_cyl(bm, base, Vector((x, y, gz + 4.6)), 0.22, 0.2, seg=8, mat=0))
        groups.append((vs, base, 5.4))
    a1, a2 = gate - half_gate, gate + half_gate
    gz = ground_height(cx + radius * math.cos(gate), cy + radius * math.sin(gate))
    p1 = Vector((radius * math.cos(a1), radius * math.sin(a1), gz + 4.3))
    p2 = Vector((radius * math.cos(a2), radius * math.sin(a2), gz + 4.3))
    vs = list(bm_cyl(bm, p1, p2, 0.16, seg=6, mat=0))
    groups.append((vs, (p1 + p2) / 2 - Vector((0, 0, 4.3)), 4.5))
    bm.verts.index_update()
    idx_groups = [([v.index for v in vs], base, h) for vs, base, h in groups]
    me = mesh_from_bm(f"MTP_{name}", bm, [pal.log_wood])
    ob = tag(new_object(name, me, coll, loc=(cx, cy, 0)), "palisade_logs", jitter=False)
    ob.shape_key_add(name="Basis", from_mix=False)
    buried = ob.shape_key_add(name="Buried", from_mix=False)
    decayed = ob.shape_key_add(name="Decayed", from_mix=False)
    for idxs, base, h in idx_groups:
        drop = h + 0.8 + rng.uniform(0.0, 0.6)
        gone = rng.random() < 0.35
        axis = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0)).normalized()
        rot = Matrix.Rotation(math.radians(rng.uniform(8, 50)), 4, axis)
        sink = rng.uniform(0.4, 1.6) + (h + 2.0 if gone else 0.0)
        for i in idxs:
            co = Vector(me.vertices[i].co)
            buried.data[i].co = co - Vector((0, 0, drop))
            decayed.data[i].co = (rot @ (co - base)) + base - Vector((0, 0, sink))
    return ob


def mesh_pine_cross(pal):
    def build():
        bm = bmesh.new()
        bm_cyl(bm, (0, 0, -0.6), (0, 0, 6.6), 0.17, 0.14, seg=8)
        bm_cyl(bm, (-1.5, 0, 4.7), (1.5, 0, 4.7), 0.13, seg=8)
        return mesh_from_bm("MTP_pine_cross", bm, [pal.log_wood])
    return _cached(("cross", 0), build)


def mesh_spanish_hut(pal):
    """Rudimentary A-frame hut, palmetto thatch over pole framing."""
    def build():
        bm = bmesh.new()
        w, ln, ridge = 2.6, 3.0, 2.4
        ang = math.atan2(ridge, w / 2)
        slope = math.hypot(w / 2, ridge)
        for side in (1, -1):
            rot = Matrix.Rotation(side * (math.pi / 2 - ang), 3, "Y")
            bm_box(bm, (side * w / 4, 0, ridge / 2), (0.14, ln, slope), rot=rot, mat=1)
        bm_cyl(bm, (0, -ln / 2 - 0.2, ridge), (0, ln / 2 + 0.2, ridge), 0.06, seg=6, mat=0)
        for y in (-ln / 2, ln / 2):
            for side in (1, -1):
                bm_cyl(bm, (side * w / 2, y, -0.2), (0, y, ridge + 0.1), 0.05, seg=5, mat=0)
        return mesh_from_bm("MTP_spanish_hut", bm, [pal.log_wood, pal.thatch])
    return _cached(("span_hut", 0), build)


def mesh_log(pal, length=3.6, radius=0.16):
    def build():
        bm = bmesh.new()
        bm_cyl(bm, (-length / 2, 0, 0), (length / 2, 0, 0), radius, radius * 0.9, seg=8)
        return mesh_from_bm(f"MTP_log_{length:.1f}", bm, [pal.log_wood])
    return _cached(("log", length, radius), build)


def mesh_arquebus(pal):
    def build():
        bm = bmesh.new()
        bm_cyl(bm, (0, 0, -0.35), (0, 0, 0.35), 0.03, 0.025, seg=6, mat=0)
        bm_cyl(bm, (0, 0, 0.3), (0, 0, 1.0), 0.013, seg=6, mat=1)
        return mesh_from_bm("MTP_arquebus", bm, [pal.log_wood, pal.iron])
    return _cached(("arquebus", 0), build)


def mesh_nail(pal):
    def build():
        bm = bmesh.new()
        bm_cyl(bm, (0, 0, 0), (0, 0, 0.11), 0.0045, 0.001, seg=4)
        bm_cyl(bm, (0, 0, -0.003), (0, 0, 0.0), 0.009, seg=8)
        return mesh_from_bm("MTP_nail", bm, [pal.iron])
    return _cached(("nail", 0), build)


def mesh_slate(pal):
    def build():
        bm = bmesh.new()
        bm_box(bm, (0, 0, 0), (0.26, 0.012, 0.19))
        return mesh_from_bm("MTP_slate", bm, [pal.slate])
    return _cached(("slate", 0), build)


# ---------------------------------------------------------------------------
# Costume pieces for make_person(extras=[...])
# ---------------------------------------------------------------------------

def moss_skirt(bm, s, hip, shoulder):
    bm_cyl(bm, (0, 0, (hip - 0.02) * s), (0, 0, (hip - 0.48) * s), 0.2 * s, 0.30 * s, seg=14, mat=1)


def breechcloth(bm, s, hip, shoulder):
    bm_box(bm, (0, 0.14 * s, (hip - 0.2) * s), (0.22 * s, 0.03 * s, 0.35 * s), mat=1)
    bm_box(bm, (0, -0.14 * s, (hip - 0.2) * s), (0.22 * s, 0.03 * s, 0.35 * s), mat=1)


def soldier_kit(bm, s, hip, shoulder):
    bm_cyl(bm, (0, 0.02, (hip + 0.04) * s), (0, 0.02, (shoulder - 0.02) * s), 0.21 * s, 0.225 * s, seg=12, mat=1)
    head_z = (shoulder + 0.17) * s
    bm_ellipsoid(bm, (0, 0, head_z + 0.08 * s), (0.125 * s, 0.14 * s, 0.09 * s), mat=1)
    bm_cyl(bm, (0, 0, head_z + 0.035 * s), (0, 0, head_z + 0.05 * s), 0.21 * s, 0.21 * s, seg=16, mat=1)
    bm_box(bm, (0, 0, head_z + 0.17 * s), (0.02 * s, 0.22 * s, 0.07 * s), mat=1)


def cassock(bm, s, hip, shoulder):
    bm_cyl(bm, (0, 0, (shoulder - 0.02) * s), (0, 0, 0.02), 0.21 * s, 0.30 * s, seg=16, mat=1)
