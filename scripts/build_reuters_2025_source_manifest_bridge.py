#!/usr/bin/env python3
import csv,re
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output'
LOG=OUT/'REUTERS_2025_DEEP_SEARCH_LOG_V1.csv'
REC=OUT/'REUTERS_2025_VIINA_RECONCILIATION_V1.csv'
RAW=OUT/'REUTERS_2025_DEEP_RAW_HITS_V1.csv'
MAN=OUT/'REUTERS_2025_SOURCE_COMPONENT_MANIFEST_V1.csv'
BR=OUT/'REUTERS_2025_101_ROW_BRIDGE_V1.csv'
AUD=OUT/'REUTERS_2025_SOURCE_BRIDGE_FORMAL_AUDIT_V1.txt'

with LOG.open(encoding='utf-8',newline='') as f: log=list(csv.DictReader(f))
with REC.open(encoding='utf-8',newline='') as f: rec=list(csv.DictReader(f))
with RAW.open(encoding='utf-8',newline='') as f: raw=list(csv.DictReader(f))
assert sum(int(r['NamedReutersDirectComponents']) for r in log)==86
assert len(rec)==101

fam_short={'R1_ENERGY_REFINING':'R1','R2_ENERGY_STORAGE_EXPORT':'R2','R3_PIPELINE_PUMPING':'R3','R4_DEFENSE_INDUSTRY':'R4','R5_STRATEGIC_AIR':'R5','R6_GRID_SUPPORT':'R6','R7_LOGISTICS_OTHER':'R7'}
def qtr(d):
 m=int(d[5:7]); return 'Q1' if m<=3 else 'Q2' if m<=6 else 'Q3' if m<=9 else 'Q4'
def norm(s): return re.sub(r'[^a-z0-9]+',' ',(s or '').lower()).strip()

manifest=[]; slots=defaultdict(list)
for lr in log:
 n=int(lr['NamedReutersDirectComponents'])
 for i in range(1,n+1):
  sid=f"R25S-{lr['Quarter']}-{fam_short[lr['SearchFamily']]}-{i:02d}"
  row={'SourceComponentID':sid,'Quarter':lr['Quarter'],'SearchFamily':lr['SearchFamily'],'CellOrdinal':i,
       'RecoveredCanonicalDate':'','RecoveredTargetOrEvent':'','RecoveredFrom':'SEARCH_LOG_COUNT_ONLY',
       'RecoveryStatus':'UNRECOVERED_IDENTITY','Anchor':lr['KeyReutersAnchors'],'FinalDisposition':'','Notes':''}
  manifest.append(row); slots[(lr['Quarter'],fam_short[lr['SearchFamily']])].append(row)

used=set()
for rr in raw:
 key=(qtr(rr['CanonicalEventDate']),fam_short[rr['SearchFamily']])
 choices=[s for s in slots[key] if s['SourceComponentID'] not in used]
 if not choices: continue
 s=choices[0]; used.add(s['SourceComponentID'])
 s['RecoveredCanonicalDate']=rr['CanonicalEventDate']; s['RecoveredTargetOrEvent']=rr['TargetOrCluster']
 s['RecoveredFrom']=rr['ReutersHitID']; s['RecoveryStatus']='EXACT'; s['FinalDisposition']=rr['ReutersStatus']
 s['Notes']=rr['PhysicalEffectEvidence']

OSC={'R25R-0060','R25R-0061','R25R-0062','R25R-0063','R25R-0064'}
VIINA_ADD={'R25R-0040','R25R-0065','R25R-0081','R25R-0082','R25R-0087','R25R-0088','R25R-0089'}
CORR={'R25R-0067','R25R-0096','R25R-0097','R25R-0098','R25R-0099'}
FOLLOW={'R25R-0100','R25R-0101'}
SPLIT={'R25R-0009','R25R-0083','R25R-0084'}
def tclass(rid):
 if rid in OSC:return 'OSC-Routing'
 if rid in VIINA_ADD:return 'VIINA-Zusatz'
 if rid in CORR:return 'Korrektur'
 if rid in FOLLOW:return 'Follow-up'
 if rid in SPLIT:return 'Split'
 return '1:1'

bycell=defaultdict(list)
for s in manifest: bycell[(s['Quarter'],fam_short[s['SearchFamily']])].append(s)
def score(r,s):
 sc=0
 if s['RecoveryStatus']=='EXACT':
  if s['RecoveredCanonicalDate']==r['CanonicalEventDate']: sc+=5
  a=norm(r['TargetOrEvent']); b=norm(s['RecoveredTargetOrEvent'])
  if a and b and (a in b or b in a): sc+=8
  sc+=len(set(a.split())&set(b.split()))
 return sc

