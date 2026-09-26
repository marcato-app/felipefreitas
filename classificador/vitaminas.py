"""VITAMINA E MINERAL (EST MER 6 do cliente): aprende com a base da categoria inteira (dados/vitaminas/*.tsv).

Na base do cliente todo suplemento de vitamina/mineral fica em VITAMINA E MINERAL -> VITAMINA OUTRO ou MULTIVITAMINICO,
mesmo os que têm registro de remédio (CITONEURIN, DEPURA, CALTRATE); os grupos ATC A11/A12/A13 quase não são usados.
Saída (consts.json -> farmaVit):
- marcas: [[termo, marca da base, fabricante, % MULTIVITAMINICO, SKUs, genérico 0/1], ...]  (marca da base e da DIMA VITAMINA E MINERAL)
- pesos: {palavra: peso}  log-odds MULTIVITAMINICO x VITAMINA OUTRO (naive Bayes nas descrições das lojas e do cliente)
- prior: log-odds da base
- fora: marcas que a DIMA/Hoja só conhecem fora de vitamina (não trocam para VITAMINA OUTRO)
Uso: python3 vitaminas.py && python3 build.py   (depois de dima.py)
"""
import csv, gzip, json, math, re, unicodedata
from collections import Counter, defaultdict
from pathlib import Path

here = Path(__file__).parent
N = lambda s: ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().upper()).split())
SEM = {'OUTRA MARCA', 'POR DEFECTO', 'OUTRO FABRICANTE', 'SIN PROVEEDOR ASOCIADO', ''}
# palavra que sozinha não é marca (a descrição traz em qualquer produto)
COMUM = set('SUPL ALIM SUPLEMENTO ALIMENTAR VITAMINA VITAMINAS VIT MULTI MAX PLUS PRO GOLD LIFE NATURAL NATURE KIDS BABY '
            'MULHER HOMEM SENIOR FORTE ULTRA MEGA SUPER CAPS CAPSULAS COMPRIMIDOS PO GOTAS FARMA PHARMA LAB NUTRI NUTRITION '
            'HEALTH VITA BIO OLEO SAUDE VIDA ZERO FIT'.split())


NUTRI = set('VITAMINA VIT OMEGA COMPLEXO MAGNESIO ZINCO CALCIO COLAGENO BIOTINA COENZIMA CURCUMA SELENIO FERRO CROMO '
            'MELATONINA LUTEINA LICOPENO METILFOLATO ACIDO OLEO CLORETO CITRATO CARBONATO MACA SPIRULINA PROPOLIS '
            'CASTANHA VINAGRE CAFEINA TRIPTOFANO GLUTAMINA COQ10 L MULTIVITAMINICO POLIVITAMINICO CARVAO FENO'.split())


CODIGOS = set()  # sufixos que são código de laboratório (repetem em várias marcas: RDF, NES, HAL, CAT); montado no main()


def termo(marca):
    """nome da marca como aparece na descrição: sem o código do laboratório ("SUNDOWN NES" -> SUNDOWN, "(HAL)")"""
    m = N(re.sub(r'\s*\([A-Z0-9 ]{0,5}\)\s*$', '', str(marca)))
    b = re.match(r'^(.*\S)\s+([A-Z]{3})$', m)
    return [m] + ([b.group(1)] if b and b.group(2) in CODIGOS and len(b.group(1)) >= 3 else [])


