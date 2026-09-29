"""Prepare the pre-1836 ('natural') landscape for Act 1 from the present-day terrain.

Runs in normal Python (rasterio, scipy, numpy, pillow). Writes Blender-ready assets that
build_act1.py loads with numpy only, so the Blender side needs no extra packages.

What changes from today's terrain
  - Grid is resampled to lat/lon so Blender can place anything with one simple formula
    (x = (lon - LON0) * KX, y = (lat - LAT0) * KY); see act1_geo.json.
  - Man-made islands removed (Dodge/port, Watson, Venetian, Star, Palm, Hibiscus, Brickell Key,
    spoil islands) and causeways cut: only the natural land masses are kept
    (mainland, Miami Beach, Fisher Island, Virginia Key, Key Biscayne).
  - Government Cut (dredged 1905) filled: Fisher Island joins Miami Beach again.
  - Dredged channels and the port basin raised to natural bay depth (<= 4.5 m).
  - Highways, building pads and landfill mounds smoothed away; heights capped (ridge ~7 m).
  Known approximation: mainland bayfront fill (Bayfront Park etc.) is not removed.

Outputs (act1/assets/):
  terrain_20m.npy      float32 heights (m, sea level 0) on a ~20 m lat/lon grid (row 0 = north)
  landcover_5m.png     RGB colour texture for the terrain (land cover + water depth)
  landclass_5m.npy     uint8 class grid (see CLASSES) for placing things on the right ground
  trees.npz            tree points per type: x, y, z (m, local), variant
  act1_geo.json        origin, scale factors, grid sizes, class legend
"""
import json
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.warp import reproject
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parent.parent
DEM = ROOT / "data" / "terrain" / "miami_dem_5m.tif"
OUT = Path(__file__).resolve().parent / "assets"

S, W, N, E = 25.65, -80.24, 25.82, -80.12
LAT0, LON0 = 25.7715, -80.1885          # local origin: mouth of the Miami River
KY = 110574.0                            # m per degree latitude
KX = 111320.0 * np.cos(np.radians(LAT0))  # m per degree longitude at the origin
STEP_M = 5.0
rng = np.random.default_rng(1836)

CLASSES = {0: "deep water", 1: "bay", 2: "sand", 3: "mangrove", 4: "hammock",
           5: "pine rockland", 6: "glades/prairie"}
NATURAL_LAND = {  # seed points of land masses that existed before dredging (several per mass:
    # the river and canals split them into pieces after the causeway-cutting step)
    "mainland": [(25.790, -80.220), (25.750, -80.225), (25.715, -80.235), (25.760, -80.200)],
    "miami_beach": [(25.775, -80.133), (25.790, -80.130), (25.805, -80.128), (25.815, -80.125)],
    "fisher_island": [(25.7605, -80.1420)], "virginia_key": [(25.7360, -80.1560)],
    "key_biscayne": [(25.6900, -80.1620), (25.6720, -80.1580)],
}
BIG_LAND_KM2 = 3.0  # any remaining land piece this large is natural too (dredged islands are smaller)
HEIGHT_CAP = {"mainland": 7.0, "miami_beach": 4.0, "fisher_island": 3.0,
              "virginia_key": 2.5, "key_biscayne": 3.0}


def to_rc(lat, lon, shape):
    h, w = shape
    return int((N - lat) / (N - S) * h), int((lon - W) / (E - W) * w)