bridge=[]
for r in rec:
 rid=r['ReutersReconID']; cls=tclass(rid); key=(qtr(r['CanonicalEventDate']),r['SearchFamily'])
 sid=''; basis=''
 if cls=='OSC-Routing': basis='Open Source Centre data embedded/used by Reuters; external DG_OSINT_SPECIALIST path.'
 elif cls=='VIINA-Zusatz': basis='Reconciliation/VIINA-side addition or component not established as a frozen Reuters-direct source component.'
 else:
  ranked=sorted(((score(r,s),s) for s in bycell.get(key,[])), key=lambda x:x[0], reverse=True)
  if ranked and ranked[0][0]>=8:
   sid=ranked[0][1]['SourceComponentID']; basis='Exact frozen raw-hit date/target match.'
 bridge.append({'ReutersReconID':rid,'CanonicalEventDate':r['CanonicalEventDate'],'TargetOrEvent':r['TargetOrEvent'],
                'SearchFamily':r['SearchFamily'],'TransformationClass':cls,'SourceComponentID':sid,
                'ExternalPath':('DG_OSINT_SPECIALIST' if cls=='OSC-Routing' else 'VIINA_RECONCILIATION' if cls=='VIINA-Zusatz' else ''),
                'MappingStatus':('EXACT' if sid else 'EXTERNAL' if cls in {'OSC-Routing','VIINA-Zusatz'} else 'UNRESOLVED'),
                'MappingBasis':basis})

used_by_bridge=set(b['SourceComponentID'] for b in bridge if b['SourceComponentID'])
for b in bridge:
 if b['MappingStatus']!='UNRESOLVED': continue
 key=(qtr(b['CanonicalEventDate']),b['SearchFamily'])
 available=[s for s in bycell.get(key,[]) if s['SourceComponentID'] not in used_by_bridge]
 if available:
  s=available[0]; used_by_bridge.add(s['SourceComponentID'])
  if s['RecoveryStatus']=='UNRECOVERED_IDENTITY':
   s['RecoveredCanonicalDate']=b['CanonicalEventDate']; s['RecoveredTargetOrEvent']=b['TargetOrEvent']
   s['RecoveredFrom']='RECONCILIATION_INFERENCE'; s['RecoveryStatus']='ANCHORED_ONLY'
   s['Notes']='Identity inferred from cell quota plus R25R reconciliation; no frozen row-level ReutersHitID proves this exact source component.'
  b['SourceComponentID']=s['SourceComponentID']; b['MappingStatus']='ANCHORED_ONLY'
  b['MappingBasis']='Assigned within frozen search-cell quota; not row-level source-proven.'

for s in manifest:
 mapped=[b for b in bridge if b['SourceComponentID']==s['SourceComponentID']]
 if not mapped and s['RecoveryStatus']=='UNRECOVERED_IDENTITY':
  s['FinalDisposition']='UNRESOLVED_SOURCE_IDENTITY'
  s['Notes']='Frozen search log says this retained named Reuters-direct component existed, but no row-level identity can be recovered from frozen raw hits/reconciliation.'
 elif mapped:
  s['FinalDisposition']='BRIDGED'

allowed={'1:1','Split','Follow-up','VIINA-Zusatz','OSC-Routing','Korrektur','Non-Candidate'}
assert len(bridge)==101
assert all(b['TransformationClass'] in allowed for b in bridge)
with MAN.open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=manifest[0].keys()); w.writeheader(); w.writerows(manifest)
with BR.open('w',encoding='utf-8',newline='') as f:
 w=csv.DictWriter(f,fieldnames=bridge[0].keys()); w.writeheader(); w.writerows(bridge)
exact=sum(s['RecoveryStatus']=='EXACT' for s in manifest)
anch=sum(s['RecoveryStatus']=='ANCHORED_ONLY' for s in manifest)
unrec=sum(s['RecoveryStatus']=='UNRECOVERED_IDENTITY' for s in manifest)
row_exact=sum(b['MappingStatus']=='EXACT' for b in bridge)
row_anch=sum(b['MappingStatus']=='ANCHORED_ONLY' for b in bridge)
row_ext=sum(b['MappingStatus']=='EXTERNAL' for b in bridge)
row_unres=sum(b['MappingStatus']=='UNRESOLVED' for b in bridge)
bridge_complete=(exact==86 and anch==0 and unrec==0 and row_anch==0 and row_unres==0)
AUD.write_text(f'''REUTERS 2025 SOURCE COMPONENT / 101-ROW BRIDGE FORMAL AUDIT V1\n\nFrozen source components required: 86\nManifest rows: {len(manifest)}\nEXACT source identities: {exact}\nANCHORED_ONLY source identities: {anch}\nUNRECOVERED source identities: {unrec}\n\nR25R rows required: 101\nBridge rows: {len(bridge)}\nEXACT R25R mappings: {row_exact}\nANCHORED_ONLY R25R mappings: {row_anch}\nExplicit external VIINA/OSC mappings: {row_ext}\nUNRESOLVED R25R mappings: {row_unres}\n\nBridgeComplete={'TRUE' if bridge_complete else 'FALSE'}\nRowAcceptanceStatus={'PASS' if bridge_complete else 'NOT_READY'}\nCandidateCensusComplete=FALSE\n''',encoding='utf-8')
print('manifest',len(manifest),'exact',exact,'anchored',anch,'unrecovered',unrec)
print('bridge',len(bridge),'exact',row_exact,'anchored',row_anch,'external',row_ext,'unresolved',row_unres)
print('BridgeComplete=',bridge_complete)
