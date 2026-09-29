"""
Shared helpers for "Miami: Walking Through Time".

Target: Blender 4.2 LTS or newer. API differences in 4.4+ and 5.x
(layered actions, renamed engines, sky model names) are handled with guards.

Everything is plain bpy, so each part script runs from the Scripting
workspace or headless:
    blender -b your_file.blend -P build_part01_tequesta_spanish.py
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

try:
    from mathutils import noise as _mnoise
except ImportError:  # pragma: no cover
    _mnoise = None

FPS = 30
RES_X, RES_Y = 1920, 1080
FILM_END = 12480  # 6:56 at 30 fps; frame 1 is 0:00
SCENE_3D = "MIAMI_3D"
SCENE_EDIT = "MIAMI_EDIT"
EYE_HEIGHT = 1.62
SEATED_EYE = 0.95


def tc(t):
    """Timecode 'm:ss' (or seconds) to a frame number. Frame 1 is 0:00."""
    if isinstance(t, str):
        m, s = t.split(":")
        t = int(m) * 60 + float(s)
    return int(round(t * FPS)) + 1


def _try_set(owner, attr, value):
    if owner is not None and hasattr(owner, attr):
        try:
            setattr(owner, attr, value)
            return True
        except (TypeError, ValueError, AttributeError):
            return False
    return False


def _set_enum(owner, attr, candidates):
    for c in candidates:
        if _try_set(owner, attr, c):
            return c
    return None


# ---------------------------------------------------------------------------
# Scenes, collections, objects
# ---------------------------------------------------------------------------

def get_scene(name):
    sc = bpy.data.scenes.get(name)
    if sc is None:
        sc = bpy.data.scenes.new(name)
    return sc


def setup_render(scene, frame_start, frame_end, engine="EEVEE"):
    r = scene.render
    r.resolution_x, r.resolution_y = RES_X, RES_Y
    r.resolution_percentage = 100
    r.fps = FPS
    scene.frame_start = frame_start
    scene.frame_end = frame_end
    if engine == "CYCLES":
        r.engine = "CYCLES"
    else:
        _set_enum(r, "engine", ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"))
    _try_set(r, "use_motion_blur", True)
    ee = getattr(scene, "eevee", None)
    _try_set(ee, "use_motion_blur", True)
    _try_set(ee, "volumetric_end", 900.0)
    _try_set(ee, "volumetric_tile_size", "8")
    _set_enum(scene.view_settings, "view_transform", ("AgX", "Filmic"))


def get_collection(name, parent_coll):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    if c.name not in parent_coll.children.keys():
        parent_coll.children.link(c)
    return c


def wipe_collection(c):
    for child in list(c.children):
        wipe_collection(child)
        bpy.data.collections.remove(child)
    for ob in list(c.objects):
        bpy.data.objects.remove(ob, do_unlink=True)


def purge_orphans(prefixes=("MT", "MTP_", "POV_")):
    for datablocks in (bpy.data.meshes, bpy.data.cameras, bpy.data.lights,
                       bpy.data.curves):
        for d in list(datablocks):
            if d.users == 0 and d.name.startswith(prefixes):
                datablocks.remove(d)


def new_object(name, data, coll, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), parent=None):
    ob = bpy.data.objects.new(name, data)
    coll.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    ob.location = loc
    ob.rotation_euler = rot
    ob.scale = scale
    return ob


def new_empty(name, coll, loc=(0, 0, 0), parent=None, size=0.25, shape="PLAIN_AXES"):
    ob = new_object(name, None, coll, loc, parent=parent)
    ob.empty_display_type = shape
    ob.empty_display_size = size
    return ob


def descendants(ob):
    out = [ob]
    for ch in ob.children:
        out.extend(descendants(ch))
    return out


# ---------------------------------------------------------------------------
# Animation utilities (handles pre-4.4 actions and 4.4+/5.x slotted actions)
# ---------------------------------------------------------------------------

def fcurves_of(idblock):
    ad = getattr(idblock, "animation_data", None)
    if ad is None or ad.action is None:
        return []
    act = ad.action
    try:
        return list(act.fcurves)
    except AttributeError:
        pass
    try:
        from bpy_extras import anim_utils
        cb = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
        return list(cb.fcurves) if cb else []
    except Exception:
        return []


def set_interpolation(idblock, interp, paths=None, frame_range=None):
    for fc in fcurves_of(idblock):
        if paths is not None and not any(p in fc.data_path for p in paths):
            continue
        for kp in fc.keyframe_points:
            if frame_range is None or frame_range[0] <= kp.co[0] <= frame_range[1]:
                kp.interpolation = interp


def clear_keys(idblock, f0, f1):
    """Remove keyframes and restricted-range F-modifiers inside [f0, f1]."""
    for fc in fcurves_of(idblock):
        for kp in reversed(list(fc.keyframe_points)):
            if f0 <= kp.co[0] <= f1:
                fc.keyframe_points.remove(kp)
        for m in list(fc.modifiers):
            if m.use_restricted_range and f0 <= m.frame_start <= f1:
                fc.modifiers.remove(m)


def key(owner, attr, frame, value=None, index=-1):
    if value is not None:
        if index >= 0:
            getattr(owner, attr)[index] = value
        else:
            setattr(owner, attr, value)
    owner.keyframe_insert(data_path=attr, frame=frame, index=index)


def key_socket(socket, frame, value):
    socket.default_value = value
    socket.keyframe_insert("default_value", frame=frame)


def show_range(obs, f_in=None, f_out=None):
    """Make objects visible from f_in (inclusive) until f_out (exclusive)."""
    if not isinstance(obs, (list, tuple)):
        obs = [obs]
    for ob in obs:
        for o in descendants(ob):
            def k(frame, hidden):
                for attr in ("hide_render", "hide_viewport"):
                    setattr(o, attr, hidden)
                    try:
                        o.keyframe_insert(attr, frame=frame)
                    except (TypeError, RuntimeError):
                        pass
            start = f_in or 1
            if start > 1:
                k(start - 1, True)
            k(start, False)
            if f_out is not None:
                k(f_out, True)
            set_interpolation(o, "CONSTANT", paths=("hide_render", "hide_viewport"))


def _ensure_fcurve(ob, path, index):
    is_array = hasattr(getattr(ob, path), "__len__")
    want = index if is_array else 0
    for fc in fcurves_of(ob):
        if fc.data_path == path and fc.array_index == want:
            return fc
    if is_array:
        ob.keyframe_insert(path, index=index, frame=1)
    else:
        ob.keyframe_insert(path, frame=1)
    for fc in fcurves_of(ob):
        if fc.data_path == path and fc.array_index == want:
            return fc
    raise RuntimeError(f"could not create F-curve {path}[{index}] on {ob.name}")


def _range(m, f0, f1, blend_in, blend_out):
    m.use_restricted_range = True
    m.frame_start = f0
    m.frame_end = f1
    span = max(1, f1 - f0)
    m.blend_in = min(blend_in, span * 0.5)
    m.blend_out = min(blend_out, span - m.blend_in)


def add_sine(ob, path, index, amp, period_frames, f0, f1, blend=8, phase=0.0):
    """Additive sine wave on one channel, only between f0 and f1."""
    fc = _ensure_fcurve(ob, path, index)
    m = fc.modifiers.new("FNGENERATOR")
    m.function_type = "SIN"
    m.amplitude = amp
    m.phase_multiplier = 2 * math.pi / max(1e-3, period_frames)
    m.phase_offset = phase
    m.value_offset = 0.0
    m.use_additive = True
    _range(m, f0, f1, blend, blend)
    return m


def add_noise(ob, path, index, strength, scale_frames, f0, f1, blend_in=1, blend_out=None, phase=1.0):
    """Additive noise on one channel, only between f0 and f1."""
    fc = _ensure_fcurve(ob, path, index)
    m = fc.modifiers.new("NOISE")
    m.blend_type = "ADD"
    m.strength = strength
    m.scale = scale_frames
    m.phase = phase
    _try_set(m, "depth", 1)
    _range(m, f0, f1, blend_in, blend_out if blend_out is not None else (f1 - f0) * 0.85)
    return m


# ---------------------------------------------------------------------------
# Geography of the river mouth (+X is east / Biscayne Bay, +Y is north)
# ---------------------------------------------------------------------------

RIVER_HALF_WIDTH = 35.0


def river_center_y(x):
    return 6.0 * math.sin(x / 60.0)


def shore_x(y):
    return 45.0 + 10.0 * math.sin(y / 40.0)


def shore_distance(x, y):
    """Rough signed distance to water: > 0 on land, < 0 in water."""
    sx = shore_x(y)
    d_bay = sx - x
    if x > sx:
        return d_bay
    d_river = abs(y - river_center_y(x)) - RIVER_HALF_WIDTH
    return min(d_bay, d_river)


def _noise2(x, y):
    if _mnoise is not None:
        return _mnoise.noise(Vector((x, y, 0.37)))
    return 0.5 * math.sin(x * 1.7) * math.cos(y * 1.3)


def ground_height(x, y):
    d = shore_distance(x, y)
    h = max(-2.5, min(1.2, d * 0.18))
    if d > 0:
        h += 0.25 * _noise2(x * 0.03, y * 0.03) * min(1.0, d / 12.0)
    return h


def is_land(x, y, margin=0.0):
    return shore_distance(x, y) > margin


# ---------------------------------------------------------------------------
# Materials (all named MT_*, so BlenderKit materials can be dropped on later)
# ---------------------------------------------------------------------------

def _fresh_material(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.animation_data_clear()
    m.node_tree.nodes.clear()
    return m


def _node(nt, type_, loc=(0, 0)):
    n = nt.nodes.new(type_)
    n.location = loc
    return n


def _set_input(node, names, value):
    for n in names:
        if n in node.inputs:
            node.inputs[n].default_value = value
            return True
    return False


def _principled(nt, loc=(300, 0)):
    return _node(nt, "ShaderNodeBsdfPrincipled", loc)


def mat_basic(name, color, rough=0.7, metal=0.0, emission=None, emission_strength=0.0):
    m = _fresh_material(name)
    nt = m.node_tree
    out = _node(nt, "ShaderNodeOutputMaterial", (600, 0))
    b = _principled(nt)
    _set_input(b, ["Base Color"], (*color, 1.0))
    _set_input(b, ["Roughness"], rough)
    _set_input(b, ["Metallic"], metal)
    if emission is not None:
        _set_input(b, ["Emission Color", "Emission"], (*emission, 1.0))
        _set_input(b, ["Emission Strength"], emission_strength)
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    m.diffuse_color = (*color, 1.0)
    return m


def mat_varied(name, c1, c2, scale=4.0, rough=0.8, bump=0.2, bands=None):
    """Two-colour noise material; `bands` adds wave stripes (for thatch)."""
    m = _fresh_material(name)
    nt = m.node_tree
    out = _node(nt, "ShaderNodeOutputMaterial", (700, 0))
    b = _principled(nt, (400, 0))
    coord = _node(nt, "ShaderNodeTexCoord", (-900, 0))
    noise = _node(nt, "ShaderNodeTexNoise", (-650, 0))
    _set_input(noise, ["Scale"], scale)
    _set_input(noise, ["Detail"], 6.0)
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    fac = noise.outputs["Fac"]
    if bands:
        wave = _node(nt, "ShaderNodeTexWave", (-650, -250))
        _set_input(wave, ["Scale"], bands)
        _set_input(wave, ["Distortion"], 4.0)
        nt.links.new(coord.outputs["Object"], wave.inputs["Vector"])
        mix = _node(nt, "ShaderNodeMath", (-400, -100))
        mix.operation = "MULTIPLY"
        nt.links.new(noise.outputs["Fac"], mix.inputs[0])
        nt.links.new(wave.outputs["Fac"], mix.inputs[1])
        fac = mix.outputs[0]
    ramp = _node(nt, "ShaderNodeValToRGB", (-200, 0))
    ramp.color_ramp.elements[0].color = (*c1, 1.0)
    ramp.color_ramp.elements[1].color = (*c2, 1.0)
    nt.links.new(fac, ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bm = _node(nt, "ShaderNodeBump", (100, -300))
    _set_input(bm, ["Strength"], bump)
    nt.links.new(fac, bm.inputs["Height"])
    nt.links.new(bm.outputs["Normal"], b.inputs["Normal"])
    _set_input(b, ["Roughness"], rough)
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    m.diffuse_color = (*c1, 1.0)
    return m


def mat_terrain(name="MT_Terrain"):
    """Wet sand at the waterline, dry sand, then scrubby grass inland."""
    m = _fresh_material(name)
    nt = m.node_tree
    out = _node(nt, "ShaderNodeOutputMaterial", (800, 0))
    b = _principled(nt, (500, 0))
    geo = _node(nt, "ShaderNodeNewGeometry", (-900, 100))
    sep = _node(nt, "ShaderNodeSeparateXYZ", (-700, 100))
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    mr = _node(nt, "ShaderNodeMapRange", (-500, 100))
    _set_input(mr, ["From Min"], -0.6)
    _set_input(mr, ["From Max"], 1.3)
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    noise = _node(nt, "ShaderNodeTexNoise", (-700, -200))
    _set_input(noise, ["Scale"], 0.6)
    _set_input(noise, ["Detail"], 8.0)
    madd = _node(nt, "ShaderNodeMath", (-300, 0))
    madd.operation = "MULTIPLY_ADD"
    nt.links.new(noise.outputs["Fac"], madd.inputs[0])
    madd.inputs[1].default_value = 0.25
    nt.links.new(mr.outputs["Result"], madd.inputs[2])
    ramp = _node(nt, "ShaderNodeValToRGB", (0, 0))
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.20, (0.28, 0.24, 0.17, 1)   # wet sand
    els[1].position, els[1].color = 0.85, (0.30, 0.34, 0.14, 1)   # scrub grass
    e = els.new(0.45)
    e.color = (0.72, 0.64, 0.48, 1)                               # dry sand
    e = els.new(0.70)
    e.color = (0.55, 0.50, 0.33, 1)                               # sandy soil
    nt.links.new(madd.outputs[0], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    bump = _node(nt, "ShaderNodeBump", (200, -300))
    _set_input(bump, ["Strength"], 0.3)
    detail = _node(nt, "ShaderNodeTexNoise", (-100, -400))
    _set_input(detail, ["Scale"], 40.0)
    nt.links.new(detail.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    _set_input(b, ["Roughness"], 0.9)
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    m.diffuse_color = (0.6, 0.55, 0.4, 1)
    return m


def mat_water(name="MT_Water", frame_end=FILM_END):
    m = _fresh_material(name)
    nt = m.node_tree
    out = _node(nt, "ShaderNodeOutputMaterial", (800, 0))
    b = _principled(nt, (500, 0))
    _set_input(b, ["Base Color"], (0.02, 0.10, 0.10, 1))
    _set_input(b, ["Roughness"], 0.04)
    _set_input(b, ["IOR"], 1.333)
    coord = _node(nt, "ShaderNodeTexCoord", (-900, 0))
    mapping = _node(nt, "ShaderNodeMapping", (-700, 0))
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    noise = _node(nt, "ShaderNodeTexNoise", (-450, 0))
    _set_input(noise, ["Scale"], 0.35)
    _set_input(noise, ["Detail"], 10.0)
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    bump = _node(nt, "ShaderNodeBump", (200, -200))
    _set_input(bump, ["Strength"], 0.35)
    _set_input(bump, ["Distance"], 0.15)
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    # ripples drift slowly for the whole film
    loc = mapping.inputs["Location"]
    loc.default_value = (0, 0, 0)
    loc.keyframe_insert("default_value", frame=1)
    loc.default_value = (frame_end * 0.004, frame_end * 0.002, frame_end * 0.01)
    loc.keyframe_insert("default_value", frame=frame_end)
    set_interpolation(nt, "LINEAR")
    m.diffuse_color = (0.02, 0.1, 0.1, 1)
    return m


def mat_smoke(name="MT_Smoke", height=9.0, frame_end=FILM_END, density=1.2):
    m = _fresh_material(name)
    nt = m.node_tree
    out = _node(nt, "ShaderNodeOutputMaterial", (900, 0))
    vol = _node(nt, "ShaderNodeVolumePrincipled", (600, 0))
    _set_input(vol, ["Color"], (0.55, 0.55, 0.55, 1))
    coord = _node(nt, "ShaderNodeTexCoord", (-900, 0))
    mapping = _node(nt, "ShaderNodeMapping", (-700, 0))
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    noise = _node(nt, "ShaderNodeTexNoise", (-450, 0))
    _set_input(noise, ["Scale"], 0.9)
    _set_input(noise, ["Detail"], 4.0)
    nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    ramp = _node(nt, "ShaderNodeValToRGB", (-200, 0))
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position = 0.75
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    sep = _node(nt, "ShaderNodeSeparateXYZ", (-450, -300))
    nt.links.new(coord.outputs["Object"], sep.inputs[0])
    fade = _node(nt, "ShaderNodeMapRange", (-200, -300))
    _set_input(fade, ["From Min"], 0.0)
    _set_input(fade, ["From Max"], height)
    _set_input(fade, ["To Min"], 1.0)
    _set_input(fade, ["To Max"], 0.0)
    nt.links.new(sep.outputs["Z"], fade.inputs["Value"])
    mul = _node(nt, "ShaderNodeMath", (100, 0))
    mul.operation = "MULTIPLY"
    nt.links.new(ramp.outputs["Color"], mul.inputs[0])
    nt.links.new(fade.outputs["Result"], mul.inputs[1])
    mul2 = _node(nt, "ShaderNodeMath", (350, 0))
    mul2.operation = "MULTIPLY"
    mul2.inputs[1].default_value = density
    nt.links.new(mul.outputs[0], mul2.inputs[0])
    nt.links.new(mul2.outputs[0], vol.inputs["Density"])
    nt.links.new(vol.outputs[0], out.inputs["Volume"])
    loc = mapping.inputs["Location"]
    loc.default_value = (0, 0, 0)
    loc.keyframe_insert("default_value", frame=1)
    loc.default_value = (frame_end * 0.002, 0, -frame_end * 0.03)
    loc.keyframe_insert("default_value", frame=frame_end)
    set_interpolation(nt, "LINEAR")
    return m


class Palette:
    """Materials shared by all parts. Names start with MT_ so they are easy to swap."""

    def __init__(self):
        self.terrain = mat_terrain()
        self.water = mat_water()
        self.smoke = mat_smoke()
        self.bark = mat_varied("MT_Bark", (0.20, 0.15, 0.11), (0.33, 0.27, 0.21), scale=18, bump=0.5)
        self.palm_trunk = mat_varied("MT_PalmTrunk", (0.30, 0.26, 0.21), (0.42, 0.37, 0.30), scale=25, bump=0.6)
        self.frond = mat_varied("MT_Frond", (0.12, 0.22, 0.07), (0.25, 0.33, 0.11), scale=6, rough=0.6)
        self.mangrove_leaf = mat_varied("MT_MangroveLeaf", (0.06, 0.15, 0.05), (0.14, 0.24, 0.08), scale=5, rough=0.55)
        self.pine_needle = mat_varied("MT_PineNeedle", (0.10, 0.17, 0.07), (0.20, 0.26, 0.10), scale=9)
        self.thatch = mat_varied("MT_PalmettoThatch", (0.33, 0.27, 0.15), (0.55, 0.47, 0.28), scale=3, bands=14, bump=0.6)
        self.mat_weave = mat_varied("MT_WovenMat", (0.40, 0.33, 0.20), (0.58, 0.50, 0.32), scale=30, bands=40, bump=0.3)
        self.log_wood = mat_varied("MT_LogWood", (0.25, 0.19, 0.13), (0.40, 0.31, 0.21), scale=14, bump=0.5)
        self.charred = mat_varied("MT_CharredWood", (0.06, 0.05, 0.04), (0.20, 0.14, 0.09), scale=20, bump=0.4)
        self.shell = mat_varied("MT_Shell", (0.86, 0.78, 0.70), (0.95, 0.82, 0.78), scale=12, rough=0.35)
        self.stone = mat_varied("MT_Limestone", (0.55, 0.52, 0.45), (0.72, 0.68, 0.60), scale=8, bump=0.6)
        self.ember = mat_basic("MT_Ember", (0.3, 0.05, 0.0), emission=(1.0, 0.35, 0.05), emission_strength=6.0)
        self.fish = mat_basic("MT_DriedFish", (0.45, 0.38, 0.28), rough=0.5)
        self.canvas = mat_varied("MT_Canvas", (0.78, 0.74, 0.64), (0.88, 0.85, 0.76), scale=20, rough=0.9)
        self.ship_wood = mat_varied("MT_ShipWood", (0.16, 0.10, 0.06), (0.28, 0.18, 0.11), scale=10, bump=0.3)
        self.iron = mat_basic("MT_Iron", (0.10, 0.10, 0.10), rough=0.5, metal=1.0)
        self.steel = mat_basic("MT_Steel", (0.55, 0.56, 0.58), rough=0.3, metal=1.0)
        self.slate = mat_basic("MT_Slate", (0.08, 0.09, 0.10), rough=0.6)
        self.pov_skin = mat_basic("MT_POV_Skin", (0.45, 0.30, 0.22), rough=0.5)


# ---------------------------------------------------------------------------
# bmesh building blocks
# ---------------------------------------------------------------------------

def _faces_of(verts):
    return {f for v in verts for f in v.link_faces}


def bm_cyl(bm, p0, p1, r0, r1=None, seg=8, mat=0):
    r1 = r0 if r1 is None else r1
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    ret = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                                radius1=r0, radius2=r1, depth=max(1e-4, d.length))
    rot = d.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4() if d.length > 1e-6 else Matrix()
    bmesh.ops.transform(bm, matrix=Matrix.Translation((p0 + p1) * 0.5) @ rot, verts=ret["verts"])
    for f in _faces_of(ret["verts"]):
        f.material_index = mat
    return ret["verts"]


def bm_ellipsoid(bm, center, radii, subdiv=2, mat=0):
    ret = bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    m = Matrix.Translation(center) @ Matrix.Diagonal(Vector((*radii, 1.0)))
    bmesh.ops.transform(bm, matrix=m, verts=ret["verts"])
    for f in _faces_of(ret["verts"]):
        f.material_index = mat
    return ret["verts"]


def bm_box(bm, center, size, rot=None, mat=0):
    ret = bmesh.ops.create_cube(bm, size=1.0)
    m = Matrix.Translation(center)
    if rot is not None:
        m = m @ rot.to_4x4()
    m = m @ Matrix.Diagonal(Vector((*size, 1.0)))
    bmesh.ops.transform(bm, matrix=m, verts=ret["verts"])
    for f in _faces_of(ret["verts"]):
        f.material_index = mat
    return ret["verts"]


def mesh_from_bm(name, bm, mats, smooth=False):
    me = bpy.data.meshes.get(name)
    if me is None:
        me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.clear()
    for m in mats:
        me.materials.append(m)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    me.update()
    return me


def bm_hull(bm, length, width, depth, open_top=True, stations=18, arc=10, wall=0.05, mat=0):
    """Canoe/boat hull along +X, rim at z=0, keel at z=-depth."""
    loops = []
    for i in range(stations + 1):
        u = i / stations
        x = (u - 0.5) * length
        w = max(0.04, width * 0.5 * math.sin(math.pi * u) ** 0.45)
        d = max(0.04, depth * math.sin(math.pi * u) ** 0.25)
        ring = []
        for j in range(arc + 1):
            t = math.pi + math.pi * j / arc
            ring.append(bm.verts.new((x, w * math.cos(t), d * math.sin(t))))
        if open_top:
            wi, di = max(0.02, w - wall), max(0.02, d - wall)
            for j in range(arc, -1, -1):
                t = math.pi + math.pi * j / arc
                ring.append(bm.verts.new((x, wi * math.cos(t), di * math.sin(t))))
        loops.append(ring)
    n = len(loops[0])
    for a, b in zip(loops[:-1], loops[1:]):
        rng_ = range(n) if open_top else range(n - 1)
        for j in rng_:
            k = (j + 1) % n
            f = bm.faces.new((a[j], a[k], b[k], b[j]))
            f.material_index = mat
    for ring in (loops[0], loops[-1]):
        f = bm.faces.new(ring if ring is loops[-1] else list(reversed(ring)))
        f.material_index = mat
    if not open_top:
        # deck
        top = [loops[i][0] for i in range(len(loops))] + [loops[i][-1] for i in reversed(range(len(loops)))]
        f = bm.faces.new(top)
        f.material_index = mat
    return loops


# ---------------------------------------------------------------------------
# Terrain, water, sky
# ---------------------------------------------------------------------------

def build_terrain(coll, pal, x0=-320, x1=520, y0=-320, y1=320, step=2.5):
    nx = int((x1 - x0) / step) + 1
    ny = int((y1 - y0) / step) + 1
    verts = []
    for j in range(ny):
        y = y0 + j * step
        for i in range(nx):
            x = x0 + i * step
            verts.append((x, y, ground_height(x, y)))
    faces = [(j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i)
             for j in range(ny - 1) for i in range(nx - 1)]
    me = bpy.data.meshes.get("MT_Terrain") or bpy.data.meshes.new("MT_Terrain")
    me.clear_geometry()
    me.from_pydata(verts, [], faces)
    for p in me.polygons:
        p.use_smooth = True
    me.materials.clear()
    me.materials.append(pal.terrain)
    me.update()
    return new_object("MT_Terrain", me, coll)


def build_water(coll, pal, size=6000):
    s = size * 0.5
    me = bpy.data.meshes.get("MT_Water") or bpy.data.meshes.new("MT_Water")
    me.clear_geometry()
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    me.materials.clear()
    me.materials.append(pal.water)
    me.update()
    return new_object("MT_Water", me, coll)


SKY_AZIMUTH_OFFSET_DEG = 0.0  # adjust if the sky's sun disc and the sun lamp disagree


def build_world():
    w = bpy.data.worlds.get("MT_World") or bpy.data.worlds.new("MT_World")
    w.use_nodes = True
    nt = w.node_tree
    nt.animation_data_clear()
    nt.nodes.clear()
    out = _node(nt, "ShaderNodeOutputWorld", (600, 0))
    bg = _node(nt, "ShaderNodeBackground", (300, 0))
    sky = _node(nt, "ShaderNodeTexSky", (0, 0))
    sky.name = "MT_Sky"
    _set_enum(sky, "sky_type", ("NISHITA", "MULTIPLE_SCATTERING", "SINGLE_SCATTERING", "HOSEK_WILKIE"))
    _try_set(sky, "sun_disc", True)
    _try_set(sky, "sun_size", math.radians(0.8))
    nt.links.new(sky.outputs[0], bg.inputs["Color"])
    nt.links.new(bg.outputs[0], out.inputs["Surface"])
    bg.name = "MT_Background"
    return w


def build_mist(coll, center=(60.0, 0.0), size=(1400.0, 1000.0, 70.0)):
    """Ground mist / haze as a bounded volume box.

    A world volume would fill infinite space, and in Cycles that absorbs the
    whole sky and sun, so the mist lives in a box instead (works in EEVEE too).
    """
    m = _fresh_material("MT_MistVolume")
    nt = m.node_tree
    out = _node(nt, "ShaderNodeOutputMaterial", (300, 0))
    vol = _node(nt, "ShaderNodeVolumePrincipled", (0, 0))
    vol.name = "MT_Mist"
    _set_input(vol, ["Density"], 0.0)
    _set_input(vol, ["Color"], (0.86, 0.89, 0.93, 1))
    _set_input(vol, ["Anisotropy"], 0.35)
    nt.links.new(vol.outputs[0], out.inputs["Volume"])
    sx, sy, sz = size
    me = bpy.data.meshes.get("MT_Mist") or bpy.data.meshes.new("MT_Mist")
    me.clear_geometry()
    bm = bmesh.new()
    bm_box(bm, (0, 0, 0), (sx, sy, sz))
    bm.to_mesh(me)
    bm.free()
    me.materials.clear()
    me.materials.append(m)
    ob = new_object("MT_Mist", me, coll, loc=(center[0], center[1], sz / 2 - 3.0))
    ob.display_type = "BOUNDS"
    return ob


def build_sun(coll):
    ld = bpy.data.lights.get("MT_Sun") or bpy.data.lights.new("MT_Sun", "SUN")
    ld.animation_data_clear()
    ld.angle = math.radians(0.8)
    return new_object("MT_Sun", ld, coll)


def _sun_dir(elev_deg, azim_deg):
    e, a = math.radians(elev_deg), math.radians(azim_deg)
    return Vector((math.cos(e) * math.sin(a), math.cos(e) * math.cos(a), math.sin(e)))


def sky_key(world, sun, frame, elev, azim, air=1.0, dust=1.0, ozone=1.0, strength=1.0, mist=0.0, sun_energy=None):
    """Key the sky, the sun lamp and the world mist together.

    elev: sun elevation in degrees (negative is night); azim: compass bearing
    in degrees (0 north, 90 east). Colour/strength of the lamp follows elevation.
    """
    nt = world.node_tree
    sky = nt.nodes["MT_Sky"]
    for attr, val in (("sun_elevation", math.radians(elev)),
                      ("sun_rotation", math.radians(azim + SKY_AZIMUTH_OFFSET_DEG)),
                      ("air_density", air), ("dust_density", dust),
                      ("aerosol_density", dust), ("ozone_density", ozone)):
        if hasattr(sky, attr):
            setattr(sky, attr, val)
            sky.keyframe_insert(attr, frame=frame)
    key_socket(nt.nodes["MT_Background"].inputs["Strength"], frame, strength)
    mist_mat = bpy.data.materials.get("MT_MistVolume")
    if mist_mat is not None and "MT_Mist" in mist_mat.node_tree.nodes:
        key_socket(mist_mat.node_tree.nodes["MT_Mist"].inputs["Density"], frame, mist)

    d = _sun_dir(elev, azim)
    sun.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    sun.keyframe_insert("rotation_euler", frame=frame)
    t = max(0.0, min(1.0, elev / 40.0))
    warm, noon = Vector((1.0, 0.55, 0.32)), Vector((1.0, 0.96, 0.90))
    sun.data.color = warm.lerp(noon, t)
    sun.data.keyframe_insert("color", frame=frame)
    if sun_energy is None:
        sun_energy = 0.0 if elev <= -2 else 2.6 * max(0.05, min(1.0, (elev + 2) / 30.0))
    sun.data.energy = sun_energy
    sun.data.keyframe_insert("energy", frame=frame)


# ---------------------------------------------------------------------------
# Colour grade (compositor). Skipped quietly where the compositor API differs.
# ---------------------------------------------------------------------------

def build_grade(scene):
    try:
        scene.use_nodes = True
        nt = scene.node_tree
    except AttributeError:
        print("[mt] compositor API not available here; skipping colour grade")
        return None
    if nt is None:
        return None
    nt.animation_data_clear()
    nt.nodes.clear()
    rl = _node(nt, "CompositorNodeRLayers", (-600, 0))
    cb = _node(nt, "CompositorNodeColorBalance", (-300, 0))
    cb.name = "MT_Grade"
    _try_set(cb, "correction_method", "LIFT_GAMMA_GAIN")
    hsv = _node(nt, "CompositorNodeHueSat", (0, 0))
    hsv.name = "MT_Sat"
    out = _node(nt, "CompositorNodeComposite", (300, 0))
    nt.links.new(rl.outputs["Image"], cb.inputs["Image"])
    nt.links.new(cb.outputs["Image"], hsv.inputs["Image"])
    nt.links.new(hsv.outputs["Image"], out.inputs["Image"])
    return nt


def grade_key(scene, frame, lift=(1, 1, 1), gamma=(1, 1, 1), gain=(1, 1, 1), saturation=1.0):
    nt = getattr(scene, "node_tree", None)
    if nt is None or "MT_Grade" not in nt.nodes:
        return
    cb = nt.nodes["MT_Grade"]
    for attr, val in (("lift", lift), ("gamma", gamma), ("gain", gain)):
        if hasattr(cb, attr):
            setattr(cb, attr, (*val, 1.0) if len(getattr(cb, attr)) == 4 else val)
            cb.keyframe_insert(attr, frame=frame)
    hsv = nt.nodes["MT_Sat"]
    if "Saturation" in hsv.inputs:
        key_socket(hsv.inputs["Saturation"], frame, saturation)


# ---------------------------------------------------------------------------
# First-person camera rig
# ---------------------------------------------------------------------------

class PovRig:
    """Rig > Look (Track To target) > Bob > Shake > Impact > Camera.

    - Rig: world position. Use `walk_to` / `hold`.
    - Look: aims the head at the POV_Target empty. Move the target to turn the head.
    - Bob / Shake / Impact: additive layers in head space (x right, y up, z back).
    """

    def __init__(self, scene, coll, lens=22.0):
        names = ("POV_Rig", "POV_Look", "POV_Bob", "POV_Shake", "POV_Impact", "POV_Target", "POV_Cam")
        for n in names:
            ob = bpy.data.objects.get(n)
            if ob is not None:
                bpy.data.objects.remove(ob, do_unlink=True)
        self.rig = new_empty("POV_Rig", coll, size=0.5, shape="ARROWS")
        self.look = new_empty("POV_Look", coll, parent=self.rig)
        self.bob = new_empty("POV_Bob", coll, parent=self.look)
        self.shake_ob = new_empty("POV_Shake", coll, parent=self.bob)
        self.impact_ob = new_empty("POV_Impact", coll, parent=self.shake_ob)
        self.target = new_empty("POV_Target", coll, size=0.4, shape="SPHERE")
        cam_data = bpy.data.cameras.get("POV_Cam") or bpy.data.cameras.new("POV_Cam")
        cam_data.animation_data_clear()
        cam_data.lens = lens
        cam_data.sensor_width = 36.0
        cam_data.clip_start = 0.03
        cam_data.clip_end = 8000.0
        self.cam = new_object("POV_Cam", cam_data, coll, parent=self.impact_ob)
        self.base_lens = lens
        c = self.look.constraints.new("TRACK_TO")
        c.target = self.target
        c.track_axis = "TRACK_NEGATIVE_Z"
        c.up_axis = "UP_Y"
        scene.camera = self.cam
        for ob in (self.bob, self.shake_ob, self.impact_ob):
            for i in range(3):
                ob.keyframe_insert("location", index=i, frame=1)
                ob.keyframe_insert("rotation_euler", index=i, frame=1)

    # -- position -----------------------------------------------------------
    def at(self, frame, x, y, z=None, eye=EYE_HEIGHT):
        if z is None:
            z = max(0.0, ground_height(x, y)) + eye
        self.rig.location = (x, y, z)
        self.rig.keyframe_insert("location", frame=frame)

    def path(self, points, eye=EYE_HEIGHT):
        """points: [(frame, x, y) or (frame, x, y, z)]"""
        for p in points:
            self.at(p[0], p[1], p[2], p[3] if len(p) > 3 else None, eye=eye)

    def look_at(self, frame, x, y, h):
        """Aim the head at (x, y), `h` metres above the ground (or water) there."""
        self.target.location = (x, y, max(0.0, ground_height(x, y)) + h)
        self.target.keyframe_insert("location", frame=frame)

    # -- layers -------------------------------------------------------------
    def walk_bob(self, f0, f1, speed=1.3, amp=0.022):
        """Footstep bob: vertical bounce per step, sway and roll per stride."""
        step_hz = 1.45 * speed / 1.3
        per_step = FPS / step_hz
        add_sine(self.bob, "location", 1, amp, per_step, f0, f1, blend=8)
        add_sine(self.bob, "location", 0, amp * 0.6, per_step * 2, f0, f1, blend=8, phase=math.pi / 2)
        add_sine(self.bob, "rotation_euler", 2, math.radians(0.45), per_step * 2, f0, f1, blend=8)
        add_sine(self.bob, "rotation_euler", 0, math.radians(0.25), per_step, f0, f1, blend=8, phase=math.pi)

    def float_sway(self, f0, f1, roll_deg=1.6, pitch_deg=0.8, period_s=3.6):
        """Gentle roll and pitch while sitting in a boat."""
        add_sine(self.bob, "rotation_euler", 2, math.radians(roll_deg), period_s * FPS, f0, f1, blend=12)
        add_sine(self.bob, "rotation_euler", 0, math.radians(pitch_deg), period_s * FPS * 0.7, f0, f1, blend=12, phase=1.1)
        add_sine(self.bob, "location", 1, 0.03, period_s * FPS * 0.8, f0, f1, blend=12, phase=0.4)

    def shake(self, frame, duration, intensity=1.0, speed=1.0, seed=1.0):
        """Noise shake that hits at `frame` and decays over `duration` frames.

        intensity: 0.3 distant rumble / footstep, 1 heavy thud, 3 nearby blast,
        5 the ground itself moving. speed: >1 is faster jitter.
        """
        f1 = frame + duration
        sc = 2.2 / max(0.1, speed)
        for i, amt in enumerate((0.010, 0.012, 0.004)):
            add_noise(self.shake_ob, "location", i, amt * intensity, sc, frame, f1, phase=seed + i * 7.1)
        for i, amt in enumerate((0.9, 0.6, 1.1)):
            add_noise(self.shake_ob, "rotation_euler", i, math.radians(amt) * intensity, sc, frame, f1,
                      phase=seed + 13.3 + i * 5.7)

    def rumble(self, f0, f1, intensity=0.25, speed=0.6):
        """Long, low shake with soft edges (storms, time-lapse transitions)."""
        sc = 2.2 / max(0.1, speed)
        blend = (f1 - f0) * 0.3
        for i, amt in enumerate((0.010, 0.012, 0.004)):
            add_noise(self.shake_ob, "location", i, amt * intensity, sc, f0, f1, blend_in=blend, blend_out=blend,
                      phase=31.0 + i)
        for i, amt in enumerate((0.9, 0.6, 1.1)):
            add_noise(self.shake_ob, "rotation_euler", i, math.radians(amt) * intensity, sc, f0, f1,
                      blend_in=blend, blend_out=blend, phase=47.0 + i)

    def impact(self, frame, dip=0.05, pitch_deg=2.0, recover=14):
        """A single physical jolt: the head drops and nods, then settles."""
        ob = self.impact_ob
        for f, k in ((frame - 1, 0.0), (frame + 2, -1.0), (frame + 6, 0.3), (frame + recover, 0.0)):
            ob.location[1] = dip * k
            ob.rotation_euler[0] = math.radians(pitch_deg) * k
            ob.keyframe_insert("location", index=1, frame=f)
            ob.keyframe_insert("rotation_euler", index=0, frame=f)

    def blast(self, frame, intensity=3.0, from_dir=(1, 0, 0), duration=45):
        """Explosion: impact kick + shake + a short FOV punch. For later parts."""
        self.impact(frame, dip=0.03 * intensity, pitch_deg=1.5 * intensity, recover=18)
        self.shake(frame, duration, intensity=intensity, speed=1.4)
        self.fov_pulse(frame, 10, delta=-2.0 * intensity)

    def fov_pulse(self, frame, duration, delta=-3.0):
        cd = self.cam.data
        for f, v in ((frame - 1, self.base_lens), (frame + duration // 2, self.base_lens + delta),
                     (frame + duration, self.base_lens)):
            cd.lens = v
            cd.keyframe_insert("lens", frame=f)

    def time_rush(self, f0, f1):
        """Signature transition between eras: soft rumble + a slow lens breathe."""
        self.rumble(f0, f1, intensity=0.18, speed=0.5)
        self.fov_pulse(f0, f1 - f0, delta=-3.0)

    def clear(self, f0, f1):
        for ob in (self.rig, self.target, self.bob, self.shake_ob, self.impact_ob):
            clear_keys(ob, f0, f1)
        clear_keys(self.cam.data, f0, f1)


def build_pov_arm(coll, rig, pal):
    """Placeholder right forearm in camera space. Replace with rigged FPS arms."""
    for n in ("POV_ArmR", "POV_ArmR_Mesh", "POV_HandR"):
        ob = bpy.data.objects.get(n)
        if ob is not None:
            bpy.data.objects.remove(ob, do_unlink=True)
    arm = new_empty("POV_ArmR", coll, parent=rig.cam)
    bm = bmesh.new()
    bm_cyl(bm, (0, 0, 0), (0, 0, -0.36), 0.045, 0.038, seg=10)
    bm_ellipsoid(bm, (0, -0.01, -0.40), (0.045, 0.028, 0.06))
    me = mesh_from_bm("POV_ArmR_Mesh", bm, [pal.pov_skin], smooth=True)
    new_object("POV_ArmR_Mesh", me, coll, parent=arm)
    hand = new_empty("POV_HandR", coll, loc=(0, 0.035, -0.41), parent=arm, size=0.05)
    arm_pose(arm, 1, "down")
    return arm, hand


ARM_POSES = {
    # camera space: x right, y up, -z forward
    "down": ((0.24, -0.95, -0.25), (math.radians(60), 0, math.radians(10))),
    "reach": ((0.20, -0.36, -0.20), (math.radians(62), math.radians(-12), math.radians(8))),
    "hold": ((0.22, -0.40, -0.14), (math.radians(55), math.radians(-18), math.radians(6))),
    "drink": ((0.06, -0.22, -0.02), (math.radians(92), math.radians(-40), math.radians(-20))),
    "show": ((0.12, -0.30, -0.10), (math.radians(70), math.radians(-30), 0)),
}


def arm_pose(arm, frame, pose):
    loc, rot = ARM_POSES[pose]
    arm.location = loc
    arm.rotation_euler = rot
    arm.keyframe_insert("location", frame=frame)
    arm.keyframe_insert("rotation_euler", frame=frame)


def handoff(obj, from_socket, to_socket, frame, blend=6, mode="COPY_LOCATION"):
    """obj follows from_socket, then blends onto to_socket at `frame`.

    COPY_LOCATION keeps the object's own (keyable) world rotation, so a cup
    stays upright while arms swing; use COPY_TRANSFORMS for rigid grips.
    """
    c1 = obj.constraints.get("HOLD_FROM") or obj.constraints.new(mode)
    c1.name = "HOLD_FROM"
    c1.target = from_socket
    c2 = obj.constraints.get("HOLD_TO") or obj.constraints.new(mode)
    c2.name = "HOLD_TO"
    c2.target = to_socket
    c2.influence = 0.0
    c2.keyframe_insert("influence", frame=frame)
    c2.influence = 1.0
    c2.keyframe_insert("influence", frame=frame + blend)


# ---------------------------------------------------------------------------
# Placeholder people (swap for Human Generator characters)
# ---------------------------------------------------------------------------

def facing_deg(frm, to):
    dx, dy = to[0] - frm[0], to[1] - frm[1]
    return math.degrees(math.atan2(-dx, dy))


def make_person(coll, name, pos, face, clothes, skin=(0.36, 0.22, 0.14), height=1.68,
                tag=None, notes="", extras=None, kneel=False, legwear=None):
    """A capsule stand-in: root at the feet, front is local +Y.

    Returns dict(root, arm_r, arm_l, hand_r, hand_l). Arms hang along -Z;
    rotating an arm's X axis positively swings it forward.
    """
    x, y = pos
    z = max(0.0, ground_height(x, y))
    if isinstance(face, (tuple, list)):
        face = facing_deg(pos, face)
    root = new_empty(name, coll, loc=(x, y, z), size=0.3, shape="SINGLE_ARROW")
    root.rotation_euler = (0, 0, math.radians(face))
    root["asset_tag"] = f"human_{tag or name}"
    root["notes"] = notes
    s = height / 1.68
    hip = 0.55 if kneel else 0.92
    shoulder = hip + 0.52
    mat_skin = mat_basic(f"MT_Skin_{tag or name}", skin, rough=0.5)
    mat_cloth = clothes if isinstance(clothes, bpy.types.Material) else mat_basic(f"MT_Cloth_{tag or name}", clothes, rough=0.85)
    mat_legs = mat_skin if legwear is None else mat_basic(f"MT_Legs_{tag or name}", legwear, rough=0.85)
    bm = bmesh.new()
    if kneel:
        bm_box(bm, (0, 0.10, 0.18 * s), (0.36 * s, 0.55 * s, 0.34 * s), mat=2)
    else:
        bm_cyl(bm, (-0.09 * s, 0, 0), (-0.09 * s, 0, hip * s), 0.07 * s, 0.08 * s, seg=8, mat=2)
        bm_cyl(bm, (0.09 * s, 0, 0), (0.09 * s, 0, hip * s), 0.07 * s, 0.08 * s, seg=8, mat=2)
    bm_cyl(bm, (0, 0, (hip - 0.12) * s), (0, 0, hip * s), 0.19 * s, 0.19 * s, seg=12, mat=1)   # loin / skirt band
    bm_cyl(bm, (0, 0, hip * s), (0, 0, shoulder * s), 0.17 * s, 0.20 * s, seg=12, mat=0)       # torso
    bm_ellipsoid(bm, (0, 0.01, (shoulder + 0.17) * s), (0.10 * s, 0.11 * s, 0.13 * s), mat=0)   # head
    for fn in (extras or []):
        fn(bm, s, hip, shoulder)
    me = mesh_from_bm(f"MT_{name}_Body", bm, [mat_skin, mat_cloth, mat_legs], smooth=True)
    new_object(f"{name}_Body", me, coll, parent=root)

    arms = {}
    for side, sx in (("r", 1), ("l", -1)):
        piv = new_empty(f"{name}_Arm_{side}", coll, loc=(sx * 0.23 * s, 0, (shoulder - 0.03) * s), parent=root, size=0.08)
        bm = bmesh.new()
        bm_cyl(bm, (0, 0, 0), (0, 0, -0.60 * s), 0.05 * s, 0.04 * s, seg=8)
        bm_ellipsoid(bm, (0, 0, -0.65 * s), (0.045 * s, 0.03 * s, 0.07 * s))
        me = mesh_from_bm(f"MT_{name}_Arm_{side}", bm, [mat_skin], smooth=True)
        new_object(f"{name}_ArmMesh_{side}", me, coll, parent=piv)
        hand = new_empty(f"{name}_Hand_{side}", coll, loc=(0, 0.03 * s, -0.66 * s), parent=piv, size=0.06)
        arms[side] = (piv, hand)
    return dict(root=root, arm_r=arms["r"][0], arm_l=arms["l"][0], hand_r=arms["r"][1], hand_l=arms["l"][1])


def arm_key(pivot, frame, fwd_deg=0.0, side_deg=0.0, twist_deg=0.0):
    pivot.rotation_euler = (math.radians(fwd_deg), math.radians(twist_deg), math.radians(side_deg))
    pivot.keyframe_insert("rotation_euler", frame=frame)


def loop_action(pivot, f0, f1, amp_deg=25.0, period_s=1.2, base_deg=None, axis=0, phase=0.0):
    """Repeating arm motion (pounding, scraping, spear work) between f0 and f1."""
    if base_deg is not None:
        arm_key(pivot, f0, fwd_deg=base_deg)
    add_sine(pivot, "rotation_euler", axis, math.radians(amp_deg), period_s * FPS, f0, f1, blend=10, phase=phase)


def turn_key(root, frame, face):
    if isinstance(face, (tuple, list)):
        face = facing_deg((root.location.x, root.location.y), face)
    root.rotation_euler[2] = math.radians(face)
    root.keyframe_insert("rotation_euler", index=2, frame=frame)


# ---------------------------------------------------------------------------
# Swapping placeholders for real assets (BlenderKit, Human Generator)
# ---------------------------------------------------------------------------

def swap_proxies(scene, only_tags=None, seed=7):
    """Replace every object tagged asset_tag=<tag> with an instance of LIB_<tag>.

    Workflow: import a BlenderKit tree (or a Human Generator character) into a
    collection named e.g. LIB_sabal_palm or LIB_human_villareal, exclude that
    collection from the view layer, then run this. Instances are parented to
    the placeholders, so they follow placeholder animation. The placeholders'
    meshes move to MT_REPLACED_PROXIES (hidden in renders).
    """
    rng = random.Random(seed)
    out = get_collection("MT_SWAPPED", scene.collection)
    hidden = get_collection("MT_REPLACED_PROXIES", scene.collection)
    hidden.hide_render = True
    n = 0
    for ob in list(scene.objects):
        tag = ob.get("asset_tag")
        if not tag or ob.get("swapped"):
            continue
        if only_tags and tag not in only_tags:
            continue
        lib = bpy.data.collections.get("LIB_" + tag)
        if lib is None or len(lib.all_objects) == 0:
            continue
        inst = bpy.data.objects.new(f"INST_{ob.name}", None)
        inst.instance_type = "COLLECTION"
        inst.instance_collection = lib
        out.objects.link(inst)
        inst.parent = ob
        if not tag.startswith("human_") and ob.get("jitter", True):
            inst.rotation_euler.z = rng.uniform(0, 2 * math.pi)
            s = rng.uniform(0.85, 1.15)
            inst.scale = (s, s, s)
        # copy show/hide keys so the asset appears and disappears with the proxy
        for fc in fcurves_of(ob):
            if fc.data_path in ("hide_render", "hide_viewport"):
                for kp in fc.keyframe_points:
                    setattr(inst, fc.data_path, bool(kp.co[1]))
                    inst.keyframe_insert(fc.data_path, frame=int(kp.co[0]))
        set_interpolation(inst, "CONSTANT")
        for o in descendants(ob):
            if o.type == "MESH":
                o["orig_colls"] = [c.name for c in o.users_collection]
                for c in list(o.users_collection):
                    c.objects.unlink(o)
                hidden.objects.link(o)
                o.display_type = "WIRE"
        ob["swapped"] = True
        n += 1
    print(f"[mt] swapped {n} placeholders")
    return n


def unswap_proxies(scene):
    out = bpy.data.collections.get("MT_SWAPPED")
    if out:
        for ob in list(out.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
    hidden = bpy.data.collections.get("MT_REPLACED_PROXIES")
    if hidden:
        for o in list(hidden.objects):
            for cname in o.get("orig_colls", []):
                c = bpy.data.collections.get(cname)
                if c and o.name not in c.objects:
                    c.objects.link(o)
            hidden.objects.unlink(o)
            o.display_type = "TEXTURED"
    for ob in scene.objects:
        if "swapped" in ob:
            del ob["swapped"]


def tag(ob, asset_tag, jitter=True, notes=None):
    ob["asset_tag"] = asset_tag
    ob["jitter"] = jitter
    if notes:
        ob["notes"] = notes
    return ob
