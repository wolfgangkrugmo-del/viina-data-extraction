#!/usr/bin/env python3
import csv
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'output'/'DEEP_COMPLETENESS_REBUILD_MATRIX_2022_2026.csv'
with p.open(encoding='utf-8',newline='') as f:
    rows=list(csv.DictReader(f)); fields=f.fieldnames
found=False
for r in rows:
    if r['MatrixRowID']=='SRC-2025-REUTERS':
        found=True
        r['AccessStatus']='AVAILABLE'
        r['SearchStatus']='COMPLETED'
        r['CoverageStatus']='FULL_PROTOCOL'
        r['DependencyAuditStatus']='PARTLY_DERIVATIVE'
        r['QueryProtocolVersion']='REUTERS_2025_DEEP_SEARCH_PROTOCOL_V1'
        r['QueryProtocolNotes']='28/28 frozen Reuters cells completed; candidate-row coding and dedupe structurally complete; source acceptance still blocked by unproven exact 86-direct-component to 101-reconciliation-row historical bridge.'
        r['SearchCompletedAt']='2026-08-19'
        r['RawHits']='86'
        r['CandidateRows']='100'
        r['IncludedRussiaProper']='47'
        r['ExcludedOutsideRussiaProper']='0'
        r['ExcludedCrimeaScope']='0'
        r['ExcludedNotEvent']='17'
        r['ExcludedOtherScope']='0'
        r['DuplicateRows']='33'
        r['UnresolvedRows']='3'
        r['NewUniqueAfterMerge']='47'
        r['SearchPassCount']='28'
        r['StopRuleStatus']='NOT_EVALUATED'
        r['EvidenceArchivePath']='output/REUTERS_2025_DEEP_SEARCH_LOG_V1.csv|output/REUTERS_2025_VIINA_RECONCILIATION_V1.csv|output/REUTERS_2025_DEPENDENCY_AUDIT_V1.txt|output/REUTERS_2025_FINAL_DISPOSITION_9_V1.csv|output/REUTERS_2025_PROVENANCE_LINKAGE_5_V1.csv|output/REUTERS_2025_CONFIRMED_NEW_EVENTS_V4.csv|output/REUTERS_2025_CANDIDATE_DEDUPE_LEDGER_V1.csv|output/REUTERS_2025_CLOSURE_FORMAL_AUDIT_V3.txt|output/REUTERS_2025_CANDIDATE_LEDGER_CLOSURE_STATUS_V3.txt'
        r['CandidateRegisterVersion']='REUTERS_2025_CANDIDATE_DEDUPE_LEDGER_V1|REUTERS_2025_CONFIRMED_NEW_EVENTS_V4'
        r['ReviewStatus']='COMPLETE'
        r['DedupeReviewStatus']='COMPLETE'
        for c in ['C1_TimeCoverage','C2_IndependentDiscovery','C3_AllCandidatesCoded','C4_DedupeComplete','C5_NoOutcomeRelevantUnresolved','C6_SourceConvergence','C7_VersionFrozen']:
            r[c]='NA'
        r['RowAcceptanceStatus']='NOT_READY'
        r['YearAcceptanceStatus']='NA'
        r['CandidateCensusComplete']='FALSE'
        r['Notes']='Formal closure audit completed 2026-08-19. Candidate-level coding/dedupe complete; confirmed Reuters-new vs reviewed VIINA = +47. Three DG_REUTERS outcome-relevant unresolved records remain (Engels/Kombinat Kristall physical effect; Shatura eligibility; Belgorod dam eligibility). Source-row PASS is withheld because the frozen log count of 86 Reuters-direct components is not exactly row-level bridged to the 101-row historical reconciliation. CandidateCensusComplete remains FALSE.'
if not found: raise SystemExit('SRC-2025-REUTERS not found')
with p.open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
print('updated SRC-2025-REUTERS without promoting RowAcceptanceStatus')
# Trigger marker: formal audited matrix application, 2026-08-19.
