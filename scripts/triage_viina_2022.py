#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import re
from collections import Counter, defaultdict
from pathlib import Path

CRIMEA = re.compile(r"\b(crimea|krym|sevastopol|feodosia|simferopol|dzhankoi|kerch|saki)\b|крим|крым|севастопол|феодос|симферопол|джанко|керч|саки", re.I)
OCCUPIED_UA = re.compile(r"\b(donetsk|luhansk|lugansk|mariupol|melitopol|berdiansk|berdyansk|kherson|zaporizhzhia|zaporozhye)\b|донецьк|донецк|луганськ|луганск|маріупол|мариупол|мелітопол|мелитопол|бердянськ|бердянск|херсон|запоріж|запорож", re.I)
RUSSIA_EXPLICIT = re.compile(r"\b(in|inside|within) russia\b|\brussian federation\b|\bon russian territory\b|\bв россии\b|\bв рф\b|\bна территории россии\b|\bу росії\b|\bна території росії\b", re.I)
RUSSIA_PLACES = re.compile(
    r"\b(belgorod|bryansk|kursk|rostov|krasnodar|voronezh|oryol|orel|kaluga|tula|lipetsk|tambov|ryazan|smolensk|pskov|leningrad|novgorod|saratov|samara|tatarstan|bashkortostan|nizhny novgorod|volgograd|astrakhan|stavropol|dagestan|komi|murmansk|arkhangelsk|yaroslavl|tver|moscow)\b|"
    r"белгород|брянск|курск|ростов|краснодар|воронеж|ор[её]л|калуг|тул[аеы]?|липецк|тамбов|рязан|смоленск|псков|ленинград|новгород|саратов|самар|татарстан|башк|нижн.{0,8}новгород|волгоград|астрахан|ставропол|дагестан|коми|мурманск|архангельск|ярослав|твер|москв",
    re.I,
)
FRESH = re.compile(r"\b(attacked|attack on|struck|hit|drone strike|missile strike|sabotage)\b|атаковал|атакували|ударил|ударили|уразил|уразили|вдарил|вдарили|влуч|поразил|поразили", re.I)
FOLLOWUP = re.compile(r"\b(after (?:the )?(?:strike|attack)|still burning|continues? to burn|satellite (?:image|images)|aftermath|repair|repairs)\b|після (?:удару|атаки)|после (?:удара|атаки)|продовжує.{0,12}гор|продолжа.{0,12}гор|супутников|спутников|наслідк|последств|ремонт", re.I)


def norm(v: str) -> str:
    return re.sub(r"\s+", " ", (v or "").strip().casefold())


def classify_scope(text: str):
    c = bool(CRIMEA.search(text))
    u = bool(OCCUPIED_UA.search(text))
    r_exp = bool(RUSSIA_EXPLICIT.search(text))
    r_place = bool(RUSSIA_PLACES.search(text))
    r = r_exp or r_place
    if c and r:
        return "CONFLICT_OR_COMPOSITE", "CRIMEA_AND_RUSSIA_TEXT"
    if u and r:
        return "CONFLICT_OR_COMPOSITE", "OCCUPIED_UA_AND_RUSSIA_TEXT"
    if c:
        return "CRIMEA_SEVASTOPOL", "CRIMEA_TEXT"
    if u:
        return "UKRAINE_OCCUPIED_OTHER", "OCCUPIED_UA_TEXT"
    if r_exp:
        return "RUSSIA_PROPER", "EXPLICIT_RUSSIA_TEXT"
    if r_place:
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


