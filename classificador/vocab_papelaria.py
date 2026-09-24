"""Vocabulário de papelaria / armarinho / festa (a partir do backlog "PAPELARIA OUTROS").

Mesmo esquema do vocab_material.py: palavra solta vai para "tipo" (só vale como 1ª palavra da descrição),
frase vai para "incluir"; "excluir" tira falsos positivos; "remover_tipo" limpa tipos que o patch de
material tinha posto e que pertencem à papelaria (LINHA, LETRA, BOBINA, GRAMPEADOR, ESTILETE).
Tipo sem categoria própria vai para PAPELARIA OUTROS (categoria dinâmica: o descritivo começa pelo tipo).

Uso (depois do vocab_material.py): python3 vocab_papelaria.py && python3 build.py
"""
import json
from pathlib import Path
from vocab_material import pl

here = Path(__file__).parent
PATCH_ID = 'papelaria-2026-09'

PATCH = {
    'PAPELARIA OUTROS': {'remover_excluir': ['LAPIS', 'CANETA'], 'incluir': pl(
        'ESTOJO', 'PASTA', 'PASTA CATALOGO', 'PASTA SANFONADA', 'PASTA ELASTICO', 'PASTA AZ', 'PASTA SUSPENSA', 'CLIPS', 'CLIPES',
        'CLIPE', 'CLIP', 'GRAFITE', 'REGUA', 'ENVELOPE', 'ETIQUETA', 'ETIQ', 'ETIQUETADORA', 'CALCULADORA', 'MARCADOR DE PAGINA',
        'MARCADOR PAGINA', 'MARCADOR PAG', 'CARTOLINA', 'PAPEL', 'PAPEL CREPOM', 'PAPEL CREPON', 'CREPON', 'CREPOM', 'PAPEL COUCHE',
        'PAPEL CELOFANE', 'PAPEL FOTO', 'PAPEL FOTOGRAFICO', 'PAPEL CARTAO', 'PAPEL KRAFT', 'PAPEL VERGE', 'PAPEL CARBONO', 'CARBONO',
        'PAPEL CONTACT', 'CONTACT', 'PAPEL LAMINADO', 'PAPEL MANTEIGA', 'PAPEL VEGETAL', 'PAPEL MICROONDULADO', 'EVA', 'FOLHA EVA',
        'PLACA EVA', 'PLACA DE EVA', 'PLACA EM EVA', 'FOLHA', 'FOLHAS', 'GLITTER', 'GLITER', 'PURPURINA', 'LANTEJOULA', 'MICANGA',
        'LETRA', 'LETRA EVA', 'LETRA DECORATIVA', 'LETRA ISOPOR', 'BOBINA TERMICA', 'BOBINA PDV', 'BOBINA PARA PDV', 'BOBINA TERMO',
        'BOBINA TERMICAS', 'TELA PARA PINTURA', 'TELA PINTURA', 'TELA DE PINTURA', 'PORTA LAPIS', 'PORTA CANETA', 'PORTA CARTAO',
        'PORTA CARTOES', 'PORTA CRACHA', 'PORTA DOCUMENTO', 'PORTA DOCUMENTOS', 'PORTA CLIPS', 'PORTA ACESS', 'PORTA BLOCO',
        'CRACHA', 'REVISTA', 'REV', 'JORNAL', 'ALMANAQUE', 'GIBI', 'PALAVRAS CRUZADAS', 'CRUZADINHA', 'COMPASSO', 'TRANSFERIDOR',
        'CARIMBO', 'ALMOFADA PARA CARIMBO', 'PRANCHETA', 'FICHARIO', 'DIVISORIA', 'ARQUIVO', 'CAIXA ARQUIVO', 'TALAO', 'RECIBO',
        'NOTA PROMISSORIA', 'PEDIDO', 'TALAO DE PEDIDO', 'VALE', 'LUPA', 'PERCEVEJO', 'TACHINHA', 'PERFURADOR', 'FURADOR',
        'GRAMPEADOR', 'GRAMPO PARA GRAMPEADOR', 'GRAMPO P GRAMPEADOR', 'GRAMPO 26 6', 'GRAMPO 23', 'EXTRATOR DE GRAMPO',
        'ESTILETE', 'LAMINA', 'LAMINAS', 'LAMINA ESTILETE', 'LAMINA PARA ESTILETE', 'AQUARELA', 'GUACHE', 'TINTA GUACHE', 'TEMPERA', 'TINTA TEMPERA',
        'ALBUM', 'ALBUM DE FIGURINHAS', 'ALBUM FOTO', 'ALBUM PARA FOTOS', 'MALETA', 'MALETA ARTISTICA', 'IMA', 'IMAS', 'LOUSA',
        'QUADRO BRANCO', 'QUADRO DE AVISOS', 'CORTIÇA', 'CORTICA', 'CARTAO', 'CARTAO PRESENTE', 'CARTAO LEMBRANCINHA', 'CARTAO VISITA',
        'CALENDARIO', 'CADERNETA', 'CAPA PLASTICA', 'PLASTICO', 'PLASTICOS', 'TNT', 'FELTRO ARTESANATO',
        'COLORIR', 'KIT ESCOLAR', 'MATERIAL ESCOLAR', 'APONT', 'BORRACHAS', 'RASCUNHO', 'BLOCO RASCUNHO',
    )},
    'ESCRITA OUTROS': {'incluir': pl(
        'MARCADOR', 'MARCADOR PERMANENTE', 'MARCADOR DE QUADRO', 'MARCADOR QUADRO BRANCO', 'MARCADOR BRUSH', 'MARCADOR CD',
        'PINCEL ATOMICO', 'CORRETOR', 'CORRETIVO', 'FITA CORRETIVA', 'GIZ', 'GIZAO', 'GIZ DE CERA', 'GIZ PASTEL', 'REABASTECEDOR',
        'REFIL DE MARCADOR', 'CARGA CANETA', 'CARGA PARA CANETA', 'MINAS', 'MINA GRAFITE',
    )},
    'BLOCO DE NOTAS': {'incluir': pl('BLOCO', 'BLOCO LEMBRETE', 'BLOCO DE ANOTACOES', 'BLOCO ANOTACOES', 'BLOCO RECADO', 'RECADO', 'NOTAS', 'NOTA ADESIVA', 'POST IT', 'BLOCO ADESIVO')},
    'CADERNO': {'incluir': pl('CADERNETA ESCOLAR', 'CAD', 'CADERNO BROCHURA', 'CADERNO ESPIRAL', 'CADERNO DE DESENHO', 'CADERNO CALIGRAFIA', 'DIARIO')},
    'LIVRO': {'incluir': pl('LIV', 'BIBLIA', 'DICIONARIO', 'ATLAS', 'CARTILHA', 'TABUADA', 'LIVRO DE COLORIR', 'LIVRO COLORIR', 'LIVRO INFANTIL', 'HISTORIAS', 'CLASSICOS', 'TODOLIVRO', 'CULTURAMA', 'ATIVIDADES', 'LIVRINHO')},
    'LAPIS/LAPISERA': {'remover_excluir': ['BORRACHA', 'APONTADOR'], 'incluir': pl('LAPIS', 'LAPIS PRETO', 'LAPIS GRAFITE', 'LAPIS ESCOLAR', 'LAPIS N2', 'LAPIS HB')},
    'FOLHA SULFITE': {'incluir': pl('PAPEL OFICIO', 'RESMA', 'PAPEL A4 SULFITE')},
    'FITILHO': {'incluir': pl('FITA', 'FITAS', 'FITA CETIM', 'FITA DE CETIM', 'FITA POLI', 'FITA DECORATIVA', 'FITA GORGURAO', 'FITA DE GORGURAO', 'FITA ORGANZA', 'FITA VELUDO', 'FITA DE VELUDO', 'FITA LANTECORES', 'FITA METALIZADA', 'FITA JUTA', 'FITA ESTAMPADA', 'FITA XADREZ', 'FITILHOS')},
    'FITA ADESIVA': {'incluir': pl('FITA DUREX', 'DUREX', 'FITA TRANSPARENTE', 'FITA DUPLA FACE', 'FITA EMPACOTAMENTO', 'FITA KRAFT', 'FITA ADESIVA COLORIDA', 'FITA MAGICA', 'FITA WASHI', 'WASHI TAPE')},
    'EMBALAGEM  PRESENTE': {'incluir': pl('LACO', 'LACO FACIL', 'LACO PRONTO', 'LACO MAGICO', 'LACO FITA', 'SACO PRESENTE', 'SACO DE PRESENTE', 'SACO PARA PRESENTE', 'SACOS PARA PRESENTE', 'SACO P PRESENTE', 'SACO CROMUS', 'SACO CELOFANE', 'CROMUS', 'PAPEL PRESENTE', 'PAPEL DE PRESENTE', 'BOBINA DE PAPEL DE PRESENTE', 'BOBINA PAPEL PRESENTE', 'CAIXA PRESENTE', 'CAIXA DE PRESENTE', 'FOLHA PRESENTE', 'ETIQUETA PRESENTE', 'TAG PRESENTE')},
    'SACOLA PRESENTE': {'incluir': pl('SACOLA PAPEL', 'SACOLA DE PAPEL', 'SACOLA SURPRESA', 'SACOLA SURP', 'SACOLINHA SURPRESA', 'SACOLINHA')},
    'EMBALAGEM OUTROS': {'incluir': pl('SACOLA', 'SACOLA PLASTICA', 'SACOLA REEXT', 'SACOLA ALCA', 'SACO', 'SACO PLASTICO', 'SACO VAZIO', 'SACO ALGODAO', 'SACARIA', 'BOBINA PAPEL PADARIA', 'SACO DE PAPEL', 'SACO PAPEL', 'SACO KRAFT')},
    'ACESSORIO COSTURA': {'incluir': pl('LINHA', 'LINHA CROCHE', 'LINHA PARA CROCHE', 'LINHA P CROCHE', 'LINHA TRICO', 'LINHA PARA TRICO', 'LINHA BORDAR', 'LINHA PARA BORDAR', 'LINHA MERCERIZADA', 'FIO DE LA', 'FIO CROCHE', 'FIO P CROCHE', 'FIO PARA CROCHE', 'FIO TRICO', 'FIO PARA TRICO', 'FIO PRINCESA', 'FIO EURO ROMA', 'NOVELO', 'LA', 'AGULHA', 'AGULHA CROCHE', 'AGULHA TRICO', 'AVIAMENTO', 'AVIAM', 'BOTAO', 'BOTOES', 'ZIPER', 'VIES', 'ELASTICO DE COSTURA', 'CARRETEL', 'FRANJA', 'PASSAMANARIA', 'RENDA', 'ENTRETELA', 'COSTURA')},
    'LINHA BARBANTE': {'incluir': pl('BARB', 'BARBANTES', 'BARBANTE CROCHE')},
    'BRINQUEDO MASSA DE MODELAR': {'incluir': pl('MASSA DE MODELAR', 'MASSA P MODELAR', 'MASSA PARA MODELAR', 'MASSINHA', 'MASSINHA DE MODELAR')},
    'ACESSORIO PARA FESTA GERAL': {'incluir': pl('LEQUE', 'FAIXA', 'FAIXA FELIZ ANIVERSARIO', 'FAIXA DECORATIVA', 'BANDEIRA', 'BANDEIRINHA', 'BANDEIROLA', 'CONVITE', 'JUNCO', 'SERPENTINA', 'APITO', 'LINGUA DE SOGRA', 'CHAPEU DE FESTA')},
    'ACESSORIO PERIFERICO': {'incluir': pl('PEN DRIVE', 'PENDRIVE', 'CARTAO DE MEMORIA', 'CARTAO MEMORIA', 'CARTUCHO DE TINTA', 'CARTUCHO TINTA', 'CARTUCHO HP', 'TONER', 'MOUSE', 'MOUSEPAD')},
    'UTILIDADE OUTROS': {'incluir': pl('CHAVEIRO', 'VENTOSA', 'PORTA CONTROLE', 'PORTA CONTROLE REMOTO')},
    'TESOURA': {'incluir': pl('TESOUR', 'TESOURA ESCOLAR', 'TESOURA SEM PONTA')},
    'MOCHILA': {'incluir': pl('LANCHEIRA', 'MOCHILETE', 'MOCHILA ESCOLAR')},
    'AGENDA': {'incluir': pl('PLANNER', 'AGENDA ESCOLAR')},
    # --- falsos positivos vistos no backlog de papelaria ---
    'ENERGETICO': {'excluir': ['BRANCO 1400', '1400 MM', '1400MM', 'MT', 'METRO', 'METROS', 'ROLO', 'TECIDO', 'VMP', 'AZUL CLARO']},
    'TUBO E CONEXAO': {'excluir': ['GLITTER', 'GLITER', 'PURPURINA', 'COLA', 'TINTA', 'GUACHE', 'ESCOLAR', 'SCHOOL']},
    'VITAMINA OUTRO': {'excluir': ['IMA', 'IMAS', 'MAGNETS', 'CLIPES', 'CLIPS', 'PERFURADOR', 'FURADOR']},
    'BIJUTERIA': {'excluir': ['IMA', 'MAGNETS', 'FICHARIO', 'ARGOLA FICHARIO']},
    'ELASTICO': {'excluir': ['PASTA', 'PASTAS']},
    'PLANTA E FLOR': {'excluir': ['PASTA', 'ESTOJO', 'FITA', 'CARTOLINA', 'EVA', 'LACO', 'PAPEL', 'REGUA', 'FOLHA EVA', 'GLITTER']},
    'OTP - OUTROS TABACO': {'excluir': ['PAPEL CREPOM', 'PAPEL CELOFANE', 'PAPEL PRESENTE', 'PAPEL SEDA COLORIDO', 'PAPEL SEDA ARTESANATO', 'CORDA']},
    'COPA': {'excluir': ['ALBUM', 'FIGURINHA', 'FIGURINHAS']},
    'ROUPA INFANTIL': {'excluir': ['ESTOJO', 'MALETA', 'ALBUM', 'SACO PRESENTE', 'LIVRO', 'CADERNO']},
    'CONJUNTO DE ROUPA': {'excluir': ['CONJUNTO ESCOLAR', 'CONJUNTO GEOMETRICO', 'CONJUNTO DE CANETAS', 'CONJUNTO CANETA', 'CANETA', 'LAPIS', 'REGUA', 'ESQUADRO']},
    'DOCE OUTROS': {'excluir': ['SACOLA', 'SACOLAS', 'SACOLINHA']},
    'FRALDINHA BOVINA': {'excluir': ['SACO', 'SACARIA', 'VAZIO']},
    'LARANJA': {'excluir': ['EVA', 'CARTOLINA', 'PAPEL', 'FITA', 'CETIM', 'COR LARANJA', 'GLITTER']},
    'AZEITONA': {'remover_incluir': ['AZ'], 'incluir': ['AZ VERDE', 'AZ PRETA', 'AZ CHILENA', 'AZ FATIADA', 'AZ RECHEADA', 'AZ S CAROCO', 'AZ SEM CAROCO'], 'excluir': ['PASTA', 'FITA', 'CETIM', 'EVA', 'PAPEL']},
    'ACESSORIO PARA CABELO OUTROS': {'excluir': ['GRAMPEADOR', 'GRAMPO 26', 'GRAMPO 23', 'GRAMPO TRILHO', 'GRAMPO PARA GRAMPEADOR']},
    # tipos soltos que o patch de material tinha posto e são de papelaria / armarinho
    'MATERIAL OUTROS': {'remover_tipo': ['LINHA', 'LINHAS', 'LETRA', 'LETRAS', 'BOBINA', 'BOBINAS']},
    'EQUIPAMENTO MANUAL': {'remover_tipo': ['GRAMPEADOR', 'GRAMPEADORES', 'ESTILETE', 'ESTILETES']},
}


