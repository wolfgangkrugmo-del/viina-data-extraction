#!/usr/bin/env python3
import csv
from pathlib import Path

p=Path('output/DEEP_COMPLETENESS_REBUILD_MATRIX_2022_2026.csv')
with p.open(encoding='utf-8',newline='') as f:
    r=csv.DictReader(f); fields=r.fieldnames; rows=list(r)
found=False
for x in rows:
    if x.get('MatrixRowID')=='SRC-2025-VIINA':
        found=True
        x['SearchStatus']='COMPLETED'
        x['CoverageStatus']='FULL_PROTOCOL'
        x['UnresolvedRows']='0'
        x['ReviewStatus']='COMPLETE'
        x['DedupeReviewStatus']='COMPLETE'
        x['EvidenceArchivePath']='|'.join([
            'output/VIINA_2025_REBUILD.csv',
            'output/VIINA_2025_POST_EXACT_DEDUPE_REVIEW.csv',
            'output/VIINA_2025_RUSSIA_PRIORITY.csv',
            'output/VIINA_2025_STAGE1_SUMMARY.txt',
            'output/VIINA_2025_STAGE1_PROVENANCE.txt',
            'output/VIINA_2025_RUSSIA_PRIORITY_MANUAL_REVIEW_V1.csv',
            'output/VIINA_2025_UNKNOWN_REDUCTION_V2.csv',
            'output/VIINA_2025_UNKNOWN_HIGH_PRIORITY_MANUAL_REVIEW_V2.csv',
            'output/VIINA_2025_UNKNOWN_M1_MANUAL_REVIEW_V1.csv',
            'output/VIINA_2025_UNKNOWN_M2_MANUAL_REVIEW_V2.csv',
            'output/VIINA_2025_LOW_PRIORITY_RESIDUAL_AUDIT_V1.csv',
            'output/VIINA_2025_LOW_PRIORITY_RESIDUAL_MANUAL_REVIEW_V1.csv',
            'output/VIINA_2025_LANE_CLOSURE_V1.txt'])
        x['CandidateCensusComplete']='FALSE'
        x['Notes']='VIINA 2025 stable lane fully reviewed and deduplicated for census relevance; outcome-relevant unresolved rows=0. Low-priority residual audit covered all 56 remaining low-priority rows (14 composite flags plus one L2 cross-border geocode manually reviewed; 41 deterministic Crimea no-leak rows). Russia-proper discoveries remain CENSUS_CANDIDATE_ONLY pending independent-source confirmation. Overall 2025 census remains incomplete because Reuters and remaining C1-C7 completeness gates are not complete.'
if not found:
    raise SystemExit('SRC-2025-VIINA row missing')
with p.open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
