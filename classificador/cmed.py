"""Lista de preços da CMED/Anvisa (PMC - xls) -> cmed.json.gz, embutido no app pelo build.py (/*CMED*/null).

Por código de barras (EAN 1/2/3): PRODUTO, APRESENTAÇÃO (quantidade oficial), LABORATÓRIO, SUBSTÂNCIA,
CLASSE TERAPÊUTICA (EphMRA: "L1H - INIBIDORES DE PROTEINA QUINASE") e TIPO (Genérico, Similar, Novo...).
A planilha tem ~40 linhas de aviso antes do cabeçalho; o script acha a linha com APRESENTAÇÃO e EAN.
Usa o arquivo mais novo de dados/cmed/. Uso: python3 cmed.py && python3 build.py
"""
import gzip, json, re, unicodedata
from pathlib import Path
import openpyxl

here = Path(__file__).parent
N = lambda s: ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()).split())


def main():
    arqs = sorted((here / 'dados' / 'cmed').glob('*.xls*'))
    if not arqs: print('sem arquivo em dados/cmed'); return
    ws = openpyxl.load_workbook(arqs[-1], read_only=True).worksheets[0]
    it = ws.iter_rows(values_only=True); H = None
    for r in it:
        if r and any('APRESENTA' in str(v or '').upper() for v in r) and any('EAN' in str(v or '').upper() for v in r):
            H = [N(v or '').replace(' ', '') for v in r]; break
    col = lambda t: next(i for i, x in enumerate(H) if x.startswith(t))
    iS, iL, iP, iA, iC, iT = col('SUBSTANCIA'), col('LABORATORIO'), H.index('PRODUTO'), col('APRESENTACAO'), col('CLASSETERAPEUTICA'), col('TIPODEPRODUTO')
    iE = [i for i, x in enumerate(H) if x.startswith('EAN')]
    idx = {k: {} for k in 'prod lab cls sub tipo'.split()}
    ix = lambda k, v: idx[k].setdefault(str(v or '').strip(), len(idx[k]))
    rows, vistos = [], set()
    for r in it:
        if not r or not r[iP]: continue
        eans = [re.sub(r'\D', '', str(r[i] or '')).lstrip('0') for i in iE]
        eans = [e for e in eans if len(e) >= 8 and e not in vistos]
        if not eans: continue
        vistos.update(eans)
        rows.append([','.join(eans), ix('prod', r[iP]), str(r[iA] or '').strip(), ix('lab', r[iL]), ix('cls', r[iC]), ix('sub', r[iS]), ix('tipo', r[iT])])
    inv = lambda d: [k for k, _ in sorted(d.items(), key=lambda kv: kv[1])]
    out = {'fonte': arqs[-1].name, **{k: inv(v) for k, v in idx.items()}, 'rows': rows}
    raw = json.dumps(out, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    (here / 'cmed.json.gz').write_bytes(gzip.compress(raw, 9))
    print(f"{arqs[-1].name}: {len(rows)} apresentações, {len(vistos)} EANs, {len(idx['prod'])} produtos; "
          f"{len(raw)/1e6:.1f} MB -> {(here / 'cmed.json.gz').stat().st_size/1e6:.2f} MB gzip")


if __name__ == '__main__':
    main()
