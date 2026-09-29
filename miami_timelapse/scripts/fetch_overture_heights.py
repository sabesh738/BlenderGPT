"""Download Overture Maps buildings (heights, floors, names) for the Miami frame.

Overture merges OpenStreetMap, Microsoft and other footprints; OSM contributors have
tagged heights/levels for most of Miami's towers. Used to fix building heights, which the
county footprint layer mostly lacks. Reads remote GeoParquet with DuckDB (bbox filter).

Output: data/buildings/overture_buildings.geojson
"""
import sys
from pathlib import Path

import duckdb

RELEASE = sys.argv[1] if len(sys.argv) > 1 else "2026-09-23.1"
S, W, N, E = 25.73, -80.24, 25.82, -80.12
OUT = Path(__file__).resolve().parent.parent / "data" / "buildings" / "overture_buildings.geojson"

con = duckdb.connect()
for ext in ("httpfs", "spatial"):
    con.execute(f"INSTALL {ext}; LOAD {ext};")
# public bucket: force anonymous access even if AWS credentials exist in the environment
con.execute("CREATE OR REPLACE SECRET overture (TYPE s3, PROVIDER config, KEY_ID '', SECRET '', "
            "REGION 'us-west-2');")
src = f"s3://overturemaps-us-west-2/release/{RELEASE}/theme=buildings/type=building/*"
con.execute(f"""
COPY (
  SELECT id, names.primary AS name, height, num_floors, roof_height, class, subtype,
         sources[1].dataset AS source, geometry
  FROM read_parquet('{src}', filename=true, hive_partitioning=1)
  WHERE bbox.xmin <= {E} AND bbox.xmax >= {W} AND bbox.ymin <= {N} AND bbox.ymax >= {S}
) TO '{OUT}' WITH (FORMAT GDAL, DRIVER 'GeoJSON');
""")
print("wrote", OUT)
