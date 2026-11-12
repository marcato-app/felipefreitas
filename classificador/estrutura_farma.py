"""Estrutura nova de Farmácia do cliente (dados/farma_estrutura/*.tsv: EST MER 3..7 + código, exportação "Hoja").

- nome oficial (o que sai na planilha) e código EST MER 7 de cada categoria de Farmácia do app passam a ser os da
  estrutura nova, escritos como o cliente escreve (inclusive espaço duplo: "R01A9 OUTRAS PREPARACOES TOPICAS  NASAIS");
- folhas da estrutura que o app não tinha viram categorias novas (A11A2 PEDIATRICOS, A11X3 VITAMINA E PURA, COLAGENO...);
- categorias que deixaram de existir (VITAMINA OUTRO, MULTIVITAMINICO, grupos que viraram subgrupos: H02A -> H02A1/H02A2)
  vão para consts.json -> farmaCatNova {categoria antiga: categoria nova}; vitamina/mineral é decidido no app pela
  composição (vitNova em src.html) e o valor daqui é só o padrão.
Uso: python3 estrutura_farma.py && python3 build.py   (depois de estmer.py)
"""
import csv, json, re, unicodedata
from pathlib import Path

here = Path(__file__).parent
N = lambda s: ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().upper()).split())
code = lambda s: (re.match(r'^([A-Z]\d\d[A-Z]\d?)(?![A-Z0-9])', N(s)) or [None, None])[1]
sem = lambda s: re.sub(r'^[A-Z]\d\d[A-Z]?\d?\s+', '', N(s))

# grupo que virou subgrupos / código que mudou: categoria antiga -> código (ou nome) da folha nova
MANUAL = {
    'VITAMINA OUTRO': 'A11X9', 'MULTIVITAMINICO': 'A11A4',  # padrão; o app decide pela composição
    'A03G': 'A03A', 'B01X': 'B01C4', 'B02E': 'B02E1', 'B02D': 'B02D1', 'J05B': 'J05B9', 'K03B3': 'K03B1', 'K04A2': 'K04A1',
    'R03X': 'R03X2', 'A13A': 'A13A2', 'C05A': 'C05A2', 'C07B': 'C07B1', 'D07B': 'D07B4', 'H01C': 'H01C2', 'H02A': 'H02A2',
    'J06H': 'J06H6', 'J07B': 'J07B1', 'L02A': 'L02A3', 'S01G': 'S01G1',
    'EXTRATO DE PROPOLIS': 'PROPOLIS', 'TONICOS E RECONSTITUINTES': 'A13A2',
}


def ler(p):
    raw = p.read_bytes()
    txt = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('utf-8-sig')
    return list(csv.DictReader(txt.splitlines(), delimiter='\t'))


