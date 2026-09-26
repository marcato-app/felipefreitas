"""Nome oficial (EST MER 7 / EST MER 6 com o código) das categorias cujo nome interno perdeu o código.

Uma limpeza antiga tirou o código ATC do começo do nome de ~380 categorias de Farmácia
("A02B1 ANTAGONISTAS H2" virou "ANTAGONISTAS H2"). O nome interno fica como está (regras, ligações e o que está
salvo no navegador dependem dele); o nome oficial vai em consts.json -> nomesOficiais e é o que sai na planilha e
o que é reconhecido na coluna CATEGORIA do arquivo. Fontes: dicionário de princípios ativos (Est Mer 6/7) e DIMA.
Nomes sem fonte ficam como estão até chegar a árvore oficial (pôr em dados/arvore_est_mer.xlsx: colunas
EST MER 7 / EST MER 6 com código e rodar de novo).

Uso: python3 nomes_oficiais.py && python3 build.py
"""
import gzip, json, re, unicodedata
from collections import Counter
from pathlib import Path
import openpyxl

here = Path(__file__).parent
N = lambda s: ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()).split())
COD = re.compile(r'^[A-Z]\d{2}[A-Z]?\d?\s+')
tira = lambda s: COD.sub('', s.strip())


# decididos com o cliente quando a fonte tem mais de um código para o mesmo nome
FIXOS = {'CORTICOIDES': 'S01B CORTICOIDES',  # R03D ou S01B: cliente escolheu o oftalmológico
         'INJETAVEIS': 'H02A1 INJETAVEIS'}  # corticosteroide puro injetável (CMED H02A1)


# categorias que a CMED não resolveu sozinha: código EphMRA conferido à mão com a classe da CMED (ou com a base do
# cliente, quando ela já traz o nome: A11A1 PRENATAL, A03E OUTRAS ASSOCIACOES). Só vale quando ainda não há código.
MANUAL = {
    'REFORCO DO AMP CICLICO PLAQUETARIO INIBIDORES': 'B01C4', 'COMBINACOES DE INIBIDORES DA CICLO OXIGENASE COM': 'B01C5',
    'COMBINACOES': 'B03A2', 'AGENTES POUPADORES DE POTASSIO COMBINADOS COM TIAZ': 'C03A5',
    'ANTAGONISTAS DO CALCIO ASSOCIADOS COM BETA BLOQUEA': 'C08B2', 'INIBIDORES ACE COMBINADOS COM ANTI HIPERTENSIVOS': 'C09B1',
    'INIBIDORES ACE COMBINADOS COM ANTAGONISTAS DO CALC': 'C09B3', 'ANTAGONISTAS ANGIOTENSINA II ASSO COM A HIPERT C2': 'C09D1',
    'ANTAGONISTAS ANGIONTENSINA II ASSOCIADOS COM ANTAG': 'C09D3', 'TRICOMONICIDAS FORMAS COMBINADAS': 'G01A3',
    'OUTROS PRODUTOS GINECOLOGICOS': 'G02X9', 'MONOFASICOS IGUAL OU MAIOR 50 MCG ESTROGENOS': 'G03A2',  # G03A1 = menor 50 MCG
    'PREPARADOS BIFASICOS': 'G03A3', 'PREPARADOS TRIFASICOS': 'G03A4',
    'COMBINACAO DE ALFA-ANDRENERGICO C 5ARI ANTAGONISTA': 'G04C4', '5 ARI E OU ANTAGONISTAS ALFA ANDRENERGICO COMBI': 'G04C7',
    'ANTIVIRAES PARA COVID': 'J05B6', 'IMUNOGLOB ANTIRSV': 'J06H6', 'VACINAS RSV': 'J07E7', 'AGUA AGUA BIDESTILADA': 'K01B4',
    'SOLUCOES PROTEICAS MENOR 5 PORCENTO': 'K03B3', 'SOLUCOES ELETROLITICAS MAIOR 20 ML': 'K04A2',
    'CITOSTATICOS ESTROGENICOS': 'L02A1', 'CITOSTATICOS PROGESTINICOS': 'L02A2', 'CITOSTATICOS ANTIESTROGENOS': 'L02B1',
    'ASSOCIADOS': 'M01A2', 'BIFOSFONATOS PARA DESORDENES TUMORAES': 'M05B4', 'SEDANTES HIPNOTICOS': 'N05B2',
    'A DEPRESSIVOS C ERVAS': 'N06A2', 'ANTICOLI ACA CURTA C AGON B2 AC CURTA INA': 'R03L1', 'OUTROS ANTITUSSIGENOS ASSOC': 'R05D2',
    'SISTEMICOS': 'S01E1', 'OUTROS PRODUTOS PARA OLHO SECO': 'S01K9', 'TOPICOS OFTALMOLOGICOS OUTROS': 'S01X2',
    'PROD P ELIMINAR CERA DO OUVIDO': 'S02D1', 'TODOS OS OUTROS OTOLOGICOS': 'S02D9',
    'TODOS OUTROS AGENTES CURATIVOS FERIDAS': 'D03A9', 'ANTIPRURIGINOSOS INCLUSIVE ANTIHISTAMINICOS ANEST': 'D04A',
    'COM ANTIBACTERIANOS': 'D07B1', 'COM ANTIMICOTICOS': 'D07B2', 'COM ANTIBACTERIANOS E ANTIMICOTICOS': 'D07B3',
    'OUTRAS ASSOCIACOES DERMATOLOGICAS': 'D07B4',
    'OUTRAS ASSOCIACOES DIGESTIVAS': 'A03E OUTRAS ASSOCIACOES', 'PRENATAL POLIVITAMINICO': 'A11A1 PRENATAL',
    'PRENATAL VITAMINICO PURO': 'A11B1 PRENATAL',
}
# mesma classe de outra categoria do app (categoria repetida): recebem o nome oficial da que já tem o código
MESMO_QUE = {'AGONISTAS DE TROMBOPOIETINA': 'B02E', 'ANTICOLINERGICOS ACAO PROLONG COMB C AGON B2 A': 'R03L2',
             'PRODUTOS PARA TRATAMENTO DA DOENCA PILMONAR CRONIC': 'R03X', 'ANTISEPTICOS OCULARES': 'S01A'}
