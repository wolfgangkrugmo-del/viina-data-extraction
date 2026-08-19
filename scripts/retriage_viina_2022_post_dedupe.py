#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

WORD = r"A-Za-zА-Яа-яЁёІіЇїЄєҐґ0-9_"

def bounded(terms: list[str]) -> re.Pattern[str]:
    body = "|".join(terms)
    return re.compile(rf"(?<![{WORD}])(?:{body})(?![{WORD}])", re.I | re.U)

RUSSIA_EXPLICIT = bounded([
    r"in russia", r"inside russia", r"within russia", r"russian federation", r"on russian territory",
    r"в россии", r"в рф", r"на территории россии", r"у росії", r"на території росії",
])

RUSSIA_PLACES = bounded([
    r"belgorod", r"bryansk", r"kursk", r"rostov", r"krasnodar", r"voronezh", r"oryol", r"orel",
    r"kaluga", r"tula", r"lipetsk", r"tambov", r"ryazan", r"smolensk", r"pskov", r"leningrad",
    r"novgorod", r"saratov", r"samara", r"tatarstan", r"bashkortostan", r"nizhny novgorod",
    r"volgograd", r"astrakhan", r"stavropol", r"dagestan", r"komi", r"murmansk", r"arkhangelsk",
    r"yaroslavl", r"tver", r"moscow", r"engels", r"taganrog",
    r"белгород(?:а|е|у|ом)?", r"брянск(?:а|е|у|ом)?", r"курск(?:а|е|у|ом|ой)?", r"ростов(?:а|е|у|ом)?",
    r"краснодар(?:а|е|у|ом|ский|ского|ском)?", r"воронеж(?:а|е|у|ом)?", r"ор[её]л(?:а|е|у|ом)?",
    r"калуг(?:а|е|и|ой)", r"тул(?:а|е|ы|ой)", r"липецк(?:а|е|у|ом)?", r"тамбов(?:а|е|у|ом)?",
    r"рязан(?:ь|и|ью|ская|ской)", r"смоленск(?:а|е|у|ом)?", r"псков(?:а|е|у|ом)?",
    r"ленинград(?:ская|ской|скую|ской области)", r"новгород(?:а|е|у|ом|ская|ской)?", r"саратов(?:а|е|у|ом|ская|ской)?",
    r"самар(?:а|е|ы|ой|ская|ской)", r"татарстан(?:а|е|у|ом)?", r"башкортостан(?:а|е|у|ом)?",
    r"нижн(?:ий|его|ем) новгород(?:е|а|у|ом)?", r"волгоград(?:а|е|у|ом|ская|ской)?",
    r"астрахан(?:ь|и|ью|ская|ской)", r"ставропол(?:ь|я|е|ю|ем|ьский|ьского|ьском)?",
    r"дагестан(?:а|е|у|ом)?", r"коми", r"мурманск(?:а|е|у|ом)?", r"архангельск(?:а|е|у|ом)?",
    r"ярославл(?:ь|я|е|ю|ем|ьская|ьской)?", r"твер(?:ь|и|ью|ская|ской)", r"москв(?:а|е|ы|ой|у)",
    r"энгельс(?:а|е|у|ом)?", r"таганрог(?:а|е|у|ом)?",
])

CRIMEA = bounded([
    r"crimea", r"krym", r"sevastopol", r"feodosia", r"simferopol", r"dzhankoi", r"kerch", r"saki",
    r"крим", r"крым", r"севастопол(?:ь|я|е|ю|ем)?", r"феодос(?:ия|ии|ию|ией)", r"симферопол(?:ь|я|е|ю|ем)?",
    r"джанко(?:й|я|е|ю|ем)", r"керч(?:ь|и|ью)", r"саки",
])

OCCUPIED_UA = bounded([
    r"donetsk", r"luhansk", r"lugansk", r"mariupol", r"melitopol", r"berdiansk", r"berdyansk", r"kherson",
    r"zaporizhzhia", r"zaporozhye", r"makii?vka", r"soledar", r"enerhodar", r"berdyansk",
    r"донецьк(?:а|ій|у|ом)?", r"донецк(?:а|е|у|ом)?", r"луганськ(?:а|ій|у|ом)?", r"луганск(?:а|е|у|ом)?",
    r"маріупол(?:ь|і|я|ю|ем)?", r"мариупол(?:ь|е|я|ю|ем)?", r"мелітопол(?:ь|і|я|ю|ем)?",
    r"мелитопол(?:ь|е|я|ю|ем)?", r"бердянськ(?:а|у|ом)?", r"бердянск(?:а|е|у|ом)?",
    r"херсон(?:а|е|у|ом|ська|ской)?", r"запоріж(?:жя|жі|жю|зька|зькій)", r"запорож(?:ье|ья|ской|ская)",
    r"макеевк(?:а|е|и|ой)", r"макіївк(?:а|и|і|ою)", r"соледар(?:а|е|у|ом)?", r"энергодар(?:а|е|у|ом)?",
])

