"""Join footprints to parcels and Overture -> one building table with year, height, floors.

Input : data/buildings/footprints_raw.geojson, parcels_raw.geojson, condo_stats.json
        (fetch_buildings.py) and overture_buildings.geojson (fetch_overture_heights.py)
Output: data/buildings/buildings.geojson       - footprint polygons + attributes
        data/buildings/buildings_summary.json  - coverage stats, buildings per decade

Attributes per building:
  year        construction year: parcel YEAR_BUILT, or for condo towers the earliest unit year
  year_src    "parcel" | "condo_units" | "curated" (named landmark in structures.json) | "none"
  height_m    best available height (metres)
  height_src  "overture" (OSM-tagged) | "curated" (structures.json) | "county" | "podium_guess" (secondary piece of a split
              tower, capped at 25 m) | "overture_floors" | "parcel_floors" | "none"
  floors      floor count (Overture, else parcel/condo records)
  name        building name when OSM has one (e.g. "Panorama Tower")
  use         Property Appraiser use description (SINGLE FAMILY, CONDOMINIUM, OFFICE...)
"""
import json
from collections import Counter
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.strtree import STRtree

D = Path(__file__).resolve().parent.parent / "data" / "buildings"
FT = 0.3048
FLOOR_M = 3.2  # metres per storey when only a floor count is known
PODIUM_M = 25.0  # height given to secondary pieces of a split tower footprint


def load(name):
    p = D / name
    return json.loads(p.read_text())["features"] if p.exists() else []


def valid(geom):
    g = shape(geom)
    return g if g.is_valid else g.buffer(0)


fp = load("footprints_raw.geojson")
pc = [f for f in load("parcels_raw.geojson") if f.get("geometry")]
ov = [f for f in load("overture_buildings.geojson") if f.get("geometry")]
condo_path = D / "condo_stats.json"
condos = json.loads(condo_path.read_text()) if condo_path.exists() else {}

parcel_geoms = [valid(f["geometry"]) for f in pc]
parcel_props = [f["properties"] for f in pc]
parcel_tree = STRtree(parcel_geoms)
ov_geoms = [valid(f["geometry"]) for f in ov]
ov_props = [f["properties"] for f in ov]
ov_tree = STRtree(ov_geoms)


def best_parcel(pt):
    """Parcel containing the point; among stacked parcels prefer one with a year."""
    hits = [i for i in parcel_tree.query(pt) if parcel_geoms[i].contains(pt)]
    if not hits:
        return None
    hits.sort(key=lambda i: (not (parcel_props[i].get("YEAR_BUILT") or 0) > 0,
                             -(parcel_props[i].get("FLOOR_COUNT") or 0)))
    return parcel_props[hits[0]]


def best_overture(g):
    """(index, overlap area) of the matching Overture building, or (None, 0).
    Candidates overlap >= 50% of the smaller shape. OSM often has a tower outline and a
    podium outline inside one county footprint, so the tallest candidate wins; without
    heights, the largest overlap wins."""
    cands = []
    for i in ov_tree.query(g):
        inter = g.intersection(ov_geoms[i]).area
        if inter / max(min(g.area, ov_geoms[i].area), 1e-12) >= 0.5:
            cands.append((ov_props[i].get("height") or 0, inter, i))
    if not cands:
        return None, 0.0
    _, area, i = max(cands)
    return i, area


# Curated landmark years (structures.json) override missing/odd parcel years for named buildings
curated = {s["name"].lower(): s for s in json.loads(
    (D.parent / "structures.json").read_text())["structures"]
    if s.get("remove") is None and s.get("appear", 0) >= 1896}  # standing modern buildings only


def curated_entry(name):
    if not name:
        return {}
    n = name.lower()
    for k, s in curated.items():
        if n == k or k.split(" (")[0] == n or (len(n) >= 8 and (n in k or k in n)):
            return s
    return {}


# The county often splits one tower into several polygons (tower + podium). Give the Overture
# height only to the piece overlapping it most; the other pieces are treated as podium.
matches = []
for f in fp:
    if f.get("geometry"):
        g = valid(f["geometry"])
        matches.append((f, g, *best_overture(g)))
main_piece = {}
for k, (_, _, oi, area) in enumerate(matches):
    if oi is not None and area > main_piece.get(oi, (None, -1))[1]:
        main_piece[oi] = (k, area)

out, decades, stats = [], Counter(), Counter()
for k, (f, g, oi, _) in enumerate(matches):
    p = f["properties"]
    par = best_parcel(g.representative_point()) or {}
    o = ov_props[oi] if oi is not None else {}
    is_main = oi is not None and main_piece[oi][0] == k

    # --- year ---
    year, year_src = par.get("YEAR_BUILT") or 0, "parcel"
    condo = condos.get(par.get("FOLIO") or "")
    if condo and not 1800 <= year <= 2026:
        # earliest valid unit year = construction year (later years are unit renovations)
        years = [y for y in (condo.get("year_min"), condo.get("year")) if y and 1800 <= y <= 2026]
        if years:
            year, year_src = min(years), "condo_units"
    year = year if 1800 <= year <= 2026 else None
    cur = curated_entry(o.get("name"))
    cy = cur.get("appear")
    if cy and (year is None or abs(year - cy) > 3):
        year, year_src = cy, "curated"

    # --- floors and height ---
    parcel_floors = par.get("FLOOR_COUNT") or (condo or {}).get("floors") or None
    floors = o.get("num_floors") or parcel_floors
    if o.get("height") and is_main:
        h, h_src = o["height"], "overture"
    elif cur.get("height_ft") and is_main:
        h, h_src = cur["height_ft"] * FT, "curated"
    elif (p.get("HEIGHT") or 0) > 0:
        h, h_src = p["HEIGHT"] * FT, "county"
    elif o.get("height"):
        # secondary piece of a split tower: podium, capped
        h, h_src = min(o["height"], PODIUM_M), "podium_guess"
    elif o.get("num_floors"):
        h, h_src = o["num_floors"] * FLOOR_M, "overture_floors"
    elif parcel_floors and (par.get("BUILDING_COUNT") or 1) <= 1:
        # a parcel's floor count describes its main building; skip multi-building parcels
        h, h_src = parcel_floors * FLOOR_M, "parcel_floors"
    else:
        h, h_src = None, "none"

    stats[f"year_{year_src if year else 'none'}"] += 1
    stats[f"height_{h_src}"] += 1
    if year:
        decades[f"{year // 10 * 10}s"] += 1
    out.append({"type": "Feature", "geometry": mapping(g), "properties": {
        "id": p.get("UNIQUEID") or p.get("OBJECTID"),
        "year": year, "year_src": year_src if year else "none",
        "height_m": round(h, 1) if h else None, "height_src": h_src,
        "floors": floors, "name": o.get("name"),
        "use": par.get("DOR_DESC"), "fp_type": p.get("TYPE"),
    }})

(D / "buildings.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": out}))
summary = {"buildings": len(out), **dict(sorted(stats.items())),
           "per_decade": dict(sorted(decades.items())),
           "tallest": sorted(({"name": f["properties"]["name"], "height_m": f["properties"]["height_m"],
                               "year": f["properties"]["year"]} for f in out if f["properties"]["height_m"]),
                             key=lambda x: -x["height_m"])[:15]}
(D / "buildings_summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary, indent=2))
