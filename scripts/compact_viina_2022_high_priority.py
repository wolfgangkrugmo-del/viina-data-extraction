#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,re
from pathlib import Path

def clean(s:str,limit:int=650)->str:
    s=re.sub(r"\s+"," ",(s or "")).strip()
    return s if len(s)<=limit else s[:limit-3]+"..."

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args()
    with a.input.open(encoding='utf-8',newline='') as f:
        r=csv.DictReader(f); rows=list(r)
    if len(rows)!=50: raise RuntimeError(f'expected 50 rows, found {len(rows)}')
    fields=['event_id_1pd','date','R5PriorityV3','sources_matching','source_urls','asciiname','ADM1_NAME','ADM2_NAME','location_method','nearest_ru_distance_km','nearest_ru_name','a_ukr','a_rus_init','a_rus','ua_actor_text_terms','target_classes','target_terms','attack_terms','text_excerpt']
    out=[]
    for x in rows:
        out.append({
            'event_id_1pd':x.get('event_id_1pd',''),'date':x.get('date',''),'R5PriorityV3':x.get('R5PriorityV3',''),
            'sources_matching':x.get('sources_matching',''),'source_urls':clean(x.get('source_urls',''),300),
            'asciiname':x.get('asciiname',''),'ADM1_NAME':x.get('ADM1_NAME',''),'ADM2_NAME':x.get('ADM2_NAME',''),
            'location_method':x.get('location_method',''),'nearest_ru_distance_km':x.get('nearest_ru_distance_km',''),
            'nearest_ru_name':x.get('nearest_ru_name',''),'a_ukr':x.get('a_ukr',''),'a_rus_init':x.get('a_rus_init',''),'a_rus':x.get('a_rus',''),
            'ua_actor_text_terms':x.get('ua_actor_text_terms',''),'target_classes':x.get('target_classes',''),
            'target_terms':clean(x.get('target_terms',''),180),'attack_terms':x.get('attack_terms',''),
            'text_excerpt':clean(x.get('representative_text',''),650)
        })
    with a.output.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(out)
if __name__=='__main__': main()