# não são medicamento (correlato, dermocosmético, suplemento de varejo): não existe código ATC/EphMRA; ficam com o nome
SEM_ATC = ['AUXILIAR PARA RESPIRACAO', 'AUXILIAR PARA TRATAMENTO', 'CURATIVO', 'MONITORAMENTO E TESTE', 'CORRELATO OUTROS',
           'PRIMEIROS SOCORROS', 'LUVA DE PROCEDIMENTO', 'LUBRIFICANTE INTIMO GEL', 'MASCARA DE PROTECAO', 'SORO FISIOLOGICO',
           'VITAMINA OUTRO', 'MULTIVITAMINICO', 'DERMOCOSMETICO CAPILAR', 'DERMOCOSMETICO CORPORAL', 'DERMOCOSMETICO FACIAL',
           'DERMOCOSMETICO SOLAR', 'AGUA OXIGENADA']


def manual(cats, out):
    """MANUAL / MESMO_QUE para quem ainda não tem código; devolve as linhas para a planilha"""
    nomes = {x['nome'] for x in cats}; rel = []
    for k, v in MANUAL.items():
        if k in nomes and not COD.match(out.get(k, '')):
            out[k] = v if ' ' in v else v + ' ' + N(conserta(k)); rel.append([k, out[k].split(' ')[0], out[k], 'manual (EphMRA x CMED)', ''])
    for k, cod in MESMO_QUE.items():
        dono = next((v for v in out.values() if v.split(' ')[0] == cod), None)
        if k in nomes and dono and not COD.match(out.get(k, '')):
            out[k] = dono; rel.append([k, cod, dono, 'mesma classe de outra categoria do app', 'categoria repetida'])
    rel += [[k, '', '', 'não é medicamento: sem código ATC/EphMRA', ''] for k in SEM_ATC if k in nomes and not COD.match(out.get(k, ''))]
    return rel


def conserta(nome):
    """mojibake (ANÃ\\x81LOGOS -> ANALOGOS) e hífen que sobrou no lugar do código"""
    try: t = nome.encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError): t = nome
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode()
    return re.sub(r'^[-\s]+', '', t).strip()


