#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import filter_viina as fv

CASES = [
    ("Belgorod", 50.59556, 36.58734, "STRICT"),
    ("Samara", 53.21946, 50.20393, "STRICT"),
    ("Taganrog", 47.21537, 38.92852, "STRICT"),
    ("Feodosia", 45.02665, 35.38391, "REVIEW"),
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ru-geonames", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()

    gaz = fv.load_ru_gazetteer(a.ru_geonames)
    lines = [
        f"gazetteer_ids={len(gaz['ids'])}",
        f"gazetteer_names={len(gaz['names'])}",
        f"gazetteer_grid_cells={len(gaz['grid'])}",
    ]
    if len(gaz['ids']) < 1000:
        raise SystemExit(f"FAIL gazetteer too small: {len(gaz['ids'])} IDs")

    failures = []
    for name, lat, lon, expected in CASES:
        row = {"latitude": str(lat), "longitude": str(lon), "geonameid": "", "asciiname": name}
        bucket, method, dist, gid, nearest = fv.location_decision(row, gaz)
        lines.append(
            f"{name}: expected={expected} actual={bucket} method={method} distance_km={dist} nearest_gid={gid} nearest_name={nearest}"
        )
        if bucket != expected:
            failures.append(f"{name}: expected {expected}, got {bucket}/{method}")
        if name == "Feodosia" and method != "REVIEW_DISPUTED_CRIMEA":
            failures.append(f"Feodosia: expected REVIEW_DISPUTED_CRIMEA, got {method}")

    lines.append("result=" + ("PASS" if not failures else "FAIL"))
    if failures:
        lines.extend("failure=" + x for x in failures)

    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    if failures:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
