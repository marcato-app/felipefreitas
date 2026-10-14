# Varredura DE (Detalhe) -> PARA (backlog classificado pelo app): um arquivo por categoria do backlog.
#   python3 -I testes_farma/varredura_backlog.py <BACKLOG_CLASSIFICADO.xlsx> <Detalhe.csv> <pasta_saida>
# Colunas: as do backlog (PARA) + DE do Detalhe + SAIR DE FARMA? + NAS BASES / AVISO + O QUE MUDOU + ALERTAS do app.
import csv, json, re, sys, unicodedata, collections, zipfile
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

csv.field_size_limit(10 ** 9)
here = Path(__file__).resolve().parent.parent
BK, DET, OUT = sys.argv[1], sys.argv[2], Path(sys.argv[3]); OUT.mkdir(parents=True, exist_ok=True)


def N(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().upper()
    return ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', s).split())


def bcn(x):
    s = re.sub(r'\D', '', str(x or '')); return s.lstrip('0')


C = json.loads((here / 'consts.json').read_text(encoding='utf-8'))
of = C.get('nomesOficiais', {})
cesta = {}
for x in C['libSeed']['categorias'] + C['cfg']['categorias']:
    if not x.get('cesta'): continue
    for k in (x['nome'], of.get(x['nome'], '')):
        if k: cesta[N(k)] = x['cesta']
for k, v in of.items():
    if N(k) in cesta: cesta.setdefault(N(v), cesta[N(k)])
    if N(v) in cesta: cesta.setdefault(N(k), cesta[N(v)])
def cesta_de(cat):
    n = N(cat)
    if n in cesta: return cesta[n]
    if re.match(r'^[A-Z]\d\d[A-Z]', n): return 'FARMACIA'
    if n in ('VITAMINA OUTRO', 'MULTIVITAMINICO', 'VITAMINA E MINERAL'): return 'FARMACIA'
    if n in ('CODIGO INTERNO', 'OUTRA CATEGORIA'): return n
    return ''

# bases
dima_m = {N(m[0]) for m in C.get('farmaDima', [])}
hoja_m = {N(m[0]) for m in C.get('farmaMarcas', [])}
vit_m = {N(m[0]) for m in (C.get('farmaVit', {}).get('marcas') or [])} | {N(m[1]) for m in (C.get('farmaVit', {}).get('marcas') or [])}
fabs = {N(x) for x in C.get('hojaFabs', [])} | {N(x) for x in C.get('farmaFabs', {}).values()}
vit_bc = set()
for p in (here / 'dados' / 'vitaminas').glob('*.tsv'):
    for r in csv.DictReader(open(p, encoding='utf-8'), delimiter='\t'): vit_bc.add(bcn(r.get('Codigo Barras')))
cmed = {}
ws = openpyxl.load_workbook(here / 'dados' / 'cmed' / 'cmed_pmc_20260909.xlsx', read_only=True).active
hdr = False
for r in ws.iter_rows(values_only=True):
    if not hdr: hdr = bool(r and str(r[0]).startswith('SUBST')); continue
    for e in r[5:8]:
        e = bcn(e)
        if len(e) >= 8: cmed[e] = (str(r[8] or ''), str(r[2] or ''), str(r[10] or ''), str(r[11] or ''))
sig = lambda m: re.sub(r'\s+[A-Z0-9]{3}$', '', N(m))

# DE: Detalhe
de = {}
rd = csv.reader(open(DET, encoding='utf-16'), delimiter='\t'); h = next(rd)
ix = lambda nome, n=0: [i for i, x in enumerate(h) if x.strip() == nome][n]
iB, iD, iC, i6, i7, iM, iF, iT, iV = ix('barcode'), ix('Descripcion'), ix('Contenido'), ix('Est Mer 6 Descripcion'), ix('Est Mer 7 Descripcion'), ix('Marca'), ix('Fabricante'), ix('TOP_DESCRIPCION'), ix('Imp Vta (Ult 24Meses)')
for r in rd:
    if len(r) > iV: de[bcn(r[iB])] = r

# PARA: backlog
wb = openpyxl.load_workbook(BK, read_only=True)
P = list(wb['Planilha1'].iter_rows(values_only=True)); cabP = list(P[0]); P = P[1:]
RV = list(wb['REVISAO'].iter_rows(values_only=True)); cabR = RV[0]
rv = {bcn(r[0]): r for r in RV[1:]}
jA, jP, jG = cabR.index('ALERTAS'), cabR.index('PRIORIDADE'), cabR.index('PESQUISA GOOGLE')

NAO_FARMA = re.compile(r'(?<![A-Z])(TINTURA CAPILAR|COLORACAO|DESCOLORANTE|CONDICIONADOR|ESMALTE|ACETONA|PERFUME|DESODORANTE|ABSORVENTE|FRALDA|ESCOVA DE CABELO|PENTE|TOALHA|BISCOITO|REFRIGERANTE|CERVEJA|RACAO|BRINQUEDO|PILHA|LAMPADA|CADERNO|IGORA|KOLESTON|ALISANTE|PROGRESSIVA)(?![A-Z])')
VET = re.compile(r'(?<![A-Z])(CAES|CAO|GATOS|GATO|PETS|VETERINARIO|VETERINARIA|VET|BOVINO|BOVINOS|EQUINO|EQUINOS|AVES|SUINOS|DRONTAL|IVERMECTAN|PIOLHOAVES|BRAVECTO|NEXGARD|SIMPARIC|FRONTLINE)(?![A-Z])')
def OXIDANTE(t, fab):  # água oxigenada de cabelo: cremosa, 20/30/40 volumes, 6-12%, marca de cosmético
    t = ' ' + t + ' '
    m = re.search(r'(?<![0-9])(15|20|30|40)\s*(V|VOL|VOLS|VOLUMES)(?![A-Z])', t)
    if m: return m.group(1) + ' volumes'
    if re.search(r'(?<![0-9])(6|9|12)\s*%', t) or re.search(r'(?<![0-9])(6|9|12) (?=1L|900|60ML|90ML)', t): return 'concentração de cabelo'
    for w in ('CREMOSA', 'CREME', 'OXIDANTE', 'DEVELOPER', 'EMULSAO', 'OXILY', 'BLOND', 'DESCOLOR', 'COLORACAO', 'TINTURA', 'IGORA', 'KOLESTON', 'WELLA', 'KEUNE', 'YAMA', 'SALON LINE', 'ALFAPARF', 'LOREAL', 'PROFESSIONAL', 'BEAUTY', 'HAIR'):
        if re.search(r'(?<![A-Z])' + w, t): return w
    if re.search(r'COSMETIC|HAIR|BEAUTY|PROFESSIONAL', fab): return 'fabricante de cosmético'
    return ''
cab = cabP + ['DE DESCRICAO', 'DE DESCRICAO LOJA', 'DE CONTENIDO', 'DE EST MER 6', 'DE EST MER 7', 'DE MARCA', 'DE FABRICANTE', 'VENDA 24M',
              'O QUE MUDOU', 'SAIR DE FARMA?', 'NAS BASES', 'AVISO BASES', 'REGISTRO CMED', 'ALERTAS DO APP', 'PRIORIDADE', 'PESQUISA GOOGLE']
por_cat = collections.defaultdict(list); resumo = collections.defaultdict(collections.Counter)
k = {c: cabP.index(c) for c in cabP}
for r in P:
    b = bcn(r[0]); d = de.get(b); x = rv.get(b)
    cat = str(r[k['CATEGORIA']] or ''); ce = cesta_de(cat)
    de7 = d[i7].strip() if d else ''; de6 = d[i6].strip() if d else ''
    txt = N(' '.join([str(r[k['DESCRITIVO PADRONIZADO']] or ''), d[iD] if d else '', d[iT] if d else '']))
    # o que mudou
    mud = []
    if d:
        if N(de7) != N(cat) and N(de6) != N(cat): mud.append('CATEGORIA')
        if sig(d[iM]) != sig(r[k['MARCA']]): mud.append('MARCA')
        if N(d[iF]) != N(r[k['FABRICANTE']]): mud.append('FABRICANTE')
        try:
            if abs(float(str(d[iC]).replace(',', '.') or 0) - float(r[k['CONTENIDO']] or 0)) > 1e-6: mud.append('CONTENIDO')
        except ValueError: pass
    else: mud.append('NAO ESTA NO DETALHE')
    # sair de farma
    if N(cat) == 'AGUA OXIGENADA' and OXIDANTE(txt, N(r[k['FABRICANTE']])):
        sair = 'SIM - água oxigenada cosmética (oxidante de cabelo: ' + OXIDANTE(txt, N(r[k['FABRICANTE']])) + ') -> PERFUMARIA'
    elif N(cat) == 'AGUA OXIGENADA': sair = 'PROVAVELMENTE FICA - água oxigenada 10 volumes/3% (antisséptica); conferir'
    elif ce and ce not in ('FARMACIA', 'CODIGO INTERNO', 'OUTRA CATEGORIA'): sair = f'SIM - app mandou para {ce}'
    elif ce == 'OUTRA CATEGORIA': sair = 'VERIFICAR - app não achou categoria'
    elif VET.search(' ' + re.sub(r'UNHA DE GATO|GATO PRETO', '', txt) + ' '): sair = 'SIM - produto veterinário (' + VET.search(' ' + txt + ' ').group(1) + ') -> PET'
    elif NAO_FARMA.search(' ' + re.sub(r'LEVED[OU]R?A? DE CERVEJA|LEVEDO CERVEJA|PENTE FINO|PIOLHO', '', txt) + ' '): sair = 'VERIFICAR - descrição parece de outra cesta: ' + NAO_FARMA.search(' ' + txt + ' ').group(1)
    elif ce == 'CODIGO INTERNO': sair = 'CODIGO INTERNO (produtos distintos no código)'
    else: sair = 'NAO'
    # bases
    m0 = sig(r[k['MARCA']]); fab0 = N(r[k['FABRICANTE']])
    bases = []
    if b in cmed: bases.append('CMED (código)')
    if b in vit_bc: bases.append('BASE VITAMINAS (código)')
    if m0 in dima_m: bases.append('DIMA (marca)')
    if m0 in hoja_m: bases.append('HOJA (marca)')
    if m0 in vit_m: bases.append('VITAMINAS (marca)')
    if fab0 in fabs: bases.append('HOJA (fabricante)')
    aviso = ''
    if not bases: aviso = 'NAO CONSTA EM NENHUMA BASE - conferir'
    elif m0 not in dima_m | hoja_m | vit_m and m0 not in ('OUTRA MARCA',) and not (r[k['STATUS']] or '').startswith('SEM'):
        aviso = 'marca nova (não está em DIMA/Hoja/vitaminas)'
    if fab0 and fab0 not in fabs and fab0 != 'OUTRO FABRICANTE': aviso = (aviso + '; ' if aviso else '') + 'fabricante novo (não está no Hoja)'
    cm = cmed.get(b); reg = f'{cm[0]} | {cm[1]} | {cm[2]} | {cm[3]}' if cm else ''
    linha = list(r) + ([d[iD], d[iT], d[iC], de6, de7, d[iM], d[iF], d[iV]] if d else [''] * 8) + \
            [', '.join(mud), sair, ', '.join(bases), aviso, reg, (x[jA] if x else ''), (x[jP] if x else ''), (x[jG] if x else '')]
    por_cat[cat].append(linha)
    rs = resumo[cat]; rs['ITENS'] += 1; rs['MUDOU CATEGORIA'] += 'CATEGORIA' in mud; rs['MUDOU MARCA'] += 'MARCA' in mud
    rs['MUDOU FABRICANTE'] += 'FABRICANTE' in mud; rs['SAIR DE FARMA'] += sair.startswith('SIM'); rs['VERIFICAR FARMA'] += sair.startswith(('VERIFICAR', 'PROVAVELMENTE'))
    rs['SEM BASE'] += aviso.startswith('NAO CONSTA'); rs['CRIAR MARCA/FAB'] += bool(r[k['STATUS']] and 'CRIAR' in str(r[k['STATUS']])); rs['CESTA'] = ce

amarelo, vermelho, verde, azul = (PatternFill('solid', fgColor=c) for c in ('FFF2CC', 'FFC7CE', 'C6EFCE', 'DDEBF7'))
def salva(cat, linhas):
    w = openpyxl.Workbook(); s = w.active; s.title = 'ITENS'; s.append(cab)
    for c in s[1]:
        c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='1F3864' if c.column <= len(cabP) else '7F6000')
        c.alignment = Alignment(wrap_text=True, vertical='top')
    iS, iA = cab.index('SAIR DE FARMA?') + 1, cab.index('AVISO BASES') + 1
    for l in sorted(linhas, key=lambda l: (not str(l[iS - 1]).startswith('SIM'), not str(l[iS - 1]).startswith('VERIF'), -(float(str(l[cab.index('VENDA 24M')]).replace('.', '').replace(',', '.') or 0) if l[cab.index('VENDA 24M')] else 0))):
        s.append(l); rr = s.max_row
        v = str(l[iS - 1]); s.cell(rr, iS).fill = vermelho if v.startswith('SIM') else amarelo if v.startswith(('VERIF', 'CODIGO')) else verde
        if str(l[iA - 1]).startswith('NAO CONSTA'): s.cell(rr, iA).fill = vermelho
        elif l[iA - 1]: s.cell(rr, iA).fill = amarelo
    larg = {'DESCRITIVO PADRONIZADO': 50, 'DE DESCRICAO': 45, 'DE DESCRICAO LOJA': 45, 'ALERTAS DO APP': 60, 'REGISTRO CMED': 45, 'SAIR DE FARMA?': 34, 'NAS BASES': 34, 'AVISO BASES': 34, 'PESQUISA GOOGLE': 20}
    for i, c in enumerate(cab, 1): s.column_dimensions[openpyxl.utils.get_column_letter(i)].width = larg.get(c, 18)
    s.freeze_panes = 'C2'; s.auto_filter.ref = s.dimensions
    nome = re.sub(r'[^A-Za-z0-9 _-]', '', N(cat))[:80].strip() or 'SEM CATEGORIA'
    p = OUT / f'{nome}.xlsx'; w.save(p); return p