SIN = {'PREOTEINA': 'PROTEINA', 'KINASE': 'QUINASE', 'ANTIINFLAMATORIOS': 'ANTI INFLAMATORIOS', 'ANTIREUMATICOS': 'ANTI REUMATICOS',
       'ESTEROIDES': 'ESTEROIDAIS', 'DESCONGESTIVOS': 'DESCONGESTIONANTES', 'OFTALMICOS': 'OFTALMOLOGICOS', 'CORTICOESTEROIDES': 'CORTICOIDES', 'CORTICOSTEROIDES': 'CORTICOIDES'}
STOP = set('DE DA DO DAS DOS E EM PARA A O OS AS OU C P INCLUINDO EXCETO EXCLUINDO'.split())
ASSOC = re.compile(r'(?<![A-Z])(ASSO\w*|COMB\w*|COM (?!ACAO|ATIVIDADE)\w+|C [A-Z]\w*|FORMAS COMBINADAS)(?![A-Z])')


GENERICAS = set('OUTROS OUTRAS TODOS TODAS PRODUTOS PREPARACOES AGENTES SIMPLES PUROS PURAS ASSOCIADOS ASSOCIACOES'.split())


def distintas(a, b):
    """palavras em comum que não são genéricas (OUTROS, PRODUTOS...); palavra cortada vale (INTERF = INTERFERONAS)"""
    A, B = toks(a) - GENERICAS, toks(b) - GENERICAS
    n = sum(1 for x in A if any(x == y or (min(len(x), len(y)) >= 5 and (x.startswith(y) or y.startswith(x))) for y in B))
    return 9 if toks(a) == toks(b) else n  # nome idêntico ("TODOS OUTROS ANTINEOPLASICOS") sempre vale


def conflito(cat, cl):
    """nome da categoria e da classe dizem coisas opostas: puro x associado, sistêmico x tópico, com x sem"""
    a, b = N(cat), N(cl)
    if bool(ASSOC.search(a)) != bool(ASSOC.search(b)): return True
    if bool(re.search(r'PUROS?|PURAS?|SOZINHOS|SOLO|SIMPLES', a)) and ASSOC.search(b): return True
    for x, y in (('SISTEMIC', 'TOPIC'), ('ORA', 'INJET'), ('NASA', 'OFTAL')):
        if (x in a and y in b and x not in b) or (y in a and x in b and y not in b): return True
    if re.search(r'\bSEM\b', a) and not re.search(r'\bSEM\b', b): return True
    return False


def toks(s):
    t = re.sub(r'\bANTI (?=[A-Z])', 'ANTI', N(s)).replace('OFTAMOLOGICOS', 'OFTALMOLOGICOS')  # ANTI HISTAMINICOS = ANTIHISTAMINICOS
    return {SIN.get(w, w) for w in t.split() if w not in STOP}


def cod_cmed(c):
    m = re.match(r'^\s*([A-Z])\s*(\d{1,2})\s*([A-Z])\s*(\d)?', N(c))
    return (m.group(1) + m.group(2).zfill(2) + m.group(3) + (m.group(4) or '')) if m else None