def main():
    c = json.loads((here / 'consts.json').read_text(encoding='utf-8'))
    byname = {x['nome']: x for x in c['libSeed']['categorias'] + c['cfg']['categorias']}
    faltou = [n for n in PATCH if n not in byname]
    assert not faltou, faltou
    for p in PATCH.values():
        inc = p.pop('incluir', [])
        p['tipo'] = [t for t in inc if ' ' not in t]
        p['incluir'] = [t for t in inc if ' ' in t]
    for nome, p in PATCH.items():
        x = byname[nome]
        x.setdefault('tipo', [])
        for k in ('incluir', 'excluir', 'tipo'):
            for t in p.get(k, []):
                if t not in x[k]: x[k].append(t)
        rm = set(p.get('remover_tipo', []))
        x['tipo'] = [t for t in x['tipo'] if t not in rm]
        rmi = set(p.get('remover_incluir', []))
        x['incluir'] = [t for t in x['incluir'] if t not in rmi]
        rme = set(p.get('remover_excluir', []))
        x['excluir'] = [t for t in x['excluir'] if t not in rme]
    c.setdefault('libPatches', {})[PATCH_ID] = PATCH
    (here / 'consts.json').write_text(json.dumps(c, ensure_ascii=False), encoding='utf-8')
    print(f'{len(PATCH)} categorias ajustadas; {sum(len(p["tipo"]) for p in PATCH.values())} tipos (1a palavra) e '
          f'{sum(len(p["incluir"]) for p in PATCH.values())} frases novas')


if __name__ == '__main__':
    main()
