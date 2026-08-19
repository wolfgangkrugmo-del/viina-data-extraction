#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

WORD = r"A-Za-zА-Яа-яЁёІіЇїЄєҐґ0-9_"

def bounded(terms: list[str]) -> re.Pattern[str]:
    return re.compile(rf"(?<![{WORD}])(?:{'|'.join(terms)})(?![{WORD}])", re.I | re.U)

# 2022 Russia-proper places/facilities that can be omitted from broad oblast-level wording.
RU_TARGET = bounded([
    r"millerovo", r"миллерово",
    r"engels", r"энгельс", r"енгельс",
    r"dyagilevo", r"diagilevo", r"дягилево",
    r"novoshakhtinsk", r"новошахтинск",
    r"shebekino", r"шебекино",
    r"solokhi", r"солохи",
    r"klimovo", r"климово",
    r"klintsy", r"клинцы",
    r"valuyki", r"валуйки",
    r"grayvoron", r"graivoron", r"грайворон",
    r"staraya nelidovka", r"старая нелидовка",
    r"novaya nelidovka", r"новая нелидовка",
    r"novoshakhtinsk refinery", r"новошахтинск(?:ий|ого) нпз",
    r"engels air(?: |-)?base", r"аэродром энгельс", r"авиабаз(?:а|е|у) энгельс",
])

UA_ADM1 = {
    "kharkiv", "kharkivs'ka", "kiev", "kyiv", "kiev city", "donets'k", "luhans'k",
    "kherson", "zaporizhzhya", "dnipropetrovs'k", "mykolayiv", "odessa", "poltava",
    "sumy", "chernihiv", "cherkasy", "vinnytsya", "zhytomyr", "khmel'nyts'kyy",
    "rivne", "volyn", "lviv", "ternopil", "ivano-frankivs'k", "chernivtsi",
    "kirovohrad", "zakarpattia"
}
CRIMEA_ADM1 = {"crimea", "sevastopol city"}

RUSSIA_REVIEW_METHODS = {
    "REVIEW_NAME_ONLY_RU_SUPPORT", "REVIEW_COORDINATE_NEAR_RU"
}


def truth(v: str) -> bool:
    return (v or "").strip().casefold() in {"1", "true", "t", "yes", "y"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--high-output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    args = ap.parse_args()

    with args.input.open(encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        fields = list(r.fieldnames or [])
        rows = [x for x in r if x.get("TriagePriorityV2") == "R5_SCOPE_UNKNOWN"]

    if len(rows) != 344:
        raise RuntimeError(f"Expected 344 R5 rows, found {len(rows)}")

    counts = Counter()
    out = []
    high = []

    for row in rows:
        text = row.get("representative_text", "") or ""
        adm1 = (row.get("ADM1_NAME", "") or "").strip().casefold()
        method = (row.get("location_method", "") or "").strip()
        ua_actor = truth(row.get("a_ukr", "")) or bool((row.get("ua_actor_text_terms", "") or "").strip())
        ru_actor = truth(row.get("a_rus", "")) or truth(row.get("a_rus_init", ""))
        ru_target_hits = sorted(set(m.group(0) for m in RU_TARGET.finditer(text)))
        ua_geo = adm1 in UA_ADM1
        crimea_geo = adm1 in CRIMEA_ADM1
        ru_review = method in RUSSIA_REVIEW_METHODS

        if ru_target_hits:
            priority = "H1_RUSSIA_TARGET_TEXT"
            reason = "KNOWN_RUSSIA_2022_TARGET_OR_PLACE_TEXT"
        elif ua_actor and ru_review:
            priority = "H2_UA_ACTOR_RUSSIA_LOCATION_REVIEW"
            reason = "UA_ACTOR_PLUS_RUSSIA_SUSPECT_LOCATION_METHOD"
        elif ua_actor and not ua_geo and not crimea_geo:
            priority = "H3_UA_ACTOR_NO_CLEAR_UA_GEO"
            reason = "UA_ACTOR_WITHOUT_CLEAR_UKRAINE_OR_CRIMEA_ADM1"
        elif ua_actor and ua_geo:
            priority = "M1_UA_ACTOR_UA_GEO"
            reason = "UA_ACTOR_BUT_VIINA_GEOCODE_IN_UKRAINE_REQUIRES_TEXT_CHECK"
        elif crimea_geo:
            priority = "L1_CRIMEA_GEO"
            reason = "VIINA_ADM1_CRIMEA"
        elif ru_actor and ua_geo:
            priority = "L2_RUS_ACTOR_UA_GEO"
            reason = "RUSSIAN_ACTOR_AND_UKRAINE_GEOCODE"
        elif ua_geo:
            priority = "L3_UA_GEO_NO_UA_ACTOR"
            reason = "UKRAINE_GEOCODE_WITHOUT_UA_ACTOR_EVIDENCE"
        else:
            priority = "M2_REMAINS_UNRESOLVED"
            reason = "NO_DECISIVE_SECOND_STAGE_SIGNAL"

        x = dict(row)
        x.update({
            "R5PriorityV3": priority,
            "R5PriorityReasonV3": reason,
            "RussiaTargetTextHitsV3": "|".join(ru_target_hits),
            "UkraineActorEvidenceV3": "TRUE" if ua_actor else "FALSE",
            "RussiaActorEvidenceV3": "TRUE" if ru_actor else "FALSE",
            "UkraineAdm1EvidenceV3": "TRUE" if ua_geo else "FALSE",
            "CrimeaAdm1EvidenceV3": "TRUE" if crimea_geo else "FALSE",
            "RussiaReviewMethodEvidenceV3": "TRUE" if ru_review else "FALSE",
            "ManualReviewRequired": "TRUE",
            "CandidateCensusComplete": "FALSE",
        })
        out.append(x)
        counts[priority] += 1
        if priority.startswith("H"):
            high.append(x)

    extra = [
        "R5PriorityV3", "R5PriorityReasonV3", "RussiaTargetTextHitsV3",
        "UkraineActorEvidenceV3", "RussiaActorEvidenceV3", "UkraineAdm1EvidenceV3",
        "CrimeaAdm1EvidenceV3", "RussiaReviewMethodEvidenceV3"
    ]
    seen = set()
    out_fields = [c for c in fields + extra if not (c in seen or seen.add(c))]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    for path, data in [(args.output, out), (args.high_output, high)]:
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
            w.writeheader(); w.writerows(data)

    order = [
        "H1_RUSSIA_TARGET_TEXT", "H2_UA_ACTOR_RUSSIA_LOCATION_REVIEW", "H3_UA_ACTOR_NO_CLEAR_UA_GEO",
        "M1_UA_ACTOR_UA_GEO", "M2_REMAINS_UNRESOLVED", "L1_CRIMEA_GEO",
        "L2_RUS_ACTOR_UA_GEO", "L3_UA_GEO_NO_UA_ACTOR"
    ]
    with args.summary.open("w", encoding="utf-8") as f:
        f.write("protocol=VIINA_2022_R5_SECOND_STAGE_V3\n")
        f.write(f"input_r5_rows={len(rows)}\n")
        f.write(f"high_priority_rows={len(high)}\n")
        for k in order:
            f.write(f"{k}={counts[k]}\n")
        f.write("policy=PRIORITIZATION_ONLY_NO_AUTOMATIC_EXCLUSION\n")
        f.write("manual_review_required=TRUE\n")
        f.write("candidate_census_complete=FALSE\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