def load_matrix(path: Path):
    """Read matrix and repair only CSV overflow that belongs to final Notes field."""
    repaired_rows = 0
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, restkey="__EXTRA__", restval="")
        fields = list(reader.fieldnames or [])
        if not fields or fields[-1] != "Notes":
            raise RuntimeError("Matrix schema changed: Notes is not the final column")
        rows = []
        for line_no, row in enumerate(reader, start=2):
            extra = row.pop("__EXTRA__", None)
            if extra:
                # The matrix was originally written manually; unquoted commas in the
                # final Notes field are parsed as overflow columns. Since Notes is
                # schema-verified as the last field, rejoin them losslessly here.
                row["Notes"] = (row.get("Notes") or "") + "," + ",".join(v or "" for v in extra)
                repaired_rows += 1
            for key in fields:
                if row.get(key) is None:
                    row[key] = ""
            rows.append(row)
    return fields, rows, repaired_rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--priority-output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    ap.add_argument("--matrix", type=Path, required=True)
    args = ap.parse_args()

    with args.input.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        review = [r for r in reader if (r.get("TriageStatus") or "").startswith("REVIEW_")]
        in_fields = list(reader.fieldnames or [])

    groups = defaultdict(list)
    for r in review:
        k = (norm(r.get("source_urls", "")), norm(r.get("representative_text", "")))
        if k != ("", ""):
            groups[k].append(r.get("event_id_1pd", ""))
    dup_id = {}
    cluster_no = 0
    for k, ids in groups.items():
        if len(ids) > 1:
            cluster_no += 1
            cid = f"EXACT2022-{cluster_no:04d}"
            for eid in ids:
                dup_id[eid] = cid

    counts = Counter()
    enriched = []
    priority = []
    for r in review:
        text = r.get("representative_text", "") or ""
        scope, scope_reason = classify_scope(text)
        event_form, event_reason = classify_event(text)
        old = r.get("TriageStatus", "")
        exact_cluster = dup_id.get(r.get("event_id_1pd", ""), "")

        if scope == "RUSSIA_PROPER" and old == "REVIEW_TEXT_RUSSIA_UA_ACTOR":
            p = "P1_RUSSIA_UA_ACTOR"
        elif scope == "RUSSIA_PROPER":
            p = "P2_RUSSIA_FROM_AMBIGUOUS"
        elif scope == "CONFLICT_OR_COMPOSITE":
            p = "P3_SCOPE_CONFLICT_COMPOSITE"
        elif scope == "CRIMEA_SEVASTOPOL":
            p = "P4_CRIMEA"
        elif scope == "UKRAINE_OCCUPIED_OTHER":
            p = "P5_OCCUPIED_UA_OTHER"
        else:
            p = "P6_SCOPE_UNKNOWN"

        x = dict(r)
        x.update({
            "ScopeAuto": scope,
            "ScopeReason": scope_reason,
            "EventFormAuto": event_form,
            "EventFormReason": event_reason,
            "ExactReportDuplicateCluster": exact_cluster,
            "TriagePriority": p,
            "ManualReviewRequired": "TRUE",
            "CandidateCensusComplete": "FALSE",
        })
        enriched.append(x)
        counts[p] += 1
        counts[f"SCOPE_{scope}"] += 1
        counts[f"EVENT_{event_form}"] += 1
        if exact_cluster:
            counts["ROWS_IN_EXACT_REPORT_DUP_CLUSTERS"] += 1
        if p in {"P1_RUSSIA_UA_ACTOR", "P2_RUSSIA_FROM_AMBIGUOUS"}:
            priority.append(x)

    out_fields = in_fields + [
        "ScopeAuto", "ScopeReason", "EventFormAuto", "EventFormReason",
        "ExactReportDuplicateCluster", "TriagePriority", "ManualReviewRequired"
    ]
    seen = set()
    out_fields = [c for c in out_fields if not (c in seen or seen.add(c))]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    for path, rows in [(args.output, enriched), (args.priority_output, priority)]:
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)

    unique_clusters = len(set(dup_id.values()))

    mfields, mrows, repaired_matrix_rows = load_matrix(args.matrix)
    found = False
    for r in mrows:
        if r.get("MatrixRowID") == "SRC-2022-VIINA":
            found = True
            r["SearchStatus"] = "COMPLETED"
            r["CoverageStatus"] = "FULL_PROTOCOL"
            r["QueryProtocolVersion"] = "VIINA_2022_ACTOR_INDEPENDENT_V1"
            r["RawHits"] = "2060"
            r["CandidateRows"] = str(len(review))
            r["UnresolvedRows"] = str(len(review))
            r["SearchPassCount"] = "1"
            r["EvidenceArchivePath"] = "output/VIINA_2022_REBUILD.csv|output/VIINA_2022_REBUILD_SUMMARY.txt|output/VIINA_2022_REBUILD_PROVENANCE.txt|output/VIINA_2022_TRIAGE.csv"
            r["ReviewStatus"] = "IN_PROGRESS"
            r["DedupeReviewStatus"] = "NOT_STARTED"
            r["RowAcceptanceStatus"] = "NOT_READY"
            r["CandidateCensusComplete"] = "FALSE"
            r["Notes"] = "Full actor-independent VIINA 2022 protocol completed: 2060 raw text-match groups reconciled; 1421 machine non-candidates documented; 639 review rows under triage. a_ukr_init coverage is zero and is not an exclusion gate."
    if not found:
        raise RuntimeError("SRC-2022-VIINA row not found in matrix")
    with args.matrix.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=mfields, extrasaction="raise")
        w.writeheader()
        w.writerows(mrows)

    with args.summary.open("w", encoding="utf-8") as f:
        f.write("protocol=VIINA_2022_REVIEW_TRIAGE_V1\n")
        f.write(f"input_review_rows={len(review)}\n")
        f.write(f"priority_russia_rows={len(priority)}\n")
        for key in [
            "P1_RUSSIA_UA_ACTOR", "P2_RUSSIA_FROM_AMBIGUOUS", "P3_SCOPE_CONFLICT_COMPOSITE",
            "P4_CRIMEA", "P5_OCCUPIED_UA_OTHER", "P6_SCOPE_UNKNOWN"
        ]:
            f.write(f"{key}={counts[key]}\n")
        f.write(f"exact_report_duplicate_clusters={unique_clusters}\n")
        f.write(f"rows_in_exact_report_duplicate_clusters={counts['ROWS_IN_EXACT_REPORT_DUP_CLUSTERS']}\n")
        f.write(f"matrix_rows_with_notes_overflow_repaired={repaired_matrix_rows}\n")
        f.write("matrix_overflow_repair_policy=REJOIN_TO_FINAL_NOTES_ONLY\n")
        f.write("manual_review_required_for_all_triage_rows=TRUE\n")
        f.write("candidate_census_complete=FALSE\n")

    print(
        f"review_rows={len(review)} priority_russia={len(priority)} "
        f"exact_dup_clusters={unique_clusters} repaired_matrix_rows={repaired_matrix_rows}"
    )
    for p in [args.output, args.priority_output, args.summary, args.matrix]:
        print(hashlib.sha256(p.read_bytes()).hexdigest(), p)


if __name__ == "__main__":
    main()
