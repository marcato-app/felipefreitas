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
            'HEALTH VITA BIO OLEO SAUDE VIDA ZERO FIT HOMEM MULHER INFANTIL GESTANTE ADULTO CABELO CABELOS PELE UNHA UNHAS '
            'IMUNIDADE IMUNE VEGANO VEGANA VEGAN COMPLEXO EXTRATO SKIN HAIR NAILS BEAUTY'.split())


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
        if re.match(r'^(A ?Z|POLIVITAMINICO|MULTIVITAMINICO)( |$)', t): continue  # A Z TEU (1 SKU): indica multivitamínico, não é marca
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
    # nome de linha que a loja escreve no lugar da marca (ADDERITOS = ADDERA, linha infantil): 1ª palavra da descrição da
    # loja que começa com o nome da marca (5+ letras iguais) -> mesma marca
    por_t = {m[0]: m for m in marcas}; lin = defaultdict(Counter)
    for b in base:
        ts = [t for t in termo(b['Marca']) if t in por_t and not por_t[t][5]]
        if not ts: continue
        t = ts[-1]
        for col in ('TOP_DESCRIPCION', 'MAX_DESCRIPCION', 'Descripcion'):
            w = (N(b[col]).split() or [''])[0]
            if len(w) > len(t.split()[0]) >= 5 and len(w) >= 6 and w.startswith(t.split()[0][:max(5, len(t.split()[0]) - 1)]) and w not in COMUM | NUTRI: lin[w][t] += 1
    for w, cn in lin.items():
        t, v = cn.most_common(1)[0]
        if w not in ja and w not in fora and v / sum(cn.values()) >= 0.8: marcas.append([w] + por_t[t][1:]); ja.add(w)
    print('linhas da marca:', sorted((w, cn.most_common(1)[0][0]) for w, cn in lin.items() if w in ja)[:20])
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
    # planilha de padrões do cliente: categoria de remédio de vitamina (A11, A12, A13, B02B) é "FARMA" -> sem início fixo
    pz = here / 'dados' / 'padroes_descritivo.xlsx'
    if pz.exists():
        import openpyxl
        pad = {N(r[0]): N(r[2]) for r in list(openpyxl.load_workbook(pz, read_only=True).worksheets[0].iter_rows(values_only=True))[1:] if r[0]}
        for x in cj['libSeed']['categorias'] + cj['cfg']['categorias']:
            o = of.get(x['nome'], '')
            if x.get('cesta') == 'FARMACIA' and x.get('inicio') and re.match(r'^(A1[123]|B02B)', o) and pad.get(N(o), 'FARMA') in ('FARMA', ''):
                x['inicio'] = ''
    # prefixo da empresa no código de barras (789 + 4 a 6 dígitos) -> fabricante (>= 80% dos SKUs, 3+ SKUs): suplemento
    # sem fabricante na descrição ganha o do dono do código de barras
    pre = defaultdict(Counter)
    for b in base:
        e = re.sub(r'\D', '', b['Codigo Barras']).lstrip('0')
        if len(e) == 13 and e[:3] in ('789', '790') and N(b['Fabricante']) not in SEM:
            for k in (7, 8, 9): pre[e[:k]][b['Fabricante'].strip()] += 1
    pref = {p: c.most_common(1)[0][0] for p, c in pre.items() if (sum(c.values()) >= 3 and c.most_common(1)[0][1] / sum(c.values()) >= 0.8) or (sum(c.values()) == 2 and len(c) == 1)}  # 2 SKUs do mesmo fabricante também
    # fabricante que só faz suplemento (50%+ dos SKUs na DIMA em vitamina, cálcio/minerais A11-A13, colágeno, probiótico, ou 3+ SKUs na base e fora da DIMA):
    # item sem categoria com o nome dele ou o prefixo dele no código de barras é vitamina (MAXINUTRI X 60 CPR)
    fd = defaultdict(Counter)
    for k in range(0, len(d['rows']), 3):
        f = d['fabs'][d['rows'][k + 2]]
        if N(f) not in SEM: fd[f.strip()][bool(re.match(r'^(VITAMINA E MINERAL|COLAGENO|SUPLEMENTO|A1[123][A-Z]|A07F|B03A)', d['segs'][d['rows'][k + 1]]))] += 1
    fb = Counter(b['Fabricante'].strip() for b in base if N(b['Fabricante']) not in SEM)
    fab_vit = sorted({f for f, c in fd.items() if sum(c.values()) >= 3 and c[True] / sum(c.values()) >= 0.5} |
                     {f for f, n in fb.items() if n >= 3 and f not in fd})
    cj['farmaVit'] = {'marcas': marcas, 'pesos': pesos, 'prior': prior, 'fora': trava, 'pref': pref, 'fabVit': fab_vit}
    (here / 'consts.json').write_text(json.dumps(cj, ensure_ascii=False), encoding='utf-8')
    # acerto do modelo MULTI x OUTRO na própria base (só as palavras, sem a marca)
    ok = 0
    for b in base:
        w = set()
        for col in ('TOP_DESCRIPCION', 'MAX_DESCRIPCION'): w |= set(N(b[col]).split())
        s = prior + sum(pesos.get(x, 0) for x in w)
        ok += (s > 0) == multi(b)
    print(len(fab_vit), 'fabricantes só de suplemento, ex.:', [f for f in fab_vit if f in ('MAXINUTRI', 'KATIGUA', 'UNILIFE', 'GRUPO PANVEL', 'BAYER', 'ACHE LABORATORIOS FARMACEUTICOS SA', 'KRESS FARMACEUTICA', 'GOLD VITAM')])
    print(f"{len(base)} SKUs da base; {len(marcas)} marcas de vitamina ({sum(1 for m in marcas if m[4])} da base); "
          f"{len(pesos)} palavras MULTI x OUTRO; acerto só pelas palavras das lojas {100 * ok / max(1, len(base)):.0f}%")


if __name__ == '__main__':
    main()