FRESH = bounded([
    r"attacked", r"attack on", r"struck", r"hit", r"drone strike", r"missile strike", r"sabotage",
    r"атаковал(?:а|и|о)?", r"атакували", r"ударил(?:а|и|о)?", r"уразил(?:а|и|о)?", r"вдарил(?:а|и|о)?",
    r"поразил(?:а|и|о)?",
])
FOLLOWUP = bounded([
    r"after the strike", r"after strike", r"after the attack", r"after attack", r"still burning", r"continues to burn",
    r"satellite image", r"satellite images", r"aftermath", r"repair", r"repairs",
    r"після удару", r"після атаки", r"после удара", r"после атаки", r"супутников(?:і|е|их)?", r"спутников(?:ые|ых)?",
    r"наслідк(?:и|ів|ами)?", r"последств(?:ия|ий|иями)?", r"ремонт(?:а|е|у|ом|ные|ных)?",
])


def classify_scope(text: str):
    c = bool(CRIMEA.search(text))
    u = bool(OCCUPIED_UA.search(text))
    rexp = bool(RUSSIA_EXPLICIT.search(text))
    rp = bool(RUSSIA_PLACES.search(text))
    r = rexp or rp
    if c and r:
        return "CONFLICT_OR_COMPOSITE", "CRIMEA_AND_RUSSIA_TEXT"
    if u and r:
        return "CONFLICT_OR_COMPOSITE", "OCCUPIED_UA_AND_RUSSIA_TEXT"
    if c:
        return "CRIMEA_SEVASTOPOL", "CRIMEA_TEXT"
    if u:
        return "UKRAINE_OCCUPIED_OTHER", "OCCUPIED_UA_TEXT"
    if rexp:
        return "RUSSIA_PROPER", "EXPLICIT_RUSSIA_TEXT"
    if rp:
        return "RUSSIA_PROPER", "RUSSIAN_PLACE_TEXT"
    return "UNKNOWN", "NO_DECISIVE_SCOPE_TEXT"


def classify_event(text: str):
    fresh = bool(FRESH.search(text))
    follow = bool(FOLLOWUP.search(text))
    if fresh and follow:
        return "FRESH_WITH_FOLLOWUP_WORDING", "FRESH_AND_FOLLOWUP_CUES"
    if fresh:
        return "FRESH_ATTACK_WORDING", "FRESH_ATTACK_CUE"
    if follow:
        return "FOLLOWUP_OR_AFTERMATH", "FOLLOWUP_CUE_NO_FRESH_VERB"
    return "EVENT_FORM_UNRESOLVED", "NO_DECISIVE_EVENT_FORM_CUE"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--russia-output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    args = ap.parse_args()

    with args.input.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        rows = list(reader)

    if len(rows) != 507:
        raise RuntimeError(f"Expected 507 post-dedupe review rows, found {len(rows)}")

    out = []
    russia = []
    counts = Counter()
    for r in rows:
        text = r.get("representative_text", "") or ""
        scope, scope_reason = classify_scope(text)
        event_form, event_reason = classify_event(text)
        if scope == "RUSSIA_PROPER":
            priority = "R1_RUSSIA_PROPER_TEXT"
            russia.append(r)
        elif scope == "CONFLICT_OR_COMPOSITE":
            priority = "R2_SCOPE_CONFLICT_COMPOSITE"
        elif scope == "CRIMEA_SEVASTOPOL":
            priority = "R3_CRIMEA"
        elif scope == "UKRAINE_OCCUPIED_OTHER":
            priority = "R4_OCCUPIED_UA_OTHER"
        else:
            priority = "R5_SCOPE_UNKNOWN"
        x = dict(r)
        x.update({
            "ScopeAutoV2": scope,
            "ScopeReasonV2": scope_reason,
            "EventFormAutoV2": event_form,
            "EventFormReasonV2": event_reason,
            "TriagePriorityV2": priority,
            "ManualReviewRequired": "TRUE",
            "CandidateCensusComplete": "FALSE",
        })
        out.append(x)
        counts[priority] += 1
        counts[f"EVENT_{event_form}"] += 1

    russia_rows = [x for x in out if x["TriagePriorityV2"] == "R1_RUSSIA_PROPER_TEXT"]

    extra = ["ScopeAutoV2","ScopeReasonV2","EventFormAutoV2","EventFormReasonV2","TriagePriorityV2"]
    seen=set(); out_fields=[c for c in fields+extra if not (c in seen or seen.add(c))]
    for path,data in [(args.output,out),(args.russia_output,russia_rows)]:
        with path.open("w", encoding="utf-8", newline="") as f:
            w=csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
            w.writeheader(); w.writerows(data)

    with args.summary.open("w", encoding="utf-8") as f:
        f.write("protocol=VIINA_2022_POST_DEDUPE_RETRIAGE_V2\n")
        f.write("input_rows=507\n")
        f.write(f"russia_priority_rows_v2={len(russia_rows)}\n")
        for key in ["R1_RUSSIA_PROPER_TEXT","R2_SCOPE_CONFLICT_COMPOSITE","R3_CRIMEA","R4_OCCUPIED_UA_OTHER","R5_SCOPE_UNKNOWN"]:
            f.write(f"{key}={counts[key]}\n")
        f.write("manual_review_required_for_all_rows=TRUE\n")
        f.write("event_level_dedupe_status=PENDING\n")
        f.write("candidate_census_complete=FALSE\n")
        f.write("note=V2 uses bounded Russia place regexes to prevent substring false positives such as твер within утверждается.\n")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