def disk(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    width = int(round((E - W) * KX / STEP_M))
    height = int(round((N - S) * KY / STEP_M))
    geo_t = from_bounds(W, S, E, N, width, height)
    dem = np.zeros((height, width), np.float32)
    with rasterio.open(DEM) as src:
        reproject(rasterio.band(src, 1), dem, dst_transform=geo_t, dst_crs="EPSG:4326",
                  resampling=Resampling.bilinear)
    shape = dem.shape

    # ---- natural land mask -------------------------------------------------------------
    land_now = dem > 0.6
    opened = ndi.binary_opening(land_now, structure=disk(8))    # cut causeways (< ~80 m wide)
    labels, nlab = ndi.label(opened)
    _, (nir, nic) = ndi.distance_transform_edt(labels == 0, return_indices=True)
    keep = np.zeros(shape, bool)
    comp_of = {}
    for name, seeds in NATURAL_LAND.items():
        comp = np.zeros(shape, bool)
        for la, lo in seeds:
            r, c = to_rc(la, lo, shape)
            lab = labels[r, c] or labels[nir[r, c], nic[r, c]]  # seed in water: nearest land
            comp |= labels == lab
        comp_of[name] = comp
        keep |= comp
    sizes = ndi.sum(np.ones(shape), labels, index=np.arange(1, nlab + 1)) * STEP_M * STEP_M / 1e6
    for lab in np.nonzero(sizes >= BIG_LAND_KM2)[0] + 1:
        piece = labels == lab
        if not (keep & piece).any():
            keep |= piece
            comp_of["mainland"] |= piece
    # restore shoreline detail lost by the opening, but only next to kept land masses
    land = land_now & ndi.binary_dilation(keep, structure=disk(8))
    # Government Cut: bridge Miami Beach and Fisher Island (before 1905 they were one)
    mb_f = comp_of["miami_beach"] | comp_of["fisher_island"]
    bridged = ndi.binary_closing(mb_f, structure=disk(45))
    r0, c0 = to_rc(25.775, -80.150, shape)
    r1, c1 = to_rc(25.755, -80.120, shape)
    box = np.zeros(shape, bool)
    box[r0:r1, c0:c1] = True
    cut_fill = bridged & box & ~land
    land |= cut_fill
    # small enclosed water bodies (golf-course ponds, borrow pits, marinas cut into land) -> land
    wlab, nw = ndi.label(~land)
    wsizes = ndi.sum(np.ones(shape), wlab, index=np.arange(1, nw + 1)) * STEP_M * STEP_M / 1e6
    small = np.isin(wlab, np.nonzero(wsizes < 0.4)[0] + 1)
    land |= small

    # ---- land heights: remove roads/pads/mounds, cap by land mass ---------------------------
    idx = ndi.distance_transform_edt(~land, return_distances=False, return_indices=True)
    h = dem[idx[0], idx[1]]                                  # extend land values into water
    h = ndi.grey_opening(h, size=(13, 13))                   # flatten narrow raised features
    h = ndi.gaussian_filter(h, 3)
    cap = np.full(shape, 7.0, np.float32)
    for name, comp in comp_of.items():
        cap[ndi.binary_dilation(comp, structure=disk(8))] = HEIGHT_CAP[name]
    h = np.clip(h, 0.3, cap)
    h[cut_fill] = np.maximum(h[cut_fill], 1.0)

    # ---- water depths: natural bay ---------------------------------------------------------
    water = ~land
    was_land = water & land_now                               # removed islands / fill
    ok = water & ~was_land & (dem < 0)
    # removed islands: fill by normalized convolution (smooth blend of the surrounding bay floor)
    wd = np.where(ok, np.clip(dem, -6.0, -0.4), 0).astype(np.float32)
    okf = ok.astype(np.float32)
    for sigma in (8, 30, 90):
        num, den = ndi.gaussian_filter(wd * okf, sigma), ndi.gaussian_filter(okf, sigma)
        fill = (den > 1e-3) & ~ok & (okf == 0)
        wd[fill] = num[fill] / den[fill]
        okf[fill] = 1.0
    wd = ndi.gaussian_filter(np.clip(wd, -6.0, -0.4), 3)
    ocean = np.zeros(shape, bool)                             # open Atlantic: east of the barrier
    ocean[:, int(0.85 * shape[1]):] = True
    ocean &= water & (dem < -6)
    wd = np.where(ocean, dem, np.maximum(wd, -4.5))           # fill dredged channels in the bay
    wd = np.where(water, ndi.gaussian_filter(wd, 10), wd)     # soften survey-edge seams
    east = np.zeros(shape, bool)                              # open-ocean strip: blur the hard
    east[:, int(0.78 * shape[1]):] = True                     # edge where the bay survey ends
    wd = np.where(water & east & ~ndi.binary_dilation(land, structure=disk(20)),
                  ndi.gaussian_filter(wd, 60), wd)
    elev = np.where(land, h, np.minimum(wd, -0.4)).astype(np.float32)

    # ---- land cover classes ----------------------------------------------------------------
    dist_sea = ndi.distance_transform_edt(land) * STEP_M      # m to nearest water (0 on water)
    cls = np.zeros(shape, np.uint8)
    cls[water] = 1
    cls[water & (elev < -4.0)] = 0
    barrier = land & ~ndi.binary_dilation(comp_of["mainland"], structure=disk(8))
    # sand: barrier-island land within 70 m of the open ocean (water east of each row's
    # easternmost barrier land) or at the southern tip of Key Biscayne (Cape Florida beach)
    cols = np.arange(shape[1])[None, :]
    east_edge = np.where(barrier.any(1), shape[1] - 1 - np.argmax(barrier[:, ::-1], 1), shape[1])
    open_ocean = water & (cols > east_edge[:, None])
    dist_ocean = ndi.distance_transform_edt(~open_ocean) * STEP_M
    cls[barrier & (dist_ocean < 70)] = 2
    rest = land & (cls == 0)
    cls[rest & (elev < 1.2) & (dist_sea < 400)] = 3
    cls[rest & (cls == 0) & (elev < 1.5) & (dist_sea > 1500)] = 6
    cls[rest & (cls == 0) & (elev > 3.0)] = 5
    cls[rest & (cls == 0)] = 4

    # ---- colour texture --------------------------------------------------------------------
    pal = {2: (226, 206, 160), 3: (46, 84, 44), 4: (74, 112, 50),
           5: (122, 138, 66), 6: (140, 140, 78)}
    img = np.zeros(shape + (3,), np.float32)
    for k, c in pal.items():
        img[cls == k] = c
    d = np.clip(-elev, 0, 8)
    stops = [(0, (132, 206, 192)), (1, (86, 176, 182)), (3, (44, 118, 156)),
             (5, (28, 80, 126)), (8, (20, 52, 96))]
    for (d0, c0), (d1, c1) in zip(stops, stops[1:]):
        m = water & (d >= d0) & (d <= d1)
        t = ((d - d0) / (d1 - d0))[m][:, None]
        img[m] = np.array(c0) * (1 - t) + np.array(c1) * t
    noise = ndi.gaussian_filter(rng.normal(0, 1, shape), 6)
    noise = noise / (noise.std() + 1e-6)
    img[land] *= (1 + 0.06 * noise[land])[:, None]
    img[land] *= (1 + 0.05 * rng.normal(0, 1, land.sum()))[:, None]
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(OUT / "landcover_5m.png")
    np.save(OUT / "landclass_5m.npy", cls)

    # ---- 20 m mesh heights -----------------------------------------------------------------
    hh, ww = shape[0] // 4 * 4, shape[1] // 4 * 4
    t20 = elev[:hh, :ww].reshape(hh // 4, 4, ww // 4, 4).mean(axis=(1, 3)).astype(np.float32)
    np.save(OUT / "terrain_20m.npy", t20)

    # ---- trees -----------------------------------------------------------------------------
    # density = trees per m^2 of that class; variant 0-2 = small/medium/large
    density = {"pine": (5, 1 / 700), "hammock": (4, 1 / 260), "mangrove": (3, 1 / 220),
               "palm": (6, 1 / 3000)}
    cell = STEP_M * STEP_M
    trees = {}
    lat_of = N - (np.arange(shape[0]) + 0.5) / shape[0] * (N - S)
    lon_of = W + (np.arange(shape[1]) + 0.5) / shape[1] * (E - W)
    for name, (k, dens) in density.items():
        rr, cc = np.nonzero(cls == k)
        if name == "palm":  # palms also scatter through the hammock
            r2, c2 = np.nonzero(cls == 4)
            rr, cc = np.concatenate([rr, r2]), np.concatenate([cc, c2])
        pick = rng.random(rr.size) < dens * cell
        rr, cc = rr[pick], cc[pick]
        jr, jc = rng.random(rr.size) - 0.5, rng.random(rr.size) - 0.5
        lat = lat_of[rr] - jr * (N - S) / shape[0]
        lon = lon_of[cc] + jc * (E - W) / shape[1]
        trees[name] = np.stack([(lon - LON0) * KX, (lat - LAT0) * KY, elev[rr, cc],
                                rng.integers(0, 3, rr.size)], axis=1).astype(np.float32)
    np.savez_compressed(OUT / "trees.npz", **trees)

    geo = {"bbox_SWNE": [S, W, N, E], "lat0": LAT0, "lon0": LON0, "kx": KX, "ky": KY,
           "grid_5m": list(shape), "grid_20m": list(t20.shape),
           "extent_m": {"x_min": (W - LON0) * KX, "x_max": (E - LON0) * KX,
                        "y_min": (S - LAT0) * KY, "y_max": (N - LAT0) * KY},
           "terrain_20m_extent_m": {"x_min": (W - LON0) * KX, "x_max": (W - LON0) * KX + t20.shape[1] * 4 * (E - W) * KX / shape[1],
                                    "y_max": (N - LAT0) * KY, "y_min": (N - LAT0) * KY - t20.shape[0] * 4 * (N - S) * KY / shape[0]},
           "classes": CLASSES, "tree_counts": {k: int(v.shape[0]) for k, v in trees.items()},
           "land_masses_kept": list(NATURAL_LAND)}
    (OUT / "act1_geo.json").write_text(json.dumps(geo, indent=2))
    print(json.dumps({k: geo[k] for k in ("grid_5m", "grid_20m", "tree_counts")}, indent=2))


if __name__ == "__main__":
    main()
