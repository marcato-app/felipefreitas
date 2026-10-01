"""Dicionário de siglas de laboratório (3 letras) para o fim do descritivo de Farmácia: "NIMESULIDA 100MG 12CPRS (GER)".

Fontes (sem duplicar): marcas da DIMA com o código no fim ("NIMESULIDA GER", "DORFLEX (OPE)"), códigos da base de marcas de
Farmácia do cliente (Hoja, farmaCodLab) e a base de VITAMINA E MINERAL (marca "SUNDOWN NES", descrição "... (NES)").
- codigos: sigla -> fabricante (o que mais aparece com ela, >= 50% e 2+ vezes)
- fab: fabricante -> sigla padrão (a que tem as letras do nome: HYPERA -> HYP; senão a mais usada); fabricante sem
  nenhuma sigla nas bases ganha uma gerada (3 primeiras letras do nome, sem repetir), marcada para revisão
Saída: consts.json -> farmaSiglas e dados/farma_siglas_laboratorios.xlsx (para conferir).
Uso: python3 siglas.py && python3 build.py   (depois de dima.py e farma_marcas.py)
"""
import csv, gzip, json, re, unicodedata
from collections import Counter, defaultdict
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill

here = Path(__file__).parent
N = lambda s: ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().upper()).split())
SEM = {'OUTRO FABRICANTE', 'SIN PROVEEDOR ASOCIADO', 'SIN PROVEEDOR', 'POR DEFECTO', ''}
LIXO = set('LABORATORIO LABORATORIOS LAB LABS FARMACEUTICA FARMACEUTICOS FARMACEUTICO FARMA PHARMA PHARMACEUTICA IND '
           'INDUSTRIA COM COMERCIO SA S A LTDA ME EIRELI DO DA DE E BRASIL BR CIA GRUPO'.split())
NAO_SIGLA = set('MARCA OUTRA OUTRO COM SEM CPR COMP CAP CAPS CPS DRG GTS SOL SUS XPE AMP INJ CRE POM GEL ADT INF PED UND '
                'MCG MEQ REV OPC GOT KIT MAX PRO NEW ONE DAY MIX FIT TOP KID VIT MAG ZERO SUN MET DUO FOR XR RET ORO ZIN CAL FER OMG'.split())  # palavra de produto (MET = metformina)
# palavras que não distinguem um fabricante de outro (razão social): somem na chave do nome único
FAB_LIXO = LIXO | set('LABORATORIOS FARMACETICA FARMACEUTICAS FARMACEUTICOS FARMACEUTICO IMPORTACAO EXPORTACAO IMP EXP MEDICAMENTOS DISTRIBUIDORA'.split())
chave_fab = lambda f: ' '.join(w for w in N(f).split() if w not in FAB_LIXO)
ok_sigla = lambda s: bool(re.fullmatch(r'(?=.*[A-Z])[A-Z0-9]{3}', s)) and s not in NAO_SIGLA  # 1FA (1FARMA) também vale


