#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

from filter_viina import (
    first_csv,
    is_true,
    label_value,
    load_ru_gazetteer,
    location_decision,
    ndate,
    scan_info,
    val,
)

START_2022 = 20220224
END_2022 = 20221231

UA_ACTOR_PATTERNS = [
    r"\bukrain(?:e|ian)\b",
    r"\bukrainian forces\b",
    r"\bukrainian drone",
    r"\bukrainian missile",
    r"\bSBU\b",
    r"\bAFU\b",
    r"україн",
    r"украин",
    r"\bзсу\b",
    r"\bвсу\b",
    r"\bсбу\b",
    r"\bссо\b",
    r"сил(?:и|ы) оборон",
    r"збройн",
]

RU_SCOPE_PATTERNS = [
    r"\bin russia\b",
    r"\brussian federation\b",
    r"\bon russian territory\b",
    r"\binside russia\b",
    r"\bв россии\b",
    r"\bв рф\b",
    r"\bна территории россии\b",
    r"\bна території росії\b",
    r"\bу росії\b",
    r"белгород",
    r"брянск",
    r"курск",
    r"ростов",
    r"краснодар",
    r"воронеж",
    r"ор[её]л",
    r"калуг",
    r"тул",
    r"липецк",
    r"тамбов",
    r"рязан",
    r"смоленск",
    r"псков",
    r"ленинград",
    r"новгород",
    r"саратов",
    r"самар",
    r"татарстан",
    r"башк",
    r"нижн(?:ий|его) новгород",
    r"волгоград",
    r"астрахан",
    r"ставропол",
    r"дагестан",
    r"чечн",
    r"осети",
    r"коми",
    r"мурманск",
    r"архангельск",
    r"ярослав",
    r"твер",
    r"москв",
    r"belgorod",
    r"bryansk",
    r"kursk",
    r"rostov",
    r"krasnodar",
    r"voronezh",
    r"oryol|orel",
    r"kaluga",
    r"tula",
    r"lipetsk",
    r"tambov",
    r"ryazan",
    r"smolensk",
    r"pskov",
    r"leningrad",
    r"novgorod",
    r"saratov",
    r"samara",
    r"tatarstan",
    r"bashkort",
    r"nizhny novgorod",
    r"volgograd",
    r"astrakhan",
    r"stavropol",
    r"dagestan",
    r"komi",
    r"murmansk",
    r"arkhangelsk",
    r"yaroslavl",
    r"tver",
    r"moscow",
]

UA_RX = [re.compile(p, re.I | re.U) for p in UA_ACTOR_PATTERNS]
RU_RX = [re.compile(p, re.I | re.U) for p in RU_SCOPE_PATTERNS]


