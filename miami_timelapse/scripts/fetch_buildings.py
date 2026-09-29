"""Download Miami building footprints + parcel year-built data for the timelapse.

Sources (public, Miami-Dade County GIS):
  - BuildingFootprint2D (2024): footprint polygons with HEIGHT (ft)
  - Property Appraiser parcels (MD_LandInformation layer 26): YEAR_BUILT, FLOOR_COUNT, DOR_DESC

Owner names and mailing addresses are deliberately NOT requested.

Output (in data/buildings/):
  footprints_raw.geojson   all footprints in the bbox
  parcels_raw.geojson      parcels in the bbox (non-personal fields only)

Usage: python3 fetch_buildings.py [south west north east]
"""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

BBOX = (25.73, -80.24, 25.82, -80.12)  # main frame: S, W, N, E

FOOTPRINTS = ("https://services.arcgis.com/8Pc9XBTAsYuxx9Ny/arcgis/rest/services/"
              "BuildingFootprint2D_gdb/FeatureServer/0/query")
PARCELS = "https://gis.miamidade.gov/arcgis/rest/services/MD_LandInformation/MapServer/26/query"

OUT = Path(__file__).resolve().parent.parent / "data" / "buildings"


def fetch_all(url, fields, bbox, page):
    s, w, n, e = bbox
    base = {
        "where": "1=1",
        "geometry": f"{w},{s},{e},{n}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": fields,
        "outSR": 4326,
        "returnGeometry": "true",
        "f": "geojson",
        "orderByFields": "OBJECTID",
    }
    features, offset = [], 0
    while True:
        q = dict(base, resultOffset=offset, resultRecordCount=page)
        req = url + "?" + urllib.parse.urlencode(q)
        for attempt in range(5):
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    data = json.load(r)
                break
            except Exception as exc:  # network hiccup: back off and retry
                if attempt == 4:
                    raise
                time.sleep(2 ** attempt)
                print(f"  retry {attempt + 1}: {exc}", file=sys.stderr)
        batch = data.get("features", [])
        features.extend(batch)
        print(f"  {url.split('/services/')[1][:40]}... {len(features)}", file=sys.stderr)
        if len(batch) < page:
            return features
        offset += page


PROPERTY_POINTS = "https://gis.miamidade.gov/arcgis/rest/services/MD_LandInformation/MapServer/24/query"


def fetch_condo_stats(bbox):
    """Condo towers sit on 'REFERENCE FOLIO' parcels with no year; the year and floor count
    live on the individual unit records. Aggregate units by PARENT_FOLIO."""
    s, w, n, e = bbox
    stats = [{"statisticType": "max", "onStatisticField": "YEAR_BUILT", "outStatisticFieldName": "year"},
             {"statisticType": "min", "onStatisticField": "YEAR_BUILT", "outStatisticFieldName": "year_min"},
             {"statisticType": "max", "onStatisticField": "FLOOR_COUNT", "outStatisticFieldName": "floors"},
             {"statisticType": "count", "onStatisticField": "FOLIO", "outStatisticFieldName": "units"}]
    # The server ignores resultOffset on statistics queries, so page by folio instead.
    rows, last = {}, ""
    while True:
        q = {"where": f"PARENT_FOLIO IS NOT NULL AND PARENT_FOLIO > '{last}'",
             "geometry": f"{w},{s},{e},{n}", "geometryType": "esriGeometryEnvelope", "inSR": 4326,
             "outStatistics": json.dumps(stats), "groupByFieldsForStatistics": "PARENT_FOLIO",
             "orderByFields": "PARENT_FOLIO", "f": "json"}
        with urllib.request.urlopen(PROPERTY_POINTS, urllib.parse.urlencode(q).encode(), timeout=180) as r:
            data = json.load(r)
        batch = [f["attributes"] for f in data.get("features", [])]
        for a in batch:
            rows[a.pop("PARENT_FOLIO")] = a
        print(f"  condo groups {len(rows)}", file=sys.stderr)
        if not batch or not data.get("exceededTransferLimit"):
            return rows
        new_last = max(rows)
        if new_last <= last:  # no progress: stop rather than loop forever
            return rows
        last = new_last


def save(name, features):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_text(json.dumps({"type": "FeatureCollection", "features": features}))
    print(f"wrote {path} ({len(features)} features)")


if __name__ == "__main__":
    bbox = tuple(map(float, sys.argv[1:5])) if len(sys.argv) == 5 else BBOX
    condos = fetch_condo_stats(bbox)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "condo_stats.json").write_text(json.dumps(condos))
    print(f"wrote condo_stats.json ({len(condos)} condo buildings)")
    if "--condos-only" in sys.argv:
        sys.exit()
    save("footprints_raw.geojson",
         fetch_all(FOOTPRINTS, "OBJECTID,UNIQUEID,TYPE,HEIGHT,YEARUPDATE,SOURCE", bbox, 2000))
    save("parcels_raw.geojson",
         fetch_all(PARCELS, "OBJECTID,FOLIO,PARENT_FOLIO,CONDO_FLAG,DOR_CODE_CUR,DOR_DESC,"
                            "FLOOR_COUNT,UNIT_COUNT,BUILDING_COUNT,YEAR_BUILT", bbox, 1000))
