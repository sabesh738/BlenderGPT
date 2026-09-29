"""Clip NOAA historical shoreline surveys (T-sheets) to the Miami frame, one GeoJSON per project.

Input : data/historical/shorelines/<PROJECT>.zip  (download from https://nsde.ngs.noaa.gov/downloads/<PROJECT>.zip)
Output: data/historical/shorelines_<PROJECT>.geojson  (WGS84 lines; attributes: date, kind)
        data/historical/shorelines_index.json          (project -> survey dates, feature counts)

Projects: EC19B01 (1913), EC19B03 (1927-28), FL3502 (1935), FL4501 (1945-47), PH7113 (1974-76).
'kind' comes from the survey ATTRIBUTE, e.g. "Natural.Mean High Water", "Man-made.Bulkhead Or Sea Wall",
"Natural.Mangrove Or Cypress" -- mangrove edges show the pre-dredging swamp outline.
"""
import json
import zipfile
from pathlib import Path

import pyogrio
from shapely.geometry import box, mapping

S, W, N, E = 25.65, -80.24, 25.82, -80.12
H = Path(__file__).resolve().parent.parent / "data" / "historical"
PROJECTS = ["EC19B01", "EC19B03", "FL3502", "FL4501", "PH7113"]
frame = box(W, S, E, N)

index = {}
for proj in PROJECTS:
    zp = H / "shorelines" / f"{proj}.zip"
    if not zp.exists():
        print("missing", zp)
        continue
    folder = zp.with_suffix("")
    zipfile.ZipFile(zp).extractall(folder)
    df = pyogrio.read_dataframe(folder / "historicl1.shp").to_crs(4326)
    feats, dates = [], set()
    for _, row in df.iterrows():
        g = row.geometry
        if g is None or not g.intersects(frame):
            continue
        g = g.intersection(frame)
        if g.is_empty:
            continue
        date = str(row.get("SRC_DATE") or "")
        dates.add(date[:4])
        feats.append({"type": "Feature", "geometry": mapping(g),
                      "properties": {"project": proj, "date": date, "kind": row.get("ATTRIBUTE"),
                                     "source": row.get("SOURCE_ID")}})
    (H / f"shorelines_{proj}.geojson").write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
    index[proj] = {"survey_years": sorted(d for d in dates if d), "features_in_frame": len(feats)}
    print(proj, index[proj])

(H / "shorelines_index.json").write_text(json.dumps(index, indent=2))
