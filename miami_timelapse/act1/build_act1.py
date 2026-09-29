"""Build and animate Act 1 (500 BC - 1836) of the Miami timelapse in Blender.

Reads act1_timeline.json (beats, camera shots, lighting, counters) and the assets made by
prep_act1.py. Needs only Blender (bpy + its bundled numpy); tested with Blender 4.2.

Usage (inside Blender's own Python, from this folder):
  blender -b -P build_act1.py -- --save act1.blend
  blender -b -P build_act1.py -- --stills renders/stills --res 960x540 --samples 32
  blender -b -P build_act1.py -- --anim renders/frames --step 3 --res 640x360
Or with the 'bpy' pip module:  python3 build_act1.py --stills renders/stills
You can also open Blender, load this file in the Text Editor and press Run Script
(it builds the scene; render from the UI with Eevee or Cycles).

Captions, the year counter and the population counter are added afterwards by overlay.py
so the typography stays sharp and editable.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy  # noqa: I001  (bpy must be imported before bmesh when using the pip module)
import bmesh
import numpy as np
from mathutils import Matrix, Vector

try:
    HERE = Path(__file__).resolve().parent
except NameError:  # run from Blender's Text Editor: use the saved .blend's folder
    HERE = Path(bpy.path.abspath("//"))
ASSETS = HERE / "assets"
TL = json.loads((HERE / "act1_timeline.json").read_text())
GEO = json.loads((ASSETS / "act1_geo.json").read_text())

FPS = 24
VZ = 3.0            # vertical exaggeration (Miami is flat: the ridge is only ~7 m)
S_HUT = 2.2         # object exaggeration, like the reference videos' toy-scale houses
S_SHIP = 2.2
S_PERSON = 4.0
S_TREE = 1.8
S_TOWER = 1.6
rng = np.random.default_rng(1513)

T20 = np.load(ASSETS / "terrain_20m.npy")
EXT = GEO["terrain_20m_extent_m"]
FULL = GEO["extent_m"]


# ------------------------------------------------------------------------------ helpers
def fr(t):
    """seconds -> frame"""
    return int(round(t * FPS)) + 1


def ll(lat, lon):
    return (lon - GEO["lon0"]) * GEO["kx"], (lat - GEO["lat0"]) * GEO["ky"]


def height_m(x, y):
    """Bilinear terrain height (metres, not exaggerated) at local x, y."""
    nr, nc = T20.shape
    dx = (EXT["x_max"] - EXT["x_min"]) / nc
    dy = (EXT["y_max"] - EXT["y_min"]) / nr
    c = (x - EXT["x_min"]) / dx - 0.5
    r = (EXT["y_max"] - y) / dy - 0.5
    c = min(max(c, 0), nc - 1.001)
    r = min(max(r, 0), nr - 1.001)
    c0, r0 = int(c), int(r)
    fc, fr_ = c - c0, r - r0
    a = T20[r0, c0] * (1 - fc) + T20[r0, c0 + 1] * fc
    b = T20[r0 + 1, c0] * (1 - fc) + T20[r0 + 1, c0 + 1] * fc
    return float(a * (1 - fr_) + b * fr_)


def ground(x, y):
    return max(height_m(x, y), 0.0) * VZ


def P(lat, lon, dz=0.0):
    x, y = ll(lat, lon)
    return Vector((x, y, ground(x, y) + dz))


def water_snap(x, y, depth=-0.8, radius=600):
    """Nearest point with water deeper than `depth` (so boats never sit on land)."""
    if height_m(x, y) < depth:
        return x, y
    best = None
    for rad in range(20, radius + 1, 20):
        for a in np.linspace(0, 2 * math.pi, 24, endpoint=False):
            px, py = x + rad * math.cos(a), y + rad * math.sin(a)
            if height_m(px, py) < depth:
                best = (px, py)
                break
        if best:
            return best
    return x, y


def land_snap(x, y, minh=0.5, radius=300):
    if height_m(x, y) > minh:
        return x, y
    for rad in range(10, radius + 1, 10):
        for a in np.linspace(0, 2 * math.pi, 16, endpoint=False):
            px, py = x + rad * math.cos(a), y + rad * math.sin(a)
            if height_m(px, py) > minh:
                return px, py
    return None


def mat(name, color, rough=0.8, emit=None, strength=0.0, alpha=1.0, metallic=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metallic
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
    return m


def srgb(*c):
    return tuple((v / 255.0) ** 2.2 for v in c)


class Builder:
    """Accumulate primitives into one mesh with per-part materials."""

    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []

    def _mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def _tag(self, verts, m):
        mi = self._mi(m)
        for f in {f for v in verts for f in v.link_faces}:
            f.material_index = mi

    def box(self, m, size, loc=(0, 0, 0), rot=0.0):
        M = Matrix.Translation(loc) @ Matrix.Rotation(rot, 4, "Z") @ Matrix.Diagonal((*size, 1))
        r = bmesh.ops.create_cube(self.bm, size=1.0, matrix=M)
        self._tag(r["verts"], m)

    def cone(self, m, r1, r2, depth, loc=(0, 0, 0), seg=10, rot=None):
        M = Matrix.Translation(loc)
        if rot is not None:
            M = M @ rot
        M = M @ Matrix.Translation((0, 0, depth / 2))
        r = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg,
                                  radius1=r1, radius2=r2, depth=depth, matrix=M)
        self._tag(r["verts"], m)

    def blob(self, m, r, loc=(0, 0, 0), sz=1.0, sub=1):
        M = Matrix.Translation(loc) @ Matrix.Diagonal((1, 1, sz, 1))
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r, matrix=M)
        self._tag(res["verts"], m)

    def quad(self, m, pts):
        vs = [self.bm.verts.new(p) for p in pts]
        f = self.bm.faces.new(vs)
        f.material_index = self._mi(m)

    def obj(self, name, coll=None, smooth=False):
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        if smooth:
            me.shade_smooth()
        o = bpy.data.objects.new(name, me)
        (coll or bpy.context.scene.collection).objects.link(o)
        return o


def collection(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def instance(src, name, loc, rot=0.0, scale=1.0, coll=None):
    o = bpy.data.objects.new(name, src.data)
    o.location = loc
    o.rotation_euler = (0, 0, rot)
    o.scale = (scale,) * 3
    o["base_scale"] = scale
    (coll or bpy.context.scene.collection).objects.link(o)
    return o


def key_visible(o, intervals, grow=8, axis="xyz"):
    """Show object only during [(t_on, t_off), ...] seconds, popping/growing in and out."""
    s = o.get("base_scale", 1.0)

    def setk(frame, v):
        if axis == "z":
            o.scale = (s, s, v)
        else:
            o.scale = (v, v, v)
        o.keyframe_insert("scale", frame=frame)

    setk(1, 0.0)
    for t_on, t_off in intervals:
        a, b = fr(t_on), fr(t_off)
        setk(max(a, 2), 0.0)
        setk(a + grow, s)
        if b < fr(TL["duration_s"]) + 1:
            setk(max(b - grow, a + grow + 1), s)
            setk(b, 0.0)


def key_path(o, keys):
    """keys: [(t, Vector)] -> location keyframes, heading follows motion."""
    prev = None
    for t, p in keys:
        o.location = p
        o.keyframe_insert("location", frame=fr(t))
        if prev is not None and (p - prev[1]).length > 1:
            d = p - prev[1]
            o.rotation_euler = (0, 0, math.atan2(d.y, d.x))
            o.keyframe_insert("rotation_euler", frame=fr(prev[0]) + 1)
            o.keyframe_insert("rotation_euler", frame=fr(t))
        prev = (t, p)


def interp(pairs, t):
    xs, ys = zip(*pairs)
    return float(np.interp(t, xs, ys))


# ------------------------------------------------------------------------------ scene
def setup_scene(res, samples):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, fr(TL["duration_s"])
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 2
    sc.cycles.transparent_max_bounces = 8
    sc.render.use_persistent_data = True
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    sc.view_layers[0].use_pass_mist = True
    sc.world = bpy.data.worlds.new("sky")
    return sc


def build_terrain():
    nr, nc = T20.shape
    dx = (EXT["x_max"] - EXT["x_min"]) / nc
    dy = (EXT["y_max"] - EXT["y_min"]) / nr
    xs = EXT["x_min"] + (np.arange(nc) + 0.5) * dx
    ys = EXT["y_max"] - (np.arange(nr) + 0.5) * dy
    X, Y = np.meshgrid(xs, ys)
    Z = T20 * VZ
    co = np.stack([X, Y, Z], -1).reshape(-1, 3).astype(np.float32)
    idx = np.arange(nr * nc).reshape(nr, nc)
    q = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]], -1).reshape(-1, 4)
    me = bpy.data.meshes.new("terrain_1836")
    me.vertices.add(len(co))
    me.vertices.foreach_set("co", co.ravel())
    me.loops.add(q.size)
    me.loops.foreach_set("vertex_index", q.ravel().astype(np.int32))
    me.polygons.add(len(q))
    me.polygons.foreach_set("loop_start", np.arange(0, q.size, 4, dtype=np.int32))
    uv = me.uv_layers.new(name="UV")
    u = (co[:, 0] - FULL["x_min"]) / (FULL["x_max"] - FULL["x_min"])
    v = (co[:, 1] - FULL["y_min"]) / (FULL["y_max"] - FULL["y_min"])
    uvs = np.stack([u, v], -1)[q.ravel()]
    uv.data.foreach_set("uv", uvs.ravel().astype(np.float32))
    me.update(calc_edges=True)
    me.polygons.foreach_set("use_smooth", np.ones(len(q), bool))
    o = bpy.data.objects.new("terrain_1836", me)
    bpy.context.scene.collection.objects.link(o)

    m = bpy.data.materials.new("terrain")
    m.use_nodes = True
    nt = m.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(ASSETS / "landcover_5m.png"))
    tex.interpolation = "Linear"
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = 0.95
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    me.materials.append(m)

    # beyond the data: far sea floor, far water and far land so the horizon is not empty
    for name, z, size, col in [("far_seabed", -18.0 * VZ, 200000, srgb(20, 50, 92))]:
        bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
        p = bpy.context.object
        p.name = name
        p.data.materials.append(mat(name, col, rough=1.0))
    land_col = mat("far_land", srgb(92, 118, 60), rough=1.0)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 1.2 * VZ))
    fl = bpy.context.object
    fl.name = "far_land_west"
    fl.scale = (60000, 120000, 1)
    fl.location = (EXT["x_min"] - 30000 + 20, 0, 1.2 * VZ)
    fl.data.materials.append(land_col)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 1.2 * VZ))
    fn = bpy.context.object
    fn.name = "far_land_north"
    fn.scale = (40000 + (0 - EXT["x_min"]), 60000, 1)
    fn.location = ((EXT["x_min"] - 40000 + 0) / 2, EXT["y_max"] + 30000 - 20, 1.2 * VZ)
    fn.data.materials.append(land_col)
    return o


def build_water():
    bpy.ops.mesh.primitive_plane_add(size=200000, location=(0, 0, 0))
    w = bpy.context.object
    w.name = "water"
    m = bpy.data.materials.new("water")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*srgb(40, 120, 150), 1)
    b.inputs["Roughness"].default_value = 0.06
    b.inputs["IOR"].default_value = 1.33
    b.inputs["Alpha"].default_value = 0.42
    w.data.materials.append(m)
    return w


def build_sky_and_sun():
    sc = bpy.context.scene
    wn = sc.world
    wn.use_nodes = True
    nt = wn.node_tree
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.air_density = 1.4
    sky.dust_density = 2.0
    bg = nt.nodes["Background"]
    bg.inputs["Strength"].default_value = 0.22
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])

    sun_d = bpy.data.lights.new("sun", "SUN")
    sun_d.angle = math.radians(1.5)
    sun_d.color = (1.0, 0.9, 0.78)
    sun = bpy.data.objects.new("sun", sun_d)
    sc.collection.objects.link(sun)
    moon_d = bpy.data.lights.new("moon", "SUN")
    moon_d.color = (0.55, 0.65, 1.0)
    moon = bpy.data.objects.new("moon", moon_d)
    moon.rotation_euler = (math.radians(35), 0, math.radians(200))
    sc.collection.objects.link(moon)

    for k in TL["lighting"]:
        f = fr(k["t"])
        el, az = math.radians(k["sun_el"] if "sun_el" in k else k["sun_elev"]), math.radians(k["sun_az"])
        sun.rotation_euler = (math.pi / 2 - max(el, math.radians(-5)), 0, math.pi - az)
        sun.keyframe_insert("rotation_euler", frame=f)
        day = max(0.0, min(1.0, (math.degrees(el) + 2) / 10))
        sun_d.energy = 4.0 * day * (0.35 if k.get("storm") else 1.0)
        sun_d.keyframe_insert("energy", frame=f)
        moon_d.energy = 0.25 * (1 - day)
        moon_d.keyframe_insert("energy", frame=f)
        sky.sun_elevation = max(el, math.radians(-8))
        sky.sun_rotation = az
        sky.keyframe_insert("sun_elevation", frame=f)
        sky.keyframe_insert("sun_rotation", frame=f)
        bg.inputs["Strength"].default_value = (0.22 if not k.get("storm") else 0.08) * (0.25 + 0.75 * day)
        bg.inputs["Strength"].keyframe_insert("default_value", frame=f)


def build_camera():
    sc = bpy.context.scene
    cam_d = bpy.data.cameras.new("cam")
    cam_d.lens = 30
    cam_d.clip_start = 5
    cam_d.clip_end = 90000
    cam = bpy.data.objects.new("cam", cam_d)
    sc.collection.objects.link(cam)
    sc.camera = cam
    tgt = bpy.data.objects.new("cam_target", None)
    sc.collection.objects.link(tgt)
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"

    groups = []  # merge consecutive beats that use the same shot
    for b in TL["beats"]:
        if groups and groups[-1][0] == b["shot"]:
            groups[-1][2] = b["t"][1]
        else:
            groups.append([b["shot"], b["t"][0], b["t"][1]])
    for shot, t0, t1 in groups:
        s = TL["shots"][shot]
        tx, ty = ll(*s["target"])
        tz = ground(tx, ty)
        drift = min(10.0, (t1 - t0) * 0.8)
        for t, az, dist in [(t0 + s["blend_s"], s["az_deg"], s["dist_m"]),
                            (t1, s["az_deg"] + drift, s["dist_m"] * 0.93)]:
            if t > t1:
                t = t1
            el, a = math.radians(s["elev_deg"]), math.radians(az)
            off = Vector((math.sin(a) * math.cos(el), math.cos(a) * math.cos(el), math.sin(el))) * dist
            tgt.location = (tx, ty, tz)
            cam.location = Vector((tx, ty, tz)) + off
            tgt.keyframe_insert("location", frame=fr(t))
            cam.keyframe_insert("location", frame=fr(t))
    # mist (distance haze) through the compositor
    sc.world.mist_settings.start = 1500
    sc.world.mist_settings.depth = 11000
    sc.world.mist_settings.falloff = "QUADRATIC"
    sc.use_nodes = True
    nt = sc.node_tree
    rl = nt.nodes["Render Layers"]
    comp = nt.nodes["Composite"]
    mix = nt.nodes.new("CompositorNodeMixRGB")
    mix.inputs[2].default_value = (0.74, 0.80, 0.86, 1)
    nt.links.new(rl.outputs["Image"], mix.inputs[1])
    mul = nt.nodes.new("CompositorNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 0.8
    nt.links.new(rl.outputs["Mist"], mul.inputs[0])
    nt.links.new(mul.outputs[0], mix.inputs[0])
    nt.links.new(mix.outputs[0], comp.inputs["Image"])
    return cam


# ------------------------------------------------------------------------------ models
M = {}


def materials():
    M["thatch"] = mat("thatch", srgb(196, 164, 104))
    M["wood"] = mat("wood", srgb(110, 78, 50))
    M["darkwood"] = mat("darkwood", srgb(70, 48, 32))
    M["sail"] = mat("sail", srgb(236, 228, 208))
    M["redsail"] = mat("redsail", srgb(170, 50, 40))
    M["white"] = mat("white", srgb(238, 236, 228))
    M["black"] = mat("black", srgb(25, 25, 25), rough=0.5)
    M["lamp"] = mat("lamp", srgb(255, 240, 200), emit=srgb(255, 230, 170), strength=0.0)
    M["glow"] = mat("window_glow", srgb(40, 25, 15), emit=srgb(255, 120, 40), strength=0.0)
    M["fire"] = mat("fire", srgb(255, 140, 40), emit=srgb(255, 120, 30), strength=25.0)
    M["smoke"] = mat("smoke", srgb(70, 68, 66), rough=1.0, alpha=0.45)
    M["flash"] = mat("flash", srgb(255, 240, 200), emit=srgb(255, 220, 150), strength=60.0)
    M["skin"] = mat("skin", srgb(150, 100, 70))
    M["navy"] = mat("navy", srgb(40, 50, 80))
    M["field"] = mat("field", srgb(120, 150, 60))
    M["soil"] = mat("soil", srgb(140, 110, 70))
    M["red"] = mat("red", srgb(180, 40, 40))
    M["ash"] = mat("ash", srgb(40, 36, 34))
    for i, c in enumerate([(52, 92, 48), (62, 104, 52), (74, 116, 58)]):
        M[f"leaf{i}"] = mat(f"leaf{i}", srgb(*c))
    M["pineleaf"] = mat("pineleaf", srgb(70, 104, 62))
    M["trunk"] = mat("trunk", srgb(96, 76, 56))


def model_hut():
    b = Builder()
    for dx in (-2.2, 2.2):
        for dy in (-2.2, 2.2):
            b.box(M["wood"], (0.3, 0.3, 1.4), (dx, dy, 0.7))
    b.box(M["wood"], (5.4, 5.4, 0.3), (0, 0, 1.5))
    b.cone(M["thatch"], 4.2, 0.2, 3.4, (0, 0, 1.6), seg=4, rot=Matrix.Rotation(math.pi / 4, 4, "Z"))
    return b.obj("M_hut", coll=collection("_models"))


def model_shack():
    b = Builder()
    b.box(M["wood"], (5, 4, 2.4), (0, 0, 1.2))
    b.cone(M["thatch"], 4.4, 0.2, 2.6, (0, 0, 2.4), seg=4, rot=Matrix.Rotation(math.pi / 4, 4, "Z"))
    return b.obj("M_shack", coll=collection("_models"))


def model_canoe():
    b = Builder()
    b.box(M["darkwood"], (8, 1.1, 0.6), (0, 0, 0.3))
    for dx in (-2, 1.5):
        b.blob(M["skin"], 0.45, (dx, 0, 1.1), sz=1.6)
    return b.obj("M_canoe", coll=collection("_models"))


def model_ship(spanish=True):
    b = Builder()
    L, Wd = 26, 7
    b.box(M["darkwood"], (L, Wd, 4), (0, 0, 1.0))
    b.box(M["darkwood"], (6, Wd, 3), (-L / 2 + 3, 0, 4.2))        # sterncastle
    b.cone(M["darkwood"], Wd / 2, 0.4, 6, (L / 2, 0, 1.0), seg=4,
           rot=Matrix.Rotation(-math.pi / 2, 4, "Y") @ Matrix.Rotation(math.pi / 4, 4, "X"))  # bow
    masts = [(-5, 20), (4, 24), (10, 16)] if spanish else [(-4, 22), (6, 22)]
    for x, h in masts:
        b.cone(M["wood"], 0.35, 0.25, h, (x, 0, 3.0), seg=6)
        if spanish:
            for zz, w in ((h * 0.45, 9), (h * 0.75, 7)):
                b.box(M["sail"], (0.3, w, h * 0.25), (x + 0.4, 0, zz + 3))
        else:
            b.quad(M["sail"], [(x - 0.2, 0, 5), (x - 8, 0, 5), (x - 0.2, 0, h + 1)])
    if spanish:
        b.box(M["redsail"], (0.2, 1.6, 1.2), (masts[1][0], 0, masts[1][1] + 3.6))  # pennant
    return b.obj("M_ship" if spanish else "M_schooner", coll=collection("_models"))


def model_person(col="skin"):
    b = Builder()
    b.cone(M[col], 0.28, 0.22, 1.2, (0, 0, 0), seg=6)
    b.blob(M["skin"], 0.22, (0, 0, 1.42))
    return b.obj(f"M_person_{col}", coll=collection("_models"))


def model_trees():
    out = {}
    for v, s in enumerate((0.8, 1.0, 1.25)):
        b = Builder()
        b.cone(M["trunk"], 0.3 * s, 0.2 * s, 10 * s, (0, 0, 0), seg=5)
        b.cone(M["pineleaf"], 2.6 * s, 0.3 * s, 3.2 * s, (0, 0, 8.2 * s), seg=6)
        b.cone(M["pineleaf"], 1.8 * s, 0.1 * s, 2.4 * s, (0, 0, 10 * s), seg=6)
        out[("pine", v)] = b.obj(f"T_pine{v}", coll=collection("_models"))
        b = Builder()
        b.cone(M["trunk"], 0.4 * s, 0.3 * s, 3 * s, (0, 0, 0), seg=5)
        b.blob(M[f"leaf{v}"], 3.6 * s, (0, 0, 4.6 * s), sz=0.75)
        out[("hammock", v)] = b.obj(f"T_hammock{v}", coll=collection("_models"))
        b = Builder()
        for dx, dy in ((0, 0), (2.2, 0.8), (-1.6, 1.6)):
            b.blob(M[f"leaf{(v + 1) % 3}"], 2.3 * s, (dx * s, dy * s, 1.9 * s), sz=0.7)
        out[("mangrove", v)] = b.obj(f"T_mangrove{v}", coll=collection("_models"))
        b = Builder()
        b.cone(M["trunk"], 0.25 * s, 0.2 * s, 8 * s, (0, 0, 0), seg=5)
        b.blob(M["leaf2"], 2.8 * s, (0, 0, 8.2 * s), sz=0.35)
        out[("palm", v)] = b.obj(f"T_palm{v}", coll=collection("_models"))
    return out


def model_lighthouse():
    b = Builder()
    b.cone(M["white"], 3.4, 2.4, 20.0, (0, 0, 0), seg=16)
    b.cone(M["black"], 3.0, 3.0, 0.4, (0, 0, 20.0), seg=16)        # gallery
    b.cone(M["lamp"], 1.6, 1.6, 2.6, (0, 0, 20.4), seg=10)         # lantern glass
    b.cone(M["black"], 1.9, 0.2, 1.4, (0, 0, 23.0), seg=10)        # cap
    for z in (5, 10, 15):
        b.box(M["glow"], (0.4, 0.8, 1.4), (-2.9 + z * 0.045, 0, z))  # windows (glow when burning)
    b.box(M["glow"], (0.4, 1.6, 2.4), (-3.3, 0, 1.2))               # door
    return b.obj("lighthouse", coll=collection("act1_lighthouse"))


def model_house(name, w=8, d=6, h=3.5, wall="white", roof="darkwood"):
    b = Builder()
    b.box(M[wall], (w, d, h), (0, 0, h / 2))
    b.cone(M[roof], max(w, d) * 0.75, 0.2, h * 0.8, (0, 0, h), seg=4, rot=Matrix.Rotation(math.pi / 4, 4, "Z"))
    return b.obj(name)


def model_stockade(radius, n_posts, name, with_blockhouse=True):
    b = Builder()
    for i in range(n_posts):
        a = 2 * math.pi * i / n_posts
        b.cone(M["wood"], 0.35, 0.3, 4.5, (radius * math.cos(a), radius * math.sin(a), 0), seg=5)
    if with_blockhouse:
        b.box(M["wood"], (8, 8, 5), (0, 0, 2.5))
        b.box(M["darkwood"], (10, 10, 3.5), (0, 0, 6.7), rot=math.pi / 4)
        b.cone(M["darkwood"], 7.5, 0.3, 3, (0, 0, 8.4), seg=4)
    return b.obj(name)


def model_cross():
    b = Builder()
    b.box(M["wood"], (0.5, 0.5, 9), (0, 0, 4.5))
    b.box(M["wood"], (4, 0.5, 0.5), (0, 0, 7))
    return b.obj("cross_1566")


# ------------------------------------------------------------------------------ effects
def fire(name, loc, t0, t1, size=1.0, coll=None, light=True):
    coll = coll or collection("fx")
    b = Builder()
    b.blob(M["fire"], 1.6 * size, (0, 0, 1.6 * size), sz=1.6)
    fl = b.obj(name + "_flame", coll=coll)
    fl.location = loc
    fl.scale = (0, 0, 0)
    fl.keyframe_insert("scale", frame=1)
    fl.keyframe_insert("scale", frame=fr(t0))
    f = fr(t0) + 2
    while f < fr(t1) - 3:
        s = rng.uniform(0.7, 1.3)
        fl.scale = (s, s, rng.uniform(0.8, 1.5))
        fl.keyframe_insert("scale", frame=f)
        f += 3
    fl.scale = (0, 0, 0)
    fl.keyframe_insert("scale", frame=fr(t1))
    if light:
        ld = bpy.data.lights.new(name + "_light", "POINT")
        ld.color = (1.0, 0.55, 0.2)
        ld.shadow_soft_size = 2
        lo = bpy.data.objects.new(name + "_light", ld)
        lo.location = loc + Vector((0, 0, 4 * size))
        coll.objects.link(lo)
        for fr_, e in [(1, 0), (fr(t0), 0), (fr(t0) + 6, 4000 * size), (fr(t1) - 6, 4000 * size), (fr(t1), 0)]:
            ld.energy = e
            ld.keyframe_insert("energy", frame=fr_)
    # smoke puffs rising on a loop
    for k in range(3):
        b = Builder()
        b.blob(M["smoke"], 3.0 * size, sub=1)
        sm = b.obj(f"{name}_smoke{k}", coll=coll)
        sm.scale = (0, 0, 0)
        sm.keyframe_insert("scale", frame=1)
        period = 2.4
        t = t0 + k * period / 3
        while t < t1 + 3:
            sm.location = loc + Vector((0, 0, 4 * size))
            sm.scale = (0.4, 0.4, 0.4)
            sm.keyframe_insert("location", frame=fr(t))
            sm.keyframe_insert("scale", frame=fr(t))
            drift = Vector((rng.uniform(8, 16), rng.uniform(-4, 4), 30 * size + rng.uniform(0, 10)))
            sm.location = loc + drift
            sm.scale = (2.2, 2.2, 2.2) if t < t1 else (0, 0, 0)
            sm.keyframe_insert("location", frame=fr(t + period) - 1)
            sm.keyframe_insert("scale", frame=fr(t + period) - 1)
            t += period
        sm.scale = (0, 0, 0)
        sm.keyframe_insert("scale", frame=fr(t) + 1)
    return fl


def flashes(name, locs, t0, t1, rate=1.5):
    coll = collection("fx")
    b = Builder()
    b.blob(M["flash"], 0.8)
    src = b.obj(name + "_src", coll=collection("_models"))
    for i, p in enumerate(locs):
        o = instance(src, f"{name}{i}", p, coll=coll)
        o.scale = (0, 0, 0)
        o.keyframe_insert("scale", frame=1)
        t = t0 + rng.uniform(0, 1.0 / rate)
        while t < t1:
            f = fr(t)
            for df, s in ((0, 0), (1, 1.5), (3, 0)):
                o.scale = (s, s, s)
                o.keyframe_insert("scale", frame=f + df)
            t += rng.uniform(0.6, 1.6) / rate


# ------------------------------------------------------------------------------ act 1
def place_trees(tree_models, clear_zones, plantation_rects):
    data = np.load(ASSETS / "trees.npz")
    coll = collection("vegetation")
    cap = {"pine": 60000, "hammock": 90000, "mangrove": 90000, "palm": 15000}
    for kind in ("pine", "hammock", "mangrove", "palm"):
        a = data[kind]
        if len(a) > cap[kind]:
            a = a[rng.choice(len(a), cap[kind], replace=False)]
        keep = np.ones(len(a), bool)
        for (cx, cy, r) in clear_zones:
            keep &= (a[:, 0] - cx) ** 2 + (a[:, 1] - cy) ** 2 > r * r
        a = a[keep]
        in_pl = np.zeros(len(a), bool)
        for (x0, y0, x1, y1) in plantation_rects:
            in_pl |= (a[:, 0] > x0) & (a[:, 0] < x1) & (a[:, 1] > y0) & (a[:, 1] < y1)
        for group, sel in (("", ~in_pl), ("_plantation", in_pl)):
            for v in range(3):
                pts = a[sel & (a[:, 3] == v)]
                if not len(pts):
                    continue
                me = bpy.data.meshes.new(f"pts_{kind}{v}{group}")
                co = np.stack([pts[:, 0], pts[:, 1], np.maximum(pts[:, 2], 0) * VZ], -1).astype(np.float32)
                me.vertices.add(len(co))
                me.vertices.foreach_set("co", co.ravel())
                par = bpy.data.objects.new(f"trees_{kind}{v}{group}", me)
                coll.objects.link(par)
                par.instance_type = "VERTS"
                child = tree_models[(kind, v)].copy()
                child.name = f"inst_{kind}{v}{group}"
                child.scale = (S_TREE,) * 3
                coll.objects.link(child)
                child.parent = par
                if group:  # plantation clearing in 1830
                    par["base_scale"] = 1.0
                    for o in (par,):
                        o.hide_render = False
                        o.keyframe_insert("hide_render", frame=1)
                        o.hide_render = True
                        o.keyframe_insert("hide_render", frame=fr(127))
                        o.hide_viewport = False
    print("trees placed")


def act1():
    materials()
    trees = model_trees()
    hut, shack, canoe = model_hut(), model_shack(), model_canoe()
    ship, schooner = model_ship(True), model_ship(False)
    person, sailor = model_person("skin"), model_person("navy")
    coll_v = collection("act1_village")

    # --- Tequesta village ---------------------------------------------------------------
    huts = []
    for (lat, lon, r, n) in [(25.7730, -80.1895, 260, 44), (25.7697, -80.1898, 140, 16)]:
        cx, cy = ll(lat, lon)
        tries = 0
        while n and tries < 4000:
            tries += 1
            a, d = rng.uniform(0, 2 * math.pi), r * math.sqrt(rng.uniform(0, 1))
            x, y = cx + d * math.cos(a), cy + d * math.sin(a)
            if height_m(x, y) < 0.6 or any((x - h[0]) ** 2 + (y - h[1]) ** 2 < 22 ** 2 for h in huts):
                continue
            huts.append((x, y))
            n -= 1
    order = rng.permutation(len(huts))
    stockade_xy = ll(25.7726, -80.1902)
    burn_rank = np.argsort([math.hypot(x - stockade_xy[0], y - stockade_xy[1]) for x, y in huts])
    burn_start = {int(i): 52.5 + 6.5 * k / len(huts) for k, i in enumerate(burn_rank)}
    pop = TL["population_at"]
    n_max = len(huts)
    for rank, i in enumerate(order):
        x, y = huts[i]
        o = instance(hut, f"hut{i}", Vector((x, y, ground(x, y))), rot=rng.uniform(0, math.pi), scale=S_HUT, coll=coll_v)
        # visible while the population supports this many huts (hut 'rank' is the n-th to exist)
        intervals, on = [], None
        for t in np.arange(0, 99.5, 0.5):
            growth = min(1.0, 0.25 + t / 20.0)   # the village grows over the first 20 s
            vis = rank < round(n_max * growth * interp(pop, t) / 800)
            if 52 <= t < 64:   # the burning: every hut standing at 52 s burns down by 60 s
                vis = rank < round(n_max * interp(pop, 51.5) / 800) and t < burn_start[int(i)] + 1.5
            if t < 64 and t >= 60:
                vis = False
            if vis and on is None:
                on = float(t)
            if not vis and on is not None:
                intervals.append((on, float(t)))
                on = None
        if on is not None:
            intervals.append((on, 99.0))
        key_visible(o, intervals)
        if rank < round(n_max * interp(pop, 51.5) / 800):
            p = Vector((x, y, ground(x, y)))
            fire(f"hutfire{i}", p, burn_start[int(i)], burn_start[int(i)] + 4.5, size=1.0,
                 light=(rank % 4 == 0))

    # Miami Circle (Brickell Point): posts + thatched roof, 500 BC - AD 750
    mc = Vector(ll(25.7697, -80.1888))
    mcz = Vector((mc.x, mc.y, ground(mc.x, mc.y)))
    b = Builder()
    for k in range(24):
        a = 2 * math.pi * k / 24
        b.cone(M["wood"], 0.4, 0.35, 3.2, (13 * math.cos(a), 13 * math.sin(a), 0), seg=5)
    posts = b.obj("miami_circle_posts", coll=coll_v)
    posts.location = mcz
    key_visible(posts, [(0, 24.0)])
    b = Builder()
    b.cone(M["thatch"], 15, 0.5, 6, (0, 0, 3.2), seg=16)
    roof = b.obj("miami_circle_roof", coll=coll_v)
    roof.location = mcz
    key_visible(roof, [(0, 19.5)])

    # canoes on the bay (daily life), fewer as the population falls
    coll_b = collection("act1_boats")
    mouth = Vector((*ll(25.7702, -80.1878), 0.3))
    for k in range(10):
        c = instance(canoe, f"canoe{k}", mouth, scale=3.0, coll=coll_b)
        keys, t = [], rng.uniform(0, 3)
        last = 95 if k < 3 else (52 if k >= 6 else 90)
        while t < last:
            a, d = rng.uniform(0, 2 * math.pi), rng.uniform(300, 2600)
            x, y = water_snap(mouth.x + d * math.cos(a), mouth.y + d * math.sin(a) * 0.8)
            keys.append((t, Vector((x, y, 0.3))))
            t += rng.uniform(5, 9)
        key_path(c, keys)
        key_visible(c, [(0, 52)] + ([(64, last)] if last > 64 else []))

    # exodus up the river (56-60 s) and departure for Cuba (92-99 s)
    river = [(25.7702, -80.1885), (25.7722, -80.1930), (25.7748, -80.1985), (25.7772, -80.2040),
             (25.7795, -80.2100), (25.7822, -80.2165), (25.7852, -80.2235)]
    rpts = [Vector((*water_snap(*ll(*p), depth=-0.3, radius=300), 0.3)) for p in river]
    for k in range(10):
        c = instance(canoe, f"exodus{k}", rpts[0], scale=3.0, coll=coll_b)
        t0 = 55.5 + k * 0.35
        key_path(c, [(t0 + j * 0.9, p) for j, p in enumerate(rpts)])
        key_visible(c, [(t0, t0 + 0.9 * len(rpts))])

    # --- ships ---------------------------------------------------------------------------
    def sea(lat, lon):
        return Vector((*water_snap(*ll(lat, lon), depth=-1.2), 0.0))

    entry = [sea(25.652, -80.128), sea(25.656, -80.166), sea(25.690, -80.183), sea(25.728, -80.180)]
    anchor = sea(25.7685, -80.1805)
    for k in range(2):  # 1513 Ponce de Leon
        s = instance(ship, f"ponce{k}", entry[0], scale=S_SHIP, coll=coll_b)
        off = Vector((k * 90, -k * 60, 0))
        key_path(s, [(26 + k, entry[0] + off), (28 + k, entry[1] + off), (30.5 + k, entry[2] + off),
                     (32.5 + k, entry[3] + off), (34 + k, entry[2] + off), (36 + k, entry[1] + off)])
        key_visible(s, [(26 + k, 37)])
    for k in range(2):  # 1566 Menendez: arrive, anchor, one leaves 1568
        s = instance(ship, f"menendez{k}", entry[0], scale=S_SHIP, coll=coll_b)
        off = Vector((k * 110, -k * 80, 0))
        keys = [(40, entry[1] + off), (42, entry[2] + off), (44, entry[3] + off), (45.5, anchor + off)]
        if k == 0:
            keys += [(60, anchor + off), (62, entry[3] + off), (64, entry[2] + off)]
        key_path(s, keys)
        key_visible(s, [(40, 64 if k == 0 else 58)])
    for name, t_in, t_out in [("ship1710", 76, 82), ("ship1743", 82.5, 92), ("ship1763", 92, 99.5)]:
        s = instance(ship if name != "ship1743" else schooner, name, entry[3], scale=S_SHIP, coll=coll_b)
        key_path(s, [(t_in, entry[3]), (t_in + 1.5, anchor), (t_out - 2, anchor), (t_out, entry[2])])
        key_visible(s, [(t_in, t_out)])
    for k in range(6):  # 1763: canoes carry the last people out to the ship
        c = instance(canoe, f"leave{k}", mouth, scale=3.0, coll=coll_b)
        t0 = 93 + k * 0.5
        key_path(c, [(t0, Vector((mouth.x, mouth.y, 0.3))), (t0 + 2.5, anchor + Vector((20 * k, 30, 0.3)))])
        key_visible(c, [(t0, t0 + 3)])

    # --- 1566/67 cross and stockade; 1743 stockade ----------------------------------------
    cross = model_cross()
    cross.location = P(25.7718, -80.1880)
    key_visible(cross, [(45, 64)], axis="z")
    st = model_stockade(28, 40, "stockade_1567")
    st.location = P(*[25.7726, -80.1902])
    key_visible(st, [(47, 64)], axis="z")
    st2 = model_stockade(16, 26, "stockade_1743")
    st2.location = P(25.7735, -80.1880)
    key_visible(st2, [(84, 92)], axis="z")

    # --- settlers (c. 1800) --------------------------------------------------------------
    for k, (lat, lon) in enumerate([(25.7745, -80.1872), (25.7752, -80.1880), (25.7690, -80.1915),
                                    (25.7680, -80.1905), (25.7760, -80.1868)]):
        xy = land_snap(*ll(lat, lon))
        if xy:
            o = instance(shack, f"shack{k}", Vector((xy[0], xy[1], ground(*xy))), rot=rng.uniform(0, 3),
                         scale=S_HUT, coll=coll_v)
            key_visible(o, [(103 + k * 2.2, 175)])

    # --- 1830 plantation ---------------------------------------------------------------
    coll_p = collection("act1_plantation")
    rects = []
    for (lat, lon, w, h) in [(25.7762, -80.1950, 260, 180), (25.7782, -80.2002, 240, 200),
                             (25.7752, -80.2012, 220, 150), (25.7796, -80.1945, 200, 160)]:
        cx, cy = ll(lat, lon)
        rects.append((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
        b = Builder()
        rows = 8
        for r in range(rows):
            b.box(M["field"] if r % 2 == 0 else M["soil"], (w, h / rows, 0.2),
                  (0, -h / 2 + (r + 0.5) * h / rows, 0))
        fo = b.obj(f"field_{lat}", coll=coll_p)
        fo.location = (cx, cy, ground(cx, cy) + 0.6)
        key_visible(fo, [(127, 175)])
    house = model_house("plantation_house", 14, 10, 6)
    house.location = P(25.7738, -80.1908)
    coll_p.objects.link(house)
    bpy.context.scene.collection.objects.unlink(house)
    key_visible(house, [(127.5, 175)], axis="z")
    cabin = model_house("M_cabin", 6, 4, 3, wall="wood", roof="darkwood")
    for k in range(8):
        xy = land_snap(*ll(25.7746 + (k // 4) * 0.0002, -80.1928 + (k % 4) * 0.00022))
        if xy:
            o = instance(cabin, f"cabin{k}", Vector((xy[0], xy[1], ground(*xy))), scale=1.6, coll=coll_p)
            key_visible(o, [(128 + k * 0.2, 175)], axis="z")
    for k in range(2):  # January 1836 evacuation boats
        c = instance(canoe, f"evac{k}", mouth, scale=3.4, coll=coll_b)
        key_path(c, [(139.5 + k, Vector((mouth.x, mouth.y, 0.3))), (143 + k, sea(25.745, -80.180) + Vector((0, 0, 0.3)))])
        key_visible(c, [(139.5 + k, 144 + k)])

    # --- Cape Florida lighthouse ----------------------------------------------------------
    lh = model_lighthouse()
    lh_p = P(25.6664, -80.1557)
    lh.location = lh_p
    lh.scale = (S_TOWER,) * 3
    lh["base_scale"] = S_TOWER
    key_visible(lh, [(116.5, 175)], grow=int(4.5 * FPS), axis="z")
    lamp = M["lamp"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for t, e in [(0, 0), (121.5, 0), (122.5, 40), (150, 40), (151, 0)]:
        lamp.default_value = e
        lamp.keyframe_insert("default_value", frame=fr(t))
    glow = M["glow"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    for t, e in [(0, 0), (148.5, 0), (150, 25), (160, 25), (161, 80), (162, 30), (167, 5), (170, 0)]:
        glow.default_value = e
        glow.keyframe_insert("default_value", frame=fr(t))
    keeper = model_house("keepers_house", 8, 6, 3.5)
    keeper.location = lh_p + Vector((-22, 16, 0))
    keeper.location.z = ground(keeper.location.x, keeper.location.y)
    key_visible(keeper, [(118, 162)], axis="z")
    ruin = model_house("keepers_house_ruin", 8, 6, 1.2, wall="ash", roof="ash")
    ruin.location = keeper.location
    key_visible(ruin, [(162, 175)], axis="z")
    fire("keeperfire", keeper.location, 151, 166, size=1.6)
    fire("towerfire", lh_p + Vector((-3.5, 0, 0)), 148.5, 162, size=1.3)
    # 1835 hurricane: the water rises over Key Biscayne
    w = bpy.data.objects["water"]
    for t, z in [(0, 0), (135.5, 0), (137, 1.0 * VZ), (138.2, 1.0 * VZ), (139, 0)]:
        w.location.z = z
        w.keyframe_insert("location", frame=fr(t))

    # raiders: land at 144 s, surround, fire, leave after the explosion
    coll_a = collection("act1_attack")
    land_xy = land_snap(lh_p.x - 110, lh_p.y - 40) or (lh_p.x - 30, lh_p.y - 20)
    land_at = Vector((land_xy[0], land_xy[1], 0))
    boat = instance(canoe, "raider_boat", lh_p, scale=3.6, coll=coll_a)
    far = Vector((*water_snap(lh_p.x - 900, lh_p.y - 300), 0.3))
    near = Vector((*water_snap(land_at.x - 40, land_at.y - 20, depth=-0.3), 0.3))
    key_path(boat, [(142, far), (144.5, near), (160.5, near), (163.5, far)])
    key_visible(boat, [(142, 164)])
    ring = []
    for k in range(12):
        a = 2 * math.pi * k / 12 + rng.uniform(-0.2, 0.2)
        rad = rng.uniform(26, 44)
        xy = land_snap(lh_p.x + rad * math.cos(a), lh_p.y + rad * math.sin(a)) or (lh_p.x, lh_p.y - 30)
        tgt = Vector((xy[0], xy[1], ground(*xy)))
        ring.append(tgt)
        o = instance(person, f"raider{k}", land_at, scale=S_PERSON, coll=coll_a)
        start = Vector((land_at.x, land_at.y, ground(land_at.x, land_at.y)))
        key_path(o, [(144.5, start), (146.5 + k * 0.1, tgt), (158.5, tgt), (160.5, start)])
        key_visible(o, [(144.5, 161)])
    flashes("musket", [p + Vector((0, 0, 1.4 * S_PERSON)) for p in ring], 145, 157, rate=0.8)
    for k, dx in enumerate((-1.3, 1.3)):   # Thompson and Carter at the gallery
        o = instance(sailor, f"defender{k}", lh_p + Vector((dx, 1.8, 20.2 * S_TOWER)), scale=S_PERSON * 0.7, coll=coll_a)
        key_visible(o, [(154, 158.5 if k == 1 else 164)])
    # the powder keg: flash + light pulse at 160 s
    b = Builder()
    b.blob(M["flash"], 3, sub=2)
    boom = b.obj("keg_explosion", coll=coll_a)
    boom.location = lh_p + Vector((0, 0, 10 * S_TOWER))
    for t, s in [(0, 0), (160, 0), (160.15, 5), (160.5, 3), (161.2, 0)]:
        boom.scale = (s, s, s * 2.5)
        boom.keyframe_insert("scale", frame=fr(t))
    ld = bpy.data.lights.new("keg_light", "POINT")
    ld.color = (1, 0.7, 0.4)
    lo = bpy.data.objects.new("keg_light", ld)
    lo.location = boom.location
    coll_a.objects.link(lo)
    for t, e in [(0, 0), (160, 0), (160.15, 400000), (160.8, 60000), (161.6, 0)]:
        ld.energy = e
        ld.keyframe_insert("energy", frame=fr(t))
    # rescue: schooner Motto at dawn, rowboat to the beach
    mot = instance(schooner, "motto", lh_p, scale=S_SHIP, coll=coll_a)
    off1 = Vector((*water_snap(lh_p.x + 1800, lh_p.y - 700, depth=-2), 0))
    off2 = Vector((*water_snap(lh_p.x + 350, lh_p.y - 260, depth=-2), 0))
    key_path(mot, [(163.5, off1), (166, off2), (175, off2 + Vector((-10, 0, 0)))])
    key_visible(mot, [(163.5, 175)])
    row = instance(canoe, "rowboat", off2, scale=3.0, coll=coll_a)
    key_path(row, [(166, off2 + Vector((0, 0, 0.3))), (167.8, near)])
    key_visible(row, [(166, 168)])

    # --- Fort Dallas (1836) -------------------------------------------------------------
    coll_f = collection("act1_fort_dallas")
    for k, (lat, lon) in enumerate([(25.7731, -80.1893), (25.7724, -80.1882)]):
        bh = model_stockade(0.01, 1, f"blockhouse{k}")
        bh.location = P(lat, lon)
        bh.scale = (1.4,) * 3
        bh["base_scale"] = 1.4
        key_visible(bh, [(169 + k * 0.6, 175)], axis="z")
    b = Builder()
    b.cone(M["white"], 0.2, 0.15, 16, (0, 0, 0), seg=6)
    for s in range(5):
        b.box(M["red"] if s % 2 == 0 else M["white"], (0.1, 5, 0.6), (0, 2.6, 15.4 - s * 0.6))
    b.box(M["navy"], (0.12, 2.2, 1.8), (0, 1.2, 14.8))
    flag = b.obj("flag_fort_dallas", coll=coll_f)
    flag.location = P(25.7728, -80.1888)
    key_visible(flag, [(170.5, 175)], axis="z")
    sch = instance(schooner, "schooner_bay_1836", anchor, scale=S_SHIP, coll=coll_f)
    key_path(sch, [(168, entry[3]), (171, anchor), (175, anchor + Vector((30, 20, 0)))])
    key_visible(sch, [(168, 175)])

    # --- vegetation (cleared around the village, circle, lighthouse; plantation in 1830) ---
    vx, vy = ll(25.7722, -80.1895)
    clear = [(vx, vy, 330), (mc.x, mc.y, 60), (lh_p.x, lh_p.y, 70)]
    place_trees(trees, clear, rects)

    # hide model sources from render
    for o in collection("_models").objects:
        o.hide_render = True
        o.hide_viewport = True
    for o in bpy.data.objects:  # instancers hide their child in render; keep child visible for dupliverts
        if o.name.startswith("inst_"):
            o.hide_viewport = False


# ------------------------------------------------------------------------------ main
def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", default=str(HERE / "act1.blend"))
    ap.add_argument("--stills", help="render one frame per beat into this folder")
    ap.add_argument("--anim", help="render the animation (PNG frames) into this folder")
    ap.add_argument("--step", type=int, default=1, help="render every Nth frame")
    ap.add_argument("--start", type=float, default=0.0, help="start time (s) for --anim")
    ap.add_argument("--end", type=float, default=None, help="end time (s) for --anim")
    ap.add_argument("--res", default="1280x720")
    ap.add_argument("--samples", type=int, default=24)
    return ap.parse_args(argv)


def main():
    a = parse()
    res = tuple(int(v) for v in a.res.lower().split("x"))
    sc = setup_scene(res, a.samples)
    build_terrain()
    build_water()
    build_sky_and_sun()
    build_camera()
    act1()
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=a.save)
        print("saved", a.save)
    if a.stills:
        out = Path(a.stills)
        out.mkdir(parents=True, exist_ok=True)
        for i, b in enumerate(TL["beats"]):
            t = b["t"][0] + 0.65 * (b["t"][1] - b["t"][0])
            sc.frame_set(fr(t))
            sc.render.filepath = str(out / f"beat{i:02d}_{b['shot']}_t{t:05.1f}.png")
            bpy.ops.render.render(write_still=True)
            print("still", sc.render.filepath)
    if a.anim:
        out = Path(a.anim)
        out.mkdir(parents=True, exist_ok=True)
        f0 = fr(a.start)
        f1 = fr(a.end) if a.end is not None else sc.frame_end
        for f in range(f0, f1 + 1, a.step):
            p = out / f"f{f:05d}.png"
            if p.exists():
                continue  # resumable
            sc.frame_set(f)
            sc.render.filepath = str(p)
            bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
