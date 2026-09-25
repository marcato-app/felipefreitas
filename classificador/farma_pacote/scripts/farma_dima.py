"""Categoria de Farmácia pela DIMA: marca/substância -> EST MER 6 (ATC EphMRA nível 3) -> categoria do app.

A DIMA (dima.json.gz) tem 252 EST MER 6 de Farmácia e ~12 mil marcas nelas ("NIMESULIDA EMS", "DORFLEX (OPE)").
O nome sem o código do laboratório vira termo; a EST MER 6 mais votada (>= 60% das linhas) dá o código; o código
vira a categoria do app (EST MER 7 com esse prefixo no nome oficial):
- uma categoria só com o prefixo: ela;
- várias: associação (+, " E ", COMP/ASSOC no nome) -> filha com ASSOC/COMB/COM no nome; senão a filha "pura"
  (PUROS/SIMPLES/SOLO/SOLA) ou a de menor número; marcada para revisão;
- nenhuma com código: categoria cujo nome interno é o da EST MER 6 (sem o código).
Vale depois da base Hoja (farma_marcas.py) e do dicionário de princípios ativos (farma_pa.py): só completa o que eles
não sabem. Saída: consts.json -> farmaDima = [[termo, categoria, EST MER 6, escolhida(0/1)], ...]

Uso: python3 farma_dima.py && python3 build.py   (depois de dima.py, nomes_oficiais.py e farma_marcas.py)
"""
import gzip, json, re, unicodedata
from collections import defaultdict, Counter
from pathlib import Path

here = Path(__file__).parent
N = lambda s: ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()).split())
COD = re.compile(r'^([A-Z]\d\d[A-Z]?\d?)\s+(-\s+)?')
cod = lambda s: (COD.match(s + ' ') or [None, None])[1]
NAO = set('OUTRA OUTRO MARCA FABRICANTE GENERICO GENERICA SIMILAR COMPRIMIDO COMPRIMIDOS CAPSULA CAPSULAS GOTAS XAROPE '
          'POMADA CREME GEL SPRAY SOLUCAO SUSPENSAO AMPOLA INJETAVEL COLIRIO PO SACHE LIQUIDO NATURAL KIT INFANTIL ADULTO '
          'FARMA PHARMA LABORATORIO LAB'.split())


# EST MER 6 cuja categoria no app ainda não tem o código no nome: ligação feita à mão (1 = escolha incerta, vai para revisão)
MAPA6 = {
    'A03E': ('OUTRAS ASSOCIACOES DIGESTIVAS', 0), 'C04A': ('VASOTERAPIA CEREBRAL E PERIF EXCLUINDO ANTAG CALC', 0),
    'C06B': ('OUTROS PRODUTOS PARA A HIPERTENSAO ARTERIAL PULMON', 1), 'C08B': ('ANTAGONISTAS DO CALCIO ASSOCIADOS COM BETA BLOQUEA', 1),
    'C09B': ('INIBIDORES ACE COMBINADOS COM ANTI HIPERTENSIVOS', 1), 'C09D': ('ANTAGONISTAS ANGIOTENSINA II ASSO COM A HIPERT C2', 1),
    'D03A': ('TODOS OUTROS AGENTES CURATIVOS FERIDAS', 1), 'D04A': ('ANTIPRURIGINOSOS INCLUSIVE ANTIHISTAMINICOS ANEST', 0),
    'D06D': ('OUTROS PRODUTOS TOPICOS PARA INFECOES VIRAIS', 0), 'G01A': ('TRICOMONICIDAS TOPICOS', 1),
    'G02X': ('OUTROS PRODUTOS GINECOLOGICOS', 0), 'J01H': ('PENICILINAS PEQUENO MEDIANO ESPECTRO PURAS', 0),
    'K01F': ('TERAPIA OSMOTICA', 0), 'K03B': ('SOLUCOES PROTEICAS MENOR 5 PORCENTO', 1), 'K04A': ('SOLUCOES ELETROLITICAS MAIOR 20 ML', 1),
    'L01X': ('TODOS OUTROS ANTINEOPLASICOS', 0), 'M01A': ('ANTI REUMATICOS NAO ESTEROIDAIS PUROS', 0),
    'N01B': ('ANESTESICOS LOCAIS MEDICINAIS INJETAVEIS', 1), 'R03F': ('AGONISTAS BETA 2  E CORTICOIDES INAL COMBIN', 0),
    'R03L': ('ANTICOLINERGICOS ACAO PROLONG COMB C AGON B2 A', 0), 'S01C': ('COMBINACOES DE CORTICOESTEROIDES OFTALMICOS E ANTI', 0),
    'S01E': ('TOPICOS OFTALMOLOGICOS ANTIGLAUCOMA', 0), 'S01K': ('OUTROS PRODUTOS PARA OLHO SECO', 0),
    'S01X': ('TOPICOS OFTALMOLOGICOS OUTROS', 0), 'S02D': ('TODOS OS OUTROS OTOLOGICOS', 0), 'T02X': ('TODOS OUTROS TESTES DIAGNOSTICOS', 0),
}


# EST MER 6 da DIMA sem código ATC que é de Farmácia (vitaminas de marca: EPHYNAL, EMAMA)
SEG_EXTRA = {'VITAMINA E MINERAL': ('VITAMINA OUTRO', 1)}


