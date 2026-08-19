#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

# Strong retrospective/commentary cues. These are intentionally conservative:
# only clear non-event/report-about-event cases are auto-dropped.
NON_EVENT_PATTERNS = [
    r"\bексперт\b", r"\bэксперт\b", r"\bexpert\b",
    r"\bприпустив\b", r"\bпредположил\b", r"\bwhy\b", r"\bчому\b",
    r"мовчить про удари", r"молчит об ударах", r"reaction to", r"реакц.*на удар",
    r"супутников.*після удар", r"спутников.*после удар", r"satellite.*after (?:the )?strike",
]

# Effect/follow-up wording: only a non-event if no fresh attack wording occurs before it.
FOLLOWUP_PATTERNS = [
    r"після влучання", r"после попадания", r"після удар", r"после удар",
    r"пожежа .*третій день", r"пожар .*третий день", r"continues? to burn",
]

FRESH_ATTACK_PATTERNS = [
    r"дрони атакували", r"дроны атаковали", r"атакували дрони", r"атаковали дроны",
    r"завдали удар", r"нанесли удар", r"уразили", r"поразили", r"влуч", r"попад",
    r"strike hit", r"drones? attacked", r"was attacked", r"sabotage",
]

# Location-explicit Russia-proper wording. Mere references to Russian forces/assets
# are NOT sufficient; wording must tie the event/target to Russia as a place.
RUSSIA_LOCATION_PATTERNS = [
    r"\bв\s+россии\b", r"\bу\s+росії\b", r"\bв\s+рф\b", r"\bна\s+территории\s+россии\b",
    r"\bна\s+території\s+росії\b", r"\bв\s+российском\s+(?:городе|регионе|порту)\b",
    r"\bу\s+російському\s+(?:місті|регіоні|порту)\b", r"\bроссийский\s+экспортный\s+порт\b",
    r"\bросійський\s+експортний\s+порт\b",
]

# Russian federal-subject/location phrases commonly present in the current review set.
# These are geographic, not actor, indicators.
RUSSIA_REGION_PATTERNS = [
    r"брянск\w*\s+област", r"астрахан\w*\s+(?:област|порт)", r"ленинград\w*\s+област",
    r"ростов\w*\s+област", r"белгород\w*\s+област", r"самар\w*\s+област",
    r"ярослав\w*\s+област", r"краснодар\w*\s+кра", r"татарстан", r"башкортостан",
    r"нижегород\w*\s+област", r"волгоград\w*\s+област", r"калуж\w*\s+област",
    r"твер\w*\s+област", r"москов\w*\s+област", r"орлов\w*\s+област",
]

CRIMEA_TEXT_PATTERNS = [
    r"\bкрим\w*\b", r"\bкрым\w*\b", r"\bcrimea\b", r"\bсевастопол", r"\bsevastopol",
    r"\bфеодос", r"\bfeodos", r"\bсимферопол", r"\bsimferopol",
]


def any_match(patterns, text):
    return any(re.search(p, text, re.I | re.U) for p in patterns)


def is_crimea(row, text):
    status = (row.get("candidate_status") or "").upper()
    adm1 = (row.get("ADM1_NAME") or "").casefold()
    if status == "REVIEW_DISPUTED_CRIMEA":
        return True
    if "crimea" in adm1 or "sevastopol" in adm1:
        return True
    return any_match(CRIMEA_TEXT_PATTERNS, text)


def event_gate(text):
    if any_match(NON_EVENT_PATTERNS, text):
        return "FAIL", "STRONG_COMMENTARY_OR_RETROSPECTIVE_CUE"
    if any_match(FOLLOWUP_PATTERNS, text) and not any_match(FRESH_ATTACK_PATTERNS, text):
        return "FAIL", "FOLLOWUP_EFFECT_WITHOUT_FRESH_ATTACK"
    # VIINA input is already target+attack screened and a_ukr_init=1, so absent a
    # strong contrary cue we preserve it as a candidate rather than auto-dropping.
    if any_match(FRESH_ATTACK_PATTERNS, text):
        return "PASS", "FRESH_ATTACK_WORDING"
    return "UNCERTAIN", "EVENT_WORDING_NOT_DECISIVE"


def explicit_russia_location(text):
    if any_match(RUSSIA_LOCATION_PATTERNS, text):
        return True, "EXPLICIT_RUSSIA_LOCATION_TEXT"
    if any_match(RUSSIA_REGION_PATTERNS, text):
        return True, "RUSSIAN_REGION_LOCATION_TEXT"
    return False, ""


