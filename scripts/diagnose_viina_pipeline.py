#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, io, zipfile
from pathlib import Path
import filter_viina as fv

KNOWN = {
    '399662':'Feodosia 2025-10-08',
    '399666':'Feodosia 2025-10-13',
    '399670':'Feodosia 2025-10-15',
    '399674':'Feodosia 2025-10-18',
    '431493':'Feodosia 2026-01-28',
    '431536':'Feodosia 2026-04-08',
    '431539':'Belgorod 2026-04-16',
    '431557':'Samara 2026-04-21',
    '431572':'Yaroslavl/Rostov 2026-05-08',
    '431597':'Taganrog 2026-05-30',
    '431608':'Taganrog 2026-06-20',
}

def open_csv(zip_path: Path):
    z=zipfile.ZipFile(zip_path)
    names=[n for n in z.namelist() if n.lower().endswith('.csv')]
    if not names: raise RuntimeError(f'No CSV in {zip_path}')
    f=io.TextIOWrapper(z.open(names[0],'r'), encoding='utf-8-sig', newline='')
    return z,f

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--viina-data-dir', type=Path, required=True)
    ap.add_argument('--ru-geonames', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a=ap.parse_args()

    gaz=fv.load_ru_gazetteer(a.ru_geonames)
    lines=[]
    lines.append(f'gazetteer_ids={len(gaz["ids"])}')
    lines.append(f'gazetteer_names={len(gaz["names"])}')
    lines.append(f'gazetteer_grid_cells={len(gaz["grid"])}')

    known_info={k:[] for k in KNOWN}
    known_onepd={k:[] for k in KNOWN}

    for year in range(2022,2027):
        info=a.viina_data_dir/f'event_info_latest_{year}.zip'
        z,f=open_csv(info)
        total=date_ok=gid_nonempty=gid_ru=text_match=key_nonempty=0
        try:
            r=csv.DictReader(f)
            lines.append(f'INFO_{year}_FIELDS='+'|'.join(r.fieldnames or []))
            for row in r:
                total += 1
                d=fv.ndate(row.get('date'))
                if d is None or not fv.START <= d <= fv.END:
                    continue
                date_ok += 1
                gid=str(row.get('geonameid','')).strip()
                if gid:
                    gid_nonempty += 1
                if gid in gaz['ids']:
                    gid_ru += 1
                text=str(row.get('text','') or '')
                c,t,att=fv.hits(text)
                if c and att:
                    text_match += 1
                key=str(row.get('event_id_1pd','')).strip()
                if key:
                    key_nonempty += 1
                if key in KNOWN:
                    known_info[key].append({
                        'year':year,'gid':gid,'gid_ru':gid in gaz['ids'],
                        'date':row.get('date',''),'asciiname':row.get('asciiname',''),
                        'lat':row.get('latitude',''),'lon':row.get('longitude',''),
                        'target_attack_match':bool(c and att),
                        'text':text.replace('\n',' ')[:180],
                    })
        finally:
            f.close(); z.close()
        raw=fv.scan_info(info,gaz)
        lines.append(f'INFO_{year}_COUNTS total={total} date_ok={date_ok} gid_nonempty={gid_nonempty} gid_ru={gid_ru} text_match={text_match} key_nonempty={key_nonempty} raw_keys={len(raw)}')

        one=a.viina_data_dir/f'event_1pd_latest_{year}.zip'
        z,f=open_csv(one)
        total1=raw_join=ukr_init=0
        try:
            r=csv.DictReader(f)
            lines.append(f'ONEPD_{year}_FIELDS='+'|'.join(r.fieldnames or []))
            for row in r:
                total1 += 1
                key=fv.val(row,'event_id_1pd')
                if key in raw:
                    raw_join += 1
                    _,av=fv.first_existing(row,['a_ukr_init_b','a_ukr_init'])
                    if fv.is_true(av):
                        ukr_init += 1
                if key in KNOWN:
                    _,av=fv.first_existing(row,['a_ukr_init_b','a_ukr_init'])
                    decision=fv.location_decision(row,gaz)
                    known_onepd[key].append({
                        'year':year,'gid':fv.val(row,'geonameid'),'asciiname':fv.val(row,'asciiname'),
                        'lat':fv.val(row,'latitude'),'lon':fv.val(row,'longitude'),
                        'a_ukr_init':str(av or ''),'loc_decision':decision,
                        'in_raw':key in raw,
                    })
        finally:
            f.close(); z.close()
        lines.append(f'ONEPD_{year}_COUNTS total={total1} raw_join={raw_join} ukr_init_after_raw_join={ukr_init}')

    lines.append('=== KNOWN_EVENT_DIAGNOSTICS ===')
    for key,label in KNOWN.items():
        lines.append(f'KNOWN {key} {label}')
        lines.append('  INFO='+repr(known_info[key]))
        lines.append('  ONEPD='+repr(known_onepd[key]))

    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print('\n'.join(lines))

if __name__=='__main__':
    main()
