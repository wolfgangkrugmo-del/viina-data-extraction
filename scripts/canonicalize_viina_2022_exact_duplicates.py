#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


def as_int(v: str, default: int = 10**18) -> int:
    try:
        return int((v or "").strip())
    except Exception:
        return default


def canonical_key(row: dict[str, str]):
    # VIINA adjacent-day replicas with identical URL/text are one report-level cluster.
    # Keep the earliest VIINA date, then the lowest numeric event_id_1pd as a stable
    # representative. CanonicalEventDate remains subject to later event-level review.
    return (as_int(row.get("date", "")), as_int(row.get("event_id_1pd", "")), row.get("event_id_1pd", ""))


def load_matrix(path: Path):
    with path.open(encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        fields = list(r.fieldnames or [])
        rows = list(r)
    return fields, rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--all-output", type=Path, required=True)
    ap.add_argument("--review-output", type=Path, required=True)
    ap.add_argument("--cluster-output", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True)
    ap.add_argument("--matrix", type=Path, required=True)
    args = ap.parse_args()

    with args.input.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        in_fields = list(reader.fieldnames or [])
        rows = list(reader)

    if len(rows) != 639:
        raise RuntimeError(f"Expected 639 triage rows, found {len(rows)}")

    clusters: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in rows:
        cid = (r.get("ExactReportDuplicateCluster") or "").strip()
        if cid:
            clusters[cid].append(r)

    if len(clusters) != 91:
        raise RuntimeError(f"Expected 91 exact duplicate clusters, found {len(clusters)}")

    clustered_rows = sum(len(v) for v in clusters.values())
    if clustered_rows != 223:
        raise RuntimeError(f"Expected 223 rows in exact duplicate clusters, found {clustered_rows}")

    canonical_for: dict[str, str] = {}
    cluster_meta = []
    for cid, members in sorted(clusters.items()):
        if len(members) < 2:
            raise RuntimeError(f"Cluster {cid} has fewer than two rows")
        canon = min(members, key=canonical_key)
        canon_id = canon.get("event_id_1pd", "")
        dates = sorted({r.get("date", "") for r in members})
        ids = sorted((r.get("event_id_1pd", "") for r in members), key=lambda x: as_int(x))
        for r in members:
            canonical_for[r.get("event_id_1pd", "")] = canon_id
        cluster_meta.append({
            "DedupeClusterID": cid,
            "CanonicalEventID1pd": canon_id,
            "ClusterRowCount": str(len(members)),
            "MemberEventIDs": "|".join(ids),
            "MemberDates": "|".join(dates),
            "SourceURLs": canon.get("source_urls", ""),
            "RepresentativeText": canon.get("representative_text", ""),
            "DedupeBasis": "EXACT_SOURCE_URL_AND_REPRESENTATIVE_TEXT",
            "CanonicalSelectionRule": "EARLIEST_VIINA_DATE_THEN_LOWEST_EVENT_ID_1PD",
            "CandidateCensusComplete": "FALSE",
        })

    out_rows = []
    review_rows = []
    counts = Counter()
    priority_before = Counter()
    priority_after = Counter()

    for r in rows:
        x = dict(r)
        eid = r.get("event_id_1pd", "")
        cid = (r.get("ExactReportDuplicateCluster") or "").strip()
        priority = r.get("TriagePriority", "")
        priority_before[priority] += 1

        if cid:
            canon_id = canonical_for[eid]
            if eid == canon_id:
                decision = "CANONICAL"
                counts["canonical_cluster_rows"] += 1
            else:
                decision = "DUPLICATE_LINKED"
                counts["duplicate_rows_removed_from_manual_queue"] += 1
        else:
            canon_id = eid
            decision = "UNIQUE_EXACT_REPORT_LEVEL"
            counts["unique_noncluster_rows"] += 1

        x.update({
            "DedupeClusterID": cid,
            "DedupeDecision": decision,
            "CanonicalEventID1pd": canon_id,
            "DedupeBasis": "EXACT_SOURCE_URL_AND_REPRESENTATIVE_TEXT" if cid else "NO_EXACT_REPORT_DUPLICATE",
            "EventLevelDedupeStatus": "PENDING",
            "CandidateCensusComplete": "FALSE",
        })
        out_rows.append(x)

        if decision != "DUPLICATE_LINKED":
            review_rows.append(x)
            priority_after[priority] += 1

    if counts["canonical_cluster_rows"] != 91:
        raise RuntimeError("Canonical cluster row count mismatch")
    if counts["duplicate_rows_removed_from_manual_queue"] != 132:
        raise RuntimeError("Expected 132 duplicate rows to remove")
    if len(review_rows) != 507:
        raise RuntimeError(f"Expected 507 post-dedupe review rows, found {len(review_rows)}")

    extra_fields = [
        "DedupeClusterID", "DedupeDecision", "CanonicalEventID1pd",
        "DedupeBasis", "EventLevelDedupeStatus"
    ]
    seen = set()
    out_fields = [c for c in in_fields + extra_fields if not (c in seen or seen.add(c))]

    args.all_output.parent.mkdir(parents=True, exist_ok=True)
    for path, data in [(args.all_output, out_rows), (args.review_output, review_rows)]:
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=out_fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(data)

    cluster_fields = [
        "DedupeClusterID", "CanonicalEventID1pd", "ClusterRowCount", "MemberEventIDs",
        "MemberDates", "SourceURLs", "RepresentativeText", "DedupeBasis",
        "CanonicalSelectionRule", "CandidateCensusComplete"
    ]
    with args.cluster_output.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cluster_fields)
        w.writeheader()
        w.writerows(cluster_meta)

    # Update only verified dedupe progress; do not claim event-level dedupe complete.
    mfields, mrows = load_matrix(args.matrix)
    found = False
    for r in mrows:
        if r.get("MatrixRowID") == "SRC-2022-VIINA":
            found = True
            r["DuplicateRows"] = "132"
            r["UnresolvedRows"] = "507"
            r["DedupeReviewStatus"] = "IN_PROGRESS"
            r["CandidateCensusComplete"] = "FALSE"
            r["EvidenceArchivePath"] = (
                "output/VIINA_2022_REBUILD.csv|output/VIINA_2022_REBUILD_SUMMARY.txt|"
                "output/VIINA_2022_REBUILD_PROVENANCE.txt|output/VIINA_2022_TRIAGE.csv|"
                "output/VIINA_2022_EXACT_DEDUPE.csv|output/VIINA_2022_POST_EXACT_DEDUPE_REVIEW.csv|"
                "output/VIINA_2022_EXACT_DUPLICATE_CLUSTERS.csv"
            )
            r["Notes"] = (
                "Full actor-independent VIINA 2022 protocol completed. Exact report-level dedupe: "
                "91 clusters / 223 rows canonicalized; 132 duplicate rows linked and removed from the "
                "manual queue; 507 canonical/unique rows remain. Event-level dedupe and substantive "
                "review remain in progress."
            )
    if not found:
        raise RuntimeError("SRC-2022-VIINA matrix row missing")
    with args.matrix.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=mfields)
        w.writeheader()
        w.writerows(mrows)

    p1p2_before = priority_before["P1_RUSSIA_UA_ACTOR"] + priority_before["P2_RUSSIA_FROM_AMBIGUOUS"]
    p1p2_after = priority_after["P1_RUSSIA_UA_ACTOR"] + priority_after["P2_RUSSIA_FROM_AMBIGUOUS"]
    with args.summary.open("w", encoding="utf-8") as f:
        f.write("protocol=VIINA_2022_EXACT_REPORT_DEDUPE_V1\n")
        f.write(f"input_rows={len(rows)}\n")
        f.write(f"exact_duplicate_clusters={len(clusters)}\n")
        f.write(f"rows_in_clusters={clustered_rows}\n")
        f.write(f"canonical_cluster_rows={counts['canonical_cluster_rows']}\n")
        f.write(f"duplicate_rows_linked={counts['duplicate_rows_removed_from_manual_queue']}\n")
        f.write(f"unique_noncluster_rows={counts['unique_noncluster_rows']}\n")
        f.write(f"post_exact_dedupe_review_rows={len(review_rows)}\n")
        f.write(f"priority_russia_rows_before={p1p2_before}\n")
        f.write(f"priority_russia_rows_after={p1p2_after}\n")
        f.write(f"p1_before={priority_before['P1_RUSSIA_UA_ACTOR']}\n")
        f.write(f"p1_after={priority_after['P1_RUSSIA_UA_ACTOR']}\n")
        f.write(f"p2_before={priority_before['P2_RUSSIA_FROM_AMBIGUOUS']}\n")
        f.write(f"p2_after={priority_after['P2_RUSSIA_FROM_AMBIGUOUS']}\n")
        f.write("event_level_dedupe_status=PENDING\n")
        f.write("dedupe_review_status=IN_PROGRESS\n")
        f.write("candidate_census_complete=FALSE\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
