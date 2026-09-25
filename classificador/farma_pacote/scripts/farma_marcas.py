"""Base de marcas de Farmácia do cliente (marca x fabricante x EST MER 7) -> consts.json (farmaMarcas, farmaCodLab).

Arquivos em dados/farma_marcas/*.tsv|*.csv (exportação "Hoja": fabricante, Marca, Algoritmo Marca Propia,
Est Mer 6 Descripcion, EST_MER_6_CODIGO, Est Mer 7 Descripcion, Est Mer Codigo, Imp venta últ 24 meses, Qtd Sku).
A marca vem com o código do laboratório no fim ("DEXILANT TKD", "OMEPRAZOL TEU", "ENTEROGERMINA (OPE)").

- Marca comercial (sem princípio ativo no nome): nome sem o código -> categoria (EST MER 7 de maior venda) e fabricante.
- Genérico (princípio ativo no nome): a marca é o próprio princípio ativo; a linha só ensina o código do laboratório
  (TEU -> TEUTO), que vira o fabricante.

Uso: python3 farma_marcas.py && python3 build.py   (rodar depois de farma_pa.py e nomes_oficiais.py)
"""
import csv, io, json, re, unicodedata
from collections import defaultdict
from pathlib import Path

here = Path(__file__).parent
N = lambda s: ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()).split())
COD = re.compile(r'^[A-Z]\d{2}[A-Z]?\d?\s+(-\s+)?')
SEM_FAB = {'OUTRO FABRICANTE', 'SIN PROVEEDOR ASOCIADO', ''}
# sal/abreviação que vem antes do princípio ativo ("CLOR DE METFORMINA")
SAIS = set('CLOR CLORID CLORIDR CLORIDRATO HCL SOD SODICO SODICA POT POTASSICO POTASSICA MAL MALEATO SUCC SUCCINATO '
           'ACET ACETATO SULF SULFATO CIT CITRATO FOSF FOSFATO BESIL BESILATO MESIL MESILATO TART TARTARATO DE DI'.split())


def conserta(t):
    try: return t.encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError): return t


def _tabela(p):
    b = p.read_bytes()
    t = b.decode('utf-16') if b[:2] in (b'\xff\xfe', b'\xfe\xff') else b.decode('utf-8-sig')
    return list(csv.reader(io.StringIO(t.replace('\r', '')), delimiter='\t' if '\t' in t.split('\n')[0] else ';'))


def ler_linhas(p):
    """linhas como dict (cabeçalho normalizado: 'EST MER 7 DESCRIPCION'...)"""
    rows = _tabela(p); h = [N(x) for x in rows[0]]
    return [dict(zip(h, r)) for r in rows[1:]]


def ler(p):
    rows = _tabela(p)
    h = [N(x) for x in rows[0]]
    col = lambda *ks: next(i for i, x in enumerate(h) if any(x.startswith(k) for k in ks))
    iF, iM, i7, iV = col('FABRICANTE'), col('MARCA'), col('EST MER 7'), col('IMP VENTA')
    for r in rows[1:]:
        if len(r) > max(iF, iM, i7, iV) and r[iM].strip():
            yield r[iF].strip(), r[iM].strip(), conserta(r[i7].strip()), float(re.sub(r'[^0-9]', '', r[iV]) or 0)


def separa(marca, fab):
    """'DEXILANT TKD' -> ('DEXILANT', 'TKD'); 'ENTEROGERMINA (OPE)' -> ('ENTEROGERMINA', 'OPE'); 'NEO B EUR' -> ('NEO B', 'EUR')"""
    m = re.match(r'^(.*?)\s*\(([A-Z0-9]{2,4})\)$', marca.strip())
    if m: return N(m.group(1)), m.group(2)
    w = N(marca).split()
    if len(w) > 1 and (re.fullmatch(r'[A-Z0-9]{3}', w[-1]) or (len(w[-1]) >= 2 and N(fab).replace(' ', '').startswith(w[-1]))):
        return ' '.join(w[:-1]), w[-1]
    return ' '.join(w), ''


def main():
    c = json.loads((here / 'consts.json').read_text(encoding='utf-8'))
    cats = [x for x in c['libSeed']['categorias'] + c['cfg']['categorias'] if x.get('cesta') == 'FARMACIA']
    of = c.get('nomesOficiais', {})
    interna = {}
    for x in cats:
        interna.setdefault(N(x['nome']), x['nome'])
        if x['nome'] in of: interna.setdefault(N(of[x['nome']]), x['nome']); interna.setdefault(N(COD.sub('', of[x['nome']])), x['nome'])
    termos = sorted({N(a) for r in c.get('farmaPA', []) for p in r['partes'] for a in p.split('|') if N(a)}, key=len, reverse=True)
    rx_pa = re.compile(r'(?<![A-Z0-9])(?:' + '|'.join(map(re.escape, termos)) + r')(?![A-Z0-9])') if termos else None

    com = defaultdict(lambda: {'cat': defaultdict(float), 'fab': defaultdict(float)})
    codfab = defaultdict(lambda: defaultdict(float))
    sem_cat, n = set(), 0
    for p in sorted((here / 'dados' / 'farma_marcas').glob('*')):
        if p.suffix.lower() not in ('.tsv', '.csv', '.txt'): continue
        for fab, marca, e7, v in ler(p):
            n += 1; nome, cod = separa(marca, fab); v = v or 1
            if cod and fab not in SEM_FAB: codfab[cod][fab] += v
            if not nome or (rx_pa and rx_pa.search(nome)) or nome.split()[0] in SAIS: continue  # genérico: marca = princípio ativo
            cat = interna.get(N(e7)) or interna.get(N(COD.sub('', e7)))
            if cat: com[nome]['cat'][cat] += v
            elif N(e7) != 'POR DEFECTO': sem_cat.add(e7)
            if fab not in SEM_FAB: com[nome]['fab'][fab] += v
    top = lambda d: max(d.items(), key=lambda kv: kv[1])[0] if d else ''
    marcas = [[nome, top(d['cat']), top(d['fab']), len(d['cat'])] for nome, d in sorted(com.items()) if len(nome) >= 3]
    codlab = {}
    for cod, d in codfab.items():
        tot = sum(d.values()); f = top(d)
        if d[f] / tot >= 0.8: codlab[cod] = f
    c['farmaMarcas'] = marcas; c['farmaCodLab'] = codlab
    (here / 'consts.json').write_text(json.dumps(c, ensure_ascii=False), encoding='utf-8')
    print(f"{n} linhas -> {len(marcas)} marcas comerciais ({sum(1 for m in marcas if m[1])} com categoria, "
          f"{sum(1 for m in marcas if m[3] > 1)} em mais de uma), {len(codlab)} códigos de laboratório; "
          f"EST MER 7 sem categoria no app: {sorted(sem_cat)}")


if __name__ == '__main__':
    main()
