#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,re
from pathlib import Path

WORD=r"A-Za-zА-Яа-яЁёІіЇїЄєҐґ0-9_"
def bounded(terms): return re.compile(rf"(?<![{WORD}])(?:{'|'.join(terms)})(?![{WORD}])",re.I|re.U)
RU=bounded([
 r"in russia",r"inside russia",r"russian federation",r"on russian territory",r"в россии",r"в рф",r"у росії",r"на території росії",
 r"belgorod",r"bryansk",r"kursk",r"rostov",r"krasnodar",r"voronezh",r"oryol",r"orel",r"kaluga",r"tula",r"lipetsk",r"tambov",r"ryazan",r"smolensk",r"pskov",r"novgorod",r"saratov",r"samara",r"tatarstan",r"volgograd",r"stavropol",r"moscow",r"tver",r"engels",r"taganrog",r"novorossiysk",r"tuapse",r"adygea",r"orenburg",r"omsk",r"murmansk",r"nizhny novgorod",r"yaroslavl",r"kazan",r"primorsk",r"kirishi",r"unecha",r"naytopovichi",r"kropotkinskaya",r"ilsky",r"afipsky",r"sheskharis",r"gukovo",r"novoshakhtinsk",r"millerovo",r"korenevo",r"novospasskoye",r"budennovsk",
 r"белгород(?:а|е|у|ом)?",r"брянск(?:а|е|у|ом)?",r"курск(?:а|е|у|ом)?",r"ростов(?:а|е|у|ом)?",r"краснодар(?:а|е|у|ом|ский|ского|ском)?",r"воронеж(?:а|е|у|ом)?",r"ор[её]л(?:а|е|у|ом)?",r"калуг(?:а|е|и|ой)",r"тул(?:а|е|ы|ой)",r"липецк(?:а|е|у|ом)?",r"тамбов(?:а|е|у|ом)?",r"рязан(?:ь|и|ью|ская|ской)",r"смоленск(?:а|е|у|ом)?",r"псков(?:а|е|у|ом)?",r"новгород(?:а|е|у|ом)?",r"саратов(?:а|е|у|ом)?",r"самар(?:а|е|ы|ой)",r"татарстан(?:а|е|у|ом)?",r"волгоград(?:а|е|у|ом)?",r"ставропол(?:ь|я|е|ю|ем)?",r"москв(?:а|е|ы|ой|у)",r"твер(?:ь|и|ью)",r"энгельс(?:а|е|у|ом)?",r"таганрог(?:а|е|у|ом)?",r"новороссийск(?:а|е|у|ом)?",r"туапсе",r"адыге(?:я|е|и|ю)",r"оренбург(?:а|е|у|ом)?",r"омск(?:а|е|у|ом)?",r"мурманск(?:а|е|у|ом)?",r"нижн(?:ий|его|ем) новгород(?:е|а|у|ом)?",r"ярославл(?:ь|я|е|ю|ем)?",r"казан(?:ь|и|ью)",r"приморск(?:а|е|у|ом)?",r"кириш(?:и|ах|ами)?",r"унеч(?:а|е|и|ой)",r"найтопович",r"кропоткинск(?:ая|ой|ую)",r"ильск(?:ий|ого|ом)?",r"афипск(?:ий|ого|ом)?",r"шесхарис",r"гуков(?:о|е|ом)?",r"новошахтинск(?:а|е|у|ом)?",r"миллеров(?:о|е|ом)?",r"коренев(?:о|е|ом)?",r"новоспасск",r"буд[её]нновск"
])
COMPOSITE=re.compile(r"\|\||;|, а |, и | та | та у | and | while | meanwhile | а в | а у | а також | також",re.I|re.U)
YEAR_OTHER=re.compile(r"\b202[0-46-9]\b|\b201\d\b",re.I)

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--input',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); ap.add_argument('--flagged-output',type=Path,required=True); ap.add_argument('--summary',type=Path,required=True); a=ap.parse_args()
 with a.input.open(encoding='utf-8',newline='') as f:
  rd=csv.DictReader(f); fields=list(rd.fieldnames or []); rows=[r for r in rd if r.get('UnknownPriorityV2') in {'L1_CRIMEA_GEO','L2_RUS_ACTOR_UA_GEO','L3_UA_GEO_NO_UA_ACTOR'}]
 if len(rows)!=56: raise RuntimeError(f'Expected 56 low-priority rows, found {len(rows)}')
 out=[]; flagged=[]; ru_n=comp_n=year_n=0
 for r in rows:
  text=r.get('representative_text','') or ''; ru_hits=sorted(set(m.group(0) for m in RU.finditer(text))); comp=bool(COMPOSITE.search(text)); oy=bool(YEAR_OTHER.search(text))
  reasons=[]
  if ru_hits: reasons.append('RUSSIA_TEXT_HIT'); ru_n+=1
  if comp: reasons.append('POSSIBLE_COMPOSITE'); comp_n+=1
  if oy: reasons.append('POSSIBLE_OTHER_YEAR_TEXT'); year_n+=1
  x=dict(r); x.update({'ResidualAuditFlags':'|'.join(reasons),'RussiaTextHitsAudit':'|'.join(ru_hits),'PossibleCompositeAudit':'TRUE' if comp else 'FALSE','PossibleOtherYearAudit':'TRUE' if oy else 'FALSE','CandidateCensusComplete':'FALSE'})
  out.append(x)
  if reasons: flagged.append(x)
 extra=['ResidualAuditFlags','RussiaTextHitsAudit','PossibleCompositeAudit','PossibleOtherYearAudit']; seen=set(); of=[c for c in fields+extra if not(c in seen or seen.add(c))]
 for path,data in [(a.output,out),(a.flagged_output,flagged)]:
  with path.open('w',encoding='utf-8',newline='') as f: w=csv.DictWriter(f,fieldnames=of,extrasaction='ignore'); w.writeheader(); w.writerows(data)
 with a.summary.open('w',encoding='utf-8') as f:
  f.write('protocol=VIINA_2025_LOW_RESIDUAL_AUDIT_V1\n'); f.write(f'input_low_rows={len(rows)}\n'); f.write(f'flagged_rows={len(flagged)}\n'); f.write(f'russia_text_rows={ru_n}\n'); f.write(f'possible_composite_rows={comp_n}\n'); f.write(f'possible_other_year_rows={year_n}\n'); f.write('policy=AUDIT_ONLY_NO_AUTOMATIC_EXCLUSION\ncandidate_census_complete=FALSE\n')
if __name__=='__main__': main()
