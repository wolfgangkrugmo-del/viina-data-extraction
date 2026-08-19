#!/usr/bin/env python3
import csv
from pathlib import Path

p=Path('output/DEEP_COMPLETENESS_REBUILD_MATRIX_2022_2026.csv')
with p.open(encoding='utf-8',newline='') as f:
    r=csv.DictReader(f); fields=r.fieldnames; rows=list(r)

found_2022=False
found_2023=False
for x in rows:
    if x.get('MatrixRowID')=='SRC-2022-VIINA':
        found_2022=True
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
    elif x.get('MatrixRowID')=='SRC-2023-VIINA':
        found_2023=True
        x['UnresolvedRows']='0'
        x['ReviewStatus']='COMPLETE'
        x['DedupeReviewStatus']='COMPLETE'
        x['EvidenceArchivePath']='|'.join([
            'output/VIINA_2023_REBUILD.csv','output/VIINA_2023_POST_EXACT_DEDUPE_REVIEW.csv','output/VIINA_2023_RUSSIA_PRIORITY.csv',
            'output/VIINA_2023_STAGE1_SUMMARY.txt','output/VIINA_2023_STAGE1_PROVENANCE.txt',
            'output/VIINA_2023_RUSSIA_PRIORITY_MANUAL_REVIEW_V1.csv',
            'output/VIINA_2023_UNKNOWN_HIGH_PRIORITY_MANUAL_REVIEW_V2.csv',
            'output/VIINA_2023_UNKNOWN_M2_MANUAL_REVIEW_V2.csv',
            'output/VIINA_2023_LOW_RESIDUAL_MANUAL_REVIEW_V1.csv',
            'output/VIINA_2023_LANE_CLOSURE_V1.txt'])
        x['Notes']='VIINA 2023 stable lane fully reviewed and deduplicated for census relevance; outcome-relevant unresolved rows=0. Two Russia-proper census candidates retained (Taman/Volna 2023-05-03 and Voronezh Rosneft 2023-12-12), both CENSUS_CANDIDATE_ONLY pending independent-source confirmation. Overall 2023 census remains incomplete because Reuters and remaining C1-C7 completeness gates are not complete.'
        x['CandidateCensusComplete']='FALSE'

if not found_2022:
    raise SystemExit('SRC-2022-VIINA row missing')
if not found_2023:
    raise SystemExit('SRC-2023-VIINA row missing')

with p.open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