arqs = [salva(cat, l) for cat, l in sorted(por_cat.items())]
# resumo geral
w = openpyxl.Workbook(); s = w.active; s.title = 'RESUMO'
cols = ['CATEGORIA (PARA)', 'CESTA', 'ITENS', 'MUDOU CATEGORIA', 'MUDOU MARCA', 'MUDOU FABRICANTE', 'SAIR DE FARMA', 'VERIFICAR FARMA', 'SEM BASE', 'CRIAR MARCA/FAB']
s.append(cols)
for cat, rs in sorted(resumo.items(), key=lambda x: -x[1]['ITENS']):
    s.append([cat, rs['CESTA'], rs['ITENS'], rs['MUDOU CATEGORIA'], rs['MUDOU MARCA'], rs['MUDOU FABRICANTE'], rs['SAIR DE FARMA'], rs['VERIFICAR FARMA'], rs['SEM BASE'], rs['CRIAR MARCA/FAB']])
tot = collections.Counter()
for rs in resumo.values(): tot.update({k2: v for k2, v in rs.items() if k2 != 'CESTA'})
s.append([]); s.append(['TOTAL', '', tot['ITENS'], tot['MUDOU CATEGORIA'], tot['MUDOU MARCA'], tot['MUDOU FABRICANTE'], tot['SAIR DE FARMA'], tot['VERIFICAR FARMA'], tot['SEM BASE'], tot['CRIAR MARCA/FAB']])
for c in s[1]: c.font = Font(bold=True, color='FFFFFF'); c.fill = PatternFill('solid', fgColor='1F3864')
for i, wd in enumerate([52, 14, 8, 12, 12, 14, 12, 14, 10, 14], 1): s.column_dimensions[openpyxl.utils.get_column_letter(i)].width = wd
s.freeze_panes = 'A2'; s.auto_filter.ref = s.dimensions
# de -> para de categoria (matriz)
s2 = w.create_sheet('DE PARA CATEGORIA'); s2.append(['DE EST MER 6', 'DE EST MER 7', 'PARA CATEGORIA', 'ITENS'])
dp = collections.Counter()
for cat, ls in por_cat.items():
    for l in ls: dp[(l[cab.index('DE EST MER 6')], l[cab.index('DE EST MER 7')], cat)] += 1
