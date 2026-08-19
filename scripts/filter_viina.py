#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import math
import re
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path

START, END = 20220224, 20260630
STRICT_RU_DISTANCE_KM = 5.0
REVIEW_RU_DISTANCE_KM = 20.0

TARGET_PATTERNS = {
    "REFINING_PETROCHEM_GAS": [r"\brefiner", r"oil refinery", r"gas processing", r"нефтеперерабат", r"\bнпз\b", r"нафтоперероб", r"газоперерабат", r"petrochem", r"нефтехим"],
    "FUEL_STORAGE_TERMINAL": [r"oil depot", r"fuel depot", r"tank farm", r"oil terminal", r"нефтебаз", r"нафтобаз", r"нефтехранил", r"нефтян.*терминал", r"нафтов.*термінал"],
    "PIPELINE_PUMPING": [r"pipeline", r"pumping station", r"pump station", r"нефтепровод", r"нафтопров", r"трубопровод", r"перекачивающ.*станц"],
    "PORT_EXPORT_LOGISTICS": [r"\bport\b", r"sea terminal", r"export terminal", r"\bпорт\b", r"морск.*терминал", r"морськ.*термінал"],
    "STRATEGIC_AIRBASE": [r"airbase", r"air base", r"airfield", r"авиабаз", r"авіабаз", r"аэродром", r"аеродром", r"strategic bomber", r"стратегическ.*бомбард"],
    "AMMUNITION_ARSENAL": [r"ammunition depot", r"ammo depot", r"\barsenal\b", r"склад.*боеприпас", r"склад.*боєприпас", r"\bарсенал"],
    "DEFENSE_INDUSTRY": [r"defen[cs]e plant", r"military plant", r"arms plant", r"weapons plant", r"оборонн.*завод", r"военн.*завод", r"\bвпк\b", r"порохов.*завод"],
    "MILITARY_REPAIR_SHIPYARD": [r"shipyard", r"repair yard", r"dry dock", r"судоремонт", r"суднобуд", r"верф", r"сух.*док"],
    "RAIL_STRATEGIC_LOGISTICS": [r"railway depot", r"railway hub", r"железнодорож.*узел", r"залізничн.*вузол", r"железнодорож.*депо"],
    "MILITARY_COMMS_SPACE": [r"satellite communication", r"communications center", r"space communications", r"спутников.*связ", r"супутников.*зв", r"центр.*связ"],
    "ENERGY_GRID_SUPPORT": [r"power substation", r"electrical substation", r"подстанц", r"підстанц"],
}
ATTACK_PATTERNS = [
    r"\battack", r"\bstrike", r"\bdrone", r"\bmissile", r"\bexplosion", r"\bfire\b", r"\bdamag", r"\bdestroy", r"\bsabot",
    r"атак", r"удар", r"дрон", r"беспилот", r"безпілот", r"ракет", r"взрыв", r"вибух", r"пожар", r"пожеж", r"поврежд", r"пошкодж", r"уничтож", r"знищ",
]

CT = {k: [re.compile(p, re.I | re.U) for p in v] for k, v in TARGET_PATTERNS.items()}
CA = [re.compile(p, re.I | re.U) for p in ATTACK_PATTERNS]


def first_csv(zip_path: Path):
    z = zipfile.ZipFile(zip_path)
    names = [n for n in z.namelist() if n.lower().endswith(".csv")]
    if not names:
        raise RuntimeError(f"No CSV in {zip_path}")
    return z, io.TextIOWrapper(z.open(names[0], "r"), encoding="utf-8-sig", newline="")


def ndate(v):
    s = re.sub(r"\D", "", str(v or ""))
    return int(s[:8]) if len(s) >= 8 else None


def norm_name(v):
    s = unicodedata.normalize("NFKD", str(v or "")).casefold()
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"[^a-zа-яёіїєґ0-9]+", " ", s, flags=re.I).strip()


def hits(text):
    classes, target_terms, attack_terms = [], [], []
    for cls, pats in CT.items():
        matched = [m.group(0) for p in pats if (m := p.search(text))]
        if matched:
            classes.append(cls)
            target_terms.extend(matched)
    for p in CA:
        m = p.search(text)
        if m:
            attack_terms.append(m.group(0))
    return sorted(set(classes)), sorted(set(target_terms)), sorted(set(attack_terms))


def grid_key(lat, lon, cell=0.25):
    return int(math.floor(lat / cell)), int(math.floor(lon / cell))


def haversine_km(lat1, lon1, lat2, lon2):
    radius = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(min(1.0, math.sqrt(a)))