def separa(m):
    x = re.match(r'^(.*?)\s*\(([A-Z0-9]{2,4})\)$', m.strip()) or re.match(r'^(.*\S)\s+([A-Z0-9]{3})$', m.strip())
    return N(x.group(1)) if x else N(m)


def main():
    c = json.loads((here / 'consts.json').read_text(encoding='utf-8'))
    d = json.loads(gzip.decompress((here / 'dima.json.gz').read_bytes()))
    of = c.setdefault('nomesOficiais', {})
    # EST MER 6 de Farmácia da DIMA sem nenhuma categoria no app: cria a categoria (nome oficial com o código)
    todas = c['libSeed']['categorias'] + c['cfg']['categorias']
    temcod = {cod(of.get(x['nome'], '') or x['nome']) for x in todas if x.get('cesta') == 'FARMACIA'}
    nomes = {N(x['nome']) for x in todas}
    novas = []
    for seg in sorted(x for x in d['segs'] if cod(x)):
        k = cod(seg)
        if any(t and t.startswith(k) for t in temcod) or k in MAPA6: continue
        nome = N(COD.sub('', seg))
        if nome in nomes: of[nome] = k + ' ' + nome; continue  # já criada numa rodada anterior
        c['libSeed']['categorias'].append({'ativa': False, 'cesta': 'FARMACIA', 'nome': nome, 'inicio': '', 'incluir': [], 'tambem': [],
                                           'excluir': [], 'forte': [], 'pctMin': None, 'remover': [], 'regra': 'Criada da DIMA (EST MER 6 ' + k + ')'})
        of[nome] = k + ' ' + nome; nomes.add(nome); novas.append(of[nome])
    if novas: print(len(novas), 'categorias criadas:', novas)
    cats = [x for x in c['libSeed']['categorias'] + c['cfg']['categorias'] if x.get('cesta') == 'FARMACIA']
    porcod = defaultdict(list)
    for x in cats:
        k = cod(of.get(x['nome'], '') or x['nome'])
        if k and x['nome'] not in porcod[k]: porcod[k].append(x['nome'])
    pornome = {N(x['nome']): x['nome'] for x in cats}
    labs = {N(f) for f in d['fabs']} | {w for f in d['fabs'] for w in [N(f).split(' ')[0]] if len(w) >= 4}

    def destino(seg, termo):
        if seg in SEG_EXTRA: return SEG_EXTRA[seg]
        k = cod(seg); filhos = sorted({n for kk, v in porcod.items() if kk.startswith(k) for n in v},
                                      key=lambda n: cod(of.get(n, '') or n) or 'Z')
        if len(filhos) == 1: return filhos[0], 0
        if filhos:
            assoc = bool(re.search(r'\+| E |(?<![A-Z])(COMP|COMPOSTO|ASSOC|ASSOCIADO|PLUS)(?![A-Z])', termo))
            rx_a = re.compile(r'(?<![A-Z])(ASSOC\w*|COMB\w*|COM)(?![A-Z])')
            f = [n for n in filhos if bool(rx_a.search(N(n))) == assoc]
            pura = [n for n in f if re.search(r'(?<![A-Z])(PUROS?|PURAS?|SIMPLES|SOLO|SOLA)(?![A-Z])', N(n))]
            return (pura or f or filhos)[0], 1
        if k in MAPA6 and MAPA6[k][0] in {x for v in pornome.values() for x in [v]}: return MAPA6[k]
        n = pornome.get(N(COD.sub('', seg)))
        return (n, 0) if n else (None, 0)

    atc, fora = defaultdict(Counter), Counter()
    r = d['rows']
    for k in range(0, len(r), 3):
        seg = d['segs'][r[k + 1]]; t = separa(d['marcas'][r[k]])
        if cod(seg) or seg in SEG_EXTRA: atc[t][seg] += 1
        else: fora[t] += 1
    # palavra comum (listas do app e termos das categorias de outras cestas: LENTE, PORTA...) não vira termo de Farmácia
    comum = {N(w) for k in ('GENERIC', 'NOISE', 'ATTR', 'FLAVORS') for w in c['const'].get(k, [])}
    for x in todas:
        if x.get('cesta') != 'FARMACIA':
            for t in (x.get('incluir') or []) + (x.get('tipo') or []) + (x.get('tambem') or []): comum.update(N(str(t).replace('*', ' ')).split())
    out, sem = [], 0
    for t, cs in sorted(atc.items()):
        w = t.split(' ')
        if len(t) < 4 or t.isdigit() or (len(w) == 1 and t in comum) or w[0] in NAO or t in NAO or t in labs or w[-1] in ('DE', 'DA', 'DO', 'E', 'C', 'P', 'COM'): continue
        tot = sum(cs.values()); seg, v = cs.most_common(1)[0]
        if fora[t] > tot: continue  # marca mais de fora da Farmácia (GRANADO)
        cat, esc = destino(seg, t)
        if not cat: sem += 1; continue
        out.append([t, cat, seg, 1 if v / tot < 0.6 else esc])  # EST MER 6 dividida: fica a mais votada, para revisão
    c['farmaDima'] = out
    (here / 'consts.json').write_text(json.dumps(c, ensure_ascii=False), encoding='utf-8')
    print(f"{len(out)} termos da DIMA com categoria ({sum(o[3] for o in out)} com subcategoria escolhida); {sem} sem categoria no app")


if __name__ == '__main__':
    main()