def pela_cmed(cats, out):
    """categoria de Farmácia sem código -> código EphMRA da lista CMED/Anvisa, por duas pistas:
    termos da categoria (substâncias/produtos do "incluir") -> classe deles na CMED, e nome da categoria x nome da classe.
    Só grava quando as pistas concordam; tudo vai para dados/farma_nomes_oficiais_cmed.xlsx para conferir."""
    cz = here / 'cmed.json.gz'
    if not cz.exists(): return []
    j = json.loads(gzip.decompress(cz.read_bytes()))
    linhas = [(j['prod'][r[1]], j['sub'][r[5]], j['cls'][r[4]]) for r in j['rows']]
    for h in sorted((here / 'dados' / 'cmed' / 'historico').glob('*.json.gz')):
        linhas += [(r[1], r[5], r[4]) for r in json.loads(gzip.decompress(h.read_bytes()))]
    nome_cls, por_termo = {}, {}
    for prod, sub, cl in linhas:
        k = cod_cmed(cl)
        if not k: continue
        nome_cls.setdefault(k, Counter())[N(re.sub(r'^[^-]*-\s*', '', cl))] += 1
        for t in [N(prod)] + [N(x) for x in re.split(r'[;,+]', sub)]:
            if t: por_termo.setdefault(t, Counter())[k] += 1
    nome_cls = {k: v.most_common(1)[0][0] for k, v in nome_cls.items()}
    usados = {v.split(' ')[0] for v in out.values() if COD.match(v)}
    rel = []
    for x in cats:
        if x.get('cesta') != 'FARMACIA' or COD.match(out.get(x['nome'], '')): continue
        votos = Counter()
        for t in x.get('incluir') or []:
            t = N(str(t).replace('*', ' '))
            c = por_termo.get(t) or next((v for k, v in por_termo.items() if k.endswith(' ' + t) or k.startswith(t + ' ')), None)  # CLORIDRATO DE X
            if c: votos[c.most_common(1)[0][0]] += 1
        tn = toks(x['nome'])
        sim = lambda k: len(tn & toks(nome_cls[k])) / max(1, len(tn | toks(nome_cls[k])))
        escolha, motivo, obs = None, '', ''
        if votos:
            k, v = votos.most_common(1)[0]
            ok = v / sum(votos.values()) >= 0.6 and (sim(k) >= 0.3 or (v >= 2 and sim(k) > 0) or v >= 4)
            if ok and not conflito(x['nome'], nome_cls[k]) and k not in usados: escolha, motivo = k, f'termos ({v} de {sum(votos.values())}) + nome {sim(k):.2f}'
            elif ok: obs = f'recusado: {k} {nome_cls[k]}' + (' (código já usado)' if k in usados else ' (nome em conflito)')
        if not escolha:
            cand = sorted(((sim(k), k) for k in nome_cls if len(k) == 5 and k not in usados and not conflito(x['nome'], nome_cls[k]) and distintas(x['nome'], nome_cls[k]) >= 2), reverse=True)[:2]
            if cand and cand[0][0] >= 0.6 and (len(cand) < 2 or cand[0][0] - cand[1][0] >= 0.15): escolha, motivo = cand[0][1], f'nome {cand[0][0]:.2f}'
        rel.append([x['nome'], escolha or '', nome_cls.get(escolha, '') if escolha else '', motivo, obs, sim(escolha) if escolha else 0])
    # cada código para uma categoria só (a de nome mais parecido)
    dono = {}
    for r in rel:
        if r[1] and (r[1] not in dono or r[5] > dono[r[1]][5]): dono[r[1]] = r
    for r in rel:
        if r[1] and dono[r[1]] is not r: r[4] = f'recusado: {r[1]} ficou com {dono[r[1]][0]}'; r[1] = r[2] = r[3] = ''
    # segunda rodada, só pelo nome, para quem perdeu a disputa ou não achou nada (sem repetir código)
    tomados = usados | {r[1] for r in rel if r[1]}
    for r in rel:
        if r[1]: continue
        tn = toks(r[0]); sim = lambda k: len(tn & toks(nome_cls[k])) / max(1, len(tn | toks(nome_cls[k])))
        cand = sorted(((sim(k), k) for k in nome_cls if len(k) == 5 and k not in tomados and not conflito(r[0], nome_cls[k]) and distintas(r[0], nome_cls[k]) >= 2), reverse=True)[:2]
        if cand and cand[0][0] >= 0.5 and (len(cand) < 2 or cand[0][0] - cand[1][0] >= 0.15):
            r[1], r[2], r[3] = cand[0][1], nome_cls[cand[0][1]], f'nome {cand[0][0]:.2f} (2ª rodada)'; tomados.add(r[1])
    for r in rel:
        if r[1]: out[r[0]] = r[1] + ' ' + N(conserta(r[0]))
    for r in rel: r.pop()
    wb = openpyxl.Workbook(); ws = wb.active; ws.title = 'Pela CMED'
    ws.append(['CATEGORIA DO APP', 'CODIGO', 'CLASSE NA CMED', 'PISTA', 'OBS'])  # OBS: o que foi recusado e por quê
    for r in rel: ws.append(r)
    wb.save(here / 'dados' / 'farma_nomes_oficiais_cmed.xlsx')
    return rel


