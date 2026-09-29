# Act 1: Before the City (500 BC to 1836)

A 2 min 55 s sequence: the Tequesta at the river mouth, the Spanish, the depopulation of the bay, the first settlers, the Cape Florida Lighthouse, the plantation, and the 1836 Seminole attack on the lighthouse. It ends with Fort Dallas being built.

| File | Role |
|---|---|
| `act1_timeline.json` | **The script.** 23 beats with times, captions, camera shots, lighting keys, year and population counters. Edit this to re-time or re-word anything; the other files read it. |
| `prep_act1.py` | Turns today's terrain into the 1836 landscape: removes dredged islands and causeways, refills Government Cut and dredged channels, smooths away roads, paints land cover (pine rockland, hammock, mangrove, glades, beach, bay depths), scatters about 215,000 trees. |
| `assets/` | Output of `prep_act1.py`: 20 m terrain grid, 5 m colour texture, land-cover classes, tree points, geo reference. |
| `build_act1.py` | Builds and animates the whole act in Blender: terrain, water, sky and sun, camera moves, Tequesta village (grows, burns in 1567, empties by 1763), Miami Circle, canoes, Spanish ships, stockades, settlers, plantation, lighthouse and the attack, Fort Dallas. |
| `overlay.py` | Adds the year counter, population counter and captions to the rendered frames and encodes the MP4. |

## Run it on your PC (Blender 4.2 or newer)
```bash
cd miami_timelapse/act1
python3 prep_act1.py                     # once; needs rasterio, scipy, pillow (see ../README.md)
blender -b -P build_act1.py -- --save act1.blend
```
Then open `act1.blend` and render with Eevee (fast, needs a GPU) or Cycles. For a headless Cycles render:
```bash
blender -b -P build_act1.py -- --anim renders/frames --res 1920x1080 --samples 64
python3 overlay.py renders/frames act1.mp4
```
Useful options: `--stills DIR` (one frame per beat, a quick storyboard), `--step 3` (every 3rd frame, an animatic), `--start/--end` seconds (render one section), `--res`, `--samples`. Frame rendering can be resumed: frames already on disk are skipped.

## Historical choices made in the scene
- **Coastline**: natural land masses only (mainland, Miami Beach with Fisher Island attached, Virginia Key, Key Biscayne). The mainland's modern bayfront fill (Bayfront Park, Biscayne Boulevard) is **not** removed, because no surveyed pre-1896 downtown shoreline was found.
- **Village**: huts on raised platforms with palmetto-thatch roofs (the sources describe wooden-post houses with raised floors). The site is at the north bank of the river mouth, with a smaller cluster at Brickell Point around the Miami Circle.
- **1567 stockade**: sources disagree on which bank it stood on. It's placed on the north bank beside the village.
- **Spanish ships** enter the bay south of Key Biscayne past Cape Florida, because Government Cut didn't exist before 1905.
- **Attackers at the lighthouse**: about 12 figures arriving by boat. Accounts range from 12 to 40.
- **Population counter**: 800 (low end of the Tequesta estimate), 180 in 1743 (Spanish count), 0 after 1763. The 20 settlers and 80 plantation residents are illustrative. The counter shows "est." until 1743.
- **Scale**: heights ×3 and objects ×1.6–4 so they read from the air, as in the reference videos.
