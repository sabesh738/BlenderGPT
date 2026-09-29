"""
PART 01 of "Miami: Walking Through Time"
c. 2,000 years ago  ->  1513  ->  1567-1570          0:00-0:38, frames 1-1140

Scene 1 (frames 1-540)
  You arrive at dawn in a Tequesta dugout, paddled into the mouth of the
  Miami River. The canoe grounds on the beach at Brickell Point; you step off.
  A woman gathering shellfish hands you a shell cup; you drink. You pass a
  woman pounding coontie root and stop at the round thatched house on the
  38-ft ring of posts (the Miami Circle). Time rushes: the house collapses.
Scene 2 (frames 541-1140)
  1513: you walk back to the beach. Three Spanish sails pass on the horizon
  while Tequesta watch. Time rushes to March 1567: a palisade rises behind you
  (you turn to see it), 28 huts, a cross cut from a pine. You walk in through
  the gate past soldiers; one drops a log. Brother Francisco Villareal hands
  you an iron nail and says "Agua". 1570: the mission is abandoned; days and
  nights strobe past while it rots and the scrub grows back. The counter runs
  on toward 1836 (Part 02).

Run it
  Blender 4.2+: Scripting workspace > Open this file > Run Script.
  Headless:     blender -b -P build_part01_tequesta_spanish.py
  Test stills:  blender -b -P build_part01_tequesta_spanish.py -- --stills /tmp/p01
It builds two scenes: MIAMI_3D (the world) and MIAMI_EDIT (HUD on top).
Render MIAMI_EDIT for the finished frames.

Facts on screen are sourced in ../ERA_BIBLE.md and ../PART01_SHOTLIST.md.
"""
import importlib
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector


def _here():
    try:
        d = os.path.dirname(os.path.abspath(__file__))
        if os.path.exists(os.path.join(d, "mt_common.py")):
            return d
    except NameError:
        pass
    for t in bpy.data.texts:
        if t.filepath and "build_part01" in t.name:
            return os.path.dirname(bpy.path.abspath(t.filepath))
    return bpy.path.abspath("//")


sys.path.insert(0, _here())
import mt_common  # noqa: E402
import mt_hud  # noqa: E402
import mt_props  # noqa: E402

for _m in (mt_common, mt_props, mt_hud):
    importlib.reload(_m)

from mt_common import (EYE_HEIGHT, SCENE_3D, SEATED_EYE, Palette, PovRig, add_noise, add_sine,  # noqa: E402
                       arm_key, arm_pose, build_grade, build_pov_arm, build_sun, build_terrain,
                       build_mist, build_water, build_world, facing_deg, get_collection, get_scene, grade_key,
                       ground_height, handoff, key, loop_action, make_person, new_empty, new_object,
                       purge_orphans, set_interpolation, setup_render, shore_distance, show_range,
                       sky_key, tag, turn_key, wipe_collection)
from mt_props import (breechcloth, build_drying_rack, build_dugout, build_fire, build_miami_circle,  # noqa: E402
                      build_midden, build_stockade, cassock, flicker, mesh_arquebus, mesh_basket,
                      mesh_coontie, mesh_log, mesh_longboat, mesh_mortar, mesh_nail, mesh_nao,
                      mesh_pestle, mesh_pine_cross, mesh_pole, mesh_saw_palmetto, mesh_seagrape,
                      mesh_shell_cup, mesh_slate, mesh_spanish_hut, mesh_tequesta_house, moss_skirt,
                      place, reset_cache, scatter, soldier_kit)

ENGINE = os.environ.get("MT_ENGINE", "EEVEE")  # "CYCLES" for the final render if your GPU allows

# ---------------------------------------------------------------------------
# Timing (frame 1 = 0:00, 30 fps)
# ---------------------------------------------------------------------------
P0, P1 = 1, 1140
S2 = 541                      # scene 2 starts (0:18)
LAND_F = 232                  # canoe grounds
CUP_F = 338                   # shell cup changes hands
S1_RUSH = (470, 540)          # time rushes: c. 2,000 years ago -> 1513
SKIP_1567 = (740, 790)        # time rushes: 1513 -> 1567
LOG_F = 862                   # soldier drops a log
NAIL_F = 946                  # iron nail changes hands
AGUA_F = 965                  # "Agua"
ABANDON_F = 1030              # 1570
DECAY = (1040, 1125)          # the mission rots
COUNT_1836 = (1060, 1140)

# ---------------------------------------------------------------------------
# Places (metres; +X east toward Biscayne Bay, +Y north across the river)
# ---------------------------------------------------------------------------
CANOE_KEYS = [(1, (36.0, -19.0)), (150, (30.0, -24.5)), (LAND_F, (24.0, -32.2))]
STEP_OFF = (21.3, -35.3)
WOMAN = (20.0, -38.3)
MEET = (20.8, -36.9)
COONTIE = (19.8, -42.6)
CIRCLE = (14.0, -46.0)
CIRCLE_VIEW = (18.2, -40.4)
BEACH_VIEW = (20.8, -36.2)
CHILDREN = [(26.5, -33.8), (28.3, -35.0)]
CARVER = (10.6, -36.4)
FIRE = (11.5, -41.0)
RACK = (9.2, -40.2)
MIDDEN = (4.5, -38.6)
VILLAGE = [(-30, 48), (-15, 52), (0, 47), (15, 55), (-5, 62), (-22, 64)]
STOCK_C, STOCK_R = (7.0, -50.0), 14.0
GATE = (17.05, -40.26)
GATE_DEG = math.degrees(math.atan2(GATE[1] - STOCK_C[1], GATE[0] - STOCK_C[0]))
APPROACH = (18.9, -38.2)
VILLAREAL = (13.3, -44.1)
MEET2 = (14.6, -43.0)
YOUTH = (12.2, -43.2)

# colours (placeholders; Human Generator and BlenderKit replace these)
TEQ_SKIN = [(0.33, 0.20, 0.13), (0.30, 0.18, 0.11), (0.37, 0.23, 0.15)]
SPAN_SKIN = (0.62, 0.45, 0.35)
PALMETTO_FIBRE = (0.45, 0.38, 0.22)
SPANISH_MOSS = (0.42, 0.45, 0.36)
HOSE = (0.35, 0.22, 0.12)
BLACK_HABIT = (0.03, 0.03, 0.035)

