# Miami: Walking Through Time — Blender build

**Part 01:** c. 2,000 years ago → 1513 → 1567–1570 · 0:00–0:38 · frames 1–1140 · 1920×1080 @ 30 fps

Built and checked in Blender 4.2 LTS; the scripts guard the API changes in 4.4+ and 5.x.

## Render it
1. Open `../MIAMI_P01_Tequesta_Spanish.blend`.
2. Make sure **MIAMI_EDIT** is the active scene (top-right scene selector). It plays the 3D scene (`MIAMI_3D`) with the HUD on top.
3. Set Output Properties > Output to your folder and format (PNG sequence recommended), then **Render > Render Animation**.

The file is set up for **EEVEE**. For Cycles, set `MIAMI_3D` > Render Engine to Cycles (or rebuild with the environment variable `MT_ENGINE=CYCLES`).

## What's in the file
| Scene | Contents |
|---|---|
| `MIAMI_3D` | Terrain, river mouth, bay, vegetation, the Tequesta camp and town, the Miami Circle house, canoes, the 1513 ships, the 1567 stockade, people, POV camera rig, sky and colour grade |
| `MIAMI_EDIT` | Video Sequencer strips: the era bar (top), year and population (bottom centre), events list (bottom left), culture captions (bottom right), subtitles, title card, timeline markers |

### Camera (first-person)
`POV_Rig` › `POV_Look` (aims at `POV_Target`) › `POV_Bob` › `POV_Shake` › `POV_Impact` › `POV_Cam` (22 mm).
- **Footsteps and canoe sway:** F-curve modifiers on `POV_Bob`.
- **Jolts:** keyframes on `POV_Impact` for the canoe grounding (f232), the first step (f258) and the log hitting the ground (f862).
- **Shakes:** noise modifiers on `POV_Shake`.
- **Time rushes** between eras: a soft rumble plus a lens breathe.
- **Explosions (later parts):** `PovRig.blast()` combines a kick, a heavy shake and an FOV punch.
- **Turning your head:** move `POV_Target`.

### Hands and hand-offs
`POV_ArmR` is a placeholder forearm parented to the camera; `POV_HandR` is the grip point.
- `HANDOFF_ShellCup` blends from the Tequesta woman's hand to yours at f338, and you drink at f375.
- `HANDOFF_Nail` blends from Villareal's hand at f946.
- Both use Copy Location constraints (`HOLD_FROM` → `HOLD_TO`), so their rotation stays keyable.

## Swap in BlenderKit and Human Generator
Every placeholder has a custom property `asset_tag`. To swap:
1. Import the real asset into a collection named `LIB_<tag>`, e.g. `LIB_sabal_palm`, `LIB_mangrove`, `LIB_human_s2_villareal`. Then exclude that collection in the Outliner.
2. In the Scripting workspace, run:
   ```python
   import sys; sys.path.insert(0, r"<path to this folder>")
   import bpy, mt_common
   mt_common.swap_proxies(bpy.data.scenes["MIAMI_3D"])
   ```
   - Instances are parented to the placeholders, so they follow their animation and show/hide timing.
   - Placeholder meshes move to `MT_REPLACED_PROXIES`, which is hidden in renders.
   - `mt_common.unswap_proxies(scene)` undoes the swap.
3. **Human Generator characters:** make one per `human_*` tag, then pose or animate the rig with Mixamo or HG poses. The placeholder arm animation does not transfer. Line up the hand-off sockets (`*_Hand_r`) with the character's hand bone.

| Tag | BlenderKit search |
|---|---|
| `sabal_palm` | "sabal palm", "cabbage palm" |
| `mangrove` | "red mangrove" |
| `sea_grape` | "sea grape" |
| `saw_palmetto` | "saw palmetto" |
| `slash_pine` | "slash pine", "pine tree" |
| `coontie` | "zamia", "cycad" |
| `tequesta_house` | build from "thatch roof" materials; it is a reconstruction guess |
| `dugout_canoe` | "dugout canoe" |
| `spanish_nao` | "caravel", "galleon 16th century" |
| `spanish_longboat` | "rowboat wooden" |
| `palisade_logs` | keep the placeholder (it carries the rise and decay shape keys); give it a BlenderKit bark material |
| Materials `MT_*` | drag BlenderKit materials onto them: sand, palmetto thatch, bark, calm sea water |

**People to create in Human Generator:**
- **Tequesta:** shellfish-gatherer woman, two children, coontie woman (kneeling), canoe carver, elder, paddler, fishermen, villagers, 1513 watchers, 1567 youth, elder and visitors. Clothing: palmetto-fibre breechcloths for men, Spanish-moss skirts for women, very little else.
- **Spanish:** six soldiers (morion helmet, breastplate, hose, one arquebus), and Brother Francisco Villareal (black Jesuit habit, slate in his left hand).

Please consult HistoryMiami or tribal historic-preservation staff on how the Tequesta are depicted. No Tequesta words are invented; only Spanish is spoken ("Agua").

## Rebuild or tweak
Edit `build_part01_tequesta_spanish.py` and run it in Blender's Scripting workspace (Open › Run Script), or:
```
blender -b -P build_part01_tequesta_spanish.py
```
Rebuilding replaces `MIAMI_3D`/`MIAMI_EDIT` contents; swapped assets must be swapped again.

| To change | Where |
|---|---|
| Timing | Constants at the top: `LAND_F`, `CUP_F`, `SKIP_1567`, `NAIL_F`, … |
| Walk path | `build_camera()` → `rig.path([...])` |
| Where you look | `build_camera()` → `look_at` list (heights are metres above ground) |
| Sky, sun, mist per era | `build_sky()` keys: frame, elevation°, azimuth°, air, dust, strength, mist |
| HUD text | `build_hud()` |
| Fonts | Drop `Cinzel-Regular.ttf` and `CormorantGaramond-Medium.ttf` (Google Fonts, OFL) into `fonts/` and rebuild |

**Sky direction check:** if the sun disc in the sky and the sun lamp's shadows disagree, set `SKY_AZIMUTH_OFFSET_DEG` in `mt_common.py` (try 90 or −90) and rebuild.

## Sources
Facts on screen come from `../ERA_BIBLE.md` (scenes 1–2). The population range (Tequesta at contact, est. 800–10,000) is from [Wikipedia: Tequesta](https://en.wikipedia.org/wiki/Tequesta). The shape of the Tequesta house and the building on the Miami Circle are design guesses; the ring itself is documented.
