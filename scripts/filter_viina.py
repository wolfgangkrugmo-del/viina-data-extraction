#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, io, re, zipfile
from collections import defaultdict
from pathlib import Path

START, END = 20220224, 20260630

TARGET_PATTERNS = {
    "REFINING_PETROCHEM_GAS": [r"\brefiner", r"oil refinery", r"gas processing", r"нефтеперерабат", r"\bнпз\b", r"нафтоперероб", r"газоперерабат", r"petrochem", r"нефтехим"],
    "FUEL_STORAGE_TERMINAL": [r"oil depot", r"fuel depot", r"tank farm", r"oil terminal", r"нефтебаз", r"нафтобаз", r"нефтехранил", r"нефтян.*терминал", r"нафтов.*термінал"],
    "PIPELINE_PUMPING": [r"pipeline", r"pumping station", r"pump station", r"нефтепровод", r"нафтопров", r"трубопровод", r"перекачивающ.*станц"],
    "PORT_EXPORT_LOGISTICS": [r"\bport\b", r"sea terminal", r"export terminal", r"\bпорт\b", r"морск.*терминал", r"морськ.*термінал"],
    "STRATEGIC_AIRBASE": [r"airbase", r"air base", r"airfield", r"авиабаз", r"авіабаз", r"аэродром", r"аеродром", r"strategic bomber", r"стратегическ.*бомбард"],
    "AMMUNITION_ARSENAL": [r"ammunition depot", r"ammo depot", r"\barsenal\b", r"склад.*боеприпас", r"склад.*боєприпас", r"\bарсенал"],
    "DEFENSE_INDUSTRY": [r"defen[cs]e plant", r"military plant", r"arms plant", r"weapons plant", r"оборонн.*завод", r"военн.*завод", r"\bвпк\b", r"порохов.*завод"],
    "MILITARY_REPAIR_SHIPYARD": [r"shipyard", r"repair yard", r"dry dock", r"судоремонт", r"суднобуд", r"верф", r"сух.*док"],
    "RAIL_STRATEGIC_LOGISTICS": [r"railway depot", r"railway hub", r"железнодорож.*узел", r"залізничн.*вузол", r"железнодорож.*депо"],
    "MILITARY_COMMS_SPACE": [r"satellite communication", r"communications center", r"space communications", r"спутников.*связ", r"супутников.*зв", r"центр.*связ"],
    "ENERGY_GRID_SUPPORT": [r"power substation", r"electrical substation", r"подстанц", r"підстанц"],
}
ATTACK_PATTERNS = [r"\battack", r"\bstrike", r"\bdrone", r"\bmissile", r"\bexplosion", r"\bfire\b", r"\bdamag", r"\bdestroy", r"\bsabot", r"атак", r"удар", r"дрон", r"беспилот", r"безпілот", r"ракет", r"взрыв", r"вибух", r"пожар", r"пожеж", r"поврежд", r"пошкодж", r"уничтож", r"знищ"]

CT = {k:[re.compile(p,re.I|re.U) for p in v] for k,v in TARGET_PATTERNS.items()}
CA = [re.compile(p,re.I|re.U) for p in ATTACK_PATTERNS]

def first_csv(zip_path):
    z=zipfile.ZipFile(zip_path)
    names=[n for n in z.namelist() if n.lower().endswith('.csv')]
    if not names: raise RuntimeError(f'No CSV in {zip_path}')
    return z, io.TextIOWrapper(z.open(names[0],'r'), encoding='utf-8-sig', newline='')

def ndate(v):
    s=re.sub(r'\D','',str(v or ''))
    return int(s[:8]) if len(s)>=8 else None

def hits(text):
    classes=[]; tt=[]; aa=[]
    for cls,pats in CT.items():
        mm=[m.group(0) for p in pats if (m:=p.search(text))]
        if mm: classes.append(cls); tt.extend(mm)
    for p in CA:
        m=p.search(text)
        if m: aa.append(m.group(0))
    return sorted(set(classes)), sorted(set(tt)), sorted(set(aa))

def load_ru_ids(path):
    ids=set()
    with zipfile.ZipFile(path) as z:
        txt=next(n for n in z.namelist() if n.lower().endswith('.txt'))
        with io.TextIOWrapper(z.open(txt), encoding='utf-8') as f:
            for line in f: ids.add(line.split('\t',1)[0])
    return ids

def is_true(v):
    return str(v or '').strip().lower() in {'1','1.0','true','t','yes'}

def first_existing(row, names):
    for n in names:
        if n in row:
            return n, row.get(n)
    return None, None

def val(row,k): return str(row.get(k,'') or '').strip()

def label_value(row, base):
    # VIINA currently exposes binary classifier columns with _b in several releases;
    # keep fallbacks so the workflow fails gracefully across release naming changes.
    name, value = first_existing(row, [base+'_b', base])
    return name or '', str(value or '').strip()