EXCLUDE = [((7.0, -50.0), 17.5), (CIRCLE, 7.5)] + [(v, 7.0) for v in VILLAGE]


def _clear(x, y):
    if 6 < x < 42 and -46 < y < -26:
        return False
    return all((x - cx) ** 2 + (y - cy) ** 2 > r * r for (cx, cy), r in EXCLUDE)


# ---------------------------------------------------------------------------
# Vegetation
# ---------------------------------------------------------------------------

def build_vegetation(c, pal):
    def land(dmin, dmax, x=(-250, 40), y=(-250, 250), cond=None):
        def s(rng):
            px, py = rng.uniform(*x), rng.uniform(*y)
            d = shore_distance(px, py)
            if dmin < d < dmax and _clear(px, py) and (cond is None or cond(px, py)):
                return (px, py)
            return None
        return s

    scatter(c, pal, "mangrove", 140, land(-4.0, 1.5, x=(-280, 60), y=(-200, 200)), seed=11, scale=(0.8, 1.3))
    scatter(c, pal, "sabal_palm", 110, land(3, 150), seed=12)
    scatter(c, pal, "sea_grape", 60, land(2, 18), seed=13)
    scatter(c, pal, "saw_palmetto", 160, land(6, 150), seed=14, scale=(0.8, 1.4))
    scatter(c, pal, "slash_pine", 70, land(30, 200, cond=lambda px, py: py < -60 or py > 70), seed=15)

    # near-field plants that frame the walk
    rng = random.Random(21)
    near = []
    for i, p in enumerate([(24.5, -44.5), (26.0, -40.0), (23.5, -47.5)]):
        near.append(place(c, f"near_palm_{i}", mt_props.mesh_sabal_palm(pal, i), p, "sabal_palm",
                          rot_z=rng.uniform(0, 6.28)))
    for i in range(26):
        p = (rng.uniform(21, 26), rng.uniform(-47, -40)) if i < 16 else (rng.uniform(2, 8), rng.uniform(-44, -40))
        near.append(place(c, f"coontie_{i:02d}", mesh_coontie(pal), p, "coontie",
                          rot_z=rng.uniform(0, 6.28), scale=rng.uniform(0.8, 1.3)))
    # cleared when the stockade goes up in 1567
    cleared = [place(c, "cleared_palm_0", mt_props.mesh_sabal_palm(pal, 3), (4.0, -37.8), "sabal_palm")]
    for i in range(8):
        a = rng.uniform(0, 6.28)
        r = rng.uniform(3, 12)
        cleared.append(place(c, f"cleared_palmetto_{i}", mesh_saw_palmetto(pal, i % 4),
                             (STOCK_C[0] + r * math.cos(a), STOCK_C[1] + r * math.sin(a)), "saw_palmetto"))
    show_range(cleared, 1, 750)
    return near


# ---------------------------------------------------------------------------
# Scene 1: Tequesta
# ---------------------------------------------------------------------------

