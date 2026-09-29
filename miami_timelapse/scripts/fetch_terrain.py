"""Build a land + bay-floor terrain grid for the Miami timelapse.

Sources
  LAND  USGS 3DEP 1 m lidar, FL_MiamiDade_D23 (2023), fallback FL_Peninsular_FDEM_2018.
        Read remotely (HTTP range requests on the COG overviews), so only a few MB move.
        Water in these tiles is hydro-flattened (a flat surface near 0 m), not sea floor.
  TOPO  USGS/NOAA topobathy lidar FL_TopobathyFLKeysNOAA_2019_D20 (real bay floor, patchy).
  BATH  NOAA NCEI Biscayne Bay (S200) estuarine bathymetric DEM, ~10 m, MLLW
        https://www.ngdc.noaa.gov/thredds/fileServer/regional/biscayne_bay_S200_2018.nc

Per cell:
  land lidar > LAND_MIN          -> land (lidar)
  else topobathy < WATER_MAX     -> bay floor (topobathy)
  else bathymetry present        -> bay floor (S200, shifted MLLW -> NAVD88)
  else land lidar present        -> lidar value
  else                           -> SEA_FILL (open ocean outside every survey)

Output: data/terrain/miami_dem_{RES}m.tif (EPSG:32617, metres, NAVD88), .png (16-bit
heightmap), .json (bounds, scale), and _source.png (which dataset filled each cell).
Usage: python3 fetch_terrain.py [RES_METRES] [path/to/biscayne_bay_S200_2018.nc]
"""
import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject, transform_bounds
from scipy.ndimage import distance_transform_edt

RES = int(sys.argv[1]) if len(sys.argv) > 1 else 5
BBOX = (25.65, -80.24, 25.82, -80.12)  # S, W, N, E  (wide frame incl. Key Biscayne)
DST_CRS = "EPSG:32617"
LAND_MIN = 0.6      # m NAVD88; hydro-flattened water and wet flats sit below this
WATER_MAX = 0.3     # m; topobathy cells below this are water bottom
MLLW_TO_NAVD88 = -0.3  # approx. offset at Miami (MLLW lies ~0.3 m below NAVD88); verify
SEA_FILL = -15.0     # deepest value used for unsurveyed open ocean
OCEAN_SLOPE = 0.01   # m of depth per m of distance from surveyed water (1%)
INLAND_WATER_DEPTH = 2.0  # m carved under hydro-flattened river/canal surfaces

BASE = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/"
TILES = ["x57y285", "x57y286", "x58y285", "x58y286", "x57y284", "x58y284"]
BATH_URL = "https://www.ngdc.noaa.gov/thredds/fileServer/regional/biscayne_bay_S200_2018.nc"

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "terrain"


def grid():
    s, w, n, e = BBOX
    left, bottom, right, top = transform_bounds("EPSG:4326", DST_CRS, w, s, e, n)
    width, height = int((right - left) / RES), int((top - bottom) / RES)
    return from_origin(left, top, RES, RES), width, height, (left, bottom, right, top)


def warp_into(path, transform, shape, overview=None):
    out = np.full(shape, np.nan, dtype=np.float32)
    kw = {"overview_level": overview} if overview is not None else {}
    with rasterio.open(path, **kw) as src:
        reproject(rasterio.band(src, 1), out, dst_transform=transform, dst_crs=DST_CRS,
                  src_nodata=src.nodata, dst_nodata=np.nan, resampling=Resampling.average)
    out[(out < -100) | (out > 1000)] = np.nan
    return out


def mosaic(projects, transform, shape):
    """First valid value wins across projects (in order) and tiles."""
    acc = np.full(shape, np.nan, dtype=np.float32)
    ovr = max(0, int(np.log2(RES)) - 1)  # COG overviews 2x,4x,8x: coarsest finer than RES
    for proj in projects:
        for tile in TILES:
            url = f"/vsicurl/{BASE}{proj}/TIFF/USGS_1M_17_{tile}_{proj}.tif"
            try:
                arr = warp_into(url, transform, shape, ovr)
            except rasterio.errors.RasterioIOError:
                continue
            fill = np.isnan(acc) & ~np.isnan(arr)
            acc[fill] = arr[fill]
            print(f"{proj} {tile}: +{fill.sum()} cells", file=sys.stderr)
    return acc


