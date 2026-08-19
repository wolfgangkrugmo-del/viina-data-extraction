#!/usr/bin/env python3
import csv
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'
LOG=OUT/'REUTERS_2025_DEEP_SEARCH_LOG_V1.csv'
REC=OUT/'REUTERS_2025_VIINA_RECONCILIATION_V1.csv'
REPORT=OUT/'REUTERS_2025_86_101_CELL_DIAGNOSTIC_V1.csv'
DETAIL=OUT/'REUTERS_2025_86_101_ROW_DIAGNOSTIC_V1.csv'

with LOG.open(encoding='utf-8',newline='') as f:
    log=list(csv.DictReader(f))
with REC.open(encoding='utf-8',newline='') as f:
    rec=list(csv.DictReader(f))

fam_map={'R1':'R1_ENERGY_REFINING','R2':'R2_ENERGY_STORAGE_EXPORT','R3':'R3_PIPELINE_PUMPING','R4':'R4_DEFENSE_INDUSTRY','R5':'R5_STRATEGIC_AIR','R6':'R6_GRID_SUPPORT','R7':'R7_LOGISTICS_OTHER'}

def qtr(d):
    m=int(d[5:7])
    return 'Q1' if m<=3 else 'Q2' if m<=6 else 'Q3' if m<=9 else 'Q4'

expected={(r['Quarter'],r['SearchFamily']):int(r['NamedReutersDirectComponents']) for r in log}
by=defaultdict(list)
for r in rec:
    key=(qtr(r['CanonicalEventDate']),fam_map[r['SearchFamily']])
    by[key].append(r)

# Known non-direct reconciliation rows established by frozen artifact text/status.
known_extra={
 'R25R-0060':'OSC_ROUTED','R25R-0061':'OSC_ROUTED','R25R-0062':'OSC_ROUTED','R25R-0063':'OSC_ROUTED','R25R-0064':'OSC_ROUTED',
 'R25R-0087':'VIINA_ONLY_RECON_COMPONENT','R25R-0088':'VIINA_ONLY_RECON_COMPONENT','R25R-0089':'VIINA_ONLY_RECON_COMPONENT',
 'R25R-0096':'LATE_RECON_CORRECTION','R25R-0097':'LATE_RECON_CORRECTION','R25R-0098':'LATE_RECON_CORRECTION','R25R-0099':'LATE_RECON_CORRECTION','R25R-0100':'LATE_RECON_CORRECTION','R25R-0101':'LATE_RECON_CORRECTION',
}

rows=[]
cell_rows=[]
for key in sorted(expected):
    rr=sorted(by.get(key,[]), key=lambda x:int(x['ReutersReconID'].split('-')[1]))
    exp=expected[key]
    fixed_extra=[r for r in rr if r['ReutersReconID'] in known_extra]
    candidates=[r for r in rr if r['ReutersReconID'] not in known_extra]
    excess=max(0,len(candidates)-exp)
    unresolved_extra_ids=set(r['ReutersReconID'] for r in candidates[-excess:]) if excess else set()
    direct_count=0
    for r in rr:
        rid=r['ReutersReconID']
        if rid in known_extra:
            cls=known_extra[rid]
        elif rid in unresolved_extra_ids:
            cls='UNRESOLVED_EXTRA'
        else:
            cls='DIRECT_COMPONENT'
            direct_count+=1
        rows.append({
            'ReutersReconID':rid,'CanonicalEventDate':r['CanonicalEventDate'],'Quarter':key[0],'SearchFamily':key[1],
            'TargetOrEvent':r['TargetOrEvent'],'ReconciliationStatus':r['ReconciliationStatus'],'BridgeClass':cls,
            'EvidenceNote':r['EvidenceNote']})
    cell_rows.append({'Quarter':key[0],'SearchFamily':key[1],'FrozenDirectCount':exp,'ReconciliationRows':len(rr),
                      'KnownExtraRows':len(fixed_extra),'DirectCandidateRows':len(candidates),'UnresolvedExcessRows':excess,
                      'ProvisionalDirectAssigned':direct_count,'BalanceDelta':direct_count-exp})

with REPORT.open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=cell_rows[0].keys()); w.writeheader(); w.writerows(cell_rows)
with DETAIL.open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

print('search_direct_total=',sum(expected.values()))
print('reconciliation_total=',len(rec))
print('known_extra_total=',sum(1 for r in rec if r['ReutersReconID'] in known_extra))
print('unresolved_extra_total=',sum(1 for r in rows if r['BridgeClass']=='UNRESOLVED_EXTRA'))
for c in cell_rows:
    if c['ReconciliationRows'] != c['FrozenDirectCount'] or c['KnownExtraRows'] or c['UnresolvedExcessRows']:
        print(c)