for (a, b2, c2), n in dp.most_common(): s2.append([a, b2, c2, n])
for c in s2[1]: c.font = Font(bold=True)
for i, wd in enumerate([45, 45, 52, 8], 1): s2.column_dimensions[openpyxl.utils.get_column_letter(i)].width = wd
s2.auto_filter.ref = s2.dimensions
s3 = w.create_sheet('COMO LER')
for t in ['Um arquivo por CATEGORIA do backlog (PARA). Colunas azuis = backlog classificado; marrons = DE (Detalhe) e a análise.',
          'O QUE MUDOU: CATEGORIA / MARCA / FABRICANTE / CONTENIDO em relação ao Detalhe.',
          'SAIR DE FARMA?: SIM quando o app mandou para outra cesta; VERIFICAR quando não achou categoria ou a descrição tem cara de outra cesta (tintura, shampoo, café, pet...).',
          'NAS BASES: onde o item aparece (CMED pelo código, base de vitaminas pelo código, DIMA/Hoja/vitaminas pela marca, Hoja pelo fabricante).',
          'AVISO BASES: NAO CONSTA EM NENHUMA BASE (conferir); marca nova; fabricante novo.',
          'REGISTRO CMED: produto | laboratório | classe terapêutica | tipo, quando o código está na lista CMED.',
          'ALERTAS DO APP / PRIORIDADE / PESQUISA GOOGLE: da aba REVISAO do backlog.']:
    s3.append([t])
s3.column_dimensions['A'].width = 150
pr = OUT / '_RESUMO_VARREDURA.xlsx'; w.save(pr)
z = OUT.parent / (OUT.name + '.zip')
with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zz:
    for p in [pr] + arqs: zz.write(p, p.name)
print(len(arqs), 'arquivos;', dict(tot)); print(z)
