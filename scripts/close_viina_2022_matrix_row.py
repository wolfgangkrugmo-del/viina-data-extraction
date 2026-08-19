#!/usr/bin/env python3
import csv
from pathlib import Path

# Explicit retrigger marker: 2026-08-19. This script only mutates SRC-2022-VIINA.
p=Path('output/DEEP_COMPLETENESS_REBUILD_MATRIX_2022_2026.csv')
with p.open(encoding='utf-8',newline='') as f:
    r=csv.DictReader(f); fields=r.fieldnames; rows=list(r)
found=False
for x in rows:
    if x.get('MatrixRowID')=='SRC-2022-VIINA':
        found=True
        x['UnresolvedRows']='0'
        x['ReviewStatus']='COMPLETE'
        x['DedupeReviewStatus']='COMPLETE'
        x['EvidenceArchivePath']='|'.join([
            'output/VIINA_2022_REBUILD.csv','output/VIINA_2022_REBUILD_SUMMARY.txt','output/VIINA_2022_REBUILD_PROVENANCE.txt',
            'output/VIINA_2022_EXACT_DEDUPE.csv','output/VIINA_2022_EXACT_DEDUPE_SUMMARY.txt',
            'output/VIINA_2022_RUSSIA_PRIORITY_MANUAL_REVIEW_V2.csv',
            'output/VIINA_2022_R5_HIGH_PRIORITY_MANUAL_REVIEW_V3.csv',
            'output/VIINA_2022_R5_MEDIUM_PRIORITY_MANUAL_REVIEW_V3.csv',
            'output/VIINA_2022_LOW_PRIORITY_RESIDUAL_MANUAL_REVIEW_V1.csv',
            'output/VIINA_2022_LANE_CLOSURE_V1.txt'])
        x['Notes']='VIINA 2022 actor-independent lane fully reviewed and deduplicated for census relevance; outcome-relevant unresolved rows=0. Lane review and dedupe COMPLETE. Overall 2022 census remains incomplete because Reuters and remaining C1-C7 completeness gates are not complete.'
        x['CandidateCensusComplete']='FALSE'
if not found:
    raise SystemExit('SRC-2022-VIINA row missing')
with p.open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
