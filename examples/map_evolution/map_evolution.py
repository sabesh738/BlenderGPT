"""
Map Evolution: a Clash-of-Clans-style 3D history diorama for Blender.

Builds a floating island split into kingdoms, then animates it through
six eras (Stone Age -> Modern World). In each era the buildings are
replaced, territory spreads outward, armies march and fight, and the
borders are redrawn by whoever wins. Everything is procedural: no
assets, no add-ons, no internet.

Run it
  * In Blender: Scripting workspace -> open this file -> Run Script.
    It builds a new scene called "MapEvolution" (your other scenes are
    left alone). Press Numpad 0 to look through the camera, then Space.
  * From a terminal (Blender 3.3+; tested on 4.5 LTS and 5.0):
      blender -b --python map_evolution.py -- --save history.blend
      blender -b --python map_evolution.py -- --stills renders/
      blender -b --python map_evolution.py -- --animation
    Extra options: --seed N, --cycles, --samples N, --resolution PCT.

Change the SETTINGS and ERAS blocks below to make it your own.
"""

import argparse
import math
import os
import random
import sys
from contextlib import contextmanager
from itertools import combinations, product

import bpy  # must come first when running with the pip "bpy" module
import bmesh
from mathutils import Matrix, Vector

# ---------------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------------
SEED = 11
GRID = 24                  # the island fits in a GRID x GRID tile square
NUM_KINGDOMS = 7
MIN_SURVIVORS = 2          # wars never wipe out more kingdoms than this
FPS = 24
ERA_FRAMES = 240           # 10 s per era at 24 fps (keep >= 240)
OUTRO_FRAMES = 72
UNIT_SCALE = 1.5           # troops are chunky, like in Clash of Clans
CAM_LENS = 40
CAM_DISTANCE = 36
CAM_ELEVATION = 52         # degrees above the horizon
ORBIT_DEGREES = 70         # slow orbit over the whole film
BATTLE_ZOOM = 0.55         # camera distance multiplier during battles
DOF_FSTOP = 2.2            # tilt-shift "miniature" blur; 0 turns it off
PREFIX = "ME_"
SCENE_NAME = "MapEvolution"

KINGDOMS = [
    ("Crimson", "#e53935"), ("Azure", "#1e88e5"), ("Golden", "#fdd835"),
    ("Violet", "#8e24aa"), ("Amber", "#fb8c00"), ("Teal", "#00acc1"),
    ("Rose", "#ec407a"), ("Ivory", "#f5f5f5"),
]

# Each era swaps the building set and the army. "reach" is how far
# civilization has spread from each city; "density" is how built-up owned
# land is; "wars" is how many battles happen (max 2).
ERAS = [
    dict(name="STONE AGE", year="10,000 BC", house="hut", capital="camp",
         unit="clubman", heavy=None, density=0.10, reach=2.6, wars=1),
    dict(name="ANCIENT EMPIRES", year="2500 BC", house="mudbrick", capital="pyramid",
         unit="spearman", heavy=None, density=0.16, reach=4.0, wars=1),
    dict(name="MIDDLE AGES", year="1200 AD", house="cottage", capital="castle",
         unit="knight", heavy=None, density=0.22, reach=5.5, wars=2, walls=True),
    dict(name="AGE OF GUNPOWDER", year="1650 AD", house="townhouse", capital="palace",
         unit="musketeer", heavy="cannon", density=0.28, reach=7.5, wars=2,
         walls=True, gunpowder=True),
    dict(name="INDUSTRIAL AGE", year="1914 AD", house="rowhouse", capital="parliament",
         unit="rifleman", heavy="landship", density=0.34, reach=10.0, wars=2,
         gunpowder=True, factories=0.3, clear_forests=True),
    dict(name="MODERN WORLD", year="2025 AD", house="tower", capital="supertall",
         unit="trooper", heavy="tank", density=0.42, reach=99.0, wars=2,
         gunpowder=True, jets=True, clear_forests=True),
]

GRASS, SAND, ROCK = "#6cc04a", "#e9d08f", "#9a9a9a"
TEAM_TINT = 0.62           # how strongly territory colors the grass
HOP = 0.07                 # marching bounce height

UP = Vector((0.0, 0.0, 1.0))


def T(frames):
    """Scale a timing written for a 240-frame era to ERA_FRAMES."""
    return int(round(frames * ERA_FRAMES / 240))


# ---------------------------------------------------------------------------
# Colors and materials
# ---------------------------------------------------------------------------
def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def to_linear(rgb):
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb)


def mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def rgba(hex_or_rgb, tint=None, amount=0.0):
    rgb = hex_rgb(hex_or_rgb) if isinstance(hex_or_rgb, str) else hex_or_rgb
    if tint is not None:
        rgb = mix(rgb, hex_rgb(tint), amount)
    return (*to_linear(rgb), 1.0)


class Namespace(dict):
    __getattr__ = dict.__getitem__


M = Namespace()


def set_input(node, names, value):
    for name in names:
        if name in node.inputs:
            node.inputs[name].default_value = value
            return