def text_match(rx_list, text: str) -> list[str]:
    out = []
    for rx in rx_list:
        m = rx.search(text)
        if m:
            out.append(m.group(0))
    return sorted(set(out))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--viina-data-dir", type=Path, required=True)
    ap.add_argument("--ru-geonames", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    args = ap.parse_args()

    info_path = args.viina_data_dir / "event_info_latest_2022.zip"
    onepd_path = args.viina_data_dir / "event_1pd_latest_2022.zip"
    gaz = load_ru_gazetteer(args.ru_geonames)
    raw = scan_info(info_path, gaz)

    rows = []
    counts = Counter()
    matched_keys = set()

    z, f = first_csv(onepd_path)
    try:
        reader = csv.DictReader(f)
        for row in reader:
            key = val(row, "event_id_1pd")
            if key not in raw:
                continue
            d = ndate(row.get("date"))
            if d is None or not START_2022 <= d <= END_2022:
                continue

            matched_keys.add(key)
            x = raw[key]
            representative_text = " || ".join(x["texts"][:3])
            ua_terms = text_match(UA_RX, representative_text)
            ru_terms = text_match(RU_RX, representative_text)

            actor_labels = {}
            for base in ["a_ukr_init", "a_ukr", "a_rus_init", "a_rus"]:
                field_name, value = label_value(row, base)
                actor_labels[base + "_field"] = field_name
                actor_labels[base] = value

            bucket, method, distance, nearest_gid, nearest_name = location_decision(row, gaz)
            a_ukr_init_true = is_true(actor_labels["a_ukr_init"])
            a_ukr_true = is_true(actor_labels["a_ukr"])
            a_rus_init_true = is_true(actor_labels["a_rus_init"])

            if bucket == "STRICT":
                triage = "REVIEW_RUSSIA_GEO"
                reason = method
            elif bucket == "REVIEW":
                triage = "REVIEW_LOCATION_AMBIGUOUS"
                reason = method
            elif ua_terms and ru_terms:
                triage = "REVIEW_TEXT_RUSSIA_UA_ACTOR"
                reason = "UA_ACTOR_TEXT+RU_SCOPE_TEXT"
            elif a_ukr_init_true:
                triage = "REVIEW_UKR_INIT_LABEL"
                reason = "A_UKR_INIT_TRUE_WITHOUT_RU_LOCATION"
            else:
                triage = "MACHINE_NONCANDIDATE"
                reason = "NO_RU_GEO_OR_UA_ACTOR_PLUS_RU_SCOPE_TEXT"

            counts[triage] += 1
            if a_ukr_init_true:
                counts["A_UKR_INIT_TRUE"] += 1
            if a_ukr_true:
                counts["A_UKR_TRUE"] += 1
            if a_rus_init_true:
                counts["A_RUS_INIT_TRUE"] += 1

            rows.append({
                "event_id_1pd": key,
                "date": d,
                "n_reports": val(row, "n_reports"),
                "event_ids_matching": "|".join(sorted(i for i in x["ids"] if i)),
                "sources_matching": "|".join(sorted(x["sources"])),
                "source_urls": "|".join(sorted(x["urls"])),
                "target_classes": "|".join(sorted(x["classes"])),
                "target_terms": "|".join(sorted(x["tt"])),
                "attack_terms": "|".join(sorted(x["aa"])),
                "geonameid": val(row, "geonameid"),
                "asciiname": val(row, "asciiname"),
                "ADM1_NAME": val(row, "ADM1_NAME"),
                "ADM2_NAME": val(row, "ADM2_NAME"),
                "longitude": val(row, "longitude"),
                "latitude": val(row, "latitude"),
                "location_bucket": bucket,
                "location_method": method,
                "nearest_ru_distance_km": distance,
                "nearest_ru_geonameid": nearest_gid,
                "nearest_ru_name": nearest_name,
                **actor_labels,
                "ua_actor_text_terms": "|".join(ua_terms),
                "ru_scope_text_terms": "|".join(ru_terms),
                "representative_text": representative_text,
                "TriageStatus": triage,
                "TriageReason": reason,
                "CandidateCensusComplete": "FALSE",
            })
    finally:
        f.close()
        z.close()

    missing_join = sorted(set(raw) - matched_keys)
    counts["RAW_TEXT_MATCH_GROUPS"] = len(raw)
    counts["JOINED_ONEPD_GROUPS"] = len(rows)
    counts["RAW_WITHOUT_ONEPD_JOIN"] = len(missing_join)

    fields = [
        "event_id_1pd", "date", "n_reports", "event_ids_matching", "sources_matching", "source_urls",
        "target_classes", "target_terms", "attack_terms", "geonameid", "asciiname", "ADM1_NAME", "ADM2_NAME",
        "longitude", "latitude", "location_bucket", "location_method", "nearest_ru_distance_km",
        "nearest_ru_geonameid", "nearest_ru_name", "a_ukr_init_field", "a_ukr_init", "a_ukr_field", "a_ukr",
        "a_rus_init_field", "a_rus_init", "a_rus_field", "a_rus", "ua_actor_text_terms", "ru_scope_text_terms",
        "representative_text", "TriageStatus", "TriageReason", "CandidateCensusComplete",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as f_out:
        w = csv.DictWriter(f_out, fieldnames=fields)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["TriageStatus"], r["date"], r["event_id_1pd"])))

    review_total = sum(v for k, v in counts.items() if k.startswith("REVIEW_"))
    with args.summary.open("w", encoding="utf-8") as s:
        s.write("protocol=VIINA_2022_ACTOR_INDEPENDENT_V1\n")
        s.write(f"study_start={START_2022}\n")
        s.write(f"study_end={END_2022}\n")
        s.write(f"raw_text_match_groups={counts['RAW_TEXT_MATCH_GROUPS']}\n")
        s.write(f"joined_onepd_groups={counts['JOINED_ONEPD_GROUPS']}\n")
        s.write(f"raw_without_onepd_join={counts['RAW_WITHOUT_ONEPD_JOIN']}\n")
        s.write(f"review_total={review_total}\n")
        for key in sorted(k for k in counts if k.startswith("REVIEW_")):
            s.write(f"{key}={counts[key]}\n")
        s.write(f"machine_noncandidate={counts['MACHINE_NONCANDIDATE']}\n")
        s.write(f"a_ukr_init_true={counts['A_UKR_INIT_TRUE']}\n")
        s.write(f"a_ukr_true={counts['A_UKR_TRUE']}\n")
        s.write(f"a_rus_init_true={counts['A_RUS_INIT_TRUE']}\n")
        s.write("candidate_census_complete=FALSE\n")
        s.write("note=2022 a_ukr_init is diagnostic evidence only and is not used as an exclusion gate.\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