def main():
    transform, width, height, bounds = grid()
    shape = (height, width)

    land = mosaic(["FL_MiamiDade_D23", "FL_Peninsular_FDEM_2018_D19_DRRA"], transform, shape)
    topo = mosaic(["FL_TopobathyFLKeysNOAA_2019_D20"], transform, shape)

    bath_path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "cache" / "biscayne_bay_S200_2018.nc"
    if not bath_path.exists():
        bath_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading {BATH_URL}", file=sys.stderr)
        urllib.request.urlretrieve(BATH_URL, bath_path)
    bath = warp_into(str(bath_path), transform, shape) + MLLW_TO_NAVD88

    dem = np.full(shape, SEA_FILL, dtype=np.float32)
    src = np.zeros(shape, dtype=np.uint8)  # 0 sea fill, 1 land lidar, 2 topobathy lidar, 3 S200
    # Both lidar sets hydro-flatten water (the 2019 topobathy tiles hold a constant -0.5 m over
    # the bay), so lidar is trusted only for land; the bay floor comes from S200.
    rules = [
        (1, (land > LAND_MIN), land),
        (2, (topo > LAND_MIN), topo),
        (3, ~np.isnan(bath), bath),
        # inland water (river, canals, lakes) not in S200: carve below the flattened surface
        (1, ~np.isnan(land), np.where(land < WATER_MAX, land - INLAND_WATER_DEPTH, land)),
    ]
    done = np.zeros(shape, dtype=bool)
    for code, mask, values in rules:
        m = mask & ~done & ~np.isnan(values)
        dem[m], src[m] = values[m], code
        done |= m
    # open ocean beyond every survey: deepen with distance from the nearest surveyed cell
    dist_px, idx = distance_transform_edt(~done, return_indices=True)
    edge = dem[idx[0], idx[1]]
    ocean = ~done
    dem[ocean] = np.maximum(np.minimum(edge[ocean], -1.0) - dist_px[ocean] * RES * OCEAN_SLOPE, SEA_FILL)

    OUT.mkdir(parents=True, exist_ok=True)
    stem = OUT / f"miami_dem_{RES}m"
    with rasterio.open(f"{stem}.tif", "w", driver="GTiff", width=width, height=height, count=1,
                       dtype="float32", crs=DST_CRS, transform=transform, compress="deflate",
                       predictor=3, tiled=True) as dst:
        dst.write(dem, 1)
    lo, hi = float(dem.min()), float(dem.max())
    png16 = ((dem - lo) / (hi - lo) * 65535).round().astype(np.uint16)
    with rasterio.open(f"{stem}.png", "w", driver="PNG", width=width, height=height, count=1,
                       dtype="uint16") as dst:
        dst.write(png16, 1)
    with rasterio.open(f"{stem}_source.png", "w", driver="PNG", width=width, height=height,
                       count=1, dtype="uint8") as dst:
        dst.write(src * 80, 1)

    names = {0: "sea_fill", 1: "land_lidar_2023", 2: "topobathy_lidar_2019", 3: "noaa_S200_bathymetry"}
    meta = {
        "crs": DST_CRS, "resolution_m": RES, "width": width, "height": height,
        "bounds_utm": list(bounds), "bbox_wgs84_SWNE": BBOX,
        "min_m": lo, "max_m": hi, "vertical_datum": "NAVD88 (metres)",
        "png_to_metres": f"h = {lo:.4f} + value/65535 * {hi - lo:.4f}",
        "coverage_pct": {names[k]: round(float((src == k).mean() * 100), 2) for k in names},
        "thresholds": {"land_min_m": LAND_MIN, "water_max_m": WATER_MAX,
                       "mllw_to_navd88_m": MLLW_TO_NAVD88, "sea_fill_min_m": SEA_FILL,
                       "ocean_slope": OCEAN_SLOPE, "inland_water_depth_m": INLAND_WATER_DEPTH},
        "sources": [f"{BASE}FL_MiamiDade_D23/", f"{BASE}FL_TopobathyFLKeysNOAA_2019_D20/",
                    f"{BASE}FL_Peninsular_FDEM_2018_D19_DRRA/", BATH_URL],
        "note": "Present-day terrain. Pre-1905 coastline/islands must be edited using historical shorelines (see README).",
    }
    Path(f"{stem}.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta["coverage_pct"], indent=2))


if __name__ == "__main__":
    main()
