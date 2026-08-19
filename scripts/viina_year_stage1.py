#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,re
from collections import Counter,defaultdict
from pathlib import Path
from filter_viina import first_csv,is_true,label_value,load_ru_gazetteer,location_decision,ndate,scan_info,val

WORD=r"A-Za-zА-Яа-яЁёІіЇїЄєҐґ0-9_"
def bounded(terms): return re.compile(rf"(?<![{WORD}])(?:{'|'.join(terms)})(?![{WORD}])",re.I|re.U)
UA=bounded([r"ukraine",r"ukrainian",r"SBU",r"AFU",r"україн(?:а|и|і|ськ\w*)?",r"украин(?:а|ы|е|ск\w*)?",r"зсу",r"всу",r"сбу",r"ссо",r"сил(?:и|ы) оборон",r"збройн\w*"])
RUEXP=bounded([r"in russia",r"inside russia",r"within russia",r"russian federation",r"on russian territory",r"в россии",r"в рф",r"на территории россии",r"у росії",r"на території росії"])
RUPL=bounded([r"belgorod",r"bryansk",r"kursk",r"rostov",r"krasnodar",r"voronezh",r"oryol",r"orel",r"kaluga",r"tula",r"lipetsk",r"tambov",r"ryazan",r"smolensk",r"pskov",r"leningrad",r"novgorod",r"saratov",r"samara",r"tatarstan",r"bashkortostan",r"nizhny novgorod",r"volgograd",r"astrakhan",r"stavropol",r"dagestan",r"komi",r"murmansk",r"arkhangelsk",r"yaroslavl",r"tver",r"moscow",r"engels",r"taganrog",r"taman",r"belgorod",r"klintsy",r"klimovo",r"shebekino",r"solokhi",r"millerovo",r"novoshakhtinsk",r"dyagilevo",r"белгород(?:а|е|у|ом)?",r"брянск(?:а|е|у|ом)?",r"курск(?:а|е|у|ом|ой)?",r"ростов(?:а|е|у|ом)?",r"краснодар(?:а|е|у|ом|ский|ского|ском)?",r"воронеж(?:а|е|у|ом)?",r"ор[её]л(?:а|е|у|ом)?",r"калуг(?:а|е|и|ой)",r"тул(?:а|е|ы|ой)",r"липецк(?:а|е|у|ом)?",r"тамбов(?:а|е|у|ом)?",r"рязан(?:ь|и|ью|ская|ской)",r"смоленск(?:а|е|у|ом)?",r"псков(?:а|е|у|ом)?",r"ленинград(?:ская|ской|скую)?",r"новгород(?:а|е|у|ом|ская|ской)?",r"саратов(?:а|е|у|ом|ская|ской)?",r"самар(?:а|е|ы|ой|ская|ской)",r"татарстан(?:а|е|у|ом)?",r"башкортостан(?:а|е|у|ом)?",r"нижн(?:ий|его|ем) новгород(?:е|а|у|ом)?",r"волгоград(?:а|е|у|ом|ская|ской)?",r"астрахан(?:ь|и|ью|ская|ской)",r"ставропол(?:ь|я|е|ю|ем|ьский|ьского|ьском)?",r"дагестан(?:а|е|у|ом)?",r"коми",r"мурманск(?:а|е|у|ом)?",r"архангельск(?:а|е|у|ом)?",r"ярославл(?:ь|я|е|ю|ем|ьская|ьской)?",r"твер(?:ь|и|ью|ская|ской)",r"москв(?:а|е|ы|ой|у)",r"энгельс(?:а|е|у|ом)?",r"таганрог(?:а|е|у|ом)?",r"таман(?:ь|и|ью|ская|ской)",r"клинц(?:ы|ах|ами)?",r"климов(?:о|е|ом)?",r"шебекин(?:о|е|ом)?",r"солох(?:и|ах|ами)?",r"миллеров(?:о|е|ом)?",r"новошахтинск(?:а|е|у|ом)?",r"дягилев(?:о|е|ом)?"])
CRIMEA=bounded([r"crimea",r"krym",r"sevastopol",r"feodosia",r"simferopol",r"dzhankoi",r"kerch",r"saki",r"крим",r"крым",r"севастопол(?:ь|я|е|ю|ем)?",r"феодос(?:ия|ии|ию|ией)",r"симферопол(?:ь|я|е|ю|ем)?",r"джанко(?:й|я|е|ю|ем)",r"керч(?:ь|и|ью)",r"саки"])
OCC=bounded([r"donetsk",r"luhansk",r"lugansk",r"mariupol",r"melitopol",r"berdiansk",r"berdyansk",r"kherson",r"zaporizhzhia",r"zaporozhye",r"донецьк(?:а|ій|у|ом)?",r"донецк(?:а|е|у|ом)?",r"луганськ(?:а|ій|у|ом)?",r"луганск(?:а|е|у|ом)?",r"маріупол(?:ь|і|я|ю|ем)?",r"мариупол(?:ь|е|я|ю|ем)?",r"мелітопол(?:ь|і|я|ю|ем)?",r"мелитопол(?:ь|е|я|ю|ем)?",r"бердянськ(?:а|у|ом)?",r"бердянск(?:а|е|у|ом)?",r"херсон(?:а|е|у|ом|ська|ской)?",r"запоріж(?:жя|жі|жю|зька|зькій)",r"запорож(?:ье|ья|ской|ская)"])