def _heading(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def canoe_seat(center, heading_deg, back=1.4):
    h = math.radians(heading_deg)
    return (center[0] - math.cos(h) * back, center[1] - math.sin(h) * back)


def canoe_headings():
    out = []
    for i, (f, p) in enumerate(CANOE_KEYS):
        q = CANOE_KEYS[min(i + 1, len(CANOE_KEYS) - 1)][1]
        r = CANOE_KEYS[max(i - 1, 0)][1]
        out.append(_heading(p, q) if i + 1 < len(CANOE_KEYS) else _heading(r, p))
    return out


def tequesta(c, name, pos, face, woman=False, kneel=False, height=None, i=0, notes=""):
    skin = TEQ_SKIN[i % len(TEQ_SKIN)]
    if woman:
        return make_person(c, name, pos, face, SPANISH_MOSS, skin=skin, height=height or 1.56,
                           extras=[moss_skirt], kneel=kneel, tag=name.lower(), notes=notes)
    return make_person(c, name, pos, face, PALMETTO_FIBRE, skin=skin, height=height or 1.66,
                       extras=[breechcloth], kneel=kneel, tag=name.lower(), notes=notes)


def build_scene1(c, pal):
    o = {}
    heads = canoe_headings()

    # --- your canoe and the paddler at the bow ---------------------------
    canoe = build_dugout(c, pal, "S1_POV_Canoe", (*CANOE_KEYS[0][1], 0.25), heads[0])
    for (f, p), h in zip(CANOE_KEYS, heads):
        canoe.location = (p[0], p[1], 0.25 if f < LAND_F else 0.18)
        canoe.rotation_euler[2] = math.radians(h)
        canoe.keyframe_insert("location", frame=f)
        canoe.keyframe_insert("rotation_euler", index=2, frame=f)
    add_sine(canoe, "rotation_euler", 0, math.radians(1.3), 3.6 * 30, 1, LAND_F, blend=12)
    o["canoe"] = canoe
    pad = tequesta(c, "S1_Paddler", (0, 0), 0, kneel=True, i=1,
                   notes="Paddles at the bow. Breechcloth of palmetto fibre.")
    pad["root"].parent = canoe
    pad["root"].location = (2.5, 0, -0.32)
    pad["root"].rotation_euler = (0, 0, math.radians(-90))
    paddle = new_object("S1_Paddle", mesh_pole(pal, 2.2, 0.03, "MTP_paddle"), c,
                        rot=(math.radians(70), 0, 0), parent=pad["hand_r"])
    tag(paddle, "canoe_paddle", jitter=False)
    loop_action(pad["arm_r"], 1, LAND_F - 10, amp_deg=35, period_s=1.6, base_deg=40)
    loop_action(pad["arm_l"], 1, LAND_F - 10, amp_deg=35, period_s=1.6, base_deg=40, phase=math.pi)
    show_range(canoe, 1, 750)
    show_range(pad["root"], 1, S2)

    # --- woman gathering shellfish, who hands you the shell cup ----------
    w = tequesta(c, "S1_Woman_Cup", WOMAN, (26.0, -32.0), woman=True, i=0,
                 notes="Gathers clams at the waterline, then offers the shell cup.")
    loop_action(w["arm_r"], 1, 285, amp_deg=15, period_s=1.4, base_deg=60)
    loop_action(w["arm_l"], 1, 285, amp_deg=15, period_s=1.4, base_deg=60, phase=1.0)
    turn_key(w["root"], 290, facing_deg(WOMAN, (26.0, -32.0)))
    turn_key(w["root"], 306, facing_deg(WOMAN, MEET))
    for f, deg in ((285, 60), (300, 8), (318, 12), (CUP_F - 4, 78), (CUP_F + 10, 78), (CUP_F + 22, 10)):
        arm_key(w["arm_r"], f, fwd_deg=deg)
    arm_key(w["arm_l"], 300, fwd_deg=5)
    basket = new_object("S1_Basket_Woman", mesh_basket(pal), c,
                        loc=(WOMAN[0] + 0.7, WOMAN[1] + 0.5, ground_height(WOMAN[0] + 0.7, WOMAN[1] + 0.5)))
    show_range([w["root"], basket], 1, S2)
    o["woman"] = w

    cup = new_object("HANDOFF_ShellCup", mesh_shell_cup(pal), c)
    tag(cup, "shell_cup", jitter=False)
    o["cup"] = cup

    # --- children gathering shells --------------------------------------
    for i, p in enumerate(CHILDREN):
        k = tequesta(c, f"S1_Child_{i}", p, (p[0] + 3, p[1] + 2), woman=(i == 1), height=1.15, i=i + 1,
                     notes="Collects clams, conchs and oysters into a basket.")
        loop_action(k["arm_r"], 1, S2, amp_deg=20, period_s=1.1 + 0.2 * i, base_deg=70)
        loop_action(k["arm_l"], 1, S2, amp_deg=20, period_s=1.3 + 0.2 * i, base_deg=65, phase=0.7)
        new_object(f"S1_Basket_Child_{i}", mesh_basket(pal), c,
                   loc=(p[0] - 0.5, p[1] + 0.3, ground_height(p[0] - 0.5, p[1] + 0.3)), scale=(0.8, 0.8, 0.8))
        show_range(k["root"], 1, S2)

    # --- woman pounding coontie root ------------------------------------
    cw = tequesta(c, "S1_Coontie_Woman", COONTIE, (COONTIE[0] - 1, COONTIE[1] + 0.5), woman=True,
                  kneel=True, i=2, notes="Pounds coontie root to flour; toxins are washed out before baking.")
    fwd = math.radians(facing_deg(COONTIE, (COONTIE[0] - 1, COONTIE[1] + 0.5)))
    mx, my = COONTIE[0] - math.sin(fwd) * 0.5, COONTIE[1] + math.cos(fwd) * 0.5
    tag(new_object("S1_Mortar", mesh_mortar(pal), c, loc=(mx, my, ground_height(mx, my))), "wooden_mortar", False)
    new_object("S1_Pestle", mesh_pestle(pal), c, loc=(0, 0.1, 0), parent=cw["hand_r"])
    loop_action(cw["arm_r"], 1, S2, amp_deg=28, period_s=0.9, base_deg=50)
    loop_action(cw["arm_l"], 1, S2, amp_deg=28, period_s=0.9, base_deg=50)
    show_range(cw["root"], 1, S2)

    # --- carving a dugout from a log ------------------------------------
    build_dugout(c, pal, "S1_Dugout_Unfinished", (CARVER[0] - 0.6, CARVER[1] - 1.2, ground_height(*CARVER) + 0.35), 5)
    cv = tequesta(c, "S1_Carver", CARVER, (CARVER[0] - 0.6, CARVER[1] - 1.2), kneel=True, i=0,
                  notes="Hollows a log with a shell adze; charred wood is scraped out.")
    new_object("S1_Adze", mesh_pole(pal, 0.5, 0.02, "MTP_adze"), c, parent=cv["hand_r"])
    loop_action(cv["arm_r"], 1, S2, amp_deg=35, period_s=1.1, base_deg=60)
    show_range(cv["root"], 1, S2)

    # --- camp: fire, fish rack, shell midden ----------------------------
    fire, light, smoke = build_fire(c, pal, "S1_Fire", FIRE)
    flicker(light, 1, 750)
    rack = build_drying_rack(c, pal, "S1_FishRack", RACK, face_deg=30)
    midden = build_midden(c, pal, "S1_Midden", MIDDEN)
    show_range([fire, rack, midden], 1, 750)

    # --- the Miami Circle -----------------------------------------------
    posts, roof, floor = build_miami_circle(c, pal, CIRCLE)
    elder = tequesta(c, "S1_Elder", (13.3, -41.4), CIRCLE_VIEW, i=2, height=1.62,
                     notes="Stands at the edge of the round house, watching you arrive.")
    arm_key(elder["arm_l"], 1, fwd_deg=10)
    f0, f1 = S1_RUSH
    gz = roof.location.z
    for f, dz, tilt, s in ((f0, 0.0, 0.0, 1.0), (f0 + 30, -0.9, 0.12, 0.97), (f1 - 5, -2.4, 0.35, 0.9)):
        roof.location.z = gz + dz
        roof.rotation_euler[0] = tilt
        roof.scale = (s, s, s)
        roof.keyframe_insert("location", index=2, frame=f)
        roof.keyframe_insert("rotation_euler", index=0, frame=f)
        roof.keyframe_insert("scale", frame=f)
    pz = posts.location.z
    for f, dz in ((f0 + 10, 0.0), (f1 - 3, -2.8)):
        posts.location.z = pz + dz
        posts.keyframe_insert("location", index=2, frame=f)
    show_range([posts, roof, floor, elder["root"]], 1, S2)

    # --- life on the water ----------------------------------------------
    rc = build_dugout(c, pal, "S1_River_Canoe", (-40, 5, 0.25), 0)
    for f, x, y in ((1, -40, 5), (750, 12, -2)):
        rc.location = (x, y, 0.25)
        rc.keyframe_insert("location", frame=f)
    set_interpolation(rc, "LINEAR", paths=("location",))
    add_sine(rc, "rotation_euler", 0, math.radians(1.5), 100, 1, 750, blend=10)
    for i, (lx, notes) in enumerate(((-2.0, "Poles the canoe."), (2.0, "Spear raised for fish."))):
        fm = tequesta(c, f"S1_River_Fisher_{i}", (0, 0), 0, i=i, notes=notes)
        fm["root"].parent = rc
        fm["root"].location = (lx, 0, -0.35)
        fm["root"].rotation_euler = (0, 0, math.radians(-90))
        new_object(f"S1_River_Pole_{i}", mesh_pole(pal, 3.2 if i == 0 else 2.4), c,
                   rot=(math.radians(20 if i == 0 else 150), 0, 0), parent=fm["hand_r"])
        loop_action(fm["arm_r"], 1, 750, amp_deg=30 if i == 0 else 15, period_s=2.2 if i == 0 else 3.0,
                    base_deg=45 if i == 0 else 120)
    show_range(rc, 1, 750)

    bc = build_dugout(c, pal, "S1_Bay_Canoe", (78, -8, 0.25), 70)
    for f, x, y in ((1, 78, -8), (750, 72, -2)):
        bc.location = (x, y, 0.25)
        bc.keyframe_insert("location", frame=f)
    add_sine(bc, "rotation_euler", 0, math.radians(2.0), 80, 1, 750, blend=10)
    for i in range(2):
        bm_ = tequesta(c, f"S1_Bay_Fisher_{i}", (0, 0), 0, kneel=True, i=i + 1,
                       notes="Fishes the bay for shark and sailfish; manatee was a chief's delicacy.")
        bm_["root"].parent = bc
        bm_["root"].location = (-1.5 + 3.0 * i, 0, -0.1)
        loop_action(bm_["arm_r"], 1, 750, amp_deg=25, period_s=2.5 + i, base_deg=70)
    show_range(bc, 1, 750)

    # --- the town across the river --------------------------------------
    houses = []
    for i, (x, y) in enumerate(VILLAGE):
        h = new_object(f"S1_Village_House_{i}", mesh_tequesta_house(pal), c,
                       loc=(x, y, ground_height(x, y)), rot=(0, 0, math.radians(90 + (i * 23) % 40 - 20)))
        houses.append(tag(h, "tequesta_house", jitter=False))
    vfire, vlight, _ = build_fire(c, pal, "S1_Village_Fire", (-8, 55))
    flicker(vlight, 1, 1060)
    show_range(vfire, 1, 1060)
    for i, p in enumerate([(-12, 50), (5, 51), (-26, 55)]):
        v = tequesta(c, f"S1_Villager_{i}", p, (p[0], p[1] - 5), woman=bool(i % 2), i=i)
        loop_action(v["arm_r"], 1, 750, amp_deg=20, period_s=1.5 + 0.3 * i, base_deg=40)
        show_range(v["root"], 1, 750)
    o["houses"] = houses
    return o


# ---------------------------------------------------------------------------
# Scene 2: Spanish contact
# ---------------------------------------------------------------------------

def spaniard(c, name, pos, face, pal, notes="", villareal=False):
    if villareal:
        return make_person(c, name, pos, face, BLACK_HABIT, skin=SPAN_SKIN, height=1.66, extras=[cassock],
                           legwear=BLACK_HABIT, tag=name.lower(), notes=notes)
    return make_person(c, name, pos, face, pal.steel, skin=SPAN_SKIN, height=1.64, extras=[soldier_kit],
                       legwear=HOSE, tag=name.lower(), notes=notes)


def build_scene2(c, pal, s1):
    o = {}
    # --- 1513: Tequesta on the beach watch Spanish sails pass -----------
    for i, p in enumerate([(23.0, -33.3), (24.8, -33.9), (21.6, -34.6)]):
        t = tequesta(c, f"S2_Watcher_{i}", p, (400, p[1]), woman=(i == 1), i=i,
                     notes="Watches the ships; one points.")
        if i == 0:
            arm_key(t["arm_r"], 600, fwd_deg=5)
            arm_key(t["arm_r"], 612, fwd_deg=95, side_deg=-5)
            arm_key(t["arm_r"], 690, fwd_deg=95, side_deg=-5)
            arm_key(t["arm_r"], 705, fwd_deg=5)
        show_range(t["root"], S2, 750)

    for i, (x, lead) in enumerate(((380, 0), (405, 60), (430, 120))):
        s = tag(new_object(f"S2_Ship_1513_{i}", mesh_nao(pal), c, rot=(0, 0, math.radians(-90))), "spanish_nao", False)
        for f, y in ((560, 330 + lead), (780, -330 + lead)):
            s.location = (x, y, 0.0)
            s.keyframe_insert("location", frame=f)
        set_interpolation(s, "LINEAR", paths=("location",))
        add_sine(s, "rotation_euler", 1, math.radians(1.5), 110, S2, 780, blend=10)
        show_range(s, S2, 780)

    # --- 1567: ship at anchor, longboat on the beach --------------------
    anchor = tag(new_object("S2_Ship_1567", mesh_nao(pal), c, loc=(95, -10, 0), rot=(0, 0, math.radians(200))),
                 "spanish_nao", False)
    add_sine(anchor, "rotation_euler", 0, math.radians(1.2), 140, 750, ABANDON_F, blend=10)
    lb = tag(new_object("S2_Longboat", mesh_longboat(pal), c, loc=(25.5, -32.9, 0.35), rot=(0, 0, math.radians(200))),
             "spanish_longboat", False)
    show_range([anchor, lb], 750, ABANDON_F)

    # --- the stockade rises ----------------------------------------------
    st = build_stockade(c, pal, "S2_Stockade", STOCK_C, STOCK_R, GATE_DEG)
    kb = st.data.shape_keys.key_blocks
    for f, v in ((SKIP_1567[0] + 5, 1.0), (SKIP_1567[1] - 5, 0.0)):
        kb["Buried"].value = v
        kb["Buried"].keyframe_insert("value", frame=f)
    for f, v in ((DECAY[0], 0.0), (DECAY[1], 1.0)):
        kb["Decayed"].value = v
        kb["Decayed"].keyframe_insert("value", frame=f)
    show_range(st, SKIP_1567[0] + 5, None)
    o["stockade"] = st

    cz = ground_height(*STOCK_C)
    cross = tag(new_object("S2_Pine_Cross", mesh_pine_cross(pal), c, loc=(*STOCK_C, cz)), "pine_cross", False)
    for f, rx, dz in ((770, 88, 0), (796, 0, 0), (1082, 0, 0), (1098, -84, 0), (1118, -84, -1.2)):
        cross.rotation_euler[0] = math.radians(rx)
        cross.location.z = cz + dz
        cross.keyframe_insert("rotation_euler", index=0, frame=f)
        cross.keyframe_insert("location", index=2, frame=f)
    show_range(cross, 750, None)

    rng = random.Random(28)
    huts, tries = [], 0
    path_pts = [GATE, MEET2, VILLAREAL, YOUTH]
    while len(huts) < 28 and tries < 6000:
        tries += 1
        a, r = rng.uniform(0, 2 * math.pi), rng.uniform(4.0, 12.2)
        x, y = STOCK_C[0] + r * math.cos(a), STOCK_C[1] + r * math.sin(a)
        if any((x - hx) ** 2 + (y - hy) ** 2 < 3.1 ** 2 for hx, hy in huts):
            continue
        if any((x - px) ** 2 + (y - py) ** 2 < 3.0 ** 2 for px, py in path_pts):
            continue
        huts.append((x, y))
    hut_obs = []
    for i, (x, y) in enumerate(huts):
        gz = ground_height(x, y)
        h = tag(new_object(f"S2_Hut_{i:02d}", mesh_spanish_hut(pal), c, loc=(x, y, gz),
                           rot=(0, 0, math.radians(facing_deg((x, y), STOCK_C)))), "spanish_hut", False)
        t0 = int(SKIP_1567[0] + 10 + rng.uniform(0, 30))
        h.scale = (0.01, 0.01, 0.01)
        h.keyframe_insert("scale", frame=t0)
        h.scale = (1, 1, 1)
        h.keyframe_insert("scale", frame=t0 + 12)
        td = int(DECAY[0] + rng.uniform(0, 55))
        h.keyframe_insert("rotation_euler", frame=td)
        h.keyframe_insert("location", index=2, frame=td)
        h.rotation_euler[0] = math.radians(rng.uniform(-55, 55))
        h.rotation_euler[1] = math.radians(rng.uniform(-40, 40))
        h.location.z = gz - rng.uniform(0.8, 1.6)
        h.keyframe_insert("rotation_euler", frame=td + 16)
        h.keyframe_insert("location", index=2, frame=td + 16)
        show_range(h, SKIP_1567[0] + 5, 1118)
        hut_obs.append(h)
    o["huts"] = hut_obs

    # --- people of the mission ------------------------------------------
    people = []
    s1l = spaniard(c, "S2_Soldier_Logs", (15.6, -42.0), (17.0, -40.0), pal,
                   notes="Carries a log to the palisade and drops it.")
    arm_key(s1l["arm_r"], 790, fwd_deg=160)
    arm_key(s1l["arm_l"], 790, fwd_deg=160)
    arm_key(s1l["arm_r"], LOG_F - 4, fwd_deg=160)
    arm_key(s1l["arm_l"], LOG_F - 4, fwd_deg=160)
    arm_key(s1l["arm_r"], LOG_F + 2, fwd_deg=40)
    arm_key(s1l["arm_l"], LOG_F + 2, fwd_deg=40)
    turn_key(s1l["root"], LOG_F + 10, (15.6, -45.0))
    people.append(s1l)
    log = tag(new_object("S2_Dropped_Log", mesh_log(pal), c), "log", False)
    lx, ly = 15.6, -42.0
    gz = ground_height(lx, ly)
    head = math.radians(facing_deg((lx, ly), (17.0, -40.0)))
    log.rotation_euler = (0, 0, head)
    for f, z, roll in ((790, gz + 1.95, 0.0), (LOG_F - 3, gz + 1.95, 0.0), (LOG_F, gz + 0.16, 0.25),
                       (LOG_F + 5, gz + 0.22, 0.05), (LOG_F + 9, gz + 0.16, 0.0)):
        log.location = (lx, ly, z)
        log.rotation_euler[1] = roll
        log.keyframe_insert("location", frame=f)
        log.keyframe_insert("rotation_euler", index=1, frame=f)
    set_interpolation(log, "LINEAR", paths=("location",), frame_range=(LOG_F - 3, LOG_F))
    pile = [tag(new_object(f"S2_LogPile_{i}", mesh_log(pal), c,
                           loc=(16.6, -42.8 + 0.34 * (i % 3), ground_height(16.6, -42.8) + 0.16 + 0.3 * (i // 3)),
                           rot=(0, 0, math.radians(95))), "log", False) for i in range(5)]

    guard = spaniard(c, "S2_Soldier_Guard", (19.3, -40.9), APPROACH, pal, notes="Guards the gate with an arquebus.")
    new_object("S2_Arquebus", mesh_arquebus(pal), c, loc=(0, 0.05, 0.1), parent=guard["hand_r"])
    arm_key(guard["arm_r"], 790, fwd_deg=12)
    people.append(guard)
    for i, (p, face, period) in enumerate((((4.0, -46.5), (3.0, -48.0), 1.0), ((9.5, -55.0), (9.0, -56.5), 1.3),
                                           ((1.0, -53.5), (0.0, -55.0), 1.6))):
        sw = spaniard(c, f"S2_Soldier_Work_{i}", p, face, pal, notes="Builds huts: lashing poles, laying thatch.")
        loop_action(sw["arm_r"], 790, ABANDON_F, amp_deg=30, period_s=period, base_deg=70)
        loop_action(sw["arm_l"], 790, ABANDON_F, amp_deg=20, period_s=period * 1.3, base_deg=50, phase=1.0)
        people.append(sw)
    sc = spaniard(c, "S2_Soldier_Cross", (8.2, -48.6), STOCK_C, pal, notes="Steadies the cross.")
    arm_key(sc["arm_r"], 790, fwd_deg=100)
    arm_key(sc["arm_l"], 790, fwd_deg=100)
    people.append(sc)

    vil = spaniard(c, "S2_Villareal", VILLAREAL, YOUTH, pal, villareal=True,
                   notes="Brother Francisco Villareal, Jesuit. Teaches words with a slate; hands you a nail; says 'Agua'.")
    new_object("S2_Slate", mesh_slate(pal), c, loc=(0, 0.06, 0), parent=vil["hand_l"])
    arm_key(vil["arm_l"], 790, fwd_deg=70)
    turn_key(vil["root"], 900, YOUTH)
    turn_key(vil["root"], 920, MEET2)
    for f, deg in ((NAIL_F - 14, 10), (NAIL_F - 2, 72), (NAIL_F + 8, 72), (NAIL_F + 18, 10)):
        arm_key(vil["arm_r"], f, fwd_deg=deg)
    for f, fwd, side in ((AGUA_F - 4, 70, 0), (AGUA_F + 6, 85, -35), (AGUA_F + 40, 85, -35), (AGUA_F + 55, 70, 0)):
        arm_key(vil["arm_l"], f, fwd_deg=fwd, side_deg=side)
    people.append(vil)

    youth = tequesta(c, "S2_Tequesta_Youth", YOUTH, VILLAREAL, i=1, height=1.5,
                     notes="Learns Spanish words from Villareal; repeats 'Agua'.")
    people.append(youth)
    elder = tequesta(c, "S2_Tequesta_Elder", (21.0, -43.5), GATE, i=2, height=1.62,
                     notes="Stands outside the wall and watches.")
    people.append(elder)
    for i, p in enumerate([(19.6, -36.9), (20.6, -37.6)]):
        v = tequesta(c, f"S2_Tequesta_Visitor_{i}", p, GATE, woman=bool(i), i=i,
                     notes="Visitors at the gate with a basket of fish.")
        arm_key(v["arm_r"], 790, fwd_deg=25)
        new_object(f"S2_Visitor_Basket_{i}", mesh_basket(pal), c, loc=(0, 0.1, 0), parent=v["hand_r"])
        people.append(v)
    show_range([p["root"] for p in people] + [log] + pile, 790, ABANDON_F)

    nail = tag(new_object("HANDOFF_Nail", mesh_nail(pal), c), "iron_nail", False)
    o["nail"], o["villareal"] = nail, vil

    # --- the scrub grows back after 1570 ---------------------------------
    rng = random.Random(70)
    for i in range(40):
        a, r = rng.uniform(0, 2 * math.pi), rng.uniform(0, 14)
        x, y = STOCK_C[0] + r * math.cos(a), STOCK_C[1] + r * math.sin(a)
        kind = rng.choice(("saw_palmetto", "saw_palmetto", "sea_grape"))
        me = mesh_saw_palmetto(pal, i % 4) if kind == "saw_palmetto" else mesh_seagrape(pal, i % 4)
        g = place(c, f"S2_Regrowth_{i:02d}", me, (x, y), kind, rot_z=rng.uniform(0, 6.28))
        tg = int(DECAY[0] + 10 + rng.uniform(0, 70))
        s = rng.uniform(0.7, 1.2)
        g.scale = (0.01, 0.01, 0.01)
        g.keyframe_insert("scale", frame=tg)
        g.scale = (s, s, s)
        g.keyframe_insert("scale", frame=tg + 18)
        show_range(g, tg, None)

    # the town across the river empties and rots too
    for i, h in enumerate(s1["houses"]):
        td = 1060 + i * 8
        h.keyframe_insert("rotation_euler", frame=td)
        h.keyframe_insert("location", index=2, frame=td)
        h.rotation_euler[0] += math.radians(25 + 7 * i)
        h.location.z -= 1.4
        h.keyframe_insert("rotation_euler", frame=td + 14)
        h.keyframe_insert("location", index=2, frame=td + 14)
        show_range(h, 1, 1125)
    return o


# ---------------------------------------------------------------------------
# Camera, hands and hand-offs
# ---------------------------------------------------------------------------

def build_camera(rig, arm, hand, s1, s2):
    heads = canoe_headings()
    pts = []
    for (f, p), h in zip(CANOE_KEYS, heads):
        sx, sy = canoe_seat(p, h)
        pts.append((f, sx, sy, SEATED_EYE if f < LAND_F else SEATED_EYE - 0.05))
    sx, sy = canoe_seat(CANOE_KEYS[-1][1], heads[-1])
    pts.append((LAND_F + 8, sx, sy, SEATED_EYE - 0.05))
    rig.path(pts)
    rig.path([
        (262, *STEP_OFF), (330, *MEET), (400, *MEET), (470, *CIRCLE_VIEW), (S2, *CIRCLE_VIEW),
        (640, *BEACH_VIEW), (SKIP_1567[0], *BEACH_VIEW), (SKIP_1567[1], *APPROACH),
        (855, *GATE), (940, *MEET2), (P1, *MEET2),
    ])

    # (frame, x, y, height above the ground there)
    for f, x, y, h in [
        (1, *WOMAN, 1.4), (70, *WOMAN, 1.2), (120, -10, 3, 1.4), (170, -5, 2, 1.4),
        (205, *CHILDREN[0], 0.6), (LAND_F, 22.5, -34.5, 0.2), (262, *WOMAN, 1.45), (300, *WOMAN, 1.45),
        (CUP_F, 20.3, -37.5, 1.1), (360, *WOMAN, 1.4), (395, *WOMAN, 1.4), (430, *COONTIE, 0.7),
        (470, *CIRCLE, 2.2), (505, *CIRCLE, 3.4), (540, 13.0, -46.0, 1.8),
        (575, 60, -25, 2.0), (600, 120, -10, 3.0), (640, 405, 90, 8.0), (SKIP_1567[0], 405, -210, 8.0),
        (760, 18.0, -40.0, 2.4), (SKIP_1567[1], *GATE, 2.2), (855, 14.5, -43.5, 1.5), (LOG_F, 15.6, -42.0, 0.3),
        (880, *VILLAREAL, 1.55), (NAIL_F - 6, *VILLAREAL, 1.55), (NAIL_F + 4, 13.9, -43.6, 1.05),
        (AGUA_F, *VILLAREAL, 1.6), (1000, *YOUTH, 1.4), (ABANDON_F, *STOCK_C, 2.4),
        (1080, 2.0, -45.0, 2.0), (P1, 10.0, -58.0, 1.8),
    ]:
        rig.look_at(f, x, y, h)

    # layers: boat sway, footsteps, jolts, time rushes
    rig.float_sway(1, LAND_F)
    rig.impact(LAND_F, dip=0.05, pitch_deg=2.5)          # hull grinds onto the sand
    rig.shake(LAND_F, 22, intensity=0.7, speed=1.6)
    rig.impact(258, dip=0.03, pitch_deg=1.2)             # first step onto the beach
    for f0, f1 in ((262, 330), (400, 470), (S2, 640), (SKIP_1567[0], 940)):
        rig.walk_bob(f0, f1)
    rig.impact(LOG_F, dip=0.022, pitch_deg=1.0)          # the log hits the ground
    rig.shake(LOG_F, 12, intensity=0.5, speed=1.8)
    rig.time_rush(*S1_RUSH)
    rig.time_rush(*SKIP_1567)
    rig.time_rush(DECAY[0], P1)

    # right hand
    for f, pose in ((1, "down"), (CUP_F - 14, "down"), (CUP_F - 2, "reach"), (CUP_F + 8, "hold"),
                    (362, "hold"), (375, "drink"), (392, "drink"), (405, "hold"), (505, "hold"), (525, "down"),
                    (NAIL_F - 12, "down"), (NAIL_F, "reach"), (NAIL_F + 10, "show"), (1015, "show"),
                    (1035, "down")):
        arm_pose(arm, f, pose)

    # shell cup: woman's hand -> your hand; tilt toward you to drink
    cup = s1["cup"]
    handoff(cup, s1["woman"]["hand_r"], hand, CUP_F, blend=8)
    view = Vector((WOMAN[0] - MEET[0], WOMAN[1] - MEET[1], 0)).normalized()
    axis = view.cross(Vector((0, 0, 1))).normalized()
    for f, ang in ((362, 0), (375, 70), (392, 70), (405, 0)):
        cup.rotation_euler = Matrix.Rotation(math.radians(-ang), 3, axis).to_euler()
        cup.keyframe_insert("rotation_euler", frame=f)
    show_range(cup, 290, S2)

    # iron nail: Villareal's hand -> yours
    nail = s2["nail"]
    handoff(nail, s2["villareal"]["hand_r"], hand, NAIL_F, blend=6)
    nail.rotation_euler = (math.radians(90), 0, math.radians(30))
    show_range(nail, 790, None)


# ---------------------------------------------------------------------------
# Sky and grade
# ---------------------------------------------------------------------------

def build_sky(scene, world, sun):
    keys = [
        # frame, elevation, azimuth, air, dust, strength, mist
        (1, 0.5, 95, 1.3, 3.0, 0.7, 0.006),      # dawn over the bay, ground mist
        (240, 5, 97, 1.2, 2.5, 0.6, 0.005),
        (S1_RUSH[0], 11, 100, 1.1, 2.0, 0.45, 0.004),
        (S1_RUSH[1], 58, 150, 1.0, 1.2, 0.16, 0.0009),  # time-lapse to a hot 1513 midday
        (SKIP_1567[0], 68, 185, 1.0, 1.2, 0.16, 0.0009),
        (755, -12, 270, 1.0, 1.0, 0.3, 0.003),           # night flicks past
        (770, 15, 455, 1.0, 1.4, 0.4, 0.002),            # dawn (95 deg + 360)
        (SKIP_1567[1], 42, 595, 1.0, 1.0, 0.2, 0.0012),   # March 1567 afternoon (235 deg)
        (ABANDON_F, 34, 610, 1.0, 1.1, 0.2, 0.0012),
        (1045, -15, 650, 1.0, 1.0, 0.3, 0.004),          # years pass: day, night, day...
        (1062, 50, 900, 1.0, 1.0, 0.18, 0.003),
        (1079, -15, 1010, 1.0, 1.0, 0.3, 0.004),
        (1096, 50, 1260, 1.0, 1.0, 0.18, 0.003),
        (1113, -15, 1370, 1.0, 1.0, 0.3, 0.004),
        (1130, 30, 1550, 1.0, 1.3, 0.35, 0.004),
        (P1, 25, 1560, 1.0, 1.3, 0.38, 0.004),
    ]
    for f, elev, az, air, dust, strength, mist in keys:
        sky_key(world, sun, f, elev, az, air=air, dust=dust, strength=strength, mist=mist)

    build_grade(scene)
    for f, gain, gamma, sat in ((1, (1.05, 1.0, 0.90), (1.02, 1.0, 0.96), 0.9),
                                (S1_RUSH[1], (1.02, 1.0, 0.95), (1.0, 1.0, 1.0), 1.0),
                                (SKIP_1567[1], (1.04, 1.0, 0.93), (1.0, 0.99, 0.97), 0.95),
                                (DECAY[0], (1.0, 0.98, 0.95), (1.0, 1.0, 1.0), 0.85),
                                (P1, (1.0, 0.99, 0.96), (1.0, 1.0, 1.0), 0.9)):
        grade_key(scene, f, gain=gain, gamma=gamma, saturation=sat)


# ---------------------------------------------------------------------------
# HUD
# ---------------------------------------------------------------------------

def build_hud(scene):
    hud = mt_hud.Hud(scene, P1)
    hud.era_bar()
    hud.title_card("TEQUESTA", "BISCAYNE BAY  ·  c. 2,000 YEARS AGO", 30, 270)

    hud.year("c. 2,000 YEARS AGO", 1, 515)
    hud.year("1513", 530, SKIP_1567[0] + 5, fout=0)
    hud.year_count(1513, 1567, SKIP_1567[0] + 5, SKIP_1567[1])
    hud.year("1567", SKIP_1567[1], ABANDON_F, fin=0, fout=0)
    hud.year_count(1567, 1570, ABANDON_F, ABANDON_F + 15)
    hud.year("1570", ABANDON_F + 15, COUNT_1836[0], fin=0, fout=0)
    hud.year_count(1570, 1836, COUNT_1836[0], P1 + 1)

    hud.population("POPULATION  ·  NOT RECORDED", 1, 530)
    hud.population("TEQUESTA AT CONTACT  ·  EST. 800 – 10,000", 530, SKIP_1567[1])
    hud.population("TEQUESTA  ·  EST. 800 – 10,000     SPANISH MISSION  ·  31", SKIP_1567[1], ABANDON_F)
    hud.population("TEQUESTA  ·  EST. 800 – 10,000     SPANISH MISSION  ·  0", ABANDON_F, 1095)
    hud.population("TEQUESTA  ·  LARGELY GONE BY THE MID-1700s", 1095, P1 + 1)

    hud.event_list([
        (150, "c. 2,000 YEARS AGO — ANCESTORS OF THE TEQUESTA LIVE AT THE RIVER MOUTH"),
        (420, "THE MIAMI CIRCLE — A 38-FT RING OF POST HOLES CUT INTO BEDROCK"),
        (600, "1513 — PONCE DE LEÓN REACHES ‘CHEQUESCHA’ (TRADITIONAL ACCOUNT)"),
        (800, "MARCH 1567 — MENÉNDEZ LEAVES 30 SOLDIERS AND JESUIT BROTHER FRANCISCO VILLAREAL"),
        (870, "THEY BUILD A PALISADE, 28 HUTS AND A CROSS CUT FROM A PINE"),
        (1040, "1570 — TRUST BREAKS AFTER THE CHIEF’S UNCLE IS KILLED; THE MISSION IS ABANDONED"),
    ])

    for f0, f1, txt in (
        (60, 160, "DUGOUT CANOE — A SINGLE HOLLOWED LOG"),
        (165, 255, "MEN FISH THE BAY FOR SHARK, SAILFISH, PORPOISE AND MANATEE"),
        (265, 325, "WOMEN AND CHILDREN GATHER CLAMS, CONCHS, OYSTERS AND TURTLE EGGS"),
        (335, 400, "CUPS, HAMMERS AND CHISELS ARE MADE FROM SHELL"),
        (405, 470, "COONTIE ROOT IS POUNDED INTO FLOUR, WASHED OF ITS TOXINS AND BAKED AS BREAD"),
        (475, 540, "ROOFS OF PALMETTO THATCH"),
        (650, 735, "THE FIRST RECORDED EUROPEAN VISIT TO BISCAYNE BAY"),
        (880, 935, "VILLAREAL LEARNED SOME TEQUESTA WORDS FROM THE CHIEF’S NEPHEW IN HAVANA"),
        (1070, 1135, "MANY TEQUESTA HAD LEFT FOR HAVANA BY 1711; FEW REMAINED BY THE MID-1700s"),
    ):
        hud.culture(txt, f0, f1)

    hud.subtitle("BROTHER FRANCISCO VILLAREAL", "Agua.", "(Water.)", AGUA_F, AGUA_F + 38)
    hud.subtitle("TEQUESTA YOUTH", "A… gua.", "", AGUA_F + 40, AGUA_F + 62)

    marks = [(1, "P01 S01 Tequesta: arrive by canoe"), (LAND_F, "canoe grounds"), (CUP_F, "hand-off: shell cup"),
             (S1_RUSH[0], "time rush"), (S2, "P01 S02 1513"), (SKIP_1567[0], "time rush to 1567"),
             (LOG_F, "log drop"), (NAIL_F, "hand-off: nail"), (AGUA_F, "Agua"), (ABANDON_F, "1570 abandoned"),
             (COUNT_1836[0], "count to 1836")]
    hud.ed.timeline_markers.clear()
    hud.markers(marks)
    scene.timeline_markers.clear()
    for f, n in marks:
        scene.timeline_markers.new(n, frame=f)
    return hud


# ---------------------------------------------------------------------------

def build():
    reset_cache()
    scene = get_scene(SCENE_3D)
    try:
        bpy.context.window.scene = scene
    except (AttributeError, RuntimeError):
        pass
    setup_render(scene, P0, P1, engine=ENGINE)
    root = scene.collection
    shared = get_collection("MT_SHARED", root)
    p01 = get_collection("MT_P01_Tequesta_Spanish", root)
    for c in (shared, p01):
        wipe_collection(c)
    purge_orphans()
    veg = get_collection("P01_Vegetation", p01)
    s1c = get_collection("P01_S1_Tequesta", p01)
    s2c = get_collection("P01_S2_Spanish", p01)

    pal = Palette()
    build_terrain(shared, pal)
    build_water(shared, pal)
    world = build_world()
    scene.world = world
    sun = build_sun(shared)
    build_mist(shared)
    rig = PovRig(scene, shared)
    arm, hand = build_pov_arm(shared, rig, pal)

    build_vegetation(veg, pal)
    s1 = build_scene1(s1c, pal)
    s2 = build_scene2(s2c, pal, s1)
    build_camera(rig, arm, hand, s1, s2)
    build_sky(scene, world, sun)
    build_hud(scene)
    scene.frame_set(1)
    print(f"[mt] Part 01 built: {len(scene.objects)} objects, frames {P0}-{P1}")
    return scene


def _stills(outdir, frames=(40, 240, 340, 380, 470, 520, 640, 800, 870, 950, 1100), percent=50):
    """Render finished frames (3D + HUD) from MIAMI_EDIT at `percent` size."""
    os.makedirs(outdir, exist_ok=True)
    ed = bpy.data.scenes["MIAMI_EDIT"]
    src = bpy.data.scenes[SCENE_3D]
    for s in (ed, src):
        s.render.resolution_percentage = percent
    ed.render.image_settings.file_format = "JPEG"
    for f in frames:
        src.frame_set(f)   # keep the 3D scene in step with the edit scene
        ed.frame_set(f)
        ed.render.filepath = os.path.join(outdir, f"p01_{f:04d}.jpg")
        with bpy.context.temp_override(scene=ed):
            bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    build()
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--stills" in argv:
        _stills(argv[argv.index("--stills") + 1])