def main():
    c = json.loads((here / 'consts.json').read_text(encoding='utf-8'))
    of, em = c.setdefault('nomesOficiais', {}), c.setdefault('estMer7', {})
    T = []
    for p in sorted((here / 'dados' / 'farma_estrutura').glob('*.tsv')): T += ler(p)
    folhas = {}
    for r in T:
        r = {k.strip().upper(): (v or '').strip() for k, v in r.items()}
        e7, e6, k = r.get('EST MER 7 DESCRIPCION', ''), r.get('EST MER 6 DESCRIPCION', ''), r.get('EST MER CODIGO', '')
        nome = e6 if re.search(r'DEFECTO', e7, re.I) else e7
        if not nome or not re.match(r'^\.?\d+(\.\d+)+$', k): continue
        if r.get('EST MER 3 DESCRIPCION') and N(r['EST MER 3 DESCRIPCION']) != 'FARMACIA': continue
        if N(e6) == 'SUPLEMENTO NUTRICIONAL' and N(nome) == 'COLAGENO': continue  # 2 SKUs; colágeno é FARMACIA > COLAGENO
        f = folhas.get(N(nome))
        if not f or len(k) > len(f[1]): folhas[N(nome)] = (nome, k)
    byC, byS = {}, {}
    for n, (nome, k) in folhas.items():
        if code(nome): byC.setdefault(code(nome), []).append(n)
        byS.setdefault(sem(nome), []).append(n)
    cats = [x for x in c['libSeed']['categorias'] + c['cfg']['categorias'] if x.get('cesta') == 'FARMACIA' or x['nome'] in MANUAL]
    usadas, par, sem_par = set(), {}, []
    for passo in (1, 2):  # 1: mesmo nome (com ou sem código); 2: mesmo código, nome mudou (A07G REPOSITORES -> REIDRATANTES)
        for x in cats:
            n = x['nome']; o = of.get(n, n); f = None
            if n in par: continue
            cand = []
            if passo == 1:
                if N(o) in folhas: cand.append(N(o))
                if len(byS.get(sem(o), [])) == 1 and (not code(o) or (code(folhas[byS[sem(o)][0]][0]) or '')[:3] == code(o)[:3]): cand.append(byS[sem(o)][0])  # N05B2 SEDANTES -> N05B5
                if len(byS.get(N(n), [])) == 1 and (not code(o) or (code(folhas[byS[N(n)][0]][0]) or '')[:1] == code(o)[:1]): cand.append(byS[N(n)][0])  # nome interno = folha nova (AGONISTAS DE TROMBOPOIETINA -> B02E1)
            elif code(o) and len(byC.get(code(o), [])) == 1 and code(o) not in MANUAL: cand.append(byC[code(o)][0])
            f = next((k for k in cand if k not in usadas), None)
            if f and f not in usadas: par[n] = f; usadas.add(f)
    sem_par = [x['nome'] for x in cats if x['nome'] not in par]
    # categorias novas (folha sem categoria no app): nome interno = nome oficial com o código
    modelo = next(x for x in c['libSeed']['categorias'] if x.get('cesta') == 'FARMACIA')
    existentes = {x['nome'] for x in c['libSeed']['categorias'] + c['cfg']['categorias']}
    novas = []
    for f, (nome, k) in folhas.items():
        if f in usadas: continue
        nm = ' '.join(nome.split())
        if nm in existentes: nm = nm + ' FARMACIA'
        novas.append(nm)
        if nm not in existentes:
            x = {k2: (type(v)() if isinstance(v, (list, dict)) else v) for k2, v in modelo.items()}
            x.update({'nome': nm, 'cesta': 'FARMACIA', 'ativa': modelo.get('ativa', False), 'inicio': '', 'pctMin': None,
                      'regra': f'Estrutura nova do cliente ({k}).', 'dinamico': True})
            c['libSeed']['categorias'].append(x); existentes.add(nm)
        par[nm] = f
    for n, f in par.items():
        of[n] = folhas[f][0]; em[n] = folhas[f][1]
    # nome oficial -> categoria do app (para os destinos de farmaCatNova)
    por_cod, por_nome = {}, {}
    for n, f in par.items():
        if code(folhas[f][0]): por_cod.setdefault(code(folhas[f][0]), n)
        por_nome.setdefault(N(folhas[f][0]), n)
    nova, falta = {}, []
    for n in sem_par:
        o = of.get(n, n); alvo = MANUAL.get(n) or MANUAL.get(code(o) or '-')
        d = (por_cod.get(alvo) or por_nome.get(N(alvo))) if alvo else None
        if d: nova[n] = d
        else: falta.append(n)
    c['farmaCatNova'] = nova
    (here / 'consts.json').write_text(json.dumps(c, ensure_ascii=False), encoding='utf-8')
    print(f'{len(folhas)} folhas na estrutura; {len(par) - len(novas)} categorias do app com par, {len(novas)} novas, {len(nova)} trocadas')
    print('  novas:', novas)
    print('  trocadas:', {k: of.get(v, v) for k, v in nova.items()})
    if falta: print('  SEM DESTINO:', falta)


if __name__ == '__main__':
    main()