def norm(s): return re.sub(r"\s+"," ",(s or "").strip().casefold())
def scope(text):
    c=bool(CRIMEA.search(text)); u=bool(OCC.search(text)); r=bool(RUEXP.search(text) or RUPL.search(text))
    if c and r: return "CONFLICT_OR_COMPOSITE"
    if u and r: return "CONFLICT_OR_COMPOSITE"
    if c: return "CRIMEA_SEVASTOPOL"
    if u: return "UKRAINE_OCCUPIED_OTHER"
    if r: return "RUSSIA_PROPER"
    return "UNKNOWN"
def load_matrix(p):
    with p.open(encoding='utf-8',newline='') as f:
        rd=csv.DictReader(f); return list(rd.fieldnames or []),list(rd)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--year',type=int,required=True); ap.add_argument('--viina-data-dir',type=Path,required=True); ap.add_argument('--ru-geonames',type=Path,required=True); ap.add_argument('--outdir',type=Path,required=True); ap.add_argument('--matrix',type=Path,required=True); a=ap.parse_args()
    y=a.year; start=y*10000+101; end=y*10000+1231
    info=a.viina_data_dir/f'event_info_latest_{y}.zip'; one=a.viina_data_dir/f'event_1pd_latest_{y}.zip'; gaz=load_ru_gazetteer(a.ru_geonames); raw=scan_info(info,gaz)
    rows=[]; matched=set(); counts=Counter(); z,f=first_csv(one)
    try:
        for r in csv.DictReader(f):
            k=val(r,'event_id_1pd'); d=ndate(r.get('date'))
            if k not in raw or d is None or not start<=d<=end: continue
            matched.add(k); x=raw[k]; text=' || '.join(x['texts'][:3]); bucket,method,dist,ngid,nname=location_decision(r,gaz)
            labels={}
            for b in ['a_ukr_init','a_ukr','a_rus_init','a_rus']:
                fn,v=label_value(r,b); labels[b+'_field']=fn; labels[b]=v
            ua=bool(UA.search(text)); ru=bool(RUEXP.search(text) or RUPL.search(text))
            if bucket in {'STRICT','REVIEW'} or (ua and ru) or is_true(labels['a_ukr_init']): tri='REVIEW'
            else: tri='MACHINE_NONCANDIDATE'
            counts[tri]+=1
            for b in ['a_ukr_init','a_ukr','a_rus_init','a_rus']:
                if is_true(labels[b]): counts[b.upper()+'_TRUE']+=1
            rows.append({'event_id_1pd':k,'date':d,'n_reports':val(r,'n_reports'),'event_ids_matching':'|'.join(sorted(i for i in x['ids'] if i)),'sources_matching':'|'.join(sorted(x['sources'])),'source_urls':'|'.join(sorted(x['urls'])),'target_classes':'|'.join(sorted(x['classes'])),'target_terms':'|'.join(sorted(x['tt'])),'attack_terms':'|'.join(sorted(x['aa'])),'geonameid':val(r,'geonameid'),'asciiname':val(r,'asciiname'),'ADM1_NAME':val(r,'ADM1_NAME'),'ADM2_NAME':val(r,'ADM2_NAME'),'longitude':val(r,'longitude'),'latitude':val(r,'latitude'),'location_bucket':bucket,'location_method':method,'nearest_ru_distance_km':dist,'nearest_ru_geonameid':ngid,'nearest_ru_name':nname,**labels,'ua_actor_text':str(ua).upper(),'ru_scope_text':str(ru).upper(),'representative_text':text,'Stage1Triage':tri,'CandidateCensusComplete':'FALSE'})
    finally: f.close(); z.close()
    a.outdir.mkdir(parents=True,exist_ok=True)
    fields=list(rows[0].keys()) if rows else []
    rebuild=a.outdir/f'VIINA_{y}_REBUILD.csv'
    with rebuild.open('w',encoding='utf-8',newline='') as f: w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    review=[r for r in rows if r['Stage1Triage']=='REVIEW']
    groups=defaultdict(list)
    for r in review:
        key=(norm(r['source_urls']),norm(r['representative_text']))
        if key!=('',''): groups[key].append(r)
    clusters=[v for v in groups.values() if len(v)>1]; dup_ids=set(); canonical=set()
    for cl in clusters:
        c=min(cl,key=lambda r:(int(r['date']),int(r['event_id_1pd']) if str(r['event_id_1pd']).isdigit() else 10**18)); canonical.add(c['event_id_1pd'])
        for r in cl:
            if r['event_id_1pd']!=c['event_id_1pd']: dup_ids.add(r['event_id_1pd'])
    post=[]; sc=Counter()
    for r in review:
        if r['event_id_1pd'] in dup_ids: continue
        x=dict(r); x['ScopeAutoV1']=scope(r['representative_text']); x['ManualReviewRequired']='TRUE'; post.append(x); sc[x['ScopeAutoV1']]+=1
    pf=fields+['ScopeAutoV1','ManualReviewRequired']
    postp=a.outdir/f'VIINA_{y}_POST_EXACT_DEDUPE_REVIEW.csv'
    with postp.open('w',encoding='utf-8',newline='') as f: w=csv.DictWriter(f,fieldnames=pf); w.writeheader(); w.writerows(post)
    rp=[r for r in post if r['ScopeAutoV1'] in {'RUSSIA_PROPER','CONFLICT_OR_COMPOSITE'}]
    rpp=a.outdir/f'VIINA_{y}_RUSSIA_PRIORITY.csv'
    with rpp.open('w',encoding='utf-8',newline='') as f: w=csv.DictWriter(f,fieldnames=pf); w.writeheader(); w.writerows(rp)
    summary=a.outdir/f'VIINA_{y}_STAGE1_SUMMARY.txt'
    with summary.open('w',encoding='utf-8') as f:
        f.write(f'protocol=VIINA_{y}_STAGE1_STABLE_V1\nraw_text_match_groups={len(raw)}\njoined_onepd_groups={len(rows)}\nraw_without_onepd_join={len(set(raw)-matched)}\nreview_rows={len(review)}\nmachine_noncandidate={counts["MACHINE_NONCANDIDATE"]}\nexact_duplicate_clusters={len(clusters)}\nexact_duplicate_rows_linked={len(dup_ids)}\npost_exact_dedupe_review_rows={len(post)}\nrussia_priority_rows={len(rp)}\n')
        for k in ['RUSSIA_PROPER','CONFLICT_OR_COMPOSITE','CRIMEA_SEVASTOPOL','UKRAINE_OCCUPIED_OTHER','UNKNOWN']: f.write(f'{k}={sc[k]}\n')
        f.write(f'a_ukr_init_true={counts["A_UKR_INIT_TRUE"]}\na_ukr_true={counts["A_UKR_TRUE"]}\na_rus_init_true={counts["A_RUS_INIT_TRUE"]}\ncandidate_census_complete=FALSE\n')
    mf,mr=load_matrix(a.matrix); mid=f'SRC-{y}-VIINA'; found=False
    for r in mr:
        if r.get('MatrixRowID')==mid:
            found=True; r['SearchStatus']='COMPLETED'; r['CoverageStatus']='FULL_PROTOCOL'; r['QueryProtocolVersion']=f'VIINA_{y}_STAGE1_STABLE_V1'; r['RawHits']=str(len(raw)); r['CandidateRows']=str(len(review)); r['DuplicateRows']=str(len(dup_ids)); r['UnresolvedRows']=str(len(post)); r['SearchPassCount']='1'; r['EvidenceArchivePath']=f'output/VIINA_{y}_REBUILD.csv|output/VIINA_{y}_POST_EXACT_DEDUPE_REVIEW.csv|output/VIINA_{y}_RUSSIA_PRIORITY.csv|output/VIINA_{y}_STAGE1_SUMMARY.txt'; r['ReviewStatus']='IN_PROGRESS'; r['DedupeReviewStatus']='IN_PROGRESS'; r['RowAcceptanceStatus']='NOT_READY'; r['CandidateCensusComplete']='FALSE'; r['Notes']=f'VIINA {y} stable stage-1 complete: actor-independent high-recall discovery, exact report dedupe, bounded scope triage. Manual/event-level review remains.'
    if not found: raise RuntimeError(f'{mid} missing')
    with a.matrix.open('w',encoding='utf-8',newline='') as f: w=csv.DictWriter(f,fieldnames=mf); w.writeheader(); w.writerows(mr)
    print(summary.read_text(encoding='utf-8'))
if __name__=='__main__': main()
