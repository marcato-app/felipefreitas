"""Lista de preços da CMED/Anvisa (PMC - xls) -> cmed.json.gz, embutido no app pelo build.py (/*CMED*/null).

Por código de barras (EAN 1/2/3): PRODUTO, APRESENTAÇÃO (quantidade oficial), LABORATÓRIO, SUBSTÂNCIA,
CLASSE TERAPÊUTICA (EphMRA: "L1H - INIBIDORES DE PROTEINA QUINASE") e TIPO (Genérico, Similar, Novo...).
A planilha tem ~40 linhas de aviso antes do cabeçalho; o script acha a linha com APRESENTAÇÃO e EAN.
Usa o arquivo mais novo de dados/cmed/. Uso: python3 cmed.py [--baixar] && python3 build.py
  --baixar: baixa do site da Anvisa a lista PMC mais nova e os dados abertos de medicamentos registrados.

Medicamentos registrados (dados abertos, DADOS_ABERTOS_MEDICAMENTOS.csv): nome do produto -> princípio ativo e
categoria regulatória (Genérico, Similar, Novo...). Entra só o que não está na lista de preços; a categoria vem do
princípio ativo (dicionário do cliente no app, ou a classe que a substância tem na CMED).
"""
import csv, gzip, io, json, re, sys, unicodedata, urllib.request
from collections import Counter, defaultdict
from pathlib import Path
import openpyxl

here = Path(__file__).parent
N = lambda s: ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()).split())


PAGINA = 'https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos'
DADOS = 'https://dados.anvisa.gov.br/dados/DADOS_ABERTOS_MEDICAMENTOS.csv'


def baixa(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=120) as r: return r.read()


def baixar():
    d = here / 'dados' / 'cmed'; d.mkdir(parents=True, exist_ok=True)
    html = baixa(PAGINA).decode('utf-8', 'ignore')
    m = re.search(r'href="([^"]*xls_conformidade_site_(\d{8})[^"]*)"', html)  # "PMC - xls"
    if m:
        alvo = d / f'cmed_pmc_{m.group(2)}.xlsx'
        if not alvo.exists():
            url = m.group(1) if m.group(1).startswith('http') else 'https://www.gov.br' + m.group(1)
            alvo.write_bytes(baixa(url)); print('baixado', alvo.name)
        else: print('lista PMC já é a mais nova:', alvo.name)
    (d / 'DADOS_ABERTOS_MEDICAMENTOS.csv').write_bytes(baixa(DADOS)); print('baixado DADOS_ABERTOS_MEDICAMENTOS.csv')


def registrados(cprod, sub_cls):
    """nome do produto -> [princípio ativo, classe CMED pela substância, categoria regulatória] (só o que não está na CMED)"""
    f = here / 'dados' / 'cmed' / 'DADOS_ABERTOS_MEDICAMENTOS.csv'
    if not f.exists(): return []
    rows = csv.DictReader(io.StringIO(f.read_bytes().decode('latin-1')), delimiter=';')
    por = defaultdict(Counter)
    for r in rows:
        nome = N(r.get('NOME_PRODUTO', ''))
        if not nome or nome in cprod or len(nome) < 4 or 'DINAMIZADO' in N(r.get('CATEGORIA_REGULATORIA', '')): continue
        pa = N(r.get('PRINCIPIO_ATIVO', '').replace(',', ';'))
        if not pa: continue
        por[nome][(pa, N(r.get('CATEGORIA_REGULATORIA', '')))] += 2 if r.get('SITUACAO_REGISTRO') == 'Ativo' else 1
    out = []
    for nome, c in por.items():
        (pa, tipo), _ = c.most_common(1)[0]
        subs = sorted(x.strip() for x in pa.split(';') if x.strip())
        cls = sub_cls.get(';'.join(subs)) or (sub_cls.get(subs[0]) if len(subs) == 1 else '') or ''
        out.append([nome, ' + '.join(subs), cls, tipo])
    return out


def main():
    if '--baixar' in sys.argv: baixar()
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
    # substância -> classe mais comum na CMED (para os registrados sem preço)
    sc = defaultdict(Counter)
    for r in rows: sc[';'.join(sorted(x.strip() for x in N(out['sub'][r[5]].replace(',', ';')).split(';') if x.strip()))][out['cls'][r[4]]] += 1
    sub_cls = {k: v.most_common(1)[0][0] for k, v in sc.items()}
    out['reg'] = registrados({N(p) for p in out['prod']}, sub_cls)
    raw = json.dumps(out, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    (here / 'cmed.json.gz').write_bytes(gzip.compress(raw, 9))
    print(f"{arqs[-1].name}: {len(rows)} apresentações, {len(vistos)} EANs, {len(idx['prod'])} produtos; "
          f"{len(out['reg'])} registrados fora da lista de preços ({sum(1 for r in out['reg'] if r[2])} com classe pela substância); "
          f"{len(raw)/1e6:.1f} MB -> {(here / 'cmed.json.gz').stat().st_size/1e6:.2f} MB gzip")


if __name__ == '__main__':
    main()