def likely_text_geo_conflict(row, explicit_ru):
    if not explicit_ru:
        return "FALSE"
    # Review exists mainly because geocoder and report text conflict. Treat a
    # non-empty Ukrainian/Crimean ADM1 plus explicit Russia location as conflict.
    adm1 = (row.get("ADM1_NAME") or "").strip().casefold()
    method = (row.get("russia_location_method") or "").upper()
    if method in {"REVIEW_NAME_ONLY_RU_SUPPORT", "REVIEW_LOCATION_UNRESOLVED"}:
        return "TRUE"
    if adm1 and any(x in adm1 for x in ["donets", "zaporiz", "crimea", "sevastopol", "kherson", "luhansk"]):
        return "TRUE"
    return "UNCERTAIN"


def split_required(text):
    # Conservative automatic signal for composite articles. It does not split
    # automatically; it only raises the row for manual event-unit review.
    multi = [
        r"москв.*(?:ярослав|ростов)|(?:ярослав|ростов).*москв",
        r"(?:два|three|три)\s+(?:объект|об'єкт|target|facility)",
        r"одночасно.*(?:і|та).*(?:і|та)",
    ]
    return "TRUE" if any_match(multi, text) else "FALSE"


def classify(row):
    text = (row.get("representative_text") or "").strip()
    gate, gate_reason = event_gate(text)
    crimea = is_crimea(row, text)
    explicit_ru, ru_reason = explicit_russia_location(text)

    if gate == "FAIL":
        decision = "DROP_NOT_EVENT"
        reason = gate_reason
        confidence = "HIGH"
        priority = "1_EVENT_GATE"
    elif crimea:
        decision = "CRIMEA_REVIEW"
        reason = "CRIMEA_LOCATION_CONFIRMED"
        confidence = "HIGH"
        priority = "3_CRIMEA"
    elif explicit_ru and gate == "PASS":
        decision = "PROMOTE_RUSSIA"
        reason = ru_reason + "+FRESH_ATTACK"
        confidence = "HIGH"
        priority = "2_PROMOTE_RUSSIA"
    elif explicit_ru:
        decision = "PROMOTE_RUSSIA"
        reason = ru_reason + "+EVENT_GATE_UNCERTAIN"
        confidence = "MEDIUM"
        priority = "2_PROMOTE_RUSSIA"
    else:
        decision = "UNRESOLVED"
        reason = "NO_DECISIVE_RUSSIA_PROPER_LOCATION_EVIDENCE"
        confidence = "LOW"
        priority = "4_UNRESOLVED"

    row = dict(row)
    row.update({
        "ReviewDecisionAuto": decision,
        "DecisionReason": reason,
        "EventGate": gate,
        "EventGateReason": gate_reason,
        "LocationEvidence": "CRIMEA" if crimea else (ru_reason if explicit_ru else "INSUFFICIENT"),
        "TextGeoConflict": likely_text_geo_conflict(row, explicit_ru),
        "SplitRequired": split_required(text),
        "RelatedEventID": "",
        "DecisionConfidence": confidence,
        "PriorityGroup": priority,
        "ManualDecisionRequired": "FALSE" if confidence == "HIGH" and decision in {"DROP_NOT_EVENT", "CRIMEA_REVIEW"} else "TRUE",
    })
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    args = ap.parse_args()

    with args.input.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    out = [classify(r) for r in rows]
    out.sort(key=lambda r: (r["PriorityGroup"], r.get("date", ""), r.get("event_id_1pd", "")))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not out:
        raise RuntimeError("Review input is empty; refusing to publish classification")
    fields = list(out[0].keys())
    with args.output.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(out)

    decisions = Counter(r["ReviewDecisionAuto"] for r in out)
    priorities = Counter(r["PriorityGroup"] for r in out)
    manual = Counter(r["ManualDecisionRequired"] for r in out)
    lines = [
        f"input_rows={len(rows)}",
        "decision_counts=" + ",".join(f"{k}:{decisions[k]}" for k in sorted(decisions)),
        "priority_counts=" + ",".join(f"{k}:{priorities[k]}" for k in sorted(priorities)),
        "manual_required_counts=" + ",".join(f"{k}:{manual[k]}" for k in sorted(manual)),
        "rule_order=EVENT_GATE>PROMOTE_RUSSIA>CRIMEA>UNRESOLVED",
        "note=PROMOTE_RUSSIA remains a census candidate, not a threshold-trigger confirmation",
    ]
    args.summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