def main():
    base = []
    for p in sorted((here / 'dados' / 'vitaminas').glob('*.tsv')):
        base += list(csv.DictReader(open(p, encoding='utf-8'), delimiter='\t'))
    multi = lambda b: b['Est Mer 7 Descripcion'] == 'MULTIVITAMINICO'
    dz0 = here / 'dima.json.gz'
    todas = [b['Marca'] for b in base] + (json.loads(gzip.decompress(dz0.read_bytes()))['marcas'] if dz0.exists() else [])
    suf = defaultdict(set)
    for m in todas:
        x = re.match(r'^(.*\S)\s+([A-Z]{3})$', N(m))
        if x: suf[x.group(2)].add(x.group(1))
    CODIGOS.update(k for k, v in suf.items() if len(v) >= 3 and k not in COMUM and k not in ('NEW', 'MAX', 'PRO', 'ONE', 'DAY', 'MIX', 'FIT', 'TOP', 'KID'))
    # marcas: termo -> (marca da base mais usada, fabricante mais usado, SKUs multi, SKUs)
    por = defaultdict(lambda: [Counter(), Counter(), 0, 0])
    for b in base:
        if N(b['Marca']) in SEM: continue
        for t in termo(b['Marca']):
            x = por[t]; x[0][b['Marca'].strip()] += 1; x[2] += multi(b); x[3] += 1
            if N(b['Fabricante']) not in SEM: x[1][b['Fabricante'].strip()] += 1
    cj = json.loads((here / 'consts.json').read_text(encoding='utf-8'))
    of = cj.get('nomesOficiais', {})
    vit_cat = lambda cat: cat in ('VITAMINA OUTRO', 'MULTIVITAMINICO') or re.match(r'^A1[123][A-Z]', of.get(cat, cat) or '')
    # remédio de outro grupo que caiu na base por engano (NEOSALDINA, MOUNJARO): a DIMA ou a base de marcas de Farmácia
    # (Hoja) só conhecem a marca fora de vitamina -> não é marca de vitamina e trava a troca para VITAMINA OUTRO
    segs_de = defaultdict(set)
    dz = here / 'dima.json.gz'
    d = json.loads(gzip.decompress(dz.read_bytes())) if dz.exists() else {'rows': [], 'segs': [], 'marcas': [], 'fabs': []}
    for k in range(0, len(d['rows']), 3):
        for t in termo(d['marcas'][d['rows'][k]]): segs_de[t].add(d['segs'][d['rows'][k + 1]])
    fora = set()
    for t, ss in segs_de.items():
        if any(re.match(r'^[A-Z]\d\d', x) and not re.match(r'^A1[123]', x) for x in ss): fora.add(t)  # classe ATC fora de vitamina
    for m in cj.get('farmaMarcas', []):  # a base de marcas de Farmácia do cliente (Hoja) é por produto: vale mais que a DIMA
        if m[1] and not vit_cat(m[1]): fora.add(N(m[0]))
    if d['rows']:  # marcas da DIMA em VITAMINA E MINERAL que a base não tem
        r = d['rows']
        for k in range(0, len(r), 3):
            if d['segs'][r[k + 1]] != 'VITAMINA E MINERAL': continue
            mar, fab = d['marcas'][r[k]], d['fabs'][r[k + 2]]
            if N(mar) in SEM: continue
            for t in termo(mar):
                if t in por: continue
                x = por[t]; x[0][mar] += 1; x[3] += 0
                if N(fab) not in SEM: x[1][fab] += 1
    marcas = []
    for t, (m, f, nm, n) in sorted(por.items()):
        if len(t) < 3 or t in COMUM or t.isdigit() or (n < 10 and any(x in fora for x in termo(t))): continue
        if n <= 1 and ' ' not in t and len(t) <= 4: continue  # 1 SKU e nome curto (GABA, TOP): pouca prova
        # nome genérico usado como marca (OMEGA 3, VITAMINA C, COMPLEXO B): vários fabricantes ou nome de nutriente;
        # só vale quando a descrição não traz marca de verdade, e sem fabricante
        gen = int(len(f) >= 3 or t.split()[0] in NUTRI)
        marcas.append([t, m.most_common(1)[0][0], '' if gen else (f.most_common(1)[0][0] if f else ''), round(nm / n, 2) if n else -1, n, gen])
    # marca de 2+ palavras que a loja escreve só com a 1ª (ESSENTIAL NUTRITION -> ESSENTIAL): 1ª palavra única e distintiva
    ja = {m[0] for m in marcas}; prim = Counter(m[0].split()[0] for m in marcas if len(m[0].split()) > 1 and not m[5])
    for m in list(marcas):
        w = m[0].split()
        if len(w) > 1 and not m[5] and prim[w[0]] == 1 and len(w[0]) >= 5 and w[0] not in COMUM | NUTRI and w[0] not in ja and w[0] not in fora:
            marcas.append([w[0]] + m[1:]); ja.add(w[0])
    # naive Bayes MULTIVITAMINICO x VITAMINA OUTRO nas palavras das descrições
    cnt = {True: Counter(), False: Counter()}; tot = Counter()
    for b in base:
        w = set()
        for c in ('Descripcion', 'TOP_DESCRIPCION', 'MAX_DESCRIPCION'): w |= set(N(b[c]).split())
        w = {x for x in w if not x.isdigit() and x not in ('SUPL', 'ALIM', 'MULT')}  # MULT é o padrão que o cliente escreve
        cnt[multi(b)].update(w); tot[multi(b)] += 1
    pesos = {}
    for x in set(cnt[True]) | set(cnt[False]):
        a, o = cnt[True][x], cnt[False][x]
        if a + o < 8: continue
        v = math.log((a + 1) / (tot[True] + 2)) - math.log((o + 1) / (tot[False] + 2))
        if abs(v) >= 0.7: pesos[x] = round(v, 2)
    prior = round(math.log(tot[True] / tot[False]), 2)
    # só trava as marcas que aparecem na base de vitaminas (as que caíram lá por engano); as outras já não são marca de vitamina
    trava = sorted(t for t in fora if t in por and por[t][3] < 10 and len(t) >= 3 and t not in COMUM and t.split()[0] not in NUTRI)
    cj['farmaVit'] = {'marcas': marcas, 'pesos': pesos, 'prior': prior, 'fora': trava}
    (here / 'consts.json').write_text(json.dumps(cj, ensure_ascii=False), encoding='utf-8')
    # acerto do modelo MULTI x OUTRO na própria base (só as palavras, sem a marca)
    ok = 0
    for b in base:
        w = set()
        for col in ('TOP_DESCRIPCION', 'MAX_DESCRIPCION'): w |= set(N(b[col]).split())
        s = prior + sum(pesos.get(x, 0) for x in w)
        ok += (s > 0) == multi(b)
    print(f"{len(base)} SKUs da base; {len(marcas)} marcas de vitamina ({sum(1 for m in marcas if m[4])} da base); "
          f"{len(pesos)} palavras MULTI x OUTRO; acerto só pelas palavras das lojas {100 * ok / max(1, len(base)):.0f}%")


if __name__ == '__main__':
    main()