def scan_info(path, ru):
    agg=defaultdict(lambda: {
        'ids':set(),'sources':set(),'urls':set(),'texts':[],'classes':set(),'tt':set(),'aa':set(),
        'ru_geonameids':set(),'ru_places':set(),'ru_adm1':set(),'ru_adm2':set()
    })
    z,f=first_csv(path)
    try:
        r=csv.DictReader(f)
        for row in r:
            d=ndate(row.get('date'))
            if d is None or not START<=d<=END: continue
            gid=str(row.get('geonameid','')).strip()
            if gid not in ru: continue
            text=str(row.get('text','') or '')
            c,t,a=hits(text)
            if not c or not a: continue
            key=str(row.get('event_id_1pd','')).strip()
            if not key: continue
            x=agg[key]
            x['ids'].add(str(row.get('event_id','')).strip())
            if row.get('source'): x['sources'].add(str(row['source']).strip())
            if row.get('url'): x['urls'].add(str(row['url']).strip())
            if text and len(x['texts'])<6: x['texts'].append(text.replace('\n',' ').strip())
            x['classes'].update(c); x['tt'].update(t); x['aa'].update(a)
            x['ru_geonameids'].add(gid)
            if row.get('asciiname'): x['ru_places'].add(str(row['asciiname']).strip())
            if row.get('ADM1_NAME'): x['ru_adm1'].add(str(row['ADM1_NAME']).strip())
            if row.get('ADM2_NAME'): x['ru_adm2'].add(str(row['ADM2_NAME']).strip())
    finally:
        f.close(); z.close()
    return agg

def join_onepd(path, raw, ru):
    strict=[]; review=[]; z,f=first_csv(path)
    actor_field_seen=False
    try:
        r=csv.DictReader(f)
        fields=set(r.fieldnames or [])
        actor_candidates={'a_ukr_init_b','a_ukr_init'}
        actor_field_seen=bool(fields & actor_candidates)
        if not actor_field_seen:
            raise RuntimeError(f'{path}: neither a_ukr_init_b nor a_ukr_init present; fields={sorted(fields)}')

        for row in r:
            key=val(row,'event_id_1pd')
            if key not in raw: continue
            d=ndate(row.get('date'))
            if d is None or not START<=d<=END: continue

            actor_name, actor_val = first_existing(row,['a_ukr_init_b','a_ukr_init'])
            if not is_true(actor_val):
                continue

            x=raw[key]
            onepd_gid=val(row,'geonameid')
            onepd_ru = bool(onepd_gid and onepd_gid in ru)

            labels={}
            for base in ['a_ukr_init','a_ukr','a_rus_init','a_rus','t_mil','t_uav','t_airstrike','t_artillery','t_property','t_raid']:
                nm,v=label_value(row,base)
                labels[base+'_field']=nm
                labels[base]=v

            rec={
                'event_id_1pd':key,'date':str(d),'n_reports_viina':val(row,'n_reports'),
                'raw_reports_matching':str(len(x['ids'])),'event_ids_matching':'|'.join(sorted(x['ids'])),
                'sources_matching':'|'.join(sorted(x['sources'])),'source_urls':'|'.join(sorted(x['urls'])),
                'geonameid':onepd_gid,'asciiname':val(row,'asciiname'),'ADM1_NAME':val(row,'ADM1_NAME'),'ADM2_NAME':val(row,'ADM2_NAME'),
                'longitude':val(row,'longitude'),'latitude':val(row,'latitude'),'GEO_PRECISION':val(row,'GEO_PRECISION'),
                'raw_ru_geonameids':'|'.join(sorted(x['ru_geonameids'])),'raw_ru_places':'|'.join(sorted(x['ru_places'])),
                'raw_ru_ADM1':'|'.join(sorted(x['ru_adm1'])),'raw_ru_ADM2':'|'.join(sorted(x['ru_adm2'])),
                **labels,
                'target_class_auto':'|'.join(sorted(x['classes'])),'matched_target_terms':'|'.join(sorted(x['tt'])),'matched_attack_terms':'|'.join(sorted(x['aa'])),
                'representative_text':' || '.join(x['texts'])[:12000],
                'ukrainian_initiator_gate':'TRUE','onepd_russia_geonames_gate':'TRUE' if onepd_ru else 'FALSE',
                'raw_russia_mention_gate':'TRUE','study_period_gate':'TRUE','manual_review_required':'TRUE'
            }
            if onepd_ru:
                rec['candidate_status']='STRICT_RUSSIA_UKR_INIT_DISCOVERY'
                strict.append(rec)
            else:
                rec['candidate_status']='REVIEW_LOCATION_NOT_CONFIRMED_BY_1PD'
                review.append(rec)
    finally:
        f.close(); z.close()
    return strict, review

def write_csv(path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    if rows:
        fields=list(rows[0].keys())
    else:
        fields=['event_id_1pd','date','candidate_status']
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--viina-data-dir',type=Path,required=True)
    ap.add_argument('--ru-geonames',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--review-output',type=Path,required=True)
    a=ap.parse_args(); ru=load_ru_ids(a.ru_geonames); strict=[]; review=[]
    for y in range(2022,2027):
        raw=scan_info(a.viina_data_dir/f'event_info_latest_{y}.zip',ru)
        s,q=join_onepd(a.viina_data_dir/f'event_1pd_latest_{y}.zip',raw,ru)
        strict.extend(s); review.extend(q)
    strict={r['event_id_1pd']:r for r in strict}.values()
    review={r['event_id_1pd']:r for r in review}.values()
    strict=sorted(strict,key=lambda r:(r['date'],r['event_id_1pd']))
    review=sorted(review,key=lambda r:(r['date'],r['event_id_1pd']))
    write_csv(a.output,strict); write_csv(a.review_output,review)
    print(f'Wrote {len(strict)} strict candidates to {a.output}')
    print(f'Wrote {len(review)} location-review candidates to {a.review_output}')

if __name__=='__main__': main()
