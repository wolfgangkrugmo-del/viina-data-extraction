#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,re
from pathlib import Path
from collections import Counter

WORD=r"A-Za-zА-Яа-яЁёІіЇїЄєҐґ0-9_"
def bounded(xs):
    return re.compile(rf"(?<![{WORD}])(?:{'|'.join(xs)})(?![{WORD}])",re.I|re.U)

# Russia-proper places/facilities implicated in known or plausible 2022 cross-border/deep-strike reporting.
RU_LEAK=bounded([
 r"belgorod",r"белгород",r"bryansk",r"брянск",r"kursk",r"курск",r"voronezh",r"воронеж",
 r"rostov",r"ростов",r"taganrog",r"таганрог",r"millerovo",r"миллерово",r"engels",r"энгельс",
 r"dyagilevo",r"дягилево",r"ryazan",r"рязань",r"novoshakhtinsk",r"новошахтинск",
 r"klimovo",r"климово",r"klintsy",r"клинцы",r"shebekino",r"шебекино",r"solokhi",r"солохи",
 r"valuyki",r"валуйки",r"grayvoron",r"graivoron",r"грайворон",r"taman",r"таман",
 r"krasnodar",r"краснодар",r"saratov",r"саратов",r"russia",r"россии",r"россия",r"рф"
])

YEAR_HINT=re.compile(r"/(20(?:23|24|25|26))/|[-_/](20(?:23|24|25|26))[-_/]",re.I)


def clean(s,limit=500):
    s=re.sub(r"\s+"," ",(s or "")).strip()
    return s if len(s)<=limit else s[:limit-3]+"..."

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--input',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); ap.add_argument('--summary',type=Path,required=True); a=ap.parse_args()
    with a.input.open(encoding='utf-8',newline='') as f:
        r=csv.DictReader(f); rows=[x for x in r if x.get('R5PriorityV3','').startswith('L')]
    if len(rows)!=247: raise RuntimeError(f'expected 247 low-priority rows, found {len(rows)}')
    out=[]; c=Counter()
    for x in rows:
        text=x.get('representative_text','') or ''
        url=x.get('source_urls','') or ''
        hits=sorted(set(m.group(0) for m in RU_LEAK.finditer(text)))
        yh=sorted(set(g for m in YEAR_HINT.finditer(url) for g in m.groups() if g))
        flags=[]
        if hits: flags.append('RUSSIA_TEXT_HIT')
        if yh: flags.append('URL_LATER_YEAR_HINT')
        if '|' in (x.get('sources_matching','') or '') or '||' in text: flags.append('POSSIBLE_COMPOSITE')
        if flags:
            out.append({
                'event_id_1pd':x.get('event_id_1pd',''),'date':x.get('date',''),'R5PriorityV3':x.get('R5PriorityV3',''),
                'sources_matching':x.get('sources_matching',''),'source_urls':clean(url,350),'asciiname':x.get('asciiname',''),
                'ADM1_NAME':x.get('ADM1_NAME',''),'location_method':x.get('location_method',''),
                'RussiaTextHits': '|'.join(hits),'LaterYearHints':'|'.join(yh),'ResidualFlags':'|'.join(flags),
                'text_excerpt':clean(text,600),'CandidateCensusComplete':'FALSE'
            })
            for fl in flags: c[fl]+=1
    fields=['event_id_1pd','date','R5PriorityV3','sources_matching','source_urls','asciiname','ADM1_NAME','location_method','RussiaTextHits','LaterYearHints','ResidualFlags','text_excerpt','CandidateCensusComplete']
    with a.output.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(out)
    with a.summary.open('w',encoding='utf-8') as f:
        f.write('protocol=VIINA_2022_LOW_PRIORITY_RESIDUAL_AUDIT_V1\n')
        f.write(f'input_low_priority_rows={len(rows)}\n')
        f.write(f'flagged_rows={len(out)}\n')
        for k in ['RUSSIA_TEXT_HIT','URL_LATER_YEAR_HINT','POSSIBLE_COMPOSITE']: f.write(f'{k}={c[k]}\n')
        f.write('policy=FLAG_ONLY_NO_AUTOMATIC_EXCLUSION\n')
        f.write('candidate_census_complete=FALSE\n')
if __name__=='__main__': main()