def make_material(name, color="#ffffff", rough=0.75, metal=0.0, emit=0.0,
                  object_color=False, casts_shadow=True):
    mat = bpy.data.materials.new(PREFIX + name)
    try:
        mat.use_nodes = True
    except AttributeError:
        pass
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    col = rgba(color)
    set_input(bsdf, ("Roughness",), rough)
    set_input(bsdf, ("Metallic",), metal)
    if object_color:
        info = nt.nodes.new("ShaderNodeObjectInfo")
        nt.links.new(info.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = col
    if emit:
        set_input(bsdf, ("Emission Color", "Emission"), col)
        set_input(bsdf, ("Emission Strength",), emit)
    mat.diffuse_color = col
    if not casts_shadow:
        try:
            mat.shadow_method = "NONE"      # EEVEE Legacy (Blender < 4.2)
        except AttributeError:
            pass
    return mat


def build_materials():
    spec = dict(
        team=dict(object_color=True, rough=0.6),
        dirt=dict(color="#8a5a2b", rough=0.95), stone=dict(color="#a3a3a3"),
        stone_dark=dict(color="#626266"), snow=dict(color="#f4f7fb", rough=0.5),
        mud=dict(color="#b08453"), straw=dict(color="#e8c35a"),
        wood=dict(color="#8d5a2b"), wood_dark=dict(color="#4e3420"),
        sand=dict(color="#e9cf8f"), sand_light=dict(color="#f5e4b5"),
        marble=dict(color="#f2efe6", rough=0.4),
        gold=dict(color="#ffc12b", rough=0.3, metal=0.9),
        plaster=dict(color="#f6efe0"), roof_red=dict(color="#d9462b"),
        roof_blue=dict(color="#3f6fb5"), slate=dict(color="#4a5566"),
        copper=dict(color="#4fb3a1", rough=0.4, metal=0.3),
        brick=dict(color="#a9472f"), dark=dict(color="#2b2b30"),
        metal=dict(color="#b8bec7", rough=0.35, metal=0.8),
        olive=dict(color="#5f6b3a"),
        glass=dict(color="#7fc8f0", rough=0.08, metal=0.4),
        concrete=dict(color="#cfd3d6"), leaf=dict(color="#4fae3b"),
        pine=dict(color="#2f7d3a"), skin=dict(color="#f2c29b"),
        hair=dict(color="#3b2a1a"),
        fire=dict(color="#ffb02e", emit=8.0), smoke=dict(color="#6e6e6e", rough=1.0),
        dust=dict(color="#c9ad82", rough=1.0),
        water=dict(color="#2f8fd8", rough=0.12),
        cloud=dict(color="#ffffff", emit=0.35, rough=1.0, casts_shadow=False),
        title=dict(color="#ffd23f", emit=0.5, rough=0.3, casts_shadow=False),
        subtitle=dict(color="#ffffff", emit=0.4, casts_shadow=False),
    )
    for name, kw in spec.items():
        M[name] = make_material(name, **kw)


# ---------------------------------------------------------------------------
# Low-poly mesh kit: every building / unit / prop is one mesh with several
# material slots, built once and shared by all its instances.
# ---------------------------------------------------------------------------
def _bevel(bm, edges, offset):
    kw = dict(geom=edges, offset=offset, offset_type="OFFSET", segments=1,
              profile=0.5, clamp_overlap=True, material=-1)
    try:
        bmesh.ops.bevel(bm, affect="EDGES", **kw)
    except TypeError:
        bmesh.ops.bevel(bm, vertex_only=False, **kw)


class Kit:
    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []
        self.xf = Matrix.Identity(4)

    @contextmanager
    def at(self, x=0.0, y=0.0, z=0.0, s=1.0, rot=0.0):
        prev = self.xf
        self.xf = (prev @ Matrix.Translation((x, y, z)) @ Matrix.Rotation(rot, 4, "Z")
                   @ Matrix.Scale(s, 4))
        try:
            yield self
        finally:
            self.xf = prev

    def _slot(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def _finish(self, verts, mat):
        idx = self._slot(mat)
        faces = {f for v in verts for f in v.link_faces}
        for f in faces:
            f.material_index = idx
        return faces

    def box(self, mat, x, y, z0, sx, sy, sz, bevel=None, top=None):
        m = (self.xf @ Matrix.Translation((x, y, z0 + sz / 2))
             @ Matrix.Diagonal((sx, sy, sz, 1.0)))
        verts = bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)["verts"]
        faces = self._finish(verts, mat)
        if top is not None:
            top_idx = self._slot(top)
            for f in faces:
                f.normal_update()
                if f.normal.z > 0.9:
                    f.material_index = top_idx
        if bevel is None:
            bevel = min(0.035, min(sx, sy, sz) * 0.18)
        bevel *= self.xf.to_scale()[0]
        if bevel > 0.004:
            _bevel(self.bm, list({e for v in verts for e in v.link_edges}), bevel)

    def cyl(self, mat, x, y, z0, r, h, seg=12, r2=None, rot=0.0):
        m = self.xf @ Matrix.Translation((x, y, z0 + h / 2)) @ Matrix.Rotation(rot, 4, "Z")
        verts = bmesh.ops.create_cone(
            self.bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r,
            radius2=r if r2 is None else r2, depth=h, matrix=m)["verts"]
        self._finish(verts, mat)

    def cone(self, mat, x, y, z0, r, h, seg=12, rot=0.0):
        self.cyl(mat, x, y, z0, r, h, seg, r2=0.004, rot=rot)

    def rod(self, mat, p0, p1, r, seg=6):
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        rot = UP.rotation_difference(d.normalized()).to_matrix().to_4x4()
        m = self.xf @ Matrix.Translation((p0 + p1) / 2) @ rot
        verts = bmesh.ops.create_cone(
            self.bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r,
            radius2=r, depth=d.length, matrix=m)["verts"]
        self._finish(verts, mat)

    def sphere(self, mat, x, y, z, r, sx=1.0, sy=1.0, sz=1.0, subd=1):
        m = self.xf @ Matrix.Translation((x, y, z)) @ Matrix.Diagonal((sx, sy, sz, 1.0))
        verts = bmesh.ops.create_icosphere(self.bm, subdivisions=subd, radius=r,
                                           matrix=m)["verts"]
        self._finish(verts, mat)

    def prism(self, mat, x, y, z0, w, d, h, rot=0.0):
        """Gable roof: ridge along local Y, w wide, d long, h tall."""
        m = self.xf @ Matrix.Translation((x, y, z0)) @ Matrix.Rotation(rot, 4, "Z")
        pts = [(-w / 2, -d / 2, 0), (w / 2, -d / 2, 0), (0, -d / 2, h),
               (-w / 2, d / 2, 0), (w / 2, d / 2, 0), (0, d / 2, h)]
        v = [self.bm.verts.new(m @ Vector(p)) for p in pts]
        for idx in ((0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)):
            self.bm.faces.new([v[i] for i in idx])
        self._finish(v, mat)

    def crenels(self, mat, x0, y0, x1, y1, z0, n, size=0.07):
        for i in range(n):
            t = (i + 0.5) / n
            self.box(mat, x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, z0, size, size, size * 0.9,
                     bevel=0)

    def build(self, name):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        me = bpy.data.meshes.new(PREFIX + name)
        self.bm.to_mesh(me)
        self.bm.free()
        for mat in self.mats:
            me.materials.append(mat)
        return me


# --- terrain & props --------------------------------------------------------
def k_tile(k):
    k.box(M.dirt, 0, 0, -1.3, 0.97, 0.97, 1.3, bevel=0.04, top=M.team)


def k_peak(k):
    k.cone(M.stone, 0, 0, 0, 0.55, 0.9, seg=5)
    k.cyl(M.snow, 0, 0, 0.62, 0.2, 0.29, seg=5, r2=0.004)
    k.sphere(M.stone_dark, 0.3, -0.25, 0.05, 0.14)
    k.sphere(M.stone, -0.3, 0.28, 0.04, 0.11)


def k_pine(k):
    k.cyl(M.wood, 0, 0, 0, 0.05, 0.14, seg=6)
    k.cone(M.pine, 0, 0, 0.1, 0.24, 0.32, seg=7)
    k.cone(M.pine, 0, 0, 0.28, 0.17, 0.26, seg=7)


def k_oak(k):
    k.cyl(M.wood, 0, 0, 0, 0.05, 0.2, seg=6)
    k.sphere(M.leaf, 0, 0, 0.34, 0.2)
    k.sphere(M.leaf, 0.1, 0.05, 0.46, 0.14)


def k_flag(k):
    k.cyl(M.wood_dark, 0, 0, 0, 0.022, 1.1, seg=6)
    k.box(M.team, 0.15, 0, 0.86, 0.28, 0.02, 0.18, bevel=0)
    k.sphere(M.gold, 0, 0, 1.12, 0.04)


def k_wall(k):
    k.box(M.stone, 0, 0, 0, 1.0, 0.14, 0.26)
    k.crenels(M.stone, -0.5, 0, 0.5, 0, 0.26, 5, size=0.1)


# --- buildings: one per era, plus a capital landmark ------------------------
def k_hut(k):
    k.cyl(M.mud, 0, 0, 0, 0.25, 0.26, seg=9)
    k.cone(M.straw, 0, 0, 0.24, 0.34, 0.36, seg=9)
    k.box(M.wood_dark, 0.24, 0, 0, 0.04, 0.12, 0.17, bevel=0)


def k_camp(k):
    with k.at(s=1.35):
        k_hut(k)
    with k.at(0.5, -0.4, s=0.75):
        k_hut(k)
    with k.at(-0.45, 0.45, s=0.75):
        k_hut(k)
    k.box(M.wood, -0.5, -0.45, 0, 0.1, 0.1, 0.55)
    k.box(M.team, -0.5, -0.45, 0.5, 0.18, 0.18, 0.1)
    for a in range(7):
        ang = a / 7 * math.tau
        k.sphere(M.stone, 0.5 + 0.1 * math.cos(ang), 0.4 + 0.1 * math.sin(ang), 0.02, 0.04)
    k.cone(M.fire, 0.5, 0.4, 0, 0.07, 0.2, seg=5)


def k_mudbrick(k):
    k.box(M.sand, 0, 0, 0, 0.52, 0.46, 0.3)
    k.box(M.sand_light, 0, 0, 0.3, 0.56, 0.5, 0.04)
    k.box(M.sand, -0.12, -0.08, 0.34, 0.24, 0.24, 0.18)
    k.box(M.wood_dark, 0.265, 0.06, 0, 0.02, 0.12, 0.18, bevel=0)


def k_pyramid(k):
    k.cone(M.sand, -0.2, 0.2, 0, 0.75, 0.9, seg=4, rot=math.pi / 4)
    k.cyl(M.gold, -0.2, 0.2, 0.76, 0.085, 0.14, seg=4, r2=0.004, rot=math.pi / 4)
    with k.at(0.42, -0.45):
        k.box(M.marble, 0, 0, 0, 0.62, 0.46, 0.06)
        k.box(M.marble, 0, 0, 0.06, 0.54, 0.38, 0.05)
        for cx in (-0.2, -0.07, 0.07, 0.2):
            for cy in (-0.14, 0.14):
                k.cyl(M.marble, cx, cy, 0.11, 0.03, 0.26, seg=8)
        k.box(M.marble, 0, 0, 0.37, 0.56, 0.38, 0.06)
        k.prism(M.team, 0, 0, 0.43, 0.4, 0.58, 0.14, rot=math.pi / 2)


def k_cottage(k):
    k.box(M.plaster, 0, 0, 0, 0.46, 0.36, 0.28)
    k.prism(M.roof_red, 0, 0, 0.28, 0.44, 0.54, 0.24, rot=math.pi / 2)
    k.box(M.stone, -0.14, 0.1, 0.3, 0.08, 0.08, 0.2)
    k.box(M.wood_dark, 0, -0.185, 0, 0.1, 0.02, 0.17, bevel=0)


def k_castle(k):
    w, h = 0.6, 0.32
    for x, y, sx, sy in ((0, w, 2 * w, 0.1), (0, -w, 2 * w, 0.1),
                         (w, 0, 0.1, 2 * w), (-w, 0, 0.1, 2 * w)):
        k.box(M.stone, x, y, 0, sx, sy, h)
        if sx > sy:
            k.crenels(M.stone, x - w, y, x + w, y, h, 6)
        else:
            k.crenels(M.stone, x, y - w, x, y + w, h, 6)
    for cx, cy in product((-w, w), (-w, w)):
        k.cyl(M.stone, cx, cy, 0, 0.14, 0.58, seg=10)
        k.cone(M.roof_blue, cx, cy, 0.58, 0.18, 0.3, seg=10)
    k.box(M.stone, 0, 0, 0, 0.44, 0.44, 0.78)
    k.crenels(M.stone, -0.22, 0.22, 0.22, 0.22, 0.78, 4)
    k.crenels(M.stone, -0.22, -0.22, 0.22, -0.22, 0.78, 4)
    k.box(M.team, 0.23, 0, 0.35, 0.02, 0.16, 0.3, bevel=0)
    k.box(M.wood_dark, w + 0.05, 0, 0, 0.02, 0.16, 0.2, bevel=0)


def k_townhouse(k):
    k.box(M.plaster, 0, 0, 0, 0.44, 0.42, 0.5)
    for z in (0.14, 0.32):
        for y in (-0.1, 0.1):
            k.box(M.dark, 0.225, y, z, 0.02, 0.07, 0.1, bevel=0)
    k.prism(M.slate, 0, 0, 0.5, 0.48, 0.46, 0.22)


def k_palace(k):
    k.box(M.marble, 0, 0, 0, 1.0, 0.5, 0.36)
    k.box(M.marble, 0, 0, 0.36, 1.04, 0.54, 0.04)
    for x in (-0.45, 0.45):
        k.box(M.marble, x, 0.18, 0, 0.26, 0.56, 0.3)
    k.cyl(M.marble, 0, 0, 0.4, 0.2, 0.14, seg=16)
    k.sphere(M.copper, 0, 0, 0.54, 0.2, sz=0.9, subd=2)
    k.cyl(M.gold, 0, 0, 0.7, 0.02, 0.14, seg=6)
    for x in (-0.25, -0.15, -0.05, 0.05, 0.15, 0.25):
        k.cyl(M.marble, x, -0.29, 0, 0.025, 0.36, seg=8)
    k.box(M.team, 0, -0.26, 0.36, 0.3, 0.02, 0.1, bevel=0)


def k_rowhouse(k):
    k.box(M.brick, 0, 0, 0, 0.48, 0.44, 0.52)
    k.box(M.dark, 0, 0, 0.52, 0.5, 0.46, 0.03)
    k.box(M.brick, 0.16, 0.14, 0.55, 0.07, 0.07, 0.18)
    for z in (0.12, 0.32):
        for y in (-0.12, 0.0, 0.12):
            k.box(M.glass, 0.245, y, z, 0.02, 0.06, 0.1, bevel=0)


def k_factory(k):
    k.box(M.brick, 0, 0, 0, 0.86, 0.5, 0.34)
    for x in (-0.28, 0.0, 0.28):
        k.prism(M.slate, x, 0, 0.34, 0.28, 0.5, 0.14)
    for x in (-0.3, -0.08):
        k.cyl(M.brick, x, 0.18, 0, 0.06, 0.95, seg=8)
        k.cyl(M.dark, x, 0.18, 0.95, 0.07, 0.05, seg=8)


def k_parliament(k):
    k.box(M.stone, -0.15, 0, 0, 0.95, 0.5, 0.4)
    k.prism(M.slate, -0.15, 0, 0.4, 0.5, 0.95, 0.2, rot=math.pi / 2)
    k.box(M.stone, 0.45, 0, 0, 0.24, 0.24, 1.3)
    for rot in range(4):
        with k.at(0.45, 0, rot=rot * math.pi / 2):
            k.cyl(M.gold, 0.12, 0, 1.0, 0.07, 0.02, seg=10)
    k.cone(M.slate, 0.45, 0, 1.3, 0.17, 0.45, seg=4, rot=math.pi / 4)
    k.box(M.team, -0.15, -0.26, 0.2, 0.4, 0.02, 0.12, bevel=0)


def k_tower(k):
    k.box(M.concrete, 0, 0, 0, 0.54, 0.54, 0.08)
    k.box(M.glass, 0, 0, 0.08, 0.48, 0.48, 0.92, bevel=0.01)
    for z in (0.3, 0.55, 0.8):
        k.box(M.concrete, 0, 0, z, 0.5, 0.5, 0.025, bevel=0)
    k.box(M.concrete, 0, 0, 1.0, 0.4, 0.4, 0.06)


def k_supertall(k):
    k.box(M.concrete, 0, 0, 0, 0.8, 0.8, 0.1)
    k.box(M.glass, 0, 0, 0.1, 0.66, 0.66, 1.4, bevel=0.015)
    k.box(M.team, 0, 0, 1.5, 0.7, 0.7, 0.06)
    k.box(M.glass, 0, 0, 1.56, 0.5, 0.5, 1.1, bevel=0.015)
    k.box(M.team, 0, 0, 2.66, 0.54, 0.54, 0.05)
    k.box(M.glass, 0, 0, 2.71, 0.34, 0.34, 0.8, bevel=0.01)
    k.rod(M.metal, (0, 0, 3.5), (0, 0, 4.3), 0.025)


# --- troops (all face +X) ---------------------------------------------------
def soldier(k, helmet=None, weapon=None, shield=False):
    k.box(M.dark, 0, -0.035, 0, 0.05, 0.035, 0.06, bevel=0)
    k.box(M.dark, 0, 0.035, 0, 0.05, 0.035, 0.06, bevel=0)
    k.cyl(M.team, 0, 0, 0.05, 0.075, 0.13, seg=8)
    k.sphere(M.skin, 0, 0, 0.235, 0.06)
    if helmet == "hair":
        k.sphere(M.hair, -0.01, 0, 0.26, 0.055)
    elif helmet == "bronze":
        k.cone(M.gold, 0, 0, 0.25, 0.066, 0.08, seg=8)
    elif helmet == "great":
        k.cyl(M.metal, 0, 0, 0.19, 0.066, 0.1, seg=8)
        k.box(M.dark, 0.06, 0, 0.24, 0.02, 0.08, 0.015, bevel=0)
    elif helmet == "tricorn":
        k.cyl(M.dark, 0, 0, 0.27, 0.085, 0.03, seg=3, rot=math.pi)
    elif helmet in ("brodie", "modern"):
        if helmet == "brodie":
            k.cyl(M.olive, 0, 0, 0.27, 0.085, 0.01, seg=10)
        k.sphere(M.olive, 0, 0, 0.265, 0.064, sz=0.75)
    if weapon == "club":
        k.rod(M.wood, (0.06, 0.08, 0.1), (0.12, 0.1, 0.28), 0.018)
        k.sphere(M.wood, 0.12, 0.1, 0.29, 0.035)
    elif weapon == "spear":
        k.rod(M.wood, (0.08, 0.08, 0.02), (0.1, 0.08, 0.46), 0.01)
        k.cone(M.metal, 0.1, 0.08, 0.45, 0.022, 0.06, seg=4)
    elif weapon == "sword":
        k.rod(M.metal, (0.08, 0.09, 0.12), (0.18, 0.09, 0.3), 0.012)
    elif weapon == "musket":
        k.rod(M.wood, (-0.02, 0.08, 0.12), (0.28, 0.08, 0.2), 0.014)
    elif weapon == "rifle":
        k.rod(M.dark, (-0.02, 0.08, 0.13), (0.26, 0.08, 0.17), 0.012)
    if shield:
        k.box(M.team, 0.07, -0.085, 0.07, 0.02, 0.1, 0.13, bevel=0)
        k.sphere(M.metal, 0.085, -0.085, 0.135, 0.02)


UNIT_KITS = dict(
    clubman=lambda k: soldier(k, "hair", "club"),
    spearman=lambda k: soldier(k, "bronze", "spear", shield=True),
    knight=lambda k: soldier(k, "great", "sword", shield=True),
    musketeer=lambda k: soldier(k, "tricorn", "musket"),
    rifleman=lambda k: soldier(k, "brodie", "rifle"),
    trooper=lambda k: soldier(k, "modern", "rifle"),
)


def k_cannon(k):
    for y in (-0.11, 0.11):
        k.rod(M.wood_dark, (0, y - 0.015, 0.09), (0, y + 0.015, 0.09), 0.09, seg=10)
    k.box(M.wood, -0.04, 0, 0.05, 0.28, 0.12, 0.07, bevel=0)
    k.rod(M.dark, (-0.12, 0, 0.12), (0.24, 0, 0.18), 0.035, seg=8)
    k.box(M.team, -0.16, 0, 0.05, 0.06, 0.1, 0.1, bevel=0)


def k_landship(k):
    for y in (-0.12, 0.12):
        k.box(M.dark, 0, y, 0, 0.5, 0.05, 0.16, bevel=0.02)
    k.box(M.team, 0, 0, 0.03, 0.44, 0.2, 0.14)
    k.rod(M.dark, (0.05, 0.15, 0.1), (0.2, 0.15, 0.1), 0.015)
    k.rod(M.dark, (0.05, -0.15, 0.1), (0.2, -0.15, 0.1), 0.015)


def k_tank(k):
    for y in (-0.1, 0.1):
        k.box(M.dark, 0, y, 0, 0.46, 0.07, 0.09, bevel=0.02)
    k.box(M.team, 0, 0, 0.06, 0.42, 0.2, 0.08)
    k.box(M.team, -0.02, 0, 0.14, 0.18, 0.15, 0.07)
    k.rod(M.dark, (0.07, 0, 0.175), (0.36, 0, 0.175), 0.015)


def k_jet(k):
    k.rod(M.team, (-0.35, 0, 0), (0.25, 0, 0), 0.05, seg=8)
    k.cone(M.metal, 0.25, 0, 0, 0.05, 0.12, seg=8)
    k.box(M.team, -0.05, 0, -0.01, 0.22, 0.62, 0.02, bevel=0)
    k.box(M.team, -0.32, 0, 0.0, 0.12, 0.02, 0.16, bevel=0)
    k.sphere(M.glass, 0.1, 0, 0.04, 0.05, sx=1.8)


def k_fx(mat, r=0.5):
    return lambda k: k.sphere(mat, 0, 0, 0, r)


KIT_BUILDERS = dict(
    tile=k_tile, peak=k_peak, pine=k_pine, oak=k_oak, flag=k_flag, wall=k_wall,
    hut=k_hut, camp=k_camp, mudbrick=k_mudbrick, pyramid=k_pyramid,
    cottage=k_cottage, castle=k_castle, townhouse=k_townhouse, palace=k_palace,
    rowhouse=k_rowhouse, factory=k_factory, parliament=k_parliament,
    tower=k_tower, supertall=k_supertall, cannon=k_cannon, landship=k_landship,
    tank=k_tank, jet=k_jet, **UNIT_KITS,
)
KITS = {}


def kit(name):
    if name not in KITS:
        if name in KIT_BUILDERS:
            build = KIT_BUILDERS[name]
        else:   # fx: fire / smoke / dust / shot
            build = k_fx(M[{"shot": "dark"}.get(name, name)], 0.06 if name == "shot" else 0.5)
        k = Kit()
        build(k)
        KITS[name] = k.build(name)
    return KITS[name]


# ---------------------------------------------------------------------------
# Animation helpers
# ---------------------------------------------------------------------------
def fcurves_of(ob):
    """F-curves of an object's action: layered actions (4.4+) or classic."""
    ad = ob.animation_data
    action = ad.action
    if getattr(action, "layers", None):
        for layer in action.layers:
            for strip in layer.strips:
                bag = strip.channelbag(ad.action_slot)
                if bag is not None:
                    return bag.fcurves
    return action.fcurves


def key(ob, path, frame, value, interp="BEZIER"):
    setattr(ob, path, value)
    ob.keyframe_insert(data_path=path, frame=frame)
    if interp == "BEZIER":      # Blender's default for new keys
        return
    curves = fcurves_of(ob)
    for index in range(len(value) if hasattr(value, "__len__") else 1):
        fc = curves.find(path, index=index)
        if fc is None:
            continue
        for kp in reversed(fc.keyframe_points):
            if abs(kp.co.x - frame) < 0.5:
                kp.interpolation = interp
                break


def vec3(s):
    return (s, s, s) if isinstance(s, (int, float)) else tuple(s)


def pop_in(ob, frame, scale):
    """Scale up from nothing with a springy overshoot."""
    key(ob, "scale", frame, (0, 0, 0), "BACK")
    key(ob, "scale", frame + 10, vec3(scale), "LINEAR")


def pop_out(ob, frame, scale):
    key(ob, "scale", frame, vec3(scale), "QUAD")
    key(ob, "scale", frame + 8, (0, 0, 0), "CONSTANT")


def visible_between(ob, start, end, scale):
    key(ob, "scale", start - 1, (0, 0, 0), "CONSTANT")
    key(ob, "scale", start, vec3(scale), "CONSTANT")
    key(ob, "scale", end, vec3(scale), "CONSTANT")
    key(ob, "scale", end + 1, (0, 0, 0), "CONSTANT")


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------
def remove_collection_tree(coll):
    for child in list(coll.children):
        remove_collection_tree(child)
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    if coll.name in bpy.data.collections:
        bpy.data.collections.remove(coll)


def fresh_scene():
    old = bpy.data.scenes.get(SCENE_NAME)
    if old:
        for child in list(old.collection.children):
            remove_collection_tree(child)
        for ob in list(old.collection.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.scenes.remove(old)
    for data in (bpy.data.meshes, bpy.data.materials, bpy.data.curves, bpy.data.lights,
                 bpy.data.cameras, bpy.data.worlds, bpy.data.texts, bpy.data.actions):
        for block in list(data):
            if block.name.startswith(PREFIX) and block.users == 0:
                data.remove(block)
    scene = bpy.data.scenes.new(SCENE_NAME)
    if bpy.context.window is not None:
        bpy.context.window.scene = scene
    return scene


class Tile:
    def __init__(self, key_, x, y):
        self.key = key_
        self.x, self.y, self.z = x, y, 0.0
        self.mountain = self.coast = False
        self.jitter = 0.0
        self.ob = None
        self.events = []        # (frame, owner id or None)
        self.trees = []
        self.cut = None         # frame the trees are cleared

    @property
    def pos(self):
        return Vector((self.x, self.y, 0.0))


class Kingdom:
    def __init__(self, kid, name, hexcolor, seat, strength):
        self.id, self.name, self.hex = kid, name, hexcolor
        self.color = rgba(hexcolor)
        self.seats = [seat]
        self.strength = strength
        self.alive = True


class War:
    pass


class Story:
    def __init__(self, scene, seed):
        self.scene = scene
        self.rng = random.Random(seed)
        self.tiles = {}
        self.kingdoms = []
        self.flags = {}
        self.chronicle = []
        root = bpy.data.collections.new(SCENE_NAME)
        scene.collection.children.link(root)
        self.coll = {}
        for name in ("Terrain", "Nature", "Buildings", "Armies", "FX", "Camera"):
            c = bpy.data.collections.new(f"{SCENE_NAME}_{name}")
            root.children.link(c)
            self.coll[name] = c
        self.frame_end = 1 + len(ERAS) * ERA_FRAMES + OUTRO_FRAMES

    # -- helpers ----------------------------------------------------------
    def spawn(self, kind, coll, loc, rot=0.0, scale=1.0, color=None, name=None):
        ob = bpy.data.objects.new(PREFIX + (name or kind), kit(kind))
        self.coll[coll].objects.link(ob)
        ob.location = loc
        ob.rotation_euler = (0.0, 0.0, rot)
        ob.scale = vec3(scale)
        if color is not None:
            ob.color = color
        return ob

    def dist(self, a, b):
        ta, tb = self.tiles[a], self.tiles[b]
        return math.hypot(ta.x - tb.x, ta.y - tb.y)

    def seat_dist(self, key_, seats):
        return min(self.dist(key_, s) for s in seats)

    def base_color(self, t):
        return ROCK if t.mountain else SAND if t.coast else GRASS

    def tile_color(self, t, kid):
        if kid is None:
            return rgba(self.base_color(t))
        return rgba(self.base_color(t), self.kingdoms[kid].hex, TEAM_TINT)

    # -- world generation ---------------------------------------------------
    def make_island(self):
        rng = self.rng
        ph = [rng.uniform(0, math.tau) for _ in range(3)]
        half = (GRID - 1) / 2
        for i in range(GRID):
            for j in range(GRID):
                x, y = i - half, j - half
                a = math.atan2(y, x)
                edge = (0.86 + 0.09 * math.sin(3 * a + ph[0]) + 0.06 * math.sin(5 * a + ph[1])
                        + 0.04 * math.sin(9 * a + ph[2]))
                if math.hypot(x, y) / (GRID / 2) < edge:
                    t = Tile((i, j), x, y)
                    t.z = rng.uniform(-0.03, 0.03)
                    t.jitter = rng.uniform(-0.6, 0.6)
                    self.tiles[(i, j)] = t
        for (i, j), t in self.tiles.items():
            t.coast = any(n not in self.tiles for n in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)))
        # two mountain ridges: natural borders nobody can own
        inner = [t for t in self.tiles.values() if math.hypot(t.x, t.y) < GRID * 0.3]
        for _ in range(2):
            c = rng.choice(inner)
            ang, length = rng.uniform(0, math.pi), rng.uniform(3, 5)
            d = Vector((math.cos(ang), math.sin(ang), 0)) * length / 2
            p0, p1 = c.pos - d, c.pos + d
            for t in self.tiles.values():
                seg = p1 - p0
                u = max(0.0, min(1.0, (t.pos - p0).dot(seg) / seg.length_squared))
                if (p0 + seg * u - t.pos).length < 0.75 and not t.coast and rng.random() < 0.85:
                    t.mountain = True
                    t.z = rng.uniform(0.2, 0.4)

    def make_kingdoms(self):
        rng = self.rng
        open_tiles = [t.key for t in self.tiles.values()
                      if not t.mountain and not t.coast and math.hypot(t.x, t.y) < GRID * 0.38]
        sep = GRID * 0.22
        seats = []
        while len(seats) < min(NUM_KINGDOMS, len(KINGDOMS)):
            for _ in range(4000):
                cand = rng.choice(open_tiles)
                if all(self.dist(cand, s) >= sep for s in seats):
                    seats.append(cand)
                    break
            else:
                sep *= 0.9
        for kid, seat in enumerate(seats):
            name, col = KINGDOMS[kid]
            self.kingdoms.append(Kingdom(kid, name, col, seat, rng.uniform(0.9, 1.15)))

    def territory(self, reach):
        own = {}
        alive = [k for k in self.kingdoms if k.alive]
        for key_, t in self.tiles.items():
            best, best_d = None, 1e9
            if not t.mountain:
                for k in alive:
                    d = (self.seat_dist(key_, k.seats) + t.jitter) / k.strength
                    if d < best_d:
                        best, best_d = k.id, d
            own[key_] = best if best_d <= reach else None
        return own

    def border_edges(self, own):
        edges = {}
        for (i, j), o in own.items():
            if o is None:
                continue
            for n in ((i + 1, j), (i, j + 1)):
                o2 = own.get(n)
                if o2 is None or o2 == o:
                    continue
                edges.setdefault((min(o, o2), max(o, o2)), []).append(((i, j), n))
        return edges

    # -- static scenery ---------------------------------------------------
    def build_terrain(self):
        rng = self.rng
        for t in self.tiles.values():
            t.ob = self.spawn("tile", "Terrain", (t.x, t.y, t.z),
                              color=self.tile_color(t, None), name="tile")
            if t.mountain:
                s = rng.uniform(0.8, 1.2)
                self.spawn("peak", "Nature", (t.x, t.y, t.z), rng.uniform(0, math.tau),
                           (s, s, s * rng.uniform(0.8, 1.5)))
            elif rng.random() < (0.35 if t.coast else 0.62):
                for _ in range(rng.choice((1, 1, 2, 3))):
                    loc = (t.x + rng.uniform(-0.3, 0.3), t.y + rng.uniform(-0.3, 0.3), t.z)
                    t.trees.append(self.spawn(rng.choice(("pine", "oak")), "Nature", loc,
                                              rng.uniform(0, math.tau), rng.uniform(0.8, 1.3)))
        water = bpy.data.meshes.new(PREFIX + "sea")
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=90, y_segments=90, size=60)
        bm.to_mesh(water)
        bm.free()
        water.materials.append(M.water)
        sea = bpy.data.objects.new(PREFIX + "sea", water)
        self.coll["Terrain"].objects.link(sea)
        sea.location.z = -0.42
        wave = sea.modifiers.new("Waves", "WAVE")
        wave.height, wave.width, wave.narrowness, wave.speed = 0.05, 1.4, 1.2, 0.02

    def build_lights(self):
        sun_data = bpy.data.lights.new(PREFIX + "Sun", "SUN")
        sun_data.energy = 3.6
        sun_data.color = to_linear(hex_rgb("#fff1dc"))
        sun_data.angle = math.radians(4)
        sun = bpy.data.objects.new(PREFIX + "Sun", sun_data)
        self.coll["Camera"].objects.link(sun)
        sun.rotation_euler = (math.radians(42), math.radians(8), math.radians(-35))
        world = bpy.data.worlds.new(PREFIX + "Sky")
        try:
            world.use_nodes = True
        except AttributeError:
            pass
        bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
        bg.inputs[0].default_value = rgba("#9fd8ff")
        bg.inputs[1].default_value = 0.9
        self.scene.world = world

    def build_camera(self):
        self.pivot = bpy.data.objects.new(PREFIX + "CameraPivot", None)
        self.coll["Camera"].objects.link(self.pivot)
        data = bpy.data.cameras.new(PREFIX + "Camera")
        data.lens = CAM_LENS
        data.clip_end = 500
        cam = bpy.data.objects.new(PREFIX + "Camera", data)
        self.coll["Camera"].objects.link(cam)
        cam.parent = self.pivot
        el = math.radians(CAM_ELEVATION)
        cam.location = (0, -CAM_DISTANCE * math.cos(el), CAM_DISTANCE * math.sin(el))
        cam.rotation_euler = (math.pi / 2 - el, 0, 0)
        if DOF_FSTOP > 0:
            data.dof.use_dof = True
            data.dof.focus_object = self.pivot
            data.dof.aperture_fstop = DOF_FSTOP
        self.camera = cam
        self.scene.camera = cam
        key(self.pivot, "rotation_euler", 1, (0, 0, 0), "LINEAR")
        key(self.pivot, "rotation_euler", self.frame_end, (0, 0, math.radians(ORBIT_DEGREES)),
            "LINEAR")
        self.cam_key(1, Vector(), 1.0)
        self.cam_key(self.frame_end, Vector(), 1.15)

        # Clash-of-Clans style cloud wipe between eras
        k = Kit()
        rng = random.Random(3)
        for _ in range(44):
            k.sphere(M.cloud, rng.uniform(-3.4, 3.4), rng.uniform(-2.3, 2.3),
                     rng.uniform(-0.6, 0.6), rng.uniform(0.7, 1.3), subd=2)
        clouds = bpy.data.objects.new(PREFIX + "CloudWipe", k.build("clouds"))
        self.coll["Camera"].objects.link(clouds)
        clouds.parent = cam
        self._no_shadow(clouds)
        self.clouds = clouds
        self.cloud_keys = [(1, 0.0), (8, 0.0), (24, 8.0), (25, -8.0)]
        self.cloud_keys += [(self.frame_end - 16, -8.0), (self.frame_end, 0.0)]

    def _no_shadow(self, ob):
        try:
            ob.visible_shadow = False
        except AttributeError:
            pass

    def cam_key(self, frame, target, zoom):
        key(self.pivot, "location", frame, target)
        key(self.pivot, "scale", frame, (zoom, zoom, zoom))

    def title(self, era, start):
        dist = CAM_DISTANCE * 0.8
        hh = dist * 18 / CAM_LENS * 9 / 16
        rig = bpy.data.objects.new(PREFIX + "Title", None)
        self.coll["Camera"].objects.link(rig)
        rig.parent = self.camera
        rig.location = (0, hh * 0.62, -dist)
        for text, size, y, mat in ((era["name"], hh * 0.2, 0.0, M.title),
                                   (era["year"], hh * 0.1, -hh * 0.2, M.subtitle)):
            crv = bpy.data.curves.new(PREFIX + text, "FONT")
            crv.body = text
            crv.align_x, crv.align_y = "CENTER", "CENTER"
            crv.size = size
            crv.extrude = size * 0.06
            crv.bevel_depth = size * 0.025
            crv.materials.append(mat)
            ob = bpy.data.objects.new(PREFIX + text, crv)
            self.coll["Camera"].objects.link(ob)
            ob.parent = rig
            ob.location = (0, y, 0)
            self._no_shadow(ob)
        pop_in(rig, start + T(18), 1.0)
        pop_out(rig, start + T(84), 1.0)

    # -- history --------------------------------------------------------------
    def plan_wars(self, era, own, start):
        rng = self.rng
        alive = {k.id: k for k in self.kingdoms if k.alive}
        edges = self.border_edges(own)
        if edges:
            pairs = sorted(edges, key=lambda p: -len(edges[p]))
        else:
            pairs = sorted(combinations(sorted(alive), 2),
                           key=lambda p: self.dist(alive[p[0]].seats[0], alive[p[1]].seats[0]))
        wars, busy = [], set()
        for slot in range(min(2, era["wars"])):
            options = [p for p in pairs if not set(p) & busy]
            if not options:
                break
            a, b = rng.choice(options[:3])
            busy |= {a, b}
            ka, kb = alive[a], alive[b]
            stronger_attacks = rng.random() < 0.7
            A, D = (ka, kb) if (ka.strength >= kb.strength) == stronger_attacks else (kb, ka)
            w = War()
            w.A, w.D = A, D
            w.a_seat, w.d_seat = min(product(A.seats, D.seats), key=lambda p: self.dist(*p))
            pa, pd = self.tiles[w.a_seat].pos, self.tiles[w.d_seat].pos
            mid = (pa + pd) / 2
            border = edges.get((min(a, b), max(a, b)))
            if border:
                e0, e1 = min(border, key=lambda e: ((self.tiles[e[0]].pos + self.tiles[e[1]].pos) / 2
                                                     - mid).length)
                w.point = (self.tiles[e0].pos + self.tiles[e1].pos) / 2
            else:
                w.point = mid
            w.dir = (pd - pa).normalized() if (pd - pa).length > 1e-6 else Vector((1, 0, 0))
            w.d_seats = list(D.seats)
            w.win = rng.random() < 0.3 + 0.5 * A.strength / (A.strength + D.strength)
            survivors = sum(k.alive for k in self.kingdoms)
            w.eliminate = w.win and survivors > MIN_SURVIVORS and (
                D.strength < A.strength * 0.9 or rng.random() < 0.4)
            if w.eliminate:
                A.seats += D.seats
                D.alive = False
                A.strength *= 1.1
                verb = "conquers"
            elif w.win:
                D.strength *= 0.72
                A.strength *= 1.12
                verb = "defeats"
            else:
                A.strength *= 0.82
                D.strength *= 1.1
                verb = "is repelled by"
            w.march = start + T(50 + slot * 55)
            w.arrive = w.march + T(45)
            w.end = w.arrive + T(40)
            wars.append(w)
            self.chronicle.append(f"{era['year']:>10}  {A.name} {verb} {D.name}"
                                  f"  (frames {w.march}-{w.end})")
        return wars

    def flip_times(self, before, after, wars, start):
        flips = {}
        for key_, old in before.items():
            new = after[key_]
            if old == new:
                continue
            war = next((w for w in wars if old in (w.A.id, w.D.id) or new in (w.A.id, w.D.id)),
                       None)
            if war is not None:
                tf = war.end + 4 + int(2.2 * (self.tiles[key_].pos - war.point).length)
            else:
                tf = start + T(200) + self.rng.randint(0, 8)
            flips[key_] = (min(tf, start + ERA_FRAMES - 14), war)
        return flips

    def place_buildings(self, e, era, own, seats, colonize, flips, start, last):
        rng = self.rng
        end = start + ERA_FRAMES
        capitals = {k.seats[0] for k in self.kingdoms if k.alive}
        for key_, t in self.tiles.items():
            kid = own[key_]
            if kid is None or t.mountain:
                continue
            d = self.seat_dist(key_, seats[kid])
            if era.get("clear_forests") and t.trees and t.cut is None and rng.random() < 0.5:
                t.cut = start + T(30) + rng.randint(0, 20)
            if key_ == seats[kid][0]:
                kind, scale = era["capital"], 1.0
            elif key_ in seats[kid]:
                kind, scale = era["house"], 1.25
            else:
                near_capital = any(max(abs(key_[0] - c[0]), abs(key_[1] - c[1])) <= 1
                                   for c in capitals)
                p = era["density"] * (1.8 if d < 2.5 else 1.0 if d < 5 else 0.45)
                if near_capital or rng.random() > p:
                    continue
                kind = era["house"]
                if rng.random() < era.get("factories", 0):
                    kind = "factory"
                scale = rng.uniform(0.85, 1.05)
            target = (scale, scale, scale)
            if kind == "tower":
                target = (scale, scale, scale * (rng.uniform(0.7, 1.2) + 2.0 * math.exp(-d / 3)))
            t_in = start + 4 + int(d * 3.5) + rng.randint(0, 6)
            if key_ in colonize:
                t_in = max(t_in, colonize[key_] + 4)
            t_in = min(t_in, start + T(100))
            if t.trees and (t.cut is None or t.cut > t_in):
                t.cut = t_in - 2
            ob = self.spawn(kind, "Buildings", (t.x, t.y, t.z), rng.randrange(4) * math.pi / 2,
                            0, self.kingdoms[kid].color)
            pop_in(ob, t_in, target)
            if key_ in flips:
                t_out, war = flips[key_]
                pop_out(ob, t_out, target)
                if war is not None:
                    self.impact(t.pos, t_out, 0.6, era)
            elif not last:
                pop_out(ob, end - 4, target)

    def place_walls(self, own, flips, start, last):
        rng = self.rng
        for edge_list in self.border_edges(own).values():
            for k1, k2 in edge_list:
                t1, t2 = self.tiles[k1], self.tiles[k2]
                rot = math.pi / 2 if k1[0] != k2[0] else 0.0
                loc = ((t1.x + t2.x) / 2, (t1.y + t2.y) / 2, max(t1.z, t2.z))
                ob = self.spawn("wall", "Buildings", loc, rot, 0)
                t_in = start + T(40) + rng.randint(0, 12)
                pop_in(ob, t_in, 1.0)
                broken = [flips[k] for k in (k1, k2) if k in flips]
                if broken:
                    t_out = min(f for f, _ in broken)
                    pop_out(ob, max(t_out, t_in + 12), 1.0)
                    self.dust(Vector(loc), t_out, 0.4)
                elif not last:
                    pop_out(ob, start + ERA_FRAMES - 4, 1.0)

    # -- battles & effects ----------------------------------------------------
    def spark(self, pos, t, size):
        ob = self.spawn("fire", "FX", pos, self.rng.uniform(0, math.tau), 0)
        key(ob, "scale", t, (0, 0, 0), "BACK")
        key(ob, "scale", t + 3, vec3(size), "QUAD")
        key(ob, "scale", t + 8, (0, 0, 0), "CONSTANT")

    def dust(self, pos, t, size, kind="dust", puffs=1):
        rng = self.rng
        for _ in range(puffs):
            p = pos + Vector((rng.uniform(-0.15, 0.15), rng.uniform(-0.15, 0.15), 0.1))
            ob = self.spawn(kind, "FX", p, rng.uniform(0, math.tau), 0)
            key(ob, "scale", t + 1, (0, 0, 0))
            key(ob, "scale", t + 9, vec3(size * 1.2))
            key(ob, "scale", t + 26, vec3(size * 0.9), "QUAD")
            key(ob, "scale", t + 40, (0, 0, 0), "CONSTANT")
            key(ob, "location", t + 1, p)
            key(ob, "location", t + 40, p + UP * size * 1.6)

    def boom(self, pos, t, size):
        self.spark(pos + UP * size * 0.3, t, size)
        self.dust(pos, t + 2, size, "smoke", puffs=2)

    def impact(self, pos, t, size, era):
        if era.get("gunpowder"):
            self.boom(pos, t, size)
        else:
            self.dust(pos, t, size, puffs=2)

    def shot(self, p0, p1, t, flight=10):
        ob = self.spawn("shot", "FX", p0, scale=0)
        top = (p0 + p1) / 2 + UP * (0.6 + (p1 - p0).length * 0.25)
        for f, p in ((t, p0), (t + flight // 2, top), (t + flight, p1)):
            key(ob, "location", f, p)
        visible_between(ob, t, t + flight, 1.0)
        self.spark(p0, t, 0.15)
        self.boom(p1, t + flight, 0.5)

    def unit(self, w, era, kind, kingdom, sgn, start_pos, station, won, heavy, end):
        rng = self.rng
        d = w.dir
        perp = Vector((-d.y, d.x, 0))
        face = math.atan2(sgn * d.y, sgn * d.x)
        ob = self.spawn(kind, "Armies", start_pos, face, 0, kingdom.color)
        s = UNIT_SCALE
        pop_in(ob, w.march - 10, s)
        steps = max(2, (w.arrive - w.march) // 6)
        for i in range(steps + 1):
            p = start_pos.lerp(station, i / steps)
            if not heavy and i % 2:
                p = p + UP * HOP
            key(ob, "location", w.march + round(i * (w.arrive - w.march) / steps), p)
        dies = (not won) or (not heavy and rng.random() < 0.25)
        t_death = rng.randint(w.arrive + 8, w.end - 2) if dies else w.end
        f, hop = w.arrive + 6, False
        while f < t_death:
            lunge = rng.uniform(0, 0.05 if heavy else 0.2)
            p = station + d * sgn * lunge + perp * rng.uniform(-0.06, 0.06)
            hop = not hop
            if hop and not heavy:
                p.z += HOP
            key(ob, "location", f, p)
            f += 6
        if heavy and era.get("gunpowder"):
            f = w.arrive + rng.randint(2, 10)
            while f < t_death - 12:
                target = (w.point + d * sgn * rng.uniform(0.4, 1.4)
                          + perp * rng.uniform(-0.8, 0.8))
                self.shot(station + d * sgn * 0.3 + UP * 0.2, target, f)
                f += rng.randint(10, 16)
        if dies:
            pop_out(ob, t_death, s)
            self.impact(station, t_death, 0.3, era)
            return
        key(ob, "location", w.end + 2, station)
        key(ob, "location", w.end + 6, station + UP * 0.3)   # victory hop
        key(ob, "location", w.end + 11, station)
        leave = end - 14
        if sgn > 0 and w.eliminate:     # victors march into the fallen capital
            target = (self.tiles[w.d_seat].pos
                      + Vector((rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), 0)))
            f0, f1 = w.end + 14, min(w.end + 14 + T(30), leave - 4)
            if f1 > f0 + 6:
                steps = max(2, (f1 - f0) // 6)
                for i in range(1, steps + 1):
                    p = station.lerp(target, i / steps)
                    if not heavy and i % 2:
                        p = p + UP * HOP
                    key(ob, "location", f0 + round(i * (f1 - f0) / steps), p)
        pop_out(ob, leave, s)

    def stage_battle(self, era, w, start):
        rng = self.rng
        end = start + ERA_FRAMES
        d = w.dir
        perp = Vector((-d.y, d.x, 0))
        heavy = era.get("heavy")
        for kingdom, sgn, seat, won in ((w.A, 1, w.a_seat, w.win), (w.D, -1, w.d_seat, not w.win)):
            seat_pos = self.tiles[seat].pos
            front = w.point - d * sgn * 0.5
            n = (8 if heavy else 9) if sgn > 0 else (6 if heavy else 7)
            for i in range(n):
                row, col = divmod(i, 3)
                col -= 1
                station = (front - d * sgn * (row * 0.32)
                           + perp * (col * 0.34 + rng.uniform(-0.05, 0.05)))
                start_pos = seat_pos + perp * (col * 0.28) - d * sgn * (row * 0.28)
                self.unit(w, era, era["unit"], kingdom, sgn, start_pos, station, won, False, end)
            if heavy:
                for c in (-1, 1):
                    station = front - d * sgn * 1.25 + perp * (c * 0.5)
                    self.unit(w, era, heavy, kingdom, sgn, seat_pos + perp * (c * 0.35),
                              station, won, True, end)
        for _ in range(10):     # clashing blades / musket fire along the front
            pos = (w.point + perp * rng.uniform(-0.7, 0.7) + d * rng.uniform(-0.2, 0.2)
                   + UP * 0.15)
            self.spark(pos, rng.randint(w.arrive + 4, w.end - 6), rng.uniform(0.1, 0.17))
        if era.get("jets"):
            for j, off in enumerate((-0.6, 0.6)):
                t0 = w.arrive + 6 + j * 12
                ob = self.spawn("jet", "Armies", w.point, math.atan2(d.y, d.x), 0, w.A.color)
                key(ob, "location", t0 - 20, w.point - d * 16 + perp * off + UP * 3.2, "LINEAR")
                key(ob, "location", t0 + 20, w.point + d * 16 + perp * off + UP * 3.2, "LINEAR")
                visible_between(ob, t0 - 20, t0 + 20, 2.2)
                for b in range(3):
                    self.boom(w.point + d * rng.uniform(0.3, 1.2) + perp * rng.uniform(-0.6, 0.6),
                              t0 + 2 + b * 2, 0.55)

    # -- main -----------------------------------------------------------------
    def run(self):
        self.make_island()
        self.make_kingdoms()
        self.build_terrain()
        self.build_lights()
        self.build_camera()
        for k in self.kingdoms:
            t = self.tiles[k.seats[0]]
            ob = self.spawn("flag", "Buildings", (t.x + 0.42, t.y + 0.42, t.z), 0, 0, k.color)
            pop_in(ob, T(10) + 6, 1.0)
            self.flags[k.seats[0]] = dict(ob=ob, color=k.color, events=[])
        prev = {key_: None for key_ in self.tiles}
        for e, era in enumerate(ERAS):
            start = 1 + e * ERA_FRAMES
            last = e == len(ERAS) - 1
            print(f"[map_evolution] building era {e + 1}/{len(ERAS)}: {era['name']}")
            before = self.territory(era["reach"])
            seats = {k.id: list(k.seats) for k in self.kingdoms}
            colonize = {}
            for key_, kid in before.items():
                if kid != prev[key_]:
                    tf = start + T(10) + int(3 * self.seat_dist(key_, seats[kid]))
                    colonize[key_] = min(tf, start + T(60))
                    self.tiles[key_].events.append((colonize[key_], kid))
            wars = self.plan_wars(era, before, start)
            after = self.territory(era["reach"])
            flips = self.flip_times(before, after, wars, start)
            for key_, (tf, _) in flips.items():
                self.tiles[key_].events.append((tf, after[key_]))
            self.place_buildings(e, era, before, seats, colonize, flips, start, last)
            if era.get("walls"):
                self.place_walls(before, flips, start, last)
            for w in wars:
                self.stage_battle(era, w, start)
                if w.eliminate:
                    for s in w.d_seats:
                        if s in self.flags:
                            tf = flips.get(s, (w.end + 10, None))[0]
                            self.flags[s]["events"].append((tf, w.A.color))
            self.cam_key(start + T(70), Vector(), 1.0)
            for w in wars:
                self.cam_key(w.arrive - 2, w.point, BATTLE_ZOOM)
                self.cam_key(w.end + 2, w.point, BATTLE_ZOOM)
            self.cam_key(start + T(226), Vector(), 1.0)
            self.title(era, start)
            if e > 0:
                self.cloud_keys += [(start - 16, -8.0), (start - 2, 0.0), (start + 2, 0.0),
                                    (start + 16, 8.0), (start + 17, -8.0)]
            prev = after
        self.finish()

    def finish(self):
        for t in self.tiles.values():
            cur, last = self.tile_color(t, None), -99
            for f, kid in sorted(t.events, key=lambda ev: ev[0]):
                f = max(f, last + 8)
                new = self.tile_color(t, kid)
                key(t.ob, "color", f, cur, "LINEAR")
                key(t.ob, "color", f + 6, new, "LINEAR")
                cur, last = new, f + 6
            if t.cut is not None:
                for tree in t.trees:
                    pop_out(tree, t.cut, tuple(tree.scale))
        for flag in self.flags.values():
            cur = flag["color"]
            for f, col in sorted(flag["events"], key=lambda ev: ev[0]):
                key(flag["ob"], "color", f, cur, "CONSTANT")
                key(flag["ob"], "color", f + 1, col, "CONSTANT")
                cur = col
        for f, x in sorted(self.cloud_keys):
            key(self.clouds, "location", f, (x, 0, -5))
        text = bpy.data.texts.new(PREFIX + "Chronicle")
        text.write("\n".join(self.chronicle) + "\n")
        survivors = ", ".join(k.name for k in self.kingdoms if k.alive)
        text.write(f"\nStill standing in the present day: {survivors}\n")
        print("[map_evolution] chronicle:\n" + text.as_string())


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def setup_render(scene, args, frame_end):
    r = scene.render
    r.fps = FPS
    scene.frame_start, scene.frame_end = 1, frame_end
    r.resolution_x, r.resolution_y = 1920, 1080
    r.resolution_percentage = args.resolution
    r.filepath = "//map_evolution/frame_"
    engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    if args.cycles:
        r.engine = "CYCLES"
        scene.cycles.samples = args.samples or 64
        scene.cycles.use_denoising = True
    else:
        r.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
        settings = dict(taa_render_samples=args.samples or 64, use_gtao=True,
                        use_soft_shadows=True, use_bloom=True, bloom_intensity=0.03,
                        use_shadows=True, shadow_cascade_size="2048")
        for attr, value in settings.items():
            try:
                setattr(scene.eevee, attr, value)
            except (AttributeError, TypeError):
                pass
    vs = scene.view_settings
    for transform in ("AgX", "Filmic"):
        try:
            vs.view_transform = transform
            break
        except TypeError:
            pass
    for look in ("AgX - Punchy", "Punchy", "Filmic - Medium High Contrast",
                 "Medium High Contrast"):
        try:
            vs.look = look
            break
        except TypeError:
            pass


def era_frames():
    """Two representative frames per era: the overview and the battle."""
    return [(1 + e * ERA_FRAMES + T(72), 1 + e * ERA_FRAMES + T(118)) for e in range(len(ERAS))]


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser(prog="map_evolution.py")
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--cycles", action="store_true", help="render with Cycles instead of EEVEE")
    p.add_argument("--samples", type=int, default=0)
    p.add_argument("--resolution", type=int, default=100, help="percent of 1920x1080")
    p.add_argument("--stills", metavar="DIR", help="render an overview + battle still per era")
    p.add_argument("--animation", action="store_true", help="render the full animation")
    p.add_argument("--save", metavar="FILE", help="save the result as a .blend file")
    return p.parse_args(argv)


def main():
    args = parse_args()
    scene = fresh_scene()
    build_materials()
    story = Story(scene, args.seed)
    story.run()
    setup_render(scene, args, story.frame_end)
    scene.frame_set(1)
    if args.save:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.save))
    if args.stills:
        os.makedirs(args.stills, exist_ok=True)
        for e, frames in enumerate(era_frames()):
            for label, frame in zip(("overview", "battle"), frames):
                scene.frame_set(frame)
                scene.render.filepath = os.path.abspath(
                    os.path.join(args.stills, f"era{e + 1}_{label}.png"))
                bpy.ops.render.render(write_still=True, scene=scene.name)
    if args.animation:
        bpy.ops.render.render(animation=True, scene=scene.name)
    print(f"[map_evolution] done: scene '{SCENE_NAME}', frames 1-{story.frame_end}")


if __name__ == "__main__":
    main()