def load_ru_gazetteer(path: Path):
    ids, names, grid = set(), set(), defaultdict(list)
    with zipfile.ZipFile(path) as z:
        txt_members = [n for n in z.namelist() if n.lower().endswith(".txt")]
        preferred = next((n for n in txt_members if Path(n).name.casefold() == "ru.txt"), None)
        if preferred is None and txt_members:
            preferred = max(txt_members, key=lambda n: z.getinfo(n).file_size)
        if preferred is None:
            raise RuntimeError("GeoNames RU.zip contains no TXT member")
        with io.TextIOWrapper(z.open(preferred), encoding="utf-8") as f:
            for line in f:
                p = line.rstrip("\n").split("\t")
                if len(p) < 6 or not p[0].strip().isdigit():
                    continue
                gid = p[0].strip()
                ids.add(gid)
                for raw in [p[1], p[2]] + (p[3].split(",") if p[3] else []):
                    n = norm_name(raw)
                    if n:
                        names.add(n)
                try:
                    lat, lon = float(p[4]), float(p[5])
                except ValueError:
                    continue
                grid[grid_key(lat, lon)].append((lat, lon, gid, p[2] or p[1]))
    if not ids:
        raise RuntimeError("GeoNames Russia gazetteer loaded zero geoname IDs")
    return {"ids": ids, "names": names, "grid": grid}


def nearest_ru_point(lat, lon, gaz):
    k0 = grid_key(lat, lon)
    best = None
    for di in range(-1, 2):
        for dj in range(-1, 2):
            for glat, glon, gid, name in gaz["grid"].get((k0[0] + di, k0[1] + dj), []):
                d = haversine_km(lat, lon, glat, glon)
                if best is None or d < best[0]:
                    best = (d, gid, name, glat, glon)
    return best


def is_crimea_coordinate(lat, lon):
    # Review-only: do not silently encode the occupied/disputed peninsula as Russia proper.
    return 44.0 <= lat <= 46.4 and 32.0 <= lon <= 36.8


def is_true(v):
    return str(v or "").strip().lower() in {"1", "1.0", "true", "t", "yes"}


def first_existing(row, names):
    for n in names:
        if n in row:
            return n, row.get(n)
    return None, None


def val(row, key):
    return str(row.get(key, "") or "").strip()


def ffloat(v):
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def label_value(row, base):
    name, value = first_existing(row, [base + "_b", base])
    return name or "", str(value or "").strip()


def scan_info(path: Path, gaz=None):
    """High-recall text screen only. No country gate is allowed at this stage."""
    agg = defaultdict(lambda: {
        "ids": set(), "sources": set(), "urls": set(), "texts": [],
        "classes": set(), "tt": set(), "aa": set(), "raw_geonameids": set(),
        "raw_places": set(), "raw_adm1": set(), "raw_adm2": set(),
    })
    z, f = first_csv(path)
    try:
        reader = csv.DictReader(f)
        for row in reader:
            d = ndate(row.get("date"))
            if d is None or not START <= d <= END:
                continue
            text = str(row.get("text", "") or "")
            classes, target_terms, attack_terms = hits(text)
            if not classes or not attack_terms:
                continue
            key = str(row.get("event_id_1pd", "")).strip()
            if not key:
                continue
            x = agg[key]
            x["ids"].add(str(row.get("event_id", "")).strip())
            if row.get("source"):
                x["sources"].add(str(row["source"]).strip())
            if row.get("url"):
                x["urls"].add(str(row["url"]).strip())
            if text and len(x["texts"]) < 6:
                x["texts"].append(text.replace("\n", " ").strip())
            x["classes"].update(classes)
            x["tt"].update(target_terms)
            x["aa"].update(attack_terms)
            gid = str(row.get("geonameid", "")).strip()
            if gid:
                x["raw_geonameids"].add(gid)
            if row.get("asciiname"):
                x["raw_places"].add(str(row["asciiname"]).strip())
            if row.get("ADM1_NAME"):
                x["raw_adm1"].add(str(row["ADM1_NAME"]).strip())
            if row.get("ADM2_NAME"):
                x["raw_adm2"].add(str(row["ADM2_NAME"]).strip())
    finally:
        f.close()
        z.close()
    return agg


def location_decision(row, gaz):
    gid = val(row, "geonameid")
    lat, lon = ffloat(row.get("latitude")), ffloat(row.get("longitude"))
    place = val(row, "asciiname")

    if lat is not None and lon is not None and is_crimea_coordinate(lat, lon):
        return "REVIEW", "REVIEW_DISPUTED_CRIMEA", "", "", ""

    if gid and gid in gaz["ids"]:
        return "STRICT", "GEONAMEID_RU", "0.000", gid, place

    if lat is not None and lon is not None:
        nearest = nearest_ru_point(lat, lon, gaz)
        if nearest:
            dist = nearest[0]
            if dist <= STRICT_RU_DISTANCE_KM:
                return "STRICT", "COORDINATE_RU_STRICT", f"{dist:.3f}", nearest[1], nearest[2]
            if dist <= REVIEW_RU_DISTANCE_KM:
                return "REVIEW", "REVIEW_COORDINATE_NEAR_RU", f"{dist:.3f}", nearest[1], nearest[2]

    if place and norm_name(place) in gaz["names"]:
        return "REVIEW", "REVIEW_NAME_ONLY_RU_SUPPORT", "", "", place

    return "DROP", "DROP_LOCATION_NOT_RU", "", "", ""