def main():
    c = json.loads((here / 'consts.json').read_text(encoding='utf-8'))
    cats = c['libSeed']['categorias'] + c['cfg']['categorias']
    fonte = {}
    def junta(v):
        v = str(v).strip()
        if v and N(v) != 'POR DEFECTO' and COD.match(v): fonte.setdefault(N(tira(v)), set()).add(v)
    for r in openpyxl.load_workbook(here / 'dados' / 'dicionario_nomenclaturas_farmaceuticas.xlsx', read_only=True)['Dicionário'].iter_rows(min_row=2, values_only=True):
        for v in (r[4], r[5]):
            if v: junta(v)
    for s in json.loads(gzip.decompress((here / 'dima.json.gz').read_bytes()))['segs']: junta(s)
    # base de marcas de Farmácia do cliente (farma_marcas.py): colunas Est Mer 6 / Est Mer 7 Descripcion
    from farma_marcas import ler_linhas
    for p in sorted((here / 'dados' / 'farma_marcas').glob('*')):
        if p.suffix.lower() in ('.tsv', '.csv', '.txt'):
            for r in ler_linhas(p):
                for v in (r.get('EST MER 6 DESCRIPCION'), r.get('EST MER 7 DESCRIPCION')):
                    if v: junta(re.sub(r'^([A-Z]\d\d[A-Z]?\d?)\s+-\s+', r'\1 ', conserta(v).strip()))
    arv = here / 'dados' / 'arvore_est_mer.xlsx'
    if arv.exists():
        for ws in openpyxl.load_workbook(arv, read_only=True).worksheets:
            for row in ws.iter_rows(values_only=True):
                for v in row:
                    if v: junta(v)
    out, amb = {}, []
    for x in cats:
        k = N(conserta(x['nome'])); f = {v for v in fonte.get(k, set()) if ' - ' not in v} or fonte.get(k, set())
        cod = lambda v: v.split(' ')[0]
        f = {v for v in f if not any(o != v and cod(o).startswith(cod(v)) for o in f)}  # código mais específico
        if len(f) == 1: out[x['nome']] = next(iter(f))
        elif len(f) > 1: amb.append((x['nome'], sorted(f)))
        elif conserta(x['nome']) != x['nome']: out[x['nome']] = conserta(x['nome'])
    out.update({k: v for k, v in FIXOS.items() if any(x['nome'] == k for x in cats)})
    rel = pela_cmed(cats, out)  # categorias de Farmácia ainda sem código: código pela lista CMED/Anvisa
    man = manual(cats, out)
    wb = openpyxl.load_workbook(here / 'dados' / 'farma_nomes_oficiais_cmed.xlsx'); ws = wb.create_sheet('Manual e sem ATC')
    ws.append(['CATEGORIA DO APP', 'CODIGO', 'NOME OFICIAL', 'PISTA', 'OBS'])
    for r in man: ws.append(r)
    wb.save(here / 'dados' / 'farma_nomes_oficiais_cmed.xlsx')
    amb = [a for a in amb if a[0] not in FIXOS]
    c['nomesOficiais'] = out
    (here / 'consts.json').write_text(json.dumps(c, ensure_ascii=False), encoding='utf-8')
    far = [x['nome'] for x in cats if x.get('cesta') == 'FARMACIA']
    print(f"{len(out)} nomes oficiais ({sum(1 for n in far if n in out)} de {len(far)} de Farmácia); ambíguos: {amb}")
    print(f"pela CMED: {sum(1 for r in rel if r[1])} códigos novos de {len(rel)} categorias sem código (dados/farma_nomes_oficiais_cmed.xlsx)")
    print(f"manual: {sum(1 for r in man if r[1])} códigos; sem código ATC (não é medicamento): {[r[0] for r in man if not r[1]]}")
    print('Farmácia ainda sem código:', [x['nome'] for x in cats if x.get('cesta') == 'FARMACIA' and not COD.match(out.get(x['nome'], '')) and x['nome'] not in SEM_ATC])


if __name__ == '__main__':
    main()
