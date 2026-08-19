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

def scan_info(path, ru):
    agg=defaultdict(lambda: {'ids':set(),'sources':set(),'urls':set(),'texts':[],'classes':set(),'tt':set(),'aa':set()})
    z,f=first_csv(path)
    try:
        r=csv.DictReader(f)
        for row in r:
            d=ndate(row.get('date'))
            if d is None or not START<=d<=END: continue
            if str(row.get('geonameid','')).strip() not in ru: continue
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
    finally:
        f.close(); z.close()
    return agg

def val(row,k): return str(row.get(k,'') or '').strip()

def join_onepd(path, raw):
    out=[]; z,f=first_csv(path)
    try:
        r=csv.DictReader(f)
        for row in r:
            key=val(row,'event_id_1pd')
            if key not in raw: continue
            d=ndate(row.get('date'))
            if d is None or not START<=d<=END: continue
            x=raw[key]
            out.append({
                'event_id_1pd':key,'date':str(d),'n_reports_viina':val(row,'n_reports'),
                'raw_reports_matching':str(len(x['ids'])),'event_ids_matching':'|'.join(sorted(x['ids'])),
                'sources_matching':'|'.join(sorted(x['sources'])),'source_urls':'|'.join(sorted(x['urls'])),
                'geonameid':val(row,'geonameid'),'asciiname':val(row,'asciiname'),
                'ADM1_NAME':val(row,'ADM1_NAME'),'ADM2_NAME':val(row,'ADM2_NAME'),
                'longitude':val(row,'longitude'),'latitude':val(row,'latitude'),'GEO_PRECISION':val(row,'GEO_PRECISION'),
                'a_ukr':val(row,'a_ukr'),'a_rus':val(row,'a_rus'),'t_mil':val(row,'t_mil'),
                't_airstrike':val(row,'t_airstrike'),'t_artillery':val(row,'t_artillery'),'t_property':val(row,'t_property'),'t_raid':val(row,'t_raid'),
                'target_class_auto':'|'.join(sorted(x['classes'])),'matched_target_terms':'|'.join(sorted(x['tt'])),'matched_attack_terms':'|'.join(sorted(x['aa'])),
                'representative_text':' || '.join(x['texts'])[:12000],'russia_geonames_gate':'TRUE','study_period_gate':'TRUE',
                'manual_review_required':'TRUE','candidate_status':'DISCOVERY_ONLY'
            })
    finally:
        f.close(); z.close()
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--viina-data-dir',type=Path,required=True)
    ap.add_argument('--ru-geonames',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); ru=load_ru_ids(a.ru_geonames); rows=[]
    for y in range(2022,2027):
        raw=scan_info(a.viina_data_dir/f'event_info_latest_{y}.zip',ru)
        rows += join_onepd(a.viina_data_dir/f'event_1pd_latest_{y}.zip',raw)
    rows={r['event_id_1pd']:r for r in rows}.values()
    rows=sorted(rows,key=lambda r:(r['date'],r['event_id_1pd']))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    fields=list(rows[0].keys()) if rows else ['event_id_1pd','date','candidate_status']
    with a.output.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(f'Wrote {len(rows)} candidates to {a.output}')

if __name__=='__main__': main()