def join_onepd(path: Path, raw, gaz):
    strict, review = [], []
    z, f = first_csv(path)
    try:
        reader = csv.DictReader(f)
        fields = set(reader.fieldnames or [])
        if not (fields & {"a_ukr_init_b", "a_ukr_init"}):
            raise RuntimeError(f"{path}: a_ukr_init field missing")

        for row in reader:
            key = val(row, "event_id_1pd")
            if key not in raw:
                continue
            d = ndate(row.get("date"))
            if d is None or not START <= d <= END:
                continue
            _, actor_value = first_existing(row, ["a_ukr_init_b", "a_ukr_init"])
            if not is_true(actor_value):
                continue

            bucket, method, distance, nearest_gid, nearest_name = location_decision(row, gaz)
            if bucket == "DROP":
                continue

            x = raw[key]
            labels = {}
            for base in ["a_ukr_init", "a_ukr", "a_rus_init", "a_rus", "t_mil", "t_uav", "t_airstrike", "t_artillery", "t_property", "t_raid"]:
                field_name, value = label_value(row, base)
                labels[base + "_field"] = field_name
                labels[base] = value

            rec = {
                "event_id_1pd": key,
                "date": str(d),
                "n_reports_viina": val(row, "n_reports"),
                "raw_reports_matching": str(len(x["ids"])),
                "event_ids_matching": "|".join(sorted(x["ids"])),
                "sources_matching": "|".join(sorted(x["sources"])),
                "source_urls": "|".join(sorted(x["urls"])),
                "geonameid": val(row, "geonameid"),
                "asciiname": val(row, "asciiname"),
                "ADM1_NAME": val(row, "ADM1_NAME"),
                "ADM2_NAME": val(row, "ADM2_NAME"),
                "longitude": val(row, "longitude"),
                "latitude": val(row, "latitude"),
                "GEO_PRECISION": val(row, "GEO_PRECISION"),
                "raw_geonameids": "|".join(sorted(x["raw_geonameids"])),
                "raw_places": "|".join(sorted(x["raw_places"])),
                "raw_ADM1": "|".join(sorted(x["raw_adm1"])),
                "raw_ADM2": "|".join(sorted(x["raw_adm2"])),
                **labels,
                "target_class_auto": "|".join(sorted(x["classes"])),
                "matched_target_terms": "|".join(sorted(x["tt"])),
                "matched_attack_terms": "|".join(sorted(x["aa"])),
                "representative_text": " || ".join(x["texts"])[:12000],
                "ukrainian_initiator_gate": "TRUE",
                "russia_location_gate": "TRUE" if bucket == "STRICT" else "UNCERTAIN",
                "russia_location_method": method,
                "nearest_ru_distance_km": distance,
                "nearest_ru_geonameid": nearest_gid,
                "nearest_ru_name": nearest_name,
                "study_period_gate": "TRUE",
                "manual_review_required": "TRUE",
                "candidate_status": "STRICT_RUSSIA_UKR_INIT_DISCOVERY" if bucket == "STRICT" else method,
            }
            (strict if bucket == "STRICT" else review).append(rec)
    finally:
        f.close()
        z.close()
    return strict, review


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else ["event_id_1pd", "date", "candidate_status"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--viina-data-dir", type=Path, required=True)
    ap.add_argument("--ru-geonames", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--review-output", type=Path, required=True)
    a = ap.parse_args()

    gaz = load_ru_gazetteer(a.ru_geonames)
    strict, review = [], []
    for year in range(2022, 2027):
        raw = scan_info(a.viina_data_dir / f"event_info_latest_{year}.zip", gaz)
        s, q = join_onepd(a.viina_data_dir / f"event_1pd_latest_{year}.zip", raw, gaz)
        strict.extend(s)
        review.extend(q)

    strict = sorted({r["event_id_1pd"]: r for r in strict}.values(), key=lambda r: (r["date"], r["event_id_1pd"]))
    review = sorted({r["event_id_1pd"]: r for r in review}.values(), key=lambda r: (r["date"], r["event_id_1pd"]))
    write_csv(a.output, strict)
    write_csv(a.review_output, review)
    print(f"gazetteer_ids={len(gaz['ids'])}")
    print(f"Wrote {len(strict)} strict candidates to {a.output}")
    print(f"Wrote {len(review)} review candidates to {a.review_output}")


if __name__ == "__main__":
    main()
