"""Liga cada categoria da biblioteca (nível do manual) às categorias EST MER 6 da base DIMA / dicionário.

A marca só é aceita se existir na DIMA (ou no dicionário) numa dessas categorias, e o fabricante é o de maior
venda / mais frequente para a marca dentro delas. Fontes, nesta ordem:
1. MAPA fixo abaixo (construção, papelaria... onde o nome não entrega a ligação)
2. nome idêntico ao da categoria DIMA
3. 1ª palavra (ou 2 primeiras) igual a uma categoria DIMA inteira (FEIJAO CARIOCA -> FEIJAO)
4. Farmácia: dicionário de princípios ativos (Est Mer 6 de cada princípio)
O que ficar sem ligação o app aprende no próprio backlog (marcas encontradas nos itens da categoria), e a
pessoa pode fixar à mão no campo "Segmentos" de cada categoria.

Uso: python3 segmentos.py && python3 build.py   (depois de dima.py / farma_pa.py)
"""
import gzip, json, re, unicodedata
from pathlib import Path
import openpyxl

here = Path(__file__).parent
N = lambda s: ' '.join(re.sub(r'[^A-Z0-9 ]', ' ', unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().upper()).split())

MAPA = {
    'HIDRAULICA': ['ACESSORIO HIDRAULICA', 'TUBO E CONEXAO', 'TORNEIRA', 'DUCHA CHUVEIRO', 'CAIXA ACOPLADA', 'VELA DE FILTRO'],
    'FERRAMENTA MANUAL': ['EQUIPAMENTO MANUAL', 'MEDICAO E MARCACAO', 'ACESSORIO/PECA DE REPOSICAO'],
    'FERRAMENTA ELETRICA': ['MAQUINA ELETRICA', 'ACESSORIO/PECA DE REPOSICAO'],
    'ILUMINACAO': ['LAMPADA', 'LUMINARIA INTERNA/EXTERNA', 'ABAJUR', 'ACESSORIO DE ILUMINACAO'],
    'COMPONENTE ELETRICO': ['DISJUNTOR', 'CONECTOR ELETRICO', 'TOMADA E INTERRUPTOR'],
    'FIXACAO': ['BUCHA E PARAFUSO', 'FIXACAO OUTROS', 'PREGO E GRAMPO', 'ABRACADEIRA', 'GANCHO E SUPORTE'],
    'FERRAGEM': ['DOBRADICA E FECHADURA', 'CADEADO'],
    'PINTURA': ['TINTA E ACESSORIO'],
    'JARDINAGEM': ['JARDINAGEM OUTROS', 'PLANTA E FLOR', 'ESTERCO'],
    'FITA ADESIVA': ['FITA ADESIVA OUTROS', 'FITA ADESIVA'],
    'PILHA E BATERIA': ['PILHA', 'BATERIA'],
    'COLA': ['COLA BASTAO', 'COLA BRANCA', 'COLA MADEIRA', 'COLA INSTANTANEA', 'COLA OUTROS', 'COLA SILICONE'],
    'LAPIS LAPISERA': ['LAPIS/LAPISERA'],
    'CAIXA PLASTICA PAPELAO': ['CAIXA PLASTICA/PAPELAO'],
    'LAVANDERIA': ['PRENDEDOR DE ROUPA', 'VARAL ROUPA', 'CESTO DE ROUPA', 'TABUA DE PASSAR'],
    'UTILIDADE DOMESTICA': ['UTILIDADE OUTROS', 'LIXEIRA', 'BACIA', 'CABIDE'],
    'ARTESANATO': ['ACESSORIO COSTURA', 'LINHA BARBANTE', 'FITILHO'],
    'PAPELARIA OUTROS': ['ACESSORIO COSTURA', 'LINHA BARBANTE', 'FITILHO'],  # a DIMA registra barbante/linha também aqui
    'EMBALAGEM': ['EMBALAGEM  PRESENTE', 'SACOLA PRESENTE', 'EMBALAGEM OUTROS', 'EMBALAGEM ALIMENTO', 'SACOLA ALIMENTO'],
    'ACESSORIO PARA FESTA': ['ACESSORIO PARA FESTA GERAL'],
    'ACESSORIO ELETRO INFO': ['ACESSORIO PERIFERICO'],
}


def main():
    c = json.loads((here / 'consts.json').read_text(encoding='utf-8'))
    d = json.loads(gzip.decompress((here / 'dima.json.gz').read_bytes()))
    segs = {N(s): s for s in d['segs'] if s}
    cats = c['libSeed']['categorias'] + c['cfg']['categorias']
    out = {}
    add = lambda cat, s: out.setdefault(cat, []) if s in out.get(cat, []) else out.setdefault(cat, []).append(s)
    for s, lst in MAPA.items():
        assert N(s) in segs, s
        for cat in lst: add(cat, segs[N(s)])
    for x in cats:
        nome = x['nome']; n = N(nome); w = n.split()
        if n in segs: add(nome, segs[n])
        elif nome not in out:
            for k in (2, 1):
                if len(w) > k and ' '.join(w[:k]) in segs: add(nome, segs[' '.join(w[:k])]); break
    # Farmácia: Est Mer 6 dos princípios ativos de cada categoria
    rows = list(openpyxl.load_workbook(here / 'dados' / 'dicionario_nomenclaturas_farmaceuticas.xlsx', read_only=True)['Dicionário'].iter_rows(min_row=2, values_only=True))
    e6 = {}
    for r in rows:
        if r[3] and r[4]: e6.setdefault(N(re.sub(r'\([^)]*\)', ' ', r[3])), set()).add(N(r[4]))
    for p in c.get('farmaPA', []):
        for s in e6.get(N(re.sub(r'\([^)]*\)', ' ', p['pa'])), []):
            if s in segs: add(p['cat'], segs[s])
    c['segPadrao'] = out
    (here / 'consts.json').write_text(json.dumps(c, ensure_ascii=False), encoding='utf-8')
    far = {x['nome'] for x in cats if x.get('cesta') == 'FARMACIA'}
    print(f"{len(out)} de {len(cats)} categorias ligadas à DIMA ({sum(1 for k in out if k in far)} de Farmácia)")


if __name__ == '__main__':
    main()