def main():
    c = json.loads((here / 'consts.json').read_text(encoding='utf-8'))
    cod = defaultdict(Counter)  # sigla -> fabricante -> ocorrências
    def junta(marca_ou_desc, fab):
        if N(fab) in SEM: return
        m = re.search(r'\(([A-Z0-9]{3})\)\s*$', str(marca_ou_desc).upper()) or re.match(r'^.*\S\s+([A-Z0-9]{3})$', N(marca_ou_desc))
        if m and ok_sigla(m.group(1)): cod[m.group(1)][fab.strip()] += 1
    d = json.loads(gzip.decompress((here / 'dima.json.gz').read_bytes()))
    r = d['rows']
    for k in range(0, len(r), 3): junta(d['marcas'][r[k]], d['fabs'][r[k + 2]])
    for s, f in (c.get('farmaCodLab') or {}).items():
        if ok_sigla(s): cod[s][f] += 3  # base de marcas de Farmácia do cliente
    for p in sorted((here / 'dados' / 'vitaminas').glob('*.tsv')):
        for b in csv.DictReader(open(p, encoding='utf-8'), delimiter='\t'):
            junta(b['Marca'], b['Fabricante']); junta(b['Descripcion'], b['Fabricante'])
    codigos = {}
    for s, fs in cod.items():
        f, v = fs.most_common(1)[0]
        if v / sum(fs.values()) >= 0.5 and v >= 2: codigos[s] = f
    # fabricante -> sigla padrão
    por_fab = defaultdict(Counter)
    for s, f in codigos.items(): por_fab[f][s] += cod[s][f]
    fab, rel = {}, []
    iniciais = lambda f: ''.join(w for w in N(f).split() if w not in LIXO)
    for f, ss in por_fab.items():
        ini = iniciais(f)
        pref = [s for s in ss if ini.startswith(s)]
        fab[N(f)] = pref[0] if pref else ss.most_common(1)[0][0]
    # código que a base Hoja usa para o laboratório vale como sigla padrão dele, mesmo sendo palavra comum (FER = FERRING)
    for sg, f in (c.get('farmaCodLab') or {}).items():
        if re.fullmatch(r'(?=.*[A-Z])[A-Z0-9]{3}', sg) and N(f) not in fab: fab[N(f)] = sg
    # fabricantes das bases sem nenhuma sigla: gera (3 primeiras letras do nome, sem colidir com sigla de outro)
    # só fabricantes de Farmácia: EST MER 6 com código ATC ou de categoria da cesta Farmácia, base Hoja e base de vitaminas
    farma = {N(x['nome']) for x in c['libSeed']['categorias'] + c['cfg']['categorias'] if x.get('cesta') == 'FARMACIA'} | {'VITAMINA E MINERAL'}
    seg_farma = lambda sg: bool(re.match(r'^[A-Z]\d\d', sg)) or N(sg) in farma
    todos = Counter(d['fabs'][r[k + 2]] for k in range(0, len(r), 3) if seg_farma(d['segs'][r[k + 1]]) and N(d['fabs'][r[k + 2]]) not in SEM)
    for p in sorted((here / 'dados' / 'vitaminas').glob('*.tsv')):
        for b in csv.DictReader(open(p, encoding='utf-8'), delimiter='\t'):
            if N(b['Fabricante']) not in SEM: todos[b['Fabricante'].strip()] += 1
    for m in c.get('farmaMarcas', []):
        if m[2] and N(m[2]) not in SEM: todos[m[2]] += 1
    usadas = set(codigos)
    geradas = {}
    for f in sorted(todos):
        if N(f) in fab: continue
        ini = iniciais(f) or N(f).replace(' ', '')
        cands = [ini[:3]] + [ini[0] + x + y for x in ini[1:] for y in ini[2:]] if len(ini) >= 3 else []
        s = next((x for x in cands if ok_sigla(x) and x not in usadas), None)
        if s: fab[N(f)] = s; usadas.add(s); geradas[N(f)] = s
    # sigla de cada marca como a base de marcas de Farmácia do cliente (Hoja) escreve: NATZ RDF, PICOPREP FER, VIVACITA PRO
    # (vale antes da sigla padrão do fabricante; inclui siglas que são palavra comum, só para aquela marca)
    marcas = {}
    try:
        from farma_marcas import ler
        for pz in sorted((here / 'dados' / 'farma_marcas').glob('*')):
            if pz.suffix.lower() not in ('.tsv', '.csv', '.txt'): continue
            for f, m, _e7, v in ler(pz):
                x = re.match(r'^(.*\S)\s+\(?([A-Z0-9]{3})\)?$', N(m) if '(' not in str(m) else str(m).upper().strip())
                if x and re.fullmatch(r'(?=.*[A-Z])[A-Z0-9]{3}', x.group(2)): marcas.setdefault(N(x.group(1)), Counter())[x.group(2)] += (v or 1)
    except Exception as e:
        print('Hoja:', e)
    marcas = {k: c.most_common(1)[0][0] for k, c in marcas.items()}
    # nome único de cada fabricante: grafias do mesmo fabricante (SANOFI FARMACEUTICA / SANOFI FARMACEUTICA LTDA,
    # GROSS / LABORATORIO GROSS, PANVEL / GRUPO PANVEL) viram a mais usada nas bases do cliente (a base Hoja pesa mais)
    peso = Counter()
    for f, n in todos.items(): peso[f.strip()] += n
    for m in c.get('farmaMarcas', []):
        if m[2] and N(m[2]) not in SEM: peso[m[2].strip()] += 50
    canon = {}
    for f, n in sorted(peso.items(), key=lambda x: (-x[1], len(x[0]))):
        k = chave_fab(f)
        if k and k not in canon: canon[k] = f
    # nome curto que é começo de um só nome mais completo e bem mais usado (UNIAO -> UNIAO QUIMICA, FORHEALTH ->
    # FORHEALTH NUTRICIONAL); VITA, APIS (vários nomes começam assim) não juntam
    pk = Counter()
    for f, n in peso.items(): pk[chave_fab(f)] += n
    juntou = []
    for k in list(canon):
        if ' ' in k or len(k) < 4 or N(canon[k]) != k: continue  # GLOBAL MEDICAMENTOS, SOUL BRASIL: a palavra que sumiu pode distinguir
        longos = [x for x in canon if x.startswith(k + ' ')]
        if len(longos) == 1 and pk[longos[0]] >= 3 * pk[k]:
            juntou.append((canon[k], canon[longos[0]])); canon[k] = canon[longos[0]]
    print('juntados pelo começo do nome:', juntou)
    c['farmaFabs'] = canon
    c['farmaSiglas'] = {'codigos': codigos, 'fab': fab, 'marcas': marcas}
    (here / 'consts.json').write_text(json.dumps(c, ensure_ascii=False), encoding='utf-8')
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Siglas'
    ws.append(['SIGLA', 'FABRICANTE', 'OCORRENCIAS NAS BASES', 'ORIGEM', 'SIGLA PADRAO DO FABRICANTE?'])
    for x in ws[1]: x.font = Font(bold=True, color='FFFFFF'); x.fill = PatternFill('solid', fgColor='1F3864')
    for s in sorted(codigos): ws.append([s, codigos[s], sum(cod[s].values()), 'bases (DIMA/Hoja/vitaminas)', 'SIM' if fab.get(N(codigos[s])) == s else ''])
    for f, s in sorted(geradas.items(), key=lambda x: x[1]): ws.append([s, f, 0, 'GERADA (conferir)', 'SIM'])
    for col, w in zip('ABCDE', [8, 45, 12, 28, 14]): ws.column_dimensions[col].width = w
    ws.auto_filter.ref = ws.dimensions; ws.freeze_panes = 'A2'
    wb.save(here / 'dados' / 'farma_siglas_laboratorios.xlsx')
    print(f"{len(canon)} fabricantes (nome único; {sum(peso.values() and 1 for f in peso) - len(canon)} grafias juntadas)")
    print(f"{len(marcas)} marcas com sigla na Hoja; {len(codigos)} siglas das bases ({len(por_fab)} fabricantes), {len(geradas)} geradas; "
          f"ex.: EMS PHARMA={fab.get('EMS PHARMA')} HYPERA={fab.get('HYPERA PHARMA')} GER={codigos.get('GER')} -> dados/farma_siglas_laboratorios.xlsx")


if __name__ == '__main__':
    main()
