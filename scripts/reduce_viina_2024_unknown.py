#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,re
from collections import Counter
from pathlib import Path

WORD=r"A-Za-zА-Яа-яЁёІіЇїЄєҐґ0-9_"
def bounded(terms): return re.compile(rf"(?<![{WORD}])(?:{'|'.join(terms)})(?![{WORD}])",re.I|re.U)

# 2024 Russia-proper target/place aliases that can appear without country/oblast wording.
RU_TARGET=bounded([
 r"slavyansk[- ]eko",r"славянск[- ]эко",r"славянск(?:ий|ого) нпз",
 r"ust[- ]luga",r"усть[- ]луг(?:а|е|и|ой)",r"tuapse",r"туапсе",
 r"kстово",r"kstovo",r"нижегород(?:ский|ского) нпз",r"nizhny novgorod refinery",
 r"ryazan refinery",r"рязанск(?:ий|ого) нпз",r"syzran",r"сызран(?:ь|и|ью)",
 r"novokuibyshevsk",r"новокуйбышевск(?:а|е|у|ом)?",r"kuibyshev refinery",r"куйбышевск(?:ий|ого) нпз",
 r"ilsky",r"ильск(?:ий|ого|ом)?",r"afipsky",r"афипск(?:ий|ого|ом)?",
 r"alabuga",r"alabuga polytech",r"елабуг(?:а|е|и|ой)",r"алабуг(?:а|е|и|ой)",
 r"morozovsk",r"морозовск(?:а|е|у|ом)?",r"akhtubinsk",r"ахтубинск(?:а|е|у|ом)?",
 r"olenya",r"оленья",r"engels",r"энгельс(?:а|е|у|ом)?",
 r"khalino",r"халин(?:о|е|ом)?",r"savasleyka",r"саваслейк(?:а|е|и|ой)",
 r"borisoglebsk",r"борисоглебск(?:а|е|у|ом)?",r"baltimore airfield",r"аэродром балтимор",
 r"lipetsk airfield",r"липецк(?:ий|ого) аэродром",r"marinovka",r"мариновк(?:а|е|и|ой)",
 r"proletarsk",r"пролетарск(?:а|е|у|ом)?",r"kombinat kavkaz",r"комбинат кавказ",
 r"oktyabrsky",r"октябрьск(?:ий|ого|ом)?",r"shahed storage",r"склад.*шахед",
 r"rasskazovo",r"рассказов(?:о|е|ом)?",r"biokhim",r"биохим",
 r"yefremov",r"ефремов(?:а|е|у|ом)?",r"luzhkovsky",r"лужковск(?:ий|ого|ом)?",
 r"novonikolskoye",r"новоникольск(?:ое|ом)?",r"druzhba",r"дружб(?:а|е|ы|ой)",
 r"toropets",r"торопец(?:а|е|у|ом)?",r"tikhoretsk",r"тихорецк(?:а|е|у|ом)?",
 r"kotelnich",r"котельнич(?:а|е|у|ем)?",r"glubokinskaya",r"глубокинск(?:ая|ой|ую)",
 r"taganrog",r"таганрог(?:а|е|у|ом)?",r"novorossiysk",r"новороссийск(?:а|е|у|ом)?",
 r"pskov",r"псков(?:а|е|у|ом)?",r"shaykovka",r"шайковк(?:а|е|и|ой)",
])

UA_ADM1={"kharkiv","kharkivs'ka","kiev","kyiv","kiev city","donets'k","luhans'k","kherson","zaporizhzhya","dnipropetrovs'k","mykolayiv","odessa","poltava","sumy","chernihiv","cherkasy","vinnytsya","zhytomyr","khmel'nyts'kyy","rivne","volyn","lviv","ternopil","ivano-frankivs'k","chernivtsi","kirovohrad","zakarpattia"}
CRIMEA_ADM1={"crimea","sevastopol city","sevastopol'"}
RUSSIA_REVIEW_METHODS={"REVIEW_NAME_ONLY_RU_SUPPORT","REVIEW_COORDINATE_NEAR_RU"}

