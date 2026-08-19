#!/usr/bin/env python3
import csv
from pathlib import Path

src=Path('output/VIINA_2025_UNKNOWN_REDUCTION_V2.csv')
with src.open(encoding='utf-8',newline='') as f:
    rd=csv.DictReader(f)
    fields=list(rd.fieldnames or [])
    rows=list(rd)

m1=[r for r in rows if r.get('UnknownPriorityV2')=='M1_UA_ACTOR_UA_GEO']
m2=[r for r in rows if r.get('UnknownPriorityV2')=='M2_REMAINS_UNRESOLVED']
assert len(m1)==16, len(m1)
assert len(m2)==6, len(m2)
for path,data in [
    (Path('output/VIINA_2025_UNKNOWN_M1_REVIEW_BLOCK.csv'),m1),
    (Path('output/VIINA_2025_UNKNOWN_M2_REVIEW_BLOCK.csv'),m2),
]:
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader(); w.writerows(data)
print(f'M1={len(m1)} M2={len(m2)}')