def truth(v): return (v or '').strip().casefold() in {'1','true','t','yes','y'}

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--input',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); ap.add_argument('--high-output',type=Path,required=True); ap.add_argument('--summary',type=Path,required=True); a=ap.parse_args()
 with a.input.open(encoding='utf-8',newline='') as f:
  rd=csv.DictReader(f); fields=list(rd.fieldnames or []); rows=[x for x in rd if x.get('ScopeAutoV1')=='UNKNOWN']
 if len(rows)!=120: raise RuntimeError(f'Expected 120 UNKNOWN rows, found {len(rows)}')
 counts=Counter(); out=[]; high=[]
 for r in rows:
  text=r.get('representative_text','') or ''; adm1=(r.get('ADM1_NAME','') or '').strip().casefold(); method=(r.get('location_method','') or '').strip()
  ua_actor=truth(r.get('a_ukr','')) or (r.get('ua_actor_text','')=='TRUE')
  ru_actor=truth(r.get('a_rus','')) or truth(r.get('a_rus_init',''))
  hits=sorted(set(m.group(0) for m in RU_TARGET.finditer(text)))
  ua_geo=adm1 in UA_ADM1; crimea_geo=adm1 in CRIMEA_ADM1; ru_review=method in RUSSIA_REVIEW_METHODS
  if hits: p='H1_RUSSIA_TARGET_TEXT'; reason='KNOWN_RUSSIA_2024_TARGET_OR_PLACE_TEXT'
  elif ua_actor and ru_review: p='H2_UA_ACTOR_RUSSIA_LOCATION_REVIEW'; reason='UA_ACTOR_PLUS_RUSSIA_SUSPECT_LOCATION_METHOD'
  elif ua_actor and not ua_geo and not crimea_geo: p='H3_UA_ACTOR_NO_CLEAR_UA_GEO'; reason='UA_ACTOR_WITHOUT_CLEAR_UKRAINE_OR_CRIMEA_ADM1'
  elif ua_actor and ua_geo: p='M1_UA_ACTOR_UA_GEO'; reason='UA_ACTOR_WITH_UKRAINE_GEOCODE_REQUIRES_TEXT_CHECK'
  elif crimea_geo: p='L1_CRIMEA_GEO'; reason='VIINA_ADM1_CRIMEA'
  elif ru_actor and ua_geo: p='L2_RUS_ACTOR_UA_GEO'; reason='RUSSIAN_ACTOR_AND_UKRAINE_GEOCODE'
  elif ua_geo: p='L3_UA_GEO_NO_UA_ACTOR'; reason='UKRAINE_GEOCODE_WITHOUT_UA_ACTOR_EVIDENCE'
  else: p='M2_REMAINS_UNRESOLVED'; reason='NO_DECISIVE_SECOND_STAGE_SIGNAL'
  x=dict(r); x.update({'UnknownPriorityV2':p,'UnknownPriorityReasonV2':reason,'RussiaTargetTextHitsV2':'|'.join(hits),'UkraineActorEvidenceV2':'TRUE' if ua_actor else 'FALSE','RussiaActorEvidenceV2':'TRUE' if ru_actor else 'FALSE','UkraineAdm1EvidenceV2':'TRUE' if ua_geo else 'FALSE','CrimeaAdm1EvidenceV2':'TRUE' if crimea_geo else 'FALSE','RussiaReviewMethodEvidenceV2':'TRUE' if ru_review else 'FALSE','ManualReviewRequired':'TRUE','CandidateCensusComplete':'FALSE'})
  out.append(x); counts[p]+=1
  if p.startswith('H'): high.append(x)
 extra=['UnknownPriorityV2','UnknownPriorityReasonV2','RussiaTargetTextHitsV2','UkraineActorEvidenceV2','RussiaActorEvidenceV2','UkraineAdm1EvidenceV2','CrimeaAdm1EvidenceV2','RussiaReviewMethodEvidenceV2']
 seen=set(); of=[c for c in fields+extra if not(c in seen or seen.add(c))]
 for path,data in [(a.output,out),(a.high_output,high)]:
  with path.open('w',encoding='utf-8',newline='') as f: w=csv.DictWriter(f,fieldnames=of,extrasaction='ignore'); w.writeheader(); w.writerows(data)
 order=['H1_RUSSIA_TARGET_TEXT','H2_UA_ACTOR_RUSSIA_LOCATION_REVIEW','H3_UA_ACTOR_NO_CLEAR_UA_GEO','M1_UA_ACTOR_UA_GEO','M2_REMAINS_UNRESOLVED','L1_CRIMEA_GEO','L2_RUS_ACTOR_UA_GEO','L3_UA_GEO_NO_UA_ACTOR']
 with a.summary.open('w',encoding='utf-8') as f:
  f.write('protocol=VIINA_2024_UNKNOWN_REDUCTION_V2\n'); f.write(f'input_unknown_rows={len(rows)}\n'); f.write(f'high_priority_rows={len(high)}\n')
  for k in order: f.write(f'{k}={counts[k]}\n')
  f.write('policy=PRIORITIZATION_ONLY_NO_AUTOMATIC_EXCLUSION\nmanual_review_required=TRUE\ncandidate_census_complete=FALSE\n')
if __name__=='__main__': main()
